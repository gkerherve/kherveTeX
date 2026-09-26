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
    "Solarized Light": {
        "dark": "0",
        "base":         "#fdf6e3",
        "surface":      "#eee8d5",
        "text":         "#657b83",
        "text_muted":   "#93a1a1",
        "accent":       "#268bd2",
        "accent2":      "#cb4b16",
        "link":         "#268bd2",
        "highlight":    "#268bd2",
        "highlight_text": "#fdf6e3",
        "bright_text":  "#dc322f",
        "disabled":     "#93a1a1",
        "placeholder":  "#93a1a1",
        "alt_base":     "#eee8d5",
        "tab_active":   "#fdf6e3",
        "tab_inactive": "#e8e1ce",
        "tab_hover":    "#f0e9d5",
        "desk_bg":      "#d5cdb8",
        "page_bg":      "#fdf6e3",
        "page_border":  "#c9c1a8",
        "status_text":  "#657b83",
    },
    "Sepia": {
        "dark": "0",
        "base":         "#f5efe0",
        "surface":      "#ebe4d3",
        "text":         "#5b4636",
        "text_muted":   "#8a7560",
        "accent":       "#8b5e3c",
        "accent2":      "#b07038",
        "link":         "#7a5025",
        "highlight":    "#8b5e3c",
        "highlight_text": "#f5efe0",
        "bright_text":  "#c0392b",
        "disabled":     "#b0a08a",
        "placeholder":  "#a09080",
        "alt_base":     "#e8e0d0",
        "tab_active":   "#f5efe0",
        "tab_inactive": "#e0d7c6",
        "tab_hover":    "#ebe2d0",
        "desk_bg":      "#cdc4b2",
        "page_bg":      "#f5efe0",
        "page_border":  "#c5b9a5",
        "status_text":  "#6b5646",
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
    "Nord": {
        "dark": "1",
        "base":         "#2e3440",
        "surface":      "#3b4252",
        "text":         "#d8dee9",
        "text_muted":   "#7b88a1",
        "accent":       "#88c0d0",
        "accent2":      "#ebcb8b",
        "link":         "#88c0d0",
        "highlight":    "#88c0d0",
        "highlight_text": "#2e3440",
        "bright_text":  "#bf616a",
        "disabled":     "#616e88",
        "placeholder":  "#616e88",
        "alt_base":     "#434c5e",
        "tab_active":   "#3b4252",
        "tab_inactive": "#2e3440",
        "tab_hover":    "#434c5e",
        "desk_bg":      "#242933",
        "page_bg":      "#3b4252",
        "page_border":  "#4c566a",
        "status_text":  "#a0aec0",
    },
    "Dracula": {
        "dark": "1",
        "base":         "#282a36",
        "surface":      "#44475a",
        "text":         "#f8f8f2",
        "text_muted":   "#8a8d9e",
        "accent":       "#bd93f9",
        "accent2":      "#ffb86c",
        "link":         "#8be9fd",
        "highlight":    "#bd93f9",
        "highlight_text": "#282a36",
        "bright_text":  "#ff5555",
        "disabled":     "#6272a4",
        "placeholder":  "#6272a4",
        "alt_base":     "#383a4a",
        "tab_active":   "#44475a",
        "tab_inactive": "#282a36",
        "tab_hover":    "#383a4a",
        "desk_bg":      "#1e1f29",
        "page_bg":      "#44475a",
        "page_border":  "#6272a4",
        "status_text":  "#bfc0cc",
    },
    "Gruvbox Light": {
        "dark": "0",
        "base":         "#fbf1c7",
        "surface":      "#ebdbb2",
        "text":         "#3c3836",
        "text_muted":   "#7c6f64",
        "accent":       "#458588",
        "accent2":      "#d65d0e",
        "link":         "#458588",
        "highlight":    "#458588",
        "highlight_text": "#fbf1c7",
        "bright_text":  "#cc241d",
        "disabled":     "#a89984",
        "placeholder":  "#928374",
        "alt_base":     "#f2e5bc",
        "tab_active":   "#fbf1c7",
        "tab_inactive": "#e8d8a8",
        "tab_hover":    "#f0e4b8",
        "desk_bg":      "#d5c4a1",
        "page_bg":      "#fbf1c7",
        "page_border":  "#bdae93",
        "status_text":  "#504945",
    },
    "Gruvbox Dark": {
        "dark": "1",
        "base":         "#282828",
        "surface":      "#3c3836",
        "text":         "#ebdbb2",
        "text_muted":   "#a89984",
        "accent":       "#83a598",
        "accent2":      "#fe8019",
        "link":         "#83a598",
        "highlight":    "#83a598",
        "highlight_text": "#282828",
        "bright_text":  "#fb4934",
        "disabled":     "#665c54",
        "placeholder":  "#7c6f64",
        "alt_base":     "#3c3836",
        "tab_active":   "#3c3836",
        "tab_inactive": "#282828",
        "tab_hover":    "#504945",
        "desk_bg":      "#1d2021",
        "page_bg":      "#3c3836",
        "page_border":  "#504945",
        "status_text":  "#bdae93",
    },
    "Monokai": {
        "dark": "1",
        "base":         "#272822",
        "surface":      "#3e3d32",
        "text":         "#f8f8f2",
        "text_muted":   "#90908a",
        "accent":       "#66d9ef",
        "accent2":      "#fd971f",
        "link":         "#66d9ef",
        "highlight":    "#49483e",
        "highlight_text": "#f8f8f2",
        "bright_text":  "#f92672",
        "disabled":     "#75715e",
        "placeholder":  "#75715e",
        "alt_base":     "#3e3d32",
        "tab_active":   "#3e3d32",
        "tab_inactive": "#272822",
        "tab_hover":    "#49483e",
        "desk_bg":      "#1e1f1c",
        "page_bg":      "#3e3d32",
        "page_border":  "#575747",
        "status_text":  "#a6e22e",
    },
    "One Dark": {
        "dark": "1",
        "base":         "#282c34",
        "surface":      "#2c313a",
        "text":         "#abb2bf",
        "text_muted":   "#636d83",
        "accent":       "#61afef",
        "accent2":      "#e5c07b",
        "link":         "#61afef",
        "highlight":    "#61afef",
        "highlight_text": "#282c34",
        "bright_text":  "#e06c75",
        "disabled":     "#5c6370",
        "placeholder":  "#5c6370",
        "alt_base":     "#2c313a",
        "tab_active":   "#2c313a",
        "tab_inactive": "#282c34",
        "tab_hover":    "#353b45",
        "desk_bg":      "#21252b",
        "page_bg":      "#2c313a",
        "page_border":  "#3e4451",
        "status_text":  "#9da5b4",
    },
    "GitHub Light": {
        "dark": "0",
        "base":         "#ffffff",
        "surface":      "#f6f8fa",
        "text":         "#24292f",
        "text_muted":   "#656d76",
        "accent":       "#0969da",
        "accent2":      "#cf222e",
        "link":         "#0969da",
        "highlight":    "#0969da",
        "highlight_text": "#ffffff",
        "bright_text":  "#cf222e",
        "disabled":     "#8c959f",
        "placeholder":  "#8c959f",
        "alt_base":     "#f6f8fa",
        "tab_active":   "#ffffff",
        "tab_inactive": "#eaeef2",
        "tab_hover":    "#f0f3f6",
        "desk_bg":      "#d0d7de",
        "page_bg":      "#ffffff",
        "page_border":  "#d0d7de",
        "status_text":  "#424a53",
    },
    "Catppuccin Mocha": {
        "dark": "1",
        "base":         "#1e1e2e",
        "surface":      "#313244",
        "text":         "#cdd6f4",
        "text_muted":   "#6c7086",
        "accent":       "#89b4fa",
        "accent2":      "#fab387",
        "link":         "#89dceb",
        "highlight":    "#89b4fa",
        "highlight_text": "#1e1e2e",
        "bright_text":  "#f38ba8",
        "disabled":     "#585b70",
        "placeholder":  "#585b70",
        "alt_base":     "#313244",
        "tab_active":   "#313244",
        "tab_inactive": "#1e1e2e",
        "tab_hover":    "#45475a",
        "desk_bg":      "#181825",
        "page_bg":      "#313244",
        "page_border":  "#45475a",
        "status_text":  "#a6adc8",
    },
    "Catppuccin Latte": {
        "dark": "0",
        "base":         "#eff1f5",
        "surface":      "#e6e9ef",
        "text":         "#4c4f69",
        "text_muted":   "#8c8fa1",
        "accent":       "#1e66f5",
        "accent2":      "#fe640b",
        "link":         "#1e66f5",
        "highlight":    "#1e66f5",
        "highlight_text": "#eff1f5",
        "bright_text":  "#d20f39",
        "disabled":     "#9ca0b0",
        "placeholder":  "#9ca0b0",
        "alt_base":     "#e6e9ef",
        "tab_active":   "#eff1f5",
        "tab_inactive": "#dce0e8",
        "tab_hover":    "#e6e9ef",
        "desk_bg":      "#ccd0da",
        "page_bg":      "#eff1f5",
        "page_border":  "#bcc0cc",
        "status_text":  "#5c5f77",
    },
}

