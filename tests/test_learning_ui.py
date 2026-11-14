from __future__ import annotations

from PySide6.QtCore import QRect
from PySide6.QtWidgets import QApplication, QLabel, QMessageBox, QPushButton, QScrollArea, QWidget

from offline_quiz.app import apply_application_style
from offline_quiz.database import Database
from offline_quiz.domain import GradeResult, Question, QuestionType, QuizMode
from offline_quiz.quiz_service import QuizService
from offline_quiz.ui import (
    HomePage,
    MainWindow,
    QuizDialog,
    SessionSetupPage,
    WrongPage,
    fit_window_to_available,
)
from offline_quiz.widgets.answer_review import AnswerReviewPanel
from offline_quiz.widgets.question_navigator import QuestionNavigator
from offline_quiz.widgets.question_type_selector import QuestionTypeSelector


def _database_with_two_questions(tmp_path) -> Database:
    database = Database(tmp_path / "quiz.db")
    bank_id = database.ensure_bank("机修基础")
    for index in range(2):
        database.upsert_question(
            bank_id,
            Question(
                bank_name="机修基础",
                question_type=QuestionType.TRUE_FALSE,
                stem=f"示例判断题 {index}",
                answer=True,
                source_order=index,
            ),
        )
    return database


def test_dashboard_empty_state_shows_zero_statistics(qtbot, tmp_path):
    page = HomePage(Database(tmp_path / "empty.db"))
    qtbot.addWidget(page)

    assert page.stat_cards["banks"].value_label.text() == "0"
    assert page.stat_cards["questions"].value_label.text() == "0"
    assert page.stat_cards["wrong"].value_label.text() == "0"
    assert page.stat_cards["sessions"].value_label.text() == "0"
    assert page.scroll_area.widgetResizable()
    assert page.progress_ring.percent == 0
    assert page.trend_chart.values == [0] * 7
    assert all(bar.value() == 0 for bar in page.type_progress_bars.values())


def test_dashboard_refreshes_populated_bank_and_question_statistics(qtbot, tmp_path):
    page = HomePage(_database_with_two_questions(tmp_path))
    qtbot.addWidget(page)

    assert page.stat_cards["banks"].value_label.text() == "1"
    assert page.stat_cards["questions"].value_label.text() == "2"


def test_dashboard_learning_overview_reflects_answered_history(qtbot, tmp_path):
    database = _database_with_two_questions(tmp_path)
    session = QuizService(database).create_session({}, None, QuizMode.SEQUENTIAL)
    QuizService(database).answer_question(session, 0, False)

    page = HomePage(database)
    qtbot.addWidget(page)

    assert page.progress_ring.percent == 50
    assert page.progress_ring.practiced == 1
    assert page.trend_chart.values[-1] == 1
    assert page.type_progress_bars[QuestionType.TRUE_FALSE].value() == 50
    assert "已答 1 题" in page.recent_activity_labels[0].text()


def test_main_window_uses_seven_destination_navigation(qtbot, tmp_path):
    window = MainWindow(Database(tmp_path / "quiz.db"), tmp_path)
    qtbot.addWidget(window)

    labels = [button.text() for button in window.navigation_buttons.values()]

    assert labels == ["学习首页", "题库管理", "100 分试卷", "顺序刷题", "错题强化", "练习记录", "设置"]
    assert window.current_page_key == "home"


def test_dashboard_quick_exam_action_navigates_to_exam_setup(qtbot, tmp_path):
    window = MainWindow(Database(tmp_path / "quiz.db"), tmp_path)
    qtbot.addWidget(window)

    window.home_page.quick_exam_button.click()

    assert window.current_page_key == "exam"
    assert window.page_stack.currentWidget() is window.exam_page


def test_dashboard_common_history_action_navigates_to_history(qtbot, tmp_path):
    window = MainWindow(Database(tmp_path / "quiz.db"), tmp_path)
    qtbot.addWidget(window)

    window.home_page.common_action_buttons["history"].click()

    assert window.current_page_key == "history"
    assert window.page_stack.currentWidget() is window.history_page


