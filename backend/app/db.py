"""
Supabase DB wrappers — all sync, thin over the supabase-py client.

The module-level `_client` variable is intentionally exposed so tests can
monkeypatch it without touching real Supabase credentials.
"""
from __future__ import annotations

from supabase import create_client, Client

from app.config import settings

# Lazy singleton — tests monkeypatch this directly.
_client: Client | None = None


def _get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_key)
    return _client


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------

def insert_document(filename: str, file_type: str) -> dict:
    """Insert a new document row. Returns the created row."""
    row = {"filename": filename, "file_type": file_type}
    return _get_client().table("documents").insert(row).execute().data[0]


def list_documents() -> list[dict]:
    """Return all document rows ordered by creation time (newest first)."""
    return (
        _get_client()
        .table("documents")
        .select("*")
        .order("created_at", desc=True)
        .execute()
        .data
    )


# ---------------------------------------------------------------------------
# Chunks
# ---------------------------------------------------------------------------

def insert_chunks(rows: list[dict]) -> None:
    """Bulk-insert chunk rows.

    Each row should contain:
      document_id, content, chunk_index, embedding
    """
    if not rows:
        return
    _get_client().table("chunks").insert(rows).execute()


def match_chunks(
    query_embedding: list[float],
    match_count: int = 4,
    similarity_threshold: float = 0.35,
) -> list[dict]:
    """Call the Postgres `match_chunks` RPC and return matches above threshold."""
    return (
        _get_client()
        .rpc(
            "match_chunks",
            {
                "query_embedding": "[" + ",".join(str(v) for v in query_embedding) + "]",
                "match_count": match_count,
                "similarity_threshold": similarity_threshold,
            },
        )
        .execute()
        .data
    )
