"""
Nav Sidebar — text-only, collapsible. Like Linear / Notion sidebar.
No icons, no gray backgrounds, just clean black text.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFrame
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from app.theme import *


class NavItem(QPushButton):
    """Text-only nav item with left black bar on active."""

    def __init__(self, text, page_index):
        super().__init__(text)
        self.pidx = page_index
        self._active = False
        self._expanded = True
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(32)
        self._update_style()

    def set_active(self, a):
        self._active = a
        self._update_style()

    def set_expanded(self, e):
        self._expanded = e
        self.setText(self.text().replace(" ", ""))
        self.setVisible(e)

    def _update_style(self):
        if self._active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {TEXT_PRIMARY};
                    border: none;
                    border-left: 2px solid {BORDER_ACTIVE};
                    text-align: left;
                    padding: 0 12px;
                    font-size: 12px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background: {BG_HOVER};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {TEXT_SECONDARY};
                    border: none;
                    border-left: 2px solid transparent;
                    text-align: left;
                    padding: 0 12px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    color: {TEXT_PRIMARY};
                    background: {BG_HOVER};
                }}
            """)


class NavSidebar(QFrame):
    """Collapsible text-only sidebar."""

    page_selected = Signal(int)

    def __init__(self):
        super().__init__()
        self._expanded = True
        self.setObjectName("ns")
        self._update_frame()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignTop)

        # Toggle
        self.toggle = QPushButton("☰")
        self.toggle.setFixedHeight(32)
        self.toggle.setCursor(Qt.PointingHandCursor)
        self.toggle.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {TEXT_SECONDARY};
                border: none; text-align: left; padding: 0 12px;
                font-size: 13px;
            }}
            QPushButton:hover {{ color: {TEXT_PRIMARY}; background: {BG_HOVER}; }}
        """)
        self.toggle.clicked.connect(self._toggle)
        layout.addWidget(self.toggle)

        # Thin divider
        d = QFrame()
        d.setFixedHeight(1)
        d.setStyleSheet(f"background: {BORDER}; border: none; margin: 4px 8px;")
        layout.addWidget(d)

        # Nav items
        self.items = []
        for text, idx in [("生成练习", 0), ("历史记录", 1), ("统计", 2), ("设置", 3)]:
            btn = NavItem(text, idx)
            btn.clicked.connect(lambda checked, i=idx: self._click(i))
            self.items.append(btn)
            layout.addWidget(btn)

        layout.addStretch()
        self._set_w(140)

    def _update_frame(self):
        self.setStyleSheet(f"""
            QFrame#ns {{
                background: {BG_PRIMARY};
                border-right: 1.5px dashed {BORDER_DASH};
            }}
        """)

    def _set_w(self, w):
        self.setFixedWidth(w)

    def _toggle(self):
        self._expanded = not self._expanded
        for item in self.items:
            item.set_expanded(self._expanded)
        self._set_w(SIDEBAR_EXPANDED if self._expanded else SIDEBAR_COLLAPSED)

    def _click(self, idx):
        self.set_active_page(idx)
        self.page_selected.emit(idx)

    def set_active_page(self, idx):
        for item in self.items:
            item.set_active(item.pidx == idx)
