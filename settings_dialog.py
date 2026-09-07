from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QMessageBox,
    QPushButton, QFrame, QLineEdit, QComboBox, QSpinBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from config import load_config, save_config, PLATFORMS_CFG
from frameless import SolidFramelessDialog
from theme import (
    PRIMARY, TEXT_HEADING, TEXT_BODY, TEXT_SECONDARY,
    BG, BG_CARD, BORDER_WARM, BORDER_STRONG, ERROR,
    qss_font,
    mono_font as _mono_font,
)


_INPUT_CSS = f"""
QLineEdit, QComboBox, QSpinBox {{
    background: {BG_CARD};
    border: 1px solid {BORDER_STRONG};
    border-radius: 4px;
    padding: 7px 11px;
    color: {TEXT_BODY};
    {qss_font(12, 500)}
    selection-background-color: rgba(0, 230, 118, 0.25);
    selection-color: {TEXT_HEADING};
}}
QLineEdit:hover, QComboBox:hover, QSpinBox:hover {{
    border-color: {TEXT_SECONDARY};
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
    border-color: {PRIMARY};
    color: {TEXT_HEADING};
}}
QLineEdit::placeholder {{
    color: {TEXT_SECONDARY};
}}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{
    background: {BG};
    border: 1px solid {BORDER_STRONG};
    border-radius: 4px;
    padding: 4px;
    color: {TEXT_BODY};
    selection-background-color: {BG_CARD};
    selection-color: {PRIMARY};
    outline: none;
}}
QSpinBox::up-button, QSpinBox::down-button {{
    background: transparent; border: none; width: 16px;
}}
QSpinBox::up-arrow {{
    border-left: 4px solid transparent; border-right: 4px solid transparent;
    border-bottom: 5px solid {TEXT_SECONDARY};
}}
QSpinBox::down-arrow {{
    border-left: 4px solid transparent; border-right: 4px solid transparent;
    border-top: 5px solid {TEXT_SECONDARY};
}}
"""


class SettingsDialog(SolidFramelessDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(308)
        self.setMaximumWidth(308)

        root = QVBoxLayout(self)
        root.setContentsMargins(1, 1, 1, 1)
        root.setSpacing(0)

        self._title_bar(root)
        self._hline(root)

        body = QVBoxLayout()
        body.setContentsMargins(24, 16, 24, 12)
        body.setSpacing(6)

        body.addWidget(self._label("API KEY"))
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("输入 API Key")
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setStyleSheet(_INPUT_CSS)
        self.api_key_edit.setFont(_mono_font(12))
        body.addWidget(self.api_key_edit)

        body.addSpacing(6)
        body.addWidget(self._label("PLATFORM"))
        self.platform_combo = QComboBox()
        for key, info in PLATFORMS_CFG.items():
            self.platform_combo.addItem(info["name"], key)
        self.platform_combo.setStyleSheet(_INPUT_CSS)
        body.addWidget(self.platform_combo)

        body.addSpacing(6)
        body.addWidget(self._label("REFRESH"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(60, 3600)
        self.interval_spin.setSuffix(" 秒")
        self.interval_spin.setStyleSheet(_INPUT_CSS)
        body.addWidget(self.interval_spin)

        root.addLayout(body)

        self._hline(root)

        btns = QHBoxLayout()
        btns.setContentsMargins(24, 10, 24, 18)
        btns.setSpacing(10)
        btns.addStretch()

        cancel = QPushButton("取消")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.setStyleSheet(
            f"QPushButton{{background:transparent;color:{TEXT_BODY};"
            f"border:1px solid {BORDER_STRONG};"
            f"border-radius:4px;padding:7px 18px;{qss_font(12, 600)}}}"
            f"QPushButton:hover{{border-color:{TEXT_SECONDARY};color:{TEXT_HEADING};}}"
        )
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)

        save = QPushButton("保存")
        save.setCursor(Qt.CursorShape.PointingHandCursor)
        save.setStyleSheet(
            f"QPushButton{{background:{PRIMARY};color:#062015;border:none;"
            f"border-radius:4px;padding:7px 22px;{qss_font(12, 700)}}}"
            "QPushButton:hover{background:#2dff92;}"
            "QPushButton:pressed{background:#00c853;}"
        )
        save.clicked.connect(self._accept)
        btns.addWidget(save)

        root.addLayout(btns)
        self._load()

    def _title_bar(self, layout):
        bar = QHBoxLayout()
        bar.setContentsMargins(18, 12, 8, 10)

        # green square indicator
        ind = QFrame()
        ind.setFixedSize(8, 8)
        ind.setStyleSheet(f"background:{PRIMARY};border:none;")
        bar.addWidget(ind)
        bar.addSpacing(9)

        t = QLabel("SETTINGS")
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
        x.clicked.connect(self.reject)
        bar.addWidget(x)
        layout.addLayout(bar)

    @staticmethod
    def _label(text):
        l = QLabel(text)
        l.setFont(_mono_font(9, QFont.Weight.Bold, 160))
        l.setStyleSheet(f"color:{TEXT_SECONDARY};background:transparent;")
        return l

    @staticmethod
    def _hline(layout):
        s = QFrame()
        s.setFixedHeight(1)
        s.setStyleSheet(f"background:{BORDER_WARM};border:none;")
        layout.addWidget(s)

    def _load(self):
        cfg = load_config()
        self.api_key_edit.setText(cfg.get("api_key", ""))
        platform = cfg.get("platform", "zhipu")
        idx = self.platform_combo.findData(platform)
        if idx >= 0:
            self.platform_combo.setCurrentIndex(idx)
        self.interval_spin.setValue(cfg.get("refresh_interval", 300))

    def _accept(self):
        key = self.api_key_edit.text().strip()
        if not key:
            QMessageBox.warning(self, "提示", "请输入 API Key")
            return
        if "\n" in key or "\r" in key or " " in key or len(key) > 128:
            QMessageBox.warning(self, "提示", "API Key 格式不正确，请检查")
            return
        if not save_config({
            "api_key": key,
            "platform": self.platform_combo.currentData(),
            "refresh_interval": self.interval_spin.value(),
        }):
            QMessageBox.warning(self, "提示", "配置保存失败，请检查磁盘空间或权限")
            return
        self.accept()
