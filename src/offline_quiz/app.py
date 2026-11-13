from __future__ import annotations

import logging
import os
from pathlib import Path
import sys

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from . import __version__
from .backup import BackupService
from .branding import LEGACY_DATA_DIRECTORY, PRODUCT_NAME
from .database import Database
from .ui import APP_STYLE, MainWindow


def data_directory() -> Path:
    root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    return root / LEGACY_DATA_DIRECTORY / "data"


def configure_logging(data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=data_dir / "offline-quiz.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        encoding="utf-8",
    )


def apply_application_style(application: QApplication) -> None:
    application.setStyleSheet(APP_STYLE)


def prepare_database(data_dir: Path) -> tuple[Database | None, str | None]:
    database_path = data_dir / "offline-quiz.db"
    backup_service = BackupService(database_path, data_dir / "backups")
    safety_backup: Path | None = None
    if database_path.exists():
        try:
            safety_backup = backup_service.create_backup()
        except Exception:
            logging.exception("自动备份失败，继续尝试打开现有数据库")
    try:
        return Database(database_path), None
    except Exception as exc:
        if safety_backup is not None:
            try:
                backup_service.restore_backup(safety_backup)
            except Exception:
                logging.exception("数据库升级失败后无法自动恢复安全备份")
        logging.exception("数据库无法打开，进入恢复模式")
        return None, str(exc)


class RecoveryDialog(QDialog):
    def __init__(self, data_dir: Path, error: str, parent=None):
        super().__init__(parent)
        self.data_dir = data_dir
        self.database_path = data_dir / "offline-quiz.db"
        self.setWindowTitle("数据恢复")
        self.resize(520, 220)
        layout = QVBoxLayout(self)
        message = QLabel(
            "当前题库数据无法打开。你可以选择以前的备份进行恢复，恢复完成后重新启动应用。"
        )
        message.setWordWrap(True)
        layout.addWidget(message)
        details = QLabel(f"错误信息：{error}")
        details.setWordWrap(True)
        layout.addWidget(details)
        restore = QPushButton("选择备份并恢复")
        restore.clicked.connect(self.restore)
        layout.addWidget(restore)
        close = QPushButton("退出")
        close.clicked.connect(self.reject)
        layout.addWidget(close)

    def restore(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择题库备份",
            str(self.data_dir / "backups"),
            "数据库备份 (*.db)",
        )
        if not path:
            return
        try:
            BackupService(self.database_path, self.data_dir / "backups").restore_backup(path)
            QMessageBox.information(self, "恢复完成", "数据已恢复，请重新启动应用。")
            self.accept()
        except Exception as exc:
            QMessageBox.warning(self, "恢复失败", str(exc))


def main() -> int:
    application = QApplication(sys.argv)
    apply_application_style(application)
    application.setApplicationName(PRODUCT_NAME)
    application.setApplicationVersion(__version__)
    data_dir = data_directory()
    configure_logging(data_dir)
    try:
        database, error = prepare_database(data_dir)
        if database is None:
            recovery = RecoveryDialog(data_dir, error or "未知错误")
            recovery.show()
            return application.exec()
        window = MainWindow(database, data_dir)
        window.show()
        return application.exec()
    except Exception as exc:
        logging.exception("应用启动失败")
        QMessageBox.critical(None, "启动失败", f"无法启动应用：{exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
