"""
Settings page — dashed card sections, compact, consistent.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame,
    QLineEdit, QComboBox, QPushButton, QHBoxLayout,
    QScrollArea, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from app.theme import *
from app.services.config_service import ConfigService
from app.services.models import Config
from app.services import storage as store

MARGIN = 28


def section_card(title, parent_layout):
    """Add a dashed card with title."""
    card = QFrame()
    card.setObjectName("dc")
    card.setStyleSheet(f"""
        QFrame#dc {{
            background: transparent;
            border: 1px dashed {BORDER_DASH};
            border-radius: 4px;
        }}
    """)
    cl = QVBoxLayout(card)
    cl.setContentsMargins(16, 12, 16, 12)
    cl.setSpacing(10)
    tl = QLabel(title)
    tl.setFont(QFont(FONT_FAMILY, 11, QFont.DemiBold))
    tl.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none;")
    cl.addWidget(tl)
    parent_layout.addWidget(card)
    return cl


class SettingsPage(QWidget):
    """Settings — dashed cards, compact."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background: {BG_PRIMARY};")
        self._cs = ConfigService()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(MARGIN, MARGIN, MARGIN, MARGIN)
        layout.setSpacing(14)

        # ── API Config ──
        api = section_card("API 配置", layout)
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("输入 DeepSeek API Key...")
        self.key_input.setEchoMode(QLineEdit.Password)
        self.key_input.setFont(QFont(FONT_FAMILY, 11))
        self.key_input.setFixedHeight(INPUT_HEIGHT - 2)
        self.key_input.setStyleSheet(f"""
            QLineEdit {{ border: 1px solid {BORDER}; border-radius: {RADIUS_SM}px;
                padding: 4px 10px; color: {TEXT_PRIMARY};
                background: {BG_PRIMARY}; font-size: 11px; }}
            QLineEdit:focus {{ border: 1.5px solid {BORDER_ACTIVE}; }}
        """)
        api.addWidget(self.key_input)

        ar = QHBoxLayout()
        ar.setSpacing(8)
        self.vbtn = QPushButton("验证连接")
        self.vbtn.setFixedHeight(26)
        self.vbtn.setFont(QFont(FONT_FAMILY, 11))
        self.vbtn.setCursor(Qt.PointingHandCursor)
        self.vbtn.setStyleSheet(f"""
            QPushButton {{ background: {TEXT_PRIMARY}; color: white;
                border: none; border-radius: {RADIUS_SM}px; padding: 0 14px; }}
            QPushButton:hover {{ background: {TEXT_PRIMARY}; }}
        """)
        self.vbtn.clicked.connect(self._verify)
        ar.addWidget(self.vbtn)
        self.api_st = QLabel("状态: 未配置")
        self.api_st.setFont(QFont(FONT_FAMILY, 11))
        self.api_st.setStyleSheet(f"color: {TEXT_SECONDARY}; border: none;")
        ar.addWidget(self.api_st)
        ar.addStretch()

        # Balance reminder
        self.balance_label = QLabel("请确保 API 余额充足")
        self.balance_label.setFont(QFont(FONT_FAMILY, 10))
        self.balance_label.setStyleSheet(f"color: {TEXT_SECONDARY}; border: none;")
        ar.addWidget(self.balance_label)

        api.addLayout(ar)

        # ── Preferences ──
        pref = section_card("偏好设置", layout)
        pref_items = [
            ("语音口音", ["美式英语", "英式英语"]),
            ("默认句数", ["3", "5", "10"]),
            ("默认语速", ["正常", "慢速"]),
        ]
        self.combos = {}
        for label, items in pref_items:
            r = QHBoxLayout()
            r.setSpacing(8)
            lb = QLabel(label)
            lb.setFont(QFont(FONT_FAMILY, 11))
            lb.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none;")
            lb.setFixedWidth(70)
            r.addWidget(lb)
            cb = QComboBox()
            cb.addItems(items)
            cb.setFixedHeight(26)
            cb.setMinimumWidth(120)
            cb.setFont(QFont(FONT_FAMILY, 11))
            cb.setStyleSheet(f"""
                QComboBox {{ border: 1px solid {BORDER}; border-radius: {RADIUS_SM}px;
                    padding: 2px 8px; color: {TEXT_PRIMARY};
                    background: {BG_PRIMARY}; font-size: 11px; }}
                QComboBox:focus {{ border-color: {BORDER_ACTIVE}; }}
                QComboBox::drop-down {{ border: none; width: 20px; }}
                QComboBox QAbstractItemView {{
                    border: 1px solid {BORDER}; background: {BG_PRIMARY};
                    selection-background-color: {BG_SELECTED};
                }}
                QComboBox QAbstractItemView::item {{ padding: 3px 8px; }}
            """)
            # 默认句数支持直接输入
            if label == "默认句数":
                cb.setEditable(True)
                cb.setInsertPolicy(QComboBox.NoInsert)
            r.addWidget(cb)
            r.addStretch()
            self.combos[label] = cb
            pref.addLayout(r)

        # Save dir
        dr = QHBoxLayout()
        dr.setSpacing(8)
        dl = QLabel("默认保存")
        dl.setFont(QFont(FONT_FAMILY, 11))
        dl.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none;")
        dl.setFixedWidth(70)
        dr.addWidget(dl)
        self.dir = QLineEdit()
        self.dir.setFont(QFont(FONT_FAMILY, 11))
        self.dir.setStyleSheet(f"""
            QLineEdit {{ border: 1px solid {BORDER}; border-radius: {RADIUS_SM}px;
                padding: 3px 8px; background: {BG_PRIMARY};
                color: {TEXT_PRIMARY}; font-size: 11px; }}
        """)
        self.dir.setReadOnly(True)
        dr.addWidget(self.dir, 1)
        bb = QPushButton("更改目录")
        bb.setFixedHeight(26)
        bb.setFont(QFont(FONT_FAMILY, 11))
        bb.setCursor(Qt.PointingHandCursor)
        bb.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {TEXT_PRIMARY};
                border: 1px solid {BORDER}; border-radius: {RADIUS_SM}px;
                padding: 0 12px; font-size: 11px; }}
            QPushButton:hover {{ background: {BG_HOVER}; }}
        """)
        bb.clicked.connect(self._browse_dir)
        dr.addWidget(bb)
        pref.addLayout(dr)

        # ── Data Management ──
        data = section_card("数据管理", layout)
        dr2 = QHBoxLayout()
        dr2.setSpacing(8)
        for text, handler in [("导出所有存档", self._export), ("导入存档", self._import)]:
            btn = QPushButton(text)
            btn.setFixedHeight(26)
            btn.setFont(QFont(FONT_FAMILY, 11))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{ background: transparent; color: {TEXT_PRIMARY};
                    border: 1px solid {BORDER}; border-radius: {RADIUS_SM}px;
                    padding: 0 14px; font-size: 11px; }}
                QPushButton:hover {{ background: {BG_HOVER}; }}
            """)
            btn.clicked.connect(handler)
            dr2.addWidget(btn)
        self.dbi = QLabel("数据库: —    存档: —")
        self.dbi.setFont(QFont(FONT_FAMILY, 11))
        self.dbi.setStyleSheet(f"color: {TEXT_SECONDARY}; border: none;")
        dr2.addWidget(self.dbi)
        dr2.addStretch()
        data.addLayout(dr2)

        # Save
        save_btn = QPushButton("保存设置")
        save_btn.setFixedSize(100, 28)
        save_btn.setFont(QFont(FONT_FAMILY, 11, QFont.DemiBold))
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{ background: {TEXT_PRIMARY}; color: white;
                border: none; border-radius: {RADIUS_SM}px; font-size: 11px; }}
            QPushButton:hover {{ background: {TEXT_PRIMARY}; }}
        """)
        save_btn.clicked.connect(self._save)
        sr = QHBoxLayout()
        sr.addStretch()
        sr.addWidget(save_btn)
        layout.addLayout(sr)

        layout.addStretch()
        scroll.setWidget(inner)
        pl = QVBoxLayout(self)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.addWidget(scroll)
        self._load()

    def _load(self):
        cfg = self._cs.get_all()
        self.key_input.setText(cfg.api_key)
        self._set("语音口音", cfg.voice or "美式英语")
        self._set("默认句数", str(cfg.default_count or "5"))
        self._set("默认语速", cfg.default_speed or "正常")
        self.dir.setText(cfg.default_save_dir or store.get_default_save_dir())
        if cfg.api_key:
            self.api_st.setText("状态: 密钥已配置")
            self.api_st.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none;")
        self._refresh_db()

    def _set(self, label, val):
        if label in self.combos:
            i = self.combos[label].findText(val)
            if i >= 0:
                self.combos[label].setCurrentIndex(i)

    def _refresh_db(self):
        try:
            import os
            from app.services import database as db
            p = db.get_db_path()
            sz = f"{os.path.getsize(p)/1024:.0f} KB" if os.path.exists(p) else "—"
            ov = db.get_stats_overview()
            self.dbi.setText(f"数据库: {sz}    存档: {ov.total_archives} 个")
        except Exception as e:
            self.dbi.setText(f"数据库读取失败: {str(e)[:40]}")

    def _verify(self):
        key = self.key_input.text().strip()
        if not key:
            self.api_st.setText("状态: 请输入 API Key")
            return
        self.vbtn.setEnabled(False)
        self.vbtn.setText("验证中...")
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self._do_verify)

    def _do_verify(self):
        key = self.key_input.text().strip()
        try:
            r = self._cs.verify_api_key(key)
            ok = r.get("valid", False)
            self.api_st.setText(f"状态: {r.get('message', '完成')}")
            self.api_st.setStyleSheet(f"color: {TEXT_PRIMARY if ok else TEXT_SECONDARY}; border: none;")
        except Exception:
            self.api_st.setText("状态: 验证出错")
        finally:
            self.vbtn.setEnabled(True)
            self.vbtn.setText("验证连接")

    def _save(self):
        try:
            cnt = max(1, min(50, int(self.combos["默认句数"].currentText().strip())))
        except ValueError:
            cnt = 5
        cfg = Config(
            api_key=self.key_input.text().strip(),
            voice=self.combos["语音口音"].currentText(),
            default_count=cnt,
            default_speed=self.combos["默认语速"].currentText(),
            theme="浅色",
            default_save_dir=self.dir.text(),
        )
        ok = self._cs.save(cfg)
        self.api_st.setText(f"状态: {'设置已保存' if ok else '保存失败'}")

    def _browse_dir(self):
        c = self.dir.text() or store.get_default_save_dir()
        ch = QFileDialog.getExistingDirectory(self, "选择默认保存目录", c)
        if ch:
            self.dir.setText(ch)

    def _export(self):
        import os, zipfile
        bd = store.get_default_save_dir()
        if not os.path.exists(bd):
            QMessageBox.information(self, "导出", "暂无存档可导出。")
            return
        sp, _ = QFileDialog.getSaveFileName(self, "导出存档", "听力练习备份.zip", "ZIP (*.zip)")
        if sp:
            try:
                with zipfile.ZipFile(sp, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for root, _, files in os.walk(bd):
                        for fn in files:
                            zf.write(os.path.join(root, fn), os.path.relpath(os.path.join(root, fn), bd))
                QMessageBox.information(self, "导出成功", f"已导出到: {sp}")
            except Exception as e:
                QMessageBox.warning(self, "导出失败", str(e))

    def _import(self):
        import os, zipfile
        zp, _ = QFileDialog.getOpenFileName(self, "导入存档", "", "ZIP (*.zip)")
        if zp:
            bd = store.get_default_save_dir()
            try:
                with zipfile.ZipFile(zp, 'r') as zf:
                    zf.extractall(bd)
                QMessageBox.information(self, "导入成功", f"已导入到: {bd}")
                self._refresh_db()
            except Exception as e:
                QMessageBox.warning(self, "导入失败", str(e))
