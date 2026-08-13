"""
Enterprise AI Research Agent -- FastAPI application entrypoint.

Run locally with:
    uvicorn backend.main:app --reload --port 8000

See README.md for the full architecture and setup instructions.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db.session import init_db
from .routes.research import router as research_router

app = FastAPI(
    title="Enterprise AI Research Agent",
    description="Structured, traceable, multi-agent enterprise research at scale.",
    version="1.0.0",
)

# Streamlit frontend (local or hosted) needs to call this API cross-origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(research_router, tags=["research"])


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}
