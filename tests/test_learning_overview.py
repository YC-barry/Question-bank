from __future__ import annotations

from datetime import date, timedelta

from offline_quiz.database import Database
from offline_quiz.domain import Question, QuestionType, QuizMode


def _stored_question(
    database: Database,
    bank_id: int,
    stem: str,
    question_type: QuestionType,
):
    question_id = database.upsert_question(
        bank_id,
        Question(
            bank_name="统计题库",
            question_type=question_type,
            stem=stem,
            answer=True if question_type is QuestionType.TRUE_FALSE else [["答案"]],
        ),
    )
    return database.get_question(question_id)


def test_learning_overview_empty_database_returns_zero_filled_seven_days(tmp_path):
    overview = Database(tmp_path / "empty.db").learning_overview()

    assert overview["totals"] == {
        "total": 0,
        "practiced": 0,
        "correct": 0,
        "wrong": 0,
        "unpracticed": 0,
        "progress_percent": 0,
    }
    assert len(overview["trend"]) == 7
    assert [item["count"] for item in overview["trend"]] == [0] * 7
    assert overview["recent"] == []


def test_learning_overview_uses_latest_result_and_unique_question_coverage(tmp_path):
    database = Database(tmp_path / "overview.db")
    bank_id = database.ensure_bank("统计题库")
    first = _stored_question(database, bank_id, "判断一", QuestionType.TRUE_FALSE)
    second = _stored_question(database, bank_id, "判断二", QuestionType.TRUE_FALSE)
    _stored_question(database, bank_id, "填空一", QuestionType.FILL_BLANK)
    deleted = _stored_question(database, bank_id, "已删除历史题", QuestionType.TRUE_FALSE)
    session_id = database.create_session(QuizMode.SEQUENTIAL.value, {})

    database.save_session_item(session_id, first, False, False, 0)
    database.save_session_item(session_id, first, True, True, 1)
    database.save_session_item(session_id, second, False, False, 0)
    database.save_session_item(session_id, deleted, True, True, 1)

    today = date.today()
    yesterday = today - timedelta(days=1)
    old_day = today - timedelta(days=10)
    with database.connection() as connection:
        item_ids = [row["id"] for row in connection.execute(
            "SELECT id FROM session_items ORDER BY id"
        ).fetchall()]
        timestamps = [
            f"{yesterday.isoformat()}T09:00:00",
            f"{today.isoformat()}T09:00:00",
            f"{today.isoformat()}T10:00:00",
            f"{old_day.isoformat()}T08:00:00",
        ]
        connection.executemany(
            "UPDATE session_items SET answered_at=? WHERE id=?",
            list(zip(timestamps, item_ids)),
        )
    database.delete_question(deleted.id)

    overview = database.learning_overview()

    assert overview["totals"] == {
        "total": 3,
        "practiced": 2,
        "correct": 1,
        "wrong": 1,
        "unpracticed": 1,
        "progress_percent": 67,
    }
    assert overview["trend"][-2] == {"date": yesterday.isoformat(), "count": 1}
    assert overview["trend"][-1] == {"date": today.isoformat(), "count": 2}
    by_type = {item["question_type"]: item for item in overview["by_type"]}
    assert by_type[QuestionType.TRUE_FALSE.value] == {
        "question_type": QuestionType.TRUE_FALSE.value,
        "total": 2,
        "practiced": 2,
        "progress_percent": 100,
    }
    assert by_type[QuestionType.FILL_BLANK.value] == {
        "question_type": QuestionType.FILL_BLANK.value,
        "total": 1,
        "practiced": 0,
        "progress_percent": 0,
    }
    assert overview["recent"][0]["answered_count"] == 4
