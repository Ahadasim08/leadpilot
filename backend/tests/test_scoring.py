import pytest

from app.models.schemas import Lead
from app.services import scoring


class _FakeProvider:
    def __init__(self, response: str):
        self.response = response
        self.calls = 0

    def generate(self, prompt: str) -> str:
        self.calls += 1
        return self.response

    def stream(self, prompt: str):
        yield self.response


def test_rule_short_circuits_llm(monkeypatch):
    fake = _FakeProvider("should never be called")
    monkeypatch.setattr(scoring, "get_provider", lambda: fake)

    lead = Lead(name="x", email="x@mailinator.com", message="buy backlinks cheap")
    result = scoring.score_lead(lead)

    assert result.rule_triggered == "spam_pattern"
    assert fake.calls == 0


def test_fence_wrapped_llm_output_parses(monkeypatch):
    fenced = '```json\n{"verdict":"hot","score":88,"reasons":["explicit budget"],"missing_info":[]}\n```'
    fake = _FakeProvider(fenced)
    monkeypatch.setattr(scoring, "get_provider", lambda: fake)

    lead = Lead(
        name="Sarah",
        email="sarah@realco.com",
        message="We need Google Ads, budget $3k/month, can we talk this week?",
        budget="$3k/month",
    )
    result = scoring.score_lead(lead)

    assert result.verdict == "hot"
    assert result.score == 88
    assert result.rule_triggered is None
    assert fake.calls == 1


def test_double_parse_failure_raises_502(monkeypatch):
    from fastapi import HTTPException

    fake = _FakeProvider("not json at all")
    monkeypatch.setattr(scoring, "get_provider", lambda: fake)

    lead = Lead(name="Sarah", email="sarah@realco.com", message="We need Google Ads help please")
    with pytest.raises(HTTPException) as exc_info:
        scoring.score_lead(lead)

    assert exc_info.value.status_code == 502
    assert fake.calls == 2
