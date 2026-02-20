#!/usr/bin/env python3
"""
MediaRenamer — dark cinema aesthetic. Amber on obsidian.
"""

import sys
import os
import json
import shutil
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QListWidgetItem, QLabel, QFileDialog,
    QMessageBox, QProgressBar, QComboBox, QLineEdit, QTextEdit,
    QCheckBox, QDialog, QInputDialog, QFrame, QSizePolicy,
    QAbstractItemView, QStackedWidget,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import (
    QDragEnterEvent, QDropEvent, QColor, QPalette, QFont,
    QPainter, QBrush,
)

# ── Settings ──────────────────────────────────────────────────────────────────
SETTINGS_PATH = Path.home() / ".mediarenamer" / "settings.json"

def load_settings() -> dict:
    try:
        if SETTINGS_PATH.exists():
            return json.loads(SETTINGS_PATH.read_text())
    except Exception:
        pass
    return {}

def save_settings(data: dict):
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(data, indent=2))

# Inject saved keys before importing core
_s = load_settings()
for _env, _key in [("TMDB_API_KEY","tmdb_api_key"),("TVDB_API_KEY","tvdb_api_key"),("OPENSUBTITLES_API_KEY","opensubtitles_api_key")]:
    if _s.get(_key):
        os.environ.setdefault(_env, _s[_key])

try:
    from core.matcher import MediaMatcher
    from core.renamer import FileRenamer
    from core.subtitle_fetcher import SubtitleFetcher
    from core.history import RenameHistory
    from core.presets import PresetManager
    from core.artwork import ArtworkDownloader
    from core.metadata_writer import MetadataWriter
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from core.matcher import MediaMatcher
    from core.renamer import FileRenamer
    from core.subtitle_fetcher import SubtitleFetcher
    from core.history import RenameHistory
    from core.presets import PresetManager
    from core.artwork import ArtworkDownloader
    from core.metadata_writer import MetadataWriter

# ── Palette constants ─────────────────────────────────────────────────────────
C_BG        = "#0A0C12"
C_SURFACE   = "#11141D"
C_PANEL     = "#161923"
C_BORDER    = "#252A38"
C_BORDER2   = "#1E2330"
C_AMBER     = "#F59E0B"
C_AMBER_DIM = "#92600A"
C_AMBER_GLO = "#FCD34D"
C_TEXT      = "#E8EAF0"
C_TEXT_DIM  = "#6B7280"
C_TEXT_MID  = "#9CA3AF"
C_SUCCESS   = "#10B981"
C_ERROR     = "#EF4444"

STYLESHEET = """
QMainWindow, QWidget { background: #0A0C12; color: #E8EAF0; font-family: "Segoe UI","SF Pro Display","Helvetica Neue",sans-serif; font-size: 13px; }
QPushButton { background: #11141D; color: #9CA3AF; border: 1px solid #252A38; border-radius: 6px; padding: 7px 16px; font-size: 12px; font-weight: 500; }
QPushButton:hover { background: #161923; color: #E8EAF0; border-color: #92600A; }
QPushButton:pressed { background: #0A0C12; }
QPushButton:disabled { color: #252A38; border-color: #1E2330; }
QPushButton#primary { background: #F59E0B; color: #0A0A0A; border: none; font-weight: 700; font-size: 13px; padding: 9px 24px; border-radius: 7px; letter-spacing: 0.3px; }
QPushButton#primary:hover { background: #FCD34D; }
QPushButton#primary:pressed { background: #92600A; }
QPushButton#primary:disabled { background: #3A2E0A; color: #5A4A1A; }
QPushButton#ghost { background: transparent; color: #6B7280; border: 1px solid #1E2330; border-radius: 6px; padding: 6px 14px; font-size: 12px; }
QPushButton#ghost:hover { color: #F59E0B; border-color: #92600A; background: rgba(245,158,11,0.06); }
QPushButton#danger { background: transparent; color: #EF4444; border: 1px solid rgba(239,68,68,0.3); border-radius: 6px; padding: 6px 14px; }
QPushButton#danger:hover { background: rgba(239,68,68,0.1); border-color: #EF4444; }
QPushButton#icon_btn { background: transparent; border: none; color: #6B7280; padding: 4px 8px; border-radius: 4px; font-size: 14px; }
QPushButton#icon_btn:hover { color: #F59E0B; background: rgba(245,158,11,0.08); }
QLineEdit { background: #11141D; color: #E8EAF0; border: 1px solid #252A38; border-radius: 6px; padding: 7px 10px; selection-background-color: #92600A; }
QLineEdit:focus { border-color: #F59E0B; background: #161923; }
QLineEdit:disabled { color: #6B7280; background: #0A0C12; }
QComboBox { background: #11141D; color: #E8EAF0; border: 1px solid #252A38; border-radius: 6px; padding: 6px 10px; min-width: 130px; }
QComboBox:hover { border-color: #92600A; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox::down-arrow { border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 5px solid #6B7280; margin-right: 6px; }
QComboBox QAbstractItemView { background: #161923; color: #E8EAF0; border: 1px solid #252A38; selection-background-color: #92600A; outline: none; }
QListWidget { background: #11141D; color: #E8EAF0; border: 1px solid #252A38; border-radius: 8px; padding: 4px; outline: none; }
QListWidget::item { padding: 8px 12px; border-radius: 5px; color: #9CA3AF; margin: 1px 2px; }
QListWidget::item:selected { background: rgba(245,158,11,0.12); color: #E8EAF0; }
QListWidget::item:hover:!selected { background: rgba(255,255,255,0.03); color: #E8EAF0; }
QProgressBar { background: #11141D; border: none; border-radius: 4px; height: 6px; color: transparent; }
QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #92600A, stop:1 #FCD34D); border-radius: 4px; }
QScrollBar:vertical { background: transparent; width: 8px; }
QScrollBar::handle:vertical { background: #252A38; border-radius: 4px; min-height: 32px; }
QScrollBar::handle:vertical:hover { background: #92600A; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: transparent; height: 8px; }
QScrollBar::handle:horizontal { background: #252A38; border-radius: 4px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QTextEdit { background: #0A0C12; color: #6B7280; border: 1px solid #1E2330; border-radius: 6px; padding: 8px; font-family: "JetBrains Mono","Fira Code","Consolas",monospace; font-size: 11px; selection-background-color: #92600A; }
QCheckBox { color: #9CA3AF; spacing: 8px; }
QCheckBox::indicator { width: 16px; height: 16px; border-radius: 4px; border: 1px solid #252A38; background: #11141D; }
QCheckBox::indicator:checked { background: #F59E0B; border-color: #F59E0B; }
QCheckBox::indicator:hover { border-color: #92600A; }
QCheckBox:hover { color: #E8EAF0; }
QFrame[frameShape="4"], QFrame[frameShape="5"] { color: #252A38; }
QSplitter::handle { background: #252A38; width: 1px; }
QToolTip { background: #161923; color: #E8EAF0; border: 1px solid #92600A; border-radius: 4px; padding: 4px 8px; font-size: 12px; }
QDialog { background: #161923; }
QLabel#section_title { color: #6B7280; font-size: 10px; font-weight: 600; letter-spacing: 1.2px; }
QLabel#dimmed { color: #6B7280; font-size: 12px; }
"""

