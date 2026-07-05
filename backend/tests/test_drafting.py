from app.models.schemas import DraftRequest, Lead
from app.services import drafting


class _FakeProvider:
    def __init__(self, response: str):
        self.response = response

    def generate(self, prompt: str) -> str:
        return self.response

    def stream(self, prompt: str):
        yield self.response


def test_empty_retrieval_returns_generic_ack(monkeypatch):
    monkeypatch.setattr(drafting, "retrieve_chunks", lambda message: [])

    request = DraftRequest(
        lead=Lead(name="Sarah", email="sarah@realco.com", message="Need help with Google Ads"),
        mode="reply",
    )
    result = drafting.draft_message(request)

    assert result.low_context is True
    assert result.sources_used == []
    assert "Sarah" in result.body


def test_retrieval_hit_uses_context_and_attaches_sources(monkeypatch):
    chunks = [
        {"id": "c_12", "document_id": "d_1", "filename": "pricing.md", "content": "PPC starts at $2.5k/mo"},
    ]
    monkeypatch.setattr(drafting, "retrieve_chunks", lambda message: chunks)

    fake = _FakeProvider('{"subject":"Re: your inquiry","body":"Here is our PPC pricing..."}')
    monkeypatch.setattr(drafting, "get_provider", lambda: fake)

    request = DraftRequest(
        lead=Lead(name="Sarah", email="sarah@realco.com", message="What does PPC cost?"),
        mode="reply",
    )
    result = drafting.draft_message(request)

    assert result.low_context is False
    assert result.sources_used[0].doc == "pricing.md"
    assert result.sources_used[0].chunk_id == "c_12"
