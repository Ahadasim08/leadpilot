from app.models.schemas import Lead
from app.rules import apply_hard_rules


def _lead(**kwargs):
    defaults = dict(name="Sarah", email="sarah@realco.com", message="We need help with Google Ads")
    defaults.update(kwargs)
    return Lead(**defaults)


def test_invalid_email():
    result = apply_hard_rules(_lead(email="not-an-email"))
    assert result.verdict == "spam"
    assert result.rule_triggered == "invalid_email"


def test_message_too_short():
    result = apply_hard_rules(_lead(message="hi"))
    assert result.verdict == "spam"
    assert result.rule_triggered == "message_too_short"


def test_spam_pattern():
    result = apply_hard_rules(_lead(message="buy backlinks cheap"))
    assert result.verdict == "spam"
    assert result.rule_triggered == "spam_pattern"


def test_disposable_email():
    result = apply_hard_rules(_lead(email="x@mailinator.com"))
    assert result.verdict == "cold"
    assert result.rule_triggered == "disposable_email"


def test_pass_through():
    result = apply_hard_rules(_lead())
    assert result is None
