"""
API routes: submit new research, poll status, fetch results, browse/search
the accumulated knowledge base.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db.session import get_session
from ..db.models import ResearchTopic
from ..db import vector_store
from ..agents.orchestrator import run_pipeline
from ..schemas import (
    NewResearchRequest, TopicSummary, TopicDetail,
    ConclusionOut, ContradictionOut, FindingOut, PipelineEventOut,
)

router = APIRouter()


def _finding_out(f):
    return FindingOut(
        id=f.id, claim=f.claim, detail=f.detail,
        classification=f.classification, source_url=f.source.url,
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
    """Full detail for one topic: status, live pipeline event log, and any
    conclusions generated so far -- each with its supporting findings and
    source URLs for full traceability."""
    topic = db.get(ResearchTopic, topic_id)
    if topic is None:
        raise HTTPException(404, "topic not found")

    conclusions_out = [
        ConclusionOut(
            id=c.id,
            text=c.text,
            findings=[_finding_out(f) for f in c.findings],
        )
        for c in topic.conclusions
    ]
    contradictions_out = [
        ContradictionOut(
            id=c.id,
            explanation=c.explanation,
            finding_a=_finding_out(c.finding_a),
            finding_b=_finding_out(c.finding_b),
        )
        for c in topic.contradictions
    ]
    events_out = [
        PipelineEventOut(stage=e.stage, message=e.message, created_at=e.created_at)
        for e in sorted(topic.pipeline_events, key=lambda e: e.created_at)
    ]
    return TopicDetail(
        id=topic.id, question=topic.question, domain=topic.domain, status=topic.status,
        conclusions=conclusions_out, contradictions=contradictions_out, events=events_out,
    )


@router.get("/knowledge-base/search")
def search_knowledge_base(q: str, limit: int = 8):
    """Semantic search across every finding ever extracted, from any past
    research run. This is what makes the knowledge base reusable rather than
    a fresh scratchpad per query -- the whole point the brief calls out as
    distinguishing this from 'ChatGPT with web search'."""
    if not q.strip():
        raise HTTPException(400, "q must not be empty")
    results = vector_store.query_findings(q, n_results=limit)
    hits = []
    ids = results.get("ids", [[]])[0]
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    for i, doc, meta in zip(ids, docs, metas):
        hits.append({"finding_id": i, "text": doc, "metadata": meta})
    return {"query": q, "results": hits}
