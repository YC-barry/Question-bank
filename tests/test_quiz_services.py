from offline_quiz.backup import BackupService
from offline_quiz.database import Database
from offline_quiz.domain import Question, QuestionType, QuizMode
from offline_quiz.quiz_service import HistoryService, QuizService


def seed_questions(database: Database, count: int = 5) -> int:
    bank_id = database.ensure_bank("安全培训")
    for index in range(count):
        database.upsert_question(
            bank_id,
            Question(
                bank_name="安全培训",
                question_type=QuestionType.SINGLE_CHOICE,
                stem=f"第{index + 1}题",
                options={"A": "正确", "B": "错误"},
                answer="A",
                points=index + 1,
                source_order=index + 1,
            ),
        )
    return bank_id


def test_exam_is_random_without_replacement_and_totals_one_hundred(tmp_path):
    database = Database(tmp_path / "quiz.db")
    bank_id = seed_questions(database, 5)
    service = QuizService(database)

    session = service.create_session({"bank_ids": [bank_id]}, 4, QuizMode.EXAM, seed=7)

    assert len({question.id for question in session.questions}) == 4
    assert sum(question.points for question in session.questions) == 100


def test_exam_rejects_count_greater_than_available(tmp_path):
    database = Database(tmp_path / "quiz.db")
    bank_id = seed_questions(database, 2)

    try:
        QuizService(database).create_session({"bank_ids": [bank_id]}, 3, QuizMode.EXAM)
    except ValueError as exc:
        assert "仅有 2 道" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_sequential_session_preserves_import_order(tmp_path):
    database = Database(tmp_path / "quiz.db")
    bank_id = seed_questions(database, 4)

    session = QuizService(database).create_session(
        {"bank_ids": [bank_id]}, None, QuizMode.SEQUENTIAL
    )

    assert [question.stem for question in session.questions] == ["第1题", "第2题", "第3题", "第4题"]


def test_submit_exam_saves_score_answers_and_wrong_question(tmp_path):
    database = Database(tmp_path / "quiz.db")
    bank_id = seed_questions(database, 2)
    service = QuizService(database)
    session = service.create_session({"bank_ids": [bank_id]}, 2, QuizMode.EXAM, seed=1)
    answers = {session.questions[0].id: "A", session.questions[1].id: "B"}

    result = service.submit(session, answers)

    assert result.total == 100
    assert 0 < result.score < 100
    saved = HistoryService(database).get(session.id)
    assert len(saved["items"]) == 2
    assert sum(1 for item in saved["items"] if not item["is_correct"]) == 1
    assert len(database.list_questions(wrong_only=True)) == 1


def test_sequential_answer_returns_immediate_feedback(tmp_path):
    database = Database(tmp_path / "quiz.db")
    bank_id = seed_questions(database, 1)
    service = QuizService(database)
    session = service.create_session({"bank_ids": [bank_id]}, None, QuizMode.SEQUENTIAL)

    grade = service.answer_question(session, 0, "B")

    assert grade.is_correct is False
    assert grade.correct_answer == "A"


def test_backup_restore_and_retention(tmp_path):
    database = Database(tmp_path / "data" / "quiz.db")
    seed_questions(database, 1)
    backups = BackupService(database.path, tmp_path / "backups", keep=2)

    first = backups.create_backup()
    second = backups.create_backup()
    third = backups.create_backup()

    assert len(list((tmp_path / "backups").glob("*.db"))) == 2
    database.delete_bank(database.get_banks()[0]["id"])
    backups.restore_backup(third)
    assert len(Database(database.path).list_questions()) == 1
    assert not first.exists()
    assert second.exists()


def test_failed_backup_leaves_no_partial_file(tmp_path):
    database_path = tmp_path / "broken.db"
    database_path.write_bytes(b"not a sqlite database")
    service = BackupService(database_path, tmp_path / "backups")

    try:
        service.create_backup()
    except Exception:
        pass
    else:
        raise AssertionError("expected backup failure")

    assert list((tmp_path / "backups").glob("*.db")) == []
    assert list((tmp_path / "backups").glob("*.tmp")) == []


def test_restore_rejects_non_application_database(tmp_path):
    database = Database(tmp_path / "quiz.db")
    seed_questions(database, 1)
    foreign = tmp_path / "foreign.db"
    import sqlite3
    with sqlite3.connect(foreign) as connection:
        connection.execute("CREATE TABLE unrelated(value TEXT)")
    service = BackupService(database.path, tmp_path / "backups")

    try:
        service.restore_backup(foreign)
    except ValueError as exc:
        assert "题库助手" in str(exc)
    else:
        raise AssertionError("expected ValueError")

    assert len(Database(database.path).list_questions()) == 1


def test_retention_does_not_delete_protected_backup(tmp_path):
    database = Database(tmp_path / "quiz.db")
    seed_questions(database, 1)
    service = BackupService(database.path, tmp_path / "backups", keep=2)
    oldest = service.create_backup()
    service.create_backup()

    service.create_backup(protect=oldest)

    assert oldest.exists()


def test_exam_submission_rolls_back_all_answers_on_failure(tmp_path, monkeypatch):
    database = Database(tmp_path / "quiz.db")
    bank_id = seed_questions(database, 2)
    service = QuizService(database)
    session = service.create_session({"bank_ids": [bank_id]}, 2, QuizMode.EXAM, seed=1)
    original = database._save_session_item_with_connection
    calls = 0

    def fail_second(connection, session_id, question, user_answer, is_correct, earned_points):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated disk failure")
        return original(connection, session_id, question, user_answer, is_correct, earned_points)

    monkeypatch.setattr(database, "_save_session_item_with_connection", fail_second)

    try:
        service.submit(session, {question.id: "A" for question in session.questions})
    except OSError:
        pass
    else:
        raise AssertionError("expected OSError")

    assert database.get_session(session.id)["items"] == []
    assert session.results == {}
