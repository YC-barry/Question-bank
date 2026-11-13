from __future__ import annotations

import os
from pathlib import Path
import shutil
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette
from PySide6.QtWidgets import QApplication

from offline_quiz.app import apply_application_style
from offline_quiz.database import Database
from offline_quiz.ui import MainWindow


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    output = root / "dist" / "ui_qa" / "test4"
    output.mkdir(parents=True, exist_ok=True)
    temp_root = root / ".qa_ui"
    temp_root.mkdir(exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix="test4-dark-", dir=temp_root))
    source_database = root / ".handoff" / "KuishuQuiz-2026-11-12" / "offline-quiz-current.db"
    database_path = workspace / "offline-quiz.db"
    shutil.copy2(source_database, database_path)

    app = QApplication.instance() or QApplication([])
    font_path = Path(r"C:\Windows\Fonts\msyh.ttc")
    if font_path.exists():
        QFontDatabase.addApplicationFont(str(font_path))
        app.setFont(QFont("Microsoft YaHei UI", 10))
    palette = app.palette()
    for role in (
        QPalette.ColorRole.WindowText,
        QPalette.ColorRole.Text,
        QPalette.ColorRole.ButtonText,
    ):
        palette.setColor(role, QColor("white"))
    app.setPalette(palette)
    apply_application_style(app)

    window = MainWindow(Database(database_path), workspace)
    window.resize(1366, 728)
    window.navigate("bank")
    window.show()
    app.processEvents()
    window.grab().save(str(output / "dark-mode-bank-1366x728.png"))
    window.close()


if __name__ == "__main__":
    main()
