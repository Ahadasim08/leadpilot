def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    tokens = text.split()
    if not tokens:
        return []
    step = max(1, chunk_size - overlap)
    chunks = []
    for start in range(0, len(tokens), step):
        window = tokens[start:start + chunk_size]
        if window:
            chunks.append(" ".join(window))
        if start + chunk_size >= len(tokens):
            break
    return chunks
