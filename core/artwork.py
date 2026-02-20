"""
Artwork downloader - downloads posters and artwork from TMDB
"""

import os
import requests
from pathlib import Path
from typing import Optional, Dict
import shutil

try:
    from config import TMDB_API_KEY
except ImportError:
    TMDB_API_KEY = "YOUR_TMDB_API_KEY"


class ArtworkDownloader:
    """Downloads artwork (posters, fanart) from TMDB"""
    
    def __init__(self):
        self.tmdb_api_key = TMDB_API_KEY
        self.tmdb_base_url = "https://api.themoviedb.org/3"
        self.image_base_url = "https://image.tmdb.org/t/p"
        self.session = requests.Session()
    
    def download_poster(self, match_info: Dict, output_dir: str, size: str = "w500") -> Optional[str]:
        """Download poster image"""
        if not match_info or not match_info.get('tmdb_id'):
            return None
        
        try:
            media_type = match_info.get('type', 'movie')
            tmdb_id = match_info['tmdb_id']
            
            # Get media details
            if media_type == 'movie':
                response = self.session.get(
                    f"{self.tmdb_base_url}/movie/{tmdb_id}",
                    params={'api_key': self.tmdb_api_key},
                    timeout=10
                )
            else:  # TV
                response = self.session.get(
                    f"{self.tmdb_base_url}/tv/{tmdb_id}",
                    params={'api_key': self.tmdb_api_key},
                    timeout=10
                )
            
            if response.status_code == 200:
                data = response.json()
                poster_path = data.get('poster_path')
                
                if poster_path:
                    # Download poster
                    poster_url = f"{self.image_base_url}/{size}{poster_path}"
                    img_response = self.session.get(poster_url, timeout=30, stream=True)
                    
                    if img_response.status_code == 200:
                        # Determine filename
                        title = match_info.get('title', 'Unknown').replace('/', '-')
                        filename = f"{title}_poster.jpg"
                        filepath = os.path.join(output_dir, filename)
                        
                        os.makedirs(output_dir, exist_ok=True)
                        
                        with open(filepath, 'wb') as f:
                            shutil.copyfileobj(img_response.raw, f)
                        
                        return filepath
        except Exception as e:
            print(f"Error downloading poster: {e}")
        
        return None
    
    def download_fanart(self, match_info: Dict, output_dir: str, size: str = "w1280") -> Optional[str]:
        """Download fanart/backdrop"""
        if not match_info or not match_info.get('tmdb_id'):
            return None
        
        try:
            media_type = match_info.get('type', 'movie')
            tmdb_id = match_info['tmdb_id']
            
            # Get media details
            if media_type == 'movie':
                response = self.session.get(
                    f"{self.tmdb_base_url}/movie/{tmdb_id}",
                    params={'api_key': self.tmdb_api_key},
                    timeout=10
                )
            else:  # TV
                response = self.session.get(
                    f"{self.tmdb_base_url}/tv/{tmdb_id}",
                    params={'api_key': self.tmdb_api_key},
                    timeout=10
                )
            
            if response.status_code == 200:
                data = response.json()
                backdrop_path = data.get('backdrop_path')
                
                if backdrop_path:
                    # Download backdrop
                    backdrop_url = f"{self.image_base_url}/{size}{backdrop_path}"
                    img_response = self.session.get(backdrop_url, timeout=30, stream=True)
                    
                    if img_response.status_code == 200:
                        title = match_info.get('title', 'Unknown').replace('/', '-')
                        filename = f"{title}_fanart.jpg"
                        filepath = os.path.join(output_dir, filename)
                        
                        os.makedirs(os.path.dirname(filepath), exist_ok=True)
                        
                        with open(filepath, 'wb') as f:
                            shutil.copyfileobj(img_response.raw, f)
                        
                        return filepath
        except Exception as e:
            print(f"Error downloading fanart: {e}")
        
        return None
