"""
Naming scheme presets manager
"""

import json
import os
from pathlib import Path
from typing import Dict, List


class PresetManager:
    """Manages naming scheme presets"""
    
    def __init__(self, presets_file: str = None):
        self.presets_file = presets_file or os.path.join(
            os.path.expanduser("~"), ".mediarenamer", "presets.json"
        )
        self.presets: Dict[str, str] = {}
        self._ensure_presets_dir()
        self._load_presets()
        self._load_default_presets()
    
    def _ensure_presets_dir(self):
        """Ensure presets directory exists"""
        presets_dir = os.path.dirname(self.presets_file)
        os.makedirs(presets_dir, exist_ok=True)
    
    def _load_default_presets(self):
        """Load default presets if none exist"""
        defaults = {
            "FileBot Style": "{n}.{y}.{vf}.{vc}.{ac}",
            "Plex Standard": "{n} ({y})/{n} ({y})",
            "Simple": "{n} ({y})",
            "Detailed": "{n} ({y}) [{vf}] [{vc}] [{ac}]",
            "TV Show - Plex": "{n}/Season {s}/{n} - {s00e00} - {t}",
            "TV Show - Simple": "{n}/S{s}/E{e}",
            "TV Show - Detailed": "{n}/Season {s}/{n} - {s00e00} - {t} [{vf}] [{vc}]",
            "Movie - Full Info": "{n}.{y}.{vf}.{vc}.{ac}.{channels}",
            "Movie - Minimal": "{n} ({y})",
            "Anime Style": "{n} - {s00e00} - {t}",
        }
        
        for name, scheme in defaults.items():
            if name not in self.presets:
                self.presets[name] = scheme
    
    def _load_presets(self):
        """Load presets from file"""
        if os.path.exists(self.presets_file):
            try:
                with open(self.presets_file, 'r') as f:
                    self.presets = json.load(f)
            except Exception:
                self.presets = {}
    
    def _save_presets(self):
        """Save presets to file"""
        try:
            with open(self.presets_file, 'w') as f:
                json.dump(self.presets, f, indent=2)
        except Exception as e:
            print(f"Error saving presets: {e}")
    
    def get_preset(self, name: str) -> str:
        """Get a preset by name"""
        return self.presets.get(name, "")
    
    def save_preset(self, name: str, scheme: str):
        """Save a new preset"""
        self.presets[name] = scheme
        self._save_presets()
    
    def delete_preset(self, name: str):
        """Delete a preset"""
        if name in self.presets:
            del self.presets[name]
            self._save_presets()
    
    def list_presets(self) -> List[str]:
        """List all preset names"""
        return list(self.presets.keys())
    
    def rename_preset(self, old_name: str, new_name: str):
        """Rename a preset"""
        if old_name in self.presets:
            self.presets[new_name] = self.presets[old_name]
            del self.presets[old_name]
            self._save_presets()
