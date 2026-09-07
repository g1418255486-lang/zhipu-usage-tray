from datetime import datetime
import traceback
from PySide6.QtWidgets import (
    QSystemTrayIcon, QMenu,
    QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QWidget, QPushButton,
)
from PySide6.QtGui import (
    QIcon, QPixmap, QPainter, QColor, QFont,
    QAction, QPen,
)
from PySide6.QtCore import (
    QTimer, QThread, Signal, QObject, Qt, QRectF, QPointF,
)

from api_client import APIClient, UsageData
from config import load_config
from settings_dialog import SettingsDialog
from frameless import SolidFramelessDialog
from theme import (
    PRIMARY, TEXT_HEADING, TEXT_BODY, TEXT_SECONDARY,
    BG, BG_CARD, BORDER_WARM, BORDER_STRONG, ERROR, RADIUS,
    qss_font,
    mono_font as _mono_font,
    bar_color as _theme_bar_color,
)


def _bar_color(pct: float) -> QColor:
    return _theme_bar_color(pct)


def _create_icon(percentage: float = None) -> QIcon:
    # 4x supersampled rendering for crisp edges
    scale = 4
    size = 32
    big = size * scale
    cx, cy = big / 2, big / 2

    pixmap = QPixmap(big, big)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    r = big / 2 - 3 * scale
    ring_r = r - 3.5 * scale

    if percentage is not None:
        pct = max(0.0, min(100.0, float(percentage)))
        color = _bar_color(pct)

        # dark instrument disc
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(BG))
        painter.drawEllipse(QPointF(cx, cy), r, r)

        # rim so the disc reads on dark taskbars
        rim = QPen(QColor(BORDER_STRONG), 1.2 * scale)
        painter.setPen(rim)
        painter.drawEllipse(QPointF(cx, cy), r, r)

        # track + status arc (gauge)
        arc_rect = QRectF(cx - ring_r, cy - ring_r, ring_r * 2, ring_r * 2)
        track = QPen(QColor(31, 43, 38), 3 * scale)
        track.setCapStyle(Qt.PenCapStyle.FlatCap)
        painter.setPen(track)
        painter.drawArc(arc_rect, 0, 5760)

        span = int(pct / 100 * 5760)
        pen = QPen(color, 3 * scale)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        painter.setPen(pen)
        painter.drawArc(arc_rect, 1440, -span)

        # mono number
        painter.setFont(_mono_font(int(big * 0.34), QFont.Weight.Bold))
        painter.setPen(QColor("#e8f5ec"))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, str(int(round(pct))))
    else:
        # idle "Z" icon
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(BG))
        painter.drawEllipse(QPointF(cx, cy), r, r)

        rim = QPen(QColor(BORDER_STRONG), 1.2 * scale)
        painter.setPen(rim)
        painter.drawEllipse(QPointF(cx, cy), r, r)

        arc_rect = QRectF(cx - ring_r, cy - ring_r, ring_r * 2, ring_r * 2)
        pen = QPen(QColor(PRIMARY), 3 * scale)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        painter.setPen(pen)
        painter.drawArc(arc_rect, 1440, -int(0.62 * 5760))

        painter.setFont(_mono_font(int(big * 0.46), QFont.Weight.Bold))
        painter.setPen(QColor("#00e676"))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "Z")

    painter.end()

    out = pixmap.scaled(
        size, size,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    return QIcon(out)


class Worker(QObject):
    finished = Signal(object)

    def __init__(self, api_key: str, platform: str):
        super().__init__()
        self.api_key = api_key
        self.platform = platform

    def run(self):
        client = None
        try:
            client = APIClient(self.api_key, self.platform)
            data = client.fetch_all()
            self.finished.emit(data)
        except Exception as e:
            d = UsageData()
            d.error = str(e)
            self.finished.emit(d)
        finally:
            if client:
                client.close()


def _fmt_reset_time(ts) -> str:
    if not ts:
        return ""
    try:
        dt = datetime.fromtimestamp(ts / 1000)
        return f"RESET {dt:%m/%d %H:%M}"
    except Exception:
        return ""


# ─── 分段方块进度条 ───

class SegmentedProgressBar(QWidget):
    SEGMENTS = 24

    def __init__(self, percent=0, color=None, bar_height=12, parent=None):
        super().__init__(parent)
        self._percent = float(max(0, min(100, percent)))
        self._color = color or QColor(PRIMARY)
        self.setFixedHeight(bar_height)
        self.setMinimumWidth(80)

    def setPercent(self, pct):
        self._percent = float(max(0, min(100, pct)))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        h = self.height()
        gap = 2
        seg_w = (self.width() - gap * (self.SEGMENTS - 1)) / self.SEGMENTS

        filled = round(self._percent / 100 * self.SEGMENTS)

        p.setPen(Qt.PenStyle.NoPen)
        for i in range(self.SEGMENTS):
            x = i * (seg_w + gap)
            if i < filled:
                c = QColor(self._color)
                p.setBrush(c)
            else:
                p.setBrush(QColor(BORDER_WARM))
            p.drawRoundedRect(QRectF(x, 0, seg_w, h), 1.5, 1.5)


# ─── 详情弹窗 ───

class DetailDialog(SolidFramelessDialog):
    def __init__(self, data: UsageData, parent=None):
        super().__init__(parent)
        self.data = data
        self.setMinimumWidth(284)
        self.setMaximumWidth(284)

        root = QVBoxLayout(self)
        root.setContentsMargins(1, 1, 1, 1)
        root.setSpacing(0)

        self._build_content(root)

    def _build_content(self, root):
        self._title_bar(root)
        self._sep(root)
        self._body(root)

    def update_data(self, data: UsageData):
        self.data = data
        root = self.layout()
        self._clear_layout(root)
        self._build_content(root)
        self.adjustSize()

    @staticmethod
    def _clear_layout(layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
            elif item.layout():
                DetailDialog._clear_layout(item.layout())

    def _title_bar(self, layout):
        bar = QHBoxLayout()
        bar.setContentsMargins(18, 12, 8, 10)

        # green status indicator
        pct = self.data.token_5h_pct
        ind_color = _bar_color(pct).name() if pct is not None else BORDER_STRONG
        ind = QFrame()
        ind.setFixedSize(8, 8)
        ind.setStyleSheet(f"background:{ind_color};border:none;")
        bar.addWidget(ind)
        bar.addSpacing(9)

        t = QLabel((self.data.platform or "UNKNOWN").upper())
        t.setFont(_mono_font(12, QFont.Weight.Bold, 110))
        t.setStyleSheet(f"color:{TEXT_HEADING};background:transparent;")
        bar.addWidget(t)
        bar.addStretch()

        x = QPushButton("×")
        x.setFixedSize(26, 26)
        x.setCursor(Qt.CursorShape.PointingHandCursor)
        x.setStyleSheet(
            "QPushButton{background:transparent;border:none;border-radius:4px;"
            f"font-size:16px;color:{TEXT_SECONDARY};}}"
            f"QPushButton:hover{{background:{BG_CARD};color:{ERROR};}}"
        )
        x.clicked.connect(self.close)
        bar.addWidget(x)
        layout.addLayout(bar)

    def _sep(self, layout):
        s = QFrame()
        s.setFixedHeight(1)
        s.setStyleSheet(f"background:{BORDER_WARM};border:none;")
        layout.addWidget(s)

    def _body(self, layout):
        body = QVBoxLayout()
        body.setContentsMargins(22, 16, 22, 18)
        body.setSpacing(0)

        if self.data.token_5h_pct is not None:
            self._thin_bar(body, "TOKEN · 5H", self.data.token_5h_pct, self.data.token_5h_reset)

        if self.data.token_weekly_pct is not None:
            body.addSpacing(16)
            self._thin_bar(body, "WEEKLY", self.data.token_weekly_pct, self.data.token_weekly_reset)

        if self.data.error:
            body.addSpacing(12)
            e = QLabel(f"ERR: {self.data.error}")
            e.setWordWrap(True)
            e.setFont(_mono_font(11))
            e.setStyleSheet(f"color:{ERROR};background:transparent;")
            body.addWidget(e)

        layout.addLayout(body)

    def _thin_bar(self, layout, label, pct, reset_ts=None):
        row = QHBoxLayout()
        l = QLabel(label)
        l.setFont(_mono_font(10, QFont.Weight.Bold, 140))
        l.setStyleSheet(f"color:{TEXT_SECONDARY};background:transparent;")
        row.addWidget(l)
        row.addStretch()
        v = QLabel(f"{pct:.0f}%")
        v.setFont(_mono_font(12, QFont.Weight.Bold))
        v.setStyleSheet(f"color:{_bar_color(pct).name()};background:transparent;")
        row.addWidget(v)
        layout.addLayout(row)
        layout.addSpacing(5)

        bar = SegmentedProgressBar(int(min(pct, 100)), color=_bar_color(pct), bar_height=10)
        layout.addWidget(bar)

        if reset_ts:
            layout.addSpacing(4)
            r = QLabel(_fmt_reset_time(reset_ts))
            r.setFont(_mono_font(10))
            r.setStyleSheet(f"color:{TEXT_SECONDARY};background:transparent;")
            layout.addWidget(r)

    def showEvent(self, event):
        super().showEvent(event)
        self.adjustSize()
        geo = self.screen().availableGeometry()
        self.move(geo.right() - self.width() - 20, geo.bottom() - self.height() - 20)


# ─── 托盘应用 ───

_MENU_QSS = f"""
QMenu {{
    {qss_font(12, 500)}
    background: {BG};
    color: {TEXT_BODY};
    border: 1px solid {BORDER_STRONG};
    border-radius: {RADIUS}px;
    padding: 6px;
}}
QMenu::item {{
    padding: 7px 26px 7px 16px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background: {BG_CARD};
    color: {PRIMARY};
}}
QMenu::item:disabled {{
    color: {TEXT_SECONDARY};
}}
QMenu::separator {{
    height: 1px;
    background: {BORDER_WARM};
    margin: 5px 10px;
}}
"""


class TrayApp:
    def __init__(self, app):
        self.app = app
        self.config = load_config()
        self.current_data: UsageData = None
        self.worker_thread = None
        self.worker = None
        self._active_thread = None
        self._detail_dlg = None

        self.tray = QSystemTrayIcon()
        self.tray.setIcon(_create_icon())
        self.tray.setToolTip("智谱余量监控")
        self.tray.activated.connect(self._on_activated)

        menu = QMenu()
        menu.setStyleSheet(_MENU_QSS)

        self.refresh_action = QAction("刷新余量", self.app)
        self.refresh_action.triggered.connect(self.refresh)
        menu.addAction(self.refresh_action)

        self.detail_action = QAction("查看详情", self.app)
        self.detail_action.triggered.connect(self.show_detail)
        menu.addAction(self.detail_action)

        menu.addSeparator()

        settings_action = QAction("设置", self.app)
        settings_action.triggered.connect(self.show_settings)
        menu.addAction(settings_action)

        menu.addSeparator()

        quit_action = QAction("退出", self.app)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.show()

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self._start_timer()

        if not self.config.get("api_key"):
            QTimer.singleShot(500, self.show_settings)
        else:
            QTimer.singleShot(1000, self.refresh)

    def _start_timer(self):
        interval = self.config.get("refresh_interval", 300) * 1000
        self.timer.start(interval)

    def refresh(self):
        api_key = self.config.get("api_key", "")
        if not api_key:
            self.tray.showMessage(
                "智谱余量监控", "未设置 API Key，请在设置中配置",
                QSystemTrayIcon.MessageIcon.Warning, 3000,
            )
            return

        try:
            if self.worker_thread and self.worker_thread.isRunning():
                return
        except RuntimeError:
            self.worker_thread = None
            self.worker = None

        self.refresh_action.setEnabled(False)
        self.tray.setToolTip("智谱余量监控 - 正在刷新...")

        self.worker_thread = QThread()
        self.worker = Worker(api_key, self.config.get("platform", "zhipu"))
        self.worker.moveToThread(self.worker_thread)
        self.worker.finished.connect(self._on_data)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.started.connect(self.worker.run)
        self.worker_thread.start()
        self._active_thread = self.worker_thread

    def _on_data(self, data: UsageData):
        self.current_data = data
        self.refresh_action.setEnabled(True)

        try:
            if data.error and data.token_5h_pct is None and data.token_weekly_pct is None:
                self.tray.setIcon(_create_icon())
                self.tray.setToolTip(f"智谱余量监控 - 错误: {data.error[:50]}")
                self.tray.showMessage(
                    "查询失败", data.error[:100],
                    QSystemTrayIcon.MessageIcon.Critical, 5000,
                )
                return

            parts = []

            if data.token_5h_pct is not None:
                parts.append(f"Token(5h): {data.token_5h_pct:.0f}%")
            if data.token_weekly_pct is not None:
                parts.append(f"Token(周): {data.token_weekly_pct:.0f}%")

            max_pct = data.token_5h_pct if data.token_5h_pct is not None else 0

            self.tray.setIcon(_create_icon(max_pct))
            self.app.setWindowIcon(_create_icon(max_pct))
            tip = "智谱余量监控\n" + "\n".join(parts) if parts else "智谱余量监控 - 无数据"
            self.tray.setToolTip(tip)
        except Exception:
            traceback.print_exc()

    def show_detail(self):
        if self._detail_dlg is not None:
            self._detail_dlg.raise_()
            self._detail_dlg.activateWindow()
            return

        if self.current_data:
            dlg = DetailDialog(self.current_data)
            self._detail_dlg = dlg
            dlg.exec()
            self._detail_dlg = None
        else:
            self.tray.showMessage(
                "智谱余量监控", "暂无数据，请先刷新",
                QSystemTrayIcon.MessageIcon.Information, 3000,
            )

    def show_settings(self):
        dlg = SettingsDialog()
        if dlg.exec() == SettingsDialog.DialogCode.Accepted:
            self.config = load_config()
            self._start_timer()
            QTimer.singleShot(500, self.refresh)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_detail()

    def _quit(self):
        self.timer.stop()
        try:
            if self._active_thread and self._active_thread.isRunning():
                self._active_thread.quit()
                self._active_thread.wait(2000)
        except RuntimeError:
            pass
        self.tray.hide()
        self.app.quit()
