from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from ..assets import load_svg_icon
from ..theme import ThemeTokens


class StatCard(QFrame):
    def __init__(
        self,
        title: str,
        value: str = "0",
        caption: str = "",
        icon_name: str | None = None,
        accent: str = ThemeTokens.PRIMARY,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setMinimumHeight(126)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(5)

        header = QHBoxLayout()
        header.setSpacing(10)
        if icon_name:
            icon_host = QFrame()
            icon_host.setObjectName("statIconHost")
            icon_host.setFixedSize(38, 38)
            icon_layout = QVBoxLayout(icon_host)
            icon_layout.setContentsMargins(7, 7, 7, 7)
            self.icon_label = QLabel()
            self.icon_label.setPixmap(load_svg_icon(icon_name, accent, 24).pixmap(QSize(24, 24)))
            self.icon_label.setAlignment(Qt.AlignCenter)
            icon_layout.addWidget(self.icon_label)
            header.addWidget(icon_host)
        else:
            self.icon_label = None
        title_label = QLabel(title)
        title_label.setObjectName("statTitle")
        header.addWidget(title_label)
        header.addStretch()
        self.value_label = QLabel(value)
        self.value_label.setObjectName("statValue")
        self.value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        caption_label = QLabel(caption)
        caption_label.setObjectName("statCaption")
        caption_label.setWordWrap(True)

        layout.addLayout(header)
        layout.addWidget(self.value_label)
        layout.addWidget(caption_label)

    def set_value(self, value: int | str) -> None:
        self.value_label.setText(str(value))
