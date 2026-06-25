"""
Dialogs — minimal black/white sheets. Compact, clean.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from app.theme import *


class ConfirmDialog(QDialog):
    """Minimal confirmation dialog."""

    def __init__(self, title: str, message: str,
                 confirm_text: str = "确认", cancel_text: str = "取消",
                 confirm_danger: bool = False, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(340, 160)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(14)

        msg = QLabel(message)
        msg.setFont(QFont(FONT_FAMILY, 11))
        msg.setWordWrap(True)
        msg.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none;")
        msg.setAlignment(Qt.AlignCenter)
        layout.addWidget(msg)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.setSpacing(10)

        cancel = QPushButton(cancel_text)
        cancel.setFixedSize(80, 30)
        cancel.setFont(QFont(FONT_FAMILY, 11))
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.setStyleSheet(f"""
            QPushButton {{
                background: {BG_PRIMARY}; color: {TEXT_PRIMARY};
                border: 1px solid {BORDER}; border-radius: {RADIUS_SM}px;
            }}
            QPushButton:hover {{
                background: {BG_HOVER};
            }}
        """)
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)

        confirm = QPushButton(confirm_text)
        confirm.setFixedSize(80, 30)
        confirm.setFont(QFont(FONT_FAMILY, 11, QFont.DemiBold))
        confirm.setCursor(Qt.PointingHandCursor)
        bg = "#DC2626" if confirm_danger else TEXT_PRIMARY
        confirm.setStyleSheet(f"""
            QPushButton {{
                background: {bg}; color: white;
                border: none; border-radius: {RADIUS_SM}px;
            }}
            QPushButton:hover {{
                background: {bg};
            }}
        """)
        confirm.clicked.connect(self.accept)
        btn_row.addWidget(confirm)

        layout.addLayout(btn_row)

        self.setStyleSheet(f"""
            QDialog {{
                background: {BG_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: {RADIUS_XL}px;
            }}
        """)


class InputDialog(QDialog):
    """Minimal input dialog."""

    def __init__(self, title: str, label: str,
                 placeholder: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(340, 150)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(12)

        lbl = QLabel(label)
        lbl.setFont(QFont(FONT_FAMILY, 11))
        lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none;")
        layout.addWidget(lbl)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(placeholder)
        self.input_field.setFont(QFont(FONT_FAMILY, 11))
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {BORDER};
                border-radius: {RADIUS_SM}px;
                padding: 8px 12px;
                color: {TEXT_PRIMARY};
                background: {BG_PRIMARY};
            }}
            QLineEdit:focus {{
                border: 1.5px solid {BORDER_ACTIVE};
            }}
        """)
        layout.addWidget(self.input_field)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.setSpacing(10)

        cancel = QPushButton("取消")
        cancel.setFixedSize(72, 28)
        cancel.setFont(QFont(FONT_FAMILY, 11))
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.setStyleSheet(f"""
            QPushButton {{
                background: {BG_PRIMARY}; color: {TEXT_PRIMARY};
                border: 1px solid {BORDER}; border-radius: {RADIUS_SM}px;
            }}
            QPushButton:hover {{
                background: {BG_HOVER};
            }}
        """)
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)

        ok = QPushButton("确定")
        ok.setFixedSize(72, 28)
        ok.setFont(QFont(FONT_FAMILY, 11, QFont.DemiBold))
        ok.setCursor(Qt.PointingHandCursor)
        ok.setStyleSheet(f"""
            QPushButton {{
                background: {TEXT_PRIMARY}; color: white;
                border: none; border-radius: {RADIUS_SM}px;
            }}
            QPushButton:hover {{
                background: {TEXT_PRIMARY};
            }}
        """)
        ok.clicked.connect(self.accept)
        btn_row.addWidget(ok)

        layout.addLayout(btn_row)

        self.setStyleSheet(f"""
            QDialog {{
                background: {BG_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: {RADIUS_XL}px;
            }}
        """)

    def get_value(self) -> str:
        return self.input_field.text().strip()