def test_specialty_setup_includes_question_type_and_tag_filters(qtbot, tmp_path):
    page = SessionSetupPage(Database(tmp_path / "quiz.db"), QuizMode.SEQUENTIAL)
    qtbot.addWidget(page)
    for question_type, button in page.question_type_selector.buttons.items():
        if question_type is not QuestionType.CALCULATION:
            button.click()
    page.tag_edit.setText("液压")

    filters = page.filters()

    assert filters["question_types"] == [QuestionType.CALCULATION.value]
    assert filters["tag"] == "液压"


def test_question_type_selector_supports_combined_selection_and_keeps_one(qtbot):
    selector = QuestionTypeSelector()
    qtbot.addWidget(selector)

    assert selector.selected_values() == [item.value for item in QuestionType]

    for question_type, button in selector.buttons.items():
        if question_type is not QuestionType.TRUE_FALSE:
            button.click()
    assert selector.selected_values() == [QuestionType.TRUE_FALSE.value]

    selector.buttons[QuestionType.FILL_BLANK].click()
    assert selector.selected_values() == [
        QuestionType.TRUE_FALSE.value,
        QuestionType.FILL_BLANK.value,
    ]

    selector.buttons[QuestionType.TRUE_FALSE].click()
    selector.buttons[QuestionType.FILL_BLANK].click()
    assert selector.selected_values() == [QuestionType.FILL_BLANK.value]


def test_wrong_page_creates_sequential_session_from_unmastered_wrong_questions(qtbot, tmp_path):
    database = Database(tmp_path / "quiz.db")
    bank_id = database.ensure_bank("错题示例")
    database.upsert_question(
        bank_id,
        Question(
            bank_name="错题示例",
            question_type=QuestionType.TRUE_FALSE,
            stem="轴承安装后必须检查转动灵活性",
            answer=True,
        ),
    )
    original = QuizService(database).create_session({}, None, QuizMode.SEQUENTIAL)
    QuizService(database).answer_question(original, 0, False)
    page = WrongPage(database)
    qtbot.addWidget(page)

    session = page.create_wrong_session()

    assert session.mode is QuizMode.SEQUENTIAL
    assert session.filters["wrong_only"] is True
    assert [question.stem for question in session.questions] == ["轴承安装后必须检查转动灵活性"]


def test_answer_review_panel_is_large_and_emphasizes_correct_answer(qtbot):
    question = Question(
        bank_name="示例",
        question_type=QuestionType.SHORT_ANSWER,
        stem="液压泵的作用是什么？",
        answer="将机械能转换为液压能",
        explanation="液压泵为系统提供压力油。" * 20,
        points=10,
    )
    grade = GradeResult(False, 0, 10, question.answer, "输送液体", explanation=question.explanation)
    panel = AnswerReviewPanel()
    qtbot.addWidget(panel)

    assert panel.isHidden()
    panel.show_result(question, grade, "输送液体")

    assert not panel.isHidden()
    assert panel.minimumHeight() >= 240
    assert panel.correct_answer.toPlainText() == "将机械能转换为液压能"
    assert panel.correct_answer.font().pointSize() >= 14
    assert question.explanation in panel.explanation.toPlainText()


def test_exam_dialog_hides_answer_review_before_submission(qtbot, tmp_path):
    database = _database_with_two_questions(tmp_path)
    session = QuizService(database).create_session({}, 2, QuizMode.EXAM, seed=3)
    dialog = QuizDialog(database, session)
    qtbot.addWidget(dialog)

    assert dialog.answer_panel.isHidden()


def test_sequential_submission_reveals_large_answer_review(qtbot, tmp_path):
    database = _database_with_two_questions(tmp_path)
    session = QuizService(database).create_session({}, None, QuizMode.SEQUENTIAL)
    dialog = QuizDialog(database, session)
    qtbot.addWidget(dialog)
    dialog.current_widget.option_buttons["true"].click()

    dialog.submit_one()

    assert not dialog.answer_panel.isHidden()
    assert dialog.answer_panel.minimumHeight() >= 240
    assert dialog.answer_panel.correct_answer.toPlainText() == "对"


