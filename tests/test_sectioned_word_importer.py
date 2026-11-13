from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.shared import Inches
from PIL import Image

from offline_quiz.domain import QuestionType
from offline_quiz.sectioned_word_importer import SectionedWordImporter


def _save_document(path: Path, lines: list[str]) -> Path:
    document = Document()
    for line in lines:
        document.add_paragraph(line)
    document.save(path)
    return path


def test_parses_five_sections_without_assuming_section_order(tmp_path):
    path = _save_document(
        tmp_path / "五类题.docx",
        [
            "机修钳工测试题库",
            "一、选择题",
            "1、正确选项是（ B ）。 A、错误 B、正确 C、不确定",
            "二、填空题",
            "1、构件是（ 独立运动 ）的单元，零件是（ 独立制造 ）的单元。",
            "三、判断题",
            "1、滚动轴承属于轴承。（√）",
            "四、简答题",
            "1、液压泵有什么作用？ 答：把机械能转换为压力能。",
            "五、计算题",
            "1. 已知2+3，求结果。",
            "解：2+3=5。",
            "答：5。",
        ],
    )

    result = SectionedWordImporter().parse(path)

    assert result.has_errors is False
    assert [question.question_type for question in result.questions] == [
        QuestionType.SINGLE_CHOICE,
        QuestionType.FILL_BLANK,
        QuestionType.TRUE_FALSE,
        QuestionType.SHORT_ANSWER,
        QuestionType.CALCULATION,
    ]
    assert result.questions[0].answer == "B"
    assert result.questions[0].options == {"A": "错误", "B": "正确", "C": "不确定"}
    assert result.questions[1].stem.count("____") == 2
    assert result.questions[1].answer == [["独立运动"], ["独立制造"]]
    assert result.questions[2].answer is True
    assert result.questions[3].answer == "把机械能转换为压力能。"
    assert result.questions[4].answer == "5。"
    assert result.questions[4].solution == "2+3=5。\n答：5。"
    assert result.questions[3].requires_manual_review is True
    assert result.questions[4].requires_manual_review is True


def test_parses_answer_variants_and_warns_about_duplicate_numbers(tmp_path):
    path = _save_document(
        tmp_path / "变体.docx",
        [
            "高级题库",
            "二、选择题",
            "1、大型工件划线常用（ ）作为辅助基准。",
            "答案：A",
            "A、拉线和吊线 B、外形 C、某个面",
            "1、轴系找中的目的是保证转子（ ）。 B",
            "A、升温 B、平稳 C、变形",
            "三、判断题",
            "1、螺纹千分尺用于测量螺纹大径。（ ） ×",
        ],
    )

    result = SectionedWordImporter().parse(path)

    assert result.has_errors is False
    assert [question.answer for question in result.questions] == ["A", "B", False]
    assert any("重复题号" in issue.message for issue in result.issues)
    assert all(issue.severity == "警告" for issue in result.issues)


def test_calculation_with_answer_omitted_requires_manual_review(tmp_path):
    path = _save_document(
        tmp_path / "计算.docx",
        [
            "计算题库",
            "五、计算题",
            "1、求主轴最高转速。",
            "解：nmax=1420×2=2840r/min。",
            "答：略。",
        ],
    )

    result = SectionedWordImporter().parse(path)

    question = result.questions[0]
    assert question.question_type is QuestionType.CALCULATION
    assert question.answer == "nmax=1420×2=2840r/min。\n答：略。"
    assert question.requires_manual_review is True


