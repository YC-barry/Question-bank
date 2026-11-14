from __future__ import annotations

from math import ceil
from typing import Any

from PySide6.QtCore import QSize, QTimer, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from ..domain import GradeResult, Question
from ..assets import load_svg_icon
from ..theme import ThemeTokens
from .media_view import MediaView


def _format_answer(answer: Any, question: Question) -> str:
    if isinstance(answer, bool):
        return "对" if answer else "错"
    if isinstance(answer, list):
        if answer and isinstance(answer[0], list):
            return "；".join(" / ".join(map(str, group)) for group in answer)
        return "、".join(
            f"{item}. {question.options[item]}" if item in question.options else str(item)
            for item in answer
        )
    if isinstance(answer, str) and answer in question.options:
        return f"{answer}. {question.options[answer]}"
    return "未作答" if answer in (None, "") else str(answer)


class ExpandingTextBrowser(QTextBrowser):
    """Read-only rich text that grows vertically instead of clipping content."""

    content_height_changed = Signal()

    def __init__(self, minimum_height: int, parent: QWidget | None = None):
        super().__init__(parent)
        self._minimum_content_height = minimum_height
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._height_timer = QTimer(self)
        self._height_timer.setSingleShot(True)
        self._height_timer.timeout.connect(self.update_content_height)
        self.document().documentLayout().documentSizeChanged.connect(
            self._schedule_height_update
        )
        self.setMinimumHeight(minimum_height)

    def _schedule_height_update(self, *_args) -> None:
        self._height_timer.start(0)

    def update_content_height(self) -> None:
        document_height = ceil(self.document().size().height())
        frame = self.frameWidth() * 2
        margins = self.contentsMargins()
        height = document_height + frame + margins.top() + margins.bottom() + 2
        target_height = max(self._minimum_content_height, height)
        if target_height != self.height():
            self.setFixedHeight(target_height)
            self.content_height_changed.emit()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._schedule_height_update()


class AnswerReviewPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("answerReviewPanel")
        self.setMinimumHeight(240)
        self._fit_timer = QTimer(self)
        self._fit_timer.setSingleShot(True)
        self._fit_timer.timeout.connect(self._fit_to_contents)
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(10)

        header = QHBoxLayout()
        status_icon_host = QFrame()
        status_icon_host.setObjectName("reviewStatusIcon")
        status_icon_host.setFixedSize(30, 30)
        status_icon_layout = QVBoxLayout(status_icon_host)
        status_icon_layout.setContentsMargins(4, 4, 4, 4)
        self.status_icon = QLabel()
        self.status_icon.setAlignment(Qt.AlignCenter)
        status_icon_layout.addWidget(self.status_icon)
        self.status_label = QLabel()
        self.status_label.setObjectName("reviewStatus")
        self.score_label = QLabel()
        self.score_label.setObjectName("reviewScore")
        header.addWidget(status_icon_host)
        header.addWidget(self.status_label)
        header.addStretch()
        header.addWidget(self.score_label)
        root.addLayout(header)

        answers = QHBoxLayout()
        answers.setSpacing(14)
        user_column = QVBoxLayout()
        user_title = QLabel("我的答案")
        user_title.setObjectName("reviewCaption")
        self.user_answer = ExpandingTextBrowser(54)
        self.user_answer.setObjectName("userAnswer")
        self.user_answer.content_height_changed.connect(self._schedule_fit)
        user_column.addWidget(user_title)
        user_column.addWidget(self.user_answer)
        correct_column = QVBoxLayout()
        correct_title = QLabel("正确答案")
        correct_title.setObjectName("reviewCaption")
        self.correct_answer = ExpandingTextBrowser(54)
        self.correct_answer.setObjectName("correctAnswer")
        self.correct_answer.content_height_changed.connect(self._schedule_fit)
        answer_font = QFont(self.correct_answer.font())
        answer_font.setPointSize(15)
        answer_font.setBold(True)
        self.correct_answer.setFont(answer_font)
        correct_column.addWidget(correct_title)
        correct_column.addWidget(self.correct_answer)
        answers.addLayout(user_column, 2)
        answers.addLayout(correct_column, 3)
        root.addLayout(answers)

        explanation_title = QLabel("答案解析 / 解题过程")
        explanation_title.setObjectName("reviewCaption")
        self.explanation = ExpandingTextBrowser(90)
        self.explanation.setObjectName("reviewExplanation")
        self.explanation.content_height_changed.connect(self._schedule_fit)
        root.addWidget(explanation_title)
        root.addWidget(self.explanation, 1)
        self.media_host = QWidget()
        self.media_layout = QVBoxLayout(self.media_host)
        self.media_layout.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self.media_host)
        self.hide()

    def _fit_to_contents(self) -> None:
        self.setMinimumHeight(240)
        if self.layout() is not None:
            self.layout().activate()
        self.setMinimumHeight(max(240, self.sizeHint().height()))
        self.updateGeometry()

    def _schedule_fit(self) -> None:
        self._fit_timer.start(0)

    def clear_result(self) -> None:
        self.status_label.clear()
        self.score_label.clear()
        self.user_answer.clear()
        self.correct_answer.clear()
        self.explanation.clear()
        while self.media_layout.count():
            item = self.media_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.setMinimumHeight(240)
        self.hide()

    def show_result(self, question: Question, grade: GradeResult, user_answer: Any) -> None:
        pending = grade.requires_confirmation
        if pending:
            status = "等待人工复核"
            state = "pending"
        elif grade.is_correct:
            status = "回答正确"
            state = "correct"
        else:
            status = "回答错误或部分正确"
            state = "wrong"
        self.setProperty("resultState", state)
        icon_name, icon_color = {
            "correct": ("circle-check-big", ThemeTokens.SUCCESS),
            "wrong": ("circle-x", ThemeTokens.ERROR),
            "pending": ("clock-3", ThemeTokens.WARNING),
        }[state]
        self.status_icon.setPixmap(load_svg_icon(icon_name, icon_color, 22).pixmap(QSize(22, 22)))
        self.status_label.setText(status)
        self.score_label.setText(f"得分 {grade.earned_points} / {grade.total_points}")
        self.user_answer.setPlainText(_format_answer(user_answer, question))
        self.correct_answer.setPlainText(_format_answer(grade.correct_answer, question))
        explanation_parts = []
        if grade.explanation:
            explanation_parts.append(grade.explanation)
        if question.solution and question.solution not in explanation_parts:
            explanation_parts.append(question.solution)
        self.explanation.setPlainText("\n\n".join(explanation_parts) or "原题暂未提供解析。")
        self.user_answer.update_content_height()
        self.correct_answer.update_content_height()
        self.explanation.update_content_height()
        while self.media_layout.count():
            item = self.media_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if question.assets:
            self.media_layout.addWidget(MediaView(question.assets))
        self.style().unpolish(self)
        self.style().polish(self)
        self.show()
        self._fit_to_contents()
        self._fit_timer.start(0)
