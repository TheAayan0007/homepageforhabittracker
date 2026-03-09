"""
◈ HABITTRACK — Python Edition
Exact replica of the HTML Daily Habit & Task Tracker
Requires: pip install PyQt6
Data is stored in trackerdata.json in the same directory as this script.
"""

import sys
import os
import json
import time
import math
from datetime import datetime, date, timedelta
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QScrollArea, QFrame, QGridLayout,
    QDialog, QFileDialog, QSizePolicy, QStackedWidget, QCheckBox,
    QSpacerItem, QToolButton, QInputDialog, QMessageBox, QSplitter,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QTextEdit, QSpinBox, QComboBox
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect,
    QThread, pyqtSignal, QSize, QPoint, QEvent
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QPainter, QPen, QBrush,
    QLinearGradient, QRadialGradient, QFontDatabase, QIcon,
    QPixmap, QPainterPath, QConicalGradient
)

# ─────────────────────────────────────────────
# CONSTANTS / THEME
# ─────────────────────────────────────────────
DATA_FILE = Path(__file__).parent / "trackerdata.json"

C = {
    "bg":        "#0c0e14",
    "surface":   "#13151f",
    "surface2":  "#1a1d2b",
    "surface3":  "#222537",
    "border":    "#2a2e46",
    "green":     "#4ade80",
    "green2":    "#22c55e",
    "green_bg":  "#0a1f14",
    "green_dim": "#166534",
    "text":      "#e2e5f0",
    "text_dim":  "#7c82a0",
    "text_faint":"#3c4060",
    "red":       "#f87171",
}

STYLESHEET = f"""
QMainWindow, QWidget {{
    background: {C['bg']};
    color: {C['text']};
    font-family: 'Rajdhani', 'Segoe UI', sans-serif;
}}
QScrollArea {{ border: none; background: {C['bg']}; }}
QScrollBar:vertical {{
    background: {C['bg']}; width: 6px; border: none;
}}
QScrollBar::handle:vertical {{
    background: {C['surface3']}; border-radius: 3px; min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
QScrollBar:horizontal {{
    background: {C['bg']}; height: 6px; border: none;
}}
QScrollBar::handle:horizontal {{
    background: {C['surface3']}; border-radius: 3px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}
QLineEdit, QSpinBox {{
    background: {C['surface2']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    color: {C['text']};
    padding: 7px 11px;
    font-size: 13px;
    font-family: 'Rajdhani', 'Segoe UI', sans-serif;
}}
QLineEdit:focus, QSpinBox:focus {{
    border-color: {C['green']};
}}
QSpinBox::up-button, QSpinBox::down-button {{ width: 0px; }}
QLabel {{ background: transparent; color: {C['text']}; }}
QToolTip {{
    background: {C['surface2']};
    color: {C['text']};
    border: 1px solid {C['border']};
    border-radius: 4px;
    padding: 4px 8px;
}}
"""

def qc(hex_color):
    return QColor(hex_color)

def btn_style(bg=None, color=None, border=None, hover_bg=None, hover_color=None, radius=6, pad="6px 14px", font_size=13, bold=False):
    bg = bg or C['surface2']
    color = color or C['text']
    border = border or C['border']
    hover_bg = hover_bg or C['surface3']
    hover_color = hover_color or C['green']
    weight = "700" if bold else "600"
    return f"""
        QPushButton {{
            background: {bg};
            color: {color};
            border: 1px solid {border};
            border-radius: {radius}px;
            padding: {pad};
            font-size: {font_size}px;
            font-weight: {weight};
            font-family: 'Rajdhani', 'Segoe UI', sans-serif;
        }}
        QPushButton:hover {{
            background: {hover_bg};
            color: {hover_color};
            border-color: {hover_color};
        }}
        QPushButton:pressed {{
            background: {hover_bg};
        }}
    """

GREEN_BTN = btn_style(
    bg=C['green_bg'], color=C['green'], border=C['green2'],
    hover_bg=C['green'], hover_color='#000'
)
PRIMARY_BTN = btn_style(
    bg=C['green'], color='#000', border=C['green'],
    hover_bg=C['green2'], hover_color='#000'
)
DANGER_BTN = btn_style(
    bg=C['surface2'], color=C['text_dim'], border=C['border'],
    hover_bg='#2a1010', hover_color=C['red']
)

# ─────────────────────────────────────────────
# DATA LAYER
# ─────────────────────────────────────────────
class DataStore:
    def __init__(self):
        today = date.today()
        self.habits = [
            {"id": "h1", "name": "Wake up at 05:00", "icon": "⏰"},
            {"id": "h2", "name": "Gym",               "icon": "💪"},
            {"id": "h3", "name": "Reading / Learning","icon": "📚"},
            {"id": "h4", "name": "Budget Tracking",   "icon": "💰"},
            {"id": "h5", "name": "Project Work",      "icon": "💻"},
            {"id": "h6", "name": "No Alcohol",        "icon": "🚫"},
            {"id": "h7", "name": "Social Media Detox","icon": "📵"},
            {"id": "h8", "name": "Goal Journaling",   "icon": "📓"},
            {"id": "h9", "name": "Cold Shower",       "icon": "🚿"},
        ]
        self.completions = {}   # "YYYY-MM-DD" -> [habit_id, ...]
        self.tasks = {}         # "YYYY-MM-DD" -> [{id, text, done}, ...]
        self.vm = today.month
        self.vy = today.year
        self.load()

    def dk(self, y, m, d):
        return f"{y}-{m:02d}-{d:02d}"

    def is_checked(self, y, m, d, hid):
        return hid in self.completions.get(self.dk(y, m, d), [])

    def toggle(self, y, m, d, hid):
        k = self.dk(y, m, d)
        lst = self.completions.setdefault(k, [])
        if hid in lst:
            lst.remove(hid)
        else:
            lst.append(hid)
        self.save()

    def save(self, path=None):
        path = path or DATA_FILE
        payload = {
            "habits": self.habits,
            "completions": self.completions,
            "tasks": self.tasks,
            "vm": self.vm,
            "vy": self.vy,
            "_saved": datetime.now().isoformat(),
            "_version": "1.0"
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    def load(self, path=None):
        path = path or DATA_FILE
        if not os.path.exists(path):
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                p = json.load(f)
            if "habits"      in p: self.habits      = p["habits"]
            if "completions" in p: self.completions  = p["completions"]
            if "tasks"       in p: self.tasks        = p["tasks"]
            if "vm"          in p: self.vm           = p["vm"]
            if "vy"          in p: self.vy           = p["vy"]
            return True
        except Exception as e:
            print(f"Load error: {e}")
            return False

    def days_in_month(self, y, m):
        import calendar
        return calendar.monthrange(y, m)[1]

    def first_day(self, y, m):
        return date(y, m, 1).weekday()  # Mon=0 … Sun=6  (convert to Sun=0 below)

    def first_day_sun(self, y, m):
        # returns 0=Sun … 6=Sat
        return (date(y, m, 1).weekday() + 1) % 7

    def month_stats(self):
        y, m = self.vy, self.vm
        days = self.days_in_month(y, m)
        today = date.today()
        total = 0; checked = 0
        for d in range(1, days + 1):
            dt = date(y, m, d)
            if dt > today:
                break
            total += len(self.habits)
            checked += len(self.completions.get(self.dk(y, m, d), []))
        pct = round(checked / total * 100) if total else 0
        return {"habits": len(self.habits), "checked": checked, "pct": pct, "total": total}

D = DataStore()

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
MONTH_NAMES = ["January","February","March","April","May","June",
               "July","August","September","October","November","December"]
DAY_NAMES   = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]
DAY_SHORT   = ["Su","Mo","Tu","We","Th","Fr","Sa"]

def label(text, size=13, color=None, bold=False, mono=False):
    lbl = QLabel(text)
    color = color or C['text']
    family = "'IBM Plex Mono', 'Courier New', monospace" if mono else "'Rajdhani', 'Segoe UI', sans-serif"
    weight = "700" if bold else "500"
    lbl.setStyleSheet(f"color:{color};font-size:{size}px;font-weight:{weight};font-family:{family};background:transparent;")
    return lbl

def separator():
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet(f"background:{C['border']};border:none;max-height:1px;")
    return line

