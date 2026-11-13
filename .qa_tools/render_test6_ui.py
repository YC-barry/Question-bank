from __future__ import annotations

import os
from pathlib import Path
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

from offline_quiz.app import apply_application_style
from offline_quiz.database import Database
from offline_quiz.domain import Question, QuestionType, QuizMode
from offline_quiz.ui import MainWindow


def answer_for(question_type: QuestionType):
    return {
        QuestionType.SINGLE_CHOICE: "A",
        QuestionType.MULTIPLE_CHOICE: ["A", "B"],
        QuestionType.TRUE_FALSE: True,
        QuestionType.FILL_BLANK: [["标准答案"]],
        QuestionType.SHORT_ANSWER: "示例答案",
        QuestionType.CALCULATION: "42",
    }[question_type]


def main() -> int:
    output = ROOT / "dist" / "ui_qa" / "test6"
    output.mkdir(parents=True, exist_ok=True)
    database_path = ROOT / ".build_temp_test6_ui" / "overview.db"
    database_path.parent.mkdir(parents=True, exist_ok=True)
    if database_path.exists():
        database_path.unlink()
    database = Database(database_path)
    practiced_counts = {
        QuestionType.SINGLE_CHOICE: 4,
        QuestionType.MULTIPLE_CHOICE: 2,
        QuestionType.TRUE_FALSE: 5,
        QuestionType.FILL_BLANK: 3,
        QuestionType.SHORT_ANSWER: 1,
        QuestionType.CALCULATION: 2,
    }
    for bank_index in range(3):
        bank_id = database.ensure_bank(f"示例题库 {bank_index + 1}")
        for question_type in QuestionType:
            for index in range(6):
                question_id = database.upsert_question(
                    bank_id,
                    Question(
                        bank_name=f"示例题库 {bank_index + 1}",
                        question_type=question_type,
                        stem=f"{question_type.value}示例题 {bank_index + 1}-{index + 1}",
                        answer=answer_for(question_type),
                        options={"A": "选项一", "B": "选项二"}
                        if question_type in {QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE}
                        else {},
                        source_order=index,
                    ),
                )
                if bank_index == 0 and index < practiced_counts[question_type]:
                    question = database.get_question(question_id)
                    session_id = database.create_session(QuizMode.SEQUENTIAL.value, {})
                    database.save_session_item(
                        session_id,
                        question,
                        answer_for(question_type),
                        index % 3 != 0,
                        1 if index % 3 != 0 else 0,
                    )

    app = QApplication.instance() or QApplication([])
    font_path = Path(r"C:\Windows\Fonts\msyh.ttc")
    if font_path.exists():
        QFontDatabase.addApplicationFont(str(font_path))
        app.setFont(QFont("Microsoft YaHei UI", 10))
    apply_application_style(app)
    window = MainWindow(database, database_path.parent)
    window.resize(1180, 680)
    window.show()
    app.processEvents()
    window.grab().save(str(output / "dashboard-top-1180x680.png"))
    window.home_page.scroll_area.verticalScrollBar().setValue(
        window.home_page.scroll_area.verticalScrollBar().maximum()
    )
    app.processEvents()
    window.grab().save(str(output / "dashboard-bottom-1180x680.png"))
    window.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
