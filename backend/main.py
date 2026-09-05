"""
Enterprise AI Research Agent -- FastAPI application entrypoint.

Run locally with:
    uvicorn backend.main:app --reload --port 8000

See README.md for the full architecture and setup instructions.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()  # reads .env into the process environment before anything else runs

from .db.session import init_db
from .routes.research import router as research_router

app = FastAPI(
    title="The Brief Intelligence API",
    description="Evidence-grounded enterprise intelligence with traceable decisions.",
    version="1.1.0",
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


@app.get("/health", tags=["system"])
def health():
    return {
        "status": "ok",
        "service": "the-brief-api",
        "version": app.version,
        "environment": os.environ.get("APP_ENV", "development"),
    }
