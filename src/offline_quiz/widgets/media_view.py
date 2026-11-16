from __future__ import annotations

from typing import Iterable

from PySide2.QtCore import QSize, Qt
from PySide2.QtGui import QPixmap
from PySide2.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

from ..domain import QuestionAsset
from ..media import asset_from_snapshot


class _ScaledImageLabel(QLabel):
    def __init__(self, pixmap: QPixmap, parent: QWidget | None = None):
        super().__init__(parent)
        self._source_pixmap = pixmap
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(0, 0)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)

    def sizeHint(self) -> QSize:
        width = max(1, self.width())
        height = round(width * self._source_pixmap.height() / self._source_pixmap.width())
        return QSize(width, max(1, height))

    def _scale_to_width(self, available_width: int) -> None:
        target_width = max(1, min(available_width, self._source_pixmap.width()))
        scaled = self._source_pixmap.scaledToWidth(
            target_width, Qt.SmoothTransformation
        )
        self.setPixmap(scaled)
        self.setFixedHeight(scaled.height())

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._scale_to_width(event.size().width())


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
            label = _ScaledImageLabel(pixmap)
            label.setToolTip(asset.alt_text)
            layout.addWidget(label)
        self.setVisible(layout.count() > 0)
