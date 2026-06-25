"""
Generate Page — compact dashed cards. Row1+2 side by side. Weakness horizontal.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QComboBox, QFrame, QScrollArea, QProgressBar, QLayout,
    QApplication, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QShortcut, QKeySequence
from app.theme import *
from app.widgets.exercise_item import ExerciseItem
from app.services.generate_service import GenerateService
from app.services.models import GenerateRequest, Exercise
from app.services import storage as store
from app.services import database as db

MARGIN = 28


class DashedCard(QFrame):
    """Compact rounded dashed border card. Thinner line, dense spacing."""

    def __init__(self, padding=14):
        super().__init__()
        self.setObjectName("dc")
        self.setStyleSheet(f"""
            QFrame#dc {{
                background: transparent;
                border: 1px dashed {BORDER_DASH};
                border-radius: 8px;
            }}
        """)
        self._l = QVBoxLayout(self)
        self._l.setContentsMargins(padding, padding, padding, padding)
        self._l.setSpacing(10)

    def add(self, item):
        if isinstance(item, QWidget):
            self._l.addWidget(item)
        else:
            self._l.addLayout(item)

    def layout(self):
        return self._l


class AutoGrowTextEdit(QTextEdit):
    """Auto-resizing text input."""

    def __init__(self, placeholder="", min_lines=2, max_lines=10):
        super().__init__()
        self._min = min_lines
        self._max = max_lines
        self.setPlaceholderText(placeholder)
        self.setFont(QFont(FONT_FAMILY, 11))
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.document().contentsChanged.connect(self._resize)
        self._resize()

    def _resize(self):
        d = self.document()
        d.setTextWidth(self.viewport().width())
        m = self.contentsMargins()
        fm = self.fontMetrics()
        dh = d.size().height()
        pad = d.documentMargin() * 2 + 8
        h = int(dh + pad + m.top() + m.bottom())
        lh = fm.lineSpacing()
        self.setFixedHeight(max(lh * self._min + pad, min(h, lh * self._max + pad)))

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._resize()


class FlatCombo(QComboBox):
    """Combo with arrow."""

    def __init__(self, items, w=110):
        super().__init__()
        self.addItems(items)
        self.setFixedHeight(INPUT_HEIGHT)
        self.setMinimumWidth(w)
        self.setFont(QFont(FONT_FAMILY, 11))
        self.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {BORDER}; border-radius: {RADIUS_SM}px;
                padding: 3px 8px 3px 8px; color: {TEXT_PRIMARY};
                background: {BG_PRIMARY}; font-size: 11px;
            }}
            QComboBox:focus {{ border-color: {BORDER_ACTIVE}; }}
            QComboBox::drop-down {{ border: none; width: 22px;
                subcontrol-origin: padding; subcontrol-position: top right; }}
            QComboBox::down-arrow {{ width: 8px; height: 8px; }}
            QComboBox QAbstractItemView {{
                border: 1px solid {BORDER}; background: {BG_PRIMARY}; padding: 2px 0;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 4px 10px; min-height: 20px; color: {TEXT_PRIMARY};
            }}
            QComboBox QAbstractItemView::item:selected {{ background: {BG_SELECTED}; }}
        """)


