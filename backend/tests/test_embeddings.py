import httpx
import pytest

from app.config import settings
from app.services.embeddings import embed_texts, embed_query


def test_dim():
    v = embed_query("hello")
    assert len(v) == 384


def test_batch():
    vs = embed_texts(["a", "b"])
    assert len(vs) == 2 and all(len(v) == 384 for v in vs)


def test_api_provider_calls_hf_inference(monkeypatch):
    monkeypatch.setattr(settings, "embeddings_provider", "api")
    monkeypatch.setattr(settings, "hf_api_key", "fake-key")

    captured = {}

    def fake_post(url, headers, json, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        return httpx.Response(
            200, json=[[0.1] * 384, [0.2] * 384], request=httpx.Request("POST", url)
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    vs = embed_texts(["a", "b"])
    assert len(vs) == 2 and all(len(v) == 384 for v in vs)
    assert captured["headers"]["Authorization"] == "Bearer fake-key"
    assert captured["json"]["inputs"] == ["a", "b"]


def test_api_provider_requires_key(monkeypatch):
    monkeypatch.setattr(settings, "embeddings_provider", "api")
    monkeypatch.setattr(settings, "hf_api_key", "")

    with pytest.raises(RuntimeError):
        embed_texts(["a"])
