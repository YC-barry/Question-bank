from __future__ import annotations

import pytest

from offline_quiz.database import Database
from offline_quiz.domain import Question, QuestionType, QuizMode
from offline_quiz.quiz_service import QuizService
from offline_quiz.subjective_grading import SubjectiveGradingService


def _question(kind, answer, *, points=10, solution=""):
    return Question(
        bank_name="机械题库",
        question_type=kind,
        stem="示例题",
        answer=answer,
        solution=solution,
        points=points,
        requires_manual_review=True,
    )


def test_short_answer_suggestion_distinguishes_full_partial_unrelated_and_empty():
    question = _question(
        QuestionType.SHORT_ANSWER,
        "液压泵把机械能转换为液压能，并向系统提供压力油。",
    )
    service = SubjectiveGradingService()

    full = service.suggest(question, "把机械能转换成液压能，向液压系统提供压力油")
    partial = service.suggest(question, "把机械能转换为液压能")
    unrelated = service.suggest(question, "用于测量工件长度")
    empty = service.suggest(question, "  ")

    assert full.status == "建议正确" and full.suggested_points == 10
    assert partial.status == "建议部分正确" and 0 < partial.suggested_points < 10
    assert unrelated.status == "建议错误" and unrelated.suggested_points == 0
    assert empty.suggested_points == 0
    assert all(item.requires_confirmation for item in [full, partial, unrelated, empty])


def test_calculation_suggestion_accepts_scientific_notation_and_checks_units():
    service = SubjectiveGradingService()
    question = _question(QuestionType.CALCULATION, "2840 r/min", solution="n=1420×2")

    equivalent = service.suggest(question, "2.84e3 r/min")
    wrong_unit = service.suggest(question, "2840 mm")

    assert equivalent.status == "建议正确"
    assert equivalent.suggested_points == 10
    assert wrong_unit.status in {"建议部分正确", "待人工确认"}
    assert wrong_unit.suggested_points < 10


def test_calculation_with_multiple_results_or_answer_omitted_stays_pending():
    service = SubjectiveGradingService()
    multiple = _question(QuestionType.CALCULATION, "孔20.021mm，轴19.939mm")
    omitted = _question(QuestionType.CALCULATION, "答：略", solution="见图计算")

    partial = service.suggest(multiple, "孔20.021mm")
    pending = service.suggest(omitted, "20")

    assert partial.status == "建议部分正确"
    assert 0 < partial.suggested_points < 10
    assert pending.status == "待人工确认"
    assert pending.requires_confirmation is True


def test_exam_subjective_results_are_not_committed_until_manual_confirmation(tmp_path):
    database = Database(tmp_path / "quiz.db")
    bank_id = database.ensure_bank("机械题库")
    objective_id = database.upsert_question(
        bank_id,
        Question(
            bank_name="机械题库",
            question_type=QuestionType.TRUE_FALSE,
            stem="客观题",
            answer=True,
            points=1,
        ),
    )
    subjective_id = database.upsert_question(
        bank_id,
        _question(QuestionType.SHORT_ANSWER, "关键答案", points=1),
    )
    service = QuizService(database)
    session = service.create_session({"bank_ids": [bank_id]}, 2, QuizMode.EXAM, seed=1)
    answers = {objective_id: True, subjective_id: "关键答案"}

    provisional = service.submit(session, answers)

    saved = database.get_session(session.id)
    assert provisional.requires_review is True
    assert saved["completed_at"] is None
    assert saved["items"] == []

    final = service.finalize_subjective(session, {subjective_id: 40})

    assert final.requires_review is False
    assert final.score == 90
    saved = database.get_session(session.id)
    assert saved["completed_at"] is not None
    assert len(saved["items"]) == 2


def test_manual_score_must_cover_every_pending_question_and_stay_in_range(tmp_path):
    database = Database(tmp_path / "quiz.db")
    bank_id = database.ensure_bank("机械题库")
    question_id = database.upsert_question(
        bank_id,
        _question(QuestionType.CALCULATION, "10mm", points=1),
    )
    service = QuizService(database)
    session = service.create_session({"bank_ids": [bank_id]}, 1, QuizMode.EXAM)
    service.submit(session, {question_id: "10mm"})

    with pytest.raises(ValueError, match="确认"):
        service.finalize_subjective(session, {})
    with pytest.raises(ValueError, match="0 到 100"):
        service.finalize_subjective(session, {question_id: 101})

    assert database.get_session(session.id)["items"] == []
