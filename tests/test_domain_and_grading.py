from offline_quiz.domain import Question, QuestionType, allocate_points, fingerprint_for
from offline_quiz.grading import GradingService, normalize_text


def question(kind: QuestionType, answer, *, points: int = 5) -> Question:
    return Question(
        bank_name="示例题库",
        question_type=kind,
        stem="示例题目",
        answer=answer,
        points=points,
        options={"A": "甲", "B": "乙", "C": "丙"},
    )


def test_normalize_text_unifies_width_case_and_whitespace():
    assert normalize_text("  ＡＢＣ   Test  ") == "abc test"


def test_single_choice_grading_is_exact():
    result = GradingService.grade(question(QuestionType.SINGLE_CHOICE, "A"), "a")
    assert result.is_correct is True
    assert result.earned_points == 5


def test_multiple_choice_grading_ignores_order_but_rejects_duplicates():
    q = question(QuestionType.MULTIPLE_CHOICE, ["A", "C"])
    assert GradingService.grade(q, ["C", "A"]).is_correct is True
    assert GradingService.grade(q, ["A", "A", "C"]).is_correct is False


def test_true_false_grading_accepts_common_forms():
    q = question(QuestionType.TRUE_FALSE, True)
    assert GradingService.grade(q, "√").is_correct is True
    assert GradingService.grade(q, "错").is_correct is False


def test_fill_blank_requires_every_blank_and_accepts_aliases():
    q = question(QuestionType.FILL_BLANK, [["北京", "北京市"], ["China", "中国"]])
    assert GradingService.grade(q, ["北京市", "china"]).is_correct is True
    assert GradingService.grade(q, ["北京", "中华"]).is_correct is False


def test_fingerprint_uses_type_and_normalized_stem():
    a = fingerprint_for(QuestionType.SINGLE_CHOICE, "  什么是 Ａ？")
    b = fingerprint_for(QuestionType.SINGLE_CHOICE, "什么是 a？")
    c = fingerprint_for(QuestionType.TRUE_FALSE, "什么是 a？")
    assert a == b
    assert a != c


def test_allocate_points_always_totals_one_hundred():
    assert allocate_points([1, 1, 1]) == [34, 33, 33]
    assert allocate_points([2, 1, 1]) == [50, 25, 25]
    assert sum(allocate_points([3] * 17)) == 100

