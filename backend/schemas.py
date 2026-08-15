from datetime import datetime
from pydantic import BaseModel, Field


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
    source_title: str | None = None
    source_domain: str | None = None
    source_published_date: str | None = None
    source_type: str | None = None

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


class TrendPointOut(BaseModel):
    year: int
    source_count: int
    finding_count: int
    corroborated_count: int
    contested_count: int
    single_source_count: int


class TimelineEventOut(BaseModel):
    id: int
    event_date: str
    title: str
    description: str | None
    event_type: str
    impact_level: str
    impact_rationale: str | None
    source_url: str
    source_title: str | None = None
    source_domain: str | None = None


class TopicAnalyticsOut(BaseModel):
    """Decision-oriented aggregates derived from stored sources and findings.

    Timeline values are returned only for sources with a publisher date; the
    UI must never imply a historical trend from retrieval timestamps.
    """
    dated_source_count: int
    undated_source_count: int
    date_coverage_percent: float
    timeline_event_count: int
    source_type_counts: dict[str, int] = Field(default_factory=dict)
    source_domain_counts: list[dict] = Field(default_factory=list)
    timeline: list[TrendPointOut] = Field(default_factory=list)
    timeline_events: list[TimelineEventOut] = Field(default_factory=list)
    sub_question_breakdown: list[dict] = Field(default_factory=list)
    decision_signals: dict[str, list[str]] = Field(default_factory=dict)


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
    analytics: TopicAnalyticsOut
    conclusions: list[ConclusionOut]
    contradictions: list[ContradictionOut]
    findings_by_sub_question: list[SubQuestionFindingsOut]
    events: list[PipelineEventOut]

    class Config:
        from_attributes = True
