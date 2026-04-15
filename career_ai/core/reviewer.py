from __future__ import annotations

_SYSTEM_PROMPT = """\
You are an expert career coach and ATS specialist. Your task is to review the provided CV \
and return a structured Markdown report.

Rules:
- Do NOT invent or infer any information not present in the CV.
- Base every observation strictly on the text provided.

Output format (Markdown):
## Overall Score
X/100

## Strengths
- ...

## Weaknesses / Gaps
- ...

## Actionable Revisions
- [Original bullet] → [Suggested rewrite]
"""


def build_review_prompt(cv_text: str) -> tuple[str, str]:
    user = f"Here is the CV to review:\n\n{cv_text}"
    return _SYSTEM_PROMPT, user
