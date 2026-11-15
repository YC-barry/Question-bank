from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from PySide6.QtCore import QRect, QSize, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QRadioButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .backup import BackupService
from .assets import HERO_ARTWORK, SvgIllustration, load_svg_icon
from .branding import PRODUCT_NAME
from .database import Database
from .domain import DuplicatePolicy, Question, QuestionType, QuizMode
from .import_service import ImportService
from .importers import _build_question
from .quiz_service import HistoryService, QuizService
from .templates import TemplateService
from .theme import ThemeTokens, apply_soft_shadow, build_app_style
from .widgets.media_view import MediaView
from .widgets.answer_review import AnswerReviewPanel
from .widgets.explanation_manager import ExplanationManagerDialog
from .widgets.exam_review import ExamReviewDialog
from .widgets.learning_charts import ProgressRing, TrendChart
from .widgets.question_navigator import QuestionNavigator
from .widgets.question_type_selector import QuestionTypeSelector
from .widgets.stat_card import StatCard
from .widgets.subjective_review import SubjectiveReviewDialog


LEGACY_APP_STYLE = """
QWidget { color: #162033; }
QLineEdit, QComboBox, QSpinBox, QTextEdit, QTextBrowser { color: #162033; }
QComboBox QAbstractItemView { color: #162033; background: white; }
QTableWidget { color: #162033; }
QMainWindow, QDialog { background: #eef4fa; color: #162033; font-family: "Microsoft YaHei UI"; font-size: 14px; }
QWidget#appContent { background: #eef4fa; }
QFrame#navigationRail { background: #244f7d; border: none; }
QLabel#brandTitle { color: white; font-size: 20px; font-weight: 700; }
QLabel#brandCaption, QLabel#offlineCaption { color: #c8d9ea; font-size: 12px; }
QPushButton[role="nav"] { color: #dceafa; text-align: left; padding: 12px 16px; border: none; border-radius: 10px; background: transparent; font-size: 14px; }
QPushButton[role="nav"]:hover { background: #326391; color: white; }
QPushButton[role="nav"]:checked { background: white; color: #244f7d; font-weight: 700; }
QFrame#heroCard { background: #dcebf7; border: 1px solid #cbddeb; border-radius: 20px; }
QFrame#heroIllustration { background: rgba(255, 255, 255, 150); border: 1px solid #c5daf0; border-radius: 18px; }
QLabel#heroMark { color: #2f76c8; font-size: 38px; font-weight: 800; }
QLabel#heroTitle { color: #173b61; font-size: 28px; font-weight: 700; }
QLabel#heroText { color: #50677d; font-size: 14px; }
QFrame#statCard, QFrame#contentCard { background: white; border: 1px solid #dce6ef; border-radius: 16px; }
QFrame#overviewPanel { background: #f9fbfe; border: 1px solid #e2ebf4; border-radius: 14px; }
QScrollArea#dashboardScroll { border: none; background: transparent; }
QWidget#dashboardCanvas { background: #eef4fa; }
QPushButton[role="dashboardAction"] { min-height: 48px; text-align: left; padding-left: 16px; background: #f8fbff; }
QPushButton[role="dashboardAction"]:hover { background: #edf6ff; }
QLabel[role="activityRow"] { background: #f8fbff; border: 1px solid #e4edf6; border-radius: 9px; padding: 10px 12px; color: #36536d; }
QLabel#statTitle { color: #64778b; font-size: 13px; }
QLabel#statValue { color: #173b61; font-size: 30px; font-weight: 700; }
QLabel#statCaption { color: #8a9bad; font-size: 12px; }
QGroupBox { background: white; border: 1px solid #dce6ef; border-radius: 14px; margin-top: 14px; padding: 16px; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 6px; color: #294c6d; }
QPushButton { padding: 9px 16px; border: 1px solid #c9d8e6; border-radius: 8px; background: white; color: #28445f; }
QPushButton:hover { border-color: #3c83c6; color: #1e67a7; background: #f5faff; }
QPushButton#primary { background: #3b82c4; color: white; border-color: #3b82c4; font-weight: 600; }
QPushButton#primary:hover { background: #2f70aa; }
QPushButton[role="typeFilter"] { min-width: 86px; padding: 8px 14px; }
QPushButton[role="typeFilter"]:checked { background: #e5f1ff; border: 2px solid #438bd1; color: #155a96; font-weight: 700; }
QLineEdit, QComboBox, QSpinBox, QTextEdit { padding: 8px; border: 1px solid #cbd9e6; border-radius: 8px; background: white; selection-background-color: #8dbbe0; }
QRadioButton, QCheckBox { padding: 11px 14px; spacing: 10px; border: 1px solid #d8e3ec; border-radius: 9px; background: #fbfdff; color: #253d55; }
QRadioButton:hover, QCheckBox:hover { border-color: #78a9cf; background: #f3f9fe; }
QRadioButton:checked, QCheckBox:checked { border: 2px solid #4b91cb; background: #eaf4fc; color: #174f79; font-weight: 600; }
QRadioButton::indicator, QCheckBox::indicator { width: 18px; height: 18px; }
QTableWidget { border: 1px solid #dce6ef; border-radius: 10px; gridline-color: #e7eef5; background: white; alternate-background-color: #f7fafc; }
QHeaderView::section { background: #e7f0f8; color: #35546f; padding: 9px; border: none; border-right: 1px solid #d5e2ed; font-weight: 600; }
QLabel#title { font-size: 24px; font-weight: 700; color: #173b61; }
QLabel#sectionTitle { font-size: 18px; font-weight: 700; color: #294c6d; }
QFrame#answerReviewPanel { background: white; border: 1px solid #c9d9e6; border-radius: 14px; }
QFrame#answerReviewPanel[resultState="correct"] { border: 2px solid #55a87a; background: #f5fcf8; }
QFrame#answerReviewPanel[resultState="wrong"] { border: 2px solid #db7d7d; background: #fff8f8; }
QFrame#answerReviewPanel[resultState="pending"] { border: 2px solid #d5a94e; background: #fffaf0; }
QLabel#reviewStatus { font-size: 18px; font-weight: 700; color: #193b5b; }
QLabel#reviewScore { font-size: 16px; font-weight: 700; color: #315b7e; }
QLabel#reviewCaption { color: #64778b; font-size: 12px; font-weight: 600; }
QTextBrowser#userAnswer, QTextBrowser#correctAnswer, QTextBrowser#reviewExplanation { background: white; border: 1px solid #dbe6ef; border-radius: 8px; padding: 7px; }
QTextBrowser#correctAnswer { color: #17633c; }
QFrame#questionNavigator { background: white; border: 1px solid #dce6ef; border-radius: 14px; }
QPushButton[role="question"] { min-width: 34px; max-width: 34px; min-height: 34px; max-height: 34px; padding: 0; border-radius: 17px; background: #edf3f8; border: 1px solid #d5e1eb; color: #53697d; }
QPushButton[role="question"][questionState="current"] { background: #3b82c4; border-color: #3b82c4; color: white; font-weight: 700; }
QPushButton[role="question"][questionState="correct"] { background: #dff4e7; border-color: #7fc499; color: #17633c; }
QPushButton[role="question"][questionState="wrong"] { background: #fde7e7; border-color: #e29a9a; color: #9d3434; }
QPushButton[role="question"][questionState="answered"] { background: #dcecf8; border-color: #8db8d8; color: #245c86; }
QProgressBar { border: none; border-radius: 5px; background: #dbe7f0; height: 10px; text-align: center; color: transparent; }
QProgressBar::chunk { background: #4b91cb; border-radius: 5px; }
QScrollBar:vertical { width: 10px; background: transparent; }
QScrollBar::handle:vertical { background: #b5c9da; border-radius: 5px; min-height: 28px; }
"""

APP_STYLE = build_app_style()


