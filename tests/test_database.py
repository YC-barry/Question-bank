from offline_quiz.database import Database
from offline_quiz.domain import Question, QuestionType, QuizMode
from offline_quiz.quiz_service import QuizService


def make_question(stem: str = "第一题") -> Question:
    return Question(
        bank_name="安全培训",
        question_type=QuestionType.SINGLE_CHOICE,
        stem=stem,
        answer="A",
        options={"A": "正确", "B": "错误"},
        category="基础",
        source_order=1,
    )


def test_database_creates_bank_and_round_trips_question(tmp_path):
    db = Database(tmp_path / "quiz.db")
    bank_id = db.ensure_bank("安全培训", "source.xlsx")
    question_id = db.upsert_question(bank_id, make_question())

    loaded = db.get_question(question_id)
    assert loaded is not None
    assert loaded.bank_name == "安全培训"
    assert loaded.options == {"A": "正确", "B": "错误"}
    assert loaded.answer == "A"


def test_database_overwrite_preserves_question_id(tmp_path):
    db = Database(tmp_path / "quiz.db")
    bank_id = db.ensure_bank("安全培训")
    original_id = db.upsert_question(bank_id, make_question(), overwrite=True)
    changed = make_question()
    changed.explanation = "更新后的解析"
    updated_id = db.upsert_question(bank_id, changed, overwrite=True)

    assert updated_id == original_id
    assert db.get_question(original_id).explanation == "更新后的解析"


def test_delete_question_keeps_history_snapshot(tmp_path):
    db = Database(tmp_path / "quiz.db")
    bank_id = db.ensure_bank("安全培训")
    question_id = db.upsert_question(bank_id, make_question())
    session_id = db.create_session("考试", {"bank_ids": [bank_id]})
    db.save_session_item(session_id, db.get_question(question_id), "B", False, 0)

    db.delete_question(question_id)

    history = db.get_session(session_id)
    assert history["items"][0]["snapshot"]["stem"] == "第一题"


def test_database_counts_only_unmastered_wrong_questions(tmp_path):
    database = Database(tmp_path / "quiz.db")
    bank_id = database.ensure_bank("错题计数")
    question_id = database.upsert_question(
        bank_id,
        Question(
            bank_name="错题计数",
            question_type=QuestionType.TRUE_FALSE,
            stem="需要检查的题目",
            answer=True,
        ),
    )
    session = QuizService(database).create_session({}, None, QuizMode.SEQUENTIAL)
    QuizService(database).answer_question(session, 0, False)

    assert database.count_unmastered_wrong_questions() == 1
    database.mark_mastered(question_id)
    assert database.count_unmastered_wrong_questions() == 0
