from __future__ import annotations

import re

from app.models.schemas import Lead, ScoreResponse

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_SPAM_SUBSTRINGS = [
    "buy backlinks",
    "guest post",
    "seo packages",
    "crypto",
    "loan offer",
    "increase your ranking",
    "viagra",
]

_DISPOSABLE_DOMAINS = {
    "mailinator.com",
    "tempmail.com",
    "guerrillamail.com",
    "10minutemail.com",
}


def apply_hard_rules(lead: Lead) -> ScoreResponse | None:
    """Pure, I/O-free hard rules. Returns a ScoreResponse if a rule fires, else None."""
    if not _EMAIL_RE.match(lead.email):
        return ScoreResponse(
            verdict="spam",
            score=0,
            reasons=["invalid email address"],
            missing_info=[],
            rule_triggered="invalid_email",
        )

    if len(lead.message.strip()) < 10:
        return ScoreResponse(
            verdict="spam",
            score=0,
            reasons=["message too short"],
            missing_info=[],
            rule_triggered="message_too_short",
        )

    message_lower = lead.message.lower()
    if any(s in message_lower for s in _SPAM_SUBSTRINGS):
        return ScoreResponse(
            verdict="spam",
            score=0,
            reasons=["matched known spam pattern"],
            missing_info=[],
            rule_triggered="spam_pattern",
        )

    domain = lead.email.rsplit("@", 1)[-1].lower()
    if domain in _DISPOSABLE_DOMAINS:
        return ScoreResponse(
            verdict="cold",
            score=20,
            reasons=["disposable email domain"],
            missing_info=[],
            rule_triggered="disposable_email",
        )

    return None
