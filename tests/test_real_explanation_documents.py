from __future__ import annotations

from pathlib import Path

import pytest

from offline_quiz.explanation_packages import parse_explanation_docx


REAL_DOCUMENTS = [
    (Path(r"D:\机修钳工初级工_填空选择判断逐题解析.docx"), "初级", 599),
    (Path(r"D:\Machinist_Intermediate_Explanations.docx"), "中级", 792),
    (Path(r"D:\Machinist_Advanced_Explanations.docx"), "高级", 642),
]


@pytest.mark.parametrize(("path", "level", "expected_count"), REAL_DOCUMENTS)
def test_real_explanation_document_counts_and_completeness(path, level, expected_count):
    if not path.exists():
        pytest.skip(f"real explanation document is not available: {path}")

    package = parse_explanation_docx(path)

    assert package.subject == "机修钳工"
    assert package.level == level
    assert len(package.entries) == expected_count
    assert all(entry.original_stem for entry in package.entries)
    assert all(entry.normalized_answer for entry in package.entries)
    assert all(entry.explanation for entry in package.entries)
    assert len({(entry.question_type, entry.source_number) for entry in package.entries}) == expected_count
