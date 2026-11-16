from __future__ import annotations

from PySide2.QtGui import QColor
from PySide2.QtWidgets import QGraphicsDropShadowEffect, QWidget


class ThemeTokens:
    PALE_BLUE = "#DFEBFD"
    CANVAS = "#F4F8FF"
    CARD = "#FFFFFF"
    PRIMARY = "#2F7FEA"
    PRIMARY_HOVER = "#246FD4"
    TEXT = "#12345B"
    MUTED = "#6F8199"
    BORDER = "#D6E3F4"
    SUCCESS = "#38A88A"
    ERROR = "#E4687F"
    WARNING = "#E9A94A"


def build_app_style() -> str:
    t = ThemeTokens
    return f"""
QWidget {{ color: {t.TEXT}; }}
QMainWindow, QDialog {{ background: {t.CANVAS}; color: {t.TEXT}; font-family: "Microsoft YaHei UI"; font-size: 14px; }}
QWidget#appContent, QWidget#dashboardCanvas {{ background: {t.CANVAS}; }}
QFrame#navigationRail {{ background: #F9FBFF; border: none; border-right: 1px solid {t.BORDER}; }}
QFrame#brandMark {{ background: {t.PRIMARY}; border-radius: 10px; }}
QLabel#brandGlyph {{ color: white; font-size: 18px; font-weight: 800; }}
QLabel#brandTitle {{ color: {t.TEXT}; font-size: 20px; font-weight: 700; }}
QLabel#brandCaption, QLabel#offlineCaption {{ color: {t.MUTED}; font-size: 12px; }}
QPushButton[role="nav"] {{ color: #496580; text-align: left; padding: 12px 16px; border: none; border-radius: 12px; background: transparent; font-size: 14px; }}
QPushButton[role="nav"]:hover {{ background: #EDF4FF; color: {t.PRIMARY}; }}
QPushButton[role="nav"]:checked {{ background: {t.PALE_BLUE}; color: {t.PRIMARY}; font-weight: 700; }}
QFrame#heroCard {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #F8FBFF, stop:1 {t.PALE_BLUE}); border: 1px solid #D4E3F7; border-radius: 20px; }}
QLabel#heroTitle {{ color: {t.TEXT}; font-size: 28px; font-weight: 700; }}
QLabel#heroText {{ color: {t.MUTED}; font-size: 14px; }}
QLabel#copyrightNotice {{ color: {t.MUTED}; font-size: 12px; padding: 2px 8px; }}
QFrame#statCard, QFrame#contentCard, QFrame#settingsCard, QFrame#learningDataCard {{ background: {t.CARD}; border: 1px solid {t.BORDER}; border-radius: 16px; }}
QFrame#statIconHost {{ background: #E9F2FF; border: none; border-radius: 10px; }}
QFrame#overviewPanel {{ background: #FBFDFF; border: 1px solid #E2EBF7; border-radius: 14px; }}
QScrollArea#dashboardScroll {{ border: none; background: transparent; }}
QPushButton[role="dashboardAction"] {{ min-height: 56px; text-align: left; padding-left: 16px; background: #FBFDFF; border: 1px solid #DFE9F6; border-radius: 12px; }}
QPushButton[role="dashboardAction"]:hover {{ background: #EDF5FF; border-color: #B8D3F7; color: {t.PRIMARY}; }}
QLabel[role="activityRow"] {{ background: #FBFDFF; border: 1px solid #E4ECF6; border-radius: 9px; padding: 10px 12px; color: #36536D; }}
QLabel#statTitle {{ color: #46627F; font-size: 14px; font-weight: 600; }}
QLabel#statValue {{ color: {t.TEXT}; font-size: 30px; font-weight: 700; }}
QLabel#statCaption {{ color: {t.MUTED}; font-size: 12px; }}
QGroupBox {{ background: white; border: 1px solid {t.BORDER}; border-radius: 14px; margin-top: 14px; padding: 16px; font-weight: 600; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 14px; padding: 0 6px; color: {t.TEXT}; }}
QPushButton {{ padding: 9px 16px; border: 1px solid #C7D8EC; border-radius: 9px; background: white; color: #284A6B; }}
QPushButton:hover {{ border-color: #7FB0EF; color: {t.PRIMARY}; background: #F5F9FF; }}
QPushButton#primary {{ background: {t.PRIMARY}; color: white; border-color: {t.PRIMARY}; font-weight: 600; }}
QPushButton#primary:hover {{ background: {t.PRIMARY_HOVER}; }}
QPushButton[role="typeFilter"] {{ min-width: 86px; padding: 8px 14px; }}
QPushButton[role="typeFilter"]:checked {{ background: #E5F1FF; border: 2px solid {t.PRIMARY}; color: #155A96; font-weight: 700; }}
QLineEdit, QComboBox, QSpinBox, QTextEdit, QTextBrowser {{ padding: 8px; border: 1px solid #C8D8EA; border-radius: 8px; background: white; color: {t.TEXT}; selection-background-color: #A8C9F5; }}
QComboBox QAbstractItemView {{ color: {t.TEXT}; background: white; selection-background-color: {t.PALE_BLUE}; }}
QRadioButton, QCheckBox {{ padding: 11px 14px; spacing: 10px; border: 1px solid #D7E3F0; border-radius: 9px; background: #FBFDFF; color: #253D55; }}
QRadioButton:hover, QCheckBox:hover {{ border-color: #84AFE3; background: #F3F8FF; }}
QRadioButton:checked, QCheckBox:checked {{ border: 2px solid {t.PRIMARY}; background: #EAF3FF; color: #174F79; font-weight: 600; }}
QRadioButton::indicator, QCheckBox::indicator {{ width: 18px; height: 18px; }}
QTableWidget {{ color: {t.TEXT}; border: 1px solid {t.BORDER}; border-radius: 10px; gridline-color: #E7EEF7; background: white; alternate-background-color: #F7FAFE; }}
QHeaderView::section {{ background: #EAF2FC; color: #35546F; padding: 9px; border: none; border-right: 1px solid #D5E2F0; font-weight: 600; }}
QLabel#title {{ font-size: 24px; font-weight: 700; color: {t.TEXT}; }}
QLabel#sectionTitle {{ font-size: 18px; font-weight: 700; color: {t.TEXT}; }}
QFrame#answerReviewPanel {{ background: white; border: 1px solid #C9D9E8; border-radius: 14px; }}
QFrame#answerReviewPanel[resultState="correct"] {{ border: 2px solid {t.SUCCESS}; background: #F5FCFA; }}
QFrame#answerReviewPanel[resultState="wrong"] {{ border: 2px solid {t.ERROR}; background: #FFF8FA; }}
QFrame#answerReviewPanel[resultState="pending"] {{ border: 2px solid {t.WARNING}; background: #FFFBF2; }}
QFrame#reviewStatusIcon {{ border-radius: 15px; background: #EAF3FF; }}
QLabel#reviewStatus {{ font-size: 18px; font-weight: 700; color: {t.TEXT}; }}
QLabel#reviewScore {{ font-size: 16px; font-weight: 700; color: #315B7E; }}
QLabel#reviewCaption {{ color: {t.MUTED}; font-size: 12px; font-weight: 600; }}
QTextBrowser#userAnswer, QTextBrowser#correctAnswer, QTextBrowser#reviewExplanation {{ background: white; border: 1px solid #DBE6F1; border-radius: 8px; padding: 8px; }}
QTextBrowser#correctAnswer {{ color: #17633C; }}
QFrame#questionNavigator {{ background: white; border: 1px solid {t.BORDER}; border-radius: 14px; }}
QPushButton[role="question"] {{ min-width: 34px; max-width: 34px; min-height: 34px; max-height: 34px; padding: 0; border-radius: 17px; background: #F0F5FB; border: 1px solid #D5E1ED; color: #53697D; }}
QPushButton[role="question"][questionState="current"] {{ background: {t.PRIMARY}; border-color: {t.PRIMARY}; color: white; font-weight: 700; }}
QPushButton[role="question"][questionState="correct"] {{ background: #DFF4EA; border-color: #7FC4A9; color: #17634D; }}
QPushButton[role="question"][questionState="wrong"] {{ background: #FDE7EC; border-color: #E89AAA; color: #9D3449; }}
QPushButton[role="question"][questionState="answered"] {{ background: #DCEBFC; border-color: #8DB4E5; color: #245C86; }}
QProgressBar {{ border: none; border-radius: 5px; background: #DFE8F4; height: 10px; text-align: center; color: transparent; }}
QProgressBar::chunk {{ background: {t.PRIMARY}; border-radius: 5px; }}
QScrollBar:vertical {{ width: 10px; background: transparent; }}
QScrollBar::handle:vertical {{ background: #B5C9E1; border-radius: 5px; min-height: 28px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""


def apply_soft_shadow(widget: QWidget, level: str = "card") -> None:
    effect = QGraphicsDropShadowEffect(widget)
    if level == "hero":
        effect.setBlurRadius(32)
        effect.setOffset(0, 8)
        effect.setColor(QColor(47, 127, 234, 35))
    else:
        effect.setBlurRadius(20)
        effect.setOffset(0, 5)
        effect.setColor(QColor(35, 73, 118, 24))
    widget.setGraphicsEffect(effect)
