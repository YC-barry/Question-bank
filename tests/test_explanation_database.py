from __future__ import annotations

import hashlib
import sqlite3

import pytest

from offline_quiz.database import Database
from offline_quiz.domain import Question, QuestionType, QuizMode
from offline_quiz.explanation_packages import (
    DuplicateExplanationPackage,
    ExplanationEntry,
    ExplanationPackage,
    normalize_answer,
    normalize_stem,
)
from offline_quiz.quiz_service import QuizService


def _question(
    *,
    bank_name: str = "机修钳工初级理论知识",
    answer: str = "A",
    explanation: str = "原题解析",
) -> Question:
    return Question(
        bank_name=bank_name,
        question_type=QuestionType.SINGLE_CHOICE,
        stem="滚动轴承的滚动体是（）。",
        options={"A": "钢球", "B": "铜球"},
        answer=answer,
        explanation=explanation,
        source_order=1,
    )


def _package(
    text: str,
    *,
    answer: str = "A",
    level: str = "初级",
    filename: str | None = None,
    duplicate_entries: bool = False,
) -> ExplanationPackage:
    entry = ExplanationEntry(
        question_type=QuestionType.SINGLE_CHOICE,
        source_number=1,
        original_stem="滚动轴承的滚动体是（ A ）。 A、钢球 B、铜球",
        stem_fingerprint=normalize_stem(
            QuestionType.SINGLE_CHOICE,
            "滚动轴承的滚动体是（ A ）。 A、钢球 B、铜球",
        ),
        normalized_answer=normalize_answer(QuestionType.SINGLE_CHOICE, answer),
        explanation=text,
    )
    digest = hashlib.sha256(f"{level}|{answer}|{text}".encode()).hexdigest()
    return ExplanationPackage(
        name=f"{level}解析",
        filename=filename or f"{digest[:8]}.docx",
        subject="机修钳工",
        level=level,
        content_hash=digest,
        entries=[entry, entry] if duplicate_entries else [entry],
    )


def _insert_question(database: Database, question: Question | None = None) -> int:
    question = question or _question()
    bank_id = database.ensure_bank(question.bank_name, f"{question.bank_name}.docx")
    return database.upsert_question(bank_id, question)


def test_schema_v3_is_idempotent_and_contains_explanation_tables(tmp_path):
    path = tmp_path / "quiz.db"
    Database(path)
    Database(path)

    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT version FROM schema_version").fetchone()[0] == 3
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    assert {"explanation_packages", "explanation_entries"}.issubset(tables)


def test_package_imported_before_question_matches_after_question_import(tmp_path):
    database = Database(tmp_path / "quiz.db")
    database.import_explanation_package(_package("资料包解析"))

    before = database.list_explanation_packages()[0]
    assert (before["matched_count"], before["pending_count"], before["conflict_count"]) == (0, 1, 0)

    question_id = _insert_question(database)

    assert database.get_question(question_id).explanation == "资料包解析"
    after = database.list_explanation_packages()[0]
    assert (after["matched_count"], after["pending_count"], after["conflict_count"]) == (1, 0, 0)


def test_question_imported_before_package_matches_immediately(tmp_path):
    database = Database(tmp_path / "quiz.db")
    question_id = _insert_question(database)

    database.import_explanation_package(_package("后导入解析"))

    assert database.get_question(question_id).explanation == "后导入解析"


@pytest.mark.parametrize("bank_name", ["电工初级理论知识", "机修钳工理论知识"])
def test_other_subject_and_unknown_level_never_match(tmp_path, bank_name):
    database = Database(tmp_path / "quiz.db")
    _insert_question(database, _question(bank_name=bank_name))

    database.import_explanation_package(_package("不应附加"))

    package = database.list_explanation_packages()[0]
    assert package["matched_count"] == 0
    assert package["pending_count"] == 1
    assert database.list_questions()[0].explanation == "原题解析"


def test_same_stem_with_different_answer_is_conflict_and_keeps_original(tmp_path):
    database = Database(tmp_path / "quiz.db")
    question_id = _insert_question(database)

    database.import_explanation_package(_package("冲突解析", answer="B"))

    package = database.list_explanation_packages()[0]
    assert package["conflict_count"] == 1
    assert package["matched_count"] == 0
    assert database.get_question(question_id).explanation == "原题解析"


def test_duplicate_content_requires_explicit_atomic_replacement(tmp_path):
    database = Database(tmp_path / "quiz.db")
    original = _package("相同内容", filename="one.docx")
    original_id = database.import_explanation_package(original)
    renamed = _package("相同内容", filename="renamed.docx")

    with pytest.raises(DuplicateExplanationPackage) as exc_info:
        database.import_explanation_package(renamed)
    assert exc_info.value.package_id == original_id
    assert len(database.list_explanation_packages()) == 1

    replacement_id = database.import_explanation_package(
        renamed, replace_package_id=original_id
    )
    packages = database.list_explanation_packages()
    assert replacement_id != original_id
    assert [item["filename"] for item in packages] == ["renamed.docx"]

    broken = _package("会回滚", duplicate_entries=True)
    with pytest.raises(sqlite3.IntegrityError):
        database.import_explanation_package(broken, replace_package_id=replacement_id)
    assert [item["id"] for item in database.list_explanation_packages()] == [replacement_id]


def test_delete_latest_package_falls_back_without_changing_learning_data(tmp_path):
    database = Database(tmp_path / "quiz.db")
    question_id = _insert_question(database)
    service = QuizService(database)
    session = service.create_session({}, None, QuizMode.SEQUENTIAL)
    service.answer_question(session, 0, "B")
    older_id = database.import_explanation_package(_package("较早解析"))
    newer_id = database.import_explanation_package(_package("最新解析"))
    before_questions = len(database.list_questions())
    before_wrong = database.count_unmastered_wrong_questions()
    before_session = database.get_session(session.id)

    assert database.get_question(question_id).explanation == "最新解析"
    assert before_session["items"][0]["snapshot"]["explanation"] == "最新解析"

    database.delete_explanation_package(newer_id)

    assert database.get_question(question_id).explanation == "较早解析"
    assert database.get_session(session.id)["items"][0]["snapshot"]["explanation"] == "较早解析"
    assert len(database.list_questions()) == before_questions
    assert database.count_unmastered_wrong_questions() == before_wrong
    assert database.get_session(session.id)["score"] == before_session["score"]

    database.delete_explanation_package(older_id)
    assert database.get_question(question_id).explanation == "原题解析"
    assert database.get_session(session.id)["items"][0]["snapshot"]["explanation"] == "原题解析"


def test_history_matches_packages_against_snapshot_answer_not_current_answer(tmp_path):
    database = Database(tmp_path / "quiz.db")
    question_id = _insert_question(database)
    service = QuizService(database)
    session = service.create_session({}, None, QuizMode.SEQUENTIAL)
    service.answer_question(session, 0, "A")

    database.update_question(question_id, _question(answer="B"))
    database.import_explanation_package(_package("当前答案 B 的解析", answer="B"))

    history = database.get_session(session.id)
    assert history["items"][0]["snapshot"]["answer"] == "A"
    assert history["items"][0]["snapshot"]["explanation"] == "原题解析"

    database.import_explanation_package(_package("历史答案 A 的解析", answer="A"))
    assert (
        database.get_session(session.id)["items"][0]["snapshot"]["explanation"]
        == "历史答案 A 的解析"
    )
