"""Shared visual tokens for the desktop application."""
STYLE = """
QWidget { background: #10151d; color: #eaf0f5; font-family: 'Segoe UI'; font-size: 14px; }
QMainWindow, QDialog { background: #10151d; }
QLabel { background: transparent; }
QLabel#eyebrow { color: #63ddbd; font-size: 12px; font-weight: 700; letter-spacing: 2px; }
QLabel#title { font-size: 32px; font-weight: 700; }
QLabel#heading { font-size: 22px; font-weight: 600; }
QLabel#muted { color: #a1afc1; }
QLabel#value { font-size: 28px; font-weight: 700; }
QLabel#number { font-family: 'Consolas'; color: #a1afc1; font-size: 13px; }
QFrame#sidebar { background: #0b1017; border-right: 1px solid #263242; }
QFrame#panel { background: #17202b; border: 1px solid #2c3949; border-radius: 12px; }
QFrame#card { background: #17202b; border: 1px solid #354255; border-radius: 12px; }
QFrame#card:hover { border: 1px solid #63ddbd; }
QFrame#detail { background: #121b26; border-left: 1px solid #2c3949; }
QLabel#badge { background: #273545; color: #bbd2e6; border-radius: 5px; padding: 5px 9px; }
QPushButton { background: #263445; border: 1px solid #405269; border-radius: 7px; padding: 10px 14px; font-weight: 600; }
QPushButton:hover { background: #34475d; border-color: #7c9bb5; }
QPushButton:pressed { background: #425a70; }
QPushButton:focus, QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border: 2px solid #63ddbd; }
QPushButton#primary { background: #63ddbd; color: #0c2625; border: 1px solid #63ddbd; }
QPushButton#primary:hover { background: #92efd7; }
QPushButton#danger { color: #ffb3ad; background: #34232c; border-color: #74434a; }
QPushButton#nav { text-align: left; background: transparent; border: 0; padding: 14px; color: #a1afc1; }
QPushButton#nav:checked { background: #18332f; color: #77e5ca; }
QPushButton:disabled { color: #697a8a; background: #1b2430; border-color: #293545; }
QLineEdit, QComboBox, QSpinBox { background: #0c131c; border: 1px solid #3a4c60; border-radius: 6px; padding: 10px; min-height: 20px; }
QComboBox QAbstractItemView { background: #1b2734; selection-background-color: #31574f; }
QScrollArea { border: 0; }
QScrollBar:vertical { background: #111923; width: 10px; }
QScrollBar::handle:vertical { background: #45566b; border-radius: 5px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QTableWidget { background: #151e29; alternate-background-color: #1b2734; border: 1px solid #334357; gridline-color: #293646; selection-background-color: #28594f; }
QHeaderView::section { background: #243242; color: #b9c7d8; padding: 12px; border: 0; text-align: left; }
QTableWidget::item { padding: 8px; }
QCheckBox { spacing: 10px; }
QCheckBox::indicator { width: 20px; height: 20px; }
QStatusBar { background: #0b1017; color: #a1afc1; }
QProgressBar { background: #263545; border: 0; border-radius: 3px; max-height: 6px; }
QProgressBar::chunk { background: #63ddbd; border-radius: 3px; }
"""
