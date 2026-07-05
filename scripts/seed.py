"""
Seed Supabase with the Acme demo docs (data/acme/*.md): parse -> chunk -> embed -> insert.

Usage:
    cd backend && python ../scripts/seed.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app import db
from app.services.chunking import chunk_text
from app.services.embeddings import embed_texts

DATA_DIR = Path(__file__).parent.parent / "data" / "acme"


def seed():
    md_files = sorted(DATA_DIR.glob("*.md"))
    if not md_files:
        print(f"No .md files found in {DATA_DIR}")
        sys.exit(1)

    for path in md_files:
        text = path.read_text(encoding="utf-8")
        print(f"Ingesting {path.name}...")

        doc = db.insert_document(filename=path.name, file_type="md")
        doc_id = doc["id"]

        chunks = chunk_text(text)
        if not chunks:
            print(f"  no chunks produced, skipping")
            continue

        embeddings = embed_texts(chunks)
        rows = [
            {
                "document_id": doc_id,
                "content": chunk,
                "chunk_index": i,
                "embedding": "[" + ",".join(str(v) for v in emb) + "]",
            }
            for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
        ]
        db.insert_chunks(rows)
        print(f"  inserted {len(rows)} chunks")

    print("Seed complete.")


if __name__ == "__main__":
    seed()
