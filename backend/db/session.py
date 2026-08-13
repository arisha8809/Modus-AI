"""
Engine/session setup for the SQLite knowledge base.

The DB file lives under ./data so it persists across restarts and redeploys
(as long as the hosting platform gives that directory a persistent disk --
see README for the Render deployment notes on this).
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "data"))
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "knowledge_base.sqlite3")

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_session():
    """FastAPI dependency: yields a DB session and always closes it."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
