from app.services.embeddings import embed_texts, embed_query


def test_dim():
    v = embed_query("hello")
    assert len(v) == 384


def test_batch():
    vs = embed_texts(["a", "b"])
    assert len(vs) == 2 and all(len(v) == 384 for v in vs)
