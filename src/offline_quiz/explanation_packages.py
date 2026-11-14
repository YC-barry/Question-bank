from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from typing import Any

from docx import Document

from .domain import QuestionType
from .grading import normalize_boolean


SUPPORTED_LABELS = {
    "填空": QuestionType.FILL_BLANK,
    "选择": QuestionType.SINGLE_CHOICE,
    "判断": QuestionType.TRUE_FALSE,
}
ENTRY_HEADING_RE = re.compile(
    r"^(填空|选择|判断)\s*第\s*(\d+)\s*题(?:\s*〔[^〕]+〕)?\s*$"
)
OPTION_MARKER_RE = re.compile(r"(?<![A-Za-z0-9])([A-H])\s*[、．.，,]\s*", re.I)
SEMANTIC_SYMBOLS = set("+-−×÷*/=<>≤≥±%‰°′″'\"")


class DuplicateExplanationPackage(ValueError):
    def __init__(self, package_id: int, filename: str):
        super().__init__(f"相同内容的解析资料已导入：{filename}")
        self.package_id = package_id
        self.filename = filename


@dataclass(slots=True)
class ExplanationEntry:
    question_type: QuestionType
    source_number: int
    original_stem: str
    stem_fingerprint: str
    normalized_answer: str
    explanation: str


@dataclass(slots=True)
class ExplanationPackage:
    name: str
    filename: str
    subject: str
    level: str
    content_hash: str
    entries: list[ExplanationEntry] = field(default_factory=list)


def _text(value: Any) -> str:
    return unicodedata.normalize("NFKC", str(value or "")).strip()


def classify_mechanic_source(*values: str) -> tuple[str, str] | None:
    combined = " ".join(_text(value) for value in values if value)
    if "机修钳工" not in combined:
        return None
    levels = [level for level in ("初级", "中级", "高级") if level in combined]
    if len(levels) != 1:
        return None
    return "机修钳工", levels[0]


def _strip_choice_options(value: str) -> str:
    matches = list(OPTION_MARKER_RE.finditer(value))
    for index, match in enumerate(matches):
        if match.group(1).upper() != "A":
            continue
        if index + 1 < len(matches) and matches[index + 1].group(1).upper() == "B":
            return value[: match.start()].strip()
    return value


def _canonical_stem(question_type: QuestionType, stem: str) -> str:
    value = _text(stem)
    value = re.sub(r"^\s*\d+\s*[、.．]\s*", "", value)
    if question_type in {QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE}:
        value = _strip_choice_options(value)
        value = re.sub(r"答案\s*[:：]\s*[A-H]+", "", value, flags=re.I)
        value = re.sub(r"[（(]\s*[A-H](?:\s*[,，、]\s*[A-H])*\s*[）)]", "()", value, flags=re.I)
        value = re.sub(r"\s+[A-H](?:\s*[,，、]\s*[A-H])*\s*$", "", value, flags=re.I)
    elif question_type is QuestionType.FILL_BLANK:
        value = re.sub(r"[（(][^（）()]*[）)]", "¤", value)
    elif question_type is QuestionType.TRUE_FALSE:
        value = re.sub(r"[（(]\s*[√×对错]\s*[）)]", "", value)
        value = re.sub(r"\s*[√×]\s*$", "", value)
    value = re.sub(r"_{2,}", "¤", value)
    value = re.sub(r"[（(]\s*[）)]", "¤", value)
    canonical: list[str] = []
    folded = value.casefold()
    for index, character in enumerate(folded):
        category = unicodedata.category(character)
        if character == "¤" or category[0] in {"L", "N"}:
            canonical.append(character)
        elif character in SEMANTIC_SYMBOLS:
            canonical.append(character)
        elif (
            character == "."
            and index > 0
            and index + 1 < len(folded)
            and folded[index - 1].isdigit()
            and folded[index + 1].isdigit()
        ):
            canonical.append(character)
    normalized = "".join(canonical)
    if question_type is QuestionType.FILL_BLANK:
        normalized = re.sub(r"¤+", "¤", normalized)
    return normalized


def normalize_stem(question_type: QuestionType, stem: str) -> str:
    canonical = _canonical_stem(question_type, stem)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _normalize_answer_text(value: Any) -> str:
    text = _text(value)
    return re.sub(r"\s+", "", text).strip("。").casefold()


