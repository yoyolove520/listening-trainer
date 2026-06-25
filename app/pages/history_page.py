"""
History page — compact fonts, dashed card items.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame,
    QComboBox, QHBoxLayout, QPushButton, QScrollArea,
    QLineEdit, QMenu
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from app.theme import *
from app.services.archive_service import ArchiveService
from app.services.models import ArchiveSummary, ArchiveFilter

MARGIN = 28
CARD_STYLE = f"""
    QFrame#dc {{ background: transparent;
        border: 1px dashed {BORDER_DASH}; border-radius: 4px; }}
    QFrame#dc:hover {{ background: {BG_HOVER}; }}
"""


class ArchiveItem(QFrame):
    """Archive entry — compact."""

    def __init__(self, archive: ArchiveSummary):
        super().__init__()
        self.archive = archive
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("dc")
        self.setStyleSheet(CARD_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        r1 = QHBoxLayout()
        r1.setSpacing(8)
        tm = QLabel(archive.created_at)
        tm.setFont(QFont(FONT_FAMILY, 10))
        tm.setStyleSheet(f"color: {TEXT_SECONDARY}; border: none;")
        r1.addWidget(tm)
        sn = QLabel(archive.student)
        sn.setFont(QFont(FONT_FAMILY, 11, QFont.DemiBold))
        sn.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none;")
        r1.addWidget(sn)
        lt = QLabel(archive.level)
        lt.setFont(QFont(FONT_FAMILY, 10, QFont.DemiBold))
        lt.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none;")
        r1.addWidget(lt)
        for wt in archive.weakness_types:
            lbl = WEAKNESS_LABELS.get(wt, wt)
            wtl = QLabel(lbl)
            wtl.setFont(QFont(FONT_FAMILY, 10))
            wtl.setStyleSheet(f"color: {TEXT_SECONDARY}; border: none;")
            r1.addWidget(wtl)
        r1.addStretch()
        layout.addLayout(r1)

        sl = QLabel(f'"{archive.sentence}"')
        sl.setFont(QFont(FONT_FAMILY, 11))
        sl.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none;")
        sl.setWordWrap(True)
        if len(archive.sentence) > 80:
            sl.setText(f'"{archive.sentence[:80]}...')
        layout.addWidget(sl)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(f"""QMenu {{ background: {BG_PRIMARY}; border: 1px solid {BORDER};
            border-radius: {RADIUS_MD}px; padding: 4px; }}
            QMenu::item {{ padding: 4px 20px; border-radius: {RADIUS_SM}px;
                color: {TEXT_PRIMARY}; font-size: 11px; }}
            QMenu::item:selected {{ background: {BG_SELECTED}; }}""")
        od = menu.addAction("打开所在文件夹")
        menu.addSeparator()
        da = menu.addAction("删除存档")
        ea = menu.addAction("导出")
        action = menu.exec(event.globalPos())
        if action == od:
            self._open_dir()
        elif action == da:
            self._delete()
        elif action == ea:
            self._export()

    def _open_dir(self):
        import subprocess, os
        p = self.archive.path.replace("/", os.sep)
        if os.path.isdir(p):
            subprocess.Popen(["explorer", p])

    def _delete(self):
        from app.widgets.dialogs import ConfirmDialog
        dlg = ConfirmDialog("删除存档", "确定要删除此存档吗？",
                            confirm_text="删除", confirm_danger=True, parent=self.window())
        if dlg.exec():
            import shutil, os
            p = self.archive.path.replace("/", os.sep)
            if os.path.isdir(p):
                shutil.rmtree(p, ignore_errors=True)
            self.deleteLater()

    def _export(self):
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        import os, zipfile
        p = self.archive.path.replace("/", os.sep)
        if not os.path.isdir(p):
            return
        sp, _ = QFileDialog.getSaveFileName(self, "导出存档", f"{self.archive.session_id}.zip", "ZIP (*.zip)")
        if sp:
            try:
                with zipfile.ZipFile(sp, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for root, _, files in os.walk(p):
                        for fn in files:
                            zf.write(os.path.join(root, fn), os.path.relpath(os.path.join(root, fn), p))
                QMessageBox.information(self, "导出成功", "存档已导出")
            except Exception as e:
                QMessageBox.warning(self, "导出失败", str(e))


class HistoryPage(QWidget):
    """History — compact fonts, functional filters."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background: {BG_PRIMARY};")
        self._service = ArchiveService()
        self._filter_combos = {}

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(MARGIN, MARGIN, MARGIN, MARGIN)
        layout.setSpacing(12)

        self._build_filter_bar(layout)
        self.archive_container = QWidget()
        self.archive_list_layout = QVBoxLayout(self.archive_container)
        self.archive_list_layout.setContentsMargins(0, 0, 0, 0)
        self.archive_list_layout.setSpacing(8)
        self.archive_list_layout.setAlignment(Qt.AlignTop)
        layout.addWidget(self.archive_container, 1)
        self._populate_archives()

        scroll.setWidget(inner)
        pl = QVBoxLayout(self)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.addWidget(scroll)

    def _build_filter_bar(self, layout):
        fc = QFrame()
        fc.setObjectName("dc")
        fc.setStyleSheet(f"QFrame#dc {{ background: transparent; border: 1px dashed {BORDER_DASH}; border-radius: 4px; }}")
        fl = QHBoxLayout(fc)
        fl.setContentsMargins(12, 8, 12, 8)
        fl.setSpacing(10)

        # Load real student names from database
        from app.services import database as db
        all_students = ["全部"] + [s.name for s in db.get_all_students()]
        for label, items in [("学生", all_students), ("等级", ["全部", "KET", "PET", "中考", "高考", "雅思"]), ("类型", ["全部", "单词发音", "固定搭配", "句式结构", "言外之意"])]:
            w, cb = self._filter_combo(label, items)
            self._filter_combos[label] = cb
            fl.addWidget(w)

        self._date_from = QLineEdit()
        self._date_from.setPlaceholderText("从 (如 2026-01-01)")
        self._date_from.setText("")
        self._date_from.setFixedHeight(26)
        self._date_from.setFixedWidth(110)
        self._date_from.setFont(QFont(FONT_FAMILY, 10))
        self._date_from.setStyleSheet(f"QLineEdit {{ border: 1px solid {BORDER}; border-radius: {RADIUS_SM}px; padding: 2px 6px; color: {TEXT_PRIMARY}; background: {BG_PRIMARY}; font-size: 10px; }}")
        fl.addWidget(self._date_from)
        tl = QLabel("~")
        tl.setStyleSheet(f"color: {TEXT_SECONDARY}; border: none;")
        fl.addWidget(tl)
        self._date_to = QLineEdit()
        self._date_to.setPlaceholderText("到 (如 2026-06-23)")
        self._date_to.setText("")
        self._date_to.setFixedHeight(26)
        self._date_to.setFixedWidth(110)
        self._date_to.setFont(QFont(FONT_FAMILY, 10))
        self._date_to.setStyleSheet(f"QLineEdit {{ border: 1px solid {BORDER}; border-radius: {RADIUS_SM}px; padding: 2px 6px; color: {TEXT_PRIMARY}; background: {BG_PRIMARY}; font-size: 10px; }}")
        fl.addWidget(self._date_to)

        sb = QPushButton("搜索")
        sb.setFixedHeight(26)
        sb.setFont(QFont(FONT_FAMILY, 11))
        sb.setCursor(Qt.PointingHandCursor)
        sb.setStyleSheet(f"QPushButton {{ background: {TEXT_PRIMARY}; color: white; border: none; border-radius: {RADIUS_SM}px; padding: 0 14px; font-size: 11px; }}")
        sb.clicked.connect(self._on_search)
        fl.addWidget(sb)
        fl.addStretch()
        layout.addWidget(fc)

    def _filter_combo(self, label, items):
        c = QWidget()
        c.setStyleSheet("border: none;")
        hl = QHBoxLayout(c)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(3)
        lb = QLabel(label)
        lb.setFont(QFont(FONT_FAMILY, 11))
        lb.setStyleSheet(f"color: {TEXT_SECONDARY}; border: none;")
        hl.addWidget(lb)
        cb = QComboBox()
        cb.addItems(items)
        cb.setFixedHeight(26)
        cb.setFont(QFont(FONT_FAMILY, 11))
        cb.setMinimumWidth(60)
        cb.setStyleSheet(f"QComboBox {{ border: 1px solid {BORDER}; border-radius: {RADIUS_SM}px; padding: 2px 6px; background: {BG_PRIMARY}; color: {TEXT_PRIMARY}; font-size: 11px; }} QComboBox::drop-down {{ border: none; width: 18px; }} QComboBox QAbstractItemView {{ border: 1px solid {BORDER}; background: {BG_PRIMARY}; selection-background-color: {BG_SELECTED}; }} QComboBox QAbstractItemView::item {{ padding: 3px 8px; }}")
        hl.addWidget(cb)
        return c, cb

    def _on_search(self):
        self._populate_archives()

    def _populate_archives(self):
        while self.archive_list_layout.count():
            child = self.archive_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Build filter from combo values
        student = self._filter_combos.get("学生").currentText() if "学生" in self._filter_combos else "全部"
        level = self._filter_combos.get("等级").currentText() if "等级" in self._filter_combos else "全部"
        wtype_label = self._filter_combos.get("类型").currentText() if "类型" in self._filter_combos else "全部"

        # Convert Chinese label to English key for filtering
        label_to_key = {v: k for k, v in WEAKNESS_LABELS.items()}
        wtype_key = label_to_key.get(wtype_label, wtype_label)

        flt = ArchiveFilter(
            student=None if student == "全部" else student,
            level=None if level == "全部" else level,
            weakness_type=None if wtype_label == "全部" else wtype_key,
            date_from=self._date_from.text().strip() or None,
            date_to=self._date_to.text().strip() or None,
        )

        archives = self._service.list_archives(flt)
        if not archives:
            em = QLabel("暂无历史记录\n生成练习后自动保存到本地")
            em.setAlignment(Qt.AlignCenter)
            em.setFont(QFont(FONT_FAMILY, 11))
            em.setStyleSheet(f"color: {TEXT_PLACEHOLDER}; border: none; padding: 60px;")
            self.archive_list_layout.addWidget(em)
        else:
            for a in archives:
                self.archive_list_layout.addWidget(ArchiveItem(a))
