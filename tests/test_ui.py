from offline_quiz.database import Database
from offline_quiz.domain import Question, QuestionType
from offline_quiz.ui import MainWindow, QuestionWidget, ReviewDialog
from PySide6.QtWidgets import QTableWidget


def test_main_window_has_required_navigation(qtbot, tmp_path):
    window = MainWindow(Database(tmp_path / "quiz.db"), tmp_path)
    qtbot.addWidget(window)

    labels = [button.text() for button in window.navigation_buttons.values()]

    assert labels == ["学习首页", "题库管理", "100 分试卷", "顺序刷题", "错题强化", "练习记录", "设置"]


def test_single_choice_widget_collects_selected_option(qtbot):
    question = Question(
        bank_name="示例",
        question_type=QuestionType.SINGLE_CHOICE,
        stem="请选择",
        options={"A": "甲", "B": "乙"},
        answer="B",
    )
    widget = QuestionWidget(question)
    qtbot.addWidget(widget)

    widget.option_buttons["B"].click()

    assert widget.answer() == "B"


def test_fill_blank_widget_creates_one_input_per_blank(qtbot):
    question = Question(
        bank_name="示例",
        question_type=QuestionType.FILL_BLANK,
        stem="城市和国家",
        answer=[["北京"], ["中国"]],
    )
    widget = QuestionWidget(question)
    qtbot.addWidget(widget)
    widget.blank_inputs[0].setText("北京")
    widget.blank_inputs[1].setText("中国")

    assert widget.answer() == ["北京", "中国"]


def test_review_dialog_displays_option_text_and_explanation(qtbot):
    dialog = ReviewDialog("回看", [{
        "snapshot": {
            "stem": "示例题", "answer": "A", "options": {"A": "甲", "B": "乙"},
            "points": 5, "explanation": "这是解析",
        },
        "user_answer": "B", "is_correct": 0, "earned_points": 0,
    }])
    qtbot.addWidget(dialog)
    table = dialog.findChild(QTableWidget)

    assert table.columnCount() == 7
    assert "A. 甲" in table.item(0, 3).text()
    assert table.item(0, 6).text() == "这是解析"