def test_question_navigator_exposes_current_result_and_lock_states(qtbot):
    navigator = QuestionNavigator(5)
    qtbot.addWidget(navigator)

    navigator.set_state(
        current=2,
        answered={0, 1},
        correct={0},
        wrong={1},
        enabled={0, 1, 2},
    )

    assert navigator.buttons[0].property("questionState") == "correct"
    assert navigator.buttons[1].property("questionState") == "wrong"
    assert navigator.buttons[2].property("questionState") == "current"
    assert navigator.buttons[2].isEnabled()
    assert not navigator.buttons[3].isEnabled()


def test_long_question_navigator_keeps_all_five_columns_inside_viewport(qtbot):
    navigator = QuestionNavigator(100)
    navigator.resize(navigator.width(), 560)
    qtbot.addWidget(navigator)
    navigator.show()
    QApplication.processEvents()

    scroll = navigator.findChild(QScrollArea)
    fifth_button = navigator.buttons[4]
    fifth_button_right = fifth_button.mapTo(
        scroll.viewport(), fifth_button.rect().bottomRight()
    ).x()

    assert scroll.horizontalScrollBar().maximum() == 0
    assert fifth_button_right < scroll.viewport().width()


def test_exam_question_navigator_saves_answer_and_jumps(qtbot, tmp_path):
    database = _database_with_two_questions(tmp_path)
    session = QuizService(database).create_session({}, 2, QuizMode.EXAM, seed=8)
    dialog = QuizDialog(database, session)
    qtbot.addWidget(dialog)
    first_id = dialog.current_widget.question.id
    dialog.current_widget.option_buttons["true"].click()

    dialog.question_navigator.buttons[1].click()

    assert dialog.index == 1
    assert dialog.answers[first_id] is True
    assert dialog.progress_bar.value() == 2
    assert dialog.progress_bar.maximum() == 2


def test_sequential_question_navigator_unlocks_next_after_submission(qtbot, tmp_path):
    database = _database_with_two_questions(tmp_path)
    session = QuizService(database).create_session({}, None, QuizMode.SEQUENTIAL)
    dialog = QuizDialog(database, session)
    qtbot.addWidget(dialog)

    assert not dialog.question_navigator.buttons[1].isEnabled()
    dialog.current_widget.option_buttons["true"].click()
    dialog.submit_one()

    assert dialog.question_navigator.buttons[1].isEnabled()


def test_sequential_true_false_click_grades_and_reveals_correct_answer(qtbot, tmp_path):
    database = _database_with_two_questions(tmp_path)
    session = QuizService(database).create_session({}, None, QuizMode.SEQUENTIAL)
    dialog = QuizDialog(database, session)
    qtbot.addWidget(dialog)

    dialog.current_widget.option_buttons["false"].click()

    assert 0 in session.results
    assert session.results[0].is_correct is False
    assert not dialog.answer_panel.isHidden()
    assert dialog.answer_panel.correct_answer.toPlainText() == "对"
    assert not dialog.current_widget.option_buttons["false"].isEnabled()
    assert dialog.submit_one_button.isHidden()


def test_sequential_correct_answer_auto_advances_after_feedback_delay(qtbot, tmp_path):
    database = _database_with_two_questions(tmp_path)
    session = QuizService(database).create_session({}, None, QuizMode.SEQUENTIAL)
    dialog = QuizDialog(database, session)
    qtbot.addWidget(dialog)

    dialog.current_widget.option_buttons["true"].click()

    assert dialog.index == 0
    assert not dialog.answer_panel.isHidden()
    qtbot.waitUntil(lambda: dialog.index == 1, timeout=900)
    assert dialog.answer_panel.isHidden()