# ─────────────────────────────────────────────
# CUSTOM PAINTING — Donut / Ring Widget
# ─────────────────────────────────────────────
class DonutWidget(QWidget):
    def __init__(self, size=80, stroke=7, parent=None):
        super().__init__(parent)
        self._size = size
        self._stroke = stroke
        self._pct = 0.0
        self.setFixedSize(size, size)

    def set_pct(self, pct):
        self._pct = max(0.0, min(1.0, pct))
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self._size / 2
        s = self._stroke
        margin = s / 2 + 2
        rect = QRect(int(margin), int(margin),
                     int(self._size - 2 * margin), int(self._size - 2 * margin))
        # background ring
        pen = QPen(qc(C['surface3']), s)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawEllipse(rect)
        # filled arc
        if self._pct > 0:
            pen2 = QPen(qc(C['green']), s)
            pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen2)
            span = int(-self._pct * 360 * 16)
            p.drawArc(rect, 90 * 16, span)
        # center text
        pct_int = int(self._pct * 100)
        p.setPen(QPen(qc(C['green'] if self._pct >= 1.0 else C['text']), 1))
        font = QFont("IBM Plex Mono", int(self._size * 0.17))
        font.setBold(True)
        p.setFont(font)
        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{pct_int}%")
        p.end()


class BigRingWidget(QWidget):
    """Countdown ring for timer overlay."""
    def __init__(self, size=140, parent=None):
        super().__init__(parent)
        self._size = size
        self._pct = 1.0
        self._time_str = "00:00"
        self.setFixedSize(size, size)

    def set_state(self, pct, time_str):
        self._pct = pct
        self._time_str = time_str
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = 9
        margin = s / 2 + 3
        rect = QRect(int(margin), int(margin),
                     int(self._size - 2 * margin), int(self._size - 2 * margin))
        pen = QPen(qc(C['surface3']), s)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawEllipse(rect)
        if self._pct > 0:
            pen2 = QPen(qc(C['green']), s)
            pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen2)
            p.drawArc(rect, 90 * 16, int(-self._pct * 360 * 16))
        p.setPen(QPen(qc(C['green']), 1))
        font = QFont("IBM Plex Mono", 22)
        font.setBold(True)
        p.setFont(font)
        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._time_str)
        p.end()