def normalize_answer(question_type: QuestionType, answer: Any) -> str:
    if question_type is QuestionType.TRUE_FALSE:
        if isinstance(answer, bool):
            return "true" if answer else "false"
        normalized = normalize_boolean(_text(answer))
        if normalized is None:
            raise ValueError("判断题参考答案无效")
        return "true" if normalized else "false"
    if question_type in {QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE}:
        if isinstance(answer, (list, tuple, set)):
            raw = "".join(map(str, answer))
        else:
            raw = _text(answer)
        letters = sorted(set(re.findall(r"[A-H]", raw.upper())))
        if not letters:
            unresolved = _normalize_answer_text(raw)
            if unresolved:
                return f"unresolved:{unresolved}"
            raise ValueError("选择题参考答案无效")
        return ",".join(letters)
    if question_type is QuestionType.FILL_BLANK:
        if isinstance(answer, str):
            groups: list[Any] = re.split(r"[;；]", answer)
        elif isinstance(answer, (list, tuple)):
            groups = list(answer)
        else:
            groups = [answer]
        normalized_groups: list[str] = []
        for group in groups:
            if isinstance(group, (list, tuple)):
                if not group:
                    normalized_groups.append("")
                    continue
                group = group[0]
            normalized_groups.append(_normalize_answer_text(group))
        if not normalized_groups or any(not group for group in normalized_groups):
            raise ValueError("填空题参考答案无效")
        return "|".join(normalized_groups)
    return _normalize_answer_text(answer)


def _field_value(lines: list[str], prefixes: tuple[str, ...]) -> str:
    for line in lines:
        for prefix in prefixes:
            if line.startswith(prefix):
                return line.split("：", 1)[1].strip() if "：" in line else line[len(prefix) :].strip()
    return ""


def _build_entry(label: str, number: int, lines: list[str]) -> ExplanationEntry:
    base_type = SUPPORTED_LABELS[label]
    stem = _field_value(lines, ("题目：", "题目:"))
    raw_answer = _field_value(
        lines,
        ("填空答案（原题）：", "填空答案(原题)：", "填空答案：", "参考答案："),
    )
    explanation_parts: list[str] = []
    collecting = False
    for line in lines:
        if line.startswith("解析") and ("：" in line or ":" in line):
            separator = "：" if "：" in line else ":"
            explanation_parts.append(line.split(separator, 1)[1].strip())
            collecting = True
        elif collecting and line and not line.startswith(("题目：", "参考答案：", "填空答案")):
            explanation_parts.append(line)
    explanation = "\n".join(part for part in explanation_parts if part).strip()
    missing = []
    if not stem:
        missing.append("题干")
    if not raw_answer:
        missing.append("答案")
    if not explanation:
        missing.append("解析")
    if missing:
        raise ValueError(f"{label}第{number}题缺少{'、'.join(missing)}")
    question_type = base_type
    if label == "选择":
        letters = sorted(set(re.findall(r"[A-H]", raw_answer.upper())))
        question_type = (
            QuestionType.MULTIPLE_CHOICE if len(letters) > 1 else QuestionType.SINGLE_CHOICE
        )
    answer_value: Any = raw_answer
    if label == "填空":
        embedded_answers = re.findall(r"[（(]([^（）()]*)[）)]", _text(stem))
        if embedded_answers and all(answer.strip() for answer in embedded_answers):
            answer_value = [[answer] for answer in embedded_answers]
    return ExplanationEntry(
        question_type=question_type,
        source_number=number,
        original_stem=stem,
        stem_fingerprint=normalize_stem(question_type, stem),
        normalized_answer=normalize_answer(question_type, answer_value),
        explanation=explanation,
    )


def _content_hash(subject: str, level: str, entries: list[ExplanationEntry]) -> str:
    normalized = {
        "subject": subject,
        "level": level,
        "entries": [
            {
                "type": entry.question_type.value,
                "number": entry.source_number,
                "stem": entry.stem_fingerprint,
                "answer": entry.normalized_answer,
                "explanation": _text(entry.explanation),
            }
            for entry in entries
        ],
    }
    payload = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def parse_explanation_docx(path: str | Path) -> ExplanationPackage:
    source = Path(path)
    try:
        document = Document(source)
    except Exception as exc:
        raise ValueError(f"无法读取解析 Word：{exc}") from exc
    title = next((paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()), source.stem)
    classification = classify_mechanic_source(title, source.stem)
    if classification is None:
        raise ValueError("无法识别机修钳工学科或初级、中级、高级级别")
    subject, level = classification
    entries: list[ExplanationEntry] = []
    current: tuple[str, int] | None = None
    lines: list[str] = []

    def flush() -> None:
        nonlocal current, lines
        if current is not None:
            entries.append(_build_entry(current[0], current[1], lines))
        current = None
        lines = []

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        match = ENTRY_HEADING_RE.match(text)
        if match and paragraph.style.name == "Heading 2":
            flush()
            current = (match.group(1), int(match.group(2)))
            continue
        if current is not None and text:
            if paragraph.style.name == "Heading 1":
                flush()
                continue
            lines.append(text)
    flush()
    if not entries:
        raise ValueError("未发现填空、选择或判断逐题解析记录")
    seen: set[tuple[QuestionType, int]] = set()
    for entry in entries:
        key = (entry.question_type, entry.source_number)
        if key in seen:
            raise ValueError(f"发现重复题号：{entry.question_type.value}第{entry.source_number}题")
        seen.add(key)
    return ExplanationPackage(
        name=title,
        filename=source.name,
        subject=subject,
        level=level,
        content_hash=_content_hash(subject, level, entries),
        entries=entries,
    )
