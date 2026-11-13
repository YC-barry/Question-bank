from __future__ import annotations

import os
from pathlib import Path
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

from offline_quiz.app import apply_application_style
from offline_quiz.database import Database
from offline_quiz.domain import Question, QuestionType, QuizMode
from offline_quiz.quiz_service import QuizService
from offline_quiz.ui import MainWindow, QuizDialog


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    output = root / "dist" / "ui_qa" / "test3"
    output.mkdir(parents=True, exist_ok=True)
    temp_root = root / ".qa_ui"
    temp_root.mkdir(exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix="test3-", dir=temp_root))
    database = Database(workspace / "quiz.db")
    bank_id = database.ensure_bank("机修钳工示例题库")
    for index, (stem, answer, explanation) in enumerate(
        [
            (
                "一组互相垂直的投射线与投影面垂直时，这种投影称为什么？",
                True,
                "这种投影称为正投影。正投影能够准确表达物体各部分的形状和尺寸，是机械制图中最常用的投影方法。",
            ),
            (
                "安装滚动轴承后，应检查轴承转动是否灵活。",
                True,
                "安装结束后应转动检查，不应出现卡滞、异常阻力或异常声响。",
            ),
        ]
    ):
        database.upsert_question(
            bank_id,
            Question(
                bank_name="机修钳工示例题库",
                question_type=QuestionType.TRUE_FALSE,
                stem=stem,
                answer=answer,
                explanation=explanation,
                category="机械基础",
                difficulty="中等",
                source_order=index,
            ),
        )

    app = QApplication.instance() or QApplication([])
    font_path = Path(r"C:\Windows\Fonts\msyh.ttc")
    if font_path.exists():
        QFontDatabase.addApplicationFont(str(font_path))
        app.setFont(QFont("Microsoft YaHei UI", 10))
    apply_application_style(app)
    main_window = MainWindow(database, workspace)
    main_window.resize(1366, 768)
    main_window.show()
    app.processEvents()
    main_window.grab().save(str(output / "home-1366x768.png"))
    main_window.close()

    session = QuizService(database).create_session({}, None, QuizMode.SEQUENTIAL)
    quiz = QuizDialog(database, session)
    quiz.resize(1180, 740)
    quiz.show()
    app.processEvents()
    quiz.grab().save(str(output / "quiz-question.png"))
    quiz.current_widget.option_buttons["false"].click()
    quiz.submit_one()
    app.processEvents()
    print("reviewed_splitter_sizes", quiz.content_splitter.sizes())
    quiz.grab().save(str(output / "quiz-reviewed.png"))
    quiz.close()


if __name__ == "__main__":
    main()