# ─────────────────────────────────────────────
# CARD WIDGETS
# ─────────────────────────────────────────────
class Card(QFrame):
    def __init__(self, parent=None, radius=10, bg=None, border=None):
        super().__init__(parent)
        bg = bg or C['surface']
        border = border or C['border']
        self.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: 1px solid {border};
                border-radius: {radius}px;
            }}
            QLabel {{ background: transparent; border: none; }}
        """)

# ─────────────────────────────────────────────
# WELCOME SCREEN
# ─────────────────────────────────────────────
class WelcomeScreen(QWidget):
    enter_app = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background:{C['bg']};")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(28)
        layout.setContentsMargins(40, 40, 40, 40)

        title = QLabel("◈ DAILY HABIT TRACKER")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"""
            color: {C['green']};
            font-size: 38px; font-weight: 700;
            font-family: 'IBM Plex Mono','Courier New',monospace;
            letter-spacing: -1px;
            background: transparent;
        """)
        layout.addWidget(title)

        sub = QLabel("Build streaks. Track progress. Win every day.")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(f"""
            color: {C['text_dim']};
            font-size: 15px; font-weight: 500;
            letter-spacing: 2px;
            font-family: 'Rajdhani','Segoe UI',sans-serif;
            background: transparent;
        """)
        layout.addWidget(sub)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(14)
        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        for icon, text, tab in [("🎯", "My Habits", "habits"),
                                  ("📅", "Monthly Grid", "grid"),
                                  ("📋", "Weekly Tasks", "weekly")]:
            b = QPushButton(f"{icon}  {text}")
            b.setFixedSize(180, 50)
            style = PRIMARY_BTN if tab == "grid" else btn_style(
                bg=C['surface2'], color=C['text'], border=C['border'],
                hover_bg=C['green_bg'], hover_color=C['green'], radius=10, pad="13px 28px", font_size=15
            )
            b.setStyleSheet(style)
            b.clicked.connect(lambda _, t=tab: self.enter_app.emit(t))
            btn_row.addWidget(b)

        layout.addLayout(btn_row)

# ─────────────────────────────────────────────
# TOPBAR
# ─────────────────────────────────────────────
class TopBar(QWidget):
    tab_changed   = pyqtSignal(str)
    open_clicked  = pyqtSignal()
    save_clicked  = pyqtSignal()
    add_habit     = pyqtSignal()
    open_timer    = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setFixedHeight(54)
        self.setStyleSheet(f"""
            QWidget {{
                background: {C['surface']};
                border-bottom: 1px solid {C['border']};
            }}
            QLabel {{ background: transparent; border: none; }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(8)

        logo = QLabel("◈ <span style='color:{c}'>HABIT</span>TRACK".format(c=C['text_dim']))
        logo.setTextFormat(Qt.TextFormat.RichText)
        logo.setStyleSheet(f"""
            color: {C['green']};
            font-size: 20px; font-weight: 700;
            font-family: 'IBM Plex Mono','Courier New',monospace;
            background: transparent; border: none;
        """)
        logo.setCursor(Qt.CursorShape.PointingHandCursor)
        logo.mousePressEvent = lambda e: self.tab_changed.emit("home")
        layout.addWidget(logo)

        # Nav tabs
        self._tabs = {}
        for tab, txt in [("home","Home"),("habits","🎯 My Habits"),("grid","📅 Monthly Grid"),("weekly","📋 Weekly Tasks")]:
            b = QPushButton(txt)
            b.setCheckable(True)
            b.setFixedHeight(30)
            b.setStyleSheet(self._tab_style(False))
            b.clicked.connect(lambda _, t=tab: self.tab_changed.emit(t))
            self._tabs[tab] = b
            layout.addWidget(b)

        # File status
        self.file_lbl = QLabel("No file · local data")
        self.file_lbl.setStyleSheet(f"""
            color: {C['text_faint']};
            font-size: 11px;
            font-family: 'IBM Plex Mono','Courier New',monospace;
            background: {C['surface2']};
            border: 1px solid {C['border']};
            border-radius: 4px;
            padding: 3px 10px;
        """)
        layout.addWidget(self.file_lbl)

        layout.addStretch()

        # Timer btn
        self.timer_btn = QPushButton("⏱  Timer")
        self.timer_btn.setStyleSheet(btn_style(
            bg=C['surface2'], color=C['text_dim'], border=C['border'],
            hover_bg=C['green_bg'], hover_color=C['green'], pad="5px 12px", font_size=12
        ))
        self.timer_btn.clicked.connect(self.open_timer)
        layout.addWidget(self.timer_btn)

        b_open = QPushButton("📂 Open")
        b_open.setStyleSheet(btn_style(pad="4px 10px", font_size=12))
        b_open.clicked.connect(self.open_clicked)
        layout.addWidget(b_open)

        b_save = QPushButton("💾 Save")
        b_save.setStyleSheet(btn_style(pad="4px 10px", font_size=12))
        b_save.clicked.connect(self.save_clicked)
        layout.addWidget(b_save)

        self.add_btn = QPushButton("＋ Habit")
        self.add_btn.setStyleSheet(GREEN_BTN)
        self.add_btn.clicked.connect(self.add_habit)
        self.add_btn.hide()
        layout.addWidget(self.add_btn)

    def _tab_style(self, active):
        if active:
            return f"""
                QPushButton {{
                    background: {C['green_bg']}; color: {C['green']};
                    border: 1px solid {C['green_dim']}; border-radius: 6px;
                    padding: 4px 14px; font-size: 13px; font-weight: 600;
                    font-family: 'Rajdhani','Segoe UI',sans-serif;
                }}
            """
        return f"""
            QPushButton {{
                background: transparent; color: {C['text_dim']};
                border: 1px solid transparent; border-radius: 6px;
                padding: 4px 14px; font-size: 13px; font-weight: 600;
                font-family: 'Rajdhani','Segoe UI',sans-serif;
            }}
            QPushButton:hover {{
                color: {C['text']}; background: {C['surface2']};
            }}
        """

    def set_active(self, tab):
        for k, b in self._tabs.items():
            b.setStyleSheet(self._tab_style(k == tab))
        self.add_btn.setVisible(tab == "habits")

    def set_file_status(self, name, ok):
        self.file_lbl.setText(f"✓ {name}" if ok else f"⚠ {name}")
        color = C['green'] if ok else C['red']
        self.file_lbl.setStyleSheet(f"""
            color: {color};
            font-size: 11px;
            font-family: 'IBM Plex Mono','Courier New',monospace;
            background: {C['surface2']};
            border: 1px solid {C['green_dim'] if ok else C['border']};
            border-radius: 4px; padding: 3px 10px;
        """)

    def set_timer_running(self, running, display=""):
        if running:
            self.timer_btn.setText(f"● {display}")
            self.timer_btn.setStyleSheet(btn_style(
                bg=C['green_bg'], color=C['green'], border=C['green'],
                hover_bg=C['green_bg'], hover_color=C['green'], pad="5px 12px", font_size=12
            ))
        else:
            self.timer_btn.setText("⏱  Timer")
            self.timer_btn.setStyleSheet(btn_style(
                bg=C['surface2'], color=C['text_dim'], border=C['border'],
                hover_bg=C['green_bg'], hover_color=C['green'], pad="5px 12px", font_size=12
            ))

# ─────────────────────────────────────────────
# HOME SCREEN
# ─────────────────────────────────────────────
class HomeSection(QWidget):
    go_tab = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background:{C['bg']};")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(24)
        layout.setContentsMargins(40, 80, 40, 80)

        t = QLabel("◈ HABITTRACK")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t.setStyleSheet(f"color:{C['green']};font-size:36px;font-weight:700;font-family:'IBM Plex Mono','Courier New',monospace;background:transparent;")
        layout.addWidget(t)

        s = QLabel("What would you like to do today?")
        s.setAlignment(Qt.AlignmentFlag.AlignCenter)
        s.setStyleSheet(f"color:{C['text_dim']};font-size:14px;letter-spacing:2px;background:transparent;")
        layout.addWidget(s)

        grid = QGridLayout()
        grid.setSpacing(16)
        cards = [("🎯","My Habits","Manage & reorder","habits"),
                 ("📅","Monthly Grid","Track completions","grid"),
                 ("📋","Weekly Tasks","Daily task lists","weekly")]
        for i, (ico, name, desc, tab) in enumerate(cards):
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background:{C['surface']};border:1px solid {C['border']};
                    border-radius:14px;
                }}
                QFrame:hover {{
                    border-color:{C['green']};background:{C['green_bg']};
                }}
                QLabel {{background:transparent;border:none;}}
            """)
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            cl = QVBoxLayout(card)
            cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl.setSpacing(8)
            il = QLabel(ico); il.setAlignment(Qt.AlignmentFlag.AlignCenter)
            il.setStyleSheet("font-size:28px;background:transparent;border:none;")
            nl = QLabel(name); nl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            nl.setStyleSheet(f"font-size:15px;font-weight:700;color:{C['text']};background:transparent;border:none;")
            dl = QLabel(desc); dl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            dl.setStyleSheet(f"font-size:11px;color:{C['text_dim']};background:transparent;border:none;")
            cl.addWidget(il); cl.addWidget(nl); cl.addWidget(dl)
            card.setFixedSize(190, 120)
            card.mousePressEvent = lambda e, t=tab: self.go_tab.emit(t)
            grid.addWidget(card, 0, i)
        layout.addLayout(grid)

# ─────────────────────────────────────────────
# HABITS SECTION
# ─────────────────────────────────────────────
class HabitRow(QFrame):
    edit_clicked   = pyqtSignal(str)
    delete_clicked = pyqtSignal(str)
    timer_clicked  = pyqtSignal(str)

    def __init__(self, habit, timer_info=None):
        super().__init__()
        self.hid = habit['id']
        self.setStyleSheet(f"""
            QFrame {{
                background:{C['surface']};border:1px solid {C['border']};
                border-radius:10px;
            }}
            QLabel {{background:transparent;border:none;}}
        """)
        row = QHBoxLayout(self)
        row.setContentsMargins(14, 10, 14, 10)
        row.setSpacing(10)

        # Timer btn
        tb = QPushButton("⏱")
        tb.setFixedSize(28, 28)
        has_timer = timer_info and (timer_info.get('running') or timer_info.get('alarmSet'))
        tb.setStyleSheet(btn_style(
            bg=C['green_bg'] if has_timer else C['surface2'],
            color=C['green'] if has_timer else C['text_faint'],
            border=C['green'] if has_timer else C['border'],
            hover_bg=C['green_bg'], hover_color=C['green'], pad="0px", font_size=13
        ))
        tb.clicked.connect(lambda: self.timer_clicked.emit(self.hid))
        row.addWidget(tb)

        ico = QLabel(habit.get('icon', '●'))
        ico.setStyleSheet("font-size:18px;background:transparent;border:none;")
        row.addWidget(ico)

        name = QLabel(habit['name'])
        name.setStyleSheet(f"font-size:14px;font-weight:600;color:{C['text']};background:transparent;border:none;")
        row.addWidget(name)
        row.addStretch()

        drag_hint = QLabel("⠿")
        drag_hint.setStyleSheet(f"color:{C['text_faint']};font-size:14px;background:transparent;border:none;")
        drag_hint.setToolTip("Drag to reorder")
        row.addWidget(drag_hint)

        edit_btn = QPushButton("✏ Edit")
        edit_btn.setStyleSheet(btn_style(pad="4px 10px", font_size=11))
        edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.hid))
        row.addWidget(edit_btn)

        del_btn = QPushButton("✕")
        del_btn.setStyleSheet(DANGER_BTN.replace("padding: 6px 14px", "padding: 4px 10px").replace("font-size: 13px", "font-size: 11px"))
        del_btn.clicked.connect(lambda: self.delete_clicked.emit(self.hid))
        row.addWidget(del_btn)


class HabitsSection(QWidget):
    open_timer_for = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background:{C['bg']};")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"background:{C['bg']};border:none;")
        outer.addWidget(scroll)

        self.container = QWidget()
        self.container.setStyleSheet(f"background:{C['bg']};")
        scroll.setWidget(self.container)

        self.layout_ = QVBoxLayout(self.container)
        self.layout_.setContentsMargins(60, 28, 60, 40)
        self.layout_.setSpacing(8)
        self.habit_timers = {}
        self.refresh()

    def refresh(self, habit_timers=None):
        if habit_timers is not None:
            self.habit_timers = habit_timers
        while self.layout_.count():
            item = self.layout_.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        hdr = QHBoxLayout()
        t = QLabel("My Habits")
        t.setStyleSheet(f"color:{C['green']};font-size:22px;font-weight:700;font-family:'IBM Plex Mono','Courier New',monospace;background:transparent;")
        hint = QLabel("Drag to reorder")
        hint.setStyleSheet(f"color:{C['text_faint']};font-size:11px;background:transparent;")
        hdr.addWidget(t); hdr.addStretch(); hdr.addWidget(hint)
        self.layout_.addLayout(hdr)

        if not D.habits:
            empty = QLabel("No habits yet. Click ＋ Habit to add one.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(f"color:{C['text_faint']};font-size:14px;padding:40px;background:transparent;")
            self.layout_.addWidget(empty)
        else:
            for hab in D.habits:
                ht = self.habit_timers.get(hab['id'])
                row = HabitRow(hab, ht)
                row.edit_clicked.connect(self._edit)
                row.delete_clicked.connect(self._delete)
                row.timer_clicked.connect(self.open_timer_for)
                self.layout_.addWidget(row)

        self.layout_.addStretch()

    def _edit(self, hid):
        hab = next((h for h in D.habits if h['id'] == hid), None)
        if not hab: return
        dlg = HabitDialog(parent=self.window(), habit=hab)
        if dlg.exec():
            name, icon = dlg.result_data()
            hab['name'] = name; hab['icon'] = icon
            D.save(); self.refresh()

    def _delete(self, hid):
        reply = QMessageBox.question(self, "Remove Habit", "Remove this habit?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            D.habits = [h for h in D.habits if h['id'] != hid]
            D.save(); self.refresh()

# ─────────────────────────────────────────────
# HABIT ADD/EDIT DIALOG
# ─────────────────────────────────────────────
class HabitDialog(QDialog):
    def __init__(self, parent=None, habit=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Habit" if habit else "Add Habit")
        self.setModal(True)
        self.setFixedSize(360, 260)
        self.setStyleSheet(f"background:{C['surface']};color:{C['text']};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 26, 26, 26)
        layout.setSpacing(14)

        title = QLabel("Edit Habit" if habit else "Add New Habit")
        title.setStyleSheet(f"color:{C['green']};font-size:19px;font-weight:700;background:transparent;")
        layout.addWidget(title)

        lbl1 = QLabel("Habit Name")
        lbl1.setStyleSheet(f"color:{C['text_dim']};font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;background:transparent;")
        layout.addWidget(lbl1)
        self.name_in = QLineEdit(habit['name'] if habit else "")
        self.name_in.setPlaceholderText("e.g. Morning Walk")
        layout.addWidget(self.name_in)

        lbl2 = QLabel("Icon (emoji)")
        lbl2.setStyleSheet(f"color:{C['text_dim']};font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1px;background:transparent;")
        layout.addWidget(lbl2)
        self.icon_in = QLineEdit(habit.get('icon','') if habit else "")
        self.icon_in.setPlaceholderText("e.g. 🚶")
        self.icon_in.setMaxLength(4)
        layout.addWidget(self.icon_in)

        acts = QHBoxLayout()
        acts.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setStyleSheet(btn_style())
        cancel.clicked.connect(self.reject)
        ok = QPushButton("Save Changes" if habit else "Add Habit")
        ok.setStyleSheet(GREEN_BTN)
        ok.clicked.connect(self._accept)
        acts.addWidget(cancel); acts.addWidget(ok)
        layout.addLayout(acts)
        self.name_in.returnPressed.connect(self._accept)

    def _accept(self):
        if self.name_in.text().strip():
            self.accept()

    def result_data(self):
        return self.name_in.text().strip(), self.icon_in.text().strip() or "●"

# ─────────────────────────────────────────────
# MONTHLY GRID SECTION
# ─────────────────────────────────────────────
class GridSection(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background:{C['bg']};")
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # Header area (stats)
        self.header_widget = QWidget()
        self.header_widget.setStyleSheet(f"background:{C['bg']};")
        main.addWidget(self.header_widget)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"background:{C['bg']};border:none;")
        main.addWidget(scroll)

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet(f"background:{C['bg']};")
        scroll.setWidget(self.scroll_content)
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(20, 0, 20, 20)
        self.scroll_layout.setSpacing(14)

        self.refresh()

    def refresh(self):
        # Rebuild header
        hw = self.header_widget
        for child in hw.findChildren(QWidget):
            child.deleteLater()

        hl = QHBoxLayout(hw)
        hl.setContentsMargins(20, 18, 20, 10)
        hl.setSpacing(20)

        left = QVBoxLayout()
        mname = QLabel(f"{MONTH_NAMES[D.vm-1]} {D.vy}")
        mname.setStyleSheet(f"color:{C['text']};font-size:32px;font-weight:700;font-family:'IBM Plex Mono','Courier New',monospace;background:transparent;")
        left.addWidget(mname)

        nav = QHBoxLayout()
        nav.setSpacing(6)
        prev_btn = QPushButton("‹")
        prev_btn.setFixedSize(30, 30)
        prev_btn.setStyleSheet(btn_style(pad="0px", font_size=16))
        prev_btn.clicked.connect(lambda: self._ch_month(-1))
        today_btn = QPushButton("Today")
        today_btn.setFixedHeight(30)
        today_btn.setStyleSheet(btn_style(pad="0px 10px", font_size=11))
        today_btn.clicked.connect(self._go_today)
        next_btn = QPushButton("›")
        next_btn.setFixedSize(30, 30)
        next_btn.setStyleSheet(btn_style(pad="0px", font_size=16))
        next_btn.clicked.connect(lambda: self._ch_month(1))
        nav.addWidget(prev_btn); nav.addWidget(today_btn); nav.addWidget(next_btn)
        left.addLayout(nav)
        hl.addLayout(left)

        stats = D.month_stats()
        for lbl_txt, val, clr in [
            ("Number of habits", str(len(D.habits)), C['text']),
            ("Completed habits",  str(stats['checked']), C['green']),
            ("Progress",          f"{stats['pct']}%", C['green']),
        ]:
            sv = QVBoxLayout()
            sv.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vl = QLabel(str(val))
            vl.setStyleSheet(f"color:{clr};font-size:26px;font-weight:700;font-family:'IBM Plex Mono','Courier New',monospace;background:transparent;")
            vl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ll = QLabel(lbl_txt)
            ll.setStyleSheet(f"color:{C['text_dim']};font-size:10px;text-transform:uppercase;letter-spacing:1.2px;background:transparent;")
            ll.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sv.addWidget(vl); sv.addWidget(ll)
            hl.addLayout(sv)

        # Rebuild scroll content
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        self._build_grid()
        self._build_analysis()

    def _ch_month(self, d):
        D.vm += d
        if D.vm > 12: D.vm = 1; D.vy += 1
        if D.vm < 1:  D.vm = 12; D.vy -= 1
        D.save(); self.refresh()

    def _go_today(self):
        today = date.today()
        D.vm = today.month; D.vy = today.year
        D.save(); self.refresh()

    def _build_grid(self):
        y, m = D.vy, D.vm
        days = D.days_in_month(y, m)
        today = date.today()
        day_names_2 = ["Mo","Tu","We","Th","Fr","Sa","Su"]

        # Build weeks (Mon-based)
        weeks = []
        wk = []
        fd = D.first_day(y, m)  # Mon=0
        for _ in range(fd): wk.append(None)
        for d in range(1, days + 1):
            wk.append(d)
            if len(wk) == 7: weeks.append(wk); wk = []
        if wk:
            while len(wk) < 7: wk.append(None)
            weeks.append(wk)

        table = QTableWidget()
        table.setStyleSheet(f"""
            QTableWidget {{
                background:{C['surface']};
                gridline-color:{C['border']};
                border:1px solid {C['border']};
                border-radius:10px;
                font-size:11px;
                font-family:'Rajdhani','Segoe UI',sans-serif;
            }}
            QTableWidget::item {{
                padding:2px;
                text-align:center;
            }}
            QHeaderView::section {{
                background:{C['surface2']};
                color:{C['text_dim']};
                border:1px solid {C['border']};
                font-size:10px;
                font-weight:700;
                padding:4px;
            }}
        """)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table.verticalHeader().setVisible(False)
        table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        # Row count: habits + 3 summary rows
        n_habits = len(D.habits)
        n_rows = n_habits + 3
        # Columns: habit name + all days
        all_days = []
        for wk in weeks:
            for d in wk:
                if d is not None:
                    all_days.append(d)

        table.setRowCount(n_rows)
        table.setColumnCount(1 + len(all_days))

        # Column headers
        table.setHorizontalHeaderItem(0, QTableWidgetItem("My Habits"))
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)

        col = 1
        for d in all_days:
            dt = date(y, m, d)
            dw = dt.weekday()
            day_str = f"{day_names_2[dw]}\n{d}"
            item = QTableWidgetItem(day_str)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            is_today = dt == today
            if is_today:
                item.setForeground(qc(C['green']))
            table.setHorizontalHeaderItem(col, item)
            table.setColumnWidth(col, 36)
            col += 1

        # Row heights
        for r in range(n_rows):
            table.setRowHeight(r, 32)

        # Habit rows
        for ri, hab in enumerate(D.habits):
            name_item = QTableWidgetItem(f"  {hab.get('icon','•')}  {hab['name']}")
            name_item.setForeground(qc(C['text']))
            table.setItem(ri, 0, name_item)
            col = 1
            for d in all_days:
                dt = date(y, m, d)
                fut = dt > today
                ck = D.is_checked(y, m, d, hab['id'])
                item = QTableWidgetItem("✓" if ck else "")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if fut:
                    item.setBackground(qc(C['bg']))
                    item.setForeground(qc(C['text_faint']))
                elif ck:
                    item.setBackground(qc(C['green_bg']))
                    item.setForeground(qc(C['green']))
                else:
                    item.setBackground(qc(C['surface']))
                item.setData(Qt.ItemDataRole.UserRole, (y, m, d, hab['id']))
                table.setItem(ri, col, item)
                col += 1

        table.cellClicked.connect(self._cell_clicked)

        # Progress row
        pr = n_habits
        prog_item = QTableWidgetItem("Progress")
        prog_item.setForeground(qc(C['text_dim']))
        prog_item.setBackground(qc(C['surface2']))
        table.setItem(pr, 0, prog_item)
        col = 1
        for d in all_days:
            dt = date(y, m, d)
            if dt > today:
                it = QTableWidgetItem("—"); it.setForeground(qc(C['text_faint']))
            else:
                cnt = len(D.completions.get(D.dk(y, m, d), []))
                pct = round(cnt / len(D.habits) * 100) if D.habits else 0
                it = QTableWidgetItem(f"{pct}%")
                it.setForeground(qc(C['green'] if pct > 0 else C['text_faint']))
            it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it.setBackground(qc(C['surface2']))
            table.setItem(pr, col, it)
            col += 1

        # Done row
        dr = n_habits + 1
        done_item = QTableWidgetItem("Done")
        done_item.setForeground(qc(C['text_dim']))
        done_item.setBackground(qc(C['bg']))
        table.setItem(dr, 0, done_item)
        col = 1
        for d in all_days:
            dt = date(y, m, d)
            if dt > today: it = QTableWidgetItem("—"); it.setForeground(qc(C['text_faint']))
            else:
                cnt = len(D.completions.get(D.dk(y, m, d), []))
                it = QTableWidgetItem(str(cnt)); it.setForeground(qc(C['green']))
            it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it.setBackground(qc(C['bg']))
            table.setItem(dr, col, it)
            col += 1

        # Not Done row
        nr = n_habits + 2
        nd_item = QTableWidgetItem("Not Done")
        nd_item.setForeground(qc(C['text_dim']))
        nd_item.setBackground(qc(C['bg']))
        table.setItem(nr, 0, nd_item)
        col = 1
        for d in all_days:
            dt = date(y, m, d)
            if dt > today: it = QTableWidgetItem("—"); it.setForeground(qc(C['text_faint']))
            else:
                cnt = len(D.completions.get(D.dk(y, m, d), []))
                nd = len(D.habits) - cnt
                it = QTableWidgetItem(str(nd)); it.setForeground(qc(C['red']))
            it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it.setBackground(qc(C['bg']))
            table.setItem(nr, col, it)
            col += 1

        self.scroll_layout.addWidget(table)

    def _cell_clicked(self, row, col):
        if col == 0: return
        item = self.sender().item(row, col)
        if item is None: return
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            y, m, d, hid = data
            D.toggle(y, m, d, hid)
            self.refresh()

    def _build_analysis(self):
        y, m = D.vy, D.vm
        days = D.days_in_month(y, m)
        today = date.today()

        hcnt = {h['id']: 0 for h in D.habits}
        elapsed = 0; total_ck = 0
        for d in range(1, days + 1):
            dt = date(y, m, d)
            if dt > today: break
            elapsed += 1
            for hid in D.completions.get(D.dk(y, m, d), []):
                if hid in hcnt:
                    hcnt[hid] += 1
                    total_ck += 1

        row_layout = QHBoxLayout()
        row_layout.setSpacing(14)

        # Analysis card
        acard = Card()
        al = QVBoxLayout(acard)
        al.setContentsMargins(18, 18, 18, 18)
        al.setSpacing(7)
        at = QLabel("Analysis")
        at.setStyleSheet(f"color:{C['text']};font-size:15px;font-weight:700;background:transparent;border:none;")
        al.addWidget(at)

        for hab in D.habits:
            cnt = hcnt.get(hab['id'], 0)
            pct = round(cnt / elapsed * 100) if elapsed else 0
            hrow = QHBoxLayout()
            hrow.setSpacing(8)
            hn = QLabel(f"{hab.get('icon','')} {hab['name']}")
            hn.setStyleSheet(f"color:{C['text_dim']};font-size:11px;min-width:140px;background:transparent;border:none;")
            hn.setFixedWidth(150)
            hn.setWordWrap(False)
            bar_container = QFrame()
            bar_container.setFixedHeight(14)
            bar_container.setStyleSheet(f"background:{C['surface2']};border-radius:3px;border:none;")
            bar_fill = QFrame(bar_container)
            bar_fill.setFixedHeight(14)
            bar_fill.setFixedWidth(max(3, int(pct * 1.8)))
            bar_fill.setStyleSheet(f"background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {C['green2']},stop:1 {C['green']});border-radius:3px;border:none;")
            pct_lbl = QLabel(f"{pct}%")
            pct_lbl.setStyleSheet(f"color:{C['green']};font-size:10px;font-family:'IBM Plex Mono','Courier New',monospace;min-width:34px;background:transparent;border:none;")
            pct_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            num_lbl = QLabel(f"{cnt}/{elapsed}")
            num_lbl.setStyleSheet(f"color:{C['text_dim']};font-size:10px;font-family:'IBM Plex Mono','Courier New',monospace;min-width:46px;background:transparent;border:none;")
            num_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            hrow.addWidget(hn); hrow.addWidget(bar_container, 1)
            hrow.addWidget(pct_lbl); hrow.addWidget(num_lbl)
            al.addLayout(hrow)

        row_layout.addWidget(acard, 1)

        # Summary card
        scard = Card()
        sl = QVBoxLayout(scard)
        sl.setContentsMargins(18, 18, 18, 18)
        sl.setSpacing(0)
        st = QLabel("Summary")
        st.setStyleSheet(f"color:{C['text']};font-size:15px;font-weight:700;background:transparent;border:none;")
        sl.addWidget(st)
        sl.addSpacing(10)

        total_poss = len(D.habits) * elapsed
        ov_pct = round(total_ck / total_poss * 100) if total_poss else 0
        best_h = max(D.habits, key=lambda h: hcnt.get(h['id'], 0), default=None) if D.habits else None

        for lbl_txt, val, clr in [
            ("Days Elapsed", f"{elapsed}/{days}", C['green']),
            ("Overall Rate", f"{ov_pct}%", C['green']),
            ("Total Checks", str(total_ck), C['green']),
            ("Remaining",    str(total_poss - total_ck), C['red']),
        ]:
            item_row = QHBoxLayout()
            ll = QLabel(lbl_txt)
            ll.setStyleSheet(f"color:{C['text']};font-size:13px;background:transparent;border:none;")
            vl = QLabel(val)
            vl.setStyleSheet(f"color:{clr};font-size:13px;font-weight:600;font-family:'IBM Plex Mono','Courier New',monospace;background:transparent;border:none;")
            vl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item_row.addWidget(ll); item_row.addStretch(); item_row.addWidget(vl)
            sl.addLayout(item_row)
            sep = QFrame()
            sep.setFixedHeight(1)
            sep.setStyleSheet(f"background:{C['border']};border:none;")
            sl.addWidget(sep)

        if best_h:
            item_row = QHBoxLayout()
            ll = QLabel("Top Habit")
            ll.setStyleSheet(f"color:{C['text']};font-size:13px;background:transparent;border:none;")
            vl = QLabel(f"{best_h.get('icon','')} {best_h['name'][:15]}")
            vl.setStyleSheet(f"color:{C['green']};font-size:10px;font-weight:600;font-family:'IBM Plex Mono','Courier New',monospace;background:transparent;border:none;")
            vl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item_row.addWidget(ll); item_row.addStretch(); item_row.addWidget(vl)
            sl.addLayout(item_row)

        sl.addStretch()
        scard.setFixedWidth(260)
        row_layout.addWidget(scard)

        row_widget = QWidget()
        row_widget.setStyleSheet(f"background:{C['bg']};")
        row_widget.setLayout(row_layout)
        self.scroll_layout.addWidget(row_widget)

# ─────────────────────────────────────────────
# WEEKLY SECTION
# ─────────────────────────────────────────────
class DayCard(QFrame):
    task_changed = pyqtSignal()

    def __init__(self, year, month, day, is_ghost=False):
        super().__init__()
        self.year = year; self.month = month; self.day = day
        self.dk = D.dk(year, month, day) if day else None
        today = date.today()
        is_today = day and date(year, month, day) == today
        is_future = day and date(year, month, day) > today

        self.setFixedWidth(170)
        self.setMinimumHeight(280)
        self.setStyleSheet(f"""
            QFrame {{
                background:{C['surface']};
                border:1px solid {C['border']};
                border-radius:9px;
            }}
            QLabel {{ background:transparent; border:none; }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        if day is None:
            self.setStyleSheet(f"background:{C['surface3']};border:1px solid {C['border']};border-radius:9px;opacity:0.15;")
            return

        dw = date(year, month, day).weekday()
        day_name = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"][dw]
        date_str = f"{day:02d}.{month:02d}.{year}"

        hdr_color = C['green'] if is_today else (C['surface3'] if is_future else "#1f5c38")
        txt_color = "#000" if is_today else "#fff"
        hdr = QWidget()
        hdr.setStyleSheet(f"background:{hdr_color};border-radius:8px 8px 0 0;")
        hl = QVBoxLayout(hdr)
        hl.setContentsMargins(10, 8, 10, 8)
        hl.setSpacing(1)
        dn = QLabel(day_name)
        dn.setStyleSheet(f"color:{txt_color};font-size:13px;font-weight:700;background:transparent;")
        ds = QLabel(date_str)
        ds.setStyleSheet(f"color:{txt_color};font-size:9px;font-weight:600;font-family:'IBM Plex Mono','Courier New',monospace;background:transparent;")
        hl.addWidget(dn); hl.addWidget(ds)
        layout.addWidget(hdr)

        # Donut
        tasks = D.tasks.get(self.dk, [])
        done_tasks = sum(1 for t in tasks if t.get('done'))
        task_pct = done_tasks / len(tasks) if tasks else 0
        self.donut = DonutWidget(size=72, stroke=6)
        self.donut.set_pct(task_pct)
        donut_wrap = QHBoxLayout()
        donut_wrap.setAlignment(Qt.AlignmentFlag.AlignCenter)
        donut_wrap.setContentsMargins(8, 8, 8, 4)
        donut_wrap.addWidget(self.donut)
        layout.addLayout(donut_wrap)

        # Tasks
        tasks_wrap = QWidget()
        tasks_wrap.setStyleSheet("background:transparent;")
        tl = QVBoxLayout(tasks_wrap)
        tl.setContentsMargins(9, 2, 9, 4)
        tl.setSpacing(3)

        tlabel_row = QHBoxLayout()
        tl_lbl = QLabel("Tasks")
        tl_lbl.setStyleSheet(f"color:{C['text_dim']};font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:1px;background:transparent;")
        add_btn = QPushButton("+")
        add_btn.setFixedSize(15, 15)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background:{C['surface3']};border:1px solid {C['border']};
                border-radius:7px;color:{C['text_dim']};font-size:10px;padding:0px;
            }}
            QPushButton:hover {{background:{C['green']};border-color:{C['green']};color:#000;}}
        """)
        add_btn.clicked.connect(self._show_add_input)
        tlabel_row.addWidget(tl_lbl); tlabel_row.addStretch(); tlabel_row.addWidget(add_btn)
        tl.addLayout(tlabel_row)

        self.input_row = QHBoxLayout()
        self.input_row.setSpacing(4)
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Add a task...")
        self.task_input.setStyleSheet(f"""
            QLineEdit {{
                background:{C['surface2']};border:1px solid {C['border']};border-radius:4px;
                color:{C['text']};font-size:10px;padding:3px 6px;
            }}
            QLineEdit:focus {{border-color:{C['green']};}}
        """)
        self.task_input.returnPressed.connect(self._add_task)
        ok_btn = QPushButton("Add")
        ok_btn.setFixedHeight(20)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background:{C['green']};color:#000;border:none;border-radius:3px;
                font-weight:700;font-size:10px;padding:0px 6px;
            }}
        """)
        ok_btn.clicked.connect(self._add_task)
        self.input_row.addWidget(self.task_input); self.input_row.addWidget(ok_btn)
        self.input_widget = QWidget()
        self.input_widget.setLayout(self.input_row)
        self.input_widget.setVisible(False)
        self.input_widget.setStyleSheet("background:transparent;")
        tl.addWidget(self.input_widget)

        self.task_widgets = []
        for ti, task in enumerate(tasks):
            self._add_task_widget(tl, task, ti)

        tasks_scroll = QScrollArea()
        tasks_scroll.setWidget(tasks_wrap)
        tasks_scroll.setWidgetResizable(True)
        tasks_scroll.setMaximumHeight(140)
        tasks_scroll.setStyleSheet("border:none;background:transparent;")
        layout.addWidget(tasks_scroll)

        # Habits row
        hab_done = len(D.completions.get(self.dk, []))
        hab_total = len(D.habits)
        hab_row = QHBoxLayout()
        hab_row.setContentsMargins(9, 3, 9, 3)
        hl2 = QLabel(f"Habits: ")
        hl2.setStyleSheet(f"color:{C['text_faint']};font-size:10px;background:transparent;")
        hv = QLabel(f"{hab_done}/{hab_total}")
        hv.setStyleSheet(f"color:{C['green']};font-size:10px;font-family:'IBM Plex Mono','Courier New',monospace;background:transparent;")
        hab_row.addWidget(hl2); hab_row.addWidget(hv); hab_row.addStretch()
        hrow_wrap = QWidget(); hrow_wrap.setStyleSheet(f"background:transparent;border-top:1px solid {C['border']};")
        hrow_wrap.setLayout(hab_row)
        layout.addWidget(hrow_wrap)

        # Footer
        foot = QWidget()
        foot.setStyleSheet(f"background:transparent;border-top:1px solid {C['border']};")
        fl = QHBoxLayout(foot)
        fl.setContentsMargins(9, 6, 9, 6)
        done_col = QVBoxLayout()
        dv = QLabel(str(done_tasks))
        dv.setStyleSheet(f"color:{C['green']};font-size:13px;font-weight:600;font-family:'IBM Plex Mono','Courier New',monospace;background:transparent;")
        dl = QLabel("Completed")
        dl.setStyleSheet(f"color:{C['text_faint']};font-size:9px;text-transform:uppercase;letter-spacing:.5px;background:transparent;")
        done_col.addWidget(dv); done_col.addWidget(dl)
        nd_col = QVBoxLayout()
        nd_col.setAlignment(Qt.AlignmentFlag.AlignRight)
        ndv = QLabel(str(len(tasks) - done_tasks))
        ndv.setStyleSheet(f"color:{C['red']};font-size:13px;font-weight:600;font-family:'IBM Plex Mono','Courier New',monospace;background:transparent;")
        ndv.setAlignment(Qt.AlignmentFlag.AlignRight)
        ndl = QLabel("Not Completed")
        ndl.setStyleSheet(f"color:{C['text_faint']};font-size:9px;text-transform:uppercase;letter-spacing:.5px;background:transparent;")
        ndl.setAlignment(Qt.AlignmentFlag.AlignRight)
        nd_col.addWidget(ndv); nd_col.addWidget(ndl)
        fl.addLayout(done_col); fl.addStretch(); fl.addLayout(nd_col)
        layout.addWidget(foot)

    def _show_add_input(self):
        self.input_widget.setVisible(True)
        self.task_input.setFocus()

    def _add_task_widget(self, layout, task, ti):
        row = QHBoxLayout()
        row.setSpacing(5)
        ck = QFrame()
        ck.setFixedSize(13, 13)
        if task.get('done'):
            ck.setStyleSheet(f"background:{C['green']};border-radius:2px;border:none;")
        else:
            ck.setStyleSheet(f"background:transparent;border:1.5px solid {C['border']};border-radius:2px;")
        txt = QLabel(task['text'])
        if task.get('done'):
            txt.setStyleSheet(f"font-size:11px;color:{C['text_faint']};text-decoration:line-through;background:transparent;")
        else:
            txt.setStyleSheet(f"font-size:11px;color:{C['text']};background:transparent;")
        txt.setWordWrap(True)
        row.addWidget(ck); row.addWidget(txt, 1)
        w = QWidget(); w.setLayout(row); w.setStyleSheet("background:transparent;")
        w.setCursor(Qt.CursorShape.PointingHandCursor)
        w.mousePressEvent = lambda e, k=self.dk, i=ti: self._toggle_task(k, i)
        layout.addWidget(w)

    def _add_task(self):
        txt = self.task_input.text().strip()
        if not txt: return
        if self.dk not in D.tasks: D.tasks[self.dk] = []
        D.tasks[self.dk].append({"id": f"t{int(time.time()*1000)}", "text": txt, "done": False})
        self.task_input.clear()
        D.save(); self.task_changed.emit()

    def _toggle_task(self, k, i):
        if k not in D.tasks or i >= len(D.tasks[k]): return
        D.tasks[k][i]['done'] = not D.tasks[k][i].get('done', False)
        D.save(); self.task_changed.emit()


class WeeklySection(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background:{C['bg']};")
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)

        self.header = QWidget()
        self.header.setStyleSheet(f"background:{C['bg']};")
        main.addWidget(self.header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"background:{C['bg']};border:none;")
        main.addWidget(scroll)

        self.content = QWidget()
        self.content.setStyleSheet(f"background:{C['bg']};")
        scroll.setWidget(self.content)
        self.cl = QVBoxLayout(self.content)
        self.cl.setContentsMargins(20, 0, 20, 40)
        self.cl.setSpacing(20)

        self.refresh()

    def refresh(self):
        # Header
        for child in self.header.findChildren(QWidget):
            child.deleteLater()
        hl = QHBoxLayout(self.header)
        hl.setContentsMargins(20, 16, 20, 10)
        t = QLabel("Weekly Tasks")
        t.setStyleSheet(f"color:{C['green']};font-size:22px;font-weight:700;font-family:'IBM Plex Mono','Courier New',monospace;background:transparent;")
        hl.addWidget(t)
        prev_btn = QPushButton("‹")
        prev_btn.setFixedSize(28, 28)
        prev_btn.setStyleSheet(btn_style(pad="0px", font_size=14))
        prev_btn.clicked.connect(lambda: self._ch(-1))
        mn = QLabel(f"{MONTH_NAMES[D.vm-1]} {D.vy}")
        mn.setStyleSheet(f"color:{C['text_dim']};font-size:13px;background:transparent;")
        today_btn = QPushButton("↺")
        today_btn.setFixedSize(28, 28)
        today_btn.setStyleSheet(btn_style(pad="0px", font_size=13))
        today_btn.clicked.connect(self._go_today)
        next_btn = QPushButton("›")
        next_btn.setFixedSize(28, 28)
        next_btn.setStyleSheet(btn_style(pad="0px", font_size=14))
        next_btn.clicked.connect(lambda: self._ch(1))
        hl.addWidget(prev_btn); hl.addWidget(mn); hl.addWidget(today_btn); hl.addWidget(next_btn)
        hl.addStretch()

        # Weeks
        while self.cl.count():
            item = self.cl.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        y, m = D.vy, D.vm
        days = D.days_in_month(y, m)
        weeks = []
        wk = []
        fd = D.first_day(y, m)
        for _ in range(fd): wk.append(None)
        for d in range(1, days + 1):
            wk.append(d)
            if len(wk) == 7: weeks.append(wk); wk = []
        if wk:
            while len(wk) < 7: wk.append(None)
            weeks.append(wk)

        for wi, wk in enumerate(weeks):
            wb = QWidget(); wb.setStyleSheet(f"background:{C['bg']};")
            wbl = QVBoxLayout(wb)
            wbl.setContentsMargins(0, 0, 0, 0)
            wbl.setSpacing(8)
            wlbl = QLabel(f"Week {wi+1}")
            wlbl.setStyleSheet(f"color:{C['text_dim']};font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:1.5px;background:transparent;")
            wbl.addWidget(wlbl)

            day_row = QHBoxLayout()
            day_row.setSpacing(8)
            day_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
            for d in wk:
                card = DayCard(y, m, d)
                card.task_changed.connect(self.refresh)
                day_row.addWidget(card)
            wbl.addLayout(day_row)
            self.cl.addWidget(wb)

        self.cl.addStretch()

    def _ch(self, d):
        D.vm += d
        if D.vm > 12: D.vm = 1; D.vy += 1
        if D.vm < 1:  D.vm = 12; D.vy -= 1
        D.save(); self.refresh()

    def _go_today(self):
        today = date.today()
        D.vm = today.month; D.vy = today.year
        D.save(); self.refresh()

# ─────────────────────────────────────────────
# TIMER DIALOG
# ─────────────────────────────────────────────
class TimerDialog(QDialog):
    timer_started  = pyqtSignal()
    timer_stopped  = pyqtSignal()
    timer_tick     = pyqtSignal(int, int)   # remaining, total

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⏱ Timer")
        self.setModal(False)
        self.setFixedSize(420, 400)
        self.setStyleSheet(f"background:{C['surface']};color:{C['text']};")

        self.total = 0; self.remaining = 0
        self.running = False; self.label = ""

        self._timer = QTimer()
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        title = QLabel("⏱ Set Timer")
        title.setStyleSheet(f"color:{C['green']};font-size:22px;font-weight:700;font-family:'IBM Plex Mono','Courier New',monospace;background:transparent;")
        layout.addWidget(title)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        # Picker page
        picker = QWidget(); picker.setStyleSheet(f"background:transparent;")
        pl = QVBoxLayout(picker); pl.setSpacing(12)

        presets = QGridLayout(); presets.setSpacing(8)
        for i, (mins, lbl_txt) in enumerate([(5,"5m"),(10,"10m"),(15,"15m"),(20,"20m"),
                                               (25,"25m"),(30,"30m"),(45,"45m"),(60,"1h")]):
            b = QPushButton(lbl_txt)
            b.setStyleSheet(btn_style(
                bg=C['surface2'], color=C['text_dim'], border=C['border'],
                hover_bg=C['green_bg'], hover_color=C['green'], pad="10px 4px", font_size=13
            ))
            b.clicked.connect(lambda _, m=mins: self._preset(m))
            presets.addWidget(b, i//4, i%4)
        pl.addLayout(presets)

        custom_lbl = QLabel("Custom")
        custom_lbl.setStyleSheet(f"color:{C['text_dim']};font-size:11px;text-transform:uppercase;letter-spacing:1px;background:transparent;")
        pl.addWidget(custom_lbl)

        time_row = QHBoxLayout()
        time_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        time_row.setSpacing(8)
        self.t_h = QSpinBox(); self.t_h.setRange(0,23); self.t_h.setValue(0); self.t_h.setFixedSize(64, 40)
        self.t_m = QSpinBox(); self.t_m.setRange(0,59); self.t_m.setValue(0); self.t_m.setFixedSize(64, 40)
        self.t_s = QSpinBox(); self.t_s.setRange(0,59); self.t_s.setValue(0); self.t_s.setFixedSize(64, 40)
        for sp in [self.t_h, self.t_m, self.t_s]:
            sp.setStyleSheet(f"""
                QSpinBox {{
                    background:{C['surface2']};border:1px solid {C['border']};border-radius:8px;
                    color:{C['text']};font-size:20px;font-weight:600;font-family:'IBM Plex Mono','Courier New',monospace;
                    padding:4px;text-align:center;
                }}
                QSpinBox:focus {{border-color:{C['green']};}}
                QSpinBox::up-button, QSpinBox::down-button {{width:0px;}}
            """)
            sp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c1 = QLabel(":"); c1.setStyleSheet(f"color:{C['text_dim']};font-size:22px;background:transparent;")
        c2 = QLabel(":"); c2.setStyleSheet(f"color:{C['text_dim']};font-size:22px;background:transparent;")
        time_row.addWidget(self.t_h); time_row.addWidget(c1)
        time_row.addWidget(self.t_m); time_row.addWidget(c2)
        time_row.addWidget(self.t_s)
        pl.addLayout(time_row)

        acts = QHBoxLayout(); acts.setSpacing(8); acts.setAlignment(Qt.AlignmentFlag.AlignRight)
        cancel_b = QPushButton("Cancel"); cancel_b.setStyleSheet(btn_style()); cancel_b.clicked.connect(self.hide)
        start_b  = QPushButton("Start Timer"); start_b.setStyleSheet(GREEN_BTN); start_b.clicked.connect(self._start)
        acts.addWidget(cancel_b); acts.addWidget(start_b)
        pl.addLayout(acts)
        self.stack.addWidget(picker)

        # Running page
        running = QWidget(); running.setStyleSheet("background:transparent;")
        rl = QVBoxLayout(running); rl.setAlignment(Qt.AlignmentFlag.AlignCenter); rl.setSpacing(12)

        self.cd_label = QLabel("FOCUS SESSION")
        self.cd_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cd_label.setStyleSheet(f"color:{C['text_dim']};font-size:11px;letter-spacing:1px;background:transparent;")
        rl.addWidget(self.cd_label)

        self.ring = BigRingWidget(size=140)
        self.ring.setAlignment(Qt.AlignmentFlag.AlignCenter) if hasattr(self.ring, 'setAlignment') else None
        ring_wrap = QHBoxLayout(); ring_wrap.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ring_wrap.addWidget(self.ring)
        rl.addLayout(ring_wrap)

        r_acts = QHBoxLayout(); r_acts.setSpacing(8); r_acts.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pause_btn = QPushButton("Pause"); self.pause_btn.setStyleSheet(btn_style()); self.pause_btn.clicked.connect(self._pause)
        reset_btn = QPushButton("Reset"); reset_btn.setStyleSheet(btn_style()); reset_btn.clicked.connect(self._reset)
        minimize_btn = QPushButton("Minimize"); minimize_btn.setStyleSheet(GREEN_BTN); minimize_btn.clicked.connect(self.hide)
        r_acts.addWidget(self.pause_btn); r_acts.addWidget(reset_btn); r_acts.addWidget(minimize_btn)
        rl.addLayout(r_acts)
        self.stack.addWidget(running)

    def _preset(self, mins):
        self.t_h.setValue(0); self.t_m.setValue(mins); self.t_s.setValue(0)
        self.label = f"{mins} MIN FOCUS"

    def _start(self):
        total = self.t_h.value()*3600 + self.t_m.value()*60 + self.t_s.value()
        if total <= 0: return
        self.total = total; self.remaining = total; self.running = True
        self.stack.setCurrentIndex(1)
        self.cd_label.setText(self.label or "TIMER")
        self._update_ui()
        self._timer.start()
        self.timer_started.emit()

    def _tick(self):
        if not self.running: return
        self.remaining -= 1
        if self.remaining <= 0:
            self.remaining = 0; self.running = False
            self._timer.stop(); self._beep()
            self.timer_stopped.emit()
        self._update_ui()
        self.timer_tick.emit(self.remaining, self.total)

    def _pause(self):
        self.running = not self.running
        if self.running: self._timer.start()
        else: self._timer.stop()
        self.pause_btn.setText("Resume" if not self.running else "Pause")

    def _reset(self):
        self._timer.stop(); self.running = False
        self.remaining = 0; self.total = 0; self.label = ""
        self.stack.setCurrentIndex(0)
        self.timer_stopped.emit()

    def _update_ui(self):
        r = self.remaining
        h = r // 3600; m = (r % 3600) // 60; s = r % 60
        if h > 0:
            display = f"{h}:{m:02d}:{s:02d}"
        else:
            display = f"{m:02d}:{s:02d}"
        pct = self.remaining / self.total if self.total > 0 else 0
        self.ring.set_state(pct, display)
        self.pause_btn.setText("Resume" if not self.running else "Pause")

    def _beep(self):
        try:
            import subprocess
            subprocess.Popen(["paplay", "/usr/share/sounds/alsa/Front_Center.wav"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass
        # Visual flash
        self.ring.set_state(1.0, "DONE!")

# ─────────────────────────────────────────────
# MAIN WINDOW
# ─────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("◈ HABITTRACK")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)

        self.habit_timers = {}  # per-habit timer state
        self.timer_dialog = None

        central = QWidget()
        self.setCentralWidget(central)
        self.root_layout = QVBoxLayout(central)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background:{C['bg']};")

        # Build screens
        self.welcome = WelcomeScreen()
        self.welcome.enter_app.connect(self._enter_app)

        self.topbar = TopBar()
        self.topbar.tab_changed.connect(self.switch_tab)
        self.topbar.open_clicked.connect(self._open_file)
        self.topbar.save_clicked.connect(self._save_file)
        self.topbar.add_habit.connect(self._add_habit)
        self.topbar.open_timer.connect(self._open_timer)

        self.home_sec    = HomeSection()
        self.home_sec.go_tab.connect(self.switch_tab)
        self.habits_sec  = HabitsSection()
        self.habits_sec.open_timer_for.connect(self._open_timer_for_habit)
        self.grid_sec    = GridSection()
        self.weekly_sec  = WeeklySection()

        # App container
        self.app_widget = QWidget()
        app_layout = QVBoxLayout(self.app_widget)
        app_layout.setContentsMargins(0, 0, 0, 0)
        app_layout.setSpacing(0)
        app_layout.addWidget(self.topbar)

        self.section_stack = QStackedWidget()
        for w in [self.home_sec, self.habits_sec, self.grid_sec, self.weekly_sec]:
            self.section_stack.addWidget(w)
        app_layout.addWidget(self.section_stack)

        self.stack.addWidget(self.welcome)
        self.stack.addWidget(self.app_widget)
        self.root_layout.addWidget(self.stack)

        # Show welcome first
        self.stack.setCurrentWidget(self.welcome)
        self.current_tab = "home"

        # Auto-save indicator
        if DATA_FILE.exists():
            self.topbar.set_file_status(DATA_FILE.name, True)

    def _enter_app(self, tab):
        self.stack.setCurrentWidget(self.app_widget)
        self.switch_tab(tab)

    def switch_tab(self, tab):
        self.current_tab = tab
        self.topbar.set_active(tab)
        mapping = {"home": 0, "habits": 1, "grid": 2, "weekly": 3}
        idx = mapping.get(tab, 0)
        self.section_stack.setCurrentIndex(idx)
        if tab == "habits":
            self.habits_sec.refresh(self.habit_timers)
        elif tab == "grid":
            self.grid_sec.refresh()
        elif tab == "weekly":
            self.weekly_sec.refresh()

    def _add_habit(self):
        dlg = HabitDialog(parent=self)
        if dlg.exec():
            name, icon = dlg.result_data()
            D.habits.append({"id": f"h{int(time.time()*1000)}", "name": name, "icon": icon})
            D.save()
            self.habits_sec.refresh()

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open TrackerData", str(Path.home()),
            "JSON Files (*.json)"
        )
        if path:
            ok = D.load(path)
            if ok:
                self.topbar.set_file_status(Path(path).name, True)
                self._refresh_all()
            else:
                QMessageBox.critical(self, "Error", "Could not load the selected JSON file.")

    def _save_file(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save TrackerData", str(DATA_FILE),
            "JSON Files (*.json)"
        )
        if path:
            D.save(path)
            self.topbar.set_file_status(Path(path).name, True)

    def _open_timer(self):
        if not self.timer_dialog:
            self.timer_dialog = TimerDialog(self)
            self.timer_dialog.timer_tick.connect(self._on_timer_tick)
            self.timer_dialog.timer_stopped.connect(self._on_timer_stop)
        self.timer_dialog.show()
        self.timer_dialog.raise_()

    def _on_timer_tick(self, remaining, total):
        m = remaining // 60; s = remaining % 60
        self.topbar.set_timer_running(True, f"{m:02d}:{s:02d}")

    def _on_timer_stop(self):
        self.topbar.set_timer_running(False)

    def _open_timer_for_habit(self, hid):
        # Simple countdown for habit — just use main timer with habit name
        hab = next((h for h in D.habits if h['id'] == hid), None)
        if not hab: return
        # For simplicity, open timer dialog
        self._open_timer()

    def _refresh_all(self):
        self.home_sec.update()
        self.habits_sec.refresh()
        self.grid_sec.refresh()
        self.weekly_sec.refresh()

# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("HabitTrack")

    # Dark palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, qc(C['bg']))
    palette.setColor(QPalette.ColorRole.WindowText, qc(C['text']))
    palette.setColor(QPalette.ColorRole.Base, qc(C['surface2']))
    palette.setColor(QPalette.ColorRole.AlternateBase, qc(C['surface3']))
    palette.setColor(QPalette.ColorRole.ToolTipBase, qc(C['surface2']))
    palette.setColor(QPalette.ColorRole.ToolTipText, qc(C['text']))
    palette.setColor(QPalette.ColorRole.Text, qc(C['text']))
    palette.setColor(QPalette.ColorRole.Button, qc(C['surface2']))
    palette.setColor(QPalette.ColorRole.ButtonText, qc(C['text']))
    palette.setColor(QPalette.ColorRole.Highlight, qc(C['green']))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#000000"))
    app.setPalette(palette)
    app.setStyleSheet(STYLESHEET)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
