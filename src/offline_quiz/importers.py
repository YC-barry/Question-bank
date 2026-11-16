from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
import re
from typing import Any, Iterable

from docx import Document
from openpyxl import load_workbook
from pptx import Presentation

from .domain import ImportIssue, ImportResult, Question, QuestionType
from .grading import normalize_boolean, normalize_text


TYPE_MAP = {
    "单选": QuestionType.SINGLE_CHOICE,
    "单选题": QuestionType.SINGLE_CHOICE,
    "多选": QuestionType.MULTIPLE_CHOICE,
    "多选题": QuestionType.MULTIPLE_CHOICE,
    "判断": QuestionType.TRUE_FALSE,
    "判断题": QuestionType.TRUE_FALSE,
    "填空": QuestionType.FILL_BLANK,
    "填空题": QuestionType.FILL_BLANK,
    "简答": QuestionType.SHORT_ANSWER,
    "简答题": QuestionType.SHORT_ANSWER,
    "计算": QuestionType.CALCULATION,
    "计算题": QuestionType.CALCULATION,
}
DIFFICULTIES = {"简单", "中等", "困难"}
REQUIRED_COLUMNS = {"题型", "题干", "正确答案"}
OPTION_KEYS = tuple("ABCDEFGH")
MARKER_RE = re.compile(r"^\[([^\]]+)\]\s*(.*)$")


def _split_tags(value: Any) -> list[str]:
    return [item.strip() for item in re.split(r"[,，]", str(value or "")) if item.strip()]


def _parse_points(value: Any) -> int:
    if value is None or (isinstance(value, str) and not value.strip()):
        return 1
    if isinstance(value, bool):
        raise ValueError("分值必须为正整数")
    if isinstance(value, int):
        points = value
    elif isinstance(value, float) and value.is_integer():
        points = int(value)
    elif isinstance(value, str) and re.fullmatch(r"\+?\d+", value.strip()):
        points = int(value.strip())
    else:
        raise ValueError("分值必须为正整数")
    if points <= 0:
        raise ValueError("分值必须为正整数")
    return points


def _parse_answer(kind: QuestionType, raw: Any, options: dict[str, str]) -> Any:
    value = "" if raw is None else str(raw).strip()
    if not value:
        raise ValueError("正确答案不能为空")
    if kind is QuestionType.SINGLE_CHOICE:
        answer = normalize_text(value).upper()
        if answer not in options:
            raise ValueError("单选答案必须是已有选项编号")
        return answer
    if kind is QuestionType.MULTIPLE_CHOICE:
        answers = [item.strip().upper() for item in re.split(r"[,，]", value) if item.strip()]
        if len(answers) != len(set(answers)) or not answers or any(item not in options for item in answers):
            raise ValueError("多选答案必须是无重复的已有选项编号")
        return answers
    if kind is QuestionType.TRUE_FALSE:
        answer = normalize_boolean(value)
        if answer is None:
            raise ValueError("判断答案应为对/错、是/否、True/False 或 √/×")
        return answer
    if kind in {QuestionType.SHORT_ANSWER, QuestionType.CALCULATION}:
        return value
    groups = []
    for blank in value.split("||"):
        aliases = [item.strip() for item in blank.split("|") if item.strip()]
        if not aliases:
            raise ValueError("每个填空必须至少有一个答案")
        groups.append(aliases)
    return groups


def _raw_value(data: dict[str, Any], primary: str, fallback: str | None = None) -> Any:
    if primary in data and data[primary] is not None:
        return data[primary]
    return data.get(fallback) if fallback else None


def _build_question(data: dict[str, Any], bank_name: str, source_order: int) -> Question:
    raw_type = str(data.get("题型") or "").strip()
    if raw_type not in TYPE_MAP:
        raise ValueError(f"不支持的题型：{raw_type or '空'}")
    kind = TYPE_MAP[raw_type]
    stem = str(data.get("题干") or "").strip()
    if not stem:
        raise ValueError("题干不能为空")
    options: dict[str, str] = {}
    for key in OPTION_KEYS:
        raw_option = _raw_value(data, f"选项{key}", key)
        text = "" if raw_option is None else str(raw_option).strip()
        if text:
            options[key] = text
    if kind in {QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE} and len(options) < 2:
        raise ValueError("选择题至少需要两个选项")
    difficulty = str(data.get("难度") or "中等").strip()
    if difficulty not in DIFFICULTIES:
        raise ValueError("难度只能是简单、中等或困难")
    answer = _parse_answer(kind, _raw_value(data, "正确答案", "答案"), options)
    aliases: list[str] = []
    raw_aliases = _raw_value(data, "答案别名", "别名")
    if kind is QuestionType.FILL_BLANK and raw_aliases is not None and str(raw_aliases).strip():
        alias_groups = _parse_answer(kind, raw_aliases, options)
        if len(alias_groups) != len(answer):
            raise ValueError("答案别名的填空数量必须与正确答案一致")
        for group, alias_group in zip(answer, alias_groups):
            for alias in alias_group:
                if alias not in group:
                    group.append(alias)
                if alias not in aliases:
                    aliases.append(alias)
    explanation = str(data.get("解析") or "").strip()
    return Question(
        bank_name=bank_name.strip() or "未命名题库",
        question_type=kind,
        stem=stem,
        answer=answer,
        options=options,
        aliases=aliases,
        explanation=explanation,
        solution=explanation if kind is QuestionType.CALCULATION else str(answer),
        requires_manual_review=kind in {QuestionType.SHORT_ANSWER, QuestionType.CALCULATION},
        category=str(data.get("分类") or "").strip(),
        difficulty=difficulty,
        tags=_split_tags(data.get("标签")),
        points=_parse_points(data.get("分值")),
        source_order=source_order,
    )


