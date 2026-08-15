# Architecture — Enterprise AI Research Agent

## Design goals (from the challenge brief)

1. Real frontend + backend + data layer + AI integration (not a notebook or a prompt wrapper).
2. Data persists across restarts.
3. Processes questions systematically and generically — must handle a brand-new question live
   (the "surprise record" test), not just the topic it was demoed with.
4. Every output traceable back to the data/research that produced it.
5. Only free/open-source/free-tier/local components.

## Why domain-agnostic, not a fixed industry

The brief's example topics ("How is AI transforming retail operations?" / "...manufacturing?")
are examples, not a fixed requirement. Since the evaluator can type any question live, the
pipeline cannot assume a single industry. The **Classifier Agent** is the first pipeline stage
specifically to solve this: it reads whatever question comes in and detects the domain itself,
so every downstream agent is generic.

## The pipeline, stage by stage

| Stage | Agent / component | Input | Output | Persisted as |
|---|---|---|---|---|
| 1 | Classifier Agent | raw research question | domain label + 3-5 sub-questions | `ResearchTopic.domain`, `SubQuestion` rows |
| 2 | Search tool (Tavily) | one sub-question | ranked source title, URL, content, and optional publication date | — |
| 3 | Source persistence | normalized search result | source page content plus provenance metadata | `Source.raw_text`, `Source.published_date` |
| 4 | Extraction Agent | page text + sub-question | list of {claim, detail} | `Finding` rows |
| 5 | Evidence Agent | all findings for a sub-question | classification per finding + contradiction pairs | `Finding.classification`, `Contradiction` rows |
| 6 | Synthesis Agent | all findings across all sub-questions | final conclusions + which finding ids support each | `Conclusion` rows + `conclusion_findings` join table |

Every stage also writes a `PipelineEvent` row, which is what lets the Streamlit UI show live
progress during a demo and gives a full audit trail afterward.

The result dossier also computes transparent analytics from the stored graph rather than asking the
LLM to invent presentation metrics: evidence counts by sub-question, source portfolio by domain and
source type, strongest-evidence themes, contested themes requiring review, coverage gaps, and a
publication-year timeline when retrieved sources expose publisher dates. Undated sources are excluded
from the timeline and the UI displays the date coverage percentage explicitly.

## Data model

See `backend/db/models.py` for the SQLAlchemy schema and inline docstrings. Summary:

```
ResearchTopic ──< SubQuestion ──< Source ──< Finding >── Conclusion
                                                (many-to-many via conclusion_findings)
```

This relational structure is what makes traceability real: to explain *why* a conclusion was
reached, the app walks `Conclusion → Finding → Source → url`, not a black-box LLM summary.

## Why SQLite + Chroma instead of a hosted database

- Zero external infrastructure to set up or pay for — satisfies the free-tech requirement with
  the least friction for an evaluator running this locally.
- Both are file-based and persist automatically under `./data`.
- SQLite handles the structured, relational side (exact traceability queries).
- Chroma handles the "fuzzy" side — semantic search across findings from *any* past research
  run, which is what makes the knowledge base reusable rather than a fresh scratchpad every time.
- The dashboard is intentionally evidence-first: it exposes claim-level contradictions, source profiles,
  sub-question coverage, decision signals, and dated research horizons before showing synthesized prose.
  This is the product distinction from a chatbot that only returns a cited paragraph.

**Scaling answer** (the brief's key judging question — "1,000 processes tomorrow instead of
100"): the pipeline has no hardcoded assumption about volume. SQLite comfortably handles tens of
thousands of rows; if the workload grew far beyond a single evaluation, the same schema maps
directly onto Postgres (SQLAlchemy makes this a connection-string change) and Chroma can run in
client/server mode against a larger index. The agent logic itself doesn't change — it already
processes one sub-question / one source / one finding at a time, so it parallelizes and scales
by input volume, not by rewriting logic per new case, matching the brief's own test that adding
a new record (Process 101 in the process-library assignments; here, a brand-new research
question) must go through the exact same mechanism as everything before it.

## Why Groq for the LLM

- Free tier, no credit card, generous rate limits — usable for a multi-agent pipeline that makes
  many calls per research run.
- Serves open-weight models (Llama 3.3 70B), in keeping with the free/open-source requirement.
- All calls go through `backend/agents/llm_client.py` — one file. If Groq's free tier changes,
  swapping to another OpenAI-compatible free provider or a local Ollama model is a change to
  that one file only; no agent code changes.
