from typing import Iterator, Optional
from groq import Groq
from app.config import settings
from app.llm.base import LLMProvider


class GroqProvider(LLMProvider):
    def __init__(self):
        self.model = settings.groq_model
        self._client: Optional[Groq] = None

    def _get_client(self) -> Groq:
        if self._client is None:
            self._client = Groq(api_key=settings.groq_api_key)
        return self._client

    def generate(self, prompt: str) -> str:
        response = self._get_client().chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""

    def stream(self, prompt: str) -> Iterator[str]:
        stream = self._get_client().chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )
        for chunk in stream:
            text = chunk.choices[0].delta.content
            if text:
                yield text
