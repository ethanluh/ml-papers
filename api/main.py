"""
FastAPI backend for the arXiv ML dashboard.

Usage:
    uvicorn api.main:app --reload --port 8000
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "pipeline"))

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from db import get_papers, get_stats, init_db
from .models import PaperOut, StatsOut

app = FastAPI(title="arXiv ML Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


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