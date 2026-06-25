"""
Exercise item — always-visible progress bar, global speed control.
"""
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSlider, QMenu, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from app.theme import *
from app.services.models import Exercise
from app.services.player_service import AudioPlayer


class ExerciseItem(QFrame):
    """
    Class-level _active tracks which item currently owns the player.
    Progress bar always visible for all items.
    Speed is controlled globally (not per-item).
    """

    play_clicked = Signal(int)

    _player = AudioPlayer()
    _active = None  # the currently active ExerciseItem instance

    def __init__(self, exercise: Exercise):
        super().__init__()
        self.ex = exercise
        self._expanded = False
        self._sliding = False
        self.setObjectName("ei")
        self.setStyleSheet("QFrame#ei { background: transparent; border: none; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Row 1: Play + Tag + Sentence + 查看解析
        r1 = QHBoxLayout()
        r1.setSpacing(6)

        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(24, 24)
        self.play_btn.setFont(QFont(FONT_ENGLISH, 10))
        self.play_btn.setCursor(Qt.PointingHandCursor)
        self.play_btn.setStyleSheet(f"""
            QPushButton {{ background: {TEXT_PRIMARY}; color: white;
                border: none; border-radius: 12px; }}
            QPushButton:hover {{ background: {TEXT_PRIMARY}; }}
        """)
        self.play_btn.clicked.connect(self._toggle_play)
        if not exercise.audio_file:
            self.play_btn.setEnabled(False)
            self.play_btn.setStyleSheet(f"""
                QPushButton {{ background: {BORDER}; color: {TEXT_PLACEHOLDER};
                    border: none; border-radius: 12px; }}
            """)
        r1.addWidget(self.play_btn)

        tag = QLabel(WEAKNESS_LABELS.get(exercise.weakness_type, exercise.weakness_type))
        tag.setFont(QFont(FONT_FAMILY, 10))
        tag.setStyleSheet(f"color: {TEXT_SECONDARY}; border: none;")
        r1.addWidget(tag)

        sent = QLabel(exercise.sentence)
        sent.setFont(QFont(FONT_FAMILY, 11))
        sent.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none;")
        sent.setWordWrap(True)
        r1.addWidget(sent, 1)

        self.expand_btn = QPushButton("查看解析")
        self.expand_btn.setFixedHeight(20)
        self.expand_btn.setFont(QFont(FONT_FAMILY, 10))
        self.expand_btn.setCursor(Qt.PointingHandCursor)
        self.expand_btn.setStyleSheet(f"""
            QPushButton {{ background: {TEXT_PRIMARY}; color: white;
                border: none; border-radius: 10px; padding: 0 8px; font-size: 10px; }}
            QPushButton:hover {{ background: {TEXT_PRIMARY}; }}
        """)
        self.expand_btn.clicked.connect(self._toggle)
        r1.addWidget(self.expand_btn)

        layout.addLayout(r1)

        # Control row: Progress bar + Time (always visible)
        self.control = QFrame()
        self.control.setStyleSheet("background: transparent; border: none;")
        cr = QHBoxLayout(self.control)
        cr.setContentsMargins(0, 0, 0, 0)
        cr.setSpacing(6)

        self.progress = QSlider(Qt.Horizontal)
        self.progress.setFixedHeight(4)
        self.progress.setRange(0, 100)
        self.progress.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.progress.setStyleSheet(f"""
            QSlider::groove:horizontal {{ border: none; height: 4px;
                background: {BORDER}; border-radius: 2px; }}
            QSlider::handle:horizontal {{ background: {TEXT_PRIMARY}; width: 12px;
                height: 12px; margin: -4px 0; border-radius: 6px; }}
            QSlider::sub-page:horizontal {{ background: {TEXT_PRIMARY}; border-radius: 2px; }}
        """)
        self.progress.sliderPressed.connect(lambda: setattr(self, '_sliding', True))
        self.progress.sliderReleased.connect(self._seek)
        self.progress.sliderMoved.connect(self._scrub)
        cr.addWidget(self.progress, 1)

        self.time_lbl = QLabel("")
        self.time_lbl.setFont(QFont(FONT_FAMILY, 10))
        self.time_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; border: none;")
        cr.addWidget(self.time_lbl)

        layout.addWidget(self.control)

        # Connect to shared player signals (all items update in sync)
        self._player.player.positionChanged.connect(self._on_pos)
        self._player.player.durationChanged.connect(self._on_dur)
        self._player.player.playbackStateChanged.connect(self._on_state)

        # Expanded answer
        self.answer = QFrame()
        self.answer.setStyleSheet("background: transparent; border: none;")
        self.answer.setVisible(False)
        al = QVBoxLayout(self.answer)
        al.setContentsMargins(4, 4, 4, 4)
        al.setSpacing(3)
        if exercise.target:
            t = exercise.target
            if exercise.phonetic:
                t += f"  {exercise.phonetic}"
            tl = QLabel(t)
            tl.setFont(QFont(FONT_FAMILY, 11))
            tl.setStyleSheet(f"color: {TEXT_SECONDARY}; border: none;")
            al.addWidget(tl)
        if exercise.translation:
            tr = QLabel(f"翻译: {exercise.translation}")
            tr.setFont(QFont(FONT_FAMILY, 11))
            tr.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none;")
            al.addWidget(tr)
        if exercise.explanation:
            el = QLabel(f"解析: {exercise.explanation}")
            el.setWordWrap(True)
            el.setFont(QFont(FONT_FAMILY, 11))
            el.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none;")
            al.addWidget(el)
        layout.addWidget(self.answer)

        d = QFrame()
        d.setFixedHeight(1)
        d.setStyleSheet(f"background: {BORDER}; border: none;")
        layout.addWidget(d)

    # ── Path helpers ──
    def _path(self):
        return self.ex.audio_file or ""

    def _is_me(self):
        """Is this item the currently active one?"""
        return ExerciseItem._active is self

    # ── Playback ──
    def _toggle_play(self):
        path = self._path()
        if not path:
            return
        self.play_clicked.emit(self.ex.index)

        # If clicking the already-active item, pause/resume
        if self._is_me():
            st = self._player.player.playbackState()
            from PySide6.QtMultimedia import QMediaPlayer
            if st == QMediaPlayer.PlaybackState.PlayingState:
                self._player.pause()
                self.play_btn.setText("▶")
                return
            elif st == QMediaPlayer.PlaybackState.PausedState:
                self._player.player.play()
                self.play_btn.setText("⏸")
                return

        # Deactivate previous active item
        if ExerciseItem._active is not None:
            ExerciseItem._active._deactivate()

        # Activate this item
        ExerciseItem._active = self
        self._player.play(path)
        self.play_btn.setText("⏸")
        self.time_lbl.setText("加载中...")

    def _deactivate(self):
        """Another item took over — reset UI, keep control bar visible."""
        self.play_btn.setText("▶")
        self.progress.setValue(0)
        self.time_lbl.setText("")

    # ── Signal handlers ──
    def _on_pos(self, pos_ms):
        if self._sliding or not self._is_me():
            return
        dur = self._player.player.duration()
        if dur > 0:
            self.progress.setValue(int(pos_ms * 100 / dur))
            self._update_time(pos_ms, dur)

    def _on_dur(self, dur_ms):
        if not self._is_me():
            return
        self._update_time(self._player.player.position(), dur_ms)

    def _on_state(self, state):
        if not self._is_me():
            return
        from PySide6.QtMultimedia import QMediaPlayer
        if state == QMediaPlayer.PlaybackState.StoppedState:
            self.play_btn.setText("▶")
            self.progress.setValue(0)
            self.time_lbl.setText("")
            ExerciseItem._active = None
        elif state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_btn.setText("⏸")
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.play_btn.setText("▶")

    def _update_time(self, pos, dur):
        p = f"{pos // 60000}:{pos % 60000 // 60:02d}"
        d = f"{dur // 60000}:{dur % 60000 // 60:02d}" if dur > 0 else "0:00"
        self.time_lbl.setText(f"{p} / {d}")

    # ── Seek ──
    def _seek(self):
        self._sliding = False
        if not self._is_me():
            return
        dur = self._player.player.duration()
        if dur > 0:
            self._player.seek(int(self.progress.value() * dur / 100))

    def _scrub(self, pos):
        if not self._is_me():
            return
        dur = self._player.player.duration()
        if dur > 0:
            self._update_time(int(pos * dur / 100), dur)

    # ── Expand ──
    def _toggle(self):
        self._expanded = not self._expanded
        self.answer.setVisible(self._expanded)
        self.expand_btn.setText("收起解析" if self._expanded else "查看解析")

    # ── Context menu ──
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background: {BG_PRIMARY}; border: 1px solid {BORDER};
                border-radius: {RADIUS_MD}px; padding: 4px; }}
            QMenu::item {{ padding: 4px 20px; border-radius: {RADIUS_SM}px;
                color: {TEXT_PRIMARY}; font-size: 11px; }}
            QMenu::item:selected {{ background: {BG_SELECTED}; }}
        """)
        ca = menu.addAction("复制句子")
        a = menu.exec(event.globalPos())
        if a == ca:
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText(self.ex.sentence)
