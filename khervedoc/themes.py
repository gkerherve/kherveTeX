"""Named theme presets — palette colours, tab QSS, editor/status styling.

Each theme is a dict of named colour keys consumed by apply_theme() to
build a QPalette and by the QSS generators to style tabs, the editor
page/desk, and the status bar.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


# ------------------------------------------------------------------ #
# Theme definitions                                                    #
# ------------------------------------------------------------------ #

THEMES: dict[str, dict[str, str]] = {
    "Light": {
        "dark": "0",
        "base":         "#ffffff",
        "surface":      "#f7f7f7",
        "text":         "#1c1c1c",
        "text_muted":   "#666666",
        "accent":       "#1a6dd8",
        "accent2":      "#d96b00",
        "link":         "#1a6dd8",
        "highlight":    "#1a6dd8",
        "highlight_text": "#ffffff",
        "bright_text":  "#ff3333",
        "disabled":     "#9a9a9a",
        "placeholder":  "#888888",
        "alt_base":     "#eef1f5",
        "tab_active":   "#ffffff",
        "tab_inactive": "#e4e4e4",
        "tab_hover":    "#ececec",
        "desk_bg":      "#d0d4d8",
        "page_bg":      "#ffffff",
        "page_border":  "#b8bcc1",
        "status_text":  "#444444",
    },
    "Dark": {
        "dark": "1",
        "base":         "#1e1e1e",
        "surface":      "#2d2d2d",
        "text":         "#d4d4d4",
        "text_muted":   "#858585",
        "accent":       "#4da6ff",
        "accent2":      "#f0a050",
        "link":         "#4da6ff",
        "highlight":    "#4da6ff",
        "highlight_text": "#ffffff",
        "bright_text":  "#ff5555",
        "disabled":     "#606060",
        "placeholder":  "#777777",
        "alt_base":     "#3a3a3a",
        "tab_active":   "#2d2d2d",
        "tab_inactive": "#1e1e1e",
        "tab_hover":    "#383838",
        "desk_bg":      "#1a1a1a",
        "page_bg":      "#2d2d2d",
        "page_border":  "#555555",
        "status_text":  "#aaaaaa",
    },
}

DEFAULT_THEME = "Light"

THEME_NAMES: list[str] = list(THEMES.keys())


def saved_theme(settings) -> str:
    """Light or Dark as last chosen. A preset from before there were only
    these two becomes whichever of them it was closer to."""
    name = settings.value("theme_name", "")
    if name in THEMES:
        return name
    return "Dark" if settings.value("theme_dark", False, type=bool) \
        else DEFAULT_THEME


def is_dark(theme_name: str) -> bool:
    return THEMES.get(theme_name, THEMES["Light"])["dark"] == "1"


# ------------------------------------------------------------------ #
# QPalette builder                                                     #
# ------------------------------------------------------------------ #

def apply_theme(app: QApplication, theme_name: str) -> dict[str, str]:
    """Set the Fusion style + QPalette for the given theme. Returns the
    theme dict so callers can feed it to the QSS generators."""
    app.setStyle("Fusion")
    t = THEMES.get(theme_name, THEMES["Light"])
    pal = QPalette()

    pal.setColor(QPalette.Window,          QColor(t["surface"]))
    pal.setColor(QPalette.WindowText,      QColor(t["text"]))
    pal.setColor(QPalette.Base,            QColor(t["base"]))
    pal.setColor(QPalette.AlternateBase,   QColor(t["alt_base"]))
    pal.setColor(QPalette.ToolTipBase,     QColor(t["surface"]))
    pal.setColor(QPalette.ToolTipText,     QColor(t["text"]))
    pal.setColor(QPalette.Text,            QColor(t["text"]))
    pal.setColor(QPalette.Button,          QColor(t["surface"]))
    pal.setColor(QPalette.ButtonText,      QColor(t["text"]))
    pal.setColor(QPalette.BrightText,      QColor(t["bright_text"]))
    pal.setColor(QPalette.Link,            QColor(t["link"]))
    pal.setColor(QPalette.Highlight,       QColor(t["highlight"]))
    pal.setColor(QPalette.HighlightedText, QColor(t["highlight_text"]))
    pal.setColor(QPalette.PlaceholderText, QColor(t["placeholder"]))

    disabled_color = QColor(t["disabled"])
    pal.setColor(QPalette.Disabled, QPalette.WindowText, disabled_color)
    pal.setColor(QPalette.Disabled, QPalette.Text,       disabled_color)
    pal.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_color)
    pal.setColor(QPalette.Disabled, QPalette.Highlight,  disabled_color)

    app.setPalette(pal)
    app.setStyleSheet(chrome_stylesheet(t))
    return t


def chrome_stylesheet(t: dict[str, str]) -> str:
    """Application-wide styling of the window chrome, after KherveSheet.

    Without it only the palette changed, so menus, toolbars, the status
    bar, docks and buttons kept Qt's bare flat look and the app read as
    a web page rather than a desktop application."""
    bg = t["surface"]
    bg2 = t.get("chrome", t["surface"])
    fg, fg2 = t["text"], t["text_muted"]
    accent = t["accent"]
    border = t.get("border", t["page_border"])
    btn = t.get("button", t["tab_inactive"])
    btn_hover = t.get("button_hover", t["tab_hover"])
    menu_sel = t.get("menu_sel", t["alt_base"])
    base = t["base"]
    return f"""
