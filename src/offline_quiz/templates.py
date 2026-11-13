from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from pptx import Presentation
from pptx.enum.text import MSO_AUTO_SIZE, MSO_VERTICAL_ANCHOR
from pptx.util import Inches, Pt as PptPt

from .branding import PRODUCT_NAME


HEADERS = [
    "分类", "题型", "题干", "选项A", "选项B", "选项C", "选项D",
    "选项E", "选项F", "选项G", "选项H", "正确答案", "答案别名",
    "解析", "难度", "标签", "分值",
]

SAMPLE_QUESTIONS = [
    {
        "分类": "基础知识", "题型": "单选", "题干": "安全生产的首要原则是什么？",
        "选项A": "安全第一", "选项B": "速度第一", "选项C": "成本第一", "选项D": "产量第一",
        "正确答案": "A", "答案别名": "", "解析": "安全生产坚持安全第一。",
        "难度": "简单", "标签": "安全,基础", "分值": 1,
    },
    {
        "分类": "基础知识", "题型": "填空", "题干": "安全生产应坚持____第一。",
        "正确答案": "安全|安全生产", "答案别名": "", "解析": "可填写“安全”或“安全生产”。",
        "难度": "中等", "标签": "安全,填空", "分值": 1,
    },
    {
        "分类": "基础知识", "题型": "判断", "题干": "作业前应检查工具状态。",
        "正确答案": "对", "答案别名": "", "解析": "工具检查可以降低作业风险。",
        "难度": "简单", "标签": "安全,判断", "分值": 1,
    },
    {
        "分类": "液压基础", "题型": "简答", "题干": "简述液压泵的作用。",
        "正确答案": "把机械能转换为液压能，并向系统提供压力油。", "答案别名": "",
        "解析": "人工复核时按能量转换和提供压力油两个要点评分。",
        "难度": "中等", "标签": "液压,简答", "分值": 5,
    },
    {
        "分类": "基础计算", "题型": "计算", "题干": "已知2+3，求结果。",
        "正确答案": "5", "答案别名": "", "解析": "2+3=5。",
        "难度": "简单", "标签": "计算", "分值": 5,
    },
]


def _marker_lines(question: dict[str, object], bank_name: str) -> list[str]:
    lines = [
        f"[题库] {bank_name}",
        f"[分类] {question.get('分类', '')}",
        f"[题型] {question.get('题型', '')}",
        f"[题干] {question.get('题干', '')}",
    ]
    for key in "ABCDEFGH":
        value = question.get(f"选项{key}", "")
        if value:
            lines.append(f"[{key}] {value}")
    lines.extend([
        f"[答案] {question.get('正确答案', '')}",
        f"[别名] {question.get('答案别名', '')}",
        f"[解析] {question.get('解析', '')}",
        f"[难度] {question.get('难度', '中等')}",
        f"[标签] {question.get('标签', '')}",
        f"[分值] {question.get('分值', 1)}",
    ])
    return lines


