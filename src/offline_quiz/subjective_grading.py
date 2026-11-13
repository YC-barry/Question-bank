from __future__ import annotations

from difflib import SequenceMatcher
import math
import re
import unicodedata

from .domain import Question, QuestionType, SubjectiveSuggestion


NUMBER_RE = re.compile(
    r"(?<![\d.])([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s*"
    r"(%|[a-zA-ZμµΩ°/·]+(?:\s*/\s*[a-zA-Z]+)?)?"
)


def _compact(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", text)


def _bigrams(value: str) -> set[str]:
    return {value[index:index + 2] for index in range(max(0, len(value) - 1))}


def _similarity(expected: str, received: str) -> float:
    if not expected or not received:
        return 0.0
    sequence = SequenceMatcher(None, expected, received).ratio()
    left, right = _bigrams(expected), _bigrams(received)
    jaccard = len(left & right) / len(left | right) if left or right else 0.0
    containment = len(left & right) / len(left) if left else 0.0
    return max(sequence, 0.65 * containment + 0.35 * jaccard)


def _normalize_unit(value: str) -> str:
    unit = unicodedata.normalize("NFKC", value or "").casefold().replace(" ", "")
    return unit.replace("µ", "μ")


def _numbers(value: object) -> list[tuple[float, str]]:
    results: list[tuple[float, str]] = []
    for match in NUMBER_RE.finditer(str(value or "")):
        number = float(match.group(1))
        unit = _normalize_unit(match.group(2) or "")
        if unit == "%":
            number /= 100.0
        results.append((number, unit))
    return results


class SubjectiveGradingService:
    def suggest(self, question: Question, user_answer: str) -> SubjectiveSuggestion:
        if question.question_type is QuestionType.SHORT_ANSWER:
            return self._suggest_short(question, user_answer)
        if question.question_type is QuestionType.CALCULATION:
            return self._suggest_calculation(question, user_answer)
        return SubjectiveSuggestion(
            status="待人工确认",
            suggested_points=0,
            confidence=0.0,
            reasons=["原题答案或选项不完整，不能安全地自动判分"],
        )

    def _suggest_short(self, question: Question, user_answer: str) -> SubjectiveSuggestion:
        expected = _compact(question.answer)
        received = _compact(user_answer)
        if not received:
            return SubjectiveSuggestion("建议错误", 0, 0.98, ["未填写答案"])
        if not expected:
            return SubjectiveSuggestion(
                "待人工确认", 0, 0.0, ["原文没有可比较的标准答案"]
            )
        similarity = _similarity(expected, received)
        if similarity >= 0.72:
            return SubjectiveSuggestion(
                "建议正确", question.points, min(0.99, similarity), ["与标准答案的核心内容高度一致"]
            )
        if similarity >= 0.22:
            points = max(1, min(question.points - 1, round(question.points * similarity)))
            return SubjectiveSuggestion(
                "建议部分正确", points, similarity, ["覆盖了部分标准答案内容"]
            )
        return SubjectiveSuggestion(
            "建议错误", 0, 1.0 - similarity, ["与标准答案的核心内容差异较大"]
        )

    def _suggest_calculation(
        self, question: Question, user_answer: str
    ) -> SubjectiveSuggestion:
        expected_text = str(question.answer or "")
        if not expected_text.strip() or re.search(r"答?\s*[:：]?\s*略", expected_text):
            return SubjectiveSuggestion(
                "待人工确认", 0, 0.0, ["原文未提供可可靠比较的最终数值"]
            )
        expected = _numbers(expected_text)
        received = _numbers(user_answer)
        if not received:
            return SubjectiveSuggestion("建议错误", 0, 0.95, ["未识别到作答数值"])
        if not expected:
            return SubjectiveSuggestion(
                "待人工确认", 0, 0.0, ["标准答案中未识别到可比较数值"]
            )

        used: set[int] = set()
        value_matches = 0
        unit_matches = 0
        for expected_value, expected_unit in expected:
            for index, (received_value, received_unit) in enumerate(received):
                if index in used:
                    continue
                tolerance = max(1e-8, abs(expected_value) * 1e-4)
                if not math.isclose(expected_value, received_value, abs_tol=tolerance, rel_tol=1e-4):
                    continue
                used.add(index)
                value_matches += 1
                if not expected_unit or expected_unit == received_unit:
                    unit_matches += 1
                break

        if value_matches == len(expected) and unit_matches == len(expected):
            return SubjectiveSuggestion(
                "建议正确", question.points, 0.95, ["最终数值和单位与标准答案一致"]
            )
        if value_matches:
            ratio = value_matches / len(expected)
            unit_ratio = unit_matches / len(expected)
            points = max(1, min(question.points - 1, round(question.points * (0.7 * ratio + 0.3 * unit_ratio))))
            reason = "部分结果正确" if value_matches < len(expected) else "数值一致但单位需复核"
            return SubjectiveSuggestion("建议部分正确", points, 0.6, [reason])
        return SubjectiveSuggestion("建议错误", 0, 0.9, ["最终数值与标准答案不一致"])
