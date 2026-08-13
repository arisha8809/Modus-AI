"""
Pipeline Orchestrator.

Runs the full Assignment-9 pipeline end to end for one research topic:

  Define Research Questions -> Search Sources -> Collect Information ->
  Store Sources -> Extract Findings -> Compare Evidence -> Classify Findings
  -> Detect Contradictions -> Generate Conclusions -> Maintain Traceability

Every stage writes to SQLite immediately (not just at the end) and logs a
PipelineEvent, so:
  - the Streamlit UI can poll and show live progress during the demo, and
  - if the process crashes partway through, everything up to that point is
    already persisted, not lost.

This function is called from a FastAPI BackgroundTask so the HTTP request
that kicks off research returns immediately with a topic_id to poll.
"""

from sqlalchemy.orm import Session

from ..db.models import ResearchTopic, SubQuestion, Source, Finding, Conclusion, PipelineEvent
from ..db import vector_store
from .classifier_agent import classify_and_plan
from .web_tools import search_web
from .extraction_agent import extract_findings
from .evidence_agent import compare_evidence
from .synthesis_agent import synthesize


def _log(db: Session, topic: ResearchTopic, stage: str, message: str):
    db.add(PipelineEvent(topic_id=topic.id, stage=stage, message=message))
    db.commit()


def run_pipeline(topic_id: int, db: Session, max_sources_per_subq: int = 3):
    topic = db.get(ResearchTopic, topic_id)
    if topic is None:
        return

    try:
        topic.status = "running"
        db.commit()

        # --- Stage 1: Classify domain + define sub-questions ---
        _log(db, topic, "classify", "Classifying domain and defining sub-questions...")
        plan = classify_and_plan(topic.question)
        topic.domain = plan["domain"]
        db.commit()
        _log(db, topic, "classify", f"Domain: {plan['domain']}. {len(plan['sub_questions'])} sub-questions defined.")

        all_findings_for_synthesis = []  # [{id, claim, classification}]

        for sub_q_text in plan["sub_questions"]:
            sub_q = SubQuestion(topic_id=topic.id, text=sub_q_text)
            db.add(sub_q)
            db.commit()

            # --- Stage 2: Search sources ---
            _log(db, topic, "search", f"Searching sources for: {sub_q_text}")
            results = search_web(sub_q_text, max_results=max_sources_per_subq)

            sub_q_findings = []  # collected across all sources for this sub-question

            for r in results:
                # --- Stage 3: Collect + store sources ---
                page_text = r.get("content")
                source = Source(
                    sub_question_id=sub_q.id,
                    url=r["url"],
                    title=r["title"],
                    raw_text=page_text,
                )
                db.add(source)
                db.commit()
                _log(db, topic, "collect", f"Stored source: {r['url']}")

                if not page_text:
                    continue

                # --- Stage 4: Extract findings ---
                extracted = extract_findings(sub_q_text, page_text)
                for f in extracted:
                    finding = Finding(
                        source_id=source.id,
                        claim=f.get("claim", ""),
                        detail=f.get("detail", ""),
                    )
                    db.add(finding)
                    db.commit()
                    vector_store.add_finding(
                        finding_id=finding.id,
                        text=finding.claim + " " + (finding.detail or ""),
                        metadata={
                            "domain": topic.domain or "",
                            "topic_id": topic.id,
                            "source_url": source.url,
                        },
                    )
                    sub_q_findings.append({
                        "id": finding.id, "claim": finding.claim, "source_url": source.url,
                    })
                if extracted:
                    _log(db, topic, "extract", f"Extracted {len(extracted)} findings from {r['url']}")

            # --- Stage 5+6+7: Compare evidence, classify, detect contradictions ---
            if sub_q_findings:
                _log(db, topic, "compare", f"Comparing {len(sub_q_findings)} findings for contradictions...")
                comparison = compare_evidence(sub_q_findings)
                for finding_id_str, classification in comparison["classifications"].items():
                    finding = db.get(Finding, int(finding_id_str))
                    if finding:
                        finding.classification = classification
                db.commit()
                if comparison["contradictions"]:
                    _log(
                        db, topic, "contradictions",
                        f"Detected {len(comparison['contradictions'])} contradiction(s): "
                        + "; ".join(c.get("explanation", "") for c in comparison["contradictions"]),
                    )

                for f in sub_q_findings:
                    finding = db.get(Finding, f["id"])
                    all_findings_for_synthesis.append({
                        "id": finding.id, "claim": finding.claim, "classification": finding.classification,
                    })

        # --- Stage 8: Generate conclusions (traceable to findings) ---
        _log(db, topic, "synthesize", "Generating conclusions from all gathered evidence...")
        conclusions = synthesize(topic.question, all_findings_for_synthesis)
        for c in conclusions:
            conclusion = Conclusion(topic_id=topic.id, text=c.get("text", ""))
            db.add(conclusion)
            db.commit()
            for fid in c.get("supporting_finding_ids", []):
                finding = db.get(Finding, fid)
                if finding:
                    conclusion.findings.append(finding)
            db.commit()

        topic.status = "done"
        db.commit()
        _log(db, topic, "done", f"Pipeline complete. {len(conclusions)} conclusions generated.")

    except Exception as e:
        topic.status = "failed"
        db.commit()
        _log(db, topic, "error", f"Pipeline failed: {e}")
        raise