# ── Workers ───────────────────────────────────────────────────────────────────

class MatchWorker(QThread):
    progress   = pyqtSignal(int)
    matched    = pyqtSignal(int, object, str)
    status     = pyqtSignal(str)
    finished   = pyqtSignal(int, int)
    hard_error = pyqtSignal(str)  # first unrecoverable error (bad key, no network)

    def __init__(self, files, data_source, naming_scheme, matcher, renamer):
        super().__init__()
        self.files = files; self.data_source = data_source
        self.naming_scheme = naming_scheme; self.matcher = matcher; self.renamer = renamer
        self._hard_error_fired = False

    def run(self):
        total = len(self.files); matched_count = 0
        for i, fp in enumerate(self.files):
            try:
                mi = self.matcher.match_file(fp, self.data_source, extract_media_info=True)
                if mi:
                    nn = self.renamer.generate_new_name(fp, mi, self.naming_scheme)
                    matched_count += 1
                    self.status.emit(f"\u2713  {os.path.basename(fp)}  \u2192  {mi.get('title','?')} ({mi.get('year','')})")
                else:
                    nn = f"[no match]  {os.path.basename(fp)}"
                    self.status.emit(f"\u2717  No match: {os.path.basename(fp)}")
                self.matched.emit(i, mi, nn)
            except Exception as e:
                err = str(e)
                self.status.emit(f"\u26a0  {os.path.basename(fp)}: {err}")
                self.matched.emit(i, None, f"[error]  {os.path.basename(fp)}")
                if not self._hard_error_fired:
                    self._hard_error_fired = True
                    self.hard_error.emit(err)
            self.progress.emit(int((i+1)/total*100))
        self.finished.emit(matched_count, total)

