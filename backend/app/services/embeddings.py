from app.config import settings

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _embed_texts_local(texts: list[str]) -> list[list[float]]:
    vecs = _get_model().encode(texts, normalize_embeddings=True)
    return [v.tolist() for v in vecs]


def _embed_texts_api(texts: list[str]) -> list[list[float]]:
    raise NotImplementedError(
        "EMBEDDINGS_PROVIDER=api not implemented — only needed if Render OOMs on local model."
    )


def embed_texts(texts: list[str]) -> list[list[float]]:
    if settings.embeddings_provider == "api":
        return _embed_texts_api(texts)
    return _embed_texts_local(texts)


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
