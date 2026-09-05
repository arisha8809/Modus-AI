# Modus Intelligence

**Modus Intelligence** is an evidence-grounded enterprise intelligence workspace. It turns a business question into a structured investigation, preserves the evidence behind each finding, surfaces contradictions, and produces a decision-ready brief.

This is a focused portfolio project demonstrating the engineering path from an AI prototype to a production-shaped product: a real frontend, a typed FastAPI backend, persistent data, multi-stage AI orchestration, semantic retrieval, containerized startup, and observable pipeline progress.

## Product story

Modus is designed around a simple principle:

> Enterprise AI is more useful when it connects fragmented information to accountable decisions.

The workflow is:

```text
Business question → planning → evidence discovery → extraction → validation → decision brief
```

The central traceability path is:

```text
Decision → supporting finding → source URL
```

This makes the output inspectable rather than presenting an opaque chatbot response.

## What the project demonstrates

| Capability | Demonstrated by |
|---|---|
| AI product workflow | Guided intelligence runs with live pipeline progress |
| Python backend | FastAPI service with typed request and response models |
| AI application architecture | Multi-stage planning, extraction, evidence comparison, and synthesis |
| RAG and semantic search | Persistent Chroma knowledge base across intelligence runs |
| Structured persistence | SQLite graph for topics, sources, findings, contradictions, and conclusions |
| Explainable reasoning | Corroboration, contested evidence, coverage gaps, and source provenance |
| Production-shaped engineering | Docker, Compose, health checks, environment configuration, and persisted pipeline events |
| Product thinking | Evidence library, executive readout, detailed dossier, and transparent architecture view |

## Run locally

### Docker Compose

```bash
docker compose up --build
```

Open the workspace at `http://localhost:8501`. The API and OpenAPI documentation are available at `http://localhost:8000/docs`.

To stop the demo:

```bash
docker compose down
```

The named `modus-data` volume keeps SQLite and Chroma data between container restarts. To start with a clean workspace, remove the volume:

```bash
docker compose down -v
```

### Run services directly

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r frontend/requirements.txt
cp .env.example .env

uvicorn backend.main:app --reload --port 8000
```

In a second terminal:

```bash
source .venv/bin/activate
streamlit run frontend/app.py
```

The live intelligence pipeline requires `GROQ_API_KEY` and `TAVILY_API_KEY`. The interface remains useful for inspecting the system architecture and persisted demo data without those keys.

## Architecture

```text
Streamlit intelligence workspace
            │ REST / JSON
            ▼
FastAPI intelligence API
            │
            ├── Multi-stage agent orchestrator
            ├── SQLite structured evidence graph
            ├── Chroma persistent semantic index
            └── Pipeline events and traceability records
```

The API is provider-aware: agent logic is separated from the LLM client so the hosted provider can later be replaced by another OpenAI-compatible endpoint or a local model runtime. The evidence graph and pipeline events are persisted incrementally, so partial failures do not erase work that has already completed.

## API surface

| Endpoint | Purpose |
|---|---|
| `GET /health` | Service status and runtime metadata |
| `POST /research` | Create an intelligence run and start the background pipeline |
| `GET /research` | List saved intelligence runs |
| `GET /research/{topic_id}` | Retrieve the complete evidence dossier |
| `GET /knowledge-base/search?q=...` | Search findings across all runs |
| `/docs` | Interactive FastAPI documentation |

## Scope and next steps

The project intentionally focuses on evidence-grounded reasoning, traceability, persistence, and reproducible container startup. Authentication, multi-tenant isolation, enterprise connectors, and human-approved external actions are future production milestones rather than capabilities being overstated here.

## Repository layout

```text
backend/       FastAPI app, routes, agents, persistence, and vector search
frontend/      Streamlit intelligence workspace
docs/          API, architecture, data model, deployment, and model notes
scripts/       Optional demo-data preparation helpers
sample_data/   Sample-data documentation
```
