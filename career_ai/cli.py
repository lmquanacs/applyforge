from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Optional

import typer
from rich.markdown import Markdown

from career_ai.config import init_config, load_config, set_config_value
from career_ai.core.extractor import extract
from career_ai.core.reviewer import build_review_prompt
from career_ai.core.polisher import build_polish_prompt
from career_ai.core.generator import build_cover_letter_prompt
from career_ai.core.interviewer import build_interview_prep_prompt
from career_ai.core.ats import ats_score as compute_ats_score
from career_ai.llm.client import call_llm
from career_ai.utils.logging import (
    console,
    log_usage,
    append_chat_message,
    load_chat_history,
    clear_chat_history,
    drop_all,
)
from career_ai.utils.output import save_output, export_cv_pdf

app = typer.Typer(help="Career AI — automated CV feedback, polishing, and cover letter writing.")

cv_app = typer.Typer(help="CV commands.")
coverletter_app = typer.Typer(help="Cover letter commands.")
interview_app = typer.Typer(help="Interview preparation commands.")
config_app = typer.Typer(help="Manage configuration.")
vault_app = typer.Typer(help="Career Vault (local RAG) commands.")
agent_app = typer.Typer(help="Agentic pipeline commands.")

app.add_typer(cv_app, name="cv")
app.add_typer(coverletter_app, name="coverletter")
app.add_typer(interview_app, name="interview")
app.add_typer(config_app, name="config")
app.add_typer(vault_app, name="vault")
app.add_typer(agent_app, name="agent")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _strip_code_fence(text: str) -> str:
    return re.sub(r"^```[\w]*\n?(.*?)\n?```$", r"\1", text.strip(), flags=re.DOTALL)


def _resolve_cv(cv_file: Optional[Path]) -> Path:
    """
    Resolve the CV file path.
    Priority: explicit argument → app.default_cv_path → auto-discover single file in working_dir.
    """
    if cv_file is not None:
        return cv_file
    config = load_config()
    resolved = config.default_cv
    if resolved is None:
        raise typer.BadParameter(
            "No CV file provided. Either pass a path, set a default:\n"
            "  career-ai config set app.default_cv_path ~/Documents/career-ai/my_cv.pdf\n"
            f"or place a single PDF/DOCX in {config.working_dir_path}"
        )
    console.print(f"[dim]Using default CV: {resolved}[/]")
    return resolved


def _resolve_jd(jd: Optional[str], url: Optional[str]) -> str:
    """Return JD text from --jd (file or raw string) or --url."""
    if url:
        from career_ai.core.scraper import scrape_url
        with console.status(f"Scraping JD from {url}..."):
            return scrape_url(url)
    if jd:
        jd_path = Path(jd)
        return extract(jd_path) if jd_path.exists() else jd
    raise typer.BadParameter("Provide either --jd or --url.")


# ── Init / Config ─────────────────────────────────────────────────────────────

@app.command()
def init():
    """Generate the default config file at ~/.config/career-ai/config.yaml."""
    path = init_config()
    console.print(f"[green]Config initialized at[/] {path}")


@config_app.command("set")
def config_set(key: str, value: str):
    """Set a config value. Example: career-ai config set model.default gpt-4o"""
    set_config_value(key, value)
    console.print(f"[green]Set[/] {key} = {value}")


# ── CV Commands ───────────────────────────────────────────────────────────────

@cv_app.command("review")
def cv_review(
    cv_file: Optional[Path] = typer.Argument(None, help="Path to CV file (.pdf, .docx, .md, .txt)"),
    model: Optional[str] = typer.Option(None, help="Override model"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Preview without API call"),
):
    """Analyze a CV and produce a structured feedback report."""
    config = load_config()
    with console.status("Extracting CV..."):
        cv_text = extract(_resolve_cv(cv_file))
    system, user = build_review_prompt(cv_text)
    result = call_llm(system, user, config, model=model, dry_run=dry_run)
    console.print(Markdown(result))


@cv_app.command("polish")
def cv_polish(
    cv_file: Optional[Path] = typer.Argument(None, help="Path to CV file"),
    out: Path = typer.Option(Path("output/polished_cv.md"), "--out", help="Output file path"),
    pdf: bool = typer.Option(False, "--pdf", help="Also export a styled PDF"),
    tone: str = typer.Option("professional", help="Target tone"),
    focus: str = typer.Option("general", help="Areas to focus on"),
    model: Optional[str] = typer.Option(None, help="Override model"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Preview without API call"),
):
    """Rewrite and enhance a CV without hallucinating new facts."""
    config = load_config()
    with console.status("Extracting CV..."):
        cv_text = extract(_resolve_cv(cv_file))
    system, user = build_polish_prompt(cv_text, tone, focus)
    result = call_llm(system, user, config, model=model, dry_run=dry_run)
    result = _strip_code_fence(result)
    saved = save_output(result, out)
    console.print(f"[green]Polished CV saved to[/] {saved}")
    if pdf:
        pdf_path = out.with_suffix(".pdf")
        with console.status("Exporting PDF..."):
            export_cv_pdf(result, pdf_path)
        console.print(f"[green]PDF exported to[/] {pdf_path}")


@cv_app.command("ats-score")
def cv_ats_score(
    cv_file: Optional[Path] = typer.Argument(None, help="Path to CV file"),
    jd: Optional[str] = typer.Option(None, "--jd", help="Path to JD file or raw JD text"),
    url: Optional[str] = typer.Option(None, "--url", help="URL of the job posting"),
):
    """Score how well your CV matches a Job Description (local, zero API cost)."""
    with console.status("Extracting documents..."):
        cv_text = extract(_resolve_cv(cv_file))
        jd_text = _resolve_jd(jd, url)

    score, matched, missing = compute_ats_score(cv_text, jd_text)

    console.print(f"\n[bold]ATS Match Score:[/] [{'green' if score >= 60 else 'yellow' if score >= 40 else 'red'}]{score}%[/]")
    console.print(f"[bold]Matched keywords ({len(matched)}):[/] {', '.join(matched[:20])}{'...' if len(matched) > 20 else ''}")
    console.print(f"\n[bold red]Missing keywords ({len(missing)}):[/]")
    for kw in missing[:30]:
        console.print(f"  • {kw}")


@cv_app.command("generate")
def cv_generate(
    cv_file: Optional[Path] = typer.Argument(None, help="Path to base CV file"),
    jd: Optional[str] = typer.Option(None, "--jd", help="Path to JD file or raw JD text"),
    url: Optional[str] = typer.Option(None, "--url", help="URL of the job posting"),
    out: Path = typer.Option(Path("output/generated_cv.md"), "--out", help="Output file path"),
    pdf: bool = typer.Option(False, "--pdf", help="Also export a styled PDF"),
    model: Optional[str] = typer.Option(None, help="Override model"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d"),
):
    """Generate a tailored CV using Career Vault context (Phase 3 RAG)."""
    config = load_config()
    with console.status("Extracting documents..."):
        cv_text = extract(_resolve_cv(cv_file))
        jd_text = _resolve_jd(jd, url)

    with console.status("Querying Career Vault..."):
        try:
            from career_ai.vault.query import query_vault
            chunks = query_vault(jd_text, top_k=config.app.vault_top_k)
        except Exception:
            chunks = []

    extra = "\n\n--- ADDITIONAL CAREER CONTEXT ---\n" + "\n".join(chunks) if chunks else ""
    system, user = build_polish_prompt(cv_text + extra, "professional", "general")
    result = call_llm(system, user, config, model=model, dry_run=dry_run)
    result = _strip_code_fence(result)
    saved = save_output(result, out)
    console.print(f"[green]Generated CV saved to[/] {saved}")
    if pdf:
        pdf_path = out.with_suffix(".pdf")
        with console.status("Exporting PDF..."):
            export_cv_pdf(result, pdf_path)
        console.print(f"[green]PDF exported to[/] {pdf_path}")


# ── Cover Letter ──────────────────────────────────────────────────────────────

@coverletter_app.command("write")
def coverletter_write(
    cv_file: Optional[Path] = typer.Argument(None, help="Path to CV file"),
    jd: Optional[str] = typer.Option(None, "--jd", help="Path to JD file or raw JD text"),
    url: Optional[str] = typer.Option(None, "--url", help="URL of the job posting"),
    out: Path = typer.Option(Path("output/cover_letter.md"), "--out", help="Output file path"),
    tone: str = typer.Option("professional", help="Letter tone"),
    model: Optional[str] = typer.Option(None, help="Override model"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Preview without API call"),
):
    """Generate a tailored cover letter from a CV and Job Description."""
    config = load_config()
    with console.status("Extracting documents..."):
        cv_text = extract(_resolve_cv(cv_file))
        jd_text = _resolve_jd(jd, url)
    system, user = build_cover_letter_prompt(cv_text, jd_text, tone, config.app.max_cover_letter_words)
    result = call_llm(system, user, config, model=model, dry_run=dry_run)
    result = _strip_code_fence(result)
    saved = save_output(result, out)
    console.print(f"[green]Cover letter saved to[/] {saved}")


# ── Interview Prep ────────────────────────────────────────────────────────────

@interview_app.command("prep")
def interview_prep(
    cv_file: Optional[Path] = typer.Argument(None, help="Path to CV file"),
    jd: Optional[str] = typer.Option(None, "--jd", help="Path to JD file or raw JD text"),
    url: Optional[str] = typer.Option(None, "--url", help="URL of the job posting"),
    out: Path = typer.Option(Path("output/interview_prep.md"), "--out", help="Output file path"),
    model: Optional[str] = typer.Option(None, help="Override model"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d"),
):
    """Generate a STAR-method interview prep guide tailored to a specific JD."""
    config = load_config()
    with console.status("Extracting documents..."):
        cv_text = extract(_resolve_cv(cv_file))
        jd_text = _resolve_jd(jd, url)
    system, user = build_interview_prep_prompt(cv_text, jd_text)
    result = call_llm(system, user, config, model=model, dry_run=dry_run)
    saved = save_output(result, out)
    console.print(f"[green]Interview prep saved to[/] {saved}")
    console.print(Markdown(result))


# ── Chat (Agentic Coach) ──────────────────────────────────────────────────────

@app.command()
def chat(
    session: str = typer.Option("default", "--session", "-s", help="Session ID to resume"),
    model: Optional[str] = typer.Option(None, help="Override model"),
):
    """Start an interactive agentic coaching session with memory."""
    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.history import InMemoryHistory
    except ImportError:
        console.print("[red]prompt_toolkit is required for chat mode. Run: pip install prompt_toolkit[/]")
        raise typer.Exit(1)

    config = load_config()
    target_model = model or config.model.default
    db_path = config.usage_db

    history = load_chat_history(session, db_path)
    if history:
        console.print(f"[dim]Resuming session '{session}' ({len(history)} messages)[/]")
    else:
        console.print(f"[dim]New session '{session}'. Type 'exit' to quit.[/]")

    system_msg = {
        "role": "system",
        "content": (
            "You are an expert career coach. Help the user improve their CV, "
            "prepare for interviews, and craft cover letters. "
            "You have access to their conversation history. Be concise and actionable."
        ),
    }

    prompt_session = PromptSession(history=InMemoryHistory())

    while True:
        try:
            user_input = prompt_session.prompt("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Session saved. Goodbye.[/]")
            break

        if not user_input or user_input.lower() in ("exit", "quit", "bye"):
            console.print("[dim]Session saved. Goodbye.[/]")
            break

        append_chat_message(session, "user", user_input, db_path)
        history.append({"role": "user", "content": user_input})

        messages = [system_msg] + history

        try:
            from litellm import completion
            response = completion(
                model=target_model,
                messages=messages,
                temperature=config.model.temperature,
                max_tokens=config.tokens.max_output_limit,
            )
            reply = response.choices[0].message.content
        except Exception as exc:
            console.print(f"[red]Error:[/] {exc}")
            continue

        append_chat_message(session, "assistant", reply, db_path)
        history.append({"role": "assistant", "content": reply})
        console.print(f"\n[bold cyan]Coach:[/] {reply}\n")


# ── Ask (Natural Language Mode) ───────────────────────────────────────────────

@app.command()
def ask(
    prompt: str = typer.Argument(..., help="Natural language instruction"),
    model: Optional[str] = typer.Option(None, help="Override router model"),
):
    """Translate a natural language instruction into a career-ai command and execute it."""
    config = load_config()
    router_model = model or "gpt-4o-mini"

    config = load_config()
    default_cv = config.default_cv
    cv_hint = f"If the user refers to their CV without a full path, use: {default_cv}" if default_cv else ""

    system = (
        "You are a CLI command router for the 'career-ai' tool. "
        "Given a natural language instruction, output ONLY the exact career-ai CLI command "
        "to run (no explanation, no markdown, no code fences). "
        f"{cv_hint} "
        "Available commands: cv review, cv polish, cv ats-score, cv generate, "
        "coverletter write, interview prep. "
        "Flags: --jd, --url, --out, --tone, --model, --pdf, --dry-run."
    )

    from litellm import completion
    response = completion(
        model=router_model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=200,
    )
    command = response.choices[0].message.content.strip()
    console.print(f"[dim]→ {command}[/]")

    import subprocess, sys
    subprocess.run([sys.executable, "-m", "career_ai.cli"] + command.replace("career-ai ", "").split())


# ── Clean / Reset ─────────────────────────────────────────────────────────────

@app.command()
def clean(
    history: bool = typer.Option(False, "--history", help="Also clear chat session history"),
):
    """Remove all generated files from the output/ directory."""
    output_dir = Path("output")
    if output_dir.exists():
        removed = list(output_dir.rglob("*.md")) + list(output_dir.rglob("*.pdf"))
        for f in removed:
            f.unlink()
        console.print(f"[green]Removed {len(removed)} file(s) from output/[/]")
    else:
        console.print("[dim]output/ directory is already empty.[/]")

    if history:
        config = load_config()
        count = clear_chat_history(config.usage_db)
        console.print(f"[green]Cleared {count} chat message(s) from history.[/]")


@app.command()
def reset(
    hard: bool = typer.Option(False, "--hard", help="Factory reset: drop DB, clear vault, reset config"),
):
    """Reset data. Use --hard for a full factory reset."""
    if not hard:
        console.print("Use [bold]--hard[/] to confirm a full factory reset.")
        raise typer.Exit(0)

    confirm = typer.confirm("This will delete your database, vault, and config. Are you sure?")
    if not confirm:
        raise typer.Exit(0)

    from career_ai.config import CONFIG_PATH, CONFIG_DIR
    import shutil as _shutil

    # Drop SQLite DB
    config = load_config()
    if config.usage_db.exists():
        drop_all(config.usage_db)
        config.usage_db.unlink()
        console.print("[green]Database dropped.[/]")

    # Clear vault
    vault_dir = Path.home() / ".config" / "career-ai" / "vault"
    if vault_dir.exists():
        _shutil.rmtree(vault_dir)
        console.print("[green]Vault cleared.[/]")

    # Reset config
    if CONFIG_PATH.exists():
        CONFIG_PATH.unlink()
        init_config()
        console.print("[green]Config reset to defaults.[/]")

    console.print("[bold green]Factory reset complete.[/]")


# ── Vault ─────────────────────────────────────────────────────────────────────

@vault_app.command("ingest")
def vault_ingest(
    file: Path = typer.Argument(..., help="Document to ingest (PDF, DOCX, MD, TXT)"),
):
    """Ingest a document into the Career Vault for RAG-powered CV generation."""
    try:
        from career_ai.vault.ingest import ingest
    except ImportError:
        console.print("[red]chromadb and sentence-transformers are required. Run: pip install chromadb sentence-transformers[/]")
        raise typer.Exit(1)

    with console.status(f"Ingesting {file.name}..."):
        count = ingest(file)
    console.print(f"[green]Ingested {count} chunks from {file.name}[/]")


@vault_app.command("clear")
def vault_clear():
    """Remove all documents from the Career Vault."""
    try:
        from career_ai.vault.ingest import clear_vault
    except ImportError:
        console.print("[red]chromadb is required. Run: pip install chromadb[/]")
        raise typer.Exit(1)

    confirm = typer.confirm("Clear all vault data?")
    if not confirm:
        raise typer.Exit(0)
    clear_vault()
    console.print("[green]Vault cleared.[/]")


# ── Agent Apply ───────────────────────────────────────────────────────────────

@agent_app.command("apply")
def agent_apply(
    cv_file: Optional[Path] = typer.Argument(None, help="Path to CV file"),
    url: str = typer.Option(..., "--url", help="URL of the job posting"),
    company: str = typer.Option(..., "--company", help="Company name"),
    role: str = typer.Option(..., "--role", help="Role title"),
):
    """
    Run the full Auto-Apply pipeline: ATS score → CV generation → Cover letter → Interview prep.
    Powered by LangGraph with SQLite checkpointing.
    """
    try:
        from career_ai.agent.graph import build_graph
    except ImportError:
        console.print("[red]langgraph is required. Run: pip install langgraph[/]")
        raise typer.Exit(1)

    config = load_config()
    out_dir = Path(f"output/{company}_{role}".replace(" ", "_"))
    out_dir.mkdir(parents=True, exist_ok=True)

    with console.status("Extracting CV..."):
        cv_text = extract(_resolve_cv(cv_file))

    initial_state: dict = {
        "cv_text": cv_text,
        "jd_url": url,
        "company": company,
        "role": role,
        "output_dir": str(out_dir),
        "errors": [],
        "retry_count": 0,
    }

    graph = build_graph(db_path=str(config.usage_db))

    console.print(f"[bold]Running Auto-Apply pipeline for[/] {company} — {role}")
    final_state = graph.invoke(initial_state)

    # Save outputs
    if final_state.get("cv_draft"):
        save_output(final_state["cv_draft"], out_dir / "cv.md")
    if final_state.get("cover_letter_draft"):
        save_output(final_state["cover_letter_draft"], out_dir / "cover_letter.md")
    if final_state.get("interview_prep"):
        save_output(final_state["interview_prep"], out_dir / "interview_prep.md")

    if final_state.get("errors"):
        console.print(f"[yellow]Warnings:[/] {final_state['errors']}")


def main():
    app()


if __name__ == "__main__":
    main()
