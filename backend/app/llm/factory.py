from app.config import settings
from app.llm.base import LLMProvider
from app.llm.groq import GroqProvider


def get_provider() -> LLMProvider:
    if settings.llm_provider == "groq":
        return GroqProvider()
    raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")
