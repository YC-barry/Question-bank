from __future__ import annotations

import unicodedata
from typing import Any

from .domain import GradeResult, Question, QuestionType


TRUE_VALUES = {"对", "是", "true", "√", "正确", "1"}
FALSE_VALUES = {"错", "否", "false", "×", "错误", "0"}


def normalize_text(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold().strip()
    return " ".join(text.split())


def normalize_boolean(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    normalized = normalize_text(value)
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    return None


class GradingService:
    @staticmethod
    def grade(question: Question, user_answer: Any) -> GradeResult:
        if question.requires_manual_review or question.question_type in {
            QuestionType.SHORT_ANSWER,
            QuestionType.CALCULATION,
        }:
            from .subjective_grading import SubjectiveGradingService

            suggestion = SubjectiveGradingService().suggest(question, str(user_answer or ""))
            return GradeResult(
                is_correct=suggestion.suggested_points == question.points,
                earned_points=suggestion.suggested_points,
                total_points=question.points,
                correct_answer=question.answer,
                user_answer=user_answer,
                explanation=question.explanation,
                requires_confirmation=True,
                suggestion=suggestion,
            )
        correct = False
        if question.question_type is QuestionType.SINGLE_CHOICE:
            correct = normalize_text(user_answer) == normalize_text(question.answer)
        elif question.question_type is QuestionType.MULTIPLE_CHOICE:
            expected = [normalize_text(item) for item in question.answer]
            received = [normalize_text(item) for item in (user_answer or [])]
            correct = len(received) == len(set(received)) and set(received) == set(expected)
        elif question.question_type is QuestionType.TRUE_FALSE:
            expected_bool = normalize_boolean(question.answer)
            received_bool = normalize_boolean(user_answer)
            correct = received_bool is not None and received_bool == expected_bool
        elif question.question_type is QuestionType.FILL_BLANK:
            received = list(user_answer or [])
            answer_groups = list(question.answer or [])
            correct = len(received) == len(answer_groups) and all(
                normalize_text(value) in {normalize_text(alias) for alias in aliases}
                for value, aliases in zip(received, answer_groups)
            )
        return GradeResult(
            is_correct=correct,
            earned_points=question.points if correct else 0,
            total_points=question.points,
            correct_answer=question.answer,
            user_answer=user_answer,
            explanation=question.explanation,
        )