QMainWindow, QDialog {{ background: {bg}; }}
QMenuBar {{
    background: {bg2}; color: {fg};
    border-bottom: 1px solid {border}; padding: 2px;
}}
QMenuBar::item {{ background: transparent; padding: 3px 8px; }}
QMenuBar::item:selected {{ background: {menu_sel}; border-radius: 3px; }}
QMenu {{ background: {bg2}; color: {fg}; border: 1px solid {border}; }}
QMenu::item {{ padding: 4px 24px 4px 20px; }}
QMenu::item:selected {{ background: {menu_sel}; color: {fg}; }}
QMenu::separator {{ height: 1px; background: {border}; margin: 3px 8px; }}
QToolBar {{
    background: {bg2}; border: none; border-bottom: 1px solid {border};
    padding: 1px; spacing: 1px;
}}
QToolBar::separator {{ background: {border}; width: 1px; margin: 4px 3px; }}
QToolButton {{
    color: {fg}; padding: 1px; margin: 0px; background: transparent;
    border: 1px solid transparent; border-radius: 3px;
}}
QToolButton:hover {{ background: {btn_hover}; }}
QToolButton:pressed, QToolButton:checked {{
    background: {menu_sel}; border: 1px solid {border};
}}
QToolButton::menu-button {{ border: none; background: transparent; width: 14px; }}
QStatusBar {{
    background: {bg2}; color: {fg2}; border-top: 1px solid {border};
}}
QStatusBar::item {{ border: none; }}
QDockWidget {{ color: {fg}; }}
QDockWidget::title {{
    background: {bg2}; padding: 4px 6px; border-bottom: 1px solid {border};
}}
QPushButton {{
    background: {btn}; color: {fg};
    border: 1px solid {border}; padding: 3px 10px; border-radius: 3px;
}}
QPushButton:hover {{ background: {btn_hover}; border-color: {accent}; }}
QPushButton:pressed {{ background: {menu_sel}; }}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background: {base}; color: {fg};
    border: 1px solid {border}; border-radius: 3px; padding: 2px 4px;
}}
QComboBox:hover, QLineEdit:focus {{ border-color: {accent}; }}
QComboBox QAbstractItemView {{
    background: {base}; color: {fg}; selection-background-color: {menu_sel};
    selection-color: {fg};
}}
QListWidget, QTreeWidget, QTableWidget {{
    background: {base}; color: {fg}; border: 1px solid {border};
    alternate-background-color: {t["alt_base"]};
}}
QListWidget::item:selected, QTreeWidget::item:selected {{
    background: {menu_sel}; color: {fg};
}}
QHeaderView::section {{
    background: {bg2}; color: {fg2}; border: 1px solid {border};
    padding: 2px 4px;
}}
QToolTip {{ background: {bg2}; color: {fg}; border: 1px solid {border}; }}
QScrollBar:vertical {{ background: {bg}; width: 12px; margin: 0; }}
QScrollBar:horizontal {{ background: {bg}; height: 12px; margin: 0; }}
QScrollBar::handle {{ background: {border}; border-radius: 4px; min-height: 24px; min-width: 24px; margin: 2px; }}
QScrollBar::handle:hover {{ background: {accent}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}
QSplitter::handle {{ background: {border}; }}
"""


# ------------------------------------------------------------------ #
# QSS generators                                                      #
# ------------------------------------------------------------------ #

def tab_stylesheet(t: dict[str, str]) -> str:
    """Polished tab bar styling with accent-coloured active indicator."""
    return f"""
        QTabWidget::pane {{
            border-top: 2px solid {t["accent"]};
            background: {t["base"]};
        }}
        QTabBar::tab {{
            background: {t["tab_inactive"]};
            color: {t["text_muted"]};
            padding: 7px 20px;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
            margin-right: 2px;
            border: 1px solid transparent;
            border-bottom: none;
        }}
        QTabBar::tab:selected {{
            background: {t["tab_active"]};
            color: {t["text"]};
            border: 1px solid {t["accent"]};
            border-bottom: 2px solid {t["tab_active"]};
            font-weight: bold;
        }}
        QTabBar::tab:hover:!selected {{
            background: {t["tab_hover"]};
            color: {t["text"]};
        }}
    """


def editor_page_stylesheet(t: dict[str, str]) -> str:
    return f"#page {{ background: {t['page_bg']}; border: 1px solid {t['page_border']}; }}"


def editor_desk_stylesheet(t: dict[str, str]) -> str:
    return f"#desk {{ background: {t['desk_bg']}; }}"


def editor_textedit_stylesheet(t: dict[str, str]) -> str:
    return f"QTextEdit {{ background: {t['page_bg']}; color: {t['text']}; border: none; }}"


def latex_view_stylesheet(t: dict[str, str]) -> str:
    return f"QPlainTextEdit {{ background: {t['base']}; color: {t['text']}; }}"


def status_label_stylesheet(t: dict[str, str]) -> str:
    return f"color: {t['status_text']}; padding: 0 6px;"