class BaseImporter(ABC):
    @abstractmethod
    def parse(self, path: str | Path) -> ImportResult: ...


class ExcelImporter(BaseImporter):
    def parse(self, path: str | Path) -> ImportResult:
        source = Path(path)
        result = ImportResult(str(source))
        try:
            workbook = load_workbook(source, read_only=True, data_only=True)
        except Exception as exc:
            result.issues.append(ImportIssue(str(source), "文件", "文件", f"无法读取 Excel：{exc}"))
            return result
        try:
            for sheet in workbook.worksheets:
                rows = sheet.iter_rows(values_only=True)
                try:
                    headers = [str(value or "").strip() for value in next(rows)]
                except StopIteration:
                    result.issues.append(ImportIssue(str(source), sheet.title, "文件", "工作表为空"))
                    continue
                missing = REQUIRED_COLUMNS - set(headers)
                for field in sorted(missing):
                    result.issues.append(ImportIssue(str(source), sheet.title, field, f"缺少必填列：{field}"))
                if missing:
                    continue
                for row_number, values in enumerate(rows, start=2):
                    if not any(value not in (None, "") for value in values):
                        continue
                    data = dict(zip(headers, values))
                    try:
                        result.questions.append(_build_question(data, sheet.title, row_number - 1))
                    except ValueError as exc:
                        result.issues.append(ImportIssue(str(source), f"{sheet.title}!第{row_number}行", "题目", str(exc)))
        finally:
            workbook.close()
        return result


def _parse_marker_blocks(blocks: Iterable[tuple[str, list[str]]], source: Path) -> ImportResult:
    result = ImportResult(str(source))
    fallback_bank = source.stem
    for location, lines in blocks:
        data: dict[str, str] = {}
        current_key = ""
        for raw_line in lines:
            line = raw_line.strip()
            if not line or line == "---":
                continue
            match = MARKER_RE.match(line)
            if match:
                current_key = match.group(1).strip()
                value = match.group(2).strip()
                data[current_key] = value
            elif current_key:
                data[current_key] = f"{data[current_key]}\n{line}".strip()
        if not data:
            continue
        normalized = {
            "题型": data.get("题型"),
            "题干": data.get("题干"),
            "正确答案": data.get("答案"),
            "答案别名": data.get("别名"),
            "解析": data.get("解析"),
            "分类": data.get("分类"),
            "难度": data.get("难度"),
            "标签": data.get("标签"),
            "分值": data.get("分值"),
        }
        for key in OPTION_KEYS:
            normalized[f"选项{key}"] = data.get(key)
        try:
            result.questions.append(
                _build_question(normalized, data.get("题库") or fallback_bank, len(result.questions) + 1)
            )
        except ValueError as exc:
            result.issues.append(ImportIssue(str(source), location, "题目", str(exc)))
    if not result.questions and not result.issues:
        result.issues.append(ImportIssue(str(source), "文件", "题目", "未发现符合模板的题目"))
    return result


class WordImporter(BaseImporter):
    def parse(self, path: str | Path) -> ImportResult:
        source = Path(path)
        try:
            document = Document(source)
        except Exception as exc:
            return ImportResult(str(source), issues=[ImportIssue(str(source), "文件", "文件", f"无法读取 Word：{exc}")])
        blocks: list[tuple[str, list[str]]] = []
        current: list[str] = []
        start = 1
        for index, paragraph in enumerate(document.paragraphs, start=1):
            line = paragraph.text.strip()
            if line == "---":
                if current:
                    blocks.append((f"第{start}-{index}段", current))
                    current = []
                start = index + 1
            elif line:
                current.append(line)
        if current:
            blocks.append((f"第{start}-{len(document.paragraphs)}段", current))
        return _parse_marker_blocks(blocks, source)


class PowerPointImporter(BaseImporter):
    def parse(self, path: str | Path) -> ImportResult:
        source = Path(path)
        try:
            presentation = Presentation(source)
        except Exception as exc:
            return ImportResult(str(source), issues=[ImportIssue(str(source), "文件", "文件", f"无法读取 PowerPoint：{exc}")])
        blocks: list[tuple[str, list[str]]] = []
        for slide_number, slide in enumerate(presentation.slides, start=1):
            lines: list[str] = []
            for shape in slide.shapes:
                if not getattr(shape, "has_text_frame", False):
                    continue
                lines.extend(line for line in shape.text.splitlines() if line.strip())
            blocks.append((f"第{slide_number}页", lines))
        return _parse_marker_blocks(blocks, source)
