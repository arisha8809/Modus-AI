# Model & Library Inventory

Required deliverable per the challenge brief: every model/framework/library used, with licence,
and — for any free-tier external service — what happens if it becomes paid or unavailable.

## AI Model

| Component | Provider | Model | Cost | Licence |
|---|---|---|---|---|
| LLM (all agents) | Groq | `llama-3.3-70b-versatile` (Meta's open-weight Llama 3.3) | Free tier (no card required) | Llama 3.3 Community License (model); Groq API usage under Groq's free-tier terms |
| Embeddings | ChromaDB default (`sentence-transformers/all-MiniLM-L6-v2`) | runs locally | Free, open-source | Apache 2.0 |

**If Groq's free tier becomes paid or unavailable:** all LLM calls go through a single file
(`backend/agents/llm_client.py`). Swapping to another OpenAI-compatible free provider (e.g.
OpenRouter's free models) or a local Ollama model requires editing only that file — no changes
to any of the five agents, since they all call `chat_json()` / `chat_text()` and know nothing
about the underlying provider.

## Core libraries

| Library | Purpose | Licence |
|---|---|---|
| FastAPI | Backend API framework | MIT |
| Uvicorn | ASGI server | BSD |
| SQLAlchemy | ORM / database layer | MIT |
| Pydantic | API schema validation | MIT |
| Streamlit | Frontend UI framework | Apache 2.0 |
| ChromaDB | Local vector store | Apache 2.0 |
| `ddgs` (DuckDuckGo Search) | Free web search, no API key | MIT |
| `trafilatura` | Clean text extraction from fetched web pages | Apache 2.0 / GPL dual-licensed (used under Apache 2.0 terms) |
| `groq` (Python SDK) | Client for the Groq API | Apache 2.0 |
| `python-dotenv` | Loads `.env` config | BSD |

## Data storage

| Store | Purpose | Cost |
|---|---|---|
| SQLite | Structured knowledge base (topics, sources, findings, conclusions) | Free, built into Python, file-based |
| ChromaDB (persistent, local) | Vector index for semantic search over findings | Free, open-source, local |

No paid licence or hosted database subscription is required to run or evaluate this application.
