from offline_quiz.importers import ExcelImporter, PowerPointImporter, WordImporter
from offline_quiz.domain import QuestionType
from offline_quiz.templates import TemplateService
from docx import Document
from pptx import Presentation


def test_exported_templates_can_be_imported_by_application(tmp_path):
    paths = TemplateService.export_all(tmp_path)

    assert {path.suffix for path in paths} == {".xlsx", ".docx", ".pptx"}
    results = {
        ".xlsx": ExcelImporter().parse(next(path for path in paths if path.suffix == ".xlsx")),
        ".docx": WordImporter().parse(next(path for path in paths if path.suffix == ".docx")),
        ".pptx": PowerPointImporter().parse(next(path for path in paths if path.suffix == ".pptx")),
    }
    assert all(not result.has_errors for result in results.values())
    assert all(len(result.questions) >= 5 for result in results.values())
    expected = {
        QuestionType.FILL_BLANK,
        QuestionType.TRUE_FALSE,
        QuestionType.SINGLE_CHOICE,
        QuestionType.SHORT_ANSWER,
        QuestionType.CALCULATION,
    }
    assert all({question.question_type for question in result.questions} == expected for result in results.values())


def test_template_export_does_not_overwrite_existing_files_by_default(tmp_path):
    existing = tmp_path / "题库模板.xlsx"
    existing.write_bytes(b"user content")

    try:
        TemplateService.export_all(tmp_path)
    except FileExistsError:
        pass
    else:
        raise AssertionError("expected FileExistsError")

    assert existing.read_bytes() == b"user content"


def test_word_template_title_is_black_and_has_no_border(tmp_path):
    path = TemplateService.export_word(tmp_path / "template.docx")
    document = Document(path)

    title = document.paragraphs[0]
    style = document.styles["Title"]

    assert title.style.name == "Title"
    assert style.font.color.rgb is not None
    assert str(style.font.color.rgb) == "000000"
    assert style.element.pPr.find(
        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pBdr"
    ) is None


def test_powerpoint_template_uses_fixed_text_boxes_without_clipping_geometry(tmp_path):
    path = TemplateService.export_powerpoint(tmp_path / "template.pptx")
    presentation = Presentation(path)

    assert len(presentation.slides) == 5
    for slide in presentation.slides:
        text_shapes = [shape for shape in slide.shapes if getattr(shape, "has_text_frame", False)]
        assert len(text_shapes) == 2
        title, body = text_shapes
        assert title.top >= 0
        assert body.top > title.top + title.height
        assert body.top + body.height <= presentation.slide_height
        assert "[题库] 示例题库" in title.text
        assert "[题型]" in body.text and "[答案]" in body.text
