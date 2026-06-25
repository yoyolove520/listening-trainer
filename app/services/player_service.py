"""
Audio player — minimal wrapper. No signal forwarding, no complex state.
"""
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl, QObject
import os


class AudioPlayer(QObject):
    """Minimal shared player."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.player = QMediaPlayer()
        self.audio = QAudioOutput()
        self.player.setAudioOutput(self.audio)
        self._source = ""
        self._speed = 1.0

    @property
    def current_source(self):
        return self._source

    def play(self, filepath):
        norm = os.path.normpath(filepath)
        if self._source == norm:
            self.player.play()
            return
        self._source = norm
        self.player.setSource(QUrl.fromLocalFile(norm))
        self.player.setPlaybackRate(self._speed)
        self.player.play()

    def pause(self):
        self.player.pause()

    def stop(self):
        self.player.stop()
        self._source = ""

    def set_speed(self, s):
        self._speed = s
        self.player.setPlaybackRate(s)

    def seek(self, pos):
        self.player.setPosition(pos)
