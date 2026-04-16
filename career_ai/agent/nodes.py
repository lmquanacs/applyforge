from __future__ import annotations

from career_ai.agent.state import AgentState
from career_ai.core.scraper import scrape_url
from career_ai.core.ats import ats_score
from career_ai.core.generator import build_cover_letter_prompt
from career_ai.core.interviewer import build_interview_prep_prompt
from career_ai.config import load_config
from career_ai.llm.client import call_llm
from career_ai.utils.logging import console


def node_extract_jd(state: AgentState) -> AgentState:
    try:
        jd_text = scrape_url(state["jd_url"])
        return {**state, "jd_text": jd_text, "errors": state.get("errors", [])}
    except Exception as exc:
        errors = state.get("errors", []) + [f"extract_jd: {exc}"]
        return {**state, "jd_text": "", "errors": errors}


def node_ats_score(state: AgentState) -> AgentState:
    score, matched, missing = ats_score(state["cv_text"], state["jd_text"])
    console.print(f"[cyan]ATS Score:[/] {score}%  |  Missing: {len(missing)} keywords")
    return {**state, "ats_score": score, "matched_keywords": matched, "missing_keywords": missing}


def node_vault_query(state: AgentState) -> AgentState:
    """Query the Career Vault for relevant chunks. Gracefully skips if vault is empty."""
    try:
        from career_ai.vault.query import query_vault
        chunks = query_vault(state["jd_text"])
    except Exception:
        chunks = []
    return {**state, "vault_chunks": chunks}


def node_generate_cv(state: AgentState) -> AgentState:
    config = load_config()
    vault_chunks = state.get("vault_chunks", [])
    extra_context = "\n\n--- ADDITIONAL CAREER CONTEXT ---\n" + "\n".join(vault_chunks) if vault_chunks else ""

    from career_ai.core.polisher import build_polish_prompt
    system, user = build_polish_prompt(state["cv_text"] + extra_context, "professional", state.get("role", "general"))
    try:
        cv_draft = call_llm(system, user, config)
        return {**state, "cv_draft": cv_draft}
    except Exception as exc:
        errors = state.get("errors", []) + [f"generate_cv: {exc}"]
        return {**state, "cv_draft": state["cv_text"], "errors": errors}


def node_generate_cover_letter(state: AgentState) -> AgentState:
    config = load_config()
    system, user = build_cover_letter_prompt(
        state.get("cv_draft", state["cv_text"]),
        state["jd_text"],
        "professional",
        config.app.max_cover_letter_words,
    )
    try:
        letter = call_llm(system, user, config)
        return {**state, "cover_letter_draft": letter}
    except Exception as exc:
        errors = state.get("errors", []) + [f"generate_cover_letter: {exc}"]
        return {**state, "cover_letter_draft": "", "errors": errors}


def node_generate_interview_prep(state: AgentState) -> AgentState:
    config = load_config()
    system, user = build_interview_prep_prompt(
        state.get("cv_draft", state["cv_text"]),
        state["jd_text"],
    )
    try:
        prep = call_llm(system, user, config)
        return {**state, "interview_prep": prep}
    except Exception as exc:
        errors = state.get("errors", []) + [f"generate_interview_prep: {exc}"]
        return {**state, "interview_prep": "", "errors": errors}


def node_summarise(state: AgentState) -> AgentState:
    company = state.get("company", "Company")
    role = state.get("role", "Role")
    out_dir = state.get("output_dir", f"output/{company}_{role}")
    console.print(f"\n[bold green]✓ Auto-Apply package ready:[/] {out_dir}")
    console.print(f"  ATS Score:      {state.get('ats_score', 'N/A')}%")
    console.print(f"  Missing KWs:    {len(state.get('missing_keywords', []))}")
    console.print(f"  CV:             {out_dir}/cv.md")
    console.print(f"  Cover Letter:   {out_dir}/cover_letter.md")
    console.print(f"  Interview Prep: {out_dir}/interview_prep.md")
    return state


def should_retry_extraction(state: AgentState) -> str:
    """Conditional edge: retry if JD extraction failed, else proceed."""
    if not state.get("jd_text") and state.get("retry_count", 0) < 1:
        return "retry"
    return "continue"


def node_fix_extraction(state: AgentState) -> AgentState:
    """Increment retry counter and re-attempt extraction with a cleaned URL."""
    console.print("[yellow]JD extraction failed, retrying...[/]")
    retry_count = state.get("retry_count", 0) + 1
    try:
        import requests
        from bs4 import BeautifulSoup
        resp = requests.get(state["jd_url"], timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(separator="\n")
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        jd_text = "\n".join(lines)
    except Exception as exc:
        jd_text = ""
        state = {**state, "errors": state.get("errors", []) + [f"fix_extraction: {exc}"]}
    return {**state, "jd_text": jd_text, "retry_count": retry_count}
