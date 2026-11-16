from __future__ import annotations

import sqlite3

from PySide2.QtWidgets import QMessageBox

from offline_quiz.database import Database, SCHEMA_VERSION
from offline_quiz.domain import Question, QuestionType, QuizMode
from offline_quiz.ui import SettingsPage


def _database_with_learning_data(tmp_path) -> tuple[Database, int, int]:
    database = Database(tmp_path / "quiz.db")
    bank_id = database.ensure_bank("本地数据测试题库")
    question_id = database.upsert_question(
        bank_id,
        Question(
            bank_name="本地数据测试题库",
            question_type=QuestionType.TRUE_FALSE,
            stem="设备启动前必须检查防护装置。",
            answer=True,
        ),
    )
    question = database.get_question(question_id)
    session_id = database.create_session(QuizMode.SEQUENTIAL.value, {})
    database.save_session_item(session_id, question, False, False, 0)
    database.complete_session(session_id, 0, 1)
    return database, question_id, session_id


def _table_count(database: Database, table: str) -> int:
    with database.connection() as connection:
        return int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def test_schema_v4_contains_app_settings_and_migrates_idempotently(tmp_path):
    path = tmp_path / "schema.db"

    Database(path)
    Database(path)

    with sqlite3.connect(path) as connection:
        assert SCHEMA_VERSION == 4
        assert connection.execute("SELECT version FROM schema_version").fetchone()[0] == 4
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='app_settings'"
        ).fetchone()


def test_clear_wrong_questions_preserves_history_questions_and_packages(tmp_path):
    database, _question_id, _session_id = _database_with_learning_data(tmp_path)
    with database.connection() as connection:
        connection.execute(
            """INSERT INTO explanation_packages(
                   name, filename, subject, level, content_hash, imported_at
               ) VALUES ('测试解析', 'test.docx', '机修钳工', '初级', 'hash', '2026-11-14')"""
        )
    before_questions = len(database.list_questions())
    before_sessions = _table_count(database, "sessions")
    before_items = _table_count(database, "session_items")
    before_packages = _table_count(database, "explanation_packages")

    deleted = database.clear_wrong_questions()

    assert deleted == 1
    assert database.count_unmastered_wrong_questions() == 0
    assert len(database.list_questions()) == before_questions
    assert _table_count(database, "sessions") == before_sessions
    assert _table_count(database, "session_items") == before_items
    assert _table_count(database, "explanation_packages") == before_packages


def test_clear_practice_history_preserves_wrong_notebook_and_questions(tmp_path):
    database, _question_id, _session_id = _database_with_learning_data(tmp_path)
    before_questions = len(database.list_questions())

    deleted = database.clear_practice_history()

    assert deleted == 1
    assert database.list_sessions() == []
    assert _table_count(database, "session_items") == 0
    assert database.count_unmastered_wrong_questions() == 1
    assert len(database.list_questions()) == before_questions


def test_reset_learning_overview_preserves_history_and_starts_fresh(tmp_path):
    database, question_id, session_id = _database_with_learning_data(tmp_path)

    reset_item_id = database.reset_learning_overview()

    overview = database.learning_overview()
    assert reset_item_id > 0
    assert overview["totals"]["practiced"] == 0
    assert overview["totals"]["correct"] == 0
    assert overview["recent"] == []
    assert database.get_session(session_id)["items"]
    assert database.count_unmastered_wrong_questions() == 1

    new_session = database.create_session(QuizMode.SEQUENTIAL.value, {})
    database.save_session_item(
        new_session, database.get_question(question_id), True, True, 1
    )

    refreshed = database.learning_overview()
    assert refreshed["totals"]["practiced"] == 1
    assert refreshed["totals"]["correct"] == 1
    assert refreshed["recent"][0]["id"] == new_session


def test_settings_clear_wrong_notebook_backs_up_first_and_emits_refresh(
    qtbot, tmp_path, monkeypatch
):
    database, _question_id, _session_id = _database_with_learning_data(tmp_path)
    page = SettingsPage(database, tmp_path)
    qtbot.addWidget(page)
    changes: list[bool] = []
    page.data_changed.connect(lambda: changes.append(True))
    monkeypatch.setattr(
        QMessageBox, "question", lambda *_args, **_kwargs: QMessageBox.Yes
    )
    monkeypatch.setattr(
        QMessageBox, "information", lambda *_args, **_kwargs: QMessageBox.Ok
    )

    page.learning_data_buttons["wrong"].click()

    backups = sorted((tmp_path / "backups").glob("*.db"))
    assert len(backups) == 1
    assert Database(backups[0]).count_unmastered_wrong_questions() == 1
    assert database.count_unmastered_wrong_questions() == 0
    assert changes == [True]


def test_settings_cancelled_clear_does_not_backup_or_delete(qtbot, tmp_path, monkeypatch):
    database, _question_id, _session_id = _database_with_learning_data(tmp_path)
    page = SettingsPage(database, tmp_path)
    qtbot.addWidget(page)
    monkeypatch.setattr(
        QMessageBox, "question", lambda *_args, **_kwargs: QMessageBox.No
    )

    page.learning_data_buttons["wrong"].click()

    assert not (tmp_path / "backups").exists()
    assert database.count_unmastered_wrong_questions() == 1


def test_settings_history_button_preserves_wrong_notebook(qtbot, tmp_path, monkeypatch):
    database, _question_id, _session_id = _database_with_learning_data(tmp_path)
    page = SettingsPage(database, tmp_path)
    qtbot.addWidget(page)
    monkeypatch.setattr(
        QMessageBox, "question", lambda *_args, **_kwargs: QMessageBox.Yes
    )
    monkeypatch.setattr(
        QMessageBox, "information", lambda *_args, **_kwargs: QMessageBox.Ok
    )

    page.learning_data_buttons["history"].click()

    assert database.list_sessions() == []
    assert database.count_unmastered_wrong_questions() == 1


def test_settings_overview_button_preserves_history(qtbot, tmp_path, monkeypatch):
    database, _question_id, session_id = _database_with_learning_data(tmp_path)
    page = SettingsPage(database, tmp_path)
    qtbot.addWidget(page)
    monkeypatch.setattr(
        QMessageBox, "question", lambda *_args, **_kwargs: QMessageBox.Yes
    )
    monkeypatch.setattr(
        QMessageBox, "information", lambda *_args, **_kwargs: QMessageBox.Ok
    )

    page.learning_data_buttons["overview"].click()

    assert database.learning_overview()["totals"]["practiced"] == 0
    assert database.get_session(session_id)["items"]
    assert database.count_unmastered_wrong_questions() == 1
