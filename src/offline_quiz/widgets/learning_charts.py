from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QWidget


class ProgressRing(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.percent = 0
        self.practiced = 0
        self.total = 0
        self.setMinimumSize(178, 178)

    def set_progress(self, percent: int, practiced: int, total: int) -> None:
        self.percent = max(0, min(100, int(percent)))
        self.practiced = max(0, int(practiced))
        self.total = max(0, int(total))
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        side = min(self.width(), self.height()) - 30
        ring = QRectF(
            (self.width() - side) / 2,
            (self.height() - side) / 2,
            side,
            side,
        )
        pen = QPen(QColor("#DFE8F4"), 13, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen)
        painter.drawArc(ring, 0, 360 * 16)
        pen.setColor(QColor("#2F7FEA"))
        painter.setPen(pen)
        painter.drawArc(ring, 90 * 16, -self.percent * 360 * 16 // 100)
        painter.setPen(QColor("#12345B"))
        font = QFont("Microsoft YaHei UI", 22, QFont.Bold)
        painter.setFont(font)
        painter.drawText(ring.adjusted(0, 22, 0, -18), Qt.AlignCenter, f"{self.percent}%")
        painter.setPen(QColor("#6F8199"))
        painter.setFont(QFont("Microsoft YaHei UI", 10))
        painter.drawText(ring.adjusted(0, 72, 0, 0), Qt.AlignCenter, "学习进度")


class TrendChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.values: list[int] = []
        self.labels: list[str] = []
        self.setMinimumHeight(190)

    def set_data(self, points: list[dict]) -> None:
        self.values = [int(point.get("count", 0)) for point in points]
        self.labels = [str(point.get("date", ""))[5:].replace("-", "/") for point in points]
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        chart = QRectF(34, 16, max(1, self.width() - 48), max(1, self.height() - 46))
        maximum = max(self.values, default=0)
        scale_max = max(1, maximum)
        painter.setFont(QFont("Microsoft YaHei UI", 8))
        for index in range(4):
            y = chart.top() + chart.height() * index / 3
            painter.setPen(QPen(QColor("#D6E3F4"), 1, Qt.DashLine))
            painter.drawLine(QPointF(chart.left(), y), QPointF(chart.right(), y))
            value = round(scale_max * (3 - index) / 3)
            painter.setPen(QColor("#6F8199"))
            painter.drawText(QRectF(0, y - 8, 30, 16), Qt.AlignRight | Qt.AlignVCenter, str(value))
        if not self.values:
            return
        step = chart.width() / max(1, len(self.values) - 1)
        points = QPolygonF()
        for index, value in enumerate(self.values):
            x = chart.left() + step * index
            y = chart.bottom() - chart.height() * value / scale_max
            points.append(QPointF(x, y))
        painter.setPen(QPen(QColor("#2F7FEA"), 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        if len(points) > 1:
            painter.drawPolyline(points)
        for index, point in enumerate(points):
            painter.setBrush(QColor("white"))
            painter.setPen(QPen(QColor("#2F7FEA"), 2))
            painter.drawEllipse(point, 4, 4)
            if index < len(self.labels):
                painter.setPen(QColor("#6F8199"))
                painter.drawText(
                    QRectF(point.x() - 24, chart.bottom() + 7, 48, 18),
                    Qt.AlignCenter,
                    self.labels[index],
                )
