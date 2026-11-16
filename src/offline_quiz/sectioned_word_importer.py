from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re

from docx import Document
from docx.oxml.ns import qn

from .domain import ImportIssue, ImportResult, Question, QuestionAsset, QuestionType
from .grading import normalize_boolean


SECTION_TYPES = {
    "填空题": QuestionType.FILL_BLANK,
    "判断题": QuestionType.TRUE_FALSE,
    "选择题": QuestionType.SINGLE_CHOICE,
    "简答题": QuestionType.SHORT_ANSWER,
    "计算题": QuestionType.CALCULATION,
}
SECTION_RE = re.compile(
    r"^\s*[一二三四五六七八九十0-9]+\s*[、.．]\s*(填空题|判断题|选择题|简答题|计算题)\s*$"
)
QUESTION_RE = re.compile(r"^\s*(\d+)\s*(?:、|[.．](?!\d))\s*(.*)$")
OPTION_RE = re.compile(r"(?<![A-Za-z0-9])([A-H])\s*[、.．]\s*")
RELAXED_OPTION_RE = re.compile(
    r"(?<![A-Za-z0-9])([A-H])(?:\s*[、.．]\s*|(?=[\u4e00-\u9fff]))"
)


@dataclass
class _QuestionBlock:
    number: int
    question_type: QuestionType
    lines: list[str] = field(default_factory=list)
    assets: list[QuestionAsset] = field(default_factory=list)


def _clean_text(value: str) -> str:
    return " ".join(value.replace("\u3000", " ").split())


def _paragraph_assets(paragraph, start_position: int) -> list[QuestionAsset]:
    assets: list[QuestionAsset] = []
    for offset, blip in enumerate(paragraph._p.xpath(".//a:blip")):
        relationship_id = blip.get(qn("r:embed"))
        if not relationship_id:
            continue
        part = paragraph.part.related_parts.get(relationship_id)
        if part is None or not getattr(part, "blob", None):
            continue
        assets.append(
            QuestionAsset(
                mime_type=str(getattr(part, "content_type", "application/octet-stream")),
                data=bytes(part.blob),
                position=start_position + offset,
            )
        )
    return assets


def _outer_parentheses(value: str) -> list[tuple[int, int, str]]:
    results: list[tuple[int, int, str]] = []
    stack: list[int] = []
    start = -1
    for index, character in enumerate(value):
        if character in "（(":
            if not stack:
                start = index
            stack.append(index)
        elif character in "）)" and stack:
            stack.pop()
            if not stack and start >= 0:
                results.append((start, index + 1, value[start + 1:index].strip()))
                start = -1
    return results


def _parse_fill(text: str) -> tuple[str, list[list[str]], bool]:
    groups = _outer_parentheses(text)
    if not groups:
        raise ValueError("填空题没有识别到完整答案")
    answers = [[content] if content else [] for _, _, content in groups]
    chunks: list[str] = []
    cursor = 0
    for start, end, _ in groups:
        chunks.append(text[cursor:start])
        chunks.append("____")
        cursor = end
    chunks.append(text[cursor:])
    return _clean_text("".join(chunks)), answers, any(not aliases for aliases in answers)


def _parse_judgment(text: str) -> tuple[str, bool]:
    pattern = re.compile(
        r"(?:[（(]\s*([√×对错])\s*[）)]|[（(]\s*[）)]\s*([√×对错])|\s+([√×对错]))\s*[。.]*\s*$"
    )
    match = pattern.search(text)
    if not match:
        raise ValueError("判断题没有识别到答案")
    raw_answer = next(group for group in match.groups() if group)
    answer = normalize_boolean(raw_answer)
    if answer is None:
        raise ValueError("判断题答案无效")
    stem = _clean_text(f"{text[:match.start()]}。".replace("。。", "。"))
    return stem, answer


def _answer_letters(value: str) -> list[str]:
    return re.findall(r"[A-H]", value.upper())


