from __future__ import annotations

from PySide2.QtCore import Signal
from PySide2.QtWidgets import QGridLayout, QPushButton, QWidget

from ..domain import QuestionType


class QuestionTypeSelector(QWidget):
    """Compact multi-select control that always keeps one question type active."""

    selection_changed = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(8)
        self.buttons: dict[QuestionType, QPushButton] = {}
        for index, question_type in enumerate(QuestionType):
            button = QPushButton(question_type.value)
            button.setCheckable(True)
            button.setChecked(True)
            button.setProperty("role", "typeFilter")
            button.clicked.connect(
                lambda _checked=False, item=question_type: self._selection_updated(item)
            )
            self.buttons[question_type] = button
            layout.addWidget(button, index // 3, index % 3)

    def selected_values(self) -> list[str]:
        return [
            question_type.value
            for question_type in QuestionType
            if self.buttons[question_type].isChecked()
        ]

    def _selection_updated(self, changed_type: QuestionType) -> None:
        if not self.selected_values():
            self.buttons[changed_type].setChecked(True)
        self.selection_changed.emit(self.selected_values())
