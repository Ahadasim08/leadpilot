import httpx

from app.config import settings

_HF_API_URL = (
    "https://api-inference.huggingface.co/pipeline/feature-extraction/"
    "sentence-transformers/all-MiniLM-L6-v2"
)

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
    if not settings.hf_api_key:
        raise RuntimeError("HF_API_KEY is required when EMBEDDINGS_PROVIDER=api")
    resp = httpx.post(
        _HF_API_URL,
        headers={"Authorization": f"Bearer {settings.hf_api_key}"},
        json={"inputs": texts, "options": {"wait_for_model": True}},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def embed_texts(texts: list[str]) -> list[list[float]]:
    if settings.embeddings_provider == "api":
        return _embed_texts_api(texts)
    return _embed_texts_local(texts)


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
