"""API routes: submit new research, poll status, fetch results, browse/search
 the accumulated knowledge base.
"""

from collections import Counter, defaultdict
from datetime import datetime
import re
from urllib.parse import urlparse

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db.session import get_session
from ..db.models import ResearchTopic
from ..db import vector_store
from ..agents.orchestrator import run_pipeline
from ..schemas import (
    NewResearchRequest,
    TopicSummary,
    TopicDetail,
    TopicStats,
    TopicAnalyticsOut,
    TrendPointOut,
    TimelineEventOut,
    ConclusionOut,
    ContradictionOut,
    FindingOut,
    PipelineEventOut,
    SubQuestionFindingsOut,
)

router = APIRouter()


def _source_domain(url: str) -> str:
    host = (urlparse(url or "").netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return host or "unknown source"


def _source_type(url: str) -> str:
    """Classify source provenance deterministically from its domain.

    This is deliberately a transparent heuristic, not an LLM judgment. It is
    presented as a source profile in the UI, not as a claim about source truth.
    """
    domain = _source_domain(url)
    if domain.endswith(".gov") or domain.startswith("gov.") or ".gov." in domain or domain.endswith(".gov.uk"):
        return "Government / public sector"
    if domain.endswith(".edu") or domain.startswith("edu.") or ".edu." in domain or domain.endswith(".ac.uk"):
        return "Academic / research"
    if any(token in domain for token in ("reuters", "ft.com", "economist", "forbes", "wsj", "bloomberg", "bbc", "nytimes")):
        return "News / analysis"
    if any(token in domain for token in ("ibm", "microsoft", "google", "aws", "oracle", "salesforce", "deloitte", "accenture", "mckinsey", "pwc", "gartner")):
        return "Vendor / industry"
    return "General web"


def _published_year(value: str | None) -> int | None:
    if not value:
        return None
    match = re.search(r"\b(19|20)\d{2}\b", str(value))
    if not match:
        return None
    year = int(match.group(0))
    current_year = datetime.utcnow().year
    return year if 1990 <= year <= current_year + 1 else None


def _finding_out(f):
    source = f.source
    return FindingOut(
        id=f.id,
        claim=f.claim,
        detail=f.detail,
        classification=f.classification,
        source_url=source.url,
        source_title=source.title,
        source_domain=_source_domain(source.url),
        source_published_date=source.published_date,
        source_type=_source_type(source.url),
    )


def _run_pipeline_in_background(topic_id: int):
    # BackgroundTasks doesn't share the request's DB session (it's already
    # closed by the time this runs), so open a fresh one for the pipeline.
    from ..db.session import SessionLocal

    db = SessionLocal()
    try:
        run_pipeline(topic_id, db)
    finally:
        db.close()


@router.post("/research", response_model=TopicSummary)
def start_research(req: NewResearchRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_session)):
    """Submit a new research question. This is the endpoint the 'surprise
    record' live test hits: any question, any domain, no prior setup."""
    if not req.question or not req.question.strip():
        raise HTTPException(400, "question must not be empty")

    topic = ResearchTopic(question=req.question.strip())
    db.add(topic)
    db.commit()
    db.refresh(topic)

    background_tasks.add_task(_run_pipeline_in_background, topic.id)
    return topic


@router.get("/research", response_model=list[TopicSummary])
def list_research(db: Session = Depends(get_session)):
    """All research topics ever run -- the reusable knowledge base index."""
    return db.query(ResearchTopic).order_by(ResearchTopic.created_at.desc()).all()


