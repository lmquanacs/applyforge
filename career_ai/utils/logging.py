from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console

console = Console()


def log_usage(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    cost: float,
    db_path: Path,
) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.execute(
        """CREATE TABLE IF NOT EXISTS usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT,
            model TEXT,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            total_tokens INTEGER,
            cost_usd REAL
        )"""
    )
    con.execute(
        "INSERT INTO usage (ts, model, prompt_tokens, completion_tokens, total_tokens, cost_usd) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            datetime.now(timezone.utc).isoformat(),
            model,
            prompt_tokens,
            completion_tokens,
            total_tokens,
            cost,
        ),
    )
    con.commit()
    con.close()

    console.print(
        f"[dim]Tokens used: {total_tokens} (prompt={prompt_tokens}, "
        f"completion={completion_tokens}) | Cost: ${cost:.4f}[/]"
    )