def test_media_between_question_boundaries_is_attached_to_current_question(tmp_path):
    image_path = tmp_path / "diagram.png"
    Image.new("RGB", (20, 10), "white").save(image_path)
    path = tmp_path / "媒体.docx"
    document = Document()
    document.add_paragraph("媒体题库")
    document.add_paragraph("五、计算题")
    document.add_paragraph("1、根据图示计算结果。")
    document.add_picture(str(image_path), width=Inches(1))
    document.add_paragraph("解：结果为10。")
    document.add_paragraph("答：10。")
    document.add_paragraph("2、没有图片的题目。")
    document.add_paragraph("解：结果为20。")
    document.add_paragraph("答：20。")
    document.save(path)

    result = SectionedWordImporter().parse(path)

    assert len(result.questions[0].assets) == 1
    assert result.questions[0].assets[0].mime_type == "image/png"
    assert result.questions[0].assets[0].data.startswith(b"\x89PNG")
    assert result.questions[1].assets == []


def test_missing_answer_is_reported_instead_of_silently_skipped(tmp_path):
    path = _save_document(
        tmp_path / "缺答案.docx",
        ["题库", "一、判断题", "1、这道题没有给出答案。"],
    )

    result = SectionedWordImporter().parse(path)

    assert result.questions == []
    assert result.has_errors is True
    assert "答案" in result.issues[0].message


def test_accepts_real_template_answer_labels_and_attached_choice_letter(tmp_path):
    path = _save_document(
        tmp_path / "真实变体.docx",
        [
            "题库",
            "一、选择题",
            "1、转速表指针方向与被测轴方向( )。B",
            "A．有关 B．无关",
            "二、简答题",
            "1、清洗包括哪些方面？",
            "答(1)装配前清洗；(2)装配后清洗。",
            "2、试车应注意什么？",
            "答、观察压力、温度和振动。",
            "3、控制阀有哪些？",
            "方向阀、压力阀、流量阀。",
        ],
    )

    result = SectionedWordImporter().parse(path)

    assert result.has_errors is False
    assert result.questions[0].answer == "B"
    assert result.questions[1].answer.startswith("(1)装配前")
    assert result.questions[2].answer == "观察压力、温度和振动。"
    assert result.questions[3].answer == "方向阀、压力阀、流量阀。"


def test_decimal_solution_lines_are_not_mistaken_for_question_numbers(tmp_path):
    path = _save_document(
        tmp_path / "小数题号.docx",
        [
            "题库",
            "五、计算题",
            "26、组合量块。",
            "解：28.965-1.005=27.96",
            "27.96-1.19=26.77",
            "26.77-6.5=20.27",
            "答：选用四块量块。",
            "27、求2+3。",
            "解：2+3=5。",
            "答：5。",
        ],
    )

    result = SectionedWordImporter().parse(path)

    assert result.has_errors is False
    assert len(result.questions) == 2
    assert "27.96-1.19" in result.questions[0].solution
    assert result.questions[1].answer == "5。"


def test_choice_without_source_answer_is_retained_for_manual_completion(tmp_path):
    path = _save_document(
        tmp_path / "缺少选择答案.docx",
        [
            "题库",
            "一、选择题",
            "1、齿轮变速机构属于( )。",
            "A．无级变速 B．有级变速 C．恒定速比",
        ],
    )

    result = SectionedWordImporter().parse(path)

    assert result.has_errors is False
    assert len(result.questions) == 1
    assert result.questions[0].answer == ""
    assert result.questions[0].requires_manual_review is True
    assert any(issue.severity == "警告" and "人工" in issue.message for issue in result.issues)


def test_calculation_with_image_only_solution_is_retained_for_manual_review(tmp_path):
    image_path = tmp_path / "formula.png"
    Image.new("RGB", (20, 10), "white").save(image_path)
    path = tmp_path / "图片公式.docx"
    document = Document()
    document.add_paragraph("题库")
    document.add_paragraph("五、计算题")
    document.add_paragraph("1、求液压泵输入功率。")
    document.add_paragraph("解：")
    document.add_picture(str(image_path), width=Inches(1))
    document.save(path)

    result = SectionedWordImporter().parse(path)

    assert result.has_errors is False
    assert len(result.questions) == 1
    assert result.questions[0].requires_manual_review is True
    assert result.questions[0].assets
    assert any(issue.severity == "警告" for issue in result.issues)
