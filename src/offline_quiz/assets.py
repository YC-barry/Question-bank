from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtSvgWidgets import QSvgWidget


ASSET_ROOT = Path(__file__).resolve().parent / "visual_assets"
HERO_ARTWORK = "illustrations/graduation.svg"
REQUIRED_ICONS = (
    "house",
    "library",
    "file-text",
    "circle-play",
    "target",
    "chart-no-axes-combined",
    "settings",
    "layers",
    "notebook-tabs",
    "badge-alert",
    "circle-check-big",
    "circle-x",
    "clock-3",
    "upload",
    "database-backup",
    "rotate-ccw",
    "file-spreadsheet",
    "folder-open",
)


def asset_path(name: str) -> Path:
    relative = Path(name)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"非法素材路径：{name}")
    return ASSET_ROOT / relative


@lru_cache(maxsize=128)
def load_svg_icon(name: str, color: str, size: int = 24) -> QIcon:
    if name not in REQUIRED_ICONS:
        raise KeyError(f"未知图标：{name}")
    source = asset_path(f"icons/{name}.svg").read_text(encoding="utf-8")
    source = source.replace("currentColor", QColor(color).name())
    renderer = QSvgRenderer(QByteArray(source.encode("utf-8")))
    if not renderer.isValid():
        raise ValueError(f"SVG 图标无效：{name}")
    pixels = max(1, int(size))
    pixmap = QPixmap(pixels, pixels)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


class SvgIllustration(QSvgWidget):
    def __init__(self, asset_name: str = HERO_ARTWORK, parent=None):
        super().__init__(str(asset_path(asset_name)), parent)
        self.setObjectName("heroArtwork")
        self.setAttribute(Qt.WA_TranslucentBackground)