class RenameWorker(QThread):
    progress           = pyqtSignal(int)
    status             = pyqtSignal(str)
    finished           = pyqtSignal(bool, str)
    operation_complete = pyqtSignal(str, str, dict)

    def __init__(self, files, matches, output_dir, naming_scheme, download_artwork=False, write_metadata=False):
        super().__init__()
        self.files=files; self.matches=matches; self.output_dir=output_dir
        self.naming_scheme=naming_scheme; self.download_artwork=download_artwork; self.write_metadata=write_metadata

    def run(self):
        try:
            renamer = FileRenamer(self.naming_scheme)
            artwork_dl = ArtworkDownloader() if self.download_artwork else None
            meta_wr    = MetadataWriter()    if self.write_metadata   else None
            total = len(self.files); renamed = 0
            for i,(fp,mi) in enumerate(zip(self.files,self.matches)):
                if not mi: self.progress.emit(int((i+1)/total*100)); continue
                self.status.emit(f"Renaming  {os.path.basename(fp)}")
                new_path = renamer.rename_file(fp, mi, self.output_dir)
                if new_path:
                    renamed += 1
                    if artwork_dl:
                        p = artwork_dl.download_poster(mi, os.path.dirname(new_path))
                        if p: self.status.emit(f"  Poster: {os.path.basename(p)}")
                    if meta_wr:
                        poster = None
                        if artwork_dl:
                            c = os.path.join(os.path.dirname(new_path), f"{mi.get('title','Unknown')}_poster.jpg")
                            poster = c if os.path.exists(c) else None
                        if meta_wr.write_metadata(new_path, mi, poster):
                            self.status.emit(f"  Metadata: {os.path.basename(new_path)}")
                    self.operation_complete.emit(fp, new_path, mi)
                self.progress.emit(int((i+1)/total*100))
            self.finished.emit(True, f"Done \u2014 {renamed} of {total} file(s) renamed.")
        except Exception as e:
            self.finished.emit(False, f"Error: {e}")

# ── Settings dialog ───────────────────────────────────────────────────────────

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(520)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self._build(); self._load()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20); layout.setContentsMargins(28,28,28,24)

        header = QLabel("API Keys  &  Settings")
        header.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {C_TEXT}; letter-spacing:-0.5px;")
        layout.addWidget(header)

        sub = QLabel("Keys are stored locally at  ~/.mediarenamer/settings.json  and are never transmitted to anyone except the respective APIs.")
        sub.setWordWrap(True)
        sub.setStyleSheet(f"color: {C_TEXT_DIM}; font-size: 12px;")
        layout.addWidget(sub)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{C_BORDER};")
        layout.addWidget(sep)

        # Key rows
        grid = QVBoxLayout(); grid.setSpacing(16)

        def make_row(label, placeholder, link_url, link_label):
            box = QVBoxLayout(); box.setSpacing(5)
            top = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color:{C_TEXT_MID}; font-weight:600; font-size:12px; min-width:160px;")
            top.addWidget(lbl)
            field = QLineEdit()
            field.setPlaceholderText(placeholder)
            field.setEchoMode(QLineEdit.EchoMode.Password)
            top.addWidget(field)
            box.addLayout(top)
            hint = QLabel(f'<a href="{link_url}" style="color:{C_AMBER_DIM}; text-decoration:none; font-size:11px;">\u2197 {link_label}</a>')
            hint.setOpenExternalLinks(True)
            hint.setContentsMargins(164, 0, 0, 0)
            box.addWidget(hint)
            container = QWidget(); container.setLayout(box)
            grid.addWidget(container)
            return field

        self.tmdb_field = make_row("TMDB API Key *", "Paste v3 API key here…",
            "https://www.themoviedb.org/settings/api", "Get free key at themoviedb.org")
        self.tvdb_field = make_row("TVDB API Key", "Optional",
            "https://thetvdb.com/dashboard/account/apikey", "thetvdb.com")
        self.osub_field = make_row("OpenSubtitles Key", "Optional — for subtitle fetching",
            "https://www.opensubtitles.com/", "opensubtitles.com")

        layout.addLayout(grid)

        self.show_cb = QCheckBox("Show keys while editing")
        self.show_cb.setStyleSheet(f"color:{C_TEXT_DIM}; font-size:12px;")
        self.show_cb.toggled.connect(self._toggle_echo)
        layout.addWidget(self.show_cb)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.HLine); sep2.setStyleSheet(f"color:{C_BORDER};")
        layout.addWidget(sep2)

        note = QLabel("* Required for file matching. The app will prompt you if this is missing.")
        note.setStyleSheet(f"color:{C_TEXT_DIM}; font-size:11px;")
        note.setWordWrap(True)
        layout.addWidget(note)

        btns = QHBoxLayout(); btns.addStretch()
        cancel = QPushButton("Cancel"); cancel.setObjectName("ghost"); cancel.clicked.connect(self.reject)
        save   = QPushButton("Save Keys"); save.setObjectName("primary"); save.clicked.connect(self._save)
        btns.addWidget(cancel); btns.addWidget(save)
        layout.addLayout(btns)

    def _toggle_echo(self, show):
        m = QLineEdit.EchoMode.Normal if show else QLineEdit.EchoMode.Password
        for f in (self.tmdb_field, self.tvdb_field, self.osub_field): f.setEchoMode(m)

    def _load(self):
        s = load_settings()
        self.tmdb_field.setText(s.get("tmdb_api_key",""))
        self.tvdb_field.setText(s.get("tvdb_api_key",""))
        self.osub_field.setText(s.get("opensubtitles_api_key",""))

    def _save(self):
        s = load_settings()
        s["tmdb_api_key"]          = self.tmdb_field.text().strip()
        s["tvdb_api_key"]          = self.tvdb_field.text().strip()
        s["opensubtitles_api_key"] = self.osub_field.text().strip()
        save_settings(s)
        if s["tmdb_api_key"]:          os.environ["TMDB_API_KEY"]          = s["tmdb_api_key"]
        if s["tvdb_api_key"]:          os.environ["TVDB_API_KEY"]          = s["tvdb_api_key"]
        if s["opensubtitles_api_key"]: os.environ["OPENSUBTITLES_API_KEY"] = s["opensubtitles_api_key"]
        self.accept()