def _parse_choice(
    text: str,
) -> tuple[str, dict[str, str], str | list[str], QuestionType, bool]:
    option_matches = list(OPTION_RE.finditer(text))
    if len(option_matches) < 2:
        option_matches = list(RELAXED_OPTION_RE.finditer(text))
    if len(option_matches) < 2:
        return _clean_text(text), {}, "", QuestionType.SINGLE_CHOICE, True
    options: dict[str, str] = {}
    for index, match in enumerate(option_matches):
        end = option_matches[index + 1].start() if index + 1 < len(option_matches) else len(text)
        options[match.group(1)] = _clean_text(text[match.end():end])
    preamble = text[:option_matches[0].start()].strip()
    answer_match = re.search(r"答案\s*[:：]\s*([A-H](?:\s*[,，、]\s*[A-H])*)", preamble, re.I)
    if answer_match:
        letters = _answer_letters(answer_match.group(1))
        preamble = f"{preamble[:answer_match.start()]} {preamble[answer_match.end():]}"
    else:
        answer_match = re.search(r"[（(]\s*([A-H](?:\s*[,，、]\s*[A-H])*)\s*[）)]", preamble, re.I)
        if answer_match:
            letters = _answer_letters(answer_match.group(1))
            preamble = f"{preamble[:answer_match.start()]}（ ）{preamble[answer_match.end():]}"
        else:
            answer_match = re.search(
                r"(?:^|(?<=[\s。；;：:]))([A-H](?:\s*[,，、]\s*[A-H])*)\s*$",
                preamble,
                re.I,
            )
            if not answer_match:
                return _clean_text(preamble), options, "", QuestionType.SINGLE_CHOICE, True
            letters = _answer_letters(answer_match.group(1))
            preamble = preamble[:answer_match.start()]
    if not letters or len(letters) != len(set(letters)) or any(letter not in options for letter in letters):
        raise ValueError("选择题答案与选项不匹配")
    question_type = QuestionType.MULTIPLE_CHOICE if len(letters) > 1 else QuestionType.SINGLE_CHOICE
    answer: str | list[str] = letters if len(letters) > 1 else letters[0]
    return _clean_text(preamble), options, answer, question_type, False


def _split_label(text: str, label: str) -> tuple[str, str] | None:
    match = re.search(
        rf"(?<![\u4e00-\u9fff]){label}(?:\s*[:：、]\s*|\s+|(?=[（(]))",
        text,
    )
    if not match:
        return None
    return text[:match.start()].strip(), text[match.end():].strip()


def _parse_block(block: _QuestionBlock, bank_name: str, source_order: int) -> Question:
    joined = "\n".join(line for line in block.lines if line).strip()
    if not joined:
        raise ValueError("题干不能为空")
    common = {
        "bank_name": bank_name,
        "source_order": source_order,
        "assets": block.assets,
        "category": block.question_type.value,
    }
    if block.question_type is QuestionType.FILL_BLANK:
        stem, answer, incomplete = _parse_fill(joined)
        return Question(
            question_type=QuestionType.FILL_BLANK,
            stem=stem,
            answer=answer,
            requires_manual_review=incomplete,
            **common,
        )
    if block.question_type is QuestionType.TRUE_FALSE:
        stem, answer = _parse_judgment(joined)
        return Question(question_type=QuestionType.TRUE_FALSE, stem=stem, answer=answer, **common)
    if block.question_type is QuestionType.SINGLE_CHOICE:
        stem, options, answer, question_type, incomplete = _parse_choice(
            joined.replace("\n", " ")
        )
        return Question(
            question_type=question_type,
            stem=stem,
            answer=answer,
            options=options,
            requires_manual_review=incomplete,
            **common,
        )
    if block.question_type is QuestionType.SHORT_ANSWER:
        parts = _split_label(joined, "答")
        if parts is None and len(block.lines) > 1:
            parts = (block.lines[0], "\n".join(block.lines[1:]))
        if parts is None or not parts[1].strip():
            raise ValueError("简答题没有识别到标准答案")
        return Question(
            question_type=QuestionType.SHORT_ANSWER,
            stem=_clean_text(parts[0]),
            answer=parts[1],
            solution=parts[1],
            requires_manual_review=True,
            **common,
        )
    parts = _split_label(joined, "解")
    if parts is None:
        answer_only = _split_label(joined, "答")
        if answer_only is not None:
            stem, final_answer = answer_only
            solution = final_answer
        elif len(block.lines) > 1:
            stem, solution = block.lines[0], "\n".join(block.lines[1:])
            final_answer = solution
        else:
            stem, solution, final_answer = joined, "", ""
    else:
        stem, solution = parts
        final_answer = solution
    answer_parts = list(re.finditer(r"答\s*[:：]", solution))
    if answer_parts:
        candidate = solution[answer_parts[-1].end():].strip()
        if candidate and not re.fullmatch(r"略[。.]*", candidate):
            final_answer = candidate
    return Question(
        question_type=QuestionType.CALCULATION,
        stem=_clean_text(stem),
        answer=final_answer,
        solution=solution,
        requires_manual_review=True,
        **common,
    )


