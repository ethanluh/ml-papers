"""
FastAPI backend for the arXiv ML Dashboard.

Usage:
    uvicorn api.main:app --reload --port 8000
    
Deployment:
    - Render.com: render.yaml
    - Railway: railway.json
"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "pipeline"))

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from db import get_papers, get_stats, init_db
from .models import PaperOut, StatsOut

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="arXiv ML Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    """Initialize database on app startup."""
    try:
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialization complete")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        # Don't raise - allow app to start even if DB init fails
        # Endpoints will handle missing DB gracefully


@app.get("/api/papers", response_model=list[PaperOut])
def papers(
    task:       str | None = Query(None),
    difficulty: str | None = Query(None),
    search:     str | None = Query(None),
    limit:      int        = Query(50, le=200),
    offset:     int        = Query(0),
):
    return get_papers(task=task, difficulty=difficulty, search=search,
                      limit=limit, offset=offset)


@app.get("/api/stats", response_model=StatsOut)
def stats():
    return get_stats()


# Serve frontend static files at root
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="static")