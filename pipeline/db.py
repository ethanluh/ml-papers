"""
SQLite interface for arXiv paper storage.
Schema: papers table with full metadata + Groq summary fields.
"""

import os
import sqlite3
import json
import re
from pathlib import Path
from datetime import datetime, date

# Use persistent storage path for cloud platforms, fall back to local db/ directory
DATA_DIR = Path(os.getenv("DATABASE_PATH", "/var/data"))
if not os.getenv("DATABASE_PATH"):
    # Fallback to local directory for development
    DATA_DIR = Path(__file__).parent.parent / "db"

DB_PATH = DATA_DIR / "papers.db"


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS papers (
                id          TEXT PRIMARY KEY,
                title       TEXT NOT NULL,
                abstract    TEXT NOT NULL,
                authors     TEXT NOT NULL,
                published   TEXT NOT NULL,
                categories  TEXT NOT NULL,
                summary     TEXT,
                tldr        TEXT,
                task        TEXT,
                difficulty  TEXT,
                methods     TEXT,
                inserted_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_published  ON papers(published);
            CREATE INDEX IF NOT EXISTS idx_task       ON papers(task);
            CREATE INDEX IF NOT EXISTS idx_difficulty ON papers(difficulty);

            CREATE VIRTUAL TABLE IF NOT EXISTS papers_fts
                USING fts5(id UNINDEXED, title, abstract, summary, tldr);
        """)


def normalize_search(text: str) -> str:
    return re.sub(r'["]', ' ', text).strip()


def compute_velocity(published: str) -> float:
    try:
        published_date = datetime.strptime(published, "%Y-%m-%d").date()
    except ValueError:
        return 0.0

    age = (date.today() - published_date).days
    score = max(0.0, (14 - min(age, 14)) / 14)
    return round(score, 3)


def upsert_paper(paper: dict):
    groq = paper.get("groq", {})
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO papers
                (id, title, abstract, authors, published, categories,
                 summary, tldr, task, difficulty, methods, inserted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title       = excluded.title,
                abstract    = excluded.abstract,
                authors     = excluded.authors,
                published   = excluded.published,
                categories  = excluded.categories,
                summary     = excluded.summary,
                tldr        = excluded.tldr,
                task        = excluded.task,
                difficulty  = excluded.difficulty,
                methods     = excluded.methods,
                inserted_at = excluded.inserted_at
        """, (
            paper["id"],
            paper["title"],
            paper["abstract"],
            json.dumps(paper.get("authors", [])),
            paper["published"],
            json.dumps(paper.get("categories", [])),
            groq.get("summary"),
            groq.get("tldr"),
            groq.get("task"),
            groq.get("difficulty"),
            json.dumps(groq.get("methods", [])),
            datetime.utcnow().isoformat(),
        ))

        conn.execute("DELETE FROM papers_fts WHERE id = ?", (paper["id"],))
        conn.execute(
            "INSERT INTO papers_fts (id, title, abstract, summary, tldr) VALUES (?, ?, ?, ?, ?)",
            (
                paper["id"],
                paper["title"],
                paper["abstract"],
                groq.get("summary"),
                groq.get("tldr"),
            ),
        )


def upsert_many(papers: list[dict]):
    for p in papers:
        upsert_paper(p)


def get_papers(
    task: str | None = None,
    difficulty: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    if search:
        query = "SELECT p.* FROM papers p JOIN papers_fts f ON f.id = p.id WHERE f MATCH ?"
        params: list = [normalize_search(search)]
    else:
        query = "SELECT * FROM papers WHERE 1=1"
        params = []

    if task:
        query += " AND task = ?"
        params.append(task)
    if difficulty:
        query += " AND difficulty = ?"
        params.append(difficulty)

    query += " ORDER BY published DESC LIMIT ? OFFSET ?"
    params += [limit, offset]

    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()

    result = []
    for r in rows:
        d = dict(r)
        d["authors"]    = json.loads(d["authors"])
        d["categories"] = json.loads(d["categories"])
        d["methods"]    = json.loads(d["methods"] or "[]")
        d["velocity"]   = compute_velocity(d["published"])
        result.append(d)
    return result


def get_stats() -> dict:
    with get_conn() as conn:
        total      = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
        by_task    = conn.execute(
            "SELECT task, COUNT(*) as n FROM papers GROUP BY task ORDER BY n DESC"
        ).fetchall()
        by_date    = conn.execute(
            "SELECT published, COUNT(*) as n FROM papers GROUP BY published ORDER BY published DESC LIMIT 14"
        ).fetchall()
        trending_rows = conn.execute(
            "SELECT * FROM papers WHERE published >= date('now', '-14 days') ORDER BY published DESC LIMIT 12"
        ).fetchall()

        trending = []
        for r in trending_rows:
            d = dict(r)
            d["authors"]    = json.loads(d["authors"])
            d["categories"] = json.loads(d["categories"])
            d["methods"]    = json.loads(d["methods"] or "[]")
            d["velocity"]   = compute_velocity(d["published"])
            trending.append(d)

        trending.sort(key=lambda item: item["velocity"], reverse=True)
        trending = trending[:6]

    return {
        "total":    total,
        "by_task":  [dict(r) for r in by_task],
        "by_date":  [dict(r) for r in by_date],
        "trending": trending,
    }