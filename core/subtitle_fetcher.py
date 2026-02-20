"""
Subtitle fetcher - downloads subtitles from OpenSubtitles
"""

import os
import hashlib
import requests
from pathlib import Path
from typing import Optional


class SubtitleFetcher:
    """Fetches subtitles from OpenSubtitles"""
    
    def __init__(self):
        self.api_url = "https://api.opensubtitles.com/api/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MediaRenamer/1.0',
            'Accept': 'application/json'
        })
        
    def fetch_subtitle(self, file_path: str, language: str = "en") -> Optional[str]:
        """Fetch subtitle for a file"""
        try:
            # Calculate file hash (simplified - OpenSubtitles uses specific hash algorithm)
            file_hash = self._calculate_hash(file_path)
            file_size = os.path.getsize(file_path)
            
            # Search for subtitles
            params = {
                'moviehash': file_hash,
                'moviebytesize': file_size,
                'sublanguageid': language
            }
            
            response = self.session.get(
                f"{self.api_url}/subtitles",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('data') and len(data['data']) > 0:
                    subtitle_info = data['data'][0]
                    subtitle_id = subtitle_info.get('attributes', {}).get('files', [{}])[0].get('file_id')
                    
                    if subtitle_id:
                        return self._download_subtitle(subtitle_id, file_path)
        except Exception as e:
            print(f"Error fetching subtitle: {e}")
            
        return None
        
    def _calculate_hash(self, file_path: str) -> str:
        """Calculate OpenSubtitles hash"""
        # OpenSubtitles uses a specific hash algorithm
        # This is a simplified version
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
        
    def _download_subtitle(self, subtitle_id: int, file_path: str) -> Optional[str]:
        """Download subtitle file"""
        try:
            # Get download link
            response = self.session.get(
                f"{self.api_url}/download",
                params={'file_id': subtitle_id},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                download_link = data.get('link')
                
                if download_link:
                    # Download subtitle
                    sub_response = requests.get(download_link, timeout=30)
                    if sub_response.status_code == 200:
                        # Save subtitle
                        subtitle_path = Path(file_path).with_suffix('.srt')
                        with open(subtitle_path, 'wb') as f:
                            f.write(sub_response.content)
                        return str(subtitle_path)
        except Exception as e:
            print(f"Error downloading subtitle: {e}")
            
        return None
