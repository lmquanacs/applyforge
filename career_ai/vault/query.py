from __future__ import annotations

from sentence_transformers import SentenceTransformer

from career_ai.vault.ingest import _get_collection, _MODEL_NAME

_TOP_K = 8


def query_vault(jd_text: str, top_k: int = _TOP_K) -> list[str]:
    """Return the most relevant career vault chunks for a given JD."""
    collection = _get_collection()
    if collection.count() == 0:
        return []

    model = SentenceTransformer(_MODEL_NAME)
    embedding = model.encode([jd_text]).tolist()

    results = collection.query(query_embeddings=embedding, n_results=min(top_k, collection.count()))
    return results["documents"][0] if results["documents"] else []
