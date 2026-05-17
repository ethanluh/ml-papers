"""
Scheduler: runs the arXiv pipeline once per day at a configured UTC hour.
Can be run as a long-lived process (e.g. via systemd or screen) or
just invoked directly from a cron job:

    # crontab entry (runs daily at 06:00 UTC)
    0 6 * * * cd /path/to/arxiv-ml-dashboard && python pipeline/scheduler.py --once

Usage:
    python pipeline/scheduler.py           # loop forever, runs at RUN_HOUR UTC
    python pipeline/scheduler.py --once    # run immediately and exit
"""

import sys
import time
import logging
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [scheduler] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger(__name__)

RUN_HOUR = 6   # UTC hour to trigger daily run


def run_once():
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
        log.info(f"Pipeline complete. {len(results)} papers processed.")
    except Exception as e:
        log.error(f"Pipeline failed: {e}", exc_info=True)


def loop():
    log.info(f"Scheduler started. Will run daily at {RUN_HOUR:02d}:00 UTC.")
    last_run_date = None

    while True:
        now = datetime.now(timezone.utc)
        today = now.date()

        if now.hour >= RUN_HOUR and last_run_date != today:
            last_run_date = today
            run_once()

        time.sleep(60)   # check every minute


if __name__ == "__main__":
    if "--once" in sys.argv:
        run_once()
    else:
        loop()