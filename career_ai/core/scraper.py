from __future__ import annotations


def scrape_url(url: str) -> str:
    """Fetch and extract main text content from a job posting URL."""
    try:
        import trafilatura

        downloaded = trafilatura.fetch_url(url)
        text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        if text and text.strip():
            return text.strip()
    except ImportError:
        pass

    # Fallback: beautifulsoup4
    import requests
    from bs4 import BeautifulSoup

    resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "header", "footer", "nav"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines)
