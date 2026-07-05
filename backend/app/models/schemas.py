from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Lead(BaseModel):
    name: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    company: str | None = None
    budget: str | None = None


class ScoreResponse(BaseModel):
    verdict: Literal["hot", "warm", "cold", "spam"]
    score: int = Field(..., ge=0, le=100)
    reasons: list[str] = Field(default_factory=list)
    missing_info: list[str] = Field(default_factory=list)
    rule_triggered: str | None = None


class DraftRequest(BaseModel):
    lead: Lead
    mode: Literal["reply", "followup"]


class SourceUsed(BaseModel):
    doc: str
    chunk_id: str


class DraftResponse(BaseModel):
    subject: str
    body: str
    sources_used: list[SourceUsed] = Field(default_factory=list)
    low_context: bool = False
