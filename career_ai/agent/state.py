from __future__ import annotations

from typing import TypedDict


class AgentState(TypedDict, total=False):
    # Inputs
    cv_text: str
    jd_url: str
    company: str
    role: str
    output_dir: str

    # Pipeline outputs
    jd_text: str
    ats_score: float
    matched_keywords: list[str]
    missing_keywords: list[str]
    vault_chunks: list[str]
    cv_draft: str
    cover_letter_draft: str
    interview_prep: str

    # Control
    errors: list[str]
    retry_count: int
