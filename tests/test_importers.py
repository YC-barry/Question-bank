from pathlib import Path

from docx import Document
from openpyxl import Workbook
from pptx import Presentation

from offline_quiz.database import Database
from offline_quiz.domain import DuplicatePolicy, QuestionType
from offline_quiz.importers import ExcelImporter, PowerPointImporter, WordImporter
from offline_quiz.import_service import ImportService


HEADERS = [
    "分类", "题型", "题干", "选项A", "选项B", "选项C", "选项D",
    "选项E", "选项F", "选项G", "选项H", "正确答案", "答案别名",
    "解析", "难度", "标签", "分值",
]


def test_excel_imports_sheet_as_bank_and_preserves_order(tmp_path):
    path = tmp_path / "questions.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "安全培训"
    sheet.append(HEADERS)
    sheet.append(["基础", "单选", "安全色是什么？", "红色", "蓝色", None, None, None, None, None, None, "A", None, "红色用于警示", "简单", "安全,颜色", 2])
    sheet.append(["基础", "填空", "首都是____。", None, None, None, None, None, None, None, None, "北京|北京市", None, "", "中等", "地理", 1])
    workbook.save(path)

    result = ExcelImporter().parse(path)

    assert result.has_errors is False
    assert [q.source_order for q in result.questions] == [1, 2]
    assert result.questions[0].bank_name == "安全培训"
    assert result.questions[0].answer == "A"
    assert result.questions[1].answer == [["北京", "北京市"]]


def test_excel_reports_missing_required_column(tmp_path):
    path = tmp_path / "bad.xlsx"
    workbook = Workbook()
    workbook.active.append(["题型", "题干"])
    workbook.save(path)

    result = ExcelImporter().parse(path)

    assert result.has_errors is True
    assert any(issue.field == "正确答案" for issue in result.issues)


def test_word_imports_fixed_marker_blocks(tmp_path):
    path = tmp_path / "questions.docx"
    document = Document()
    for line in [
        "[题库] 安全培训", "[分类] 基础", "[题型] 多选", "[题干] 哪些属于安全色？",
        "[A] 红", "[B] 蓝", "[C] 紫", "[答案] A,B", "[别名]", "[解析] 红蓝均属于安全色",
        "[难度] 中等", "[标签] 安全,颜色", "[分值] 4", "---",
    ]:
        document.add_paragraph(line)
    document.save(path)

    result = WordImporter().parse(path)

    assert result.has_errors is False
    assert len(result.questions) == 1
    assert result.questions[0].question_type is QuestionType.MULTIPLE_CHOICE
    assert result.questions[0].answer == ["A", "B"]


def test_powerpoint_imports_one_question_per_slide(tmp_path):
    path = tmp_path / "questions.pptx"
    presentation = Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[1])
    slide.shapes.title.text = "[题库] 安全培训"
    slide.placeholders[1].text = "\n".join([
        "[分类] 基础", "[题型] 判断", "[题干] 安全第一。", "[答案] 对",
        "[解析] 安全应放在首位", "[难度] 简单", "[标签] 安全", "[分值] 2",
    ])
    presentation.save(path)

    result = PowerPointImporter().parse(path)

    assert result.has_errors is False
    assert len(result.questions) == 1
    assert result.questions[0].answer is True
    assert result.questions[0].source_order == 1


def test_import_service_rejects_unsupported_extension(tmp_path):
    path = tmp_path / "questions.pdf"
    path.write_text("not supported", encoding="utf-8")
    service = ImportService(Database(tmp_path / "quiz.db"))

    result = service.preview(path)

    assert result.has_errors is True
    assert "仅支持" in result.issues[0].message


