from __future__ import annotations

import json
import re

from fastapi import HTTPException

from app.llm.base import LLMProvider

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def _strip_fences(text: str) -> str:
    return _FENCE_RE.sub("", text).strip()


def call_json(provider: LLMProvider, prompt: str) -> dict:
    """Call the LLM, strip ```json fences, parse. One retry on failure, then 502."""
    for _ in range(2):
        raw = provider.generate(prompt)
        try:
            return json.loads(_strip_fences(raw))
        except json.JSONDecodeError:
            continue
    raise HTTPException(status_code=502, detail="LLM returned invalid JSON")
