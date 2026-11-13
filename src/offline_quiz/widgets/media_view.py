from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from ..domain import QuestionAsset
from ..media import asset_from_snapshot


class MediaView(QWidget):
    def __init__(
        self,
        assets: Iterable[QuestionAsset | dict] = (),
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 8)
        for raw_asset in assets:
            try:
                asset = (
                    asset_from_snapshot(raw_asset)
                    if isinstance(raw_asset, dict)
                    else raw_asset
                )
            except Exception:
                layout.addWidget(QLabel("附件无法读取"))
                continue
            if not asset.mime_type.startswith("image/"):
                layout.addWidget(QLabel(asset.alt_text or "题目附件"))
                continue
            pixmap = QPixmap()
            if not pixmap.loadFromData(asset.data):
                layout.addWidget(QLabel(asset.alt_text or "图片无法显示"))
                continue
            label = QLabel()
            label.setAlignment(Qt.AlignCenter)
            label.setPixmap(
                pixmap.scaled(680, 360, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            label.setToolTip(asset.alt_text)
            layout.addWidget(label)
        self.setVisible(layout.count() > 0)