# ── Drop zone ─────────────────────────────────────────────────────────────────

class DropZone(QWidget):
    files_dropped = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._hover = False

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls(): self._hover = True; self.update(); e.acceptProposedAction()
    def dragLeaveEvent(self, e): self._hover = False; self.update()
    def dropEvent(self, e):
        self._hover = False; self.update()
        self.files_dropped.emit([u.toLocalFile() for u in e.mimeData().urls()])
        e.acceptProposedAction()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        from PyQt6.QtCore import Qt as Qtc
        from PyQt6.QtGui import QPen
        pen = QPen(QColor(C_AMBER if self._hover else C_BORDER))
        pen.setStyle(Qtc.PenStyle.DashLine); pen.setWidth(1)
        p.setPen(pen)
        p.setBrush(QBrush(QColor(C_AMBER + "18" if self._hover else C_SURFACE)))
        p.drawRoundedRect(self.rect().adjusted(8,8,-8,-8), 12, 12)

        p.setPen(QColor(C_AMBER if self._hover else C_TEXT_DIM))
        f = QFont(); f.setPointSize(26); p.setFont(f)
        r = self.rect().adjusted(0,-36,0,-36)
        p.drawText(r, Qtc.AlignmentFlag.AlignCenter, "\u2B07")

        f2 = QFont(); f2.setPointSize(11); f2.setWeight(QFont.Weight.Medium); p.setFont(f2)
        p.setPen(QColor(C_TEXT if self._hover else C_TEXT_MID))
        p.drawText(self.rect().adjusted(0,20,0,20), Qtc.AlignmentFlag.AlignCenter, "Drop files or folders here")

        f3 = QFont(); f3.setPointSize(9); p.setFont(f3)
        p.setPen(QColor(C_TEXT_DIM))
        p.drawText(self.rect().adjusted(0,52,0,52), Qtc.AlignmentFlag.AlignCenter, "mp4  \u00b7  mkv  \u00b7  avi  \u00b7  mov  \u00b7  m4v  \u00b7  wmv")

# ── Main window ───────────────────────────────────────────────────────────────

class MediaRenamerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MediaRenamer")
        self.setMinimumSize(1100, 720); self.resize(1280, 820)
        self.files=[]; self.matches=[]
        self.matcher=MediaMatcher(); self.renamer=FileRenamer()
        self.history=RenameHistory(); self.preset_manager=PresetManager()
        self._build_ui()
        self.setAcceptDrops(True)

    def _build_ui(self):
        root = QWidget(); self.setCentralWidget(root)
        vbox = QVBoxLayout(root); vbox.setContentsMargins(0,0,0,0); vbox.setSpacing(0)
        vbox.addWidget(self._header())
        vbox.addWidget(self._body(), stretch=1)
        vbox.addWidget(self._footer())

    def _header(self):
        bar = QWidget(); bar.setFixedHeight(58)
        bar.setStyleSheet(f"QWidget {{ background:{C_PANEL}; border-bottom:1px solid {C_BORDER}; }}")
        h = QHBoxLayout(bar); h.setContentsMargins(20,0,16,0); h.setSpacing(12)

        dot = QLabel("\u25c6")
        dot.setStyleSheet(f"color:{C_AMBER}; font-size:16px; border:none;")
        h.addWidget(dot)

        title = QLabel("MediaRenamer")
        title.setStyleSheet(f"color:{C_TEXT}; font-size:16px; font-weight:700; letter-spacing:-0.5px; border:none;")
        h.addWidget(title)

        badge = QLabel("v1.0")
        badge.setStyleSheet(f"color:{C_AMBER_DIM}; background:rgba(245,158,11,0.1); border:1px solid {C_AMBER_DIM}; border-radius:3px; padding:1px 5px; font-size:9px; font-weight:700; letter-spacing:1px;")
        h.addWidget(badge)

        h.addStretch()

        src_lbl = QLabel("Source")
        src_lbl.setStyleSheet(f"color:{C_TEXT_DIM}; font-size:11px; border:none;")
        h.addWidget(src_lbl)
        self.data_source_combo = QComboBox()
        self.data_source_combo.addItems(["TheMovieDB","TheTVDB"])
        self.data_source_combo.setFixedWidth(130)
        h.addWidget(self.data_source_combo)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"color:{C_BORDER}; margin:10px 4px;")
        h.addWidget(sep)

        settings_btn = QPushButton("\u2699  Settings")
        settings_btn.setObjectName("ghost"); settings_btn.setFixedHeight(32)
        settings_btn.clicked.connect(self._open_settings)
        h.addWidget(settings_btn)
        return bar

    def _body(self):
        body = QWidget(); body.setStyleSheet(f"background:{C_BG};")
        h = QHBoxLayout(body); h.setContentsMargins(0,0,0,0); h.setSpacing(0)
        h.addWidget(self._left_panel(), stretch=5)
        div = QFrame(); div.setFrameShape(QFrame.Shape.VLine); div.setStyleSheet(f"color:{C_BORDER};")
        h.addWidget(div)
        h.addWidget(self._right_panel(), stretch=6)
        return body

    def _left_panel(self):
        panel = QWidget(); panel.setStyleSheet(f"background:{C_BG};")
        v = QVBoxLayout(panel); v.setContentsMargins(18,18,18,14); v.setSpacing(10)

        lbl = QLabel("INPUT FILES"); lbl.setObjectName("section_title"); v.addWidget(lbl)

        tb = QHBoxLayout(); tb.setSpacing(6)
        self.add_files_btn  = QPushButton("+ Files")
        self.add_folder_btn = QPushButton("+ Folder")
        self.clear_btn      = QPushButton("Clear"); self.clear_btn.setObjectName("danger")
        for b in (self.add_files_btn, self.add_folder_btn, self.clear_btn): b.setFixedHeight(30)
        self.add_files_btn.clicked.connect(self.add_files)
        self.add_folder_btn.clicked.connect(self.add_folder)
        self.clear_btn.clicked.connect(self.clear_files)
        tb.addWidget(self.add_files_btn); tb.addWidget(self.add_folder_btn)
        tb.addStretch(); tb.addWidget(self.clear_btn)
        v.addLayout(tb)

        self.file_stack = QStackedWidget()
        self.drop_zone  = DropZone()
        self.drop_zone.files_dropped.connect(self.add_files_list)
        self.original_list = QListWidget()
        self.original_list.setAcceptDrops(True)
        self.original_list.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
        self.original_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.file_stack.addWidget(self.drop_zone)
        self.file_stack.addWidget(self.original_list)
        self.file_stack.setCurrentIndex(0)
        v.addWidget(self.file_stack, stretch=1)

        self.file_count_lbl = QLabel("No files loaded")
        self.file_count_lbl.setObjectName("dimmed")
        self.file_count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(self.file_count_lbl)

        self.match_btn = QPushButton("\u25c8  Match Files")
        self.match_btn.setObjectName("primary"); self.match_btn.setFixedHeight(42)
        self.match_btn.clicked.connect(self.match_files)
        v.addWidget(self.match_btn)
        return panel

    def _right_panel(self):
        panel = QWidget(); panel.setStyleSheet(f"background:{C_BG};")
        v = QVBoxLayout(panel); v.setContentsMargins(18,18,18,14); v.setSpacing(10)

        # Naming scheme
        sl = QLabel("NAMING SCHEME"); sl.setObjectName("section_title"); v.addWidget(sl)
        sr = QHBoxLayout(); sr.setSpacing(8)
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(self.preset_manager.list_presets())
        self.preset_combo.setFixedWidth(160)
        self.preset_combo.currentTextChanged.connect(self.load_preset)
        self.naming_scheme_input = QLineEdit("{n}.{y}.{vf}.{vc}.{af}")
        self.naming_scheme_input.setToolTip("{n} title  \u00b7  {y} year  \u00b7  {vf} resolution  \u00b7  {vc} video codec\n{af} audio format  \u00b7  {ac} audio channels\n{s} season  \u00b7  {e} episode  \u00b7  {s00e00} S01E01  \u00b7  {t} ep title")
        sp = QPushButton("Save"); sp.setObjectName("ghost"); sp.setFixedWidth(56)
        sp.clicked.connect(self.save_current_preset)
        sr.addWidget(self.preset_combo); sr.addWidget(self.naming_scheme_input, stretch=1); sr.addWidget(sp)
        v.addLayout(sr)

        legend = QLabel("{n} title  \u00b7  {y} year  \u00b7  {vf} resolution  \u00b7  {vc} video  \u00b7  {af} audio format  \u00b7  {ac} channels  \u00b7  {s}{e} season/ep  \u00b7  {t} ep title")
        legend.setStyleSheet(f"color:{C_TEXT_DIM}; font-size:10px;")
        legend.setWordWrap(True); v.addWidget(legend)

        # Output dir
        ol = QLabel("OUTPUT DIRECTORY"); ol.setObjectName("section_title"); v.addWidget(ol)
        or_ = QHBoxLayout(); or_.setSpacing(6)
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setPlaceholderText("Leave empty to rename files in place")
        self.browse_output_btn = QPushButton("Browse\u2026"); self.browse_output_btn.setObjectName("ghost")
        self.browse_output_btn.setFixedWidth(80); self.browse_output_btn.clicked.connect(self.browse_output_dir)
        or_.addWidget(self.output_dir_input); or_.addWidget(self.browse_output_btn)
        v.addLayout(or_)

        # Options
        optl = QLabel("OPTIONS"); optl.setObjectName("section_title"); v.addWidget(optl)
        opt = QHBoxLayout(); opt.setSpacing(20)
        self.download_artwork_check = QCheckBox("Download Artwork")
        self.download_artwork_check.setToolTip("Download poster images alongside renamed files")
        self.write_metadata_check   = QCheckBox("Write Metadata")
        self.write_metadata_check.setToolTip("Embed metadata tags into MP4 files")
        opt.addWidget(self.download_artwork_check); opt.addWidget(self.write_metadata_check); opt.addStretch()
        v.addLayout(opt)

        # Preview
        pr = QHBoxLayout()
        pvl = QLabel("RENAMED PREVIEW"); pvl.setObjectName("section_title"); pr.addWidget(pvl)
        pr.addStretch()
        self.fetch_subs_btn = QPushButton("\u2b07 Subtitles")
        self.fetch_subs_btn.setObjectName("ghost"); self.fetch_subs_btn.setFixedHeight(26)
        self.fetch_subs_btn.clicked.connect(self.fetch_subtitles)
        pr.addWidget(self.fetch_subs_btn)
        v.addLayout(pr)

        self.new_names_list = QListWidget()
        v.addWidget(self.new_names_list, stretch=1)

        self.progress_bar = QProgressBar(); self.progress_bar.setVisible(False); self.progress_bar.setFixedHeight(6)
        v.addWidget(self.progress_bar)

        # Actions
        ar = QHBoxLayout(); ar.setSpacing(8)
        self.undo_btn = QPushButton("\u21a9 Undo"); self.undo_btn.setObjectName("ghost"); self.undo_btn.setFixedHeight(34)
        self.undo_btn.clicked.connect(self.undo_rename); self.undo_btn.setEnabled(self.history.can_undo())
        self.redo_btn = QPushButton("\u21aa Redo"); self.redo_btn.setObjectName("ghost"); self.redo_btn.setFixedHeight(34)
        self.redo_btn.clicked.connect(self.redo_rename); self.redo_btn.setEnabled(self.history.can_redo())
        self.rename_btn = QPushButton("\u25b6  Rename Files"); self.rename_btn.setObjectName("primary")
        self.rename_btn.setFixedHeight(42); self.rename_btn.setEnabled(False); self.rename_btn.clicked.connect(self.rename_files)
        ar.addWidget(self.undo_btn); ar.addWidget(self.redo_btn); ar.addStretch(); ar.addWidget(self.rename_btn)
        v.addLayout(ar)
        return panel

    def _footer(self):
        foot = QWidget(); foot.setFixedHeight(130)
        foot.setStyleSheet(f"QWidget {{ background:{C_BG}; border-top:1px solid {C_BORDER}; }}")
        v = QVBoxLayout(foot); v.setContentsMargins(18,10,18,10); v.setSpacing(6)
        row = QHBoxLayout()
        fl = QLabel("ACTIVITY LOG"); fl.setObjectName("section_title"); row.addWidget(fl)
        row.addStretch()
        clr = QPushButton("Clear log"); clr.setObjectName("icon_btn"); clr.setFixedHeight(22)
        clr.clicked.connect(lambda: self.status_text.clear()); row.addWidget(clr)
        v.addLayout(row)
        self.status_text = QTextEdit(); self.status_text.setReadOnly(True); v.addWidget(self.status_text)
        return foot

    # ── Drag & drop ───────────────────────────────────────────────
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls(): e.acceptProposedAction()
    def dropEvent(self, e):
        self.add_files_list([u.toLocalFile() for u in e.mimeData().urls()])
        e.acceptProposedAction()

    # ── File management ───────────────────────────────────────────
    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self,"Select Media Files","",
            "Video Files (*.mp4 *.mkv *.avi *.mov *.m4v *.mpg *.mpeg *.flv *.wmv);;All Files (*)")
        if files: self.add_files_list(files)

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self,"Select Folder")
        if not folder: return
        exts = {'.mp4','.mkv','.avi','.mov','.m4v','.mpg','.mpeg','.flv','.wmv'}
        found = [str(p) for p in Path(folder).rglob("*") if p.suffix.lower() in exts]
        if found: self.add_files_list(found)
        else: self._log("\u26a0  No media files found in selected folder.")

    def add_files_list(self, paths):
        added = 0
        for path in paths:
            if os.path.isdir(path):
                exts = {'.mp4','.mkv','.avi','.mov','.m4v','.mpg','.mpeg','.flv','.wmv'}
                for p in Path(path).rglob("*"):
                    if p.suffix.lower() in exts and str(p) not in self.files:
                        self.files.append(str(p)); self._add_file_item(str(p)); added+=1
            elif path not in self.files:
                self.files.append(path); self._add_file_item(path); added+=1
        if added: self._log(f"+ Added {added} file(s)"); self._refresh_ui()

    def _add_file_item(self, path):
        item = QListWidgetItem(os.path.basename(path))
        item.setToolTip(path); item.setForeground(QColor(C_TEXT_MID))
        self.original_list.addItem(item)

    def _refresh_ui(self):
        n = len(self.files)
        self.file_count_lbl.setText(f"{n} file{'s' if n!=1 else ''} loaded")
        self.file_stack.setCurrentIndex(1 if n > 0 else 0)

    def clear_files(self):
        self.files.clear(); self.matches.clear()
        self.original_list.clear(); self.new_names_list.clear()
        self.rename_btn.setEnabled(False)
        self._refresh_ui(); self._log("\u2014 List cleared")

    def browse_output_dir(self):
        d = QFileDialog.getExistingDirectory(self,"Select Output Directory")
        if d: self.output_dir_input.setText(d)

    def _open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            # Reinitialise matcher so it reads the freshly-saved env var.
            # _read_tmdb_key() in matcher.py always reads os.environ at call-time,
            # so a new MediaMatcher() picks up the key saved by SettingsDialog._save().
            self.matcher = MediaMatcher()
            key_preview = (os.environ.get("TMDB_API_KEY","") or "")
            if key_preview and key_preview not in ("YOUR_TMDB_API_KEY_HERE","YOUR_TMDB_API_KEY"):
                self._log(f"\u2713  API key active: ...{key_preview[-6:]}")
            else:
                self._log("\u26a0  No valid API key detected after save — check Settings.")

    # ── Matching ──────────────────────────────────────────────────
    def match_files(self):
        if not self.files:
            QMessageBox.warning(self,"No Files","Please add media files first."); return
        _BAD_KEYS = {"", "YOUR_TMDB_API_KEY_HERE", "YOUR_TMDB_API_KEY"}
        key = os.environ.get("TMDB_API_KEY","").strip()
        if key in _BAD_KEYS:
            reply = QMessageBox.warning(self,"TMDB API Key Missing",
                "No TMDB API key found.\n\nGo to Settings \u2192 paste your key to enable matching.\nGet a free key at: https://www.themoviedb.org/settings/api\n\nOpen Settings now?",
                QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes: self._open_settings()
            return

        self._log(f"\u27f3  Matching {len(self.files)} file(s)\u2026")
        self.match_btn.setEnabled(False); self.rename_btn.setEnabled(False)
        self.progress_bar.setVisible(True); self.progress_bar.setValue(0)
        self.matches = [None]*len(self.files)
        self.new_names_list.clear()
        for _ in self.files:
            item = QListWidgetItem("\u2026"); item.setForeground(QColor(C_TEXT_DIM))
            self.new_names_list.addItem(item)

        self.match_worker = MatchWorker(self.files, self.data_source_combo.currentText(),
            self.naming_scheme_input.text(), self.matcher, self.renamer)
        self.match_worker.progress.connect(self.progress_bar.setValue)
        self.match_worker.status.connect(self._log)
        self.match_worker.matched.connect(self._on_match_result)
        self.match_worker.finished.connect(self._on_match_finished)
        self.match_worker.hard_error.connect(self._on_match_hard_error)
        self.match_worker.start()

    def _on_match_result(self, idx, mi, nn):
        self.matches[idx] = mi
        item = self.new_names_list.item(idx); item.setText(nn)
        item.setForeground(QColor(C_TEXT if mi else (C_ERROR if "[error]" in nn else C_TEXT_DIM)))

    def _on_match_hard_error(self, error_msg: str):
        """Called when the matcher raises an unrecoverable error (bad key, no network)."""
        self.progress_bar.setVisible(False)
        self.match_btn.setEnabled(True)
        # Stop the worker so we don't spam errors for every remaining file
        if hasattr(self, 'match_worker'):
            self.match_worker.quit()

        if "401" in error_msg or "Unauthorized" in error_msg or "invalid" in error_msg.lower():
            reply = QMessageBox.critical(
                self, "Invalid API Key",
                "TMDB rejected the API key (401 Unauthorized).\n\n"
                "Please double-check your key in Settings — copy it directly\n"
                "from https://www.themoviedb.org/settings/api\n\n"
                "Open Settings now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._open_settings()
        elif "Network error" in error_msg or "Connection" in error_msg:
            QMessageBox.critical(
                self, "Network Error",
                f"Cannot reach TMDB:\n{error_msg}\n\n"
                "If running in Docker, make sure the container has internet access.\n"
                "Try: docker run --network=host ..."
            )
        else:
            QMessageBox.critical(self, "Match Error", error_msg)

    def _on_match_finished(self, matched, total):
        self.progress_bar.setVisible(False); self.match_btn.setEnabled(True)
        self.rename_btn.setEnabled(matched > 0)
        self._log(f"\u2713  Matched {matched}/{total} files.")

    # ── Subtitles ─────────────────────────────────────────────────
    def fetch_subtitles(self):
        if not self.files: QMessageBox.warning(self,"No Files","Please add files first."); return
        self._log("\u27f3  Fetching subtitles\u2026"); fetcher = SubtitleFetcher()
        for fp in self.files:
            try:
                sub = fetcher.fetch_subtitle(fp)
                self._log(f"\u2b07  {os.path.basename(sub)}" if sub else f"\u2717  No subtitle: {os.path.basename(fp)}")
            except Exception as e:
                self._log(f"\u26a0  {os.path.basename(fp)}: {e}")

    # ── Rename ────────────────────────────────────────────────────
    def rename_files(self):
        if not self.files or not any(self.matches):
            QMessageBox.warning(self,"Nothing to Rename","Please match files first."); return
        matched = sum(1 for m in self.matches if m)
        if QMessageBox.question(self,"Confirm Rename",
            f"Rename {matched} matched file(s)?\nThis operation can be undone.",
            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        self.progress_bar.setVisible(True); self.progress_bar.setValue(0)
        self.rename_btn.setEnabled(False); self.match_btn.setEnabled(False)
        self.worker = RenameWorker(self.files, self.matches,
            self.output_dir_input.text().strip() or None,
            self.naming_scheme_input.text(),
            download_artwork=self.download_artwork_check.isChecked(),
            write_metadata=self.write_metadata_check.isChecked())
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.status.connect(self._log)
        self.worker.operation_complete.connect(self._on_op_complete)
        self.worker.finished.connect(self._rename_finished)
        self.worker.start()

    def _on_op_complete(self, orig, new, mi):
        self.history.add_operation(orig, new, mi); self._update_undo_redo()

    def _rename_finished(self, ok, msg):
        self.progress_bar.setVisible(False); self.rename_btn.setEnabled(True); self.match_btn.setEnabled(True)
        self._log(("\u2713  " if ok else "\u2717  ") + msg); self._update_undo_redo()
        if not ok: QMessageBox.critical(self,"Rename Error",msg)

    # ── Undo / Redo ───────────────────────────────────────────────
    def _update_undo_redo(self):
        self.undo_btn.setEnabled(self.history.can_undo()); self.redo_btn.setEnabled(self.history.can_redo())

    def undo_rename(self):
        op = self.history.undo()
        if not op: return
        try:
            src,dst = op['new_path'],op['original_path']
            if os.path.exists(src): shutil.move(src,dst); self._log(f"\u21a9  Undone: {os.path.basename(src)}"); self._update_undo_redo()
            else: QMessageBox.warning(self,"Undo Failed",f"File not found:\n{src}")
        except Exception as e: QMessageBox.critical(self,"Error",f"Undo failed: {e}")

    def redo_rename(self):
        op = self.history.redo()
        if not op: return
        try:
            src,dst = op['original_path'],op['new_path']
            if os.path.exists(src):
                os.makedirs(os.path.dirname(dst),exist_ok=True); shutil.move(src,dst)
                self._log(f"\u21aa  Redone: {os.path.basename(dst)}"); self._update_undo_redo()
            else: QMessageBox.warning(self,"Redo Failed",f"Source no longer exists:\n{src}")
        except Exception as e: QMessageBox.critical(self,"Error",f"Redo failed: {e}")

    # ── Presets ───────────────────────────────────────────────────
    def load_preset(self, name):
        s = self.preset_manager.get_preset(name)
        if s: self.naming_scheme_input.setText(s)

    def save_current_preset(self):
        scheme = self.naming_scheme_input.text().strip()
        if not scheme: QMessageBox.warning(self,"Empty Scheme","Enter a naming scheme first."); return
        name,ok = QInputDialog.getText(self,"Save Preset","Preset name:")
        if ok and name:
            self.preset_manager.save_preset(name,scheme)
            self.preset_combo.clear(); self.preset_combo.addItems(self.preset_manager.list_presets())
            self.preset_combo.setCurrentText(name); self._log(f"\u2713  Preset saved: {name}")

    def _log(self, msg):
        self.status_text.append(msg)
        self.status_text.verticalScrollBar().setValue(self.status_text.verticalScrollBar().maximum())

# ── Entry ─────────────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MediaRenamer")
    app.setStyle("Fusion")

    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window,        QColor(C_BG))
    pal.setColor(QPalette.ColorRole.WindowText,    QColor(C_TEXT))
    pal.setColor(QPalette.ColorRole.Base,          QColor(C_SURFACE))
    pal.setColor(QPalette.ColorRole.AlternateBase, QColor(C_PANEL))
    pal.setColor(QPalette.ColorRole.Text,          QColor(C_TEXT))
    pal.setColor(QPalette.ColorRole.Button,        QColor(C_PANEL))
    pal.setColor(QPalette.ColorRole.ButtonText,    QColor(C_TEXT))
    pal.setColor(QPalette.ColorRole.Highlight,     QColor(C_AMBER_DIM))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#000"))
    pal.setColor(QPalette.ColorRole.ToolTipBase,   QColor(C_PANEL))
    pal.setColor(QPalette.ColorRole.ToolTipText,   QColor(C_TEXT))
    app.setPalette(pal)
    app.setStyleSheet(STYLESHEET)

    win = MediaRenamerApp()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
