from __future__ import annotations

import base64
from io import BytesIO

from PIL import Image
from PySide6.QtCore import QRect, Qt
from PySide6.QtWidgets import QApplication, QLabel, QScrollArea

from offline_quiz.domain import Question, QuestionAsset, QuestionType
from offline_quiz.widgets.exam_review import ExamReviewDialog, fit_review_to_available
from offline_quiz.widgets.media_view import MediaView


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9ZlS8AAAAASUVORK5CYII="
)


def _item(index: int, correct: bool, *, with_asset: bool = False) -> dict:
    question = Question(
        bank_name="机修钳工初级",
        question_type=QuestionType.SINGLE_CHOICE,
        stem=f"第{index + 1}题：请选择正确零件。" + ("长题干" * 80 if index == 1 else ""),
        options={"A": "轴承", "B": "齿轮"},
        answer="A",
        explanation="逐步解释机械原理。" * 80,
        solution="先识别结构，再核对工作条件。",
        points=10,
        assets=[QuestionAsset("image/png", PNG_1X1, 1, "结构图")] if with_asset else [],
    )
    return {
        "snapshot": question.snapshot(),
        "user_answer": "A" if correct else "B",
        "is_correct": int(correct),
        "earned_points": 10 if correct else 0,
    }


def test_exam_review_navigates_all_questions_and_updates_result_colors(qtbot):
    dialog = ExamReviewDialog(
        "试卷回看",
        [_item(0, True), _item(1, False), _item(2, True, with_asset=True)],
    )
    qtbot.addWidget(dialog)

    assert dialog.index == 0
    assert dialog.question_navigator.buttons[0].property("questionState") == "current"
    assert dialog.question_navigator.buttons[1].property("questionState") == "wrong"
    assert dialog.question_navigator.buttons[2].property("questionState") == "correct"

    dialog.question_navigator.buttons[1].click()
    assert dialog.index == 1
    assert "第2题" in dialog.stem_view.toPlainText()
    assert "B. 齿轮" in dialog.answer_panel.user_answer.toPlainText()
    assert dialog.previous_button.isEnabled()

    dialog.next_button.click()
    assert dialog.index == 2
    assert dialog.findChild(MediaView) is not None
    assert not dialog.next_button.isEnabled()


def test_exam_review_fits_1366_by_768_without_horizontal_overflow(qtbot):
    dialog = ExamReviewDialog("历史试卷回看", [_item(0, True), _item(1, False)])
    qtbot.addWidget(dialog)

    fit_review_to_available(dialog, QRect(0, 0, 1366, 728))
    dialog.show()
    QApplication.processEvents()

    assert dialog.x() >= 0
    assert dialog.y() >= 0
    assert dialog.x() + dialog.width() <= 1366
    assert dialog.y() + dialog.height() <= 728
    assert dialog.detail_scroll.horizontalScrollBarPolicy() == Qt.ScrollBarAlwaysOff
    assert dialog.detail_scroll.horizontalScrollBar().maximum() == 0
    assert dialog.previous_button.isVisible()
    assert dialog.next_button.isVisible()
    assert dialog.close_button.isVisible()


def test_exam_review_long_explanation_uses_outer_page_scroll(qtbot):
    dialog = ExamReviewDialog("试卷回看", [_item(0, False)])
    qtbot.addWidget(dialog)
    dialog.show()
    QApplication.processEvents()

    explanation = dialog.answer_panel.explanation
    qtbot.waitUntil(
        lambda: explanation.verticalScrollBar().maximum() == 0
        and dialog.detail_scroll.verticalScrollBar().maximum() > 0,
        timeout=1000,
    )

    assert explanation.verticalScrollBarPolicy() == Qt.ScrollBarAlwaysOff
    assert explanation.verticalScrollBar().maximum() == 0
    assert explanation.viewport().height() >= explanation.document().size().height() - 2
    assert dialog.detail_scroll.verticalScrollBar().maximum() > 0


def test_media_view_scales_wide_images_to_available_width_without_cropping(qtbot):
    buffer = BytesIO()
    Image.new("RGB", (1200, 600), "white").save(buffer, format="PNG")
    view = MediaView([QuestionAsset("image/png", buffer.getvalue(), 0, "尺寸链图")])
    view.setFixedWidth(500)
    view.resize(500, 400)
    qtbot.addWidget(view)
    view.show()
    QApplication.processEvents()

    image_label = next(
        label for label in view.findChildren(QLabel) if label.pixmap() is not None
    )
    pixmap = image_label.pixmap()

    assert pixmap.width() <= view.contentsRect().width()
    assert abs((pixmap.width() / pixmap.height()) - 2.0) < 0.02
    assert image_label.height() >= pixmap.height()
