#!/usr/bin/env python3
"""
MediaRenamer - A FileBot alternative for renaming movies and TV shows
"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QListWidget, QLabel, 
                             QFileDialog, QMessageBox, QProgressBar, QComboBox,
                             QLineEdit, QTextEdit, QSplitter, QGroupBox, QCheckBox,
                             QMenu, QDialog, QDialogButtonBox, QFormLayout, QInputDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

try:
    from core.matcher import MediaMatcher
    from core.renamer import FileRenamer
    from core.subtitle_fetcher import SubtitleFetcher
    from core.history import RenameHistory
    from core.presets import PresetManager
    from core.artwork import ArtworkDownloader
    from core.metadata_writer import MetadataWriter
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from core.matcher import MediaMatcher
    from core.renamer import FileRenamer
    from core.subtitle_fetcher import SubtitleFetcher
    from core.history import RenameHistory
    from core.presets import PresetManager
    from core.artwork import ArtworkDownloader
    from core.metadata_writer import MetadataWriter


class RenameWorker(QThread):
    """Worker thread for renaming operations"""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    operation_complete = pyqtSignal(str, str, dict)  # original_path, new_path, match_info
    
    def __init__(self, files, matches, output_dir, naming_scheme, download_artwork=False, write_metadata=False):
        super().__init__()
        self.files = files
        self.matches = matches
        self.output_dir = output_dir
        self.naming_scheme = naming_scheme
        self.download_artwork = download_artwork
        self.write_metadata = write_metadata
        
    def run(self):
        try:
            renamer = FileRenamer(self.naming_scheme)
            artwork_downloader = ArtworkDownloader() if self.download_artwork else None
            metadata_writer = MetadataWriter() if self.write_metadata else None
            
            total = len(self.files)
            
            for i, (file_path, match_info) in enumerate(zip(self.files, self.matches)):
                if not match_info:
                    continue
                    
                self.status.emit(f"Renaming: {os.path.basename(file_path)}")
                
                # Rename file
                new_path = renamer.rename_file(file_path, match_info, self.output_dir)
                
                if new_path:
                    # Download artwork if requested
                    if artwork_downloader and match_info:
                        art_dir = os.path.dirname(new_path)
                        poster_path = artwork_downloader.download_poster(match_info, art_dir)
                        if poster_path:
                            self.status.emit(f"Downloaded poster: {os.path.basename(poster_path)}")
                    
                    # Write metadata if requested
                    if metadata_writer and match_info:
                        poster_path = None
                        if artwork_downloader:
                            art_dir = os.path.dirname(new_path)
                            poster_path = os.path.join(art_dir, f"{match_info.get('title', 'Unknown')}_poster.jpg")
                            if not os.path.exists(poster_path):
                                poster_path = None
                        
                        if metadata_writer.write_metadata(new_path, match_info, poster_path):
                            self.status.emit(f"Wrote metadata to: {os.path.basename(new_path)}")
                    
                    self.operation_complete.emit(file_path, new_path, match_info)
                
                self.progress.emit(int((i + 1) / total * 100))
            
            self.finished.emit(True, f"Successfully renamed {total} files")
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")


class MediaRenamerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MediaRenamer - FileBot Alternative")
        self.setGeometry(100, 100, 1200, 800)
        
        self.files = []
        self.matches = []
        self.matcher = MediaMatcher()
        self.renamer = FileRenamer()
        self.history = RenameHistory()
        self.preset_manager = PresetManager()
        
        self.init_ui()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Top controls
        controls_layout = QHBoxLayout()
        
        self.add_files_btn = QPushButton("Add Files")
        self.add_files_btn.clicked.connect(self.add_files)
        controls_layout.addWidget(self.add_files_btn)
        
        self.add_folder_btn = QPushButton("Add Folder")
        self.add_folder_btn.clicked.connect(self.add_folder)
        controls_layout.addWidget(self.add_folder_btn)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_files)
        controls_layout.addWidget(self.clear_btn)
        
        controls_layout.addStretch()
        
        # Data source selection
        controls_layout.addWidget(QLabel("Data Source:"))
        self.data_source_combo = QComboBox()
        self.data_source_combo.addItems(["TheMovieDB", "TheTVDB"])
        controls_layout.addWidget(self.data_source_combo)
        
        self.match_btn = QPushButton("Match Files")
        self.match_btn.clicked.connect(self.match_files)
        controls_layout.addWidget(self.match_btn)
        
        layout.addLayout(controls_layout)
        
        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Original files
        left_group = QGroupBox("Original Files")
        left_layout = QVBoxLayout(left_group)
        
        self.original_list = QListWidget()
        self.original_list.setAcceptDrops(True)
        self.original_list.setDragDropMode(QListWidget.DragDropMode.DropOnly)
        left_layout.addWidget(self.original_list)
        
        splitter.addWidget(left_group)
        
        # Right panel - New names
        right_group = QGroupBox("New Names")
        right_layout = QVBoxLayout(right_group)
        
        self.new_names_list = QListWidget()
        right_layout.addWidget(self.new_names_list)
        
        # Naming scheme with presets
        naming_layout = QHBoxLayout()
        naming_layout.addWidget(QLabel("Naming Scheme:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(self.preset_manager.list_presets())
        self.preset_combo.currentTextChanged.connect(self.load_preset)
        naming_layout.addWidget(self.preset_combo)
        self.naming_scheme_input = QLineEdit("{n}.{y}.{vf}.{vc}.{ac}")
        self.naming_scheme_input.setToolTip("Example: {n}.{y}.{vf}.{vc}.{ac} → The.Terminator.1984.1080p.AVC.DTS.mkv")
        naming_layout.addWidget(self.naming_scheme_input)
        save_preset_btn = QPushButton("Save Preset")
        save_preset_btn.clicked.connect(self.save_current_preset)
        naming_layout.addWidget(save_preset_btn)
        right_layout.addLayout(naming_layout)
        
        # Output directory
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Output Directory:"))
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setPlaceholderText("Leave empty to rename in place")
        output_layout.addWidget(self.output_dir_input)
        self.browse_output_btn = QPushButton("Browse")
        self.browse_output_btn.clicked.connect(self.browse_output_dir)
        output_layout.addWidget(self.browse_output_btn)
        right_layout.addLayout(output_layout)
        
        # Options
        options_layout = QHBoxLayout()
        self.download_artwork_check = QCheckBox("Download Artwork")
        self.download_artwork_check.setToolTip("Download poster images for matched media")
        options_layout.addWidget(self.download_artwork_check)
        self.write_metadata_check = QCheckBox("Write Metadata")
        self.write_metadata_check.setToolTip("Write metadata tags to video files (MP4 only)")
        options_layout.addWidget(self.write_metadata_check)
        options_layout.addStretch()
        right_layout.addLayout(options_layout)
        
        splitter.addWidget(right_group)
        
        splitter.setSizes([400, 800])
        layout.addWidget(splitter)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status text
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)
        
        # Bottom buttons
        bottom_layout = QHBoxLayout()
        
        self.fetch_subtitles_btn = QPushButton("Fetch Subtitles")
        self.fetch_subtitles_btn.clicked.connect(self.fetch_subtitles)
        bottom_layout.addWidget(self.fetch_subtitles_btn)
        
        # Undo/Redo buttons
        self.undo_btn = QPushButton("Undo")
        self.undo_btn.clicked.connect(self.undo_rename)
        self.undo_btn.setEnabled(self.history.can_undo())
        bottom_layout.addWidget(self.undo_btn)
        
        self.redo_btn = QPushButton("Redo")
        self.redo_btn.clicked.connect(self.redo_rename)
        self.redo_btn.setEnabled(self.history.can_redo())
        bottom_layout.addWidget(self.redo_btn)
        
        bottom_layout.addStretch()
        
        self.rename_btn = QPushButton("Rename Files")
        self.rename_btn.clicked.connect(self.rename_files)
        self.rename_btn.setEnabled(False)
        bottom_layout.addWidget(self.rename_btn)
        
        layout.addLayout(bottom_layout)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event: QDropEvent):
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        self.add_files_list(files)
        event.acceptProposedAction()
        
    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Media Files", "", 
            "Video Files (*.mp4 *.mkv *.avi *.mov *.m4v *.mpg *.mpeg);;All Files (*)"
        )
        if files:
            self.add_files_list(files)
            
    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            media_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.m4v', '.mpg', '.mpeg', '.flv', '.wmv'}
            files = []
            for root, dirs, filenames in os.walk(folder):
                for filename in filenames:
                    if Path(filename).suffix.lower() in media_extensions:
                        files.append(os.path.join(root, filename))
            if files:
                self.add_files_list(files)
            else:
                QMessageBox.information(self, "No Media Files", "No media files found in the selected folder.")
                
    def add_files_list(self, files):
        for file_path in files:
            if file_path not in self.files:
                self.files.append(file_path)
                self.original_list.addItem(os.path.basename(file_path))
        self.status_text.append(f"Added {len(files)} file(s)")
        
    def clear_files(self):
        self.files.clear()
        self.matches.clear()
        self.original_list.clear()
        self.new_names_list.clear()
        self.rename_btn.setEnabled(False)
        self.status_text.append("Cleared all files")
        
    def browse_output_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_dir_input.setText(directory)
            
    def match_files(self):
        if not self.files:
            QMessageBox.warning(self, "No Files", "Please add files first.")
            return
        
        # Check API key
        try:
            from config import TMDB_API_KEY
            if TMDB_API_KEY == "YOUR_TMDB_API_KEY_HERE" or not TMDB_API_KEY:
                reply = QMessageBox.warning(
                    self, "API Key Not Configured",
                    "TheMovieDB API key is not configured.\n\n"
                    "Please edit config.py and add your API key.\n"
                    "Get a free API key from: https://www.themoviedb.org/settings/api\n\n"
                    "Continue anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
        except ImportError:
            pass
            
        self.status_text.append("Matching files...")
        self.match_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        data_source = self.data_source_combo.currentText()
        self.matches = []
        self.new_names_list.clear()
        
        total = len(self.files)
        for i, file_path in enumerate(self.files):
            self.progress_bar.setValue(int((i / total) * 100))
            QApplication.processEvents()
            
            try:
                match_info = self.matcher.match_file(file_path, data_source, extract_media_info=True)
                self.matches.append(match_info)
                
                if match_info:
                    new_name = self.renamer.generate_new_name(file_path, match_info, self.naming_scheme_input.text())
                    self.new_names_list.addItem(new_name)
                    self.status_text.append(f"Matched: {os.path.basename(file_path)} -> {match_info.get('title', 'Unknown')}")
                else:
                    self.new_names_list.addItem(f"[No match] {os.path.basename(file_path)}")
                    self.status_text.append(f"No match found for: {os.path.basename(file_path)}")
            except Exception as e:
                self.matches.append(None)
                self.new_names_list.addItem(f"[Error] {os.path.basename(file_path)}")
                self.status_text.append(f"Error matching {os.path.basename(file_path)}: {str(e)}")
        
        self.progress_bar.setValue(100)
        self.progress_bar.setVisible(False)
        self.match_btn.setEnabled(True)
        self.rename_btn.setEnabled(True)
        matched_count = sum(1 for m in self.matches if m)
        self.status_text.append(f"Matching complete. Found {matched_count} matches out of {total} files.")
        
    def fetch_subtitles(self):
        if not self.files:
            QMessageBox.warning(self, "No Files", "Please add files first.")
            return
            
        self.status_text.append("Fetching subtitles...")
        fetcher = SubtitleFetcher()
        
        for file_path in self.files:
            try:
                subtitle_path = fetcher.fetch_subtitle(file_path)
                if subtitle_path:
                    self.status_text.append(f"Downloaded subtitle: {os.path.basename(subtitle_path)}")
                else:
                    self.status_text.append(f"No subtitle found for: {os.path.basename(file_path)}")
            except Exception as e:
                self.status_text.append(f"Error fetching subtitle for {os.path.basename(file_path)}: {str(e)}")
                
    def rename_files(self):
        if not self.files or not self.matches:
            QMessageBox.warning(self, "No Matches", "Please match files first.")
            return
            
        # Confirm rename
        reply = QMessageBox.question(
            self, "Confirm Rename", 
            f"Are you sure you want to rename {len(self.files)} file(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        output_dir = self.output_dir_input.text().strip() or None
        naming_scheme = self.naming_scheme_input.text()
        download_artwork = self.download_artwork_check.isChecked()
        write_metadata = self.write_metadata_check.isChecked()
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.rename_btn.setEnabled(False)
        
        self.worker = RenameWorker(
            self.files, self.matches, output_dir, naming_scheme,
            download_artwork=download_artwork,
            write_metadata=write_metadata
        )
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.status.connect(lambda s: self.status_text.append(s))
        self.worker.operation_complete.connect(self.on_operation_complete)
        self.worker.finished.connect(self.rename_finished)
        self.worker.start()
        
    def on_operation_complete(self, original_path, new_path, match_info):
        """Called when a rename operation completes"""
        self.history.add_operation(original_path, new_path, match_info)
        self.update_undo_redo_buttons()
    
    def update_undo_redo_buttons(self):
        """Update undo/redo button states"""
        self.undo_btn.setEnabled(self.history.can_undo())
        self.redo_btn.setEnabled(self.history.can_redo())
    
    def undo_rename(self):
        """Undo last rename operation"""
        operation = self.history.undo()
        if operation:
            try:
                import shutil
                original = operation['new_path']
                new = operation['original_path']
                if os.path.exists(original):
                    shutil.move(original, new)
                    self.status_text.append(f"Undone: {os.path.basename(original)} → {os.path.basename(new)}")
                    self.update_undo_redo_buttons()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to undo: {str(e)}")
    
    def redo_rename(self):
        """Redo last undone operation"""
        operation = self.history.redo()
        if operation:
            try:
                import shutil
                original = operation['original_path']
                new = operation['new_path']
                if os.path.exists(original):
                    renamer = FileRenamer(self.naming_scheme_input.text())
                    renamer.rename_file(original, operation.get('match_info', {}), None)
                    self.status_text.append(f"Redone: {os.path.basename(original)} → {os.path.basename(new)}")
                    self.update_undo_redo_buttons()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to redo: {str(e)}")
    
    def load_preset(self, preset_name):
        """Load a naming scheme preset"""
        scheme = self.preset_manager.get_preset(preset_name)
        if scheme:
            self.naming_scheme_input.setText(scheme)
    
    def save_current_preset(self):
        """Save current naming scheme as a preset"""
        scheme = self.naming_scheme_input.text()
        if not scheme:
            QMessageBox.warning(self, "Empty Scheme", "Please enter a naming scheme first.")
            return
        
        name, ok = QInputDialog.getText(self, "Save Preset", "Preset name:")
        if ok and name:
            self.preset_manager.save_preset(name, scheme)
            # Refresh preset combo
            self.preset_combo.clear()
            self.preset_combo.addItems(self.preset_manager.list_presets())
            self.preset_combo.setCurrentText(name)
            self.status_text.append(f"Saved preset: {name}")
    
    def rename_finished(self, success, message):
        self.progress_bar.setVisible(False)
        self.rename_btn.setEnabled(True)
        self.status_text.append(message)
        self.update_undo_redo_buttons()
        
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)


def main():
    app = QApplication(sys.argv)
    window = MediaRenamerApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
