"""
Theme — Ultra-flat black-on-white. No backgrounds, no gray cards.
Pure content, clean borders, black text.
"""
BG_PRIMARY = "#FFFFFF"        # Pure white page
BG_HOVER = "#F8F8F8"          # Subtle hover, barely visible
BG_SELECTED = "#F5F5F5"       # Very light selected state

TEXT_PRIMARY = "#000000"      # Pure black
TEXT_SECONDARY = "#888888"    # Muted secondary
TEXT_PLACEHOLDER = "#BBBBBB"  # Light placeholder
TEXT_WHITE = "#FFFFFF"

BORDER = "#E8E8E8"            # Thin light border
BORDER_ACTIVE = "#000000"     # Black active indicator
BORDER_DASH = "#333333"       # Dashed card border
BORDER_HOVER = "#CCCCCC"

LEVEL_COLORS = {
    "KET": {"fg": "#000000"},
    "PET": {"fg": "#000000"},
    "中考": {"fg": "#000000"},
    "高考": {"fg": "#000000"},
    "雅思": {"fg": "#000000"},
}

WEAKNESS_LABELS = {
    "pronunciation": "单词发音",
    "collocation": "固定搭配",
    "structure": "句式结构",
    "implicature": "言外之意",
}

FONT_FAMILY = "PingFang SC, Microsoft YaHei UI, Microsoft YaHei, sans-serif"
FONT_ENGLISH = "SF Pro Display, Segoe UI Variable, Segoe UI, Helvetica Neue, Arial"

RADIUS_SM = 4
RADIUS_MD = 6
RADIUS_LG = 8
RADIUS_XL = 12
RADIUS_PILL = 999

SIDEBAR_COLLAPSED = 32
SIDEBAR_EXPANDED = 140

BTN_HEIGHT = 26
INPUT_HEIGHT = 26
