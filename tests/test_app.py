from offline_quiz import __version__
from offline_quiz.app import prepare_database
from offline_quiz.backup import BackupService
from offline_quiz.database import Database


def test_user_visible_version_identifies_test9_release():
    assert __version__ == "1.6.0-test9"


def test_corrupt_database_opens_recovery_path_without_partial_backup(tmp_path):
    database_path = tmp_path / "offline-quiz.db"
    database_path.write_bytes(b"broken")

    database, error = prepare_database(tmp_path)

    assert database is None
    assert error
    assert list((tmp_path / "backups").glob("*.db")) == []


def test_startup_continues_when_automatic_backup_fails(tmp_path, monkeypatch):
    Database(tmp_path / "offline-quiz.db")

    def fail_backup(self, protect=None):
        raise OSError("disk full")

    monkeypatch.setattr(BackupService, "create_backup", fail_backup)

    database, error = prepare_database(tmp_path)

    assert database is not None
    assert error is None
