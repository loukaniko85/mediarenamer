#!/usr/bin/env python3
"""
MediaRenamer — dark cinema aesthetic. Amber on obsidian.
"""

import sys
import base64
import os
import json
import shutil
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QListWidgetItem, QLabel, QFileDialog,
    QMessageBox, QProgressBar, QComboBox, QLineEdit, QTextEdit,
    QCheckBox, QDialog, QInputDialog, QFrame, QSizePolicy,
    QAbstractItemView, QStackedWidget, QMenu, QRadioButton,
    QButtonGroup, QToolButton,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import (
    QDragEnterEvent, QDropEvent, QColor, QPalette, QFont,
    QPainter, QBrush, QAction,
)

# ── Settings persistence ──────────────────────────────────────────────────────
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

# ── Embedded app icon ────────────────────────────────────────────────────────
_ICON_B64 = "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"

def _app_icon():
    """Return a QIcon from the embedded base64 PNG."""
    from PyQt6.QtGui import QPixmap, QIcon
    from PyQt6.QtCore import QByteArray
    data = QByteArray(base64.b64decode(_ICON_B64))
    pm = QPixmap(); pm.loadFromData(data, "PNG")
    return QIcon(pm)

# ── Palette ───────────────────────────────────────────────────────────────────
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
C_BLUE      = "#3B82F6"
C_BLUE_DIM  = "#1D4ED8"
C_GREEN     = "#22C55E"
C_GREEN_DIM = "#15803D"

STYLESHEET = """
QMainWindow, QWidget { background: #0A0C12; color: #E8EAF0;
    font-family: "Segoe UI","SF Pro Display","Helvetica Neue",sans-serif; font-size: 13px; }

/* ── Base button ── */
QPushButton { background: #11141D; color: #9CA3AF; border: 1px solid #252A38;
    border-radius: 6px; padding: 7px 16px; font-size: 12px; font-weight: 500; }
QPushButton:hover { background: #161923; color: #E8EAF0; border-color: #92600A; }
QPushButton:pressed { background: #0A0C12; }
QPushButton:disabled { color: #252A38; border-color: #1E2330; }

/* ── Match button — vivid blue ── */
QPushButton#match {
    background: #3B82F6; color: #FFFFFF; border: none;
    font-weight: 700; font-size: 13px; padding: 9px 24px;
    border-radius: 7px; letter-spacing: 0.3px; }
QPushButton#match:hover { background: #60A5FA; }
QPushButton#match:pressed { background: #1D4ED8; }
QPushButton#match:disabled { background: #1e3a5f; color: #3a5a8a; }

/* ── Rename button — vivid green ── */
QPushButton#rename {
    background: #22C55E; color: #FFFFFF; border: none;
    font-weight: 700; font-size: 13px; padding: 9px 24px;
    border-radius: 7px; letter-spacing: 0.3px; }
QPushButton#rename:hover { background: #4ADE80; }
QPushButton#rename:pressed { background: #15803D; }
QPushButton#rename:disabled { background: #14532d; color: #166534; }

/* ── Ghost button ── */
QPushButton#ghost { background: transparent; color: #6B7280; border: 1px solid #1E2330;
    border-radius: 6px; padding: 6px 14px; font-size: 12px; }
QPushButton#ghost:hover { color: #F59E0B; border-color: #92600A; background: rgba(245,158,11,0.06); }

/* ── Danger button ── */
QPushButton#danger { background: transparent; color: #EF4444;
    border: 1px solid rgba(239,68,68,0.3); border-radius: 6px; padding: 6px 14px; }
QPushButton#danger:hover { background: rgba(239,68,68,0.1); border-color: #EF4444; }

/* ── Icon button ── */
QPushButton#icon_btn { background: transparent; border: none; color: #6B7280;
    padding: 4px 8px; border-radius: 4px; font-size: 14px; }
QPushButton#icon_btn:hover { color: #F59E0B; background: rgba(245,158,11,0.08); }

/* ── Dry-run button ── */
QPushButton#dryrun { background: rgba(245,158,11,0.1); color: #F59E0B;
    border: 1px solid #92600A; border-radius: 6px; padding: 7px 16px; font-size: 12px; font-weight: 600; }
QPushButton#dryrun:hover { background: rgba(245,158,11,0.18); }
QPushButton#dryrun:disabled { color: #92600A; background: rgba(245,158,11,0.04); }

/* ── Inputs ── */
QLineEdit { background: #11141D; color: #E8EAF0; border: 1px solid #252A38;
    border-radius: 6px; padding: 7px 10px; selection-background-color: #92600A; }
QLineEdit:focus { border-color: #F59E0B; background: #161923; }
QLineEdit:disabled { color: #6B7280; background: #0A0C12; }
QLineEdit#search { padding-left: 28px; }

QComboBox { background: #11141D; color: #E8EAF0; border: 1px solid #252A38;
    border-radius: 6px; padding: 6px 10px; min-width: 130px; }
QComboBox:hover { border-color: #92600A; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox::down-arrow { border-left: 4px solid transparent; border-right: 4px solid transparent;
    border-top: 5px solid #6B7280; margin-right: 6px; }
QComboBox QAbstractItemView { background: #161923; color: #E8EAF0;
    border: 1px solid #252A38; selection-background-color: #92600A; outline: none; }

/* ── Radio buttons ── */
QRadioButton { color: #9CA3AF; spacing: 6px; }
QRadioButton::indicator { width: 14px; height: 14px; border-radius: 7px;
    border: 1px solid #252A38; background: #11141D; }
QRadioButton::indicator:checked { background: #F59E0B; border-color: #F59E0B; }
QRadioButton:hover { color: #E8EAF0; }

/* ── Lists ── */
QListWidget { background: #11141D; color: #E8EAF0; border: 1px solid #252A38;
    border-radius: 8px; padding: 4px; outline: none; }
QListWidget::item { padding: 6px 10px; border-radius: 5px; color: #9CA3AF; margin: 1px 2px; }
QListWidget::item:selected { background: rgba(245,158,11,0.12); color: #E8EAF0; }
QListWidget::item:hover:!selected { background: rgba(255,255,255,0.03); color: #E8EAF0; }

/* ── Progress ── */
QProgressBar { background: #11141D; border: none; border-radius: 4px; height: 6px; color: transparent; }
QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
    stop:0 #92600A, stop:1 #FCD34D); border-radius: 4px; }

/* ── Scrollbars ── */
QScrollBar:vertical { background: transparent; width: 8px; }
QScrollBar::handle:vertical { background: #252A38; border-radius: 4px; min-height: 32px; }
QScrollBar::handle:vertical:hover { background: #92600A; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: transparent; height: 8px; }
QScrollBar::handle:horizontal { background: #252A38; border-radius: 4px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ── Log / text area ── */
QTextEdit { background: #0A0C12; color: #6B7280; border: 1px solid #1E2330;
    border-radius: 6px; padding: 8px;
    font-family: "JetBrains Mono","Fira Code","Consolas",monospace; font-size: 11px;
    selection-background-color: #92600A; }

/* ── Checkboxes ── */
QCheckBox { color: #9CA3AF; spacing: 8px; }
QCheckBox::indicator { width: 16px; height: 16px; border-radius: 4px;
    border: 1px solid #252A38; background: #11141D; }
QCheckBox::indicator:checked { background: #F59E0B; border-color: #F59E0B; }
QCheckBox::indicator:hover { border-color: #92600A; }
QCheckBox:hover { color: #E8EAF0; }

/* ── Misc ── */
QFrame[frameShape="4"], QFrame[frameShape="5"] { color: #252A38; }
QSplitter::handle { background: #252A38; width: 1px; }
QToolTip { background: #161923; color: #E8EAF0; border: 1px solid #92600A;
    border-radius: 4px; padding: 4px 8px; font-size: 12px; }
QDialog { background: #161923; }
QMenu { background: #161923; color: #E8EAF0; border: 1px solid #252A38;
    border-radius: 6px; padding: 4px; }
QMenu::item { padding: 6px 18px; border-radius: 4px; }
QMenu::item:selected { background: rgba(245,158,11,0.12); color: #E8EAF0; }
QMenu::separator { height: 1px; background: #252A38; margin: 4px 8px; }
QLabel#section_title { color: #6B7280; font-size: 10px; font-weight: 600; letter-spacing: 1.2px; }
QLabel#dimmed { color: #6B7280; font-size: 12px; }
QLabel#stat_ok  { color: #22C55E; font-size: 11px; font-weight: 600; }
QLabel#stat_err { color: #EF4444; font-size: 11px; font-weight: 600; }
QLabel#stat_dim { color: #6B7280; font-size: 11px; }
"""

