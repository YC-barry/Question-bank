from __future__ import annotations

from dataclasses import replace
import random
from typing import Any

from .database import Database
from .domain import (
    GradeResult,
    QuestionType,
    QuizMode,
    QuizSession,
    SessionResult,
    allocate_points,
)
from .grading import GradingService


class QuizService:
    def __init__(self, database: Database):
        self.database = database

    def _questions_for(self, filters: dict[str, Any], *, ordered: bool) -> list:
        raw_types = filters.get("question_types") or None
        question_types = [item if isinstance(item, QuestionType) else QuestionType(item) for item in raw_types] if raw_types else None
        return self.database.list_questions(
            bank_ids=filters.get("bank_ids") or None,
            category=filters.get("category", ""),
            question_types=question_types,
            difficulty=filters.get("difficulty", ""),
            tag=filters.get("tag", ""),
            wrong_only=bool(filters.get("wrong_only", False)),
            ordered=ordered,
        )

    def create_session(
        self,
        filters: dict[str, Any],
        count: int | None,
        mode: QuizMode,
        seed: int | None = None,
    ) -> QuizSession:
        ordered = mode is QuizMode.SEQUENTIAL
        available = self._questions_for(filters, ordered=ordered)
        if not available:
            raise ValueError("当前筛选条件下没有可用题目")
        if ordered:
            selected = available if count is None else available[:count]
        else:
            requested = int(count or min(20, len(available)))
            if requested < 1:
                raise ValueError("抽题数量至少为 1")
            if requested > len(available):
                raise ValueError(f"当前条件仅有 {len(available)} 道题，无法抽取 {requested} 道")
            selected = random.Random(seed).sample(available, requested)
        if mode is QuizMode.EXAM:
            points = allocate_points([question.points for question in selected])
            selected = [replace(question, points=point) for question, point in zip(selected, points)]
        session_id = self.database.create_session(mode.value, filters)
        return QuizSession(session_id, mode, selected, filters)

    def answer_question(self, session: QuizSession, index: int, user_answer: Any) -> GradeResult:
        if index < 0 or index >= len(session.questions):
            raise IndexError("题目序号超出范围")
        if index in session.results:
            raise ValueError("该题已经提交，不能重复作答")
        question = session.questions[index]
        grade = GradingService.grade(question, user_answer)
        session.results[index] = grade
        session.answers[index] = user_answer
        if not grade.requires_confirmation:
            self.database.save_session_item(
                session.id, question, user_answer, grade.is_correct, grade.earned_points
            )
            session.persisted_indexes.add(index)
        if len(session.results) == len(session.questions) and not any(
            item.requires_confirmation for item in session.results.values()
        ):
            self._complete_from_results(session)
        return grade

    def submit(self, session: QuizSession, answers: dict[int, Any]) -> SessionResult:
        if session.results:
            raise ValueError("已经逐题提交的会话不能再次整卷提交")
        grades: list[GradeResult] = []
        rows: list[tuple] = []
        answer_by_index: dict[int, Any] = {}
        for index, question in enumerate(session.questions):
            answer = answers.get(question.id)
            grade = GradingService.grade(question, answer)
            grades.append(grade)
            rows.append((question, answer, grade.is_correct, grade.earned_points))
            answer_by_index[index] = answer
        score = sum(item.earned_points for item in grades)
        total = sum(question.points for question in session.questions)
        requires_review = any(item.requires_confirmation for item in grades)
        if not requires_review:
            self.database.save_completed_exam(
                session.id,
                rows,
                score,
                total,
            )
        session.results.update(enumerate(grades))
        session.answers.update(answer_by_index)
        if not requires_review:
            session.persisted_indexes.update(range(len(session.questions)))
        return SessionResult(
            session_id=session.id,
            score=score,
            total=total,
            correct_count=sum(1 for item in grades if item.is_correct),
            question_count=len(session.questions),
            grades=grades,
            requires_review=requires_review,
        )

    def finalize_subjective(
        self, session: QuizSession, adjustments: dict[int, int]
    ) -> SessionResult:
        pending = [
            index
            for index, grade in session.results.items()
            if grade.requires_confirmation
        ]
        if not pending:
            raise ValueError("当前会话没有待人工确认的题目")
        for index in pending:
            question = session.questions[index]
            if question.id is None or question.id not in adjustments:
                raise ValueError("请确认每一道待复核题目的最终得分")
            points = adjustments[question.id]
            if isinstance(points, bool) or not isinstance(points, int):
                raise ValueError(f"人工得分必须是 0 到 {question.points} 的整数")
            if points < 0 or points > question.points:
                raise ValueError(f"人工得分必须在 0 到 {question.points} 之间")

        for index in pending:
            question = session.questions[index]
            points = adjustments[question.id]
            session.results[index] = replace(
                session.results[index],
                earned_points=points,
                is_correct=points == question.points,
                requires_confirmation=False,
            )

        complete = len(session.results) == len(session.questions)
        result_indexes = sorted(session.results)
        grades = [session.results[index] for index in result_indexes]
        score = sum(item.earned_points for item in grades)
        total = sum(session.questions[index].points for index in result_indexes)
        if session.mode is QuizMode.EXAM and not session.persisted_indexes:
            if not complete:
                raise ValueError("试卷尚未完成，不能生成最终成绩")
            rows = [
                (
                    question,
                    session.answers.get(index),
                    session.results[index].is_correct,
                    session.results[index].earned_points,
                )
                for index, question in enumerate(session.questions)
            ]
            self.database.save_completed_exam(session.id, rows, score, total)
            session.persisted_indexes.update(range(len(session.questions)))
        else:
            for index in result_indexes:
                if index in session.persisted_indexes:
                    continue
                question = session.questions[index]
                grade = session.results[index]
                self.database.save_session_item(
                    session.id,
                    question,
                    session.answers.get(index),
                    grade.is_correct,
                    grade.earned_points,
                )
                session.persisted_indexes.add(index)
            if complete:
                self.database.complete_session(session.id, score, total)
        return SessionResult(
            session_id=session.id,
            score=score,
            total=total,
            correct_count=sum(1 for item in grades if item.is_correct),
            question_count=len(grades),
            grades=grades,
            requires_review=False,
        )

    def _complete_from_results(self, session: QuizSession) -> SessionResult:
        grades = [session.results[index] for index in sorted(session.results)]
        score = sum(item.earned_points for item in grades)
        total = sum(question.points for question in session.questions)
        self.database.complete_session(session.id, score, total)
        return SessionResult(
            session_id=session.id,
            score=score,
            total=total,
            correct_count=sum(1 for item in grades if item.is_correct),
            question_count=len(session.questions),
            grades=grades,
            requires_review=any(item.requires_confirmation for item in grades),
        )


class HistoryService:
    def __init__(self, database: Database):
        self.database = database

    def list(self) -> list[dict[str, Any]]:
        return self.database.list_sessions()

    def get(self, session_id: int) -> dict[str, Any] | None:
        return self.database.get_session(session_id)

    def wrong_questions(self):
        return self.database.list_questions(wrong_only=True, ordered=True)

    def mark_mastered(self, question_id: int, mastered: bool = True) -> None:
        self.database.mark_mastered(question_id, mastered)
