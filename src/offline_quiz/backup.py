from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sqlite3

from .database import SCHEMA_VERSION


REQUIRED_TABLES = {
    "schema_version",
    "banks",
    "questions",
    "sessions",
    "session_items",
    "wrong_questions",
}


def validate_application_database(
    path: str | Path, accepted_versions: set[int] | None = None
) -> None:
    source = Path(path)
    if not source.exists() or source.stat().st_size == 0:
        raise ValueError("该文件不是有效的题库助手备份")
    connection = None
    try:
        connection = sqlite3.connect(source)
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if integrity != "ok" or not REQUIRED_TABLES.issubset(tables):
            raise ValueError("该文件不是有效的题库助手备份")
        row = connection.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
        accepted = accepted_versions or {SCHEMA_VERSION}
        if row is None or int(row[0]) not in accepted:
            raise ValueError("备份版本与当前题库助手不兼容")
        if int(row[0]) >= 2 and "question_assets" not in tables:
            raise ValueError("该文件不是有效的题库助手备份")
    except ValueError:
        raise
    except (OSError, sqlite3.Error) as exc:
        raise ValueError("该文件不是有效的题库助手备份") from exc
    finally:
        if connection is not None:
            connection.close()


class BackupService:
    def __init__(self, database_path: str | Path, backup_dir: str | Path, keep: int = 5):
        self.database_path = Path(database_path)
        self.backup_dir = Path(backup_dir)
        self.keep = max(1, int(keep))

    def create_backup(self, protect: str | Path | None = None) -> Path:
        if not self.database_path.exists():
            raise FileNotFoundError("数据库文件不存在")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        destination = self.backup_dir / f"offline-quiz-{timestamp}.db"
        sequence = 1
        while destination.exists():
            destination = self.backup_dir / f"offline-quiz-{timestamp}-{sequence:03d}.db"
            sequence += 1
        temporary = destination.with_suffix(".tmp")
        temporary.unlink(missing_ok=True)
        source_connection = None
        target_connection = None
        try:
            source_connection = sqlite3.connect(self.database_path)
            target_connection = sqlite3.connect(temporary)
            source_connection.backup(target_connection)
            target_connection.close()
            target_connection = None
            source_connection.close()
            source_connection = None
            validate_application_database(temporary, {1, SCHEMA_VERSION})
            temporary.replace(destination)
        except Exception:
            if target_connection is not None:
                target_connection.close()
            if source_connection is not None:
                source_connection.close()
            temporary.unlink(missing_ok=True)
            destination.unlink(missing_ok=True)
            raise
        backups = sorted(
            self.backup_dir.glob("offline-quiz-*.db"),
            key=lambda path: path.stat().st_mtime_ns,
            reverse=True,
        )
        protected = Path(protect).resolve() if protect is not None else None
        removable = [
            backup for backup in backups
            if protected is None or backup.resolve() != protected
        ]
        for old_backup in removable[self.keep :]:
            old_backup.unlink(missing_ok=True)
        return destination

    def restore_backup(self, backup_path: str | Path) -> None:
        source = Path(backup_path)
        if not source.exists():
            raise FileNotFoundError("备份文件不存在")
        validate_application_database(source, {1, SCHEMA_VERSION})
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.database_path.with_suffix(".restore.tmp")
        temporary.unlink(missing_ok=True)
        try:
            shutil.copy2(source, temporary)
            validate_application_database(temporary, {1, SCHEMA_VERSION})
            temporary.replace(self.database_path)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
