"""
Main window — ultra-flat. White sidebar + content, no decorations.
"""
import sys, os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QStatusBar, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon

from app.theme import *
from app.pages.generate_page import GeneratePage
from app.pages.history_page import HistoryPage
from app.pages.stats_page import StatsPage
from app.pages.settings_page import SettingsPage
from app.widgets.nav_sidebar import NavSidebar
from app.services import database as db
from app.services.storage import load_config, get_config_dir
import app.services.storage as store


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("听力练习")
        self.setMinimumSize(900, 600)
        self.resize(1050, 680)

        self._init_backend()

        c = QWidget()
        self.setCentralWidget(c)
        ml = QHBoxLayout(c)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(0)

        # Sidebar
        self.nav = NavSidebar()
        ml.addWidget(self.nav)

        # Content
        rp = QWidget()
        rp.setStyleSheet(f"background: {BG_PRIMARY};")
        rl = QVBoxLayout(rp)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background: {BG_PRIMARY};")
        self.pages = [GeneratePage(), HistoryPage(), StatsPage(), SettingsPage()]
        for p in self.pages:
            self.stack.addWidget(p)
        rl.addWidget(self.stack, 1)
        ml.addWidget(rp, 1)

        # Status
        self.status = QStatusBar()
        self.status.setStyleSheet(f"""
            QStatusBar {{
                background: {BG_PRIMARY}; color: {TEXT_SECONDARY};
                font-size: 11px; border-top: 1px solid {BORDER};
                padding: 1px 16px;
            }}
            QStatusBar::item {{ border: none; }}
        """)
        self.status.showMessage("就绪")
        self.setStatusBar(self.status)

        self.nav.page_selected.connect(self._switch)
        self.nav.set_active_page(0)
        self._apply_global_style()
        self._restore_geometry()

    def _init_backend(self):
        d = get_config_dir()
        p = os.path.join(d, "listening_app.db")
        if not os.path.exists(p):
            lp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "listening_app.db")
            if os.path.exists(lp):
                p = lp
        db.set_db_path(p)

    def _apply_global_style(self):
        self.setStyleSheet(f"""
            QToolTip {{
                background: {TEXT_PRIMARY}; color: {TEXT_WHITE};
                border: none; padding: 4px 8px;
                border-radius: {RADIUS_SM}px; font-size: 11px;
            }}
            QScrollBar:vertical {{
                background: transparent; width: 4px; margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {BORDER}; border-radius: 2px; min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {BORDER_HOVER};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QScrollBar:horizontal {{ background: transparent; height: 0; }}
        """)

    def _switch(self, idx):
        self.stack.setCurrentIndex(idx)
        self.nav.set_active_page(idx)

    def _restore_geometry(self):
        cfg = load_config()
        g = cfg.get("window_geometry", "")
        if g:
            try:
                self.restoreGeometry(bytes.fromhex(g))
            except Exception:
                pass

    def closeEvent(self, event):
        cfg = load_config()
        cfg["window_geometry"] = self.saveGeometry().hex()
        store.save_config(cfg)
        super().closeEvent(event)


def run():
    QApplication.setStyle("Fusion")
    app = QApplication(sys.argv)
    app.setFont(QFont(FONT_FAMILY, 11))
    # Set app icon from bundled _internal resource
    base = os.path.dirname(os.path.abspath(__file__))
    for p in [os.path.join(base, "app_icon.ico"),
              os.path.join(base, "..", "app_icon.ico")]:
        if os.path.exists(p):
            app.setWindowIcon(QIcon(p))
            break
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
