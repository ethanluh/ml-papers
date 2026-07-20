"""
One-shot ingestion entry point: fetch + summarize papers, then store them
in the SQLite database.

Intended for scheduled one-shot runs (e.g. the daily GitHub Actions
workflow in .github/workflows/daily-ingestion.yml), unlike scheduler.py
which loops forever as a long-lived worker.

Usage:
    export GROQ_API_KEY=your_key_here
    python pipeline/ingest.py
"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [ingest] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger(__name__)


def main() -> int:
    log.info("Backing up existing SQLite database...")
    try:
        from backup import backup_db
        backup_db()
    except Exception as e:
        log.warning(f"Backup failed, continuing with pipeline run: {e}")

    from db import init_db, upsert_many
    from arxiv_pipeline import run_pipeline

    init_db()

    results = run_pipeline()
    if not results:
        log.error("Pipeline returned no papers; nothing stored.")
        return 1

    upsert_many(results)
    log.info(f"✓ Stored {len(results)} papers in the database.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
