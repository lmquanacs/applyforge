from __future__ import annotations

from pathlib import Path
from typing import Optional

import re

import typer
from rich.markdown import Markdown

from career_ai.config import init_config, load_config, set_config_value
from career_ai.core.extractor import extract
from career_ai.core.reviewer import build_review_prompt
from career_ai.core.polisher import build_polish_prompt
from career_ai.core.generator import build_cover_letter_prompt
from career_ai.llm.client import call_llm
from career_ai.utils.logging import console
from career_ai.utils.output import save_output, export_cv_pdf

app = typer.Typer(help="Career AI — automated CV feedback, polishing, and cover letter writing.")
config_app = typer.Typer(help="Manage configuration.")
app.add_typer(config_app, name="config")


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


@app.command()
def review(
    cv_file: Path = typer.Argument(..., help="Path to CV file (.pdf, .docx, .md, .txt)"),
    model: Optional[str] = typer.Option(None, help="Override model"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Preview without API call"),
):
    """Analyze a CV and produce a structured feedback report."""
    config = load_config()
    with console.status("Extracting CV..."):
        cv_text = extract(cv_file)

    system, user = build_review_prompt(cv_text)
    result = call_llm(system, user, config, model=model, dry_run=dry_run)
    console.print(Markdown(result))


@app.command()
def polish(
    cv_file: Path = typer.Argument(..., help="Path to CV file"),
    out: Path = typer.Option(Path("output/polished_cv.md"), "--out", help="Output file path"),
    pdf: bool = typer.Option(False, "--pdf", help="Also export a styled PDF to output/polished_cv.pdf"),
    tone: str = typer.Option("professional", help="Target tone"),
    focus: str = typer.Option("general", help="Areas to focus on"),
    model: Optional[str] = typer.Option(None, help="Override model"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Preview without API call"),
):
    """Rewrite and enhance a CV without hallucinating new facts."""
    config = load_config()
    with console.status("Extracting CV..."):
        cv_text = extract(cv_file)

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


@app.command()
def write(
    cv_file: Path = typer.Argument(..., help="Path to CV file"),
    jd: str = typer.Option(..., "--jd", help="Path to JD file or raw JD text"),
    out: Path = typer.Option(Path("output/cover_letter.md"), "--out", help="Output file path"),
    tone: str = typer.Option("professional", help="Letter tone"),
    model: Optional[str] = typer.Option(None, help="Override model"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Preview without API call"),
):
    """Generate a tailored cover letter from a CV and Job Description."""
    config = load_config()

    with console.status("Extracting documents..."):
        cv_text = extract(cv_file)
        jd_path = Path(jd)
        jd_text = extract(jd_path) if jd_path.exists() else jd

    system, user = build_cover_letter_prompt(cv_text, jd_text, tone, config.app.max_cover_letter_words)
    result = call_llm(system, user, config, model=model, dry_run=dry_run)
    result = _strip_code_fence(result)

    saved = save_output(result, out)
    console.print(f"[green]Cover letter saved to[/] {saved}")


def _strip_code_fence(text: str) -> str:
    return re.sub(r"^```[\w]*\n?(.*?)\n?```$", r"\1", text.strip(), flags=re.DOTALL)


def main():
    app()


if __name__ == "__main__":
    main()
