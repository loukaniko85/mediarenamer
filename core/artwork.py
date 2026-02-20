"""
Artwork downloader — downloads posters and fanart from TMDB.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict

import requests

log = logging.getLogger(__name__)

_PLACEHOLDERS = frozenset({
    "", "YOUR_TMDB_API_KEY_HERE", "YOUR_TMDB_API_KEY",
})


def _read_tmdb_key() -> str:
    """Read TMDB key from env at call-time (never cached at import-time)."""
    key = os.environ.get("TMDB_API_KEY", "")
    if not key:
        try:
            import config  # noqa: PLC0415
            key = getattr(config, "TMDB_API_KEY", "")
        except ImportError:
            pass
    return key or ""


class ArtworkDownloader:
    """Downloads artwork (posters, backdrops) from TMDB."""

    def __init__(self):
        self.tmdb_api_key  = _read_tmdb_key()
        self.tmdb_base_url = "https://api.themoviedb.org/3"
        self.image_base    = "https://image.tmdb.org/t/p"
        self.session       = requests.Session()
        self.session.headers.update({"User-Agent": "MediaRenamer/1.0"})

    def download_poster(
        self,
        match_info: Dict,
        output_dir: str,
        size: str = "w500",
    ) -> Optional[str]:
        """Download the primary poster for *match_info* into *output_dir*."""
        return self._download_image(match_info, output_dir, "poster_path", size, "poster")

    def download_fanart(
        self,
        match_info: Dict,
        output_dir: str,
        size: str = "w1280",
    ) -> Optional[str]:
        """Download the backdrop/fanart for *match_info* into *output_dir*."""
        return self._download_image(match_info, output_dir, "backdrop_path", size, "fanart")

    def _download_image(
        self,
        match_info: Dict,
        output_dir: str,
        image_key: str,
        size: str,
        suffix: str,
    ) -> Optional[str]:
        if not match_info or not match_info.get("tmdb_id"):
            return None
        if self.tmdb_api_key.strip() in _PLACEHOLDERS:
            log.warning("Artwork download skipped — TMDB key not configured.")
            return None

        try:
            media_type = match_info.get("type", "movie")
            tmdb_id    = match_info["tmdb_id"]
            endpoint   = "movie" if media_type == "movie" else "tv"

            resp = self.session.get(
                f"{self.tmdb_base_url}/{endpoint}/{tmdb_id}",
                params={"api_key": self.tmdb_api_key},
                timeout=10,
            )
            if not resp.ok:
                log.warning("TMDB %s details returned %s", endpoint, resp.status_code)
                return None

            image_path = resp.json().get(image_key)
            if not image_path:
                return None

            img_url  = f"{self.image_base}/{size}{image_path}"
            img_resp = self.session.get(img_url, timeout=30, stream=True)
            if not img_resp.ok:
                return None

            title    = match_info.get("title", "Unknown").replace("/", "-")
            filename = f"{title}_{suffix}.jpg"
            filepath = os.path.join(output_dir, filename)
            os.makedirs(output_dir, exist_ok=True)

            with open(filepath, "wb") as fh:
                shutil.copyfileobj(img_resp.raw, fh)

            log.info("Downloaded %s → %s", suffix, filepath)
            return filepath

        except Exception as exc:
            log.warning("Artwork download failed: %s", exc)
            return None
