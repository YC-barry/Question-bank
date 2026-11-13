from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
import json
import math
import unicodedata
from typing import Any


class QuestionType(str, Enum):
    SINGLE_CHOICE = "单选"
    MULTIPLE_CHOICE = "多选"
    TRUE_FALSE = "判断"
    FILL_BLANK = "填空"
    SHORT_ANSWER = "简答"
    CALCULATION = "计算"


class QuizMode(str, Enum):
    PRACTICE = "练习"
    EXAM = "考试"
    SEQUENTIAL = "顺序刷题"


class DuplicatePolicy(str, Enum):
    SKIP = "跳过"
    OVERWRITE = "覆盖"


@dataclass(slots=True)
class QuestionAsset:
    mime_type: str
    data: bytes
    position: int
    alt_text: str = ""


@dataclass(slots=True)
class Question:
    bank_name: str
    question_type: QuestionType
    stem: str
    answer: Any
    options: dict[str, str] = field(default_factory=dict)
    aliases: list[str] = field(default_factory=list)
    explanation: str = ""
    solution: str = ""
    requires_manual_review: bool = False
    assets: list[QuestionAsset] = field(default_factory=list)
    category: str = ""
    difficulty: str = "中等"
    tags: list[str] = field(default_factory=list)
    points: int = 1
    source_order: int = 0
    id: int | None = None
    bank_id: int | None = None

    @property
    def fingerprint(self) -> str:
        return fingerprint_for(self.question_type, self.stem)

    def snapshot(self) -> dict[str, Any]:
        data = asdict(self)
        data["question_type"] = self.question_type.value
        from .media import asset_to_snapshot

        data["assets"] = [asset_to_snapshot(asset) for asset in self.assets]
        return data


@dataclass(slots=True)
class GradeResult:
    is_correct: bool
    earned_points: int
    total_points: int
    correct_answer: Any
    user_answer: Any
    explanation: str = ""
    requires_confirmation: bool = False
    suggestion: SubjectiveSuggestion | None = None


@dataclass(slots=True)
class SubjectiveSuggestion:
    status: str
    suggested_points: int
    confidence: float
    reasons: list[str] = field(default_factory=list)
    requires_confirmation: bool = True


@dataclass(slots=True)
class ImportIssue:
    source: str
    location: str
    field: str
    message: str
    severity: str = "错误"


@dataclass(slots=True)
class ImportResult:
    source_path: str
    questions: list[Question] = field(default_factory=list)
    issues: list[ImportIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(issue.severity == "错误" for issue in self.issues)


@dataclass(slots=True)
class ImportSummary:
    inserted: int = 0
    overwritten: int = 0
    skipped: int = 0


@dataclass(slots=True)
class QuizSession:
    id: int
    mode: QuizMode
    questions: list[Question]
    filters: dict[str, Any]
    results: dict[int, GradeResult] = field(default_factory=dict)
    answers: dict[int, Any] = field(default_factory=dict)
    persisted_indexes: set[int] = field(default_factory=set)


@dataclass(slots=True)
class SessionResult:
    session_id: int
    score: int
    total: int
    correct_count: int
    question_count: int
    grades: list[GradeResult]
    requires_review: bool = False

    @property
    def accuracy(self) -> float:
        return self.correct_count / self.question_count if self.question_count else 0.0


def _normalized_fingerprint_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold().strip()
    return " ".join(normalized.split())


def fingerprint_for(question_type: QuestionType, stem: str) -> str:
    payload = f"{question_type.value}\n{_normalized_fingerprint_text(stem)}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def allocate_points(weights: list[int]) -> list[int]:
    """按权重把整数分值分配到题目上，并保证总分精确为 100。"""
    if not weights:
        raise ValueError("试卷至少需要一道题")
    if len(weights) > 100:
        raise ValueError("100 分试卷最多支持 100 道题")
    safe_weights = [max(1, int(weight or 1)) for weight in weights]
    total = sum(safe_weights)
    raw = [100 * weight / total for weight in safe_weights]
    result = [math.floor(value) for value in raw]
    remainder = 100 - sum(result)
    order = sorted(range(len(raw)), key=lambda i: (-(raw[i] - result[i]), i))
    for index in order[:remainder]:
        result[index] += 1
    return result


def snapshot_json(question: Question) -> str:
    return json.dumps(question.snapshot(), ensure_ascii=False)
