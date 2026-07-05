from __future__ import annotations

from app import db
from app.services.embeddings import embed_query


def retrieve_chunks(query: str, match_count: int = 4, similarity_threshold: float = 0.35) -> list[dict]:
    """Embed the query and fetch matching chunks above threshold."""
    return db.match_chunks(embed_query(query), match_count, similarity_threshold)