def test_import_service_skips_then_overwrites_duplicate(tmp_path):
    path = tmp_path / "questions.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "安全培训"
    sheet.append(HEADERS)
    sheet.append(["基础", "单选", "第一题", "甲", "乙", None, None, None, None, None, None, "A", None, "旧解析", "简单", "", 1])
    workbook.save(path)
    database = Database(tmp_path / "quiz.db")
    service = ImportService(database)
    preview = service.preview(path)

    first = service.commit(preview, DuplicatePolicy.SKIP)
    skipped = service.commit(preview, DuplicatePolicy.SKIP)
    preview.questions[0].explanation = "新解析"
    overwritten = service.commit(preview, DuplicatePolicy.OVERWRITE)

    assert first.inserted == 1
    assert skipped.skipped == 1
    assert overwritten.overwritten == 1
    assert database.list_questions()[0].explanation == "新解析"


def test_excel_accepts_false_and_zero_for_judgment_answers(tmp_path):
    path = tmp_path / "judgment.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "判断题"
    sheet.append(HEADERS)
    sheet.append(["", "判断", "布尔假", None, None, None, None, None, None, None, None, False, None, "", "简单", "", 1])
    sheet.append(["", "判断", "数字零", None, None, None, None, None, None, None, None, 0, None, "", "简单", "", 1])
    workbook.save(path)

    result = ExcelImporter().parse(path)

    assert result.has_errors is False
    assert [question.answer for question in result.questions] == [False, False]


def test_fill_blank_import_merges_answer_alias_column(tmp_path):
    path = tmp_path / "aliases.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "别名"
    sheet.append(HEADERS)
    sheet.append(["", "填空", "首都是____", None, None, None, None, None, None, None, None, "北京", "北京市|京城", "", "简单", "", 1])
    workbook.save(path)

    result = ExcelImporter().parse(path)

    assert result.questions[0].answer == [["北京", "北京市", "京城"]]


def test_fractional_points_are_rejected(tmp_path):
    path = tmp_path / "fraction.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "分值"
    sheet.append(HEADERS)
    sheet.append(["", "判断", "题目", None, None, None, None, None, None, None, None, "对", None, "", "简单", "", 1.5])
    workbook.save(path)

    result = ExcelImporter().parse(path)

    assert result.has_errors is True
    assert "正整数" in result.issues[0].message


def test_import_commit_rolls_back_all_questions_on_failure(tmp_path, monkeypatch):
    path = tmp_path / "atomic.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "原子导入"
    sheet.append(HEADERS)
    for stem in ("第一题", "第二题"):
        sheet.append(["", "判断", stem, None, None, None, None, None, None, None, None, "对", None, "", "简单", "", 1])
    workbook.save(path)
    database = Database(tmp_path / "quiz.db")
    service = ImportService(database)
    result = service.preview(path)
    original = database._upsert_question_with_connection
    calls = 0

    def fail_second(connection, bank_id, question, overwrite):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated disk failure")
        return original(connection, bank_id, question, overwrite)

    monkeypatch.setattr(database, "_upsert_question_with_connection", fail_second)

    try:
        service.commit(result, DuplicatePolicy.SKIP)
    except OSError:
        pass
    else:
        raise AssertionError("expected OSError")

    assert database.list_questions() == []


def test_excel_and_fixed_templates_accept_short_answer_and_calculation(tmp_path):
    path = tmp_path / "subjective.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "主观题"
    sheet.append(HEADERS)
    sheet.append(["", "简答", "液压泵作用？", None, None, None, None, None, None, None, None, "转换能量", None, "", "中等", "", 5])
    sheet.append(["", "计算", "求2+3", None, None, None, None, None, None, None, None, "5", None, "2+3=5", "中等", "", 5])
    workbook.save(path)

    result = ExcelImporter().parse(path)

    assert result.has_errors is False
    assert [item.question_type for item in result.questions] == [
        QuestionType.SHORT_ANSWER,
        QuestionType.CALCULATION,
    ]
    assert all(item.requires_manual_review for item in result.questions)
    assert result.questions[1].solution == "2+3=5"
