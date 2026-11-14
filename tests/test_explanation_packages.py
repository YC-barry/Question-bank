from __future__ import annotations

from pathlib import Path

from docx import Document

from offline_quiz.domain import QuestionType
from offline_quiz.explanation_packages import (
    classify_mechanic_source,
    normalize_answer,
    normalize_stem,
    parse_explanation_docx,
)


def _save_explanation_document(path: Path) -> Path:
    document = Document()
    document.add_heading("机修钳工中级工理论知识｜逐题解析", level=0)
    document.add_paragraph("使用说明")
    document.add_heading("填空题", level=1)
    document.add_heading("填空 第 7 题", level=2)
    document.add_paragraph("题目：构件是（机械中独立运动）的单元。")
    document.add_paragraph("填空答案（原题）：机械中独立运动")
    document.add_paragraph("解析（补充解析）：构件可以独立运动。")
    document.add_heading("选择题", level=1)
    document.add_heading("选择 第 8 题", level=2)
    document.add_paragraph("题目：允许选择两个答案（ A、C ）。 A、甲 B、乙 C、丙")
    document.add_paragraph("参考答案：AC")
    document.add_paragraph("解析（Excel参考解析）：甲和丙都符合条件。")
    document.add_heading("判断题", level=1)
    document.add_heading("判断 第 9 题", level=2)
    document.add_paragraph("题目：滚动轴承属于轴承。（√）")
    document.add_paragraph("参考答案：√")
    document.add_paragraph("解析（补充解析）：该陈述正确。")
    document.save(path)
    return path


def test_classifies_only_mechanic_sources_with_a_known_level():
    assert classify_mechanic_source("机修钳工中级工理论知识") == ("机修钳工", "中级")
    assert classify_mechanic_source("机修钳工理论知识", "高级题库.docx") == ("机修钳工", "高级")
    assert classify_mechanic_source("电工中级题库") is None
    assert classify_mechanic_source("机修钳工理论知识") is None


def test_normalized_stems_match_imported_question_shapes_exactly():
    assert normalize_stem(
        QuestionType.FILL_BLANK,
        "1、构件是（机械中独立运动）的单元。",
    ) == normalize_stem(QuestionType.FILL_BLANK, "构件是____的单元。")
    assert normalize_stem(
        QuestionType.MULTIPLE_CHOICE,
        "允许选择两个答案（ A、C ）。 A、甲 B、乙 C、丙",
    ) == normalize_stem(QuestionType.MULTIPLE_CHOICE, "允许选择两个答案（）。")
    assert normalize_stem(
        QuestionType.TRUE_FALSE,
        "滚动轴承属于轴承。（√）",
    ) == normalize_stem(QuestionType.TRUE_FALSE, "滚动轴承属于轴承。")


def test_normalize_answer_is_type_aware_and_deterministic():
    assert normalize_answer(QuestionType.FILL_BLANK, "甲；乙") == normalize_answer(
        QuestionType.FILL_BLANK, [["甲"], ["乙"]]
    )
    assert normalize_answer(QuestionType.MULTIPLE_CHOICE, "CA") == "A,C"
    assert normalize_answer(QuestionType.MULTIPLE_CHOICE, ["C", "A"]) == "A,C"
    assert normalize_answer(QuestionType.TRUE_FALSE, "√") == "true"
    assert normalize_answer(QuestionType.TRUE_FALSE, False) == "false"


def test_normalization_preserves_semantic_numbers_and_operators():
    assert normalize_answer(QuestionType.FILL_BLANK, "1.5") != normalize_answer(
        QuestionType.FILL_BLANK, "15"
    )
    assert normalize_stem(
        QuestionType.FILL_BLANK, "当 x > 5 时，结果为（正数）。"
    ) != normalize_stem(
        QuestionType.FILL_BLANK, "当 x < 5 时，结果为（正数）。"
    )


def test_parse_explanation_docx_extracts_supported_records_and_hash(tmp_path):
    path = _save_explanation_document(tmp_path / "renamed.docx")

    package = parse_explanation_docx(path)

    assert package.name == "机修钳工中级工理论知识｜逐题解析"
    assert package.filename == "renamed.docx"
    assert package.subject == "机修钳工"
    assert package.level == "中级"
    assert len(package.content_hash) == 64
    assert [entry.source_number for entry in package.entries] == [7, 8, 9]
    assert [entry.question_type for entry in package.entries] == [
        QuestionType.FILL_BLANK,
        QuestionType.MULTIPLE_CHOICE,
        QuestionType.TRUE_FALSE,
    ]
    assert package.entries[0].normalized_answer == "机械中独立运动"
    assert package.entries[1].normalized_answer == "A,C"
    assert package.entries[2].normalized_answer == "true"
    assert package.entries[1].explanation == "甲和丙都符合条件。"
    assert all(entry.stem_fingerprint for entry in package.entries)


def test_parse_rejects_unknown_level_and_incomplete_records(tmp_path):
    unknown = Document()
    unknown.add_heading("机修钳工逐题解析", level=0)
    unknown_path = tmp_path / "unknown.docx"
    unknown.save(unknown_path)

    try:
        parse_explanation_docx(unknown_path)
    except ValueError as exc:
        assert "级别" in str(exc)
    else:
        raise AssertionError("expected unknown level to be rejected")

    broken = Document()
    broken.add_heading("机修钳工初级工逐题解析", level=0)
    broken.add_heading("填空 第 1 题", level=2)
    broken.add_paragraph("题目：缺少答案。")
    broken_path = tmp_path / "broken.docx"
    broken.save(broken_path)

    try:
        parse_explanation_docx(broken_path)
    except ValueError as exc:
        assert "答案" in str(exc)
    else:
        raise AssertionError("expected incomplete record to be rejected")