def test_sequential_wrong_answer_stays_and_shows_review(qtbot, tmp_path):
    database = _database_with_two_questions(tmp_path)
    session = QuizService(database).create_session({}, None, QuizMode.SEQUENTIAL)
    dialog = QuizDialog(database, session)
    qtbot.addWidget(dialog)

    dialog.current_widget.option_buttons["false"].click()
    qtbot.wait(500)

    assert dialog.index == 0
    assert not dialog.answer_panel.isHidden()
    assert dialog.answer_panel.user_answer.toPlainText()
    assert dialog.answer_panel.correct_answer.toPlainText()
    assert dialog.answer_panel.explanation.toPlainText()


def test_sequential_final_correct_answer_stays_and_shows_completion(qtbot, tmp_path, monkeypatch):
    database = _database_with_two_questions(tmp_path)
    session = QuizService(database).create_session({}, None, QuizMode.SEQUENTIAL)
    dialog = QuizDialog(database, session)
    qtbot.addWidget(dialog)
    messages: list[tuple[str, str]] = []
    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda _parent, title, text: messages.append((title, text)) or QMessageBox.Ok,
    )
    dialog.current_widget.option_buttons["true"].click()
    dialog.next()

    dialog.current_widget.option_buttons["true"].click()
    qtbot.wait(500)

    assert dialog.index == 1
    assert not dialog.answer_panel.isHidden()
    assert messages


def test_scheduled_auto_advance_does_not_skip_after_manual_navigation(qtbot, tmp_path):
    database = _database_with_two_questions(tmp_path)
    bank_id = database.get_banks()[0]["id"]
    database.upsert_question(
        bank_id,
        Question(
            bank_name="机修基础",
            question_type=QuestionType.TRUE_FALSE,
            stem="第三题",
            answer=True,
            source_order=3,
        ),
    )
    session = QuizService(database).create_session({}, None, QuizMode.SEQUENTIAL)
    dialog = QuizDialog(database, session)
    qtbot.addWidget(dialog)

    dialog.current_widget.option_buttons["true"].click()
    dialog.next()
    qtbot.wait(500)

    assert dialog.index == 1


def test_scheduled_auto_advance_is_cancelled_after_forward_and_back_navigation(
    qtbot, tmp_path
):
    database = _database_with_two_questions(tmp_path)
    session = QuizService(database).create_session({}, None, QuizMode.SEQUENTIAL)
    dialog = QuizDialog(database, session)
    qtbot.addWidget(dialog)

    dialog.current_widget.option_buttons["true"].click()
    dialog.next()
    dialog.question_navigator.buttons[0].click()
    qtbot.wait(500)

    assert dialog.index == 0


def test_exam_correct_selection_never_auto_advances(qtbot, tmp_path):
    database = _database_with_two_questions(tmp_path)
    session = QuizService(database).create_session({}, 2, QuizMode.EXAM, seed=4)
    dialog = QuizDialog(database, session)
    qtbot.addWidget(dialog)

    dialog.current_widget.option_buttons["true"].click()
    qtbot.wait(500)

    assert dialog.index == 0
    assert session.results == {}


def test_sequential_navigator_restores_previous_answer_without_saving_again(qtbot, tmp_path):
    database = _database_with_two_questions(tmp_path)
    bank_id = database.get_banks()[0]["id"]
    database.upsert_question(
        bank_id,
        Question(
            bank_name="机修基础",
            question_type=QuestionType.TRUE_FALSE,
            stem="尚未作答的第三题",
            answer=True,
            source_order=2,
        ),
    )
    session = QuizService(database).create_session({}, None, QuizMode.SEQUENTIAL)
    dialog = QuizDialog(database, session)
    qtbot.addWidget(dialog)

    dialog.current_widget.option_buttons["false"].click()
    dialog.question_navigator.buttons[1].click()
    dialog.current_widget.option_buttons["true"].click()
    saved_before_review = len(database.get_session(session.id)["items"])

    dialog.question_navigator.buttons[0].click()

    assert dialog.index == 0
    assert dialog.current_widget.option_buttons["false"].isChecked()
    assert dialog.answer_panel.correct_answer.toPlainText() == "对"
    assert len(database.get_session(session.id)["items"]) == saved_before_review


