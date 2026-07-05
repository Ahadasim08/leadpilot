from __future__ import annotations

from app.config import settings
from app.llm.factory import get_provider
from app.llm.json_call import call_json
from app.models.schemas import Lead, ScoreResponse
from app.rules import apply_hard_rules

_SYSTEM_PROMPT = """You are a lead-qualification engine for {agency_name}, a digital marketing agency
offering: PPC/Google Ads, SEO, web design, social media management.
Return ONLY a JSON object, no markdown, no prose:
{{"verdict":"hot|warm|cold|spam","score":<0-100>,"reasons":[...],"missing_info":[...]}}
Rules: hot = clear service fit AND (budget signal OR urgency). warm = service fit, vague on
budget/timing. cold = unclear fit or mismatched need. spam = promotional/irrelevant."""

_USER_PROMPT = """Name: {name}
Email: {email}
Company: {company}
Budget: {budget}
Message: {message}"""


def _build_prompt(lead: Lead) -> str:
    system = _SYSTEM_PROMPT.format(agency_name=settings.agency_name)
    user = _USER_PROMPT.format(
        name=lead.name,
        email=lead.email,
        company=lead.company or "",
        budget=lead.budget or "",
        message=lead.message,
    )
    return f"{system}\n\n{user}"


def score_lead(lead: Lead) -> ScoreResponse:
    rule_result = apply_hard_rules(lead)
    if rule_result is not None:
        return rule_result

    prompt = _build_prompt(lead)
    data = call_json(get_provider(), prompt)

    score = max(0, min(100, int(data["score"])))
    return ScoreResponse(
        verdict=data["verdict"],
        score=score,
        reasons=data.get("reasons", []),
        missing_info=data.get("missing_info", []),
        rule_triggered=None,
    )
