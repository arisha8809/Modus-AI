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


class ContradictionOut(BaseModel):
    id: int
    explanation: str | None
    finding_a: FindingOut
    finding_b: FindingOut

    class Config:
        from_attributes = True


class TopicStats(BaseModel):
    """Aggregate counts for the topic -- what makes results demonstrable as
    structured data (numbers, breakdowns) rather than a paragraph summary."""
    sub_question_count: int
    source_count: int
    finding_count: int
    corroborated_count: int
    contested_count: int
    single_source_count: int
    contradiction_count: int
    conclusion_count: int


class SubQuestionFindingsOut(BaseModel):
    """All findings for one sub-question -- used to show the full findings
    table, not just the subset that ended up cited in a conclusion."""
    sub_question: str
    findings: list[FindingOut]


class TopicDetail(BaseModel):
    id: int
    question: str
    domain: str | None
    status: str
    stats: TopicStats
    conclusions: list[ConclusionOut]
    contradictions: list[ContradictionOut]
    findings_by_sub_question: list[SubQuestionFindingsOut]
    events: list[PipelineEventOut]

    class Config:
        from_attributes = True