class SectionedWordImporter:
    def parse(self, path: str | Path, bank_name: str | None = None) -> ImportResult:
        source = Path(path)
        result = ImportResult(str(source))
        try:
            document = Document(source)
        except Exception as exc:
            result.issues.append(ImportIssue(str(source), "文件", "文件", f"无法读取 Word：{exc}"))
            return result
        title = bank_name or next(
            (_clean_text(paragraph.text) for paragraph in document.paragraphs if _clean_text(paragraph.text)),
            source.stem,
        )
        current_type: QuestionType | None = None
        current: _QuestionBlock | None = None
        seen_numbers: set[int] = set()
        found_section = False

        def flush() -> None:
            nonlocal current
            if current is None:
                return
            try:
                question = _parse_block(current, title, len(result.questions) + 1)
                result.questions.append(question)
                incomplete = (
                    question.requires_manual_review
                    and (
                        question.question_type
                        in {
                            QuestionType.SINGLE_CHOICE,
                            QuestionType.MULTIPLE_CHOICE,
                            QuestionType.FILL_BLANK,
                            QuestionType.TRUE_FALSE,
                        }
                        or (
                            question.question_type is QuestionType.CALCULATION
                            and (not question.answer or not question.solution)
                        )
                    )
                )
                if incomplete:
                    result.issues.append(
                        ImportIssue(
                            str(source),
                            f"{current.question_type.value}题第{current.number}题",
                            "答案",
                            "原文答案或选项不完整，已保留题目，需人工补充后评分",
                            severity="警告",
                        )
                    )
            except ValueError as exc:
                result.issues.append(
                    ImportIssue(
                        str(source),
                        f"{current.question_type.value}题第{current.number}题",
                        "答案",
                        str(exc),
                    )
                )
            current = None

        for paragraph in document.paragraphs:
            text = _clean_text(paragraph.text)
            section_match = SECTION_RE.match(text)
            if section_match:
                flush()
                current_type = SECTION_TYPES[section_match.group(1)]
                seen_numbers = set()
                found_section = True
                continue
            if current_type is None:
                continue
            question_match = QUESTION_RE.match(text)
            if question_match:
                flush()
                number = int(question_match.group(1))
                if number in seen_numbers:
                    result.issues.append(
                        ImportIssue(
                            str(source),
                            f"{current_type.value}题第{number}题",
                            "题号",
                            f"发现重复题号：{number}",
                            severity="警告",
                        )
                    )
                seen_numbers.add(number)
                current = _QuestionBlock(number, current_type, [question_match.group(2)])
            elif current is not None and text:
                current.lines.append(text)
            if current is not None:
                current.assets.extend(_paragraph_assets(paragraph, len(current.assets)))
        flush()
        if not found_section:
            result.issues.append(
                ImportIssue(str(source), "文件", "章节", "未发现填空、判断、选择、简答或计算题章节")
            )
        return result
