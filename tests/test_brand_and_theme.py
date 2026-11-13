from __future__ import annotations

from docx import Document
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QComboBox, QLabel, QLineEdit, QTableWidget, QWidget

from offline_quiz.app import apply_application_style, data_directory
from offline_quiz.database import Database
from offline_quiz.templates import TemplateService
from offline_quiz.ui import MainWindow


def test_light_surface_controls_keep_dark_text_under_dark_system_palette(qtbot):
    application = QApplication.instance()
    original_palette = QPalette(application.palette())
    original_style = application.styleSheet()
    dark_system_palette = QPalette(original_palette)
    for role in (
        QPalette.ColorRole.WindowText,
        QPalette.ColorRole.Text,
        QPalette.ColorRole.ButtonText,
    ):
        dark_system_palette.setColor(role, QColor("white"))
    dark_system_palette.setColor(QPalette.ColorRole.Base, QColor("white"))

    try:
        application.setPalette(dark_system_palette)
        apply_application_style(application)
        widgets = [QWidget(), QLineEdit(), QComboBox(), QTableWidget()]
        for widget in widgets:
            qtbot.addWidget(widget)
            widget.ensurePolished()

        combo = widgets[2]
        combo.addItem("机修钳工题库")
        combo.view().ensurePolished()

        assert widgets[0].palette().color(QPalette.ColorRole.WindowText).name() == "#12345b"
        assert widgets[1].palette().color(QPalette.ColorRole.Text).name() == "#12345b"
        assert widgets[3].palette().color(QPalette.ColorRole.Text).name() == "#12345b"
        assert combo.view().palette().color(QPalette.ColorRole.Text).name() == "#12345b"
        assert combo.view().palette().color(QPalette.ColorRole.Base).name() == "#ffffff"
    finally:
        application.setStyleSheet(original_style)
        application.setPalette(original_palette)


def test_main_window_displays_kuishuquiz_brand(qtbot, tmp_path):
    window = MainWindow(Database(tmp_path / "quiz.db"), tmp_path)
    qtbot.addWidget(window)

    assert window.windowTitle() == "岿枢题典"
    assert "岿枢题典" in [label.text() for label in window.findChildren(QLabel)]


def test_word_template_uses_kuishuquiz_brand(tmp_path):
    path = TemplateService.export_word(tmp_path / "template.docx")
    paragraphs = [paragraph.text for paragraph in Document(path).paragraphs]

    assert paragraphs[0] == "岿枢题典 Word 模板"
    assert "本模板用于建立可由岿枢题典直接导入的题库。" in paragraphs[1]


def test_brand_change_preserves_legacy_user_data_directory(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    assert data_directory() == tmp_path / "OfflineQuiz" / "data"