class StudentHistoryCombo(QComboBox):
    """Editable combo with history."""

    def __init__(self):
        super().__init__()
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.lineEdit().setPlaceholderText("输入学生姓名")
        self.setFont(QFont(FONT_FAMILY, 11))
        self.setFixedHeight(INPUT_HEIGHT)
        self.setMinimumWidth(60)
        self.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {BORDER}; border-radius: {RADIUS_SM}px;
                padding: 3px 6px 3px 8px; color: {TEXT_PRIMARY};
                background: {BG_PRIMARY}; font-size: 11px;
            }}
            QComboBox:focus {{ border-color: {BORDER_ACTIVE}; }}
            QComboBox::drop-down {{ border: none; width: 20px;
                subcontrol-origin: padding; subcontrol-position: top right; }}
            QComboBox::down-arrow {{ width: 8px; height: 8px; }}
            QComboBox QAbstractItemView {{
                border: 1px solid {BORDER}; background: {BG_PRIMARY}; padding: 2px 0;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 4px 10px; min-height: 20px; color: {TEXT_PRIMARY};
            }}
            QComboBox QAbstractItemView::item:selected {{ background: {BG_SELECTED}; }}
            QComboBox QAbstractItemView::item:hover {{ background: {BG_HOVER}; }}
        """)
        self._load_items()
        self.setCurrentText("")

    def _load_items(self):
        cfg = store.load_config()
        for n in cfg.get("student_history", []):
            self.addItem(n)

    def save_current(self, name):
        cfg = store.load_config()
        names = cfg.get("student_history", [])
        if name in names:
            names.remove(name)
        names.insert(0, name)
        cfg["student_history"] = names[:10]
        store.save_config(cfg)
        self.blockSignals(True)
        self.clear()
        for n in names[:10]:
            self.addItem(n)
        self.setCurrentText(name)
        self.blockSignals(False)


class WeaknessRow(QWidget):
    """Weakness type: label then □ checkbox, clickable."""

    toggled = Signal(str, bool)

    def __init__(self, key):
        super().__init__()
        self.key = key
        self._sel = False
        self.label = WEAKNESS_LABELS.get(key, key)
        self.setCursor(Qt.PointingHandCursor)

        l = QHBoxLayout(self)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(4)
        self.text = QLabel(self.label)
        self.text.setFont(QFont(FONT_FAMILY, 11))
        self.text.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none;")
        l.addWidget(self.text)
        self.cb = QLabel("□")
        self.cb.setFont(QFont(FONT_FAMILY, 11))
        self.cb.setFixedWidth(14)
        self.cb.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none;")
        l.addWidget(self.cb)
        l.addStretch()

    def mousePressEvent(self, e):
        self._sel = not self._sel
        self.cb.setText("☑" if self._sel else "□")
        self.text.setStyleSheet(
            f"color: {TEXT_PRIMARY}; border: none; font-weight: {'600' if self._sel else '400'};")
        self.toggled.emit(self.key, self._sel)

    def is_selected(self):
        return self._sel


class GeneratePage(QWidget):
    """Compact generate page — side-by-side top cards, horizontal weakness."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background: {BG_PRIMARY};")
        self._service = GenerateService()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(MARGIN, MARGIN, MARGIN, MARGIN)
        layout.setSpacing(20)

        # ── Row: Card1 (student) + Card2 (level+count) side by side ──
        top_row = QHBoxLayout()
        top_row.setSpacing(14)

        # Card 1: Student — label + input same row with spacing
        c1 = DashedCard(padding=12)
        sr = QHBoxLayout()
        sr.setSpacing(12)
        sl = QLabel("学生姓名")
        sl.setFont(QFont(FONT_FAMILY, 11))
        sl.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none;")
        sr.addWidget(sl)
        self.student_combo = StudentHistoryCombo()
        sr.addWidget(self.student_combo, 1)
        c1.add(sr)
        top_row.addWidget(c1, 1)

        # Card 2: Level + Count
        c2 = DashedCard(padding=10)
        lr = QHBoxLayout()
        lr.setSpacing(14)
        lc = QHBoxLayout()
        lc.setSpacing(4)
        ll = QLabel("考试类型")
        ll.setFont(QFont(FONT_FAMILY, 11))
        ll.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none;")
        lc.addWidget(ll)
        self.level_combo = FlatCombo(["KET", "PET", "中考", "高考", "雅思"], 110)
        lc.addWidget(self.level_combo)
        lr.addLayout(lc)
        cc = QHBoxLayout()
        cc.setSpacing(4)
        cl = QLabel("句数")
        cl.setFont(QFont(FONT_FAMILY, 11))
        cl.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none;")
        cc.addWidget(cl)
        self.count_combo = QComboBox()
        self.count_combo.setEditable(True)
        self.count_combo.setInsertPolicy(QComboBox.NoInsert)
        self.count_combo.addItems(["5", "3", "8"])
        # Load default count from settings
        cfg = store.load_config()
        default_count = str(cfg.get("default_count", 5))
        self.count_combo.setCurrentText(default_count)
        self.count_combo.setFixedHeight(INPUT_HEIGHT)
        self.count_combo.setMinimumWidth(60)
        self.count_combo.setFont(QFont(FONT_FAMILY, 11))
        self.count_combo.setStyleSheet(f"""
            QComboBox {{ border: 1px solid {BORDER}; border-radius: {RADIUS_SM}px;
                padding: 2px 8px; color: {TEXT_PRIMARY};
                background: {BG_PRIMARY}; font-size: 11px; }}
            QComboBox:focus {{ border-color: {BORDER_ACTIVE}; }}
            QComboBox::drop-down {{ border: none; width: 18px; }}
            QComboBox::down-arrow {{ width: 8px; height: 8px; }}
            QComboBox QAbstractItemView {{
                border: 1px solid {BORDER}; background: {BG_PRIMARY};
                selection-background-color: {BG_SELECTED};
            }}
            QComboBox QAbstractItemView::item {{ padding: 3px 8px; }}
        """)
        cc.addWidget(self.count_combo)
        lr.addLayout(cc)
        lr.addStretch()
        c2.add(lr)
        top_row.addWidget(c2, 1)

        layout.addLayout(top_row)

        # ── Card 3: Weakness — title row + options row ──
        c3 = DashedCard(padding=12)
        # Title row
        wl = QLabel("薄弱类型")
        wl.setFont(QFont(FONT_FAMILY, 11))
        wl.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none;")
        c3.add(wl)
        # Options row
        wr = QHBoxLayout()
        wr.setSpacing(16)
        self.weakness_items = {}
        for key in ["pronunciation", "collocation", "structure", "implicature"]:
            w = WeaknessRow(key)
            w.toggled.connect(self._on_weakness)
            wr.addWidget(w)
            self.weakness_items[key] = w
        wr.addStretch()
        c3.add(wr)
        layout.addWidget(c3)

        # ── Card 4: Input area ──
        c4 = DashedCard(padding=12)
        self.sentence_input = AutoGrowTextEdit("请输入完整的原文句子...", 3, 10)
        self.sentence_input.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {BORDER}; border-radius: {RADIUS_SM}px;
                padding: 8px 12px; color: {TEXT_PRIMARY};
                background: {BG_PRIMARY}; font-size: 11px;
            }}
            QTextEdit:focus {{ border: 1.5px solid {BORDER_ACTIVE}; }}
        """)
        c4.add(self.sentence_input)
        self.detail_input = AutoGrowTextEdit("补充信息（可选）", 1, 6)
        self.detail_input.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {BORDER}; border-radius: {RADIUS_SM}px;
                padding: 6px 12px; color: {TEXT_PRIMARY};
                background: {BG_PRIMARY}; font-size: 11px;
            }}
            QTextEdit:focus {{ border: 1.5px solid {BORDER_ACTIVE}; }}
        """)
        c4.add(self.detail_input)
        layout.addWidget(c4)

        # ── Generate button ──
        br = QHBoxLayout()
        br.addStretch()
        self.progress = QProgressBar()
        self.progress.setFixedSize(80, 3)
        self.progress.setRange(0, 0)
        self.progress.setStyleSheet(f"""
            QProgressBar {{ border: none; background: {BORDER}; border-radius: 2px; }}
            QProgressBar::chunk {{ background: {TEXT_PRIMARY}; border-radius: 2px; }}
        """)
        self.progress.setVisible(False)
        br.addWidget(self.progress)
        br.addSpacing(8)
        self.go_btn = QPushButton("生成练习")
        self.go_btn.setFixedSize(110, BTN_HEIGHT)
        self.go_btn.setFont(QFont(FONT_FAMILY, 11, QFont.DemiBold))
        self.go_btn.setCursor(Qt.PointingHandCursor)
        self.go_btn.setStyleSheet(f"""
            QPushButton {{
                background: {TEXT_PRIMARY}; color: {TEXT_WHITE};
                border: none; border-radius: {RADIUS_SM}px; font-size: 11px;
            }}
            QPushButton:hover {{ background: {TEXT_PRIMARY}; }}
            QPushButton:disabled {{ background: {BORDER}; color: {TEXT_PLACEHOLDER}; }}
        """)
        self.go_btn.clicked.connect(self._generate)
        br.addWidget(self.go_btn)
        layout.addLayout(br)

        # ── Output ──
        self._build_output(layout)
        scroll.setWidget(inner)
        pl = QVBoxLayout(self)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.addWidget(scroll)
        # Global speed control state
        self.SPEEDS = [1.0, 0.75, 1.25, 1.5]
        self._speed_idx = 0
        self.speed_btn = None  # created in _show_results

        QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(self._generate)
        QShortcut(QKeySequence("Ctrl+Enter"), self).activated.connect(self._generate)

    def _build_output(self, layout):
        self.output = QWidget()
        self.output.setStyleSheet("background: transparent;")
        self.ol = QVBoxLayout(self.output)
        self.ol.setContentsMargins(0, 6, 0, 0)
        self.ol.setSpacing(14)

        # Empty state
        self.empty = QLabel("输入句子，点击「生成练习」")
        self.empty.setAlignment(Qt.AlignCenter)
        self.empty.setFont(QFont(FONT_FAMILY, 11))
        self.empty.setStyleSheet(f"color: {TEXT_PLACEHOLDER}; border: none; padding: 30px;")
        self.ol.addWidget(self.empty)

        # Progress state — step indicator
        self.progress_widget = QFrame()
        self.progress_widget.setStyleSheet("background: transparent;")
        pw = QVBoxLayout(self.progress_widget)
        pw.setAlignment(Qt.AlignCenter)
        pw.setSpacing(10)
        pw.setContentsMargins(0, 20, 0, 20)

        self.step_labels = []
        steps = ["诊断分析", "生成练习句", "合成音频", "保存存档"]
        self.step_indicators = []
        for i, s in enumerate(steps):
            row = QHBoxLayout()
            row.setSpacing(8)
            row.setAlignment(Qt.AlignCenter)
            icon = QLabel("○")
            icon.setFont(QFont(FONT_FAMILY, 12))
            icon.setStyleSheet(f"color: {TEXT_PLACEHOLDER}; border: none;")
            self.step_indicators.append(icon)
            row.addWidget(icon)
            label = QLabel(s)
            label.setFont(QFont(FONT_FAMILY, 11))
            label.setStyleSheet(f"color: {TEXT_PLACEHOLDER}; border: none;")
            self.step_labels.append(label)
            row.addWidget(label)
            pw.addLayout(row)

        # Error state
        self.error_widget = QFrame()
        self.error_widget.setStyleSheet("background: transparent;")
        ew = QVBoxLayout(self.error_widget)
        ew.setAlignment(Qt.AlignCenter)
        ew.setSpacing(10)
        self.error_icon = QLabel("✕")
        self.error_icon.setFont(QFont(FONT_FAMILY, 18))
        self.error_icon.setAlignment(Qt.AlignCenter)
        self.error_icon.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none;")
        ew.addWidget(self.error_icon)
        self.error_msg = QLabel("")
        self.error_msg.setAlignment(Qt.AlignCenter)
        self.error_msg.setWordWrap(True)
        self.error_msg.setFont(QFont(FONT_FAMILY, 11))
        self.error_msg.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none;")
        ew.addWidget(self.error_msg)
        self.retry_btn = QPushButton("重试")
        self.retry_btn.setFixedSize(90, BTN_HEIGHT)
        self.retry_btn.setFont(QFont(FONT_FAMILY, 11))
        self.retry_btn.setCursor(Qt.PointingHandCursor)
        self.retry_btn.setStyleSheet(f"""
            QPushButton {{
                background: {TEXT_PRIMARY}; color: white;
                border: none; border-radius: {RADIUS_SM}px;
            }}
            QPushButton:hover {{ background: {TEXT_PRIMARY}; }}
        """)
        self.retry_btn.clicked.connect(self._retry)
        ew.addWidget(self.retry_btn, 0, Qt.AlignCenter)
        self.error_widget.setVisible(False)

        self.progress_widget.setVisible(False)
        self.ol.addWidget(self.progress_widget)
        self.ol.addWidget(self.error_widget)

        # Results
        self.results = QFrame()
        self.results.setStyleSheet("background: transparent;")
        self.rl = QVBoxLayout(self.results)
        self.rl.setContentsMargins(0, 0, 0, 0)
        self.rl.setSpacing(14)
        self.results.setVisible(False)
        self.ol.addWidget(self.results, 1)
        layout.addWidget(self.output, 1)

    def _set_step(self, index, state):
        """state: 'waiting', 'current', 'done', 'error'"""
        icons = {"waiting": "○", "current": "◎", "done": "✓", "error": "✕"}
        colors = {
            "waiting": TEXT_PLACEHOLDER,
            "current": TEXT_PRIMARY,
            "done": TEXT_PRIMARY,
            "error": TEXT_PRIMARY,
        }
        self.step_indicators[index].setText(icons[state])
        self.step_indicators[index].setStyleSheet(f"color: {colors[state]}; border: none;")
        self.step_labels[index].setStyleSheet(f"color: {colors[state]}; border: none;")
        QApplication.processEvents()

    def _show_error(self, msg):
        self.progress_widget.setVisible(False)
        self.error_msg.setText(msg)
        self.error_widget.setVisible(True)
        self.empty.setVisible(False)
        self.results.setVisible(False)
        self.go_btn.setEnabled(True)
        self.go_btn.setText("生成练习")
        self.progress.setVisible(False)

    def _on_weakness(self, k, s):
        sel = [k for k, w in self.weakness_items.items() if w.is_selected()]
        ps = {"pronunciation": "哪个词/哪部分发音没抓住？（可选）",
              "collocation": "感觉哪里有固定搭配没听出来？（可选）",
              "structure": "哪个结构没理解？（倒装/从句/省略…）（可选）",
              "implicature": "谁在说话？什么情境？（可选）"}
        self.detail_input.setPlaceholderText(ps.get(sel[0], "补充信息（可选）") if len(sel) == 1 else "补充信息（可选）")

    def _generate(self):
        student = self.student_combo.currentText().strip()
        level = self.level_combo.currentText()
        sentence = self.sentence_input.toPlainText().strip()
        sel = [k for k, w in self.weakness_items.items() if w.is_selected()]
        ct = self.count_combo.currentText().strip()
        try:
            count = max(1, min(50, int(ct)))
        except ValueError:
            count = 5
        if not student:
            self._show_error("请输入学生姓名")
            return
        if not sentence:
            self._show_error("请输入原文句子")
            return
        if not sel:
            self._show_error("请选择至少一个薄弱类型")
            return

        # Save for retry
        self._last_req = (student, level, sel, sentence, count)
        self.student_combo.save_current(student)

        # Show progress
        self.empty.setVisible(False)
        self.error_widget.setVisible(False)
        self.results.setVisible(False)
        self.progress_widget.setVisible(True)
        self.go_btn.setEnabled(False)
        self.go_btn.setText("生成中...")
        self.progress.setVisible(True)
        for i in range(4):
            self._set_step(i, "waiting")

        # Check API key first
        cfg = store.load_config()
        if not cfg.get("api_key"):
            self._show_error("请先在设置页面配置 DeepSeek API Key")
            return

        # Run pipeline in next event loop iteration (keeps UI responsive)
        QTimer.singleShot(100, lambda: self._run_pipeline(student, level, sel, sentence, count))

    def _run_pipeline(self, student, level, sel, sentence, count):
        """Run the actual pipeline with step-by-step progress."""
        self._set_step(0, "current")
        QApplication.processEvents()

        try:
            # Step 1: AI diagnosis
            req = GenerateRequest(student=student, level=level, weakness_types=sel,
                                  sentence=sentence,
                                  details=self.detail_input.toPlainText().strip(),
                                  exercise_count=count)
            result = self._service.ai.generate(req)
            if not result.exercises:
                err = self._service.ai.get_last_error()
                if err:
                    err_str = str(err)
                    if "余额" in err_str or "balance" in err_str.lower() or "402" in err_str:
                        self._show_error("DeepSeek API 余额不足，请充值后重试")
                        return
                    if "401" in err_str or "unauthorized" in err_str.lower() or "密钥" in err_str or "未配置" in err_str:
                        self._show_error("API Key 无效或未配置，请检查设置页面")
                        return
                    if "timeout" in err_str.lower() or "timed out" in err_str.lower() or "网络" in err_str:
                        self._show_error("API 请求超时，请检查网络连接后重试")
                        return
                    self._show_error(f"API 调用失败: {err_str[:80]}")
                    return
                self._show_error("AI 生成失败，请稍后重试")
                return
            self._set_step(0, "done")
            self._set_step(1, "current")
            QApplication.processEvents()

            # Step 2: DB save (quick)
            student_obj = db.get_student_by_name(student)
            if not student_obj:
                student_obj = db.add_student(student)
            self._set_step(1, "done")
            self._set_step(2, "current")
            QApplication.processEvents()

            # Step 3: TTS + file save
            try:
                base_dir = store.get_default_save_dir()
                archive_dir = store.build_archive_path(
                    base_dir, level, student, sel)
                audio_files = self._service.tts.synthesize_batch(
                    result.exercises, archive_dir)
                for i, ex in enumerate(result.exercises):
                    if i < len(audio_files) and audio_files[i]:
                        ex.audio_file = audio_files[i]
                store.save_session_json(archive_dir, req, result, audio_files)
                store.save_diagnosis_txt(archive_dir, result)
                for i, ex in enumerate(result.exercises):
                    store.save_exercise_txt(archive_dir, ex, i + 1)
            except Exception as e:
                self._show_error(f"音频或文件保存失败: {str(e)[:60]}")
                return
            self._set_step(2, "done")
            self._set_step(3, "current")
            QApplication.processEvents()

            # Step 4: DB record
            try:
                import json as _json
                output_json = _json.dumps({
                    "diagnosis": result.diagnosis,
                    "exercises": [{"sentence": e.sentence, "translation": e.translation,
                                   "target": e.target, "explanation": e.explanation,
                                   "weakness_type": e.weakness_type} for e in result.exercises],
                }, ensure_ascii=False)
                db.save_practice_record(student_obj.id, req, result.session_id,
                                         output_json, archive_dir)
            except Exception:
                pass  # DB save is non-critical
            self._set_step(3, "done")
            QApplication.processEvents()

            # Show results
            self.progress_widget.setVisible(False)
            self._show_results(result)

        except Exception as e:
            self._show_error(f"生成出错: {str(e)[:80]}")
            import traceback
            traceback.print_exc()

    def _retry(self):
        if hasattr(self, '_last_req'):
            s, l, sel, sent, c = self._last_req
            self._generate()

    def _show_results(self, result):
        self._clear(self.rl)

        # ── Diagnosis section — compact cards ──
        if result and result.diagnosis:
            diag_header = QLabel("诊断分析")
            diag_header.setFont(QFont(FONT_FAMILY, 12, QFont.DemiBold))
            diag_header.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none;")
            self.rl.addWidget(diag_header)

            for wt, analysis in result.diagnosis.items():
                card = QFrame()
                card.setObjectName(f"diag_{wt}")
                card.setStyleSheet(f"""
                    QFrame#diag_{wt} {{
                        background: transparent;
                        border: 1px dashed {BORDER_DASH};
                        border-radius: 4px;
                    }}
                """)
                dl = QVBoxLayout(card)
                dl.setContentsMargins(12, 10, 12, 10)
                dl.setSpacing(4)

                # Type label
                hl = QLabel(WEAKNESS_LABELS.get(wt, wt))
                hl.setFont(QFont(FONT_FAMILY, 11, QFont.DemiBold))
                hl.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none;")
                dl.addWidget(hl)

                # Summary
                summary = analysis.get("summary", "")
                if summary:
                    sl = QLabel(summary)
                    sl.setWordWrap(True)
                    sl.setFont(QFont(FONT_FAMILY, 11))
                    sl.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none;")
                    dl.addWidget(sl)

                self.rl.addWidget(card)
        self.rl.addSpacerItem(QSpacerItem(0, 6, QSizePolicy.Minimum, QSizePolicy.Fixed))
        if result and result.exercises:
            # Header row: title + global speed control
            hr = QHBoxLayout()
            hr.setSpacing(6)
            et = QLabel(f"针对性练习（{len(result.exercises)} 句）")
            et.setFont(QFont(FONT_FAMILY, 12, QFont.DemiBold))
            et.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none;")
            hr.addWidget(et)
            hr.addStretch()
            sl = QLabel("语速")
            sl.setFont(QFont(FONT_FAMILY, 10))
            sl.setStyleSheet(f"color: {TEXT_SECONDARY}; border: none;")
            hr.addWidget(sl)
            self.speed_btn = QPushButton("1×")
            self.speed_btn.setFixedSize(50, 22)
            self.speed_btn.setFont(QFont(FONT_FAMILY, 10))
            self.speed_btn.setCursor(Qt.PointingHandCursor)
            self.speed_btn.setStyleSheet(f"""
                QPushButton {{ background: transparent; color: {TEXT_PRIMARY};
                    border: 1px solid {BORDER}; border-radius: {RADIUS_PILL}px;
                    font-size: 10px; }}
                QPushButton:hover {{ border-color: {TEXT_PRIMARY}; }}
            """)
            self.speed_btn.clicked.connect(self._cycle_speed)
            hr.addWidget(self.speed_btn)
            hw = QWidget()
            hw.setLayout(hr)
            hw.setStyleSheet("border: none;")
            self.rl.addWidget(hw)
            for ex in result.exercises:
                self.rl.addWidget(ExerciseItem(ex))
        self.results.setVisible(True)
        self.go_btn.setEnabled(True)
        self.go_btn.setText("生成练习")
        self.progress.setVisible(False)

    def _cycle_speed(self):
        self._speed_idx = (self._speed_idx + 1) % len(self.SPEEDS)
        speed = self.SPEEDS[self._speed_idx]
        self.speed_btn.setText(f"{speed}×" if speed != 1.0 else "1×")
        from app.widgets.exercise_item import ExerciseItem
        ExerciseItem._player.set_speed(speed)
        if speed != 1.0:
            self.speed_btn.setStyleSheet(f"""
                QPushButton {{ background: {BG_SELECTED}; color: {TEXT_PRIMARY};
                    border: 1px solid {TEXT_PRIMARY}; border-radius: {RADIUS_PILL}px;
                    font-size: 10px; }}
                QPushButton:hover {{ background: {BG_HOVER}; }}
            """)
        else:
            self.speed_btn.setStyleSheet(f"""
                QPushButton {{ background: transparent; color: {TEXT_PRIMARY};
                    border: 1px solid {BORDER}; border-radius: {RADIUS_PILL}px;
                    font-size: 10px; }}
                QPushButton:hover {{ border-color: {TEXT_PRIMARY}; }}
            """)

    def _clear(self, l):
        while l.count():
            c = l.takeAt(0)
            if c.widget():
                c.widget().deleteLater()
