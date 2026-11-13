from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication, QScrollArea

from offline_quiz.app import apply_application_style
from offline_quiz.database import Database
from offline_quiz.domain import QuestionType, QuizMode
from offline_quiz.quiz_service import QuizService
from offline_quiz.ui import QuizDialog


def main() -> int:
    output = ROOT / "dist" / "ui_qa" / "test7"
    output.mkdir(parents=True, exist_ok=True)
    temp_root = ROOT / ".qa_ui"
    temp_root.mkdir(exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix="test7-quiz-", dir=temp_root))
    source_database = ROOT / ".handoff" / "KuishuQuiz-2026-11-12" / "offline-quiz-current.db"
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
    dialog.resize(1180, 680)
    dialog.show()
    app.processEvents()
    dialog.current_widget.option_buttons["false"].click()
    app.processEvents()
    dialog.grab().save(str(output / "quiz-reviewed-1180x680.png"))

    scroll = dialog.question_navigator.findChild(QScrollArea)
    print("QUESTIONS", len(session.questions))
    print("HORIZONTAL_SCROLL_MAX", scroll.horizontalScrollBar().maximum())
    print("ANSWER_PANEL_VISIBLE", not dialog.answer_panel.isHidden())
    dialog.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