def fit_window_to_available(
    window: QWidget,
    preferred_width: int,
    preferred_height: int,
    available_geometry: QRect | None = None,
) -> None:
    available = available_geometry
    if available is None:
        screen = QApplication.primaryScreen()
        available = screen.availableGeometry() if screen is not None else QRect(0, 0, preferred_width, preferred_height)
    margin = 48
    width = min(preferred_width, max(640, available.width() - margin))
    height = min(preferred_height, max(480, available.height() - margin))
    window.resize(width, height)
    x = available.x() + max(0, (available.width() - window.width()) // 2)
    y = available.y() + max(0, (available.height() - window.height()) // 2)
    window.move(x, y)


def display_answer(answer: Any) -> str:
    if isinstance(answer, bool):
        return "对" if answer else "错"
    if isinstance(answer, list):
        if answer and isinstance(answer[0], list):
            return "；".join(" / ".join(map(str, group)) for group in answer)
        return ", ".join(map(str, answer))
    return "" if answer is None else str(answer)


def display_answer_with_options(snapshot: dict[str, Any], answer: Any) -> str:
    options = snapshot.get("options") or {}
    if isinstance(answer, str) and answer in options:
        return f"{answer}. {options[answer]}"
    if isinstance(answer, list) and (not answer or not isinstance(answer[0], list)):
        return ", ".join(
            f"{item}. {options[item]}" if item in options else str(item)
            for item in answer
        )
    return display_answer(answer)


def has_meaningful_answer(answer: Any) -> bool:
    if answer is None:
        return False
    if isinstance(answer, str):
        return bool(answer.strip())
    if isinstance(answer, (list, tuple, set)):
        return any(has_meaningful_answer(item) for item in answer)
    return True


class QuestionWidget(QWidget):
    def __init__(self, question: Question, parent: QWidget | None = None):
        super().__init__(parent)
        self.question = question
        self.option_buttons: dict[str, QRadioButton | QCheckBox] = {}
        self.blank_inputs: list[QLineEdit] = []
        self.subjective_input: QTextEdit | None = None
        self._group: QButtonGroup | None = None
        layout = QVBoxLayout(self)
        stem = QLabel(question.stem)
        stem.setWordWrap(True)
        stem.setStyleSheet("font-size: 18px; font-weight: 600; margin: 8px 0 14px;")
        layout.addWidget(stem)
        layout.addWidget(MediaView(question.assets))
        if question.question_type is QuestionType.SINGLE_CHOICE and question.options:
            self._group = QButtonGroup(self)
            for key, text in question.options.items():
                button = QRadioButton(f"{key}. {text}")
                self._group.addButton(button)
                self.option_buttons[key] = button
                layout.addWidget(button)
        elif question.question_type is QuestionType.MULTIPLE_CHOICE and question.options:
            for key, text in question.options.items():
                button = QCheckBox(f"{key}. {text}")
                self.option_buttons[key] = button
                layout.addWidget(button)
        elif question.question_type is QuestionType.TRUE_FALSE:
            self._group = QButtonGroup(self)
            for key, text in (("true", "对"), ("false", "错")):
                button = QRadioButton(text)
                self._group.addButton(button)
                self.option_buttons[key] = button
                layout.addWidget(button)
        elif question.question_type is QuestionType.FILL_BLANK:
            for index, _ in enumerate(question.answer, start=1):
                row = QHBoxLayout()
                row.addWidget(QLabel(f"第 {index} 空："))
                editor = QLineEdit()
                self.blank_inputs.append(editor)
                row.addWidget(editor)
                layout.addLayout(row)
        else:
            self.subjective_input = QTextEdit()
            self.subjective_input.setPlaceholderText("请在此输入答案，可输入多行计算过程或说明")
            self.subjective_input.setMinimumHeight(150)
            layout.addWidget(self.subjective_input)
        layout.addStretch()

    def answer(self) -> Any:
        kind = self.question.question_type
        if kind is QuestionType.SINGLE_CHOICE:
            return next((key for key, button in self.option_buttons.items() if button.isChecked()), None)
        if kind is QuestionType.MULTIPLE_CHOICE:
            return [key for key, button in self.option_buttons.items() if button.isChecked()]
        if kind is QuestionType.TRUE_FALSE:
            if self.option_buttons["true"].isChecked():
                return True
            if self.option_buttons["false"].isChecked():
                return False
            return None
        if self.subjective_input is not None:
            return self.subjective_input.toPlainText()
        return [editor.text() for editor in self.blank_inputs]

    def set_answer(self, answer: Any) -> None:
        if answer is None:
            return
        if self.question.question_type is QuestionType.SINGLE_CHOICE:
            if str(answer) in self.option_buttons:
                self.option_buttons[str(answer)].setChecked(True)
        elif self.question.question_type is QuestionType.MULTIPLE_CHOICE:
            for key in answer:
                if key in self.option_buttons:
                    self.option_buttons[key].setChecked(True)
        elif self.question.question_type is QuestionType.TRUE_FALSE:
            self.option_buttons["true" if answer else "false"].setChecked(True)
        elif self.subjective_input is not None:
            self.subjective_input.setPlainText(str(answer))
        else:
            for editor, value in zip(self.blank_inputs, answer, strict=False):
                editor.setText(str(value))

    def set_locked(self, locked: bool = True) -> None:
        for button in self.option_buttons.values():
            button.setEnabled(not locked)
        for editor in self.blank_inputs:
            editor.setReadOnly(locked)
        if self.subjective_input is not None:
            self.subjective_input.setReadOnly(locked)


class QuestionEditorDialog(QDialog):
    def __init__(self, bank_name: str, question: Question | None = None, parent=None):
        super().__init__(parent)
        self.bank_name = bank_name
        self.question = question
        self.setWindowTitle("编辑题目" if question else "新增题目")
        self.resize(620, 650)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.type_combo = QComboBox()
        self.type_combo.addItems([item.value for item in QuestionType])
        self.stem_edit = QTextEdit()
        self.stem_edit.setMaximumHeight(100)
        self.category_edit = QLineEdit()
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["简单", "中等", "困难"])
        self.tags_edit = QLineEdit()
        self.points_spin = QSpinBox()
        self.points_spin.setRange(1, 100)
        self.answer_edit = QLineEdit()
        self.answer_edit.setPlaceholderText("多选用逗号；多空用 ||；同义答案用 |")
        form.addRow("题型", self.type_combo)
        form.addRow("题干", self.stem_edit)
        form.addRow("分类", self.category_edit)
        form.addRow("难度", self.difficulty_combo)
        form.addRow("标签", self.tags_edit)
        form.addRow("分值权重", self.points_spin)
        self.option_edits: dict[str, QLineEdit] = {}
        for key in "ABCDEFGH":
            editor = QLineEdit()
            self.option_edits[key] = editor
            form.addRow(f"选项 {key}", editor)
        form.addRow("正确答案", self.answer_edit)
        self.explanation_edit = QTextEdit()
        self.explanation_edit.setMaximumHeight(100)
        form.addRow("解析", self.explanation_edit)
        self.solution_edit = QTextEdit()
        self.solution_edit.setMaximumHeight(110)
        self.solution_edit.setPlaceholderText("简答题参考要点或计算题完整过程")
        form.addRow("参考过程", self.solution_edit)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        if question:
            self._load(question)

    def _load(self, question: Question) -> None:
        self.type_combo.setCurrentText(question.question_type.value)
        self.stem_edit.setPlainText(question.stem)
        self.category_edit.setText(question.category)
        self.difficulty_combo.setCurrentText(question.difficulty)
        self.tags_edit.setText(",".join(question.tags))
        self.points_spin.setValue(question.points)
        for key, text in question.options.items():
            self.option_edits[key].setText(text)
        self.answer_edit.setText(display_answer(question.answer).replace("；", "||").replace(" / ", "|"))
        self.explanation_edit.setPlainText(question.explanation)
        self.solution_edit.setPlainText(question.solution)

    def value(self) -> Question:
        data: dict[str, Any] = {
            "题型": self.type_combo.currentText(),
            "题干": self.stem_edit.toPlainText(),
            "分类": self.category_edit.text(),
            "难度": self.difficulty_combo.currentText(),
            "标签": self.tags_edit.text(),
            "分值": self.points_spin.value(),
            "正确答案": self.answer_edit.text(),
            "解析": self.explanation_edit.toPlainText(),
        }
        for key, editor in self.option_edits.items():
            data[f"选项{key}"] = editor.text()
        parsed = _build_question(data, self.bank_name, self.question.source_order if self.question else 0)
        parsed.id = self.question.id if self.question else None
        parsed.bank_id = self.question.bank_id if self.question else None
        parsed.solution = self.solution_edit.toPlainText().strip() or parsed.solution
        if parsed.question_type in {QuestionType.SHORT_ANSWER, QuestionType.CALCULATION}:
            parsed.requires_manual_review = True
        if self.question:
            parsed.assets = list(self.question.assets)
        return parsed

    def _validate(self) -> None:
        try:
            self.value()
        except ValueError as exc:
            QMessageBox.warning(self, "题目有误", str(exc))
            return
        self.accept()


class BankPage(QWidget):
    data_changed = Signal()

    def __init__(self, database: Database, parent=None):
        super().__init__(parent)
        self.database = database
        self.import_service = ImportService(database)
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        title = QLabel("题库管理")
        title.setObjectName("title")
        self.import_button = QPushButton("导入 Word / PPT / Excel")
        self.import_button.setObjectName("primary")
        self.import_button.clicked.connect(self.import_files)
        self.explanation_button = QPushButton("解析资料")
        self.explanation_button.clicked.connect(self.manage_explanations)
        top.addWidget(title)
        top.addStretch()
        top.addWidget(self.explanation_button)
        top.addWidget(self.import_button)
        layout.addLayout(top)
        controls = QHBoxLayout()
        self.bank_combo = QComboBox()
        self.bank_combo.currentIndexChanged.connect(self.refresh_questions)
        self.add_button = QPushButton("新增题目")
        self.edit_button = QPushButton("编辑题目")
        self.delete_button = QPushButton("删除题目")
        self.delete_bank_button = QPushButton("删除题库")
        self.add_button.clicked.connect(self.add_question)
        self.edit_button.clicked.connect(self.edit_question)
        self.delete_button.clicked.connect(self.delete_question)
        self.delete_bank_button.clicked.connect(self.delete_bank)
        controls.addWidget(QLabel("题库："))
        controls.addWidget(self.bank_combo, 1)
        controls.addWidget(self.add_button)
        controls.addWidget(self.edit_button)
        controls.addWidget(self.delete_button)
        controls.addWidget(self.delete_bank_button)
        layout.addLayout(controls)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["序号", "题型", "题干", "分类", "难度", "分值权重"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        layout.addWidget(self.table)
        self.refresh()

    def manage_explanations(self) -> None:
        dialog = ExplanationManagerDialog(self.database, self)
        dialog.packages_changed.connect(self.data_changed.emit)
        dialog.exec()
        self.refresh_questions()

    def refresh(self) -> None:
        selected = self.bank_combo.currentData()
        self.bank_combo.blockSignals(True)
        self.bank_combo.clear()
        for bank in self.database.get_banks():
            self.bank_combo.addItem(f"{bank['name']}（{bank['question_count']}题）", bank["id"])
        if selected is not None:
            index = self.bank_combo.findData(selected)
            if index >= 0:
                self.bank_combo.setCurrentIndex(index)
        self.bank_combo.blockSignals(False)
        self.refresh_questions()

    def refresh_questions(self) -> None:
        bank_id = self.bank_combo.currentData()
        questions = self.database.list_questions(bank_ids=[bank_id], ordered=True) if bank_id else []
        self.table.setRowCount(len(questions))
        for row, question in enumerate(questions):
            values = [question.source_order or row + 1, question.question_type.value, question.stem, question.category, question.difficulty, question.points]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setData(Qt.UserRole, question.id)
                self.table.setItem(row, column, item)

    def import_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "导入题库",
            "",
            "题库文件 (*.doc *.docx *.xlsx *.pptx)",
        )
        if not paths:
            return
        totals = [0, 0, 0]
        for path in paths:
            try:
                result = self.import_service.preview(path)
            except Exception as exc:
                QMessageBox.warning(self, "读取失败", f"{Path(path).name}：{exc}")
                continue
            if result.has_errors:
                details = "\n".join(f"{issue.location}：{issue.message}" for issue in result.issues[:12])
                QMessageBox.warning(self, "导入校验失败", details)
                continue
            counts = Counter(question.question_type.value for question in result.questions)
            count_text = "，".join(
                f"{kind} {counts.get(kind, 0)}"
                for kind in ["填空", "判断", "单选", "多选", "简答", "计算"]
                if counts.get(kind, 0)
            )
            warning_count = sum(issue.severity == "警告" for issue in result.issues)
            asset_count = sum(len(question.assets) for question in result.questions)
            choice = QMessageBox.question(
                self,
                "重复题处理",
                f"{Path(path).name} 共识别 {len(result.questions)} 道题。\n"
                f"题型：{count_text or '未分类'}\n题目附件：{asset_count} 个；提示：{warning_count} 条。\n\n"
                "发现重复题时是否覆盖？\n选择“否”将跳过重复题。",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            )
            if choice == QMessageBox.Cancel:
                continue
            policy = DuplicatePolicy.OVERWRITE if choice == QMessageBox.Yes else DuplicatePolicy.SKIP
            try:
                summary = self.import_service.commit(result, policy)
            except Exception as exc:
                QMessageBox.warning(
                    self,
                    "导入失败",
                    f"{Path(path).name} 未写入任何题目。\n{exc}",
                )
                continue
            totals[0] += summary.inserted
            totals[1] += summary.overwritten
            totals[2] += summary.skipped
        self.refresh()
        self.data_changed.emit()
        QMessageBox.information(self, "导入完成", f"新增 {totals[0]} 道，覆盖 {totals[1]} 道，跳过 {totals[2]} 道。")

    def _selected_question(self) -> Question | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        return self.database.get_question(
            int(self.table.item(row, 0).data(Qt.UserRole)),
            include_package_explanation=False,
        )

    def add_question(self) -> None:
        bank_id = self.bank_combo.currentData()
        if not bank_id:
            QMessageBox.information(self, "提示", "请先导入一个题库。")
            return
        bank_name = next(bank["name"] for bank in self.database.get_banks() if bank["id"] == bank_id)
        dialog = QuestionEditorDialog(bank_name, parent=self)
        if dialog.exec() == QDialog.Accepted:
            question = dialog.value()
            question.source_order = len(self.database.list_questions(bank_ids=[bank_id])) + 1
            self.database.upsert_question(bank_id, question)
            self.refresh()
            self.data_changed.emit()

    def edit_question(self) -> None:
        question = self._selected_question()
        if not question:
            QMessageBox.information(self, "提示", "请先选择一道题。")
            return
        dialog = QuestionEditorDialog(question.bank_name, question, self)
        if dialog.exec() == QDialog.Accepted:
            self.database.update_question(question.id, dialog.value())
            self.refresh()
            self.data_changed.emit()

    def delete_question(self) -> None:
        question = self._selected_question()
        if question and QMessageBox.question(self, "确认删除", "确定删除选中的题目吗？") == QMessageBox.Yes:
            self.database.delete_question(question.id)
            self.refresh()
            self.data_changed.emit()

    def delete_bank(self) -> None:
        bank_id = self.bank_combo.currentData()
        if bank_id and QMessageBox.question(self, "确认删除", "确定删除整个题库吗？历史答题快照会保留。") == QMessageBox.Yes:
            self.database.delete_bank(bank_id)
            self.refresh()
            self.data_changed.emit()


ReviewDialog = ExamReviewDialog


class QuizDialog(QDialog):
    def __init__(self, database: Database, session, parent=None):
        super().__init__(parent)
        self.database = database
        self.service = QuizService(database)
        self.session = session
        self.index = 0
        self.answers: dict[int, Any] = {}
        self.current_widget: QuestionWidget | None = None
        self._auto_advance_expected: int | None = None
        self._auto_advance_timer = QTimer(self)
        self._auto_advance_timer.setSingleShot(True)
        self._auto_advance_timer.timeout.connect(self._run_scheduled_auto_advance)
        self.setWindowTitle(session.mode.value)
        self.setMinimumSize(960, 680)
        fit_window_to_available(self, 1180, 780)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(18, 16, 18, 14)
        self.layout.setSpacing(12)
        progress_row = QHBoxLayout()
        self.progress = QLabel()
        self.progress.setObjectName("sectionTitle")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, len(session.questions))
        self.progress_bar.setTextVisible(False)
        progress_row.addWidget(self.progress)
        progress_row.addWidget(self.progress_bar, 1)
        self.layout.addLayout(progress_row)
        self.content_splitter = QSplitter(Qt.Vertical)
        question_container = QFrame()
        question_container.setObjectName("contentCard")
        self.question_host = QVBoxLayout(question_container)
        self.question_host.setContentsMargins(18, 14, 18, 14)
        self.answer_panel = AnswerReviewPanel()
        self.answer_scroll = QScrollArea()
        self.answer_scroll.setObjectName("answerReviewScroll")
        self.answer_scroll.setWidgetResizable(True)
        self.answer_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.answer_scroll.setFrameShape(QFrame.NoFrame)
        self.answer_scroll.setWidget(self.answer_panel)
        self.content_splitter.addWidget(question_container)
        self.content_splitter.addWidget(self.answer_scroll)
        self.content_splitter.setStretchFactor(0, 3)
        self.content_splitter.setStretchFactor(1, 2)
        self.content_splitter.setSizes([650, 0])
        self.question_navigator = QuestionNavigator(len(session.questions))
        self.question_navigator.jump_requested.connect(self.jump_to)
        body = QHBoxLayout()
        body.setSpacing(12)
        body.addWidget(self.content_splitter, 1)
        body.addWidget(self.question_navigator)
        self.layout.addLayout(body, 1)
        controls = QHBoxLayout()
        self.previous_button = QPushButton("上一题")
        self.next_button = QPushButton("下一题")
        self.submit_one_button = QPushButton("提交本题")
        self.submit_exam_button = QPushButton("提交试卷")
        self.submit_exam_button.setObjectName("primary")
        self.previous_button.clicked.connect(self.previous)
        self.next_button.clicked.connect(self.next)
        self.submit_one_button.clicked.connect(self.submit_one)
        self.submit_exam_button.clicked.connect(self.submit_exam)
        controls.addWidget(self.previous_button)
        controls.addWidget(self.next_button)
        controls.addStretch()
        controls.addWidget(self.submit_one_button)
        controls.addWidget(self.submit_exam_button)
        self.layout.addLayout(controls)
        is_exam = session.mode is QuizMode.EXAM
        self.submit_exam_button.setVisible(is_exam)
        self.submit_one_button.setVisible(not is_exam)
        self.show_question()

    def _clear_host(self) -> None:
        while self.question_host.count():
            item = self.question_host.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _save_current(self) -> None:
        if self.current_widget and self.session.mode is QuizMode.EXAM:
            question = self.session.questions[self.index]
            self.answers[question.id] = self.current_widget.answer()

    def show_question(self) -> None:
        self._clear_host()
        question = self.session.questions[self.index]
        self.progress.setText(f"第 {self.index + 1} / {len(self.session.questions)} 题　{question.question_type.value}　{question.points} 分")
        self.progress_bar.setValue(self.index + 1)
        self.current_widget = QuestionWidget(question)
        if (
            self.session.mode is QuizMode.SEQUENTIAL
            and self.index in self.session.answers
        ):
            self.current_widget.set_answer(self.session.answers[self.index])
        elif question.id in self.answers:
            self.current_widget.set_answer(self.answers[question.id])
        grade = self.session.results.get(self.index)
        if (
            self.session.mode is QuizMode.SEQUENTIAL
            and question.question_type is QuestionType.TRUE_FALSE
            and grade is None
        ):
            for button in self.current_widget.option_buttons.values():
                button.clicked.connect(self._submit_selected_judgment)
        self.question_host.addWidget(self.current_widget)
        answered = grade is not None and not grade.requires_confirmation
        self.current_widget.set_locked(grade is not None)
        self.previous_button.setEnabled(self.index > 0)
        self.next_button.setEnabled(self.index < len(self.session.questions) - 1 and (self.session.mode is QuizMode.EXAM or answered))
        self.submit_one_button.setEnabled(not answered)
        self.submit_one_button.setVisible(
            self.session.mode is QuizMode.SEQUENTIAL
            and question.question_type is not QuestionType.TRUE_FALSE
        )
        self.submit_one_button.setText("人工复核" if grade and grade.requires_confirmation else "提交本题")
        if grade is not None:
            self.answer_panel.show_result(
                question, grade, self.session.answers.get(self.index)
            )
            self.content_splitter.setSizes([390, 300])
        else:
            self.answer_panel.clear_result()
            self.content_splitter.setSizes([650, 0])
        self._update_question_navigator()

    def _submit_selected_judgment(self, _checked: bool = False) -> None:
        question = self.session.questions[self.index]
        if (
            self.session.mode is QuizMode.SEQUENTIAL
            and question.question_type is QuestionType.TRUE_FALSE
            and self.index not in self.session.results
        ):
            self.submit_one()

    def _update_question_navigator(self) -> None:
        correct = {
            index
            for index, grade in self.session.results.items()
            if grade.is_correct and not grade.requires_confirmation
        }
        wrong = {
            index
            for index, grade in self.session.results.items()
            if not grade.is_correct and not grade.requires_confirmation
        }
        if self.session.mode is QuizMode.EXAM:
            answered = {
                index
                for index, question in enumerate(self.session.questions)
                if question.id in self.answers
                and has_meaningful_answer(self.answers[question.id])
            }
            enabled = set(range(len(self.session.questions)))
        else:
            answered = set(self.session.results)
            next_unlocked = min(
                len(self.session.questions) - 1,
                max(answered, default=-1) + 1,
            )
            enabled = set(range(next_unlocked + 1))
        self.question_navigator.set_state(
            current=self.index,
            answered=answered,
            correct=correct,
            wrong=wrong,
            enabled=enabled,
        )

    def jump_to(self, index: int) -> None:
        if index < 0 or index >= len(self.session.questions):
            return
        if not self.question_navigator.buttons[index].isEnabled():
            return
        self._cancel_auto_advance()
        self._save_current()
        self.index = index
        self.show_question()

    def previous(self) -> None:
        self._cancel_auto_advance()
        self._save_current()
        if self.index > 0:
            self.index -= 1
            self.show_question()

    def next(self) -> None:
        self._cancel_auto_advance()
        self._save_current()
        if self.index < len(self.session.questions) - 1:
            self.index += 1
            self.show_question()

    def _cancel_auto_advance(self) -> None:
        self._auto_advance_timer.stop()
        self._auto_advance_expected = None

    def submit_one(self) -> None:
        pending = self.session.results.get(self.index)
        if pending is not None:
            if pending.requires_confirmation:
                self._review_pending()
            return
        answer = self.current_widget.answer()
        grade = self.service.answer_question(self.session, self.index, answer)
        if grade.requires_confirmation:
            self._review_pending()
        self.show_question()
        if (
            self.session.mode is QuizMode.SEQUENTIAL
            and grade.is_correct
            and not grade.requires_confirmation
            and self.index < len(self.session.questions) - 1
        ):
            self._auto_advance_expected = self.index
            self._auto_advance_timer.start(350)
        if len(self.session.results) == len(self.session.questions) and not any(
            item.requires_confirmation for item in self.session.results.values()
        ):
            QMessageBox.information(self, "刷题完成", "已完成全部题目，可逐题查看答案。")

    def _run_scheduled_auto_advance(self) -> None:
        expected_index = self._auto_advance_expected
        self._auto_advance_expected = None
        if expected_index is not None:
            self._auto_advance(expected_index)

    def _auto_advance(self, expected_index: int) -> None:
        if self.session.mode is not QuizMode.SEQUENTIAL or self.index != expected_index:
            return
        grade = self.session.results.get(expected_index)
        if (
            grade is None
            or not grade.is_correct
            or grade.requires_confirmation
            or expected_index >= len(self.session.questions) - 1
        ):
            return
        self.index += 1
        self.show_question()

    def submit_exam(self) -> None:
        if any(grade.requires_confirmation for grade in self.session.results.values()):
            self._review_pending(finish_exam=True)
            return
        self._save_current()
        unanswered = sum(
            1
            for question in self.session.questions
            if not has_meaningful_answer(self.answers.get(question.id))
        )
        warning = (
            f"还有 {unanswered} 题未作答。\n" if unanswered else ""
        )
        if QMessageBox.question(
            self,
            "提交试卷",
            warning + "提交后不能修改答案，确定提交吗？",
        ) != QMessageBox.Yes:
            return
        try:
            result = self.service.submit(self.session, self.answers)
        except Exception as exc:
            QMessageBox.warning(self, "提交失败", f"试卷尚未提交，请稍后重试。\n{exc}")
            return
        if result.requires_review:
            self._review_pending(finish_exam=True)
            return
        self._finish_exam(result)

    def _review_pending(self, finish_exam: bool = False) -> None:
        dialog = SubjectiveReviewDialog(self.session, self)
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            result = self.service.finalize_subjective(self.session, dialog.adjustments())
        except Exception as exc:
            QMessageBox.warning(self, "复核失败", str(exc))
            return
        self.show_question()
        if finish_exam:
            self._finish_exam(result)

    def _finish_exam(self, result) -> None:
        history = self.database.get_session(self.session.id)
        QMessageBox.information(self, "考试成绩", f"得分：{result.score} / {result.total}\n正确率：{result.accuracy:.1%}")
        ReviewDialog("试卷回看", history["items"], self).exec()
        self.accept()


