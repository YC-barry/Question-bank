from offline_quiz import __version__
from offline_quiz.app import prepare_database
from offline_quiz.backup import BackupService
from offline_quiz.branding import DATA_DIRECTORY, EXECUTABLE_BASENAME, PRODUCT_NAME
from offline_quiz.database import Database


def test_user_visible_identity_identifies_win7_compatibility_release():
    assert PRODUCT_NAME == "岿枢题典（Win7 兼容版）"
    assert EXECUTABLE_BASENAME == "KuishuQuiz-Win7"
    assert DATA_DIRECTORY == "OfflineQuiz-Win7"
    assert __version__ == "1.6.0-win7-rc1"


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