@router.get("/research/{topic_id}", response_model=TopicDetail)
def get_research(topic_id: int, db: Session = Depends(get_session)):
    """Full detail for one topic, including the evidence dossier and
    decision-oriented analytics derived from its stored research graph."""
    topic = db.get(ResearchTopic, topic_id)
    if topic is None:
        raise HTTPException(404, "topic not found")

    conclusions_out = [
        ConclusionOut(
            id=conclusion.id,
            text=conclusion.text,
            findings=[_finding_out(finding) for finding in conclusion.findings],
        )
        for conclusion in topic.conclusions
    ]
    contradictions_out = [
        ContradictionOut(
            id=contradiction.id,
            explanation=contradiction.explanation,
            finding_a=_finding_out(contradiction.finding_a),
            finding_b=_finding_out(contradiction.finding_b),
        )
        for contradiction in topic.contradictions
    ]
    events_out = [
        PipelineEventOut(stage=event.stage, message=event.message, created_at=event.created_at)
        for event in sorted(topic.pipeline_events, key=lambda event: event.created_at)
    ]

    findings_by_sub_question = []
    all_findings = []
    source_count = 0
    dated_source_count = 0
    source_type_counts: Counter[str] = Counter()
    source_domain_counts: Counter[str] = Counter()
    timeline = defaultdict(
        lambda: {
            "source_count": 0,
            "finding_count": 0,
            "corroborated_count": 0,
            "contested_count": 0,
            "single_source_count": 0,
        }
    )
    sub_question_breakdown = []
    timeline_events_out = []

    for sub_question in topic.sub_questions:
        sub_question_findings = []
        sub_question_sources = 0
        sub_question_classifications: Counter[str] = Counter()

        for source in sub_question.sources:
            source_count += 1
            sub_question_sources += 1
            source_type_counts[_source_type(source.url)] += 1
            source_domain_counts[_source_domain(source.url)] += 1
            year = _published_year(source.published_date)
            for event in source.timeline_events:
                timeline_events_out.append(
                    TimelineEventOut(
                        id=event.id,
                        event_date=event.event_date,
                        title=event.title,
                        description=event.description,
                        event_type=event.event_type,
                        impact_level=event.impact_level,
                        impact_rationale=event.impact_rationale,
                        source_url=source.url,
                        source_title=source.title,
                        source_domain=_source_domain(source.url),
                    )
                )
            if year is not None:
                dated_source_count += 1
                timeline[year]["source_count"] += 1

            for finding in source.findings:
                sub_question_findings.append(_finding_out(finding))
                all_findings.append(finding)
                classification = finding.classification or "single_source"
                sub_question_classifications[classification] += 1
                if year is not None:
                    timeline[year]["finding_count"] += 1
                    timeline[year][f"{classification}_count"] += 1

        sub_question_breakdown.append(
            {
                "sub_question": sub_question.text,
                "source_count": sub_question_sources,
                "finding_count": len(sub_question_findings),
                "corroborated_count": sub_question_classifications["corroborated"],
                "contested_count": sub_question_classifications["contested"],
                "single_source_count": sub_question_classifications["single_source"],
            }
        )
        findings_by_sub_question.append(
            SubQuestionFindingsOut(sub_question=sub_question.text, findings=sub_question_findings)
        )

    stats = TopicStats(
        sub_question_count=len(topic.sub_questions),
        source_count=source_count,
        finding_count=len(all_findings),
        corroborated_count=sum(1 for finding in all_findings if finding.classification == "corroborated"),
        contested_count=sum(1 for finding in all_findings if finding.classification == "contested"),
        single_source_count=sum(1 for finding in all_findings if finding.classification == "single_source"),
        contradiction_count=len(topic.contradictions),
        conclusion_count=len(topic.conclusions),
    )

    strongest_topics = sorted(
        sub_question_breakdown,
        key=lambda row: (row["corroborated_count"], row["finding_count"]),
        reverse=True,
    )
    review_topics = sorted(
        [row for row in sub_question_breakdown if row["contested_count"] > 0],
        key=lambda row: row["contested_count"],
        reverse=True,
    )
    coverage_gaps = [
        row["sub_question"]
        for row in sub_question_breakdown
        if row["finding_count"] == 0 or row["corroborated_count"] == 0
    ]

    timeline_events_out.sort(
        key=lambda event: (_published_year(event.event_date) or 9999, event.event_date, event.id)
    )

    analytics = TopicAnalyticsOut(
        dated_source_count=dated_source_count,
        undated_source_count=max(source_count - dated_source_count, 0),
        date_coverage_percent=round((dated_source_count / source_count) * 100, 1) if source_count else 0.0,
        timeline_event_count=len(timeline_events_out),
        source_type_counts=dict(source_type_counts),
        source_domain_counts=[
            {"domain": domain, "count": count}
            for domain, count in source_domain_counts.most_common(12)
        ],
        timeline=[
            TrendPointOut(year=year, **values)
            for year, values in sorted(timeline.items())
        ],
        timeline_events=timeline_events_out,
        sub_question_breakdown=sub_question_breakdown,
        decision_signals={
            "strongest_evidence": [row["sub_question"] for row in strongest_topics[:3] if row["finding_count"]],
            "needs_review": [row["sub_question"] for row in review_topics[:3]],
            "coverage_gaps": coverage_gaps[:3],
        },
    )

    return TopicDetail(
        id=topic.id,
        question=topic.question,
        domain=topic.domain,
        status=topic.status,
        stats=stats,
        analytics=analytics,
        conclusions=conclusions_out,
        contradictions=contradictions_out,
        findings_by_sub_question=findings_by_sub_question,
        events=events_out,
    )


@router.get("/knowledge-base/search")
def search_knowledge_base(q: str, limit: int = 8):
    """Semantic search across every finding ever extracted, from any past
    research run. This makes the knowledge base reusable rather than a fresh
    scratchpad per query."""
    if not q.strip():
        raise HTTPException(400, "q must not be empty")
    results = vector_store.query_findings(q, n_results=limit)
    hits = []
    ids = results.get("ids", [[]])[0]
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    for finding_id, doc, meta in zip(ids, docs, metas):
        hits.append({"finding_id": finding_id, "text": doc, "metadata": meta})
    return {"query": q, "results": hits}
