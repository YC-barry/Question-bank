from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from offline_quiz.doc_converter import DocConversionService
from offline_quiz.domain import QuestionType
from offline_quiz.sectioned_word_importer import SectionedWordImporter


CASES = [
    (Path(r"E:\工作\题库\机修钳工理论知识初级.doc"), 750, "平行"),
    (Path(r"E:\工作\题库\机修钳工理论知识中级.doc"), 950, "基准"),
    (Path(r"E:\工作\题库\机修钳工理论知识高级.doc"), 790, "机械中独立运动"),
]


@pytest.mark.parametrize("source,minimum_count,first_fill_answer", CASES)
def test_real_mechanic_doc_converts_and_parses_all_five_types(
    source: Path, minimum_count: int, first_fill_answer: str
):
    if not source.exists():
        pytest.skip(f"真实验收源文件不存在：{source}")

    with DocConversionService().convert(source) as converted:
        result = SectionedWordImporter().parse(converted.path, source.stem)

    errors = [issue for issue in result.issues if issue.severity == "错误"]
    counts = Counter(question.question_type for question in result.questions)
    assert errors == []
    assert len(result.questions) >= minimum_count
    assert all(
        counts[kind] > 0
        for kind in [
            QuestionType.FILL_BLANK,
            QuestionType.TRUE_FALSE,
            QuestionType.SINGLE_CHOICE,
            QuestionType.SHORT_ANSWER,
            QuestionType.CALCULATION,
        ]
    )
    first_fill = next(
        question for question in result.questions if question.question_type is QuestionType.FILL_BLANK
    )
    assert first_fill.answer[0][0] == first_fill_answer
    assert any(question.assets for question in result.questions)
