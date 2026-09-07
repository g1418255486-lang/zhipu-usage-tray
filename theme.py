from PySide6.QtGui import QColor

# ─── terminal HUD design tokens ───

# accent terminal green
PRIMARY = "#00e676"
PRIMARY_ACTIVE = "#00c853"

# text (green-tinted grays)
TEXT_HEADING = "#e8f5ec"
TEXT_BODY = "#9fb5a6"
TEXT_SECONDARY = "#5f7268"
TEXT_MUTED = "#435350"

# surfaces (softened dark)
BG = "#151d19"
BG_CARD = "#1c2621"

# borders
BORDER_WARM = "#2a3730"
BORDER_LIGHT = "#2a3730"
BORDER_STRONG = "#35453c"

# status (bright for dark bg)
SUCCESS = "#00e676"
WARNING = "#ffb300"
ERROR = "#ff5252"

# corner radius (sharp, technical)
RADIUS = 6

# fonts
FONT_FAMILY = "Segoe UI Variable Text, Microsoft YaHei UI, Segoe UI, Microsoft YaHei"
MONO_FAMILY = "Cascadia Mono, JetBrains Mono, Consolas, Courier New"


def qss_font(size: int, weight: int = 400) -> str:
    return f'font-family:"{FONT_FAMILY}";font-size:{size}px;font-weight:{weight};'


def qss_mono(size: int, weight: int = 400) -> str:
    return f'font-family:"{MONO_FAMILY}";font-size:{size}px;font-weight:{weight};'


def _make_font(family_list: str, pixel: int, weight, spacing: int = 0):
    from PySide6.QtGui import QFont, QFontDatabase
    f = QFont()
    installed = QFontDatabase.families()
    families = [n for n in family_list.split(",") if n in installed]
    f.setFamilies(families + ["Consolas", "Segoe UI", "Microsoft YaHei UI"])
    f.setPixelSize(pixel)
    try:
        f.setWeight(QFont.Weight(weight))
    except Exception:
        f.setWeight(QFont.Weight.Normal)
    if spacing:
        f.setLetterSpacing(QFont.SpacingType.PercentageSpacing, spacing)
    return f


def ui_font(pixel: int, weight=400, spacing: int = 0):
    """Sans UI font. spacing: percentage letter-spacing (e.g. 120)."""
    return _make_font(FONT_FAMILY, pixel, weight, spacing)


def mono_font(pixel: int, weight=400, spacing: int = 0):
    """Monospace font for numbers/technical labels."""
    return _make_font(MONO_FAMILY, pixel, weight, spacing)


def bar_color(pct: float) -> QColor:
    if pct >= 75:
        return QColor(ERROR)
    elif pct >= 50:
        return QColor(WARNING)
    elif pct >= 25:
        return QColor(PRIMARY)
    return QColor(SUCCESS)