def test_sequential_previous_button_returns_to_completed_question(qtbot, tmp_path):
    database = _database_with_two_questions(tmp_path)
    session = QuizService(database).create_session({}, None, QuizMode.SEQUENTIAL)
    dialog = QuizDialog(database, session)
    qtbot.addWidget(dialog)

    dialog.current_widget.option_buttons["false"].click()
    dialog.next_button.click()

    assert dialog.index == 1
    assert dialog.previous_button.isEnabled()

    dialog.previous_button.click()

    assert dialog.index == 0
    assert dialog.current_widget.option_buttons["false"].isChecked()
    assert not dialog.answer_panel.isHidden()


def test_sequential_long_explanation_scrolls_as_one_panel(qtbot, tmp_path):
    database = _database_with_two_questions(tmp_path)
    first = database.list_questions()[0]
    first.explanation = "逐行说明机械原理。\n" * 80
    database.update_question(first.id, first)
    session = QuizService(database).create_session({}, None, QuizMode.SEQUENTIAL)
    dialog = QuizDialog(database, session)
    dialog.resize(960, 680)
    qtbot.addWidget(dialog)
    dialog.show()

    dialog.current_widget.option_buttons["false"].click()
    QApplication.processEvents()

    assert dialog.answer_scroll.widget() is dialog.answer_panel
    assert dialog.answer_scroll.horizontalScrollBar().maximum() == 0
    assert dialog.answer_scroll.verticalScrollBar().maximum() > 0
    assert dialog.answer_panel.explanation.verticalScrollBar().maximum() == 0


def test_exam_true_false_click_does_not_grade_before_submission(qtbot, tmp_path):
    database = _database_with_two_questions(tmp_path)
    session = QuizService(database).create_session({}, 2, QuizMode.EXAM, seed=2)
    dialog = QuizDialog(database, session)
    qtbot.addWidget(dialog)

    dialog.current_widget.option_buttons["false"].click()

    assert session.results == {}
    assert dialog.answer_panel.isHidden()
    assert dialog.current_widget.answer() is False


def test_application_style_is_applied_globally_to_top_level_dialogs(qtbot):
    application = QApplication.instance()
    previous = application.styleSheet()
    try:
        apply_application_style(application)
        assert "answerReviewPanel" in application.styleSheet()
        assert "questionNavigator" in application.styleSheet()
    finally:
        application.setStyleSheet(previous)


def test_large_windows_fit_inside_1366x768_available_desktop(qtbot):
    window = QWidget()
    qtbot.addWidget(window)

    fit_window_to_available(window, 1180, 780, QRect(0, 0, 1366, 728))

    assert window.width() <= 1180
    assert window.height() <= 680
    assert window.x() >= 0
    assert window.y() >= 0
    assert window.x() + window.width() <= 1366
    assert window.y() + window.height() <= 728


def test_blank_fill_answer_remains_pending_in_exam_navigator(qtbot, tmp_path):
    database = Database(tmp_path / "fill.db")
    bank_id = database.ensure_bank("填空题库")
    for index in range(2):
        database.upsert_question(
            bank_id,
            Question(
                bank_name="填空题库",
                question_type=QuestionType.FILL_BLANK,
                stem=f"第 {index + 1} 题：填写两个空",
                answer=[["轴"], ["孔"]],
                source_order=index,
            ),
        )
    session = QuizService(database).create_session({}, 2, QuizMode.EXAM, seed=1)
    dialog = QuizDialog(database, session)
    qtbot.addWidget(dialog)

    dialog.question_navigator.buttons[1].click()

    assert list(dialog.answers.values())[0] == ["", ""]
    assert dialog.question_navigator.buttons[0].property("questionState") == "pending"
