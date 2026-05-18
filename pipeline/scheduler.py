"""
Scheduler: runs the arXiv pipeline once per day at a configured UTC hour.

This runs as a long-lived background worker on cloud platforms (Render.com, Railway).

Usage:
    python pipeline/scheduler.py           # loop forever, runs at RUN_HOUR UTC
    python pipeline/scheduler.py --once    # run immediately and exit
"""

import sys
import os
import time
import logging
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [scheduler] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger(__name__)

RUN_HOUR = int(os.getenv("SCHEDULER_RUN_HOUR", "6"))   # UTC hour to trigger daily run


def run_once():
    """Execute one pipeline run with backup."""
    log.info("─" * 60)
    log.info("Backing up existing SQLite database...")
    try:
        from backup import backup_db
        backup_db()
    except Exception as e:
        log.warning(f"Backup failed, continuing with pipeline run: {e}")

    log.info("Starting pipeline run...")
    from arxiv_pipeline import run_pipeline
    try:
        results = run_pipeline()
        log.info(f"✓ Pipeline complete. {len(results)} papers processed.")
    except Exception as e:
        log.error(f"✗ Pipeline failed: {e}", exc_info=True)
    finally:
        log.info("─" * 60)


def loop():
    """Run scheduler loop, checking once per minute."""
    log.info(f"Scheduler started. Will run daily at {RUN_HOUR:02d}:00 UTC.")
    log.info(f"DATABASE_PATH: {os.getenv('DATABASE_PATH', 'default (./db)')}")
    last_run_date = None

    while True:
        try:
            now = datetime.now(timezone.utc)
            today = now.date()

            if now.hour >= RUN_HOUR and last_run_date != today:
                last_run_date = today
                run_once()

            time.sleep(60)   # check every minute
        except Exception as e:
            log.error(f"Scheduler loop error: {e}", exc_info=True)
            time.sleep(300)  # wait 5 minutes before retrying


if __name__ == "__main__":
    if "--once" in sys.argv:
        run_once()
    else:
        loop()