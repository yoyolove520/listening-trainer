"""
Stats page — compact fonts, dashed cards. Handles empty data states.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from app.theme import *
from app.services.stats_service import StatsService

MARGIN = 28


def sec_card(title, layout):
    card = QFrame()
    card.setObjectName("dc")
    card.setStyleSheet(f"QFrame#dc {{ background: transparent; border: 1px dashed {BORDER_DASH}; border-radius: 4px; }}")
    cl = QVBoxLayout(card)
    cl.setContentsMargins(14, 10, 14, 10)
    cl.setSpacing(10)
    tl = QLabel(title)
    tl.setFont(QFont(FONT_FAMILY, 11, QFont.DemiBold))
    tl.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none;")
    cl.addWidget(tl)
    layout.addWidget(card)
    return cl


def empty_label(text):
    """Create a centered empty-state label."""
    el = QLabel(text)
    el.setAlignment(Qt.AlignCenter)
    el.setFont(QFont(FONT_FAMILY, 11))
    el.setStyleSheet(f"color: {TEXT_PLACEHOLDER}; border: none; padding: 20px;")
    return el


class StatCard(QFrame):
    def __init__(self, title, value, subtitle=""):
        super().__init__()
        self.setObjectName("dc")
        self.setStyleSheet(f"QFrame#dc {{ background: transparent; border: 1px dashed {BORDER_DASH}; border-radius: 4px; }}")
        l = QVBoxLayout(self)
        l.setContentsMargins(14, 10, 14, 10)
        l.setSpacing(2)
        tl = QLabel(title)
        tl.setFont(QFont(FONT_FAMILY, 10))
        tl.setStyleSheet(f"color: {TEXT_SECONDARY}; border: none;")
        l.addWidget(tl)
        vl = QLabel(value)
        vl.setFont(QFont(FONT_FAMILY, 28, QFont.DemiBold))
        vl.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none;")
        l.addWidget(vl)
        if subtitle:
            sl = QLabel(subtitle)
            sl.setFont(QFont(FONT_FAMILY, 10))
            sl.setStyleSheet(f"color: {TEXT_SECONDARY}; border: none;")
            l.addWidget(sl)


class WeaknessCard(QFrame):
    """Single weakness type stat card — compact, no overlap."""

    def __init__(self, label, count, ratio):
        super().__init__()
        self.setObjectName("wc")
        self.setStyleSheet(f"""
            QFrame#wc {{
                background: transparent;
                border: 1px dashed {BORDER_DASH};
                border-radius: 4px;
            }}
        """)
        l = QVBoxLayout(self)
        l.setContentsMargins(10, 10, 10, 10)
        l.setSpacing(8)
        l.setAlignment(Qt.AlignCenter)

        lb = QLabel(label)
        lb.setFont(QFont(FONT_FAMILY, 11))
        lb.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none;")
        lb.setAlignment(Qt.AlignCenter)
        l.addWidget(lb)

        vl = QLabel(str(count))
        vl.setFont(QFont(FONT_FAMILY, 28, QFont.DemiBold))
        vl.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none;")
        vl.setAlignment(Qt.AlignCenter)
        l.addWidget(vl)

        # Proportional bar
        bar = QFrame()
        bar.setFixedHeight(4)
        bw = max(int(ratio * 80), 16)
        bar.setFixedWidth(bw)
        bar.setStyleSheet(f"background: {TEXT_PRIMARY}; border: none; border-radius: 2px;")
        bc = QHBoxLayout()
        bc.setContentsMargins(0, 0, 0, 0)
        bc.addWidget(bar, 0, Qt.AlignCenter)
        l.addLayout(bc)


class LevelBarChart(QFrame):
    """Horizontal bar chart for level distribution — responsive width."""

    def __init__(self, data):
        super().__init__()
        self.setStyleSheet("background: transparent; border: none;")
        l = QVBoxLayout(self)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(6)
        mv = max((d[1] for d in data), default=1) or 1
        for item in data:
            label, value = item[0], item[1]
            r = QHBoxLayout()
            r.setSpacing(8)
            lb = QLabel(label)
            lb.setFixedWidth(48)
            lb.setFont(QFont(FONT_FAMILY, 11))
            lb.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none;")
            r.addWidget(lb)
            bw = max(int((value / mv) * 160), 22)
            bar = QFrame()
            bar.setFixedHeight(20)
            bar.setMinimumWidth(bw)
            r.addWidget(bar, 1)
            bar.setStyleSheet(f"background: {TEXT_PRIMARY}; border: none; border-radius: 4px;")
            bl = QHBoxLayout(bar)
            bl.setContentsMargins(6, 0, 6, 0)
            vl = QLabel(str(value))
            vl.setFont(QFont(FONT_FAMILY, 10, QFont.DemiBold))
            vl.setStyleSheet("color: white; border: none;")
            bl.addWidget(vl)
            bl.addStretch()
            r.addStretch()
            l.addLayout(r)


class StatsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background: {BG_PRIMARY};")
        self._service = StatsService()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(MARGIN, MARGIN, MARGIN, MARGIN)
        layout.setSpacing(12)

        ov = self._service.get_overview()
        cr = QHBoxLayout()
        cr.setSpacing(10)
        for title, value, sub in [("总练习次数", str(ov.total_practices), "累计"), ("学生总数", str(ov.total_students), "人"), ("存档数量", str(ov.total_archives), "个")]:
            cr.addWidget(StatCard(title, value, sub))
        layout.addLayout(cr)

        # ── Level distribution ──
        lc = sec_card("考试类型分布", layout)
        ls = self._service.get_by_level()
        if ls:
            lc.addWidget(LevelBarChart([(ls2.level, ls2.count) for ls2 in ls]))
        else:
            lc.addWidget(empty_label("暂无练习记录"))

        # ── Weakness distribution ──
        wc = sec_card("薄弱类型分布", layout)
        ws = self._service.get_by_weakness()
        if ws:
            max_w = max((w.count for w in ws), default=1) or 1
            wrow = QHBoxLayout()
            wrow.setSpacing(8)
            wrow.setContentsMargins(0, 0, 0, 0)
            for w in ws:
                wrow.addWidget(WeaknessCard(w.label, w.count, w.count / max_w if max_w else 0), 1)
            wc.addLayout(wrow)
        else:
            wc.addWidget(empty_label("暂无练习记录"))

        # ── Recent trend ──
        tc = sec_card("近期趋势", layout)
        td = self._service.get_trend()
        if td:
            ttext = "  .  ".join(f"{d.date}: {d.count}次" for d in td)
            tl = QLabel(ttext)
            tl.setFont(QFont(FONT_FAMILY, 11))
            tl.setWordWrap(True)
            tl.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none;")
            tc.addWidget(tl)
            mc = max((d.count for d in td), default=1) or 1
            sw = QWidget()
            sw.setStyleSheet("border: none;")
            sr = QHBoxLayout(sw)
            sr.setContentsMargins(0, 0, 0, 0)
            sr.setSpacing(2)
            sr.setAlignment(Qt.AlignLeft)
            for d in td:
                bh = max(3, int((d.count / mc) * 40))
                b = QFrame()
                b.setFixedSize(10, bh)
                b.setStyleSheet(f"background: {TEXT_PRIMARY}; border: none; border-radius: 2px;")
                sr.addWidget(b)
            sr.addStretch()
            tc.addWidget(sw)
        else:
            tc.addWidget(empty_label("暂无数据"))

        layout.addStretch()
        scroll.setWidget(inner)
        pl = QVBoxLayout(self)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.addWidget(scroll)
