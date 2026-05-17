"""Local free backup workflow for the SQLite paper database."""

import shutil
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "db" / "papers.db"
BACKUP_DIR = DB_PATH.parent / "backups"
MAX_BACKUPS = 30
RETENTION_DAYS = 30


def ensure_backup_dir() -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def cleanup_old_backups() -> None:
    backups = sorted(BACKUP_DIR.glob("papers_backup_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in backups[MAX_BACKUPS:]:
        old.unlink(missing_ok=True)

    cutoff = datetime.utcnow() - timedelta(days=RETENTION_DAYS)
    for old in backups:
        if datetime.fromtimestamp(old.stat().st_mtime) < cutoff:
            old.unlink(missing_ok=True)


def backup_db() -> Path | None:
    ensure_backup_dir()

    if not DB_PATH.exists():
        print("No SQLite database found at", DB_PATH)
        return None

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"papers_backup_{timestamp}.db"
    shutil.copy2(DB_PATH, backup_path)
    cleanup_old_backups()
    print(f"Backup saved to: {backup_path}")
    return backup_path


if __name__ == "__main__":
    backup_db()
