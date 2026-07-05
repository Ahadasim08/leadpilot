from __future__ import annotations

from app.config import settings
from app.llm.factory import get_provider
from app.llm.json_call import call_json
from app.models.schemas import DraftRequest, DraftResponse, SourceUsed
from app.services.retrieval import retrieve_chunks

_SYSTEM_PROMPT = """You write replies to inbound leads on behalf of {agency_name}.
Use ONLY the facts in CONTEXT. Never invent services, prices, or timelines.
If CONTEXT lacks something the lead asked, say a specialist will confirm it.
Mode "reply": respond to the inquiry, reference their need, propose a short call. Under 150 words.
Mode "followup": polite nudge referencing their original message, one line of value, re-offer the call. Under 80 words.
Return ONLY JSON: {{"subject":"...","body":"..."}}"""

_USER_PROMPT = """MODE: {mode}
CONTEXT:
{chunks}
LEAD MESSAGE:
{message}
LEAD NAME: {name}"""


def _build_prompt(request: DraftRequest, chunks: list[dict]) -> str:
    system = _SYSTEM_PROMPT.format(agency_name=settings.agency_name)
    context = "\n\n".join(c["content"] for c in chunks)
    user = _USER_PROMPT.format(
        mode=request.mode,
        chunks=context,
        message=request.lead.message,
        name=request.lead.name,
    )
    return f"{system}\n\n{user}"


def _generic_ack(lead_name: str) -> DraftResponse:
    return DraftResponse(
        subject="Thanks for reaching out",
        body=(
            f"Hi {lead_name},\n\n"
            "Thanks for your message — we've received it and a specialist will follow up "
            "shortly to confirm details and next steps.\n\nBest,\nThe Team"
        ),
        sources_used=[],
        low_context=True,
    )


def draft_message(request: DraftRequest) -> DraftResponse:
    chunks = retrieve_chunks(request.lead.message)
    if not chunks:
        return _generic_ack(request.lead.name)

    prompt = _build_prompt(request, chunks)
    data = call_json(get_provider(), prompt)

    sources_used = [
        SourceUsed(doc=c.get("filename", ""), chunk_id=str(c.get("id", "")))
        for c in chunks
    ]
    return DraftResponse(
        subject=data["subject"],
        body=data["body"],
        sources_used=sources_used,
        low_context=False,
    )
