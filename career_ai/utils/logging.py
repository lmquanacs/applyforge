from __future__ import annotations

import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console

console = Console()


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.execute(
        """CREATE TABLE IF NOT EXISTS usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT, model TEXT,
            prompt_tokens INTEGER, completion_tokens INTEGER,
            total_tokens INTEGER, cost_usd REAL
        )"""
    )
    con.execute(
        """CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            ts TEXT,
            role TEXT,
            content TEXT
        )"""
    )
    con.commit()
    return con


def log_usage(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    cost: float,
    db_path: Path,
) -> None:
    con = _connect(db_path)
    con.execute(
        "INSERT INTO usage (ts, model, prompt_tokens, completion_tokens, total_tokens, cost_usd) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (datetime.now(timezone.utc).isoformat(), model, prompt_tokens, completion_tokens, total_tokens, cost),
    )
    con.commit()
    con.close()
    console.print(
        f"[dim]Tokens used: {total_tokens} (prompt={prompt_tokens}, "
        f"completion={completion_tokens}) | Cost: ${cost:.4f}[/]"
    )


def append_chat_message(session_id: str, role: str, content: str, db_path: Path) -> None:
    con = _connect(db_path)
    con.execute(
        "INSERT INTO sessions (session_id, ts, role, content) VALUES (?, ?, ?, ?)",
        (session_id, datetime.now(timezone.utc).isoformat(), role, content),
    )
    con.commit()
    con.close()


def load_chat_history(session_id: str, db_path: Path) -> list[dict]:
    con = _connect(db_path)
    rows = con.execute(
        "SELECT role, content FROM sessions WHERE session_id = ? ORDER BY id",
        (session_id,),
    ).fetchall()
    con.close()
    return [{"role": r, "content": c} for r, c in rows]


def clear_chat_history(db_path: Path) -> int:
    con = _connect(db_path)
    count = con.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    con.execute("DELETE FROM sessions")
    con.commit()
    con.close()
    return count


def drop_all(db_path: Path) -> None:
    con = _connect(db_path)
    con.execute("DROP TABLE IF EXISTS usage")
    con.execute("DROP TABLE IF EXISTS sessions")
    con.commit()
    con.close()