class HomePage(QWidget):
    navigate_requested = Signal(str)

    def __init__(self, database: Database, parent=None):
        super().__init__(parent)
        self.database = database
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("dashboardScroll")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        dashboard = QWidget()
        dashboard.setObjectName("dashboardCanvas")
        root = QVBoxLayout(dashboard)
        root.setContentsMargins(24, 22, 24, 24)
        root.setSpacing(16)
        self.scroll_area.setWidget(dashboard)
        outer.addWidget(self.scroll_area)

        hero = QFrame()
        hero.setObjectName("heroCard")
        apply_soft_shadow(hero, "hero")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(28, 22, 24, 22)
        hero_layout.setSpacing(14)
        copy = QVBoxLayout()
        title = QLabel("今天从哪里开始？")
        title.setObjectName("heroTitle")
        subtitle = QLabel("离线练习、模拟考试和错题强化，所有题库与成绩只保存在本机。")
        subtitle.setObjectName("heroText")
        subtitle.setWordWrap(True)
        copy.addWidget(title)
        copy.addWidget(subtitle)
        hero_layout.addLayout(copy, 1)
        self.hero_artwork = SvgIllustration(HERO_ARTWORK)
        self.hero_artwork.setFixedSize(185, 96)
        hero_layout.addWidget(self.hero_artwork)
        self.quick_sequential_button = QPushButton("继续顺序刷题")
        self.quick_sequential_button.setObjectName("primary")
        self.quick_exam_button = QPushButton("生成 100 分试卷")
        self.quick_import_button = QPushButton("导入题库")
        self.quick_sequential_button.setIcon(load_svg_icon("circle-play", "#FFFFFF", 20))
        self.quick_exam_button.setIcon(load_svg_icon("file-text", ThemeTokens.PRIMARY, 20))
        self.quick_import_button.setIcon(load_svg_icon("upload", ThemeTokens.PRIMARY, 20))
        for button in (
            self.quick_sequential_button,
            self.quick_exam_button,
            self.quick_import_button,
        ):
            button.setIconSize(QSize(20, 20))
            hero_layout.addWidget(button)
        self.quick_sequential_button.clicked.connect(
            lambda: self.navigate_requested.emit("sequential")
        )
        self.quick_exam_button.clicked.connect(lambda: self.navigate_requested.emit("exam"))
        self.quick_import_button.clicked.connect(lambda: self.navigate_requested.emit("bank"))
        root.addWidget(hero)

        stats = QGridLayout()
        stats.setHorizontalSpacing(14)
        self.stat_cards = {
            "banks": StatCard("本地题库", caption="已导入并可使用的题库", icon_name="layers"),
            "questions": StatCard("题目总数", caption="各类题型合计", icon_name="notebook-tabs"),
            "wrong": StatCard("待强化错题", caption="尚未标记掌握", icon_name="badge-alert", accent=ThemeTokens.ERROR),
            "sessions": StatCard("完成练习", caption="已完成的练习与考试", icon_name="circle-check-big", accent=ThemeTokens.SUCCESS),
        }
        for column, card in enumerate(self.stat_cards.values()):
            apply_soft_shadow(card)
            stats.addWidget(card, 0, column)
        root.addLayout(stats)

        overview = QFrame()
        overview.setObjectName("contentCard")
        overview_layout = QVBoxLayout(overview)
        overview_layout.setContentsMargins(18, 16, 18, 18)
        overview_header = QHBoxLayout()
        overview_title = QLabel("学习概览")
        overview_title.setObjectName("sectionTitle")
        overview_caption = QLabel("按不同题目的覆盖情况统计，重复练习不会虚增总体进度")
        overview_caption.setObjectName("heroText")
        overview_header.addWidget(overview_title)
        overview_header.addSpacing(10)
        overview_header.addWidget(overview_caption)
        overview_header.addStretch()
        overview_layout.addLayout(overview_header)

        overview_columns = QHBoxLayout()
        overview_columns.setSpacing(12)
        overall_panel = QFrame()
        overall_panel.setObjectName("overviewPanel")
        overall_layout = QVBoxLayout(overall_panel)
        overall_layout.setContentsMargins(16, 14, 16, 14)
        overall_title = QLabel("总体进度")
        overall_title.setObjectName("sectionTitle")
        overall_layout.addWidget(overall_title)
        self.progress_ring = ProgressRing()
        overall_layout.addWidget(self.progress_ring, alignment=Qt.AlignCenter)
        self.overall_legend: dict[str, QLabel] = {}
        legend_grid = QGridLayout()
        legend_items = [
            ("practiced", "已练习"),
            ("correct", "最近答对"),
            ("wrong", "最近答错"),
            ("unpracticed", "未练习"),
        ]
        for index, (key, text) in enumerate(legend_items):
            caption = QLabel(text)
            caption.setObjectName("statCaption")
            value = QLabel("0 题")
            value.setStyleSheet(f"font-weight: 700; color: {ThemeTokens.PRIMARY};")
            self.overall_legend[key] = value
            legend_grid.addWidget(caption, index // 2, (index % 2) * 2)
            legend_grid.addWidget(value, index // 2, (index % 2) * 2 + 1)
        overall_layout.addLayout(legend_grid)
        overview_columns.addWidget(overall_panel, 1)

        trend_panel = QFrame()
        trend_panel.setObjectName("overviewPanel")
        trend_layout = QVBoxLayout(trend_panel)
        trend_layout.setContentsMargins(16, 14, 16, 14)
        trend_title_row = QHBoxLayout()
        trend_title = QLabel("近 7 天练习趋势")
        trend_title.setObjectName("sectionTitle")
        trend_hint = QLabel("每日提交题数")
        trend_hint.setObjectName("statCaption")
        trend_title_row.addWidget(trend_title)
        trend_title_row.addStretch()
        trend_title_row.addWidget(trend_hint)
        trend_layout.addLayout(trend_title_row)
        self.trend_chart = TrendChart()
        trend_layout.addWidget(self.trend_chart, 1)
        overview_columns.addWidget(trend_panel, 2)

        type_panel = QFrame()
        type_panel.setObjectName("overviewPanel")
        type_layout = QVBoxLayout(type_panel)
        type_layout.setContentsMargins(16, 14, 16, 14)
        type_title = QLabel("各类题完成情况")
        type_title.setObjectName("sectionTitle")
        type_layout.addWidget(type_title)
        self.type_progress_bars: dict[QuestionType, QProgressBar] = {}
        self.type_progress_labels: dict[QuestionType, QLabel] = {}
        for question_type in QuestionType:
            row = QHBoxLayout()
            name = QLabel(question_type.value)
            name.setMinimumWidth(42)
            count = QLabel("0 / 0")
            count.setObjectName("statCaption")
            row.addWidget(name)
            row.addStretch()
            row.addWidget(count)
            progress = QProgressBar()
            progress.setRange(0, 100)
            progress.setValue(0)
            progress.setTextVisible(False)
            self.type_progress_bars[question_type] = progress
            self.type_progress_labels[question_type] = count
            type_layout.addLayout(row)
            type_layout.addWidget(progress)
        overview_columns.addWidget(type_panel, 1)
        overview_layout.addLayout(overview_columns)
        root.addWidget(overview)

        lower = QHBoxLayout()
        lower.setSpacing(14)
        activity_card = QFrame()
        activity_card.setObjectName("contentCard")
        activity_layout = QVBoxLayout(activity_card)
        activity_layout.setContentsMargins(18, 16, 18, 18)
        activity_title = QLabel("最近活动")
        activity_title.setObjectName("sectionTitle")
        activity_layout.addWidget(activity_title)
        self.recent_activity_labels: list[QLabel] = []
        for _ in range(4):
            activity = QLabel()
            activity.setProperty("role", "activityRow")
            activity.setMinimumHeight(38)
            self.recent_activity_labels.append(activity)
            activity_layout.addWidget(activity)
        lower.addWidget(activity_card, 3)

        common_card = QFrame()
        common_card.setObjectName("contentCard")
        common_layout = QVBoxLayout(common_card)
        common_layout.setContentsMargins(18, 16, 18, 18)
        common_title = QLabel("常用功能")
        common_title.setObjectName("sectionTitle")
        common_layout.addWidget(common_title)
        actions = QGridLayout()
        actions.setSpacing(10)
        action_labels = {
            "bank": "题库管理\n导入、整理与维护题库",
            "exam": "生成 100 分试卷\n按题库自动组卷",
            "sequential": "顺序刷题\n按题目顺序练习",
            "wrong": "错题强化\n集中练习薄弱知识点",
            "history": "练习记录\n查看历史成绩与答案",
            "settings": "设置\n备份与数据管理",
        }
        action_icons = {
            "bank": "library",
            "exam": "file-text",
            "sequential": "circle-play",
            "wrong": "target",
            "history": "chart-no-axes-combined",
            "settings": "settings",
        }
        self.common_action_buttons: dict[str, QPushButton] = {}
        for index, (key, text) in enumerate(action_labels.items()):
            button = QPushButton(text)
            button.setProperty("role", "dashboardAction")
            button.setIcon(load_svg_icon(action_icons[key], ThemeTokens.PRIMARY, 23))
            button.setIconSize(QSize(23, 23))
            apply_soft_shadow(button)
            button.clicked.connect(
                lambda _checked=False, page_key=key: self.navigate_requested.emit(page_key)
            )
            self.common_action_buttons[key] = button
            actions.addWidget(button, index // 2, index % 2)
        common_layout.addLayout(actions)
        lower.addWidget(common_card, 2)
        root.addLayout(lower)
        root.addStretch()
        self.refresh()

    def refresh(self) -> None:
        banks = self.database.get_banks()
        overview = self.database.learning_overview()
        totals = overview["totals"]
        wrong = self.database.count_unmastered_wrong_questions()
        sessions = [item for item in self.database.list_sessions() if item.get("completed_at")]
        self.stat_cards["banks"].set_value(len(banks))
        self.stat_cards["questions"].set_value(totals["total"])
        self.stat_cards["wrong"].set_value(wrong)
        self.stat_cards["sessions"].set_value(len(sessions))
        self.progress_ring.set_progress(
            totals["progress_percent"], totals["practiced"], totals["total"]
        )
        for key, label in self.overall_legend.items():
            label.setText(f"{totals[key]} 题")
        self.trend_chart.set_data(overview["trend"])
        for item in overview["by_type"]:
            question_type = QuestionType(item["question_type"])
            self.type_progress_bars[question_type].setValue(item["progress_percent"])
            self.type_progress_labels[question_type].setText(
                f"{item['practiced']} / {item['total']}　{item['progress_percent']}%"
            )
        recent = overview["recent"]
        for index, label in enumerate(self.recent_activity_labels):
            if index >= len(recent):
                label.setVisible(index == 0)
                if index == 0:
                    label.setText("暂无练习记录，先开始一次顺序刷题吧。")
                continue
            activity = recent[index]
            timestamp = str(activity.get("last_answered_at") or "").replace("T", " ")
            score = ""
            if activity.get("completed_at") and activity.get("total") is not None:
                score = f"　成绩 {activity.get('score') or 0} / {activity.get('total') or 0}"
            label.setText(
                f"{activity.get('mode') or '练习'}　已答 {activity.get('answered_count') or 0} 题"
                f"{score}　{timestamp}"
            )
            label.setVisible(True)


class SessionSetupPage(QWidget):
    def __init__(self, database: Database, mode: QuizMode, parent=None):
        super().__init__(parent)
        self.database = database
        self.mode = mode
        layout = QVBoxLayout(self)
        title = QLabel("随机生成 100 分试卷" if mode is QuizMode.EXAM else "顺序刷题")
        title.setObjectName("title")
        layout.addWidget(title)
        group = QGroupBox("筛选条件")
        form = QFormLayout(group)
        self.bank_combo = QComboBox()
        self.category_edit = QLineEdit()
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["全部", "简单", "中等", "困难"])
        self.question_type_selector = QuestionTypeSelector()
        self.tag_edit = QLineEdit()
        self.tag_edit.setPlaceholderText("例如：液压、安全；留空表示全部")
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 100)
        self.count_spin.setValue(20)
        form.addRow("题库", self.bank_combo)
        form.addRow("分类（可选）", self.category_edit)
        form.addRow("难度", self.difficulty_combo)
        form.addRow("题型（可多选）", self.question_type_selector)
        form.addRow("标签（可选）", self.tag_edit)
        if mode is QuizMode.EXAM:
            form.addRow("抽题数量", self.count_spin)
        layout.addWidget(group)
        description = "程序随机抽题，并按原题分值权重归一化为总分 100 分。交卷后给出成绩，可回看每一道题。" if mode is QuizMode.EXAM else "按题目导入顺序从头到尾刷题。每提交一道题，立即显示对错、正确答案和解析。"
        note = QLabel(description)
        note.setWordWrap(True)
        layout.addWidget(note)
        self.start_button = QPushButton("开始考试" if mode is QuizMode.EXAM else "开始刷题")
        self.start_button.setObjectName("primary")
        self.start_button.clicked.connect(self.start)
        layout.addWidget(self.start_button, alignment=Qt.AlignLeft)
        layout.addStretch()
        self.refresh()

    def refresh(self) -> None:
        selected = self.bank_combo.currentData()
        self.bank_combo.clear()
        self.bank_combo.addItem("全部题库", None)
        for bank in self.database.get_banks():
            self.bank_combo.addItem(f"{bank['name']}（{bank['question_count']}题）", bank["id"])
        index = self.bank_combo.findData(selected)
        if index >= 0:
            self.bank_combo.setCurrentIndex(index)

    def start(self) -> None:
        filters = self.filters()
        count = self.count_spin.value() if self.mode is QuizMode.EXAM else None
        try:
            session = QuizService(self.database).create_session(filters, count, self.mode)
        except ValueError as exc:
            QMessageBox.warning(self, "无法开始", str(exc))
            return
        QuizDialog(self.database, session, self).exec()

    def filters(self) -> dict[str, Any]:
        bank_id = self.bank_combo.currentData()
        return {
            "bank_ids": [bank_id] if bank_id else [],
            "category": self.category_edit.text().strip(),
            "difficulty": "" if self.difficulty_combo.currentText() == "全部" else self.difficulty_combo.currentText(),
            "question_types": self.question_type_selector.selected_values(),
            "tag": self.tag_edit.text().strip(),
        }


class WrongPage(QWidget):
    def __init__(self, database: Database, parent=None):
        super().__init__(parent)
        self.database = database
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        title = QLabel("错题本")
        title.setObjectName("title")
        practice = QPushButton("开始错题强化")
        practice.setObjectName("primary")
        practice.clicked.connect(self.start_wrong_practice)
        mastered = QPushButton("标记已掌握")
        mastered.clicked.connect(self.mark_mastered)
        top.addWidget(title)
        top.addStretch()
        top.addWidget(practice)
        top.addWidget(mastered)
        layout.addLayout(top)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["题库", "题型", "题目", "正确答案"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.table)
        self.refresh()

    def refresh(self) -> None:
        questions = HistoryService(self.database).wrong_questions()
        self.table.setRowCount(len(questions))
        for row, question in enumerate(questions):
            for column, value in enumerate([question.bank_name, question.question_type.value, question.stem, display_answer(question.answer)]):
                item = QTableWidgetItem(str(value))
                item.setData(Qt.UserRole, question.id)
                self.table.setItem(row, column, item)

    def mark_mastered(self) -> None:
        row = self.table.currentRow()
        if row >= 0:
            HistoryService(self.database).mark_mastered(int(self.table.item(row, 0).data(Qt.UserRole)))
            self.refresh()

    def create_wrong_session(self):
        return QuizService(self.database).create_session(
            {"wrong_only": True}, None, QuizMode.SEQUENTIAL
        )

    def start_wrong_practice(self) -> None:
        try:
            session = self.create_wrong_session()
        except ValueError:
            QMessageBox.information(self, "暂无错题", "当前没有待强化的错题。")
            return
        QuizDialog(self.database, session, self).exec()
        self.refresh()


class HistoryPage(QWidget):
    def __init__(self, database: Database, parent=None):
        super().__init__(parent)
        self.database = database
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        title = QLabel("练习记录")
        title.setObjectName("title")
        view = QPushButton("查看答题详情")
        view.clicked.connect(self.review)
        top.addWidget(title)
        top.addStretch()
        top.addWidget(view)
        layout.addLayout(top)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["开始时间", "模式", "完成时间", "得分", "总分"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.table)
        self.refresh()

    def refresh(self) -> None:
        sessions = HistoryService(self.database).list()
        self.table.setRowCount(len(sessions))
        for row, session in enumerate(sessions):
            values = [session["started_at"], session["mode"], session.get("completed_at") or "未完成", session.get("score") or 0, session.get("total") or 0]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setData(Qt.UserRole, session["id"])
                self.table.setItem(row, column, item)

    def review(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        session = HistoryService(self.database).get(int(self.table.item(row, 0).data(Qt.UserRole)))
        ReviewDialog("答题详情", session["items"], self).exec()


class SettingsPage(QWidget):
    data_changed = Signal()

    def __init__(self, database: Database, data_dir: Path, parent=None):
        super().__init__(parent)
        self.database = database
        self.data_dir = data_dir
        self.backups = BackupService(database.path, data_dir / "backups")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(16)
        title = QLabel("设置与数据保护")
        title.setObjectName("title")
        layout.addWidget(title)
        subtitle = QLabel("备份、恢复和模板均在本机完成，不会连接网络。")
        subtitle.setObjectName("heroText")
        layout.addWidget(subtitle)

        card = QFrame()
        card.setObjectName("settingsCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 20, 22, 22)
        card_layout.setSpacing(14)
        card_title = QLabel("数据安全与迁移")
        card_title.setObjectName("sectionTitle")
        card_layout.addWidget(card_title)
        path_label = QLabel(f"本地数据目录：{data_dir}")
        path_label.setObjectName("statCaption")
        path_label.setWordWrap(True)
        path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        card_layout.addWidget(path_label)
        backup = QPushButton("立即备份")
        restore = QPushButton("从备份恢复")
        templates = QPushButton("导出三种题库模板")
        open_dir = QPushButton("打开数据目录")
        self.action_buttons = {
            "backup": backup,
            "restore": restore,
            "templates": templates,
            "open_dir": open_dir,
        }
        action_icons = {
            "backup": "database-backup",
            "restore": "rotate-ccw",
            "templates": "file-spreadsheet",
            "open_dir": "folder-open",
        }
        for key, button in self.action_buttons.items():
            button.setProperty("role", "dashboardAction")
            button.setIcon(load_svg_icon(action_icons[key], ThemeTokens.PRIMARY, 22))
            button.setIconSize(QSize(22, 22))
        backup.clicked.connect(self.create_backup)
        restore.clicked.connect(self.restore_backup)
        templates.clicked.connect(self.export_templates)
        open_dir.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(data_dir))))
        action_grid = QGridLayout()
        action_grid.setSpacing(12)
        for index, button in enumerate(self.action_buttons.values()):
            action_grid.addWidget(button, index // 2, index % 2)
        card_layout.addLayout(action_grid)
        apply_soft_shadow(card)
        layout.addWidget(card)

        learning_card = QFrame()
        learning_card.setObjectName("learningDataCard")
        learning_layout = QVBoxLayout(learning_card)
        learning_layout.setContentsMargins(22, 18, 22, 20)
        learning_layout.setSpacing(10)
        learning_title = QLabel("本地学习数据")
        learning_title.setObjectName("sectionTitle")
        learning_layout.addWidget(learning_title)
        learning_note = QLabel(
            "可分别清理错题本、练习记录，或只重置首页学习概览。每次操作前都会自动备份。"
        )
        learning_note.setObjectName("statCaption")
        learning_note.setWordWrap(True)
        learning_layout.addWidget(learning_note)
        self.learning_data_buttons = {
            "wrong": QPushButton("清空错题本"),
            "history": QPushButton("清空练习记录"),
            "overview": QPushButton("重置学习概览"),
        }
        learning_icons = {
            "wrong": "target",
            "history": "notebook-tabs",
            "overview": "chart-no-axes-combined",
        }
        learning_actions = QHBoxLayout()
        learning_actions.setSpacing(12)
        for key, button in self.learning_data_buttons.items():
            button.setProperty("role", "dashboardAction")
            button.setIcon(load_svg_icon(learning_icons[key], ThemeTokens.ERROR, 22))
            button.setIconSize(QSize(22, 22))
            button.clicked.connect(
                lambda _checked=False, action=key: self.clear_learning_data(action)
            )
            learning_actions.addWidget(button, 1)
        learning_layout.addLayout(learning_actions)
        apply_soft_shadow(learning_card)
        layout.addWidget(learning_card)

        offline_card = QFrame()
        offline_card.setObjectName("overviewPanel")
        offline_layout = QHBoxLayout(offline_card)
        offline_icon = QLabel()
        offline_icon.setPixmap(
            load_svg_icon("circle-check-big", ThemeTokens.SUCCESS, 24).pixmap(QSize(24, 24))
        )
        offline = QLabel("完全离线运行 · 不上传题库、答案或成绩 · 卸载时可选择保留个人数据")
        offline.setObjectName("heroText")
        offline.setWordWrap(True)
        offline_layout.addWidget(offline_icon)
        offline_layout.addWidget(offline, 1)
        layout.addWidget(offline_card)

        copyright_notice = QLabel(
            "本软件由雨辰开发并维护，未经许可请勿复制、修改或用于商业用途。"
        )
        copyright_notice.setObjectName("copyrightNotice")
        copyright_notice.setWordWrap(True)
        copyright_notice.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        layout.addWidget(copyright_notice)
        layout.addStretch()

    def export_templates(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "选择模板保存位置")
        if not directory:
            return
        try:
            TemplateService.export_all(directory)
            QMessageBox.information(self, "导出完成", "Excel、Word、PPT 三种题库模板已导出。")
        except FileExistsError as exc:
            if QMessageBox.question(
                self,
                "模板已存在",
                f"{exc}\n是否覆盖这些文件？",
            ) == QMessageBox.Yes:
                try:
                    TemplateService.export_all(directory, overwrite=True)
                    QMessageBox.information(self, "导出完成", "三种题库模板已覆盖。")
                except Exception as overwrite_exc:
                    QMessageBox.warning(self, "导出失败", str(overwrite_exc))
        except Exception as exc:
            QMessageBox.warning(self, "导出失败", str(exc))

    def create_backup(self) -> None:
        try:
            path = self.backups.create_backup()
            QMessageBox.information(self, "备份完成", f"备份已保存：\n{path}")
        except Exception as exc:
            QMessageBox.warning(self, "备份失败", str(exc))

    def clear_learning_data(self, action: str) -> None:
        actions = {
            "wrong": {
                "title": "确认清空错题本",
                "prompt": (
                    "确定清空本机错题本吗？\n\n"
                    "只删除错题状态，不删除题库、解析资料、练习记录、答案或成绩。"
                ),
                "operation": self.database.clear_wrong_questions,
                "success": "错题本已清空",
            },
            "history": {
                "title": "确认清空练习记录",
                "prompt": (
                    "确定清空全部练习和考试记录吗？\n\n"
                    "将删除历史答题明细、答案和成绩；题库、解析资料和错题本保留。"
                ),
                "operation": self.database.clear_practice_history,
                "success": "练习记录已清空",
            },
            "overview": {
                "title": "确认重置学习概览",
                "prompt": (
                    "确定让学习首页的进度、趋势和最近活动从现在重新统计吗？\n\n"
                    "练习记录、错题本、题库和解析资料都不会被删除。"
                ),
                "operation": self.database.reset_learning_overview,
                "success": "学习概览已重置",
            },
        }
        config = actions.get(action)
        if config is None:
            return
        if QMessageBox.question(
            self,
            str(config["title"]),
            f"{config['prompt']}\n\n执行前会自动创建安全备份，是否继续？",
        ) != QMessageBox.Yes:
            return
        try:
            backup_path = self.backups.create_backup()
            config["operation"]()
            self.data_changed.emit()
            QMessageBox.information(
                self,
                str(config["success"]),
                f"{config['success']}。\n安全备份：\n{backup_path}",
            )
        except Exception as exc:
            QMessageBox.warning(self, "操作失败", str(exc))

    def restore_backup(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "选择备份", str(self.data_dir / "backups"), "数据库备份 (*.db)")
        if not path:
            return
        if QMessageBox.question(self, "确认恢复", "恢复会覆盖当前数据，是否继续？") != QMessageBox.Yes:
            return
        try:
            self.backups.create_backup(protect=Path(path))
            self.backups.restore_backup(path)
            QMessageBox.information(self, "恢复完成", "数据已恢复，请重新启动应用。")
        except Exception as exc:
            QMessageBox.warning(self, "恢复失败", str(exc))


class MainWindow(QMainWindow):
    def __init__(self, database: Database, data_dir: str | Path, parent=None):
        super().__init__(parent)
        self.database = database
        self.data_dir = Path(data_dir)
        self.setWindowTitle(PRODUCT_NAME)
        self.setMinimumSize(980, 660)
        fit_window_to_available(self, 1180, 760)
        self.home_page = HomePage(database)
        self.bank_page = BankPage(database)
        self.exam_page = SessionSetupPage(database, QuizMode.EXAM)
        self.sequential_page = SessionSetupPage(database, QuizMode.SEQUENTIAL)
        self.wrong_page = WrongPage(database)
        self.history_page = HistoryPage(database)
        self.settings_page = SettingsPage(database, self.data_dir)

        central = QWidget()
        central.setObjectName("appContent")
        shell = QHBoxLayout(central)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        navigation = QFrame()
        navigation.setObjectName("navigationRail")
        navigation.setFixedWidth(205)
        navigation_layout = QVBoxLayout(navigation)
        navigation_layout.setContentsMargins(16, 24, 16, 18)
        navigation_layout.setSpacing(8)
        brand_row = QHBoxLayout()
        brand_mark = QFrame()
        brand_mark.setObjectName("brandMark")
        brand_mark.setFixedSize(38, 38)
        brand_mark_layout = QVBoxLayout(brand_mark)
        brand_mark_layout.setContentsMargins(0, 0, 0, 0)
        brand_glyph = QLabel("题")
        brand_glyph.setObjectName("brandGlyph")
        brand_glyph.setAlignment(Qt.AlignCenter)
        brand_mark_layout.addWidget(brand_glyph)
        brand = QLabel(PRODUCT_NAME)
        brand.setObjectName("brandTitle")
        brand_row.addWidget(brand_mark)
        brand_row.addWidget(brand)
        brand_row.addStretch()
        brand_caption = QLabel("本地学习中心")
        brand_caption.setObjectName("brandCaption")
        navigation_layout.addLayout(brand_row)
        navigation_layout.addWidget(brand_caption)
        navigation_layout.addSpacing(20)

        self.page_stack = QStackedWidget()
        self.pages = {
            "home": self.home_page,
            "bank": self.bank_page,
            "exam": self.exam_page,
            "sequential": self.sequential_page,
            "wrong": self.wrong_page,
            "history": self.history_page,
            "settings": self.settings_page,
        }
        labels = {
            "home": "学习首页",
            "bank": "题库管理",
            "exam": "100 分试卷",
            "sequential": "顺序刷题",
            "wrong": "错题强化",
            "history": "练习记录",
            "settings": "设置",
        }
        self.navigation_icon_names = {
            "home": "house",
            "bank": "library",
            "exam": "file-text",
            "sequential": "circle-play",
            "wrong": "target",
            "history": "chart-no-axes-combined",
            "settings": "settings",
        }
        self.navigation_buttons: dict[str, QPushButton] = {}
        for key, page in self.pages.items():
            self.page_stack.addWidget(page)
            button = QPushButton(labels[key])
            button.setProperty("role", "nav")
            button.setIcon(load_svg_icon(self.navigation_icon_names[key], ThemeTokens.MUTED, 21))
            button.setIconSize(QSize(21, 21))
            button.setCheckable(True)
            button.clicked.connect(lambda _checked=False, page_key=key: self.navigate(page_key))
            self.navigation_buttons[key] = button
            navigation_layout.addWidget(button)
        navigation_layout.addStretch()
        offline = QLabel("完全离线 · 数据仅存本机")
        offline.setObjectName("offlineCaption")
        offline.setWordWrap(True)
        navigation_layout.addWidget(offline)

        shell.addWidget(navigation)
        shell.addWidget(self.page_stack, 1)
        self.setCentralWidget(central)
        self.page_stack.currentChanged.connect(self.refresh_current)
        self.home_page.navigate_requested.connect(self.navigate)
        self.bank_page.data_changed.connect(self.refresh_all)
        self.settings_page.data_changed.connect(self.refresh_all)
        self.setStyleSheet(APP_STYLE)
        self.current_page_key = "home"
        self.navigate("home")

    def navigate(self, key: str) -> None:
        if key not in self.pages:
            return
        self.current_page_key = key
        self.page_stack.setCurrentWidget(self.pages[key])
        for page_key, button in self.navigation_buttons.items():
            selected = page_key == key
            button.setChecked(selected)
            button.setIcon(
                load_svg_icon(
                    self.navigation_icon_names[page_key],
                    ThemeTokens.PRIMARY if selected else ThemeTokens.MUTED,
                    21,
                )
            )

    def refresh_all(self) -> None:
        self.home_page.refresh()
        self.exam_page.refresh()
        self.sequential_page.refresh()
        self.wrong_page.refresh()
        self.history_page.refresh()

    def refresh_current(self, index: int) -> None:
        widget = self.page_stack.widget(index)
        refresh = getattr(widget, "refresh", None)
        if callable(refresh):
            refresh()
