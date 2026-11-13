from __future__ import annotations

import os
from pathlib import Path
import shutil
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication, QScrollArea

from offline_quiz.app import apply_application_style
from offline_quiz.database import Database
from offline_quiz.domain import QuestionType, QuizMode
from offline_quiz.quiz_service import QuizService
from offline_quiz.ui import QuizDialog


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    output = root / "dist" / "ui_qa" / "test5"
    output.mkdir(parents=True, exist_ok=True)
    temp_root = root / ".qa_ui"
    temp_root.mkdir(exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix="test5-quiz-", dir=temp_root))
    source_database = root / ".handoff" / "KuishuQuiz-2026-11-12" / "offline-quiz-current.db"
    database_path = workspace / "offline-quiz.db"
    shutil.copy2(source_database, database_path)

    app = QApplication.instance() or QApplication([])
    font_path = Path(r"C:\Windows\Fonts\msyh.ttc")
    if font_path.exists():
        QFontDatabase.addApplicationFont(str(font_path))
        app.setFont(QFont("Microsoft YaHei UI", 10))
    apply_application_style(app)

    database = Database(database_path)
    session = QuizService(database).create_session(
        {"question_types": [QuestionType.TRUE_FALSE.value]},
        None,
        QuizMode.SEQUENTIAL,
    )
    dialog = QuizDialog(database, session)
    dialog.resize(1180, 720)
    dialog.show()
    app.processEvents()
    dialog.grab().save(str(output / "judgment-before-click.png"))
    dialog.current_widget.option_buttons["false"].click()
    app.processEvents()
    dialog.grab().save(str(output / "judgment-auto-reviewed.png"))

    scroll = dialog.question_navigator.findChild(QScrollArea)
    print("QUESTIONS", len(session.questions))
    print("NAVIGATOR_WIDTH", dialog.question_navigator.width())
    print("HORIZONTAL_SCROLL_MAX", scroll.horizontalScrollBar().maximum())
    print("RESULTS_AFTER_CLICK", len(session.results))
    print("ANSWER_PANEL_VISIBLE", not dialog.answer_panel.isHidden())
    dialog.close()


if __name__ == "__main__":
    main()
