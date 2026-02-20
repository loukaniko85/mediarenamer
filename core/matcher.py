"""
Media file matcher - matches files with online databases
"""

import os
import re
from pathlib import Path
import requests
from typing import Dict, Optional, List

try:
    from config import TMDB_API_KEY, TVDB_API_KEY
except ImportError:
    TMDB_API_KEY = "YOUR_TMDB_API_KEY"
    TVDB_API_KEY = "YOUR_TVDB_API_KEY"

try:
    from .media_info import MediaInfoExtractor
except (ImportError, ValueError):
    try:
        from core.media_info import MediaInfoExtractor
    except ImportError:
        MediaInfoExtractor = None


class MediaMatcher:
    """Matches media files with online databases"""
    
    def __init__(self):
        self.tmdb_api_key = TMDB_API_KEY
        self.tvdb_api_key = TVDB_API_KEY
        self.tmdb_base_url = "https://api.themoviedb.org/3"
        self.tvdb_base_url = "https://api4.thetvdb.com/v4"
        self.session = requests.Session()
        self.media_info_extractor = MediaInfoExtractor() if MediaInfoExtractor else None
        
    def match_file(self, file_path: str, data_source: str = "TheMovieDB", extract_media_info: bool = True) -> Optional[Dict]:
        """Match a file with online database"""
        filename = os.path.basename(file_path)
        
        # Extract information from filename
        info = self._parse_filename(filename)
        
        # Match with online database
        match_result = None
        if data_source == "TheMovieDB":
            match_result = self._match_tmdb(info)
        elif data_source == "TheTVDB":
            match_result = self._match_tvdb(info)
        
        # Extract media info if requested
        if match_result and extract_media_info and self.media_info_extractor:
            media_info = self.media_info_extractor.extract_info(file_path)
            match_result.update(media_info)
        
        return match_result
    
    def search_movies(self, query: str, year: Optional[int] = None) -> List[Dict]:
        """Search for movies and return multiple results"""
        if self._is_api_key_unconfigured(self.tmdb_api_key):
            return []
        
        try:
            params = {'api_key': self.tmdb_api_key, 'query': query}
            if year:
                params['year'] = year
            
            response = self.session.get(
                f"{self.tmdb_base_url}/search/movie",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json().get('results', [])
                return [
                    {
                        'title': m.get('title'),
                        'year': m.get('release_date', '')[:4] if m.get('release_date') else None,
                        'tmdb_id': m.get('id'),
                        'type': 'movie',
                        'overview': m.get('overview', '')
                    }
                    for m in results[:10]  # Limit to 10 results
                ]
        except Exception as e:
            print(f"Error searching movies: {e}")
        
        return []
    
    def search_tv_shows(self, query: str) -> List[Dict]:
        """Search for TV shows and return multiple results"""
        if self._is_api_key_unconfigured(self.tmdb_api_key):
            return []
        
        try:
            params = {'api_key': self.tmdb_api_key, 'query': query}
            response = self.session.get(
                f"{self.tmdb_base_url}/search/tv",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json().get('results', [])
                return [
                    {
                        'title': m.get('name'),
                        'year': m.get('first_air_date', '')[:4] if m.get('first_air_date') else None,
                        'tmdb_id': m.get('id'),
                        'type': 'tv',
                        'overview': m.get('overview', '')
                    }
                    for m in results[:10]  # Limit to 10 results
                ]
        except Exception as e:
            print(f"Error searching TV shows: {e}")
        
        return []
        
    def _parse_filename(self, filename: str) -> Dict:
        """Extract title, year, season, episode from filename"""
        # Remove extension
        name = Path(filename).stem
        
        # Common patterns
        patterns = [
            # TV Show patterns
            r'(.+?)[\.\s]+S(\d{1,2})E(\d{1,2})',  # Show S01E01
            r'(.+?)[\.\s]+(\d{1,2})x(\d{1,2})',   # Show 1x01
            r'(.+?)[\.\s]+(\d{4})[\.\s]+(\d{2})', # Show 2024 01
            # Movie patterns
            r'(.+?)[\.\s]\((\d{4})\)',            # Movie (2024)
            r'(.+?)[\.\s](\d{4})',                # Movie 2024
        ]
        
        info = {'title': name, 'year': None, 'season': None, 'episode': None, 'is_tv': False}
        
        for pattern in patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                if 'S' in pattern or 'x' in pattern:
                    # TV show
                    info['title'] = match.group(1).strip().replace('.', ' ')
                    info['season'] = int(match.group(2))
                    info['episode'] = int(match.group(3))
                    info['is_tv'] = True
                else:
                    # Movie
                    info['title'] = match.group(1).strip().replace('.', ' ')
                    info['year'] = int(match.group(2))
                break
        
        return info
        
    def _match_tmdb(self, info: Dict) -> Optional[Dict]:
        """Match with TheMovieDB"""
        if info['is_tv']:
            return self._match_tmdb_tv(info)
        else:
            return self._match_tmdb_movie(info)
            
    def _is_api_key_unconfigured(self, key: str) -> bool:
        """Return True if the given key looks like a placeholder / is empty."""
        return not key or key in ("YOUR_TMDB_API_KEY_HERE", "YOUR_TMDB_API_KEY",
                                   "YOUR_TVDB_API_KEY_HERE", "YOUR_TVDB_API_KEY")

    def _match_tmdb_movie(self, info: Dict) -> Optional[Dict]:
        """Match movie with TMDB"""
        if self._is_api_key_unconfigured(self.tmdb_api_key):
            print("Warning: TMDB API key not configured. Please set it in config.py")
            return None
            
        try:
            # Search for movie
            params = {
                'api_key': self.tmdb_api_key,
                'query': info['title'],
            }
            if info.get('year'):
                params['year'] = info['year']
            
            response = self.session.get(
                f"{self.tmdb_base_url}/search/movie",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json().get('results', [])
                if results:
                    movie = results[0]
                    return {
                        'title': movie.get('title'),
                        'year': movie.get('release_date', '')[:4] if movie.get('release_date') else None,
                        'tmdb_id': movie.get('id'),
                        'type': 'movie',
                        'overview': movie.get('overview', '')
                    }
        except Exception as e:
            print(f"Error matching movie: {e}")
            
        return None
        
    def _match_tmdb_tv(self, info: Dict) -> Optional[Dict]:
        """Match TV show with TMDB"""
        if self._is_api_key_unconfigured(self.tmdb_api_key):
            print("Warning: TMDB API key not configured. Please set it in config.py")
            return None
            
        try:
            params = {
                'api_key': self.tmdb_api_key,
                'query': info['title']
            }
            
            response = self.session.get(
                f"{self.tmdb_base_url}/search/tv",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json().get('results', [])
                if results:
                    tv_show = results[0]
                    # Get episode details
                    episode_info = self._get_tmdb_episode(
                        tv_show.get('id'),
                        info.get('season'),
                        info.get('episode')
                    )
                    
                    return {
                        'title': tv_show.get('name'),
                        'year': tv_show.get('first_air_date', '')[:4] if tv_show.get('first_air_date') else None,
                        'season': info.get('season'),
                        'episode': info.get('episode'),
                        'episode_title': episode_info.get('name') if episode_info else None,
                        'tmdb_id': tv_show.get('id'),
                        'type': 'tv',
                        'overview': tv_show.get('overview', '')
                    }
        except Exception as e:
            print(f"Error matching TV show: {e}")
            
        return None
        
    def _get_tmdb_episode(self, show_id: int, season: int, episode: int) -> Optional[Dict]:
        """Get episode details from TMDB"""
        try:
            params = {'api_key': self.tmdb_api_key}
            response = self.session.get(
                f"{self.tmdb_base_url}/tv/{show_id}/season/{season}/episode/{episode}",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
            
        return None
        
    def _match_tvdb(self, info: Dict) -> Optional[Dict]:
        """Match with TheTVDB.
        
        Full TheTVDB v4 auth requires a subscriber PIN in addition to the API key,
        so we fall back to TMDB for now. Set TVDB_API_KEY in config.py if you
        implement the full auth flow.
        """
        print("Notice: TheTVDB integration is not fully implemented; falling back to TheMovieDB.")
        return self._match_tmdb(info)
