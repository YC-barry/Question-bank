from __future__ import annotations

import json
import sqlite3

import pytest

from offline_quiz.database import Database, SCHEMA_VERSION
from offline_quiz.domain import Question, QuestionAsset, QuestionType


def _create_v1_database(path) -> None:
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE schema_version (version INTEGER NOT NULL);
            INSERT INTO schema_version VALUES (1);
            CREATE TABLE banks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                source_filename TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bank_id INTEGER NOT NULL REFERENCES banks(id) ON DELETE CASCADE,
                fingerprint TEXT NOT NULL,
                question_type TEXT NOT NULL,
                stem TEXT NOT NULL,
                options_json TEXT NOT NULL,
                answer_json TEXT NOT NULL,
                aliases_json TEXT NOT NULL,
                explanation TEXT NOT NULL,
                category TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                tags_json TEXT NOT NULL,
                points INTEGER NOT NULL,
                source_order INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(bank_id, fingerprint)
            );
            CREATE TABLE sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mode TEXT NOT NULL,
                filters_json TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                score INTEGER,
                total INTEGER
            );
            CREATE TABLE session_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                question_id INTEGER,
                snapshot_json TEXT NOT NULL,
                user_answer_json TEXT NOT NULL,
                is_correct INTEGER NOT NULL,
                earned_points INTEGER NOT NULL,
                answered_at TEXT NOT NULL
            );
            CREATE TABLE wrong_questions (
                question_id INTEGER PRIMARY KEY REFERENCES questions(id) ON DELETE CASCADE,
                wrong_count INTEGER NOT NULL DEFAULT 1,
                last_wrong_at TEXT NOT NULL,
                mastered INTEGER NOT NULL DEFAULT 0
            );
            INSERT INTO banks VALUES (1, '旧题库', 'old.docx', '2025-01-01', '2025-01-01');
            INSERT INTO questions VALUES (
                1, 1, 'fingerprint', '判断', '旧题仍保留', '{}', 'true', '[]', '',
                '基础', '中等', '[]', 1, 1, '2025-01-01', '2025-01-01'
            );
            """
        )


def _media_question() -> Question:
    return Question(
        bank_name="机械题库",
        question_type=QuestionType.CALCULATION,
        stem="根据图示计算。",
        answer="10mm",
        solution="由图计算得10mm。",
        requires_manual_review=True,
        assets=[
            QuestionAsset("image/png", b"\x89PNG\r\n", 1, "公式图"),
            QuestionAsset("image/jpeg", b"\xff\xd8\xff", 2, "结构图"),
        ],
    )


def test_v1_database_migrates_to_v2_without_losing_questions(tmp_path):
    path = tmp_path / "v1.db"
    _create_v1_database(path)

    database = Database(path)

    assert SCHEMA_VERSION == 4
    assert database.get_question(1).stem == "旧题仍保留"
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT version FROM schema_version").fetchone()[0] == 4
        columns = {row[1] for row in connection.execute("PRAGMA table_info(questions)")}
        assert {"solution", "requires_manual_review"}.issubset(columns)
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='question_assets'"
        ).fetchone()
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='explanation_packages'"
        ).fetchone()


def test_question_media_and_subjective_fields_round_trip_in_order(tmp_path):
    database = Database(tmp_path / "quiz.db")
    bank_id = database.ensure_bank("机械题库")

    question_id = database.upsert_question(bank_id, _media_question())
    loaded = database.get_question(question_id)

    assert loaded.solution == "由图计算得10mm。"
    assert loaded.requires_manual_review is True
    assert [(asset.position, asset.mime_type, asset.data) for asset in loaded.assets] == [
        (1, "image/png", b"\x89PNG\r\n"),
        (2, "image/jpeg", b"\xff\xd8\xff"),
    ]


def test_deleted_question_history_snapshot_keeps_base64_media(tmp_path):
    database = Database(tmp_path / "quiz.db")
    bank_id = database.ensure_bank("机械题库")
    question_id = database.upsert_question(bank_id, _media_question())
    question = database.get_question(question_id)
    session_id = database.create_session("练习", {})
    database.save_session_item(session_id, question, "10mm", True, 1)

    database.delete_question(question_id)

    snapshot = database.get_session(session_id)["items"][0]["snapshot"]
    assert snapshot["solution"] == "由图计算得10mm。"
    assert snapshot["assets"][0]["data_base64"].startswith("iVBOR")
    assert "data" not in snapshot["assets"][0]
    json.dumps(snapshot, ensure_ascii=False)


def test_failed_migration_rolls_back_schema_and_version(tmp_path, monkeypatch):
    path = tmp_path / "v1.db"
    _create_v1_database(path)

    def fail_migration(self, connection):
        connection.execute("ALTER TABLE questions ADD COLUMN transient TEXT")
        raise RuntimeError("simulated migration failure")

    monkeypatch.setattr(Database, "_migrate_v1_to_v2", fail_migration, raising=False)

    with pytest.raises(RuntimeError, match="migration failure"):
        Database(path)

    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT version FROM schema_version").fetchone()[0] == 1
        columns = {row[1] for row in connection.execute("PRAGMA table_info(questions)")}
        assert "transient" not in columns


def test_failure_after_v3_ddl_rolls_back_entire_v1_upgrade_and_can_retry(
    tmp_path, monkeypatch
):
    path = tmp_path / "v1-retry.db"
    _create_v1_database(path)
    original = Database._migrate_v2_to_v3

    def fail_after_v3(self, connection):
        original(self, connection)
        raise RuntimeError("simulated failure after v3 DDL")

    monkeypatch.setattr(Database, "_migrate_v2_to_v3", fail_after_v3)

    with pytest.raises(RuntimeError, match="after v3 DDL"):
        Database(path)

    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT version FROM schema_version").fetchone()[0] == 1
        columns = {row[1] for row in connection.execute("PRAGMA table_info(questions)")}
        assert "solution" not in columns
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='explanation_packages'"
        ).fetchone() is None

    monkeypatch.undo()
    database = Database(path)
    assert database.get_question(1).stem == "旧题仍保留"
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT version FROM schema_version").fetchone()[0] == 4


def test_overwrite_replaces_assets_without_changing_question_id(tmp_path):
    database = Database(tmp_path / "quiz.db")
    bank_id = database.ensure_bank("机械题库")
    original = _media_question()
    question_id = database.upsert_question(bank_id, original, overwrite=True)
    replacement = _media_question()
    replacement.assets = [QuestionAsset("image/png", b"new", 7)]

    replaced_id = database.upsert_question(bank_id, replacement, overwrite=True)

    assert replaced_id == question_id
    assert [(asset.position, asset.data) for asset in database.get_question(question_id).assets] == [
        (7, b"new")
    ]