def _tinted(bg, bg2, fg, fg2, accent, border, btn, btn_hover, menu_sel,
            link, desk, dark=False) -> dict[str, str]:
    """A theme in the Kherve family style (as in KherveSheet): the chrome
    — menus, toolbars, tabs, status bar — carries the tint, while the
    document itself stays on white paper."""
    return {
        "dark": "1" if dark else "0",
        "base": "#1e1e22" if dark else "#ffffff",
        "surface": bg, "chrome": bg2,
        "text": fg, "text_muted": fg2,
        "accent": accent, "accent2": accent, "link": link,
        "highlight": accent, "highlight_text": "#ffffff",
        "bright_text": "#ff3333", "disabled": fg2, "placeholder": fg2,
        "alt_base": btn if dark else "#f6f6f8",
        "tab_active": bg, "tab_inactive": btn, "tab_hover": btn_hover,
        "border": border, "button": btn, "button_hover": btn_hover,
        "menu_sel": menu_sel,
        "desk_bg": desk, "page_bg": "#ffffff", "page_border": border,
        "status_text": fg2,
    }


# The Kherve family themes, shared with KherveSheet. "Word Blue" is the
# default: KherveSheet is green like a spreadsheet, kherveDOC blue like
# a word processor.
THEMES.update({
    "Word Blue": _tinted(
        "#eef3fa", "#dce8f7", "#10233a", "#44607e", "#1f63c6",
        "#aac4e6", "#e6eef9", "#cfe0f5", "#c4d9f3", "#1a55b0", "#c9d3df"),
    "Emerald": _tinted(
        "#eef7f1", "#d4f0df", "#0d2a1d", "#2e5a44", "#0a9d5b",
        "#a8dcbd", "#e2f3ea", "#bfe9cf", "#bfe9cf", "#0a7d49", "#cbd8d0"),
    "Arctic": _tinted(
        "#f0f5fa", "#ffffff", "#1a2a3a", "#5a6a7a", "#2a8ad0",
        "#c8d4e0", "#f5f8fc", "#dce8f4", "#bcd4f0", "#1a6fbb", "#cfd6de"),
    "Sky": _tinted(
        "#f0f8ff", "#f8fcff", "#1a2838", "#5a6878", "#3090d0",
        "#c0d8f0", "#f4faff", "#d4e8fa", "#b8d8f4", "#2070b0", "#cdd6e0"),
    "Seafoam": _tinted(
        "#ecf7f3", "#d2f0e8", "#0e2e28", "#36605a", "#16a98a",
        "#a8ddd0", "#dff3ee", "#bce8de", "#bce8de", "#0e8a70", "#c9d8d4"),
    "Teal": _tinted(
        "#ecf6f7", "#d2eeef", "#0e2a2e", "#365e62", "#179a9a",
        "#a8dadc", "#def2f3", "#bce6e8", "#bce6e8", "#0e7d7d", "#c8d7d8"),
    "Lavender": _tinted(
        "#f4f0fa", "#faf8ff", "#2a1a3a", "#6a5a7a", "#7a50b0",
        "#d0c0e0", "#f6f2fa", "#e4d8f0", "#d0c0e4", "#6a40a0", "#d4cfdc"),
    "Rose": _tinted(
        "#faf0f3", "#fff8fa", "#3a1a22", "#7a5a62", "#c0506a",
        "#e0c0ca", "#fcf2f5", "#f4d8e0", "#e8bcc8", "#a83050", "#dccfd3"),
    "Sand": _tinted(
        "#f8f4ee", "#fffcf5", "#38301a", "#7a7060", "#b89040",
        "#dcd0b8", "#faf6ee", "#f0e0c8", "#e0ccaa", "#987020", "#d9d3c8"),
    "Charcoal": _tinted(
        "#222226", "#2c2c32", "#d8d8dc", "#909098", "#5898d0",
        "#3c3c44", "#343438", "#40404a", "#3a6090", "#70b0e8", "#18181b",
        dark=True),
    "Midnight": _tinted(
        "#0e1420", "#141c2a", "#c8d0e0", "#8090a8", "#4488cc",
        "#202838", "#1c2838", "#283850", "#2a5588", "#5ea0e0", "#0a0e16",
        dark=True),
})

DEFAULT_THEME = "Word Blue"

THEME_NAMES: list[str] = list(THEMES.keys())


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
