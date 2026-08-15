# Modus AI — Enterprise AI Research Agent

Built for the **Modus Enterprise AI Build Challenge**, Assignment 9: *Enterprise AI Research Agent*.

An AI application that conducts **structured, traceable enterprise research at scale**, on any
industry or topic — not a single hardcoded case study, and not "ChatGPT with web search."

Give it a research question (e.g. *"How is AI transforming retail operations?"*, *"What AI
technologies are changing manufacturing?"*, or anything else — including a brand-new question
typed live) and it will:

```
Classify domain & define sub-questions
        → Search sources
        → Collect & store source pages
        → Extract structured findings
        → Compare evidence across sources
        → Classify findings (corroborated / contested / single-source)
        → Detect contradictions
        → Generate conclusions
        → Every conclusion is traceable back to the findings and source URLs that support it
```

The result is an **evidence-first research dossier**, not just a cited paragraph. The dashboard shows
claim-level contradictions side by side, evidence coverage by research theme, source portfolio by
provenance type, decision signals for strongest evidence and review areas, and a publication-year
research horizon when source dates are available. All metrics are calculated from the stored research
graph, and undated sources are explicitly excluded from the timeline rather than being assigned made-up
years.

All results persist in a reusable knowledge base — restarting the app does not lose anything,
and every past research run remains searchable.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  UI LAYER            Streamlit (frontend/app.py)                │
├─────────────────────────────────────────────────────────────────┤
│  API LAYER           FastAPI (backend/main.py, backend/routes/)  │
├─────────────────────────────────────────────────────────────────┤
│  AI INTELLIGENCE     5-agent pipeline (backend/agents/)          │
│                      Classifier → Search → Extraction →          │
│                      Evidence → Synthesis                        │
│                      LLM: Groq free-tier API (Llama 3.3 70B)     │
├─────────────────────────────────────────────────────────────────┤
│  DATA & KNOWLEDGE    SQLite (structured, relational, persistent) │
│                      + ChromaDB (vector store, semantic search)  │
├─────────────────────────────────────────────────────────────────┤
│  EXTERNAL RESEARCH   Tavily search API (agent-oriented, free tier)        │
└─────────────────────────────────────────────────────────────────┘
```

Full detail, including why each choice was made, is in [`docs/architecture.md`](docs/architecture.md).

### Why this satisfies the challenge's "not accepted" list

- **Not a wrapper around a hosted LLM UI** — the intelligence is a 5-stage agent pipeline with
  real branching logic (classification, evidence comparison, contradiction detection), each
  stage backed by its own prompt and stored output.
- **Not one giant prompt** — each agent has a narrow job and its own file
  (`backend/agents/*.py`); you can point to exactly which agent does what.
- **Not hardcoded for the demo** — the domain is detected live from whatever question is typed;
  nothing assumes retail, manufacturing, or any other fixed topic.
- **Data persists** — SQLite + Chroma files under `./data`; restarting the app does not clear
  the knowledge base.
- **Traceable** — every `Conclusion` row in the database links (via a join table) to the exact
  `Finding` rows that support it, which in turn link to the `Source` URL they came from.

---

## Running it locally

### 1. Prerequisites
- Python 3.11+
- A free Groq API key: [console.groq.com](https://console.groq.com) (no credit card required)
- A free Tavily API key: [tavily.com](https://tavily.com) (1,000 free searches/month, no card)

### 2. Setup
```bash
git clone https://github.com/arisha8809/Modus-AI.git
cd Modus-AI
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and paste your GROQ_API_KEY
```

### 3. Run the backend
```bash
uvicorn backend.main:app --reload --port 8000
```

### 4. Run the frontend (in a second terminal)
```bash
streamlit run frontend/app.py
```

Open the Streamlit URL it prints (usually `http://localhost:8501`), type a research question,
and watch the pipeline run.

---

## Hosted version

- **Frontend:** _[Streamlit Community Cloud link — added once deployed]_
- **Backend API:** _[Render link — added once deployed]_

See [`docs/deployment.md`](docs/deployment.md) for how this was deployed and what happens if the
Groq free tier or Render free tier becomes unavailable.

---

## Repository structure

```
Modus-AI/
├── backend/
│   ├── main.py              # FastAPI app entrypoint
│   ├── schemas.py           # API request/response models
│   ├── db/
│   │   ├── models.py        # SQLAlchemy schema (the persistent knowledge base)
│   │   ├── session.py       # DB engine/session setup
│   │   └── vector_store.py  # ChromaDB wrapper for semantic search
│   ├── agents/
│   │   ├── llm_client.py       # single entry point for all LLM calls (Groq)
│   │   ├── web_tools.py        # free web search + page fetching
│   │   ├── classifier_agent.py # domain detection + sub-question planning
│   │   ├── extraction_agent.py # structured findings from page text
│   │   ├── evidence_agent.py   # cross-source comparison, contradiction detection
│   │   ├── synthesis_agent.py  # final conclusions, linked to supporting findings
│   │   └── orchestrator.py     # runs the full pipeline, stage by stage
│   └── routes/
│       └── research.py      # /research and /knowledge-base endpoints
├── frontend/
│   └── app.py                # Streamlit UI
├── data/                      # SQLite + Chroma files (persistent, gitignored)
├── docs/
│   ├── architecture.md
│   ├── model_library_inventory.md
│   └── deployment.md
├── sample_data/                # example research runs for quick review
├── requirements.txt
├── .env.example
└── README.md
```

## Models & libraries used

See [`docs/model_library_inventory.md`](docs/model_library_inventory.md) for the full list with
licences, as required by the challenge deliverables.

## What was built vs. AI-assisted

This project was built collaboratively with an AI coding assistant (Claude). Every component —
schema design, agent prompts, pipeline orchestration, API routes, and UI — was reviewed and is
understood and explainable by the candidate, per the challenge's disclosure requirement.
