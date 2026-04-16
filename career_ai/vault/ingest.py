from __future__ import annotations

from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from career_ai.core.extractor import extract

_COLLECTION = "career_vault"
_CHUNK_SIZE = 400  # characters
_MODEL_NAME = "all-MiniLM-L6-v2"


def _get_collection():
    db_dir = Path.home() / ".config" / "career-ai" / "vault"
    db_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(db_dir))
    return client.get_or_create_collection(_COLLECTION)


def _chunk(text: str) -> list[str]:
    words = text.split()
    chunks, current = [], []
    length = 0
    for word in words:
        current.append(word)
        length += len(word) + 1
        if length >= _CHUNK_SIZE:
            chunks.append(" ".join(current))
            current, length = [], 0
    if current:
        chunks.append(" ".join(current))
    return chunks


def ingest(file_path: str | Path) -> int:
    """Extract, chunk, embed, and store a document. Returns number of chunks added."""
    path = Path(file_path)
    text = extract(path)
    chunks = _chunk(text)

    model = SentenceTransformer(_MODEL_NAME)
    embeddings = model.encode(chunks).tolist()

    collection = _get_collection()
    ids = [f"{path.stem}_{i}" for i in range(len(chunks))]
    collection.upsert(ids=ids, documents=chunks, embeddings=embeddings)
    return len(chunks)


def clear_vault() -> None:
    """Drop all documents from the vault collection."""
    collection = _get_collection()
    all_ids = collection.get()["ids"]
    if all_ids:
        collection.delete(ids=all_ids)
