"""
One-shot ingestion entry point: fetch + summarize papers, then POST them
to the deployed app's authenticated /api/ingest endpoint, which upserts
them into Cloudflare D1.

Intended for scheduled one-shot runs (e.g. the daily GitHub Actions
workflow in .github/workflows/daily-ingestion.yml).

Usage:
    export GROQ_API_KEY=your_key_here
    export INGEST_URL=https://<your-app>.pages.dev/api/ingest
    export INGEST_TOKEN=your_shared_secret
    python pipeline/ingest.py
"""

import sys
import os
import logging
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [ingest] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger(__name__)


def main() -> int:
    ingest_url = os.environ["INGEST_URL"]
    ingest_token = os.environ["INGEST_TOKEN"]

    from arxiv_pipeline import run_pipeline

    results = run_pipeline()
    if not results:
        log.error("Pipeline returned no papers; nothing stored.")
        return 1

    resp = requests.post(
        ingest_url,
        json=results,
        headers={"X-Ingest-Token": ingest_token},
        timeout=60,
    )
    resp.raise_for_status()

    log.info(f"✓ Stored {len(results)} papers via {ingest_url} ({resp.json()}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