class TemplateService:
    @staticmethod
    def export_all(directory: str | Path, *, overwrite: bool = False) -> list[Path]:
        target = Path(directory)
        target.mkdir(parents=True, exist_ok=True)
        destinations = [
            target / "题库模板.xlsx",
            target / "题库模板.docx",
            target / "题库模板.pptx",
        ]
        existing = [path.name for path in destinations if path.exists()]
        if existing and not overwrite:
            raise FileExistsError(f"以下模板已存在：{'、'.join(existing)}")
        return [
            TemplateService.export_excel(destinations[0]),
            TemplateService.export_word(destinations[1]),
            TemplateService.export_powerpoint(destinations[2]),
        ]

    @staticmethod
    def export_excel(path: str | Path) -> Path:
        destination = Path(path)
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "示例题库"
        sheet.append(HEADERS)
        for question in SAMPLE_QUESTIONS:
            sheet.append([question.get(header, "") for header in HEADERS])
        for cell in sheet[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="2563EB")
            cell.alignment = Alignment(horizontal="center", vertical="center")
        widths = [14, 10, 36, 18, 18, 18, 18, 12, 12, 12, 12, 18, 18, 34, 10, 18, 10]
        for index, width in enumerate(widths, start=1):
            sheet.column_dimensions[get_column_letter(index)].width = width
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = f"A1:{get_column_letter(len(HEADERS))}{sheet.max_row}"
        for row in sheet.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(vertical="top", wrap_text=True)
        workbook.save(destination)
        return destination

    @staticmethod
    def export_word(path: str | Path) -> Path:
        destination = Path(path)
        document = Document()
        for section in document.sections:
            section.top_margin = Inches(0.7)
            section.bottom_margin = Inches(0.7)
            section.left_margin = Inches(0.85)
            section.right_margin = Inches(0.85)
        normal_style = document.styles["Normal"]
        normal_style.font.name = "SimSun"
        normal_style.font.size = Pt(10.5)
        normal_style.paragraph_format.space_after = Pt(0)
        normal_style.paragraph_format.line_spacing = 1.0
        title_style = document.styles["Title"]
        title_style.font.name = "Microsoft YaHei"
        title_style.font.size = Pt(24)
        title_style.font.bold = True
        title_style.font.color.rgb = RGBColor(0, 0, 0)
        title_properties = title_style.element.get_or_add_pPr()
        border = title_properties.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pBdr")
        if border is not None:
            title_properties.remove(border)
        document.add_paragraph(f"{PRODUCT_NAME} Word 模板", style="Title")
        document.add_paragraph(
            f"本模板用于建立可由{PRODUCT_NAME}直接导入的题库。"
            "每道题使用固定标记，并用单独一行的 --- 分隔；填写时请保留标记名称。"
        )
        for question in SAMPLE_QUESTIONS:
            for line in _marker_lines(question, "示例题库"):
                paragraph = document.add_paragraph(line)
                paragraph.paragraph_format.space_after = Pt(0)
                paragraph.paragraph_format.line_spacing = 1.0
            document.add_paragraph("---")
        document.save(destination)
        return destination

    @staticmethod
    def export_powerpoint(path: str | Path) -> Path:
        destination = Path(path)
        presentation = Presentation()
        presentation.slide_width = Inches(13.333)
        presentation.slide_height = Inches(7.5)
        for question in SAMPLE_QUESTIONS:
            slide = presentation.slides.add_slide(presentation.slide_layouts[6])
            title = slide.shapes.add_textbox(
                Inches(0.85), Inches(0.45), Inches(11.6), Inches(0.65)
            )
            title_frame = title.text_frame
            title_frame.clear()
            title_frame.vertical_anchor = MSO_VERTICAL_ANCHOR.MIDDLE
            title_paragraph = title_frame.paragraphs[0]
            title_paragraph.text = "[题库] 示例题库"
            title_paragraph.font.name = "Microsoft YaHei"
            title_paragraph.font.size = PptPt(24)
            title_paragraph.font.bold = True

            body = slide.shapes.add_textbox(
                Inches(0.85), Inches(1.25), Inches(11.6), Inches(5.75)
            )
            body_frame = body.text_frame
            body_frame.clear()
            body_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
            body_frame.word_wrap = True
            body_frame.margin_left = Inches(0.08)
            body_frame.margin_right = Inches(0.08)
            body_frame.margin_top = Inches(0.05)
            body_frame.margin_bottom = Inches(0.05)
            lines = _marker_lines(question, "示例题库")[1:]
            for index, line in enumerate(lines):
                paragraph = body_frame.paragraphs[0] if index == 0 else body_frame.add_paragraph()
                paragraph.text = line
                paragraph.font.name = "Microsoft YaHei"
                paragraph.font.size = PptPt(17)
                paragraph.space_after = PptPt(3)
        presentation.save(destination)
        return destination
