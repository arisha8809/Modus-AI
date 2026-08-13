"""Pydantic models defining the API's request/response shapes."""

from datetime import datetime
from pydantic import BaseModel


class NewResearchRequest(BaseModel):
    question: str


class TopicSummary(BaseModel):
    id: int
    question: str
    domain: str | None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class PipelineEventOut(BaseModel):
    stage: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


class FindingOut(BaseModel):
    id: int
    claim: str
    detail: str | None
    classification: str
    source_url: str

    class Config:
        from_attributes = True


class ConclusionOut(BaseModel):
    id: int
    text: str
    findings: list[FindingOut]

    class Config:
        from_attributes = True


class TopicDetail(BaseModel):
    id: int
    question: str
    domain: str | None
    status: str
    conclusions: list[ConclusionOut]
    events: list[PipelineEventOut]

    class Config:
        from_attributes = True
