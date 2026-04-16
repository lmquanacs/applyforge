from __future__ import annotations

import re


def _tokenize(text: str) -> set[str]:
    """Lowercase, strip punctuation, return unique word tokens (2+ chars)."""
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.]*", text.lower())
    stopwords = {
        "and", "the", "for", "with", "that", "this", "are", "you", "our",
        "will", "have", "has", "from", "your", "not", "but", "all", "can",
        "we", "be", "to", "of", "in", "a", "an", "is", "it", "as", "at",
        "by", "or", "on", "do", "if", "so", "up", "us", "its", "their",
        "they", "them", "who", "what", "how", "when", "where", "which",
        "about", "into", "than", "more", "also", "any", "each", "both",
        "other", "such", "over", "well", "just", "been", "were", "was",
    }
    return {t for t in tokens if len(t) >= 2 and t not in stopwords}


def ats_score(cv_text: str, jd_text: str) -> tuple[float, list[str], list[str]]:
    """
    Returns (match_pct, matched_keywords, missing_keywords).
    Pure local computation — zero API cost.
    """
    jd_keywords = _tokenize(jd_text)
    cv_tokens = _tokenize(cv_text)

    matched = sorted(jd_keywords & cv_tokens)
    missing = sorted(jd_keywords - cv_tokens)

    pct = (len(matched) / len(jd_keywords) * 100) if jd_keywords else 0.0
    return round(pct, 1), matched, missing
