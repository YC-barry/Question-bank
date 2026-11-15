from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QFrame, QLabel

from offline_quiz.assets import HERO_ARTWORK, REQUIRED_ICONS, asset_path, load_svg_icon
from offline_quiz.database import Database
from offline_quiz.domain import GradeResult, Question, QuestionType
from offline_quiz.theme import ThemeTokens, build_app_style
from offline_quiz.ui import MainWindow
from offline_quiz.widgets.answer_review import AnswerReviewPanel


def test_required_visual_assets_resolve_to_valid_local_svg_files():
    declared_assets = [HERO_ARTWORK, *(f"icons/{name}.svg" for name in REQUIRED_ICONS)]

    for relative_name in declared_assets:
        path = asset_path(relative_name)
        assert path.is_file(), relative_name
        assert QSvgRenderer(str(path)).isValid(), relative_name
        source = path.read_text(encoding="utf-8").lower()
        assert '<image href="http' not in source
        assert 'xlink:href="http' not in source
        assert "<script" not in source


def test_svg_icon_loader_returns_cached_non_null_icons(qapp):
    first = load_svg_icon("house", ThemeTokens.PRIMARY, 24)
    second = load_svg_icon("house", ThemeTokens.PRIMARY, 24)

    assert not first.isNull()
    assert first is second


def test_theme_builds_reference_ice_blue_palette():
    style = build_app_style()

    assert ThemeTokens.PALE_BLUE == "#DFEBFD"
    assert ThemeTokens.CANVAS == "#F4F8FF"
    assert ThemeTokens.PRIMARY == "#2F7FEA"
    assert ThemeTokens.TEXT == "#12345B"
    assert ThemeTokens.BORDER == "#D6E3F4"
    assert "QFrame#navigationRail" in style
    assert "QFrame#heroCard" in style
    assert ThemeTokens.PALE_BLUE in style


def test_navigation_and_dashboard_actions_use_local_vector_icons(qtbot, tmp_path):
    window = MainWindow(Database(tmp_path / "quiz.db"), tmp_path)
    qtbot.addWidget(window)

    assert all(not button.icon().isNull() for button in window.navigation_buttons.values())
    assert not window.home_page.quick_sequential_button.icon().isNull()
    assert not window.home_page.quick_exam_button.icon().isNull()
    assert not window.home_page.quick_import_button.icon().isNull()
    assert all(
        not button.icon().isNull()
        for button in window.home_page.common_action_buttons.values()
    )
    assert window.home_page.hero_artwork.renderer().isValid()


def test_answer_review_uses_icon_and_text_for_result_state(qtbot):
    question = Question(
        bank_name="示例",
        question_type=QuestionType.TRUE_FALSE,
        stem="设备运行前应检查防护装置。",
        answer=True,
    )
    panel = AnswerReviewPanel()
    qtbot.addWidget(panel)

    panel.show_result(
        question,
        GradeResult(True, 1, 1, True, True, explanation="防护装置必须有效。"),
        True,
    )

    assert panel.status_label.text() == "回答正确"
    assert not panel.status_icon.pixmap().isNull()
    assert panel.property("resultState") == "correct"


def test_settings_page_uses_card_layout_and_local_action_icons(qtbot, tmp_path):
    window = MainWindow(Database(tmp_path / "quiz.db"), tmp_path)
    qtbot.addWidget(window)

    assert window.settings_page.findChild(QFrame, "settingsCard") is not None
    assert window.settings_page.findChild(QFrame, "learningDataCard") is not None
    assert len(window.settings_page.action_buttons) == 4
    assert len(window.settings_page.learning_data_buttons) == 3
    assert all(
        not button.icon().isNull()
        for button in window.settings_page.action_buttons.values()
    )
    assert all(
        not button.icon().isNull()
        for button in window.settings_page.learning_data_buttons.values()
    )
    assert "QFrame#learningDataCard" in window.styleSheet()


def test_settings_page_shows_ownership_notice_below_offline_summary(qtbot, tmp_path):
    window = MainWindow(Database(tmp_path / "quiz.db"), tmp_path)
    qtbot.addWidget(window)

    notice = window.settings_page.findChild(QLabel, "copyrightNotice")
    offline_summary = window.settings_page.findChild(QFrame, "overviewPanel")

    assert notice is not None
    assert notice.text() == (
        "本软件由雨辰开发并维护，未经许可请勿复制、修改或用于商业用途。"
    )
    assert notice.wordWrap()
    assert notice.alignment() & Qt.AlignHCenter
    assert window.settings_page.layout().indexOf(notice) == (
        window.settings_page.layout().indexOf(offline_summary) + 1
    )
    assert "QLabel#copyrightNotice" in window.styleSheet()


def test_selected_navigation_icon_switches_to_primary_tone(qtbot, tmp_path):
    window = MainWindow(Database(tmp_path / "quiz.db"), tmp_path)
    qtbot.addWidget(window)
    selected_home_icon = window.navigation_buttons["home"].icon().cacheKey()
    unselected_bank_icon = window.navigation_buttons["bank"].icon().cacheKey()

    window.navigate("bank")

    assert window.navigation_buttons["home"].icon().cacheKey() != selected_home_icon
    assert window.navigation_buttons["bank"].icon().cacheKey() != unselected_bank_icon
