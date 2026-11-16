from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PySide2.QtCore import Qt, Signal
from PySide2.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from ..database import Database
from ..explanation_packages import DuplicateExplanationPackage
from ..import_service import ImportService


class ExplanationManagerDialog(QDialog):
    packages_changed = Signal()

    def __init__(self, database: Database, parent=None):
        super().__init__(parent)
        self.database = database
        self.import_service = ImportService(database)
        self.setWindowTitle("解析资料")
        self.resize(1080, 560)
        root = QVBoxLayout(self)
        description = QLabel(
            "解析资料与题库分开保存，可先导入；只对机修钳工同级别、同题型、同题干且答案一致的题目生效。"
        )
        description.setWordWrap(True)
        root.addWidget(description)

        controls = QHBoxLayout()
        self.import_button = QPushButton("导入解析 Word")
        self.import_button.setObjectName("primary")
        self.delete_button = QPushButton("删除选中资料包")
        self.close_button = QPushButton("关闭")
        self.import_button.clicked.connect(self.choose_files)
        self.delete_button.clicked.connect(self.delete_selected)
        self.close_button.clicked.connect(self.accept)
        controls.addWidget(self.import_button)
        controls.addWidget(self.delete_button)
        controls.addStretch()
        controls.addWidget(self.close_button)
        root.addLayout(controls)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["名称", "文件名", "级别", "总条目", "已匹配", "待匹配", "答案冲突", "导入时间"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        root.addWidget(self.table, 1)
        self.refresh()

    def refresh(self) -> None:
        packages = self.database.list_explanation_packages()
        self.table.setRowCount(len(packages))
        for row, package in enumerate(packages):
            values = [
                package["name"],
                package["filename"],
                package["level"],
                package["total_count"],
                package["matched_count"],
                package["pending_count"],
                package["conflict_count"],
                package["imported_at"].replace("T", " "),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setData(Qt.UserRole, int(package["id"]))
                self.table.setItem(row, column, item)
        self.delete_button.setEnabled(bool(packages))

    def choose_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "导入解析资料",
            "",
            "Word 解析资料 (*.docx)",
        )
        if paths:
            self.import_paths(paths)

    def import_paths(self, paths: Iterable[str]) -> dict[str, int]:
        summary = {"imported": 0, "replaced": 0, "failed": 0, "cancelled": 0}
        changed = False
        for raw_path in paths:
            path = Path(raw_path)
            try:
                package = self.import_service.preview_explanation(path)
                self.database.import_explanation_package(package)
                summary["imported"] += 1
                changed = True
            except DuplicateExplanationPackage as duplicate:
                choice = QMessageBox.question(
                    self,
                    "发现相同内容",
                    f"发现相同内容：{path.name} 与已导入的 {duplicate.filename} 完全一致。\n"
                    "是否替换已有解析资料？选择“取消”将不导入此文件。",
                    QMessageBox.Yes | QMessageBox.Cancel,
                    QMessageBox.Cancel,
                )
                if choice != QMessageBox.Yes:
                    summary["cancelled"] += 1
                    continue
                try:
                    self.database.import_explanation_package(
                        package, replace_package_id=duplicate.package_id
                    )
                    summary["replaced"] += 1
                    changed = True
                except Exception as exc:
                    summary["failed"] += 1
                    QMessageBox.warning(
                        self, "替换失败", f"{path.name} 未替换任何解析资料。\n{exc}"
                    )
            except Exception as exc:
                summary["failed"] += 1
                QMessageBox.warning(
                    self, "解析资料导入失败", f"{path.name} 未写入任何数据。\n{exc}"
                )
        self.refresh()
        if changed:
            self.packages_changed.emit()
        QMessageBox.information(
            self,
            "解析资料导入完成",
            f"新增 {summary['imported']} 个，替换 {summary['replaced']} 个，"
            f"取消 {summary['cancelled']} 个，失败 {summary['failed']} 个。",
        )
        return summary

    def delete_selected(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "提示", "请先选择一个解析资料包。")
            return
        package_id = int(self.table.item(row, 0).data(Qt.UserRole))
        filename = self.table.item(row, 1).text()
        if QMessageBox.question(
            self,
            "确认删除解析资料",
            f"确定删除 {filename} 吗？\n\n"
            "此操作只删除解析，不删除题目、错题、答案、成绩和历史记录。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        ) != QMessageBox.Yes:
            return
        self.database.delete_explanation_package(package_id)
        self.refresh()
        self.packages_changed.emit()
