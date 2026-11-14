from __future__ import annotations

import shutil
from pathlib import Path

from docx import Document
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from offline_quiz.database import Database
from offline_quiz.domain import Question, QuestionType
from offline_quiz.import_service import ImportService
from offline_quiz.ui import BankPage
from offline_quiz.widgets.explanation_manager import ExplanationManagerDialog


def _save_package(path: Path, explanation: str = "轴承解析") -> Path:
    document = Document()
    document.add_heading("机修钳工初级工逐题解析", level=0)
    document.add_heading("选择题", level=1)
    document.add_heading("选择 第 1 题", level=2)
    document.add_paragraph("题目：滚动轴承的滚动体是（ A ）。 A、钢球 B、铜球")
    document.add_paragraph("参考答案：A")
    document.add_paragraph(f"解析（补充解析）：{explanation}")
    document.save(path)
    return path


def _silence_messages(monkeypatch, question_result=QMessageBox.Yes):
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: question_result)


def test_import_service_recognizes_explanation_word(tmp_path):
    database = Database(tmp_path / "quiz.db")
    path = _save_package(tmp_path / "explanations.docx")

    package = ImportService(database).preview_explanation(path)

    assert package.level == "初级"
    assert len(package.entries) == 1


def test_manager_imports_files_independently_and_lists_counts(qtbot, tmp_path, monkeypatch):
    database = Database(tmp_path / "quiz.db")
    good = _save_package(tmp_path / "good.docx")
    bad = tmp_path / "bad.docx"
    Document().save(bad)
    _silence_messages(monkeypatch)
    dialog = ExplanationManagerDialog(database)
    qtbot.addWidget(dialog)

    result = dialog.import_paths([str(bad), str(good)])

    assert result == {"imported": 1, "replaced": 0, "failed": 1, "cancelled": 0}
    assert dialog.table.rowCount() == 1
    assert [dialog.table.item(0, column).text() for column in range(2, 7)] == [
        "初级",
        "1",
        "0",
        "1",
        "0",
    ]


def test_duplicate_renamed_file_requires_replace_or_cancel(qtbot, tmp_path, monkeypatch):
    database = Database(tmp_path / "quiz.db")
    original = _save_package(tmp_path / "one.docx")
    renamed = tmp_path / "renamed.docx"
    shutil.copyfile(original, renamed)
    prompts: list[str] = []

    def replace(*args, **kwargs):
        prompts.append(args[2])
        return QMessageBox.Yes

    _silence_messages(monkeypatch)
    monkeypatch.setattr(QMessageBox, "question", replace)
    dialog = ExplanationManagerDialog(database)
    qtbot.addWidget(dialog)
    dialog.import_paths([str(original)])

    result = dialog.import_paths([str(renamed)])

    assert result["replaced"] == 1
    assert len(database.list_explanation_packages()) == 1
    assert database.list_explanation_packages()[0]["filename"] == "renamed.docx"
    assert any("相同内容" in prompt and "替换" in prompt and "取消" in prompt for prompt in prompts)


def test_delete_warning_is_explicit_and_only_deletes_package(qtbot, tmp_path, monkeypatch):
    database = Database(tmp_path / "quiz.db")
    package = ImportService(database).preview_explanation(_save_package(tmp_path / "one.docx"))
    database.import_explanation_package(package)
    prompts: list[str] = []

    def confirm(*args, **kwargs):
        prompts.append(args[2])
        return QMessageBox.Yes

    _silence_messages(monkeypatch)
    monkeypatch.setattr(QMessageBox, "question", confirm)
    dialog = ExplanationManagerDialog(database)
    qtbot.addWidget(dialog)
    dialog.table.setCurrentCell(0, 0)

    dialog.delete_selected()

    assert database.list_explanation_packages() == []
    assert any(
        all(word in prompt for word in ["只删除解析", "不删除题目", "错题", "答案", "成绩", "历史记录"])
        for prompt in prompts
    )


def test_bank_page_exposes_explanation_manager_entry(qtbot, tmp_path):
    page = BankPage(Database(tmp_path / "quiz.db"))
    qtbot.addWidget(page)

    assert page.explanation_button.text() == "解析资料"
    assert page.explanation_button.testAttribute(Qt.WA_Disabled) is False


def test_editing_question_metadata_does_not_write_package_text_into_original(
    qtbot, tmp_path
):
    database = Database(tmp_path / "quiz.db")
    bank_id = database.ensure_bank("机修钳工初级理论知识")
    question_id = database.upsert_question(
        bank_id,
        Question(
            bank_name="机修钳工初级理论知识",
            question_type=QuestionType.SINGLE_CHOICE,
            stem="滚动轴承的滚动体是（）。",
            options={"A": "钢球", "B": "铜球"},
            answer="A",
            explanation="原题解析",
        ),
    )
    package = ImportService(database).preview_explanation(
        _save_package(tmp_path / "one.docx", "资料包解析")
    )
    package_id = database.import_explanation_package(package)
    page = BankPage(database)
    qtbot.addWidget(page)
    page.table.setCurrentCell(0, 0)

    selected = page._selected_question()
    assert selected.explanation == "原题解析"
    selected.category = "只修改分类"
    database.update_question(question_id, selected)
    database.delete_explanation_package(package_id)

    assert database.get_question(question_id).explanation == "原题解析"
