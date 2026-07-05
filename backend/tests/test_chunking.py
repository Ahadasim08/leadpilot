from app.services.chunking import chunk_text


def test_chunks_respect_size():
    text = " ".join(str(i) for i in range(1200))
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    assert all(len(c.split()) <= 500 for c in chunks)
    assert len(chunks) >= 3


def test_overlap_present():
    text = " ".join(str(i) for i in range(1000))
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    tail = chunks[0].split()[-50:]
    head = chunks[1].split()[:50]
    assert tail == head


def test_no_empty_chunks():
    assert chunk_text("", 500, 50) == []
    assert all(c.strip() for c in chunk_text("hello world", 500, 50))
