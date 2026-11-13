from __future__ import annotations

from io import BytesIO

from PIL import Image
from PySide6.QtWidgets import QLabel, QTextEdit

from offline_quiz.domain import (
    GradeResult,
    Question,
    QuestionAsset,
    QuestionType,
    QuizMode,
    QuizSession,
    SubjectiveSuggestion,
)
from offline_quiz.ui import QuestionWidget
from offline_quiz.ui import ReviewDialog
from offline_quiz.media import asset_to_snapshot
from offline_quiz.widgets.media_view import MediaView
from offline_quiz.widgets.subjective_review import SubjectiveReviewDialog


def _subjective_question(question_id=7, points=20):
    return Question(
        id=question_id,
        bank_name="机械题库",
        question_type=QuestionType.SHORT_ANSWER,
        stem="液压泵有什么作用？",
        answer="把机械能转换为液压能。",
        solution="把机械能转换为液压能并提供压力油。",
        points=points,
        requires_manual_review=True,
    )


def test_short_answer_widget_uses_multiline_editor(qtbot):
    widget = QuestionWidget(_subjective_question())
    qtbot.addWidget(widget)

    editor = widget.findChild(QTextEdit)
    editor.setPlainText("我的多行答案\n第二行")

    assert widget.answer() == "我的多行答案\n第二行"
    widget.set_locked(True)
    assert editor.isReadOnly() is True


def test_media_view_renders_supported_image_data(qtbot):
    buffer = BytesIO()
    Image.new("RGBA", (2, 2), (255, 255, 255, 0)).save(buffer, format="PNG")
    png = buffer.getvalue()
    view = MediaView([QuestionAsset("image/png", png, 0, "示意图")])
    qtbot.addWidget(view)

    labels = view.findChildren(QLabel)

    assert any(label.pixmap() is not None and not label.pixmap().isNull() for label in labels)


def test_subjective_review_starts_from_suggestion_and_returns_final_points(qtbot):
    question = _subjective_question()
    suggestion = SubjectiveSuggestion("建议部分正确", 12, 0.6, ["覆盖部分内容"])
    grade = GradeResult(
        False,
        12,
        20,
        question.answer,
        "转换能量",
        requires_confirmation=True,
        suggestion=suggestion,
    )
    session = QuizSession(1, QuizMode.EXAM, [question], {}, {0: grade}, {0: "转换能量"})
    dialog = SubjectiveReviewDialog(session)
    qtbot.addWidget(dialog)

    assert dialog.score_spins[question.id].value() == 12
    dialog.score_spins[question.id].setValue(18)

    assert dialog.adjustments() == {question.id: 18}
    assert dialog.score_spins[question.id].maximum() == 20


def test_subjective_review_shows_standard_answer_and_solution(qtbot):
    question = _subjective_question()
    buffer = BytesIO()
    Image.new("RGB", (4, 3), "white").save(buffer, format="PNG")
    question.assets = [QuestionAsset("image/png", buffer.getvalue(), 0, "计算图")]
    suggestion = SubjectiveSuggestion("建议正确", 20, 0.9, ["核心一致"])
    grade = GradeResult(
        True, 20, 20, question.answer, "作答", requires_confirmation=True, suggestion=suggestion
    )
    session = QuizSession(1, QuizMode.SEQUENTIAL, [question], {}, {0: grade}, {0: "作答"})
    dialog = SubjectiveReviewDialog(session)
    qtbot.addWidget(dialog)

    all_text = "\n".join(label.text() for label in dialog.findChildren(QLabel))

    assert question.answer in all_text
    assert question.solution in all_text
    media = dialog.findChild(MediaView)
    assert media is not None and media.isVisibleTo(dialog)
    assert any(
        label.pixmap() is not None and not label.pixmap().isNull()
        for label in media.findChildren(QLabel)
    )


def test_history_review_renders_snapshot_media_and_solution(qtbot):
    buffer = BytesIO()
    Image.new("RGB", (4, 3), "white").save(buffer, format="PNG")
    asset = QuestionAsset("image/png", buffer.getvalue(), 0, "历史公式")
    dialog = ReviewDialog(
        "历史回看",
        [
            {
                "snapshot": {
                    "stem": "根据图示计算",
                    "answer": "10mm",
                    "options": {},
                    "points": 10,
                    "explanation": "说明",
                    "solution": "计算过程",
                    "assets": [asset_to_snapshot(asset)],
                },
                "user_answer": "9mm",
                "is_correct": 0,
                "earned_points": 5,
            }
        ],
    )
    qtbot.addWidget(dialog)
    dialog.show()

    media = dialog.findChild(MediaView)
    all_text = "\n".join(label.text() for label in dialog.findChildren(QLabel))

    assert media is not None and media.isVisibleTo(dialog)
    assert "计算过程" in all_text
    assert any(
        label.pixmap() is not None and not label.pixmap().isNull()
        for label in media.findChildren(QLabel)
    )
