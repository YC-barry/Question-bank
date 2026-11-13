from __future__ import annotations

import math

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class QuestionNavigator(QFrame):
    jump_requested = Signal(int)

    def __init__(self, count: int, parent=None):
        super().__init__(parent)
        self.setObjectName("questionNavigator")
        self.setFixedWidth(260)
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        title = QLabel("题目导航")
        title.setObjectName("sectionTitle")
        root.addWidget(title)
        hint = QLabel("蓝色为当前题，绿色正确，红色错误")
        hint.setObjectName("statCaption")
        hint.setWordWrap(True)
        root.addWidget(hint)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content = QWidget()
        content.setMinimumWidth(198)
        grid = QGridLayout(content)
        grid.setContentsMargins(0, 8, 0, 8)
        grid.setSpacing(7)
        columns = 5
        self.buttons: list[QPushButton] = []
        for index in range(max(0, int(count))):
            button = QPushButton(str(index + 1))
            button.setProperty("role", "question")
            button.setFixedSize(34, 34)
            button.clicked.connect(
                lambda _checked=False, question_index=index: self.jump_requested.emit(
                    question_index
                )
            )
            grid.addWidget(button, index // columns, index % columns)
            self.buttons.append(button)
        if self.buttons:
            grid.setRowStretch(math.ceil(len(self.buttons) / columns), 1)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

    def set_state(
        self,
        *,
        current: int,
        answered: set[int],
        correct: set[int],
        wrong: set[int],
        enabled: set[int],
    ) -> None:
        for index, button in enumerate(self.buttons):
            if index == current:
                state = "current"
            elif index in correct:
                state = "correct"
            elif index in wrong:
                state = "wrong"
            elif index in answered:
                state = "answered"
            else:
                state = "pending"
            button.setProperty("questionState", state)
            button.setEnabled(index in enabled)
            button.style().unpolish(button)
            button.style().polish(button)
