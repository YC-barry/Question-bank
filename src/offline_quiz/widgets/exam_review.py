from __future__ import annotations

from typing import Any

from PySide6.QtCore import QRect, Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from ..domain import GradeResult, Question, QuestionType
from .answer_review import AnswerReviewPanel
from .question_navigator import QuestionNavigator


def fit_review_to_available(widget: QWidget, available: QRect | None = None) -> None:
    if available is None:
        screen = QApplication.primaryScreen()
        available = screen.availableGeometry() if screen else QRect(0, 0, 1366, 728)
    width = min(1180, max(760, available.width() - 80))
    height = min(680, max(560, available.height() - 48))
    widget.resize(width, height)
    widget.move(
        available.x() + max(0, (available.width() - width) // 2),
        available.y() + max(0, (available.height() - height) // 2),
    )


def _question_from_snapshot(snapshot: dict[str, Any]) -> Question:
    try:
        question_type = QuestionType(snapshot.get("question_type"))
    except (TypeError, ValueError):
        question_type = QuestionType.SINGLE_CHOICE
    return Question(
        id=snapshot.get("id"),
        bank_id=snapshot.get("bank_id"),
        bank_name=str(snapshot.get("bank_name") or "历史题目"),
        question_type=question_type,
        stem=str(snapshot.get("stem") or ""),
        options=dict(snapshot.get("options") or {}),
        answer=snapshot.get("answer"),
        aliases=list(snapshot.get("aliases") or []),
        explanation=str(snapshot.get("explanation") or ""),
        solution=str(snapshot.get("solution") or ""),
        requires_manual_review=bool(snapshot.get("requires_manual_review", False)),
        assets=list(snapshot.get("assets") or []),
        category=str(snapshot.get("category") or ""),
        difficulty=str(snapshot.get("difficulty") or ""),
        tags=list(snapshot.get("tags") or []),
        points=int(snapshot.get("points") or 0),
        source_order=int(snapshot.get("source_order") or 0),
    )


class ExamReviewDialog(QDialog):
    def __init__(self, title: str, items: list[dict[str, Any]], parent=None):
        super().__init__(parent)
        self.items = items
        self.index = 0
        self.setWindowTitle(title)
        self.setMinimumSize(760, 560)
        fit_review_to_available(self)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 14)
        root.setSpacing(12)

        heading = QLabel(title)
        heading.setObjectName("title")
        root.addWidget(heading)

        body = QHBoxLayout()
        body.setSpacing(12)
        self.detail_scroll = QScrollArea()
        self.detail_scroll.setObjectName("examReviewScroll")
        self.detail_scroll.setWidgetResizable(True)
        self.detail_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.detail_scroll.setFrameShape(QFrame.NoFrame)
        detail = QWidget()
        detail.setObjectName("contentCard")
        self.detail_layout = QVBoxLayout(detail)
        self.detail_layout.setContentsMargins(20, 18, 20, 20)
        self.detail_layout.setSpacing(10)
        self.position_label = QLabel()
        self.position_label.setObjectName("sectionTitle")
        self.detail_layout.addWidget(self.position_label)
        self.detail_layout.addWidget(QLabel("题干"))
        self.stem_view = QTextBrowser()
        self.stem_view.setObjectName("reviewStem")
        self.stem_view.setMinimumHeight(100)
        self.stem_view.setMaximumHeight(260)
        self.detail_layout.addWidget(self.stem_view)
        self.options_title = QLabel("选项")
        self.detail_layout.addWidget(self.options_title)
        self.options_view = QTextBrowser()
        self.options_view.setObjectName("reviewOptions")
        self.options_view.setMinimumHeight(70)
        self.options_view.setMaximumHeight(180)
        self.detail_layout.addWidget(self.options_view)
        self.answer_panel = AnswerReviewPanel()
        self.detail_layout.addWidget(self.answer_panel)
        self.detail_layout.addStretch()
        self.detail_scroll.setWidget(detail)
        body.addWidget(self.detail_scroll, 1)

        self.question_navigator = QuestionNavigator(len(items))
        self.question_navigator.jump_requested.connect(self.show_item)
        body.addWidget(self.question_navigator)
        root.addLayout(body, 1)

        controls = QHBoxLayout()
        self.previous_button = QPushButton("上一题")
        self.next_button = QPushButton("下一题")
        self.close_button = QPushButton("关闭")
        self.previous_button.clicked.connect(self.previous)
        self.next_button.clicked.connect(self.next)
        self.close_button.clicked.connect(self.accept)
        controls.addWidget(self.previous_button)
        controls.addWidget(self.next_button)
        controls.addStretch()
        controls.addWidget(self.close_button)
        root.addLayout(controls)

        if items:
            self.show_item(0)
        else:
            self.position_label.setText("没有可回看的题目")
            self.stem_view.hide()
            self.options_title.hide()
            self.options_view.hide()
            self.answer_panel.clear_result()
            self.previous_button.setEnabled(False)
            self.next_button.setEnabled(False)

    def show_item(self, index: int) -> None:
        if index < 0 or index >= len(self.items):
            return
        self.index = index
        item = self.items[index]
        snapshot = dict(item.get("snapshot") or {})
        question = _question_from_snapshot(snapshot)
        self.position_label.setText(
            f"第 {index + 1} / {len(self.items)} 题　{question.question_type.value}"
        )
        self.stem_view.setPlainText(question.stem)
        options = "\n".join(
            f"{key}. {value}" for key, value in question.options.items()
        )
        self.options_title.setVisible(bool(options))
        self.options_view.setVisible(bool(options))
        self.options_view.setPlainText(options)
        grade = GradeResult(
            is_correct=bool(item.get("is_correct")),
            earned_points=int(item.get("earned_points") or 0),
            total_points=question.points,
            correct_answer=question.answer,
            user_answer=item.get("user_answer"),
            explanation=question.explanation,
        )
        self.answer_panel.show_result(question, grade, item.get("user_answer"))
        self.previous_button.setEnabled(index > 0)
        self.next_button.setEnabled(index < len(self.items) - 1)
        correct = {
            item_index
            for item_index, row in enumerate(self.items)
            if bool(row.get("is_correct"))
        }
        wrong = set(range(len(self.items))) - correct
        self.question_navigator.set_state(
            current=index,
            answered=set(range(len(self.items))),
            correct=correct,
            wrong=wrong,
            enabled=set(range(len(self.items))),
        )
        self.detail_scroll.verticalScrollBar().setValue(0)

    def previous(self) -> None:
        self.show_item(self.index - 1)

    def next(self) -> None:
        self.show_item(self.index + 1)