# ── Workers ───────────────────────────────────────────────────────────────────

class MatchWorker(QThread):
    progress   = pyqtSignal(int)
    matched    = pyqtSignal(int, object, str)
    status     = pyqtSignal(str)
    finished   = pyqtSignal(int, int)
    hard_error = pyqtSignal(str)

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

    def __init__(self, files, matches, output_dir, naming_scheme,
                 download_artwork=False, write_metadata=False,
                 dry_run=False, copy_mode=False):
        super().__init__()
        self.files=files; self.matches=matches; self.output_dir=output_dir
        self.naming_scheme=naming_scheme; self.download_artwork=download_artwork
        self.write_metadata=write_metadata; self.dry_run=dry_run; self.copy_mode=copy_mode

    def run(self):
        try:
            renamer     = FileRenamer(self.naming_scheme)
            artwork_dl  = ArtworkDownloader() if self.download_artwork else None
            meta_wr     = MetadataWriter()    if self.write_metadata   else None
            total       = len(self.files)
            renamed     = 0
            skipped     = 0
            conflicts   = 0

            mode_label = "DRY RUN" if self.dry_run else ("COPY" if self.copy_mode else "MOVE")

            for i, (fp, mi) in enumerate(zip(self.files, self.matches)):
                if not mi:
                    self.progress.emit(int((i+1)/total*100))
                    continue

                new_name  = renamer.generate_new_name(fp, mi, self.naming_scheme)
                dest_base = Path(self.output_dir) if self.output_dir else Path(fp).parent
                dest      = dest_base / new_name
                dest.parent.mkdir(parents=True, exist_ok=True)

                if dest.exists() and dest != Path(fp):
                    conflicts += 1
                    self.status.emit(f"\u26a0  [{mode_label}] Conflict — destination exists: {dest.name}")
                    self.progress.emit(int((i+1)/total*100))
                    continue

                if self.dry_run:
                    self.status.emit(f"\u25b6  [DRY RUN] {os.path.basename(fp)} \u2192 {dest.name}")
                    renamed += 1
                    self.progress.emit(int((i+1)/total*100))
                    continue

                try:
                    if self.copy_mode:
                        shutil.copy2(fp, str(dest))
                    else:
                        shutil.move(fp, str(dest))

                    renamed += 1
                    self.status.emit(f"\u2713  [{mode_label}] {os.path.basename(fp)} \u2192 {dest.name}")

                    if artwork_dl:
                        p = artwork_dl.download_poster(mi, str(dest.parent))
                        if p: self.status.emit(f"   \U0001f5bc  Poster: {os.path.basename(p)}")

                    if meta_wr:
                        poster = None
                        if artwork_dl:
                            c = dest.parent / f"{mi.get('title','Unknown')}_poster.jpg"
                            poster = str(c) if c.exists() else None
                        if meta_wr.write_metadata(str(dest), mi, poster):
                            self.status.emit(f"   \U0001f3f7  Metadata written")

                    self.operation_complete.emit(fp, str(dest), mi)

                except Exception as e:
                    skipped += 1
                    self.status.emit(f"\u2717  Failed: {os.path.basename(fp)} — {e}")

                self.progress.emit(int((i+1)/total*100))

            parts = [f"{renamed} renamed"]
            if conflicts: parts.append(f"{conflicts} conflict(s) skipped")
            if skipped:   parts.append(f"{skipped} error(s)")
            suffix = " (dry run — no files changed)" if self.dry_run else ""
            self.finished.emit(True, "Done — " + ", ".join(parts) + suffix)

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
        from PyQt6.QtWidgets import QTabWidget
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)

        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: none; background: #161923; }
            QTabBar::tab { background: #0A0C12; color: #6B7280; padding: 10px 22px;
                           border: none; font-size: 12px; font-weight: 600; }
            QTabBar::tab:selected { background: #161923; color: #F59E0B;
                                    border-bottom: 2px solid #F59E0B; }
            QTabBar::tab:hover:!selected { color: #E8EAF0; background: #11141D; }
        """)

        # ── API Keys tab ──────────────────────────────────────────────────────
        keys_widget = QWidget()
        layout = QVBoxLayout(keys_widget)
        layout.setSpacing(18); layout.setContentsMargins(28,24,28,20)

        sub = QLabel("Keys are stored locally in  ~/.mediarenamer/settings.json  and sent only to their respective APIs.")
        sub.setWordWrap(True); sub.setStyleSheet("color: #6B7280; font-size: 12px;")
        layout.addWidget(sub)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine); sep.setStyleSheet("color: #252A38;")
        layout.addWidget(sep)

        grid = QVBoxLayout(); grid.setSpacing(14)

        def make_row(label, placeholder, link_url, link_label):
            box = QVBoxLayout(); box.setSpacing(4)
            top = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet("color: #9CA3AF; font-weight:600; font-size:12px; min-width:160px;")
            top.addWidget(lbl)
            field = QLineEdit(); field.setPlaceholderText(placeholder)
            field.setEchoMode(QLineEdit.EchoMode.Password)
            top.addWidget(field)
            box.addLayout(top)
            hint = QLabel(f'<a href="{link_url}" style="color:#92600A; text-decoration:none; font-size:11px;">\u2197 {link_label}</a>')
            hint.setOpenExternalLinks(True); hint.setContentsMargins(164,0,0,0)
            box.addWidget(hint)
            container = QWidget(); container.setLayout(box)
            grid.addWidget(container)
            return field

        self.tmdb_field = make_row("TMDB API Key *", "Paste v3 API key here\u2026",
            "https://www.themoviedb.org/settings/api", "Get free key at themoviedb.org")
        self.tvdb_field = make_row("TVDB API Key", "Optional",
            "https://thetvdb.com/dashboard/account/apikey", "thetvdb.com")
        self.osub_field = make_row("OpenSubtitles Key", "Optional \u2014 for subtitle fetching",
            "https://www.opensubtitles.com/", "opensubtitles.com")
        layout.addLayout(grid)

        self.show_cb = QCheckBox("Show keys while editing")
        self.show_cb.setStyleSheet("color: #6B7280; font-size:12px;")
        self.show_cb.toggled.connect(self._toggle_echo)
        layout.addWidget(self.show_cb)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.HLine); sep2.setStyleSheet("color: #252A38;")
        layout.addWidget(sep2)
        note = QLabel("* Required for file matching.")
        note.setStyleSheet("color: #6B7280; font-size:11px;"); layout.addWidget(note)

        btns = QHBoxLayout(); btns.addStretch()
        cancel = QPushButton("Cancel"); cancel.setObjectName("ghost"); cancel.clicked.connect(self.reject)
        save = QPushButton("Save Keys"); save.setObjectName("match"); save.clicked.connect(self._save)
        btns.addWidget(cancel); btns.addWidget(save)
        layout.addLayout(btns)
        tabs.addTab(keys_widget, "\U0001f511  API Keys")

        # ── About tab ─────────────────────────────────────────────────────────
        about_widget = QWidget()
        av = QVBoxLayout(about_widget)
        av.setContentsMargins(40, 30, 40, 30); av.setSpacing(0)
        av.addStretch(1)

        logo = QLabel("\u25c6")
        logo.setStyleSheet("color: #F59E0B; font-size: 48px; border: none;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        av.addWidget(logo)

        app_name = QLabel("MediaRenamer")
        app_name.setStyleSheet("color: #E8EAF0; font-size: 26px; font-weight: 800; letter-spacing: -0.5px; border: none;")
        app_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        av.addWidget(app_name)

        version_lbl = QLabel("v1.1  —  The open-source FileBot alternative")
        version_lbl.setStyleSheet("color: #6B7280; font-size: 13px; border: none;")
        version_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        av.addWidget(version_lbl)

        av.addSpacing(28)
        sep_about = QFrame(); sep_about.setFrameShape(QFrame.Shape.HLine)
        sep_about.setStyleSheet("color: #252A38; margin: 0 60px;")
        av.addWidget(sep_about)
        av.addSpacing(24)

        credit = QLabel(
            "Built by <b style=\'color:#F59E0B;\'>loukaniko</b>"
            " with a little help from his <b style=\'color:#6B7280;\'>LLM</b>"
        )
        credit.setStyleSheet("color: #9CA3AF; font-size: 14px; border: none;")
        credit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        av.addWidget(credit)
        av.addSpacing(14)

        desc = QLabel(
            "Rename and organise your movies, TV shows and Anime.\n"
            "Powered by TheMovieDB, TheTVDB and AniDB."
        )
        desc.setStyleSheet("color: #6B7280; font-size: 12px; border: none;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        av.addWidget(desc)
        av.addSpacing(24)

        features = QLabel(
            "\u2713  Batch rename with naming scheme presets\n"
            "\u2713  Dry-run preview before committing\n"
            "\u2713  Copy or move — keep your originals\n"
            "\u2713  REST API with Swagger UI\n"
            "\u2713  Async batch jobs with webhook callbacks\n"
            "\u2713  Checksum generation (MD5/SHA1/SHA256)\n"
            "\u2713  Artwork download & MP4 metadata embed\n"
            "\u2713  Subtitle fetching via OpenSubtitles\n"
            "\u2713  Undo / redo — nothing is permanent"
        )
        features.setStyleSheet("color: #6B7280; font-size: 11px; line-height: 1.8; border: none;")
        features.setAlignment(Qt.AlignmentFlag.AlignCenter)
        av.addWidget(features)
        av.addSpacing(24)

        # Show API link only when running inside Docker (API is only available there)
        _in_docker  = bool(os.environ.get("RUNNING_IN_DOCKER"))
        _in_appimage = bool(os.environ.get("APPIMAGE"))
        if _in_docker:
            _api_port = os.environ.get("API_PORT", "8060")
            api_lbl = QLabel(
                f'REST API + Swagger: <a href="http://localhost:{_api_port}/docs" style="color:#F59E0B;">localhost:{_api_port}/docs</a>'
                f'  <span style="color:#4B5563;">(or your-host-ip:{_api_port}/docs)</span>'
            )
            api_lbl.setStyleSheet("color: #6B7280; font-size: 11px; border: none;")
            api_lbl.setOpenExternalLinks(True)
            api_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            av.addWidget(api_lbl)
        elif _in_appimage:
            api_lbl = QLabel("Running as AppImage — GUI only (no REST API)")
            api_lbl.setStyleSheet("color: #4B5563; font-size: 11px; border: none; font-style: italic;")
            api_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            av.addWidget(api_lbl)
        else:
            api_lbl = QLabel(
                'Run via Docker to enable the REST API '
                '(<a href="https://github.com/loukaniko/mediarenamer" style="color:#92600A;">docs</a>)'
            )
            api_lbl.setStyleSheet("color: #4B5563; font-size: 11px; border: none;")
            api_lbl.setOpenExternalLinks(True)
            api_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            av.addWidget(api_lbl)

        av.addStretch(2)
        close_btn = QPushButton("Close"); close_btn.setObjectName("ghost")
        close_btn.setFixedWidth(100); close_btn.clicked.connect(self.reject)
        close_row = QHBoxLayout(); close_row.addStretch(); close_row.addWidget(close_btn); close_row.addStretch()
        av.addLayout(close_row)
        tabs.addTab(about_widget, "\u2139  About")

        outer.addWidget(tabs)

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
        p.drawText(self.rect().adjusted(0,-36,0,-36), Qtc.AlignmentFlag.AlignCenter, "\u2B07")
        f2 = QFont(); f2.setPointSize(11); f2.setWeight(QFont.Weight.Medium); p.setFont(f2)
        p.setPen(QColor(C_TEXT if self._hover else C_TEXT_MID))
        p.drawText(self.rect().adjusted(0,20,0,20), Qtc.AlignmentFlag.AlignCenter, "Drop files or folders here")
        f3 = QFont(); f3.setPointSize(9); p.setFont(f3)
        p.setPen(QColor(C_TEXT_DIM))
        p.drawText(self.rect().adjusted(0,52,0,52), Qtc.AlignmentFlag.AlignCenter,
                   "mp4  \u00b7  mkv  \u00b7  avi  \u00b7  mov  \u00b7  m4v  \u00b7  wmv")


# ── Batch Jobs Dialog ─────────────────────────────────────────────────────────

class JobPollerThread(QThread):
    """Polls the API for job list updates every 2 seconds."""
    jobs_updated = pyqtSignal(list)
    error        = pyqtSignal(str)

    def __init__(self, api_base: str):
        super().__init__()
        self._api_base = api_base
        self._running  = True

    def stop(self): self._running = False

    def run(self):
        import time as _time
        while self._running:
            try:
                import urllib.request, json as _json
                with urllib.request.urlopen(f"{self._api_base}/jobs", timeout=3) as r:
                    self.jobs_updated.emit(_json.loads(r.read()))
            except Exception as e:
                self.error.emit(str(e))
            _time.sleep(2)


class BatchJobsDialog(QDialog):
    """
    Batch Jobs panel — submit directory jobs to the FastAPI backend
    and monitor their live progress without leaving the GUI.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Batch Jobs")
        self.setMinimumSize(860, 600)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self._api_port = os.environ.get("API_PORT", "8060")
        self._api_base = f"http://localhost:{self._api_port}/api/v1"
        self._selected_job_id: str = ""
        self._poller = None
        self._build()
        self._start_poller()

    def closeEvent(self, e):
        if self._poller:
            self._poller.stop(); self._poller.quit()
        super().closeEvent(e)

    # ── Build UI ──────────────────────────────────────────────────────────────
    def _build(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0); outer.setSpacing(0)

        # ── Top bar ───────────────────────────────────────────────────────────
        topbar = QWidget(); topbar.setStyleSheet(f"background:{C_PANEL}; border-bottom:1px solid {C_BORDER};")
        topbar.setFixedHeight(52)
        th = QHBoxLayout(topbar); th.setContentsMargins(18,0,18,0); th.setSpacing(10)
        ttl = QLabel("\u25a6  Batch Jobs")
        ttl.setStyleSheet(f"font-size:15px; font-weight:700; color:{C_TEXT};")
        th.addWidget(ttl)
        api_badge = QLabel(f"API: {self._api_base}")
        api_badge.setStyleSheet(f"color:{C_TEXT_DIM}; font-size:11px;")
        th.addWidget(api_badge)
        th.addStretch()
        refresh_btn = QPushButton("\u21bb Refresh"); refresh_btn.setObjectName("ghost")
        refresh_btn.setFixedHeight(28); refresh_btn.clicked.connect(self._refresh)
        th.addWidget(refresh_btn)
        close_btn = QPushButton("Close"); close_btn.setObjectName("ghost")
        close_btn.setFixedHeight(28); close_btn.clicked.connect(self.close)
        th.addWidget(close_btn)
        outer.addWidget(topbar)

        # ── Main split ────────────────────────────────────────────────────────
        splitter_widget = QWidget(); splitter_widget.setStyleSheet(f"background:{C_BG};")
        sh = QHBoxLayout(splitter_widget); sh.setContentsMargins(0,0,0,0); sh.setSpacing(0)

        # Left — submit form
        left = QWidget(); left.setFixedWidth(320)
        left.setStyleSheet(f"background:{C_SURFACE}; border-right:1px solid {C_BORDER};")
        lv = QVBoxLayout(left); lv.setContentsMargins(16,16,16,12); lv.setSpacing(10)

        submit_lbl = QLabel("SUBMIT NEW JOB"); submit_lbl.setObjectName("section_title")
        lv.addWidget(submit_lbl)

        dir_lbl = QLabel("Directory or file paths (one per line):")
        dir_lbl.setStyleSheet(f"color:{C_TEXT_MID}; font-size:11px;")
        lv.addWidget(dir_lbl)

        self._paths_edit = QTextEdit()
        self._paths_edit.setPlaceholderText("/media/Downloads/Movies\n/media/Downloads/TV")
        self._paths_edit.setFixedHeight(90)
        self._paths_edit.setStyleSheet(
            f"background:{C_BG}; color:{C_TEXT}; border:1px solid {C_BORDER}; "
            f"border-radius:6px; padding:6px; font-size:12px; font-family:monospace;"
        )
        lv.addWidget(self._paths_edit)

        browse_row = QHBoxLayout(); browse_row.setSpacing(6)
        browse_dir_btn = QPushButton("\U0001f4c2  Browse dir"); browse_dir_btn.setObjectName("ghost")
        browse_dir_btn.setFixedHeight(28)
        browse_dir_btn.clicked.connect(self._browse_dir)
        browse_row.addWidget(browse_dir_btn); browse_row.addStretch()
        lv.addLayout(browse_row)

        scheme_lbl = QLabel("Naming scheme:"); scheme_lbl.setStyleSheet(f"color:{C_TEXT_MID}; font-size:11px;")
        lv.addWidget(scheme_lbl)
        self._scheme_edit = QLineEdit("{n} ({y})")
        lv.addWidget(self._scheme_edit)

        outdir_lbl = QLabel("Output directory (blank = rename in place):")
        outdir_lbl.setStyleSheet(f"color:{C_TEXT_MID}; font-size:11px;")
        lv.addWidget(outdir_lbl)
        od_row = QHBoxLayout(); od_row.setSpacing(6)
        self._outdir_edit = QLineEdit()
        self._outdir_edit.setPlaceholderText("/media/Movies")
        od_row.addWidget(self._outdir_edit)
        browse_out_btn = QPushButton("\u2026"); browse_out_btn.setObjectName("ghost")
        browse_out_btn.setFixedWidth(32); browse_out_btn.setFixedHeight(32)
        browse_out_btn.clicked.connect(self._browse_out)
        od_row.addWidget(browse_out_btn)
        lv.addLayout(od_row)

        src_lbl2 = QLabel("Data source:"); src_lbl2.setStyleSheet(f"color:{C_TEXT_MID}; font-size:11px;")
        lv.addWidget(src_lbl2)
        self._src_combo = QComboBox()
        self._src_combo.addItems(["TheMovieDB","TheTVDB","AniDB"])
        lv.addWidget(self._src_combo)

        op_lbl = QLabel("Operation:"); op_lbl.setStyleSheet(f"color:{C_TEXT_MID}; font-size:11px;")
        lv.addWidget(op_lbl)
        op_row = QHBoxLayout(); op_row.setSpacing(12)
        self._move_radio2 = QRadioButton("Move"); self._move_radio2.setChecked(True)
        self._copy_radio2 = QRadioButton("Copy")
        self._bg2 = QButtonGroup(self); self._bg2.addButton(self._move_radio2); self._bg2.addButton(self._copy_radio2)
        op_row.addWidget(self._move_radio2); op_row.addWidget(self._copy_radio2); op_row.addStretch()
        lv.addLayout(op_row)

        opts_row = QHBoxLayout(); opts_row.setSpacing(12)
        self._dry_run_cb2  = QCheckBox("Dry Run"); self._dry_run_cb2.setStyleSheet(f"color:{C_AMBER}; font-size:11px;")
        self._artwork_cb2  = QCheckBox("Artwork")
        self._meta_cb2     = QCheckBox("Metadata")
        opts_row.addWidget(self._dry_run_cb2); opts_row.addWidget(self._artwork_cb2)
        opts_row.addWidget(self._meta_cb2); opts_row.addStretch()
        lv.addLayout(opts_row)

        webhook_lbl = QLabel("Webhook URL (optional):")
        webhook_lbl.setStyleSheet(f"color:{C_TEXT_MID}; font-size:11px;")
        lv.addWidget(webhook_lbl)
        self._webhook_edit = QLineEdit()
        self._webhook_edit.setPlaceholderText("https://your-server/hooks/mediarenamer")
        lv.addWidget(self._webhook_edit)

        lv.addStretch()

        self._submit_btn = QPushButton("\u25b6  Submit Job")
        self._submit_btn.setObjectName("match"); self._submit_btn.setFixedHeight(40)
        self._submit_btn.clicked.connect(self._submit_job)
        lv.addWidget(self._submit_btn)
        sh.addWidget(left)

        # Right — job list + detail
        right = QWidget(); right.setStyleSheet(f"background:{C_BG};")
        rv = QVBoxLayout(right); rv.setContentsMargins(12,12,12,12); rv.setSpacing(8)

        list_lbl = QLabel("JOBS"); list_lbl.setObjectName("section_title"); rv.addWidget(list_lbl)

        self._job_list = QListWidget()
        self._job_list.setFixedHeight(180)
        self._job_list.currentRowChanged.connect(self._on_job_selected)
        rv.addWidget(self._job_list)

        # Job detail area
        detail_lbl = QLabel("JOB DETAIL"); detail_lbl.setObjectName("section_title"); rv.addWidget(detail_lbl)

        self._progress2 = QProgressBar(); self._progress2.setVisible(False); self._progress2.setFixedHeight(6)
        rv.addWidget(self._progress2)

        self._detail_lbl = QLabel("Select a job to view its log and results.")
        self._detail_lbl.setStyleSheet(f"color:{C_TEXT_DIM}; font-size:11px; padding:4px;")
        self._detail_lbl.setWordWrap(True)
        rv.addWidget(self._detail_lbl)

        self._job_log = QTextEdit(); self._job_log.setReadOnly(True)
        rv.addWidget(self._job_log, stretch=1)

        cancel_row = QHBoxLayout(); cancel_row.setSpacing(8)
        self._cancel_btn = QPushButton("\u2715  Cancel Job"); self._cancel_btn.setObjectName("danger")
        self._cancel_btn.setFixedHeight(32); self._cancel_btn.setEnabled(False)
        self._cancel_btn.clicked.connect(self._cancel_job)
        self._delete_btn = QPushButton("\u1f5d1  Delete Record"); self._delete_btn.setObjectName("ghost")
        self._delete_btn.setFixedHeight(32); self._delete_btn.setEnabled(False)
        self._delete_btn.clicked.connect(self._delete_job)
        cancel_row.addWidget(self._cancel_btn); cancel_row.addWidget(self._delete_btn); cancel_row.addStretch()
        rv.addLayout(cancel_row)
        sh.addWidget(right)

        outer.addWidget(splitter_widget, stretch=1)

        # Status bar
        self._statusbar = QLabel("  Ready")
        self._statusbar.setStyleSheet(f"background:{C_PANEL}; color:{C_TEXT_DIM}; "
                                       f"font-size:11px; border-top:1px solid {C_BORDER}; padding:4px 12px;")
        self._statusbar.setFixedHeight(26)
        outer.addWidget(self._statusbar)

    # ── Poller ────────────────────────────────────────────────────────────────
    def _start_poller(self):
        self._poller = JobPollerThread(self._api_base)
        self._poller.jobs_updated.connect(self._on_jobs_updated)
        self._poller.error.connect(lambda e: self._statusbar.setText(f"  API error: {e}"))
        self._poller.start()

    def _refresh(self):
        try:
            import urllib.request, json as _json
            with urllib.request.urlopen(f"{self._api_base}/jobs", timeout=3) as r:
                self._on_jobs_updated(_json.loads(r.read()))
        except Exception as e:
            self._statusbar.setText(f"  Refresh failed: {e}")

    def _on_jobs_updated(self, jobs: list):
        prev = self._selected_job_id
        self._job_list.clear()
        for job in jobs:
            status = job.get("status","?")
            pct    = job.get("progress",{}).get("percent", 0)
            renamed = job.get("renamed_count", 0)
            total   = job.get("file_count", 0)
            icons   = {"pending":"\u23f3","running":"\u27f3","completed":"\u2713","failed":"\u2717","cancelled":"\u2014"}
            icon    = icons.get(status,"?")
            colours = {"pending": C_TEXT_DIM, "running": C_AMBER, "completed": C_SUCCESS, "failed": C_ERROR, "cancelled": C_TEXT_DIM}
            text    = f"{icon}  [{status.upper():12}]  {renamed}/{total} files  {pct:.0f}%  — id:{job['job_id'][:8]}…"
            item    = QListWidgetItem(text)
            item.setForeground(QColor(colours.get(status, C_TEXT_MID)))
            item.setData(Qt.ItemDataRole.UserRole, job)
            self._job_list.addItem(item)
        # Restore selection
        for i in range(self._job_list.count()):
            d = self._job_list.item(i).data(Qt.ItemDataRole.UserRole)
            if d and d.get("job_id") == prev:
                self._job_list.setCurrentRow(i)
                break
        n = self._job_list.count()
        self._statusbar.setText(f"  {n} job{'s' if n!=1 else ''} — auto-refreshing every 2s")

    def _on_job_selected(self, row):
        if row < 0: return
        item = self._job_list.item(row)
        if not item: return
        job = item.data(Qt.ItemDataRole.UserRole)
        if not job: return
        self._selected_job_id = job.get("job_id","")
        status  = job.get("status","?")
        pct     = job.get("progress",{}).get("percent",0)
        renamed = job.get("renamed_count",0)
        errors  = job.get("error_count",0)
        confl   = job.get("conflict_count",0)
        total   = job.get("file_count",0)
        self._detail_lbl.setText(
            f"Job: {self._selected_job_id}   Status: {status.upper()}   "
            f"{renamed}/{total} renamed   {errors} errors   {confl} conflicts"
        )
        running = status == "running"
        self._progress2.setVisible(running or status == "pending")
        self._progress2.setValue(int(pct))
        self._cancel_btn.setEnabled(status in ("pending","running"))
        self._delete_btn.setEnabled(status not in ("pending","running"))
        # Fetch detail log
        try:
            import urllib.request, json as _json
            with urllib.request.urlopen(f"{self._api_base}/jobs/{self._selected_job_id}", timeout=3) as r:
                detail = _json.loads(r.read())
            log_lines = detail.get("log", [])
            self._job_log.setPlainText("\n".join(log_lines))
            self._job_log.verticalScrollBar().setValue(self._job_log.verticalScrollBar().maximum())
        except Exception as e:
            self._job_log.setPlainText(f"Could not fetch log: {e}")

    def _browse_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Select Directory to Process")
        if d:
            cur = self._paths_edit.toPlainText().strip()
            self._paths_edit.setPlainText((cur + "\n" + d).strip())

    def _browse_out(self):
        d = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if d: self._outdir_edit.setText(d)

    def _submit_job(self):
        raw = self._paths_edit.toPlainText().strip()
        if not raw:
            QMessageBox.warning(self, "No Paths", "Enter at least one directory or file path.")
            return
        files = [p.strip() for p in raw.splitlines() if p.strip()]
        payload = {
            "files":            files,
            "naming_scheme":    self._scheme_edit.text().strip() or "{n} ({y})",
            "output_dir":       self._outdir_edit.text().strip() or None,
            "operation":        "copy" if self._copy_radio2.isChecked() else "move",
            "data_source":      self._src_combo.currentText(),
            "dry_run":          self._dry_run_cb2.isChecked(),
            "download_artwork": self._artwork_cb2.isChecked(),
            "write_metadata":   self._meta_cb2.isChecked(),
            "webhook_url":      self._webhook_edit.text().strip() or None,
        }
        try:
            import urllib.request, json as _json
            data = _json.dumps(payload).encode()
            req  = urllib.request.Request(f"{self._api_base}/jobs",
                                          data=data, method="POST",
                                          headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as r:
                job = _json.loads(r.read())
            self._statusbar.setText(f"  Job submitted: {job['job_id']}")
            QTimer.singleShot(500, self._refresh)
        except Exception as e:
            QMessageBox.critical(self, "Submit Failed", str(e))

    def _cancel_job(self):
        if not self._selected_job_id: return
        try:
            import urllib.request
            req = urllib.request.Request(
                f"{self._api_base}/jobs/{self._selected_job_id}/cancel",
                method="POST", data=b""
            )
            urllib.request.urlopen(req, timeout=5)
            self._statusbar.setText(f"  Cancelled: {self._selected_job_id[:8]}…")
            QTimer.singleShot(300, self._refresh)
        except Exception as e:
            QMessageBox.critical(self, "Cancel Failed", str(e))

    def _delete_job(self):
        if not self._selected_job_id: return
        try:
            import urllib.request
            req = urllib.request.Request(
                f"{self._api_base}/jobs/{self._selected_job_id}",
                method="DELETE"
            )
            urllib.request.urlopen(req, timeout=5)
            self._selected_job_id = ""
            self._job_log.clear()
            self._detail_lbl.setText("Job deleted.")
            QTimer.singleShot(300, self._refresh)
        except Exception as e:
            QMessageBox.critical(self, "Delete Failed", str(e))


# ── Main window ───────────────────────────────────────────────────────────────

class MediaRenamerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MediaRenamer")
        self.setWindowIcon(_app_icon())
        self.setMinimumSize(960, 660); self.resize(1380, 840)
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

    # ── Header ────────────────────────────────────────────────────
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
        badge = QLabel("v1.1")
        badge.setStyleSheet(f"color:{C_AMBER_DIM}; background:rgba(245,158,11,0.1); border:1px solid {C_AMBER_DIM}; border-radius:3px; padding:1px 5px; font-size:9px; font-weight:700; letter-spacing:1px;")
        h.addWidget(badge)
        h.addStretch()

        # Stats bar
        self.stat_matched = QLabel("—")
        self.stat_matched.setObjectName("stat_dim")
        self.stat_matched.setToolTip("Matched files")
        h.addWidget(self.stat_matched)

        sep0 = QFrame(); sep0.setFrameShape(QFrame.Shape.VLine)
        sep0.setStyleSheet(f"color:{C_BORDER}; margin:14px 2px;")
        h.addWidget(sep0)

        src_lbl = QLabel("Source")
        src_lbl.setStyleSheet(f"color:{C_TEXT_DIM}; font-size:11px; border:none;")
        h.addWidget(src_lbl)
        self.data_source_combo = QComboBox()
        self.data_source_combo.addItems(["TheMovieDB","TheTVDB","AniDB"])
        self.data_source_combo.setFixedWidth(120)
        h.addWidget(self.data_source_combo)

        lang_lbl = QLabel("Lang")
        lang_lbl.setStyleSheet(f"color:{C_TEXT_DIM}; font-size:11px; border:none;")
        h.addWidget(lang_lbl)
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["en","fr","de","es","it","ja","ko","zh","pt","ru","nl","pl","sv","da","fi","nb"])
        self.lang_combo.setFixedWidth(60)
        self.lang_combo.setToolTip("Preferred language for metadata (ISO 639-1)")
        h.addWidget(self.lang_combo)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"color:{C_BORDER}; margin:10px 4px;")
        h.addWidget(sep)

        settings_btn = QPushButton("\u2699  Settings")
        settings_btn.setObjectName("ghost"); settings_btn.setFixedHeight(32)
        settings_btn.clicked.connect(self._open_settings)
        h.addWidget(settings_btn)

        # Batch jobs button — only shown when API is available (Docker)
        if os.environ.get("RUNNING_IN_DOCKER"):
            sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.VLine)
            sep2.setStyleSheet(f"color:{C_BORDER}; margin:10px 4px;")
            h.addWidget(sep2)
            self.jobs_btn = QPushButton("\u25a6  Batch Jobs")
            self.jobs_btn.setObjectName("ghost"); self.jobs_btn.setFixedHeight(32)
            self.jobs_btn.setToolTip("Submit and monitor async batch rename jobs via the REST API")
            self.jobs_btn.clicked.connect(self._open_jobs)
            h.addWidget(self.jobs_btn)

        return bar

    # ── Body ──────────────────────────────────────────────────────
    def _body(self):
        body = QWidget(); body.setStyleSheet(f"background:{C_BG};")
        h = QHBoxLayout(body); h.setContentsMargins(0,0,0,0); h.setSpacing(0)
        h.addWidget(self._left_panel(), stretch=5)
        div = QFrame(); div.setFrameShape(QFrame.Shape.VLine); div.setStyleSheet(f"color:{C_BORDER};")
        h.addWidget(div)
        h.addWidget(self._right_panel(), stretch=6)
        return body

    # ── Left panel ────────────────────────────────────────────────
    def _left_panel(self):
        panel = QWidget(); panel.setStyleSheet(f"background:{C_BG};")
        v = QVBoxLayout(panel); v.setContentsMargins(18,18,18,14); v.setSpacing(8)

        lbl = QLabel("INPUT FILES"); lbl.setObjectName("section_title"); v.addWidget(lbl)

        # Toolbar
        tb = QHBoxLayout(); tb.setSpacing(6)
        self.add_files_btn  = QPushButton("+ Files")
        self.add_folder_btn = QPushButton("+ Folder")
        self.remove_sel_btn = QPushButton("\u2212 Remove")
        self.remove_sel_btn.setObjectName("danger")
        self.clear_btn      = QPushButton("Clear All"); self.clear_btn.setObjectName("danger")
        for b in (self.add_files_btn, self.add_folder_btn, self.remove_sel_btn, self.clear_btn):
            b.setFixedHeight(30)
        self.add_files_btn.clicked.connect(self.add_files)
        self.add_folder_btn.clicked.connect(self.add_folder)
        self.remove_sel_btn.clicked.connect(self.remove_selected)
        self.clear_btn.clicked.connect(self.clear_files)
        tb.addWidget(self.add_files_btn); tb.addWidget(self.add_folder_btn)
        tb.addStretch()
        tb.addWidget(self.remove_sel_btn)
        tb.addWidget(self.clear_btn)
        v.addLayout(tb)

        # Search filter
        search_container = QWidget()
        search_container.setStyleSheet("background:transparent;")
        sl = QHBoxLayout(search_container); sl.setContentsMargins(0,0,0,0); sl.setSpacing(0)
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("\U0001f50d  Filter files…")
        self.filter_input.setObjectName("search")
        self.filter_input.textChanged.connect(self._apply_filter)
        sl.addWidget(self.filter_input)
        v.addWidget(search_container)

        # File list stack
        self.file_stack = QStackedWidget()
        self.drop_zone  = DropZone()
        self.drop_zone.files_dropped.connect(self.add_files_list)
        self.original_list = QListWidget()
        self.original_list.setAcceptDrops(True)
        self.original_list.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
        self.original_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.original_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.original_list.customContextMenuRequested.connect(self._file_context_menu)
        self.file_stack.addWidget(self.drop_zone)
        self.file_stack.addWidget(self.original_list)
        self.file_stack.setCurrentIndex(0)
        v.addWidget(self.file_stack, stretch=1)

        self.file_count_lbl = QLabel("No files loaded")
        self.file_count_lbl.setObjectName("dimmed")
        self.file_count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(self.file_count_lbl)

        # Match button — BLUE
        self.match_btn = QPushButton("\u25c8  Match Files")
        self.match_btn.setObjectName("match")
        self.match_btn.setFixedHeight(44)
        self.match_btn.clicked.connect(self.match_files)
        v.addWidget(self.match_btn)
        return panel

    # ── Right panel ───────────────────────────────────────────────
    def _right_panel(self):
        panel = QWidget(); panel.setStyleSheet(f"background:{C_BG};")
        v = QVBoxLayout(panel); v.setContentsMargins(18,18,18,14); v.setSpacing(8)

        # Naming scheme
        sl = QLabel("NAMING SCHEME"); sl.setObjectName("section_title"); v.addWidget(sl)
        sr = QHBoxLayout(); sr.setSpacing(8)
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(self.preset_manager.list_presets())
        self.preset_combo.setFixedWidth(160)
        self.preset_combo.currentTextChanged.connect(self.load_preset)
        self.naming_scheme_input = QLineEdit("{n}.{y}.{vf}.{vc}.{af}")
        self.naming_scheme_input.setToolTip(
            "{n} title  \u00b7  {y} year  \u00b7  {vf} resolution  \u00b7  {vc} video codec\n"
            "{af} audio format  \u00b7  {ac} audio channels\n"
            "{s} season  \u00b7  {e} episode  \u00b7  {s00e00} S01E01  \u00b7  {t} ep title"
        )
        sp = QPushButton("Save"); sp.setObjectName("ghost"); sp.setFixedWidth(56)
        sp.clicked.connect(self.save_current_preset)
        sr.addWidget(self.preset_combo); sr.addWidget(self.naming_scheme_input, stretch=1); sr.addWidget(sp)
        v.addLayout(sr)

        legend = QLabel("{n} title  \u00b7  {y} year  \u00b7  {vf} res  \u00b7  {vc} video  \u00b7  {af} audio  \u00b7  {ac} channels  \u00b7  {s}{e} season/ep  \u00b7  {t} ep title")
        legend.setStyleSheet(f"color:{C_TEXT_DIM}; font-size:10px;")
        legend.setWordWrap(True); v.addWidget(legend)

        # Output dir
        ol = QLabel("OUTPUT DIRECTORY"); ol.setObjectName("section_title"); v.addWidget(ol)
        or_ = QHBoxLayout(); or_.setSpacing(6)
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setPlaceholderText("Leave empty to rename files in place")
        browse_btn = QPushButton("Browse\u2026"); browse_btn.setObjectName("ghost")
        browse_btn.setFixedWidth(80); browse_btn.clicked.connect(self.browse_output_dir)
        or_.addWidget(self.output_dir_input); or_.addWidget(browse_btn)
        v.addLayout(or_)

        # Options row
        optl = QLabel("OPTIONS"); optl.setObjectName("section_title"); v.addWidget(optl)
        opt = QHBoxLayout(); opt.setSpacing(16)

        self.download_artwork_check = QCheckBox("Download Artwork")
        self.download_artwork_check.setToolTip("Download poster images alongside renamed files")
        self.write_metadata_check   = QCheckBox("Write Metadata")
        self.write_metadata_check.setToolTip("Embed metadata tags into MP4 files")
        self.dry_run_check          = QCheckBox("Dry Run (preview only)")
        self.dry_run_check.setToolTip("Show what WOULD be renamed without changing any files")
        self.dry_run_check.setStyleSheet(f"color:{C_AMBER}; spacing:8px;")

        opt.addWidget(self.download_artwork_check)
        opt.addWidget(self.write_metadata_check)
        opt.addWidget(self.dry_run_check)
        opt.addStretch()
        v.addLayout(opt)

        # Copy vs Move
        mode_row = QHBoxLayout(); mode_row.setSpacing(16)
        mode_lbl = QLabel("File operation:")
        mode_lbl.setStyleSheet(f"color:{C_TEXT_DIM}; font-size:11px;")
        self.move_radio = QRadioButton("Move (rename in place)")
        self.copy_radio = QRadioButton("Copy (keep originals)")
        self.move_radio.setChecked(True)
        self._mode_group = QButtonGroup(self)
        self._mode_group.addButton(self.move_radio)
        self._mode_group.addButton(self.copy_radio)
        mode_row.addWidget(mode_lbl)
        mode_row.addWidget(self.move_radio)
        mode_row.addWidget(self.copy_radio)
        mode_row.addStretch()
        v.addLayout(mode_row)

        # Preview list
        pr = QHBoxLayout()
        pvl = QLabel("RENAMED PREVIEW"); pvl.setObjectName("section_title"); pr.addWidget(pvl)
        pr.addStretch()
        self.fetch_subs_btn = QPushButton("\u2b07 Subtitles")
        self.fetch_subs_btn.setObjectName("ghost"); self.fetch_subs_btn.setFixedHeight(26)
        self.fetch_subs_btn.clicked.connect(self.fetch_subtitles)
        pr.addWidget(self.fetch_subs_btn)
        v.addLayout(pr)

        self.new_names_list = QListWidget()
        self.new_names_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.new_names_list.customContextMenuRequested.connect(self._preview_context_menu)
        v.addWidget(self.new_names_list, stretch=1)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False); self.progress_bar.setFixedHeight(6)
        v.addWidget(self.progress_bar)

        # Actions
        ar = QHBoxLayout(); ar.setSpacing(8)
        self.undo_btn = QPushButton("\u21a9 Undo"); self.undo_btn.setObjectName("ghost"); self.undo_btn.setFixedHeight(36)
        self.undo_btn.clicked.connect(self.undo_rename); self.undo_btn.setEnabled(self.history.can_undo())
        self.redo_btn = QPushButton("\u21aa Redo"); self.redo_btn.setObjectName("ghost"); self.redo_btn.setFixedHeight(36)
        self.redo_btn.clicked.connect(self.redo_rename); self.redo_btn.setEnabled(self.history.can_redo())

        # Rename button — GREEN
        self.rename_btn = QPushButton("\u25b6  Rename Files")
        self.rename_btn.setObjectName("rename")
        self.rename_btn.setFixedHeight(44)
        self.rename_btn.setEnabled(False)
        self.rename_btn.clicked.connect(self.rename_files)

        ar.addWidget(self.undo_btn); ar.addWidget(self.redo_btn)
        ar.addStretch()
        ar.addWidget(self.rename_btn)
        v.addLayout(ar)
        return panel

    # ── Footer ────────────────────────────────────────────────────
    def _footer(self):
        foot = QWidget(); foot.setFixedHeight(120)
        foot.setStyleSheet(f"QWidget {{ background:{C_BG}; border-top:1px solid {C_BORDER}; }}")
        v = QVBoxLayout(foot); v.setContentsMargins(18,8,18,8); v.setSpacing(4)
        row = QHBoxLayout()
        fl = QLabel("ACTIVITY LOG"); fl.setObjectName("section_title"); row.addWidget(fl)
        row.addStretch()
        clr = QPushButton("Clear"); clr.setObjectName("icon_btn"); clr.setFixedHeight(22)
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

    # ── Context menus ─────────────────────────────────────────────
    def _file_context_menu(self, pos):
        item = self.original_list.itemAt(pos)
        menu = QMenu(self)
        if item:
            open_act = QAction("\U0001f4c2  Open containing folder", self)
            open_act.triggered.connect(lambda: self._open_folder(item))
            menu.addAction(open_act)
            menu.addSeparator()
            rem_act = QAction("\u2212  Remove selected", self)
            rem_act.triggered.connect(self.remove_selected)
            menu.addAction(rem_act)
        add_act = QAction("+  Add files\u2026", self)
        add_act.triggered.connect(self.add_files)
        menu.addAction(add_act)
        folder_act = QAction("+  Add folder\u2026", self)
        folder_act.triggered.connect(self.add_folder)
        menu.addAction(folder_act)
        menu.exec(self.original_list.mapToGlobal(pos))

    def _preview_context_menu(self, pos):
        idx = self.new_names_list.indexAt(pos).row()
        if idx < 0 or idx >= len(self.files): return
        menu = QMenu(self)
        rematch_act = QAction("\U0001f50d  Search manually for this file", self)
        rematch_act.triggered.connect(lambda: self._manual_search(idx))
        menu.addAction(rematch_act)
        clear_act = QAction("\u2715  Clear match for this file", self)
        clear_act.triggered.connect(lambda: self._clear_match(idx))
        menu.addAction(clear_act)
        menu.exec(self.new_names_list.mapToGlobal(pos))

    def _open_folder(self, item):
        idx = self.original_list.row(item)
        if 0 <= idx < len(self.files):
            folder = str(Path(self.files[idx]).parent)
            import subprocess, sys
            if sys.platform == "darwin":
                subprocess.run(["open", folder])
            elif sys.platform == "win32":
                subprocess.run(["explorer", folder])
            else:
                subprocess.run(["xdg-open", folder])

    def _manual_search(self, idx):
        """Let user type a manual search query for a specific file."""
        fp = self.files[idx]
        query, ok = QInputDialog.getText(
            self, "Manual Search",
            f"Search query for:\n{os.path.basename(fp)}\n\n"
            "Enter title (and optionally year, e.g. 'Inception 2010'):"
        )
        if not ok or not query.strip(): return

        # Simple search — strip year from end if provided
        import re
        parts = query.strip().rsplit(None, 1)
        year = None
        title = query.strip()
        if len(parts) == 2 and re.match(r'^\d{4}$', parts[1]):
            title = parts[0]; year = int(parts[1])

        results = self.matcher.search_movies(title, year) or self.matcher.search_tv_shows(title)
        if not results:
            QMessageBox.information(self, "No Results", f"No results found for '{query}'.")
            return

        # Show picker
        choices = [f"{r['title']} ({r.get('year','?')})  [{r['type']}]" for r in results]
        choice, ok = QInputDialog.getItem(self, "Select Match", "Choose the correct match:", choices, 0, False)
        if not ok: return

        chosen = results[choices.index(choice)]
        self.matches[idx] = chosen
        new_name = self.renamer.generate_new_name(fp, chosen, self.naming_scheme_input.text())
        item = self.new_names_list.item(idx)
        item.setText(new_name)
        item.setForeground(QColor(C_SUCCESS))
        self._log(f"\u270f  Manual match: {os.path.basename(fp)} \u2192 {chosen['title']}")
        matched = sum(1 for m in self.matches if m)
        self.rename_btn.setEnabled(matched > 0)
        self._update_stats()

    def _clear_match(self, idx):
        self.matches[idx] = None
        item = self.new_names_list.item(idx)
        item.setText(f"[cleared]  {os.path.basename(self.files[idx])}")
        item.setForeground(QColor(C_TEXT_DIM))
        matched = sum(1 for m in self.matches if m)
        self.rename_btn.setEnabled(matched > 0)
        self._update_stats()

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
        if found: self.add_files_list(sorted(found))
        else: self._log("\u26a0  No media files found in selected folder.")

    def add_files_list(self, paths):
        added = 0
        for path in paths:
            if os.path.isdir(path):
                exts = {'.mp4','.mkv','.avi','.mov','.m4v','.mpg','.mpeg','.flv','.wmv'}
                for p in sorted(Path(path).rglob("*")):
                    if p.suffix.lower() in exts and str(p) not in self.files:
                        self.files.append(str(p)); self._add_file_item(str(p)); added+=1
            elif path not in self.files:
                self.files.append(path); self._add_file_item(path); added+=1
        if added:
            self.matches.extend([None]*added)
            self._log(f"+ Added {added} file(s)"); self._refresh_ui()

    def _add_file_item(self, path):
        item = QListWidgetItem(os.path.basename(path))
        item.setToolTip(path); item.setForeground(QColor(C_TEXT_MID))
        self.original_list.addItem(item)

    def remove_selected(self):
        rows = sorted([self.original_list.row(i) for i in self.original_list.selectedItems()], reverse=True)
        if not rows: return
        for r in rows:
            self.original_list.takeItem(r)
            self.files.pop(r)
            if r < len(self.matches): self.matches.pop(r)
            if r < self.new_names_list.count(): self.new_names_list.takeItem(r)
        self._log(f"\u2212  Removed {len(rows)} file(s)")
        self._refresh_ui(); self._update_stats()

    def _apply_filter(self, text):
        text = text.lower()
        for i in range(self.original_list.count()):
            item = self.original_list.item(i)
            item.setHidden(text not in item.text().lower())

    def _refresh_ui(self):
        n = len(self.files)
        self.file_count_lbl.setText(f"{n} file{'s' if n!=1 else ''} loaded")
        self.file_stack.setCurrentIndex(1 if n > 0 else 0)
        if n == 0: self.stat_matched.setText("—"); self.stat_matched.setObjectName("stat_dim")

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
            self.matcher = MediaMatcher()
            key_preview = os.environ.get("TMDB_API_KEY","").strip()
            _bad = {"","YOUR_TMDB_API_KEY_HERE","YOUR_TMDB_API_KEY"}
            if key_preview and key_preview not in _bad:
                self._log(f"\u2713  API key active: \u2026{key_preview[-6:]}")
            else:
                self._log("\u26a0  No valid TMDB API key — check Settings.")

    def _open_jobs(self):
        """Open the Batch Jobs dialog (Docker only — requires API)."""
        dlg = BatchJobsDialog(self)
        dlg.exec()

    def _update_stats(self):
        total   = len(self.files)
        matched = sum(1 for m in self.matches if m)
        if total == 0:
            self.stat_matched.setText("—")
            self.stat_matched.setObjectName("stat_dim")
        elif matched == total:
            self.stat_matched.setText(f"\u2713 {matched}/{total} matched")
            self.stat_matched.setObjectName("stat_ok")
        elif matched > 0:
            self.stat_matched.setText(f"{matched}/{total} matched")
            self.stat_matched.setObjectName("stat_dim")
        else:
            self.stat_matched.setText(f"\u2717 0/{total} matched")
            self.stat_matched.setObjectName("stat_err")
        # Force style refresh
        self.stat_matched.style().unpolish(self.stat_matched)
        self.stat_matched.style().polish(self.stat_matched)

    # ── Matching ──────────────────────────────────────────────────
    def match_files(self):
        if not self.files:
            QMessageBox.warning(self,"No Files","Please add media files first."); return
        _BAD_KEYS = {"","YOUR_TMDB_API_KEY_HERE","YOUR_TMDB_API_KEY"}
        key = os.environ.get("TMDB_API_KEY","").strip()
        if key in _BAD_KEYS:
            reply = QMessageBox.warning(self,"TMDB API Key Missing",
                "No TMDB API key found.\n\nGo to Settings \u2192 paste your key.\n"
                "Get a free key at: https://www.themoviedb.org/settings/api\n\nOpen Settings now?",
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

        self.match_worker = MatchWorker(
            self.files, self.data_source_combo.currentText(),
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
        if mi:
            item.setForeground(QColor(C_TEXT))
        elif "[error]" in nn:
            item.setForeground(QColor(C_ERROR))
        else:
            item.setForeground(QColor(C_TEXT_DIM))
        self._update_stats()

    def _on_match_hard_error(self, error_msg):
        self.progress_bar.setVisible(False)
        self.match_btn.setEnabled(True)
        if hasattr(self,'match_worker'): self.match_worker.quit()
        if "401" in error_msg or "Unauthorized" in error_msg or "invalid" in error_msg.lower():
            reply = QMessageBox.critical(self,"Invalid API Key",
                "TMDB rejected the API key (401 Unauthorized).\n\n"
                "Copy your key directly from:\nhttps://www.themoviedb.org/settings/api\n\n"
                "Open Settings now?",
                QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes: self._open_settings()
        elif "Network" in error_msg or "Connection" in error_msg:
            QMessageBox.critical(self,"Network Error",
                f"Cannot reach TMDB:\n{error_msg}\n\n"
                "In Docker, ensure the container has internet:\n"
                "  docker run --network=host ...")
        else:
            QMessageBox.critical(self,"Match Error", error_msg)

    def _on_match_finished(self, matched, total):
        self.progress_bar.setVisible(False)
        self.match_btn.setEnabled(True)
        self.rename_btn.setEnabled(matched > 0)
        self._log(f"\u2713  Matched {matched}/{total} files.")
        self._update_stats()

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
        dry_run = self.dry_run_check.isChecked()
        copy_mode = self.copy_radio.isChecked()

        mode_str = "DRY RUN (no files will be changed)" if dry_run else ("Copy" if copy_mode else "Move/rename")
        confirm = QMessageBox.question(self,"Confirm Rename",
            f"Mode: {mode_str}\n\nProcess {matched} matched file(s)?",
            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        if confirm != QMessageBox.StandardButton.Yes: return

        self.progress_bar.setVisible(True); self.progress_bar.setValue(0)
        self.rename_btn.setEnabled(False); self.match_btn.setEnabled(False)
        self.worker = RenameWorker(
            self.files, self.matches,
            self.output_dir_input.text().strip() or None,
            self.naming_scheme_input.text(),
            download_artwork=self.download_artwork_check.isChecked(),
            write_metadata=self.write_metadata_check.isChecked(),
            dry_run=dry_run,
            copy_mode=copy_mode)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.status.connect(self._log)
        self.worker.operation_complete.connect(self._on_op_complete)
        self.worker.finished.connect(self._rename_finished)
        self.worker.start()

    def _on_op_complete(self, orig, new, mi):
        self.history.add_operation(orig, new, mi); self._update_undo_redo()

    def _rename_finished(self, ok, msg):
        self.progress_bar.setVisible(False)
        self.rename_btn.setEnabled(True); self.match_btn.setEnabled(True)
        self._log(("\u2713  " if ok else "\u2717  ") + msg); self._update_undo_redo()
        if not ok: QMessageBox.critical(self,"Rename Error",msg)

    # ── Undo / Redo ───────────────────────────────────────────────
    def _update_undo_redo(self):
        self.undo_btn.setEnabled(self.history.can_undo())
        self.redo_btn.setEnabled(self.history.can_redo())

    def undo_rename(self):
        op = self.history.undo()
        if not op: return
        try:
            src,dst = op['new_path'],op['original_path']
            if os.path.exists(src):
                shutil.move(src,dst)
                self._log(f"\u21a9  Undone: {os.path.basename(src)}"); self._update_undo_redo()
            else: QMessageBox.warning(self,"Undo Failed",f"File not found:\n{src}")
        except Exception as e: QMessageBox.critical(self,"Error",f"Undo failed: {e}")

    def redo_rename(self):
        op = self.history.redo()
        if not op: return
        try:
            src,dst = op['original_path'],op['new_path']
            if os.path.exists(src):
                os.makedirs(os.path.dirname(dst),exist_ok=True)
                shutil.move(src,dst)
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
    app.setWindowIcon(_app_icon())
    app.setStyle("Fusion")
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window,           QColor(C_BG))
    pal.setColor(QPalette.ColorRole.WindowText,       QColor(C_TEXT))
    pal.setColor(QPalette.ColorRole.Base,             QColor(C_SURFACE))
    pal.setColor(QPalette.ColorRole.AlternateBase,    QColor(C_PANEL))
    pal.setColor(QPalette.ColorRole.Text,             QColor(C_TEXT))
    pal.setColor(QPalette.ColorRole.Button,           QColor(C_PANEL))
    pal.setColor(QPalette.ColorRole.ButtonText,       QColor(C_TEXT))
    pal.setColor(QPalette.ColorRole.Highlight,        QColor(C_AMBER_DIM))
    pal.setColor(QPalette.ColorRole.HighlightedText,  QColor("#000"))
    pal.setColor(QPalette.ColorRole.ToolTipBase,      QColor(C_PANEL))
    pal.setColor(QPalette.ColorRole.ToolTipText,      QColor(C_TEXT))
    app.setPalette(pal)
    app.setStyleSheet(STYLESHEET)
    win = MediaRenamerApp()

    # ── Docker: maximise to fill virtual display exactly ──────────────────────
    if os.environ.get("RUNNING_IN_DOCKER"):
        geo = os.environ.get("MEDIARENAMER_GEOMETRY", "")
        if geo and "x" in geo:
            try:
                w, h = (int(x) for x in geo.split("x"))
                win.resize(w, h)
                win.move(0, 0)
            except ValueError:
                pass
        win.showMaximized()
    else:
        win.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
