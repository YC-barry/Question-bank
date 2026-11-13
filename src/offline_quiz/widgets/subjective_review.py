from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QLabel,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..domain import QuizSession
from .media_view import MediaView


class SubjectiveReviewDialog(QDialog):
    def __init__(self, session: QuizSession, parent=None):
        super().__init__(parent)
        self.session = session
        self.score_spins: dict[int, QSpinBox] = {}
        self.setWindowTitle("人工复核主观题")
        self.resize(760, 640)
        root = QVBoxLayout(self)
        note = QLabel("自动结果仅供参考。请核对作答、标准答案和解题过程，并确认最终得分。")
        note.setWordWrap(True)
        root.addWidget(note)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        for index, grade in sorted(session.results.items()):
            if not grade.requires_confirmation:
                continue
            question = session.questions[index]
            group = QGroupBox(
                f"第 {index + 1} 题 · {question.question_type.value} · 满分 {question.points} 分"
            )
            layout = QVBoxLayout(group)
            for title, text in (
                ("题目", question.stem),
                ("我的答案", session.answers.get(index)),
                ("标准答案", question.answer),
                ("解题过程", question.solution or "原文未提供"),
            ):
                label = QLabel(f"{title}：{text or '未作答'}")
                label.setWordWrap(True)
                label.setTextInteractionFlags(label.textInteractionFlags())
                layout.addWidget(label)
            if question.assets:
                layout.addWidget(MediaView(question.assets))
            suggestion = grade.suggestion
            suggestion_text = suggestion.status if suggestion else "待人工确认"
            reasons = "；".join(suggestion.reasons) if suggestion else "信息不足"
            suggestion_label = QLabel(
                f"自动建议：{suggestion_text}，建议 {grade.earned_points} 分。{reasons}"
            )
            suggestion_label.setWordWrap(True)
            layout.addWidget(suggestion_label)
            score = QSpinBox()
            score.setRange(0, question.points)
            score.setValue(grade.earned_points)
            score.setSuffix(" 分")
            layout.addWidget(QLabel("人工确认得分："))
            layout.addWidget(score)
            if question.id is not None:
                self.score_spins[question.id] = score
            content_layout.addWidget(group)
        content_layout.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def adjustments(self) -> dict[int, int]:
        return {question_id: spin.value() for question_id, spin in self.score_spins.items()}
