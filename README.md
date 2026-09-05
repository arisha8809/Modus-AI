# Modus Intelligence — "The Brief"

An evidence-grounded enterprise research agent. You give it a business question, a multi-agent AI pipeline researches it live on the web, and it hands back a decision-ready brief where every conclusion traces back to the exact source it came from — not a chatbot paragraph.

**Live demo:** [modus-ai.streamlit.app](https://modus-ai.streamlit.app/)
*(backend is on Render's free tier — first request after idle time can take ~30-50s to wake up)*

**Source:** [github.com/arisha8809/Modus-AI](https://github.com/arisha8809/Modus-AI)

---

## What it does

- Takes any business/research question — not tied to one industry — and figures out the domain itself
- Breaks it into sub-questions, searches the live web for each one, and pulls real sources
- Extracts individual claims from each source and checks them against each other
- Flags contradictions and corroborated evidence instead of hiding disagreement
- Synthesizes final conclusions, each linked to the exact findings and source URLs behind it
- Persists every run, so the knowledge base grows and stays searchable across sessions
- Shows the pipeline running live, stage by stage, instead of just a final answer

## How the multi-agent pipeline works

The core idea: one question comes in, five specialized agents pass work down the chain, and the whole thing is orchestrated + persisted so it can recover from a mid-run failure instead of losing everything.

```
Question
   │
   ▼
┌─────────────────────┐
│ 1. Classifier Agent │  reads the question, detects the industry/domain,
└─────────┬───────────┘  breaks it into 3-5 focused sub-questions
          ▼
┌─────────────────────┐
│ 2. Web Search        │  Tavily searches each sub-question, returns
│    (web_tools.py)     │  ranked sources with content + publish date
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ 3. Extraction Agent  │  reads one source's text, pulls out distinct
└─────────┬───────────┘  factual claims + any dated timeline events
          ▼
┌─────────────────────┐
│ 4. Evidence Agent    │  looks at ALL findings for a sub-question together,
└─────────┬───────────┘  tags each as corroborated / contested / single-source,
          │              and pairs up direct contradictions
          ▼
┌─────────────────────┐
│ 5. Synthesis Agent   │  writes 3-6 final conclusions from every finding
└──────────────────────┘  collected, each one naming exactly which finding
                          ids support it
```

Every stage is domain-agnostic — nothing is hardcoded for "retail" or any single industry. The Classifier Agent is what makes that possible: it's the only place the domain gets decided, and everything downstream just operates on whatever domain + sub-questions it produced. That's deliberate, since the app has to handle a brand-new question live, not just a pre-baked demo topic.

`backend/agents/orchestrator.py` is what actually runs this end to end for one research topic. Two things worth knowing about it:
- **It persists as it goes**, not just at the end — every stage writes to SQLite immediately and logs a `PipelineEvent`, which is what lets the Streamlit UI poll and show live progress, and means a crash partway through doesn't erase work already done.
- **Failure isolation is per-item, not per-run** — only the classification stage is treated as fatal (without a domain there's nothing to search for). If one source fails to fetch or one sub-question's evidence check errors, that item is logged and skipped rather than aborting the whole topic.

All LLM calls (from every agent) go through one file, `backend/agents/llm_client.py`, which talks to Groq. That's a deliberate seam — if Groq's model access changes, only that file needs to change, not any agent logic.

## Why it's more than "ChatGPT with search"

| | Chatbot + web search | Modus |
|---|---|---|
| Output | One prose answer | Findings → contradictions → conclusions, each traceable to a source |
| Memory | Stateless per query | SQLite + vector store persist across runs and restarts |
| Evidence | Implicit | Every conclusion links back to `Finding → Source → URL` |
| Repeatability | Manual re-prompting | Same 5-stage pipeline runs identically for any new question |

## Code organization

```
backend/
├── main.py            FastAPI app entrypoint — CORS, router mounting, /health
├── schemas.py          Pydantic request/response models for the API
├── routes/
│   └── research.py    POST/GET endpoints: start a run, poll status, fetch
│                       a dossier, search the knowledge base
├── agents/
│   ├── classifier_agent.py   stage 1 — domain detection + sub-questions
│   ├── web_tools.py           stage 2 — Tavily search wrapper
│   ├── extraction_agent.py   stage 3 — per-source claim extraction
│   ├── evidence_agent.py     stage 4 — corroboration/contradiction detection
│   ├── synthesis_agent.py    stage 5 — final conclusions + citations
│   ├── orchestrator.py       runs all 5 stages for one topic, handles
│   │                          persistence + failure isolation
│   └── llm_client.py          single entry point for every Groq call
└── db/
    ├── models.py       SQLAlchemy schema (see data model below)
    ├── session.py      DB session/engine setup
    └── vector_store.py Chroma persistent semantic index over findings

frontend/
└── app.py              Streamlit workspace — submits questions, polls
                         pipeline progress, renders the evidence dossier

docs/                   architecture, API reference, data model, deployment
                         notes, and model/library inventory
```

## Data model

```
ResearchTopic ──< SubQuestion ──< Source ──< Finding >── Conclusion
                                                (many-to-many via conclusion_findings)
```

`ResearchTopic` is the question you asked. It has many `SubQuestion`s (from the Classifier), each with many `Source`s (from search), each with many `Finding`s (from extraction). `Conclusion`s connect back to whichever `Finding`s support them through a join table — that link is what makes "why was this concluded?" answerable by walking the graph instead of trusting an LLM summary.

SQLite handles this relational side; ChromaDB separately indexes every finding for semantic search across *all* past runs, so the knowledge base is reusable rather than a fresh scratchpad each time.

## Tech stack

| Layer | Tools |
|---|---|
| Backend | Python, FastAPI, Pydantic, Uvicorn |
| Frontend | Streamlit |
| AI / LLM | Groq (Llama 3.1), custom multi-agent orchestrator |
| Retrieval | Tavily (web search), ChromaDB (vector store / semantic search) |
| Data | SQLite + SQLAlchemy ORM |
| Containerization | Docker (separate backend + frontend images), Docker Compose |
| CI/CD | GitHub Actions — runs checks, then builds both Docker images and pushes them to GHCR on every push to `main` |
| Deployment | Render (backend), Streamlit Community Cloud (frontend) |

## Run it

**Docker Compose (recommended)** — starts both services with health checks and a persistent volume:

```bash
git clone https://github.com/arisha8809/Modus-AI.git
cd Modus-AI
cp .env.example .env   # add free GROQ_API_KEY + TAVILY_API_KEY
docker compose up --build
```

- Workspace: `http://localhost:8501`
- API + docs: `http://localhost:8000/docs`
- `docker compose down -v` to reset to a clean workspace

**Without Docker:**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r frontend/requirements.txt
cp .env.example .env
uvicorn backend.main:app --reload --port 8000   # terminal 1
streamlit run frontend/app.py                    # terminal 2
```

## Docker setup, in detail

- Two separate images — `Dockerfile` (FastAPI backend) and `frontend/Dockerfile` (Streamlit) — so each service scales and redeploys independently
- Backend image runs as a **non-root user**, not root
- Backend has a built-in container `HEALTHCHECK` against `/health`; the frontend's `docker-compose.yml` entry waits on that healthcheck (`depends_on: condition: service_healthy`) before starting
- A named volume (`modus-data`) keeps SQLite + Chroma data alive across container restarts
- Environment-driven config (`GROQ_API_KEY`, `TAVILY_API_KEY`, `DATA_DIR`) — nothing hardcoded into the image

## CI/CD, in detail

`.github/workflows/ci.yml` has two jobs:

1. **`checks`** — installs dependencies, compiles all Python sources, and imports the FastAPI app to catch a broken app before anything else runs.
2. **`docker`** (depends on `checks` passing) — builds the backend and frontend images from their real Dockerfiles on every push and PR, so a broken Dockerfile fails CI instead of being discovered at deploy time. On pushes to `main`, it also logs into **GitHub Container Registry (GHCR)** and pushes both images, tagged `latest` and with the commit SHA:
   - `ghcr.io/arisha8809/modus-ai/backend:latest`
   - `ghcr.io/arisha8809/modus-ai/frontend:latest`

No extra secrets or accounts needed — it authenticates with the automatically-issued `GITHUB_TOKEN`, and GHCR is free for public repos. This means every merge to `main` produces a pullable, versioned container image, not just a "does it compile" check.

## API surface

| Endpoint | Purpose |
|---|---|
| `GET /health` | Service status + runtime metadata |
| `POST /research` | Start a new research run (runs the pipeline in the background) |
| `GET /research` | List all past research runs |
| `GET /research/{topic_id}` | Full evidence dossier for one run |
| `GET /knowledge-base/search?q=...` | Semantic search across findings from every past run |
| `/docs` | Interactive OpenAPI docs |

## Honest scope

No authentication, multi-tenancy, or enterprise connectors yet — this is a focused engineering portfolio piece, not a finished product. The parts that are built (agent pipeline, persistence, traceability, containerized deploy, live hosted demo) are built to a production-shaped standard rather than a notebook demo.
