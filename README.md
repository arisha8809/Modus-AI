# The Brief

**The Brief** is an evidence-grounded enterprise intelligence workspace. It turns a business question into a structured research pipeline, preserves the evidence behind each finding, surfaces contradictions, and produces a decision-ready brief.

This is a focused proof-of-capability product rather than a claim to reproduce an entire enterprise AI platform. It demonstrates the engineering path from an AI prototype to a service that can be measured, containerized, deployed, and improved.

## Why this product

Enterprise AI is most useful when it connects fragmented information to accountable decisions. The Brief is designed around that principle:

```text
Business question → discovery → evidence collection → reasoning → validation → recommendation
```

The central traceability path is:

```text
Conclusion → supporting finding → source URL
```

That makes the result inspectable instead of presenting an opaque chatbot answer.

## What the demo shows

| Capability | Demonstrated by |
|---|---|
| AI product workflow | Guided brief creation and multi-stage pipeline |
| Python backend | FastAPI service with typed request/response models |
| AI application architecture | Multi-agent research, structured extraction, classification, and synthesis |
| RAG and vector search | Persistent Chroma knowledge base and semantic finding search |
| Data engineering | SQLite relational graph for topics, sources, findings, and conclusions |
| Enterprise reasoning | Corroboration, contradictions, coverage gaps, and decision signals |
| Production posture | Health metadata, persisted pipeline events, Docker, Compose, and environment configuration |
| Product thinking | Evidence explorer and a clear path from intelligence to human action |

## Run locally

### Option A: Docker Compose

```bash
docker compose up --build
```

Open the workspace at `http://localhost:8501`. The API and OpenAPI documentation are available at `http://localhost:8000/docs`.

To stop the demo:

```bash
docker compose down
```

The named `modus-data` volume keeps the SQLite and Chroma data between container restarts.

### Option B: Run services directly

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

The LLM and web-search pipeline requires `GROQ_API_KEY` and `TAVILY_API_KEY`. The frontend remains useful for inspecting persisted demo data and the system view without those keys.

## Architecture

```text
Streamlit workspace
        │ REST / JSON
        ▼
FastAPI intelligence API
        │
        ├── Multi-stage agent orchestrator
        ├── SQLite structured knowledge graph
        ├── Chroma persistent semantic index
        └── Pipeline events and traceability records
```

The API is intentionally provider-aware: the agent logic is separated from the LLM client so the hosted provider can later be replaced by another OpenAI-compatible endpoint or a local model runtime. The next product extension is a decision-to-action loop where a reviewed recommendation can create a controlled operational task with an audit record.

## API surface

- `GET /health` — service status and runtime metadata.
- `POST /research` — create a brief and start the background pipeline.
- `GET /research` — list saved briefs.
- `GET /research/{topic_id}` — retrieve the complete evidence dossier.
- `GET /knowledge-base/search?q=...` — search findings across all briefs.
- `/docs` — interactive FastAPI documentation.

## Deployment direction

The local Compose topology is deliberately close to a cloud deployment topology. The API container can move to Google Cloud Run, with persistent relational/vector storage, Secret Manager for credentials, Cloud Logging for structured events, and GitHub Actions for build and deployment automation. A larger installation can replace SQLite with PostgreSQL and run the orchestration layer as a separately scaled worker service.

## Honest scope

The current version focuses on the highest-value proof points: evidence-grounded reasoning, traceability, a clean demo flow, persistence, and reproducible container startup. Authentication, multi-tenant isolation, enterprise connectors, and human-approved external actions are intentionally identified as the next production milestones rather than being represented as complete capabilities.
