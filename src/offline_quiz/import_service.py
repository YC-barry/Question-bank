from __future__ import annotations

from pathlib import Path

from .database import Database
from .doc_converter import DocConversionError, DocConversionService
from .domain import DuplicatePolicy, ImportIssue, ImportResult, ImportSummary
from .explanation_packages import ExplanationPackage, parse_explanation_docx
from .importers import ExcelImporter, PowerPointImporter, WordImporter
from .sectioned_word_importer import SectionedWordImporter


class ImportService:
    def __init__(
        self,
        database: Database,
        *,
        doc_converter: DocConversionService | None = None,
    ):
        self.database = database
        self.doc_converter = doc_converter or DocConversionService()

    def preview(self, path: str | Path) -> ImportResult:
        source = Path(path)
        if source.suffix.lower() == ".doc":
            try:
                with self.doc_converter.convert(source) as converted:
                    result = SectionedWordImporter().parse(converted.path, bank_name=source.stem)
                    result.source_path = str(source)
                    return result
            except DocConversionError as exc:
                return ImportResult(
                    str(source),
                    issues=[ImportIssue(str(source), "文件", "文件", str(exc))],
                )
        importer = {
            ".xlsx": ExcelImporter,
            ".docx": WordImporter,
            ".pptx": PowerPointImporter,
        }.get(source.suffix.lower())
        if importer is None:
            return ImportResult(
                str(source),
                issues=[ImportIssue(str(source), "文件", "格式", "仅支持 .doc、.docx、.xlsx 和 .pptx 文件")],
            )
        return importer().parse(source)

    def preview_explanation(self, path: str | Path) -> ExplanationPackage:
        source = Path(path)
        if source.suffix.lower() != ".docx":
            raise ValueError("解析资料仅支持 .docx Word 文件")
        return parse_explanation_docx(source)

    def commit(self, result: ImportResult, duplicate_policy: DuplicatePolicy) -> ImportSummary:
        if result.has_errors:
            raise ValueError("导入预览包含错误，请先修正题库文件")
        return self.database.commit_import(
            result.questions,
            Path(result.source_path).name,
            duplicate_policy,
        )
