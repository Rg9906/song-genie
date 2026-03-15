"""
Dynamic Web Scraper for Song Information
Scrapes various sources for dynamic song attributes
"""

import requests
import json
import time
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import logging
import random

logger = logging.getLogger(__name__)

class DynamicWebScraper:
    """Dynamic web scraper for song information"""
    
    def __init__(self):
        self.sources = {
            'wikipedia': WikipediaScraper(),
            'musicbrainz': MusicBrainzScraper(),
            'lastfm': LastFMScraper(),
            'genius': GeniusScraper()
        }
    
    def scrape_song_info(self, artist: str, title: str) -> Dict[str, Any]:
        """Scrape song information from multiple sources"""
        song_info = {
            'artist': artist,
            'title': title,
            'scraped_data': {},
            'sources_used': []
        }
        
        for source_name, scraper in self.sources.items():
            try:
                info = scraper.scrape_song(artist, title)
                if info:
                    song_info['scraped_data'].update(info)
                    song_info['sources_used'].append(source_name)
                    logger.info(f"✅ Scraped from {source_name}")
                time.sleep(1)  # Rate limiting
            except Exception as e:
                logger.warning(f"Failed to scrape from {source_name}: {e}")
        
        return song_info
    
    def batch_scrape_songs(self, songs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Scrape multiple songs"""
        results = []
        
        for i, song in enumerate(songs):
            logger.info(f"Scraping song {i+1}/{len(songs)}: {song.get('title', 'Unknown')}")
            
            scraped_info = self.scrape_song_info(
                song.get('artists', ['Unknown'])[0] if song.get('artists') else 'Unknown',
                song.get('title', 'Unknown')
            )
            
            # Merge with existing data
            merged_song = song.copy()
            merged_song.update(scraped_info['scraped_data'])
            merged_song['scraped_sources'] = scraped_info['sources_used']
            
            results.append(merged_song)
        
        return results

class WikipediaScraper:
    """Wikipedia scraper for song information"""
    
    def scrape_song(self, artist: str, title: str) -> Optional[Dict[str, Any]]:
        """Scrape Wikipedia for song information"""
        try:
            # Search for the song
            search_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}_(song)"
            response = requests.get(search_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self._extract_wikipedia_info(data)
            
            # Try artist + title
            search_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
            response = requests.get(search_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self._extract_wikipedia_info(data)
                
        except Exception as e:
            logger.warning(f"Wikipedia scrape failed: {e}")
        
        return None
    
    def _extract_wikipedia_info(self, data: Dict) -> Dict[str, Any]:
        """Extract relevant information from Wikipedia data"""
        info = {}
        
        # Extract description
        if 'extract' in data:
            info['wikipedia_summary'] = data['extract']
        
        # Extract genres from description
        if 'extract' in data:
            genres = self._extract_genres_from_text(data['extract'])
            if genres:
                info['wikipedia_genres'] = genres
        
        # Extract year from description
        if 'extract' in data:
            year = self._extract_year_from_text(data['extract'])
            if year:
                info['wikipedia_year'] = year
        
        return info
    
    def _extract_genres_from_text(self, text: str) -> List[str]:
        """Extract genre mentions from text"""
        genre_keywords = [
            'pop', 'rock', 'jazz', 'blues', 'country', 'folk', 'electronic',
            'hip hop', 'rap', 'r&b', 'soul', 'funk', 'disco', 'punk', 'metal',
            'classical', 'reggae', 'dance', 'indie', 'alternative', 'ambient'
        ]
        
        found_genres = []
        text_lower = text.lower()
        
        for genre in genre_keywords:
            if genre in text_lower:
                found_genres.append(genre)
        
        return found_genres
    
    def _extract_year_from_text(self, text: str) -> Optional[str]:
        """Extract year from text"""
        import re
        
        # Look for years in 1900s-2020s
        year_patterns = [
            r'\b(19[0-9]{2})\b',  # 1900-1999
            r'\b(20[0-2][0-9])\b'  # 2000-2029
        ]
        
        for pattern in year_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        
        return None

class MusicBrainzScraper:
    """MusicBrainz scraper for detailed song information"""
    
    def scrape_song(self, artist: str, title: str) -> Optional[Dict[str, Any]]:
        """Scrape MusicBrainz for song information"""
        try:
            # Search for the song
            search_url = f"https://musicbrainz.org/ws/2/recording/?query=recording:{title}%20AND%20artist:{artist}&fmt=json"
            response = requests.get(search_url, timeout=10, headers={'User-Agent': 'MusicAkenator/1.0'})
            
            if response.status_code == 200:
                data = response.json()
                if data.get('recordings'):
                    recording = data['recordings'][0]
                    return self._extract_musicbrainz_info(recording)
                    
        except Exception as e:
            logger.warning(f"MusicBrainz scrape failed: {e}")
        
        return None
    
    def _extract_musicbrainz_info(self, recording: Dict) -> Dict[str, Any]:
        """Extract information from MusicBrainz recording"""
        info = {}
        
        # Extract genres from tags
        if 'tag-list' in recording:
            genres = [tag['name'] for tag in recording['tag-list'] if 'genre' in tag.get('name', '').lower()]
            if genres:
                info['musicbrainz_genres'] = genres
        
        # Extract duration
        if 'length' in recording:
            info['musicbrainz_duration'] = recording['length']
        
        # Extract release date
        if 'release-list' in recording and recording['release-list']:
            release = recording['release-list'][0]
            if 'date' in release:
                info['musicbrainz_date'] = release['date']
        
        return info

class LastFMScraper:
    """Last.fm scraper for song information"""
    
    def scrape_song(self, artist: str, title: str) -> Optional[Dict[str, Any]]:
        """Scrape Last.fm for song information"""
        try:
            # Get track info
            url = f"http://ws.audioscrobbler.com/2.0/?method=track.getinfo&api_key=YOUR_API_KEY&artist={artist}&track={title}&format=json"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'track' in data:
                    return self._extract_lastfm_info(data['track'])
                    
        except Exception as e:
            logger.warning(f"Last.fm scrape failed: {e}")
        
        return None
    
    def _extract_lastfm_info(self, track: Dict) -> Dict[str, Any]]:
        """Extract information from Last.fm track"""
        info = {}
        
        # Extract tags (genres)
        if 'toptags' in track and 'tag' in track['toptags']:
            genres = [tag['name'] for tag in track['toptags']['tag'] if tag]
            if genres:
                info['lastfm_genres'] = genres
        
        # Extract play count
        if 'playcount' in track:
            info['lastfm_playcount'] = track['playcount']
        
        # Extract listeners
        if 'listeners' in track:
            info['lastfm_listeners'] = track['listeners']
        
        return info

class GeniusScraper:
    """Genius scraper for lyrics and song information"""
    
    def scrape_song(self, artist: str, title: str) -> Optional[Dict[str, Any]]:
        """Scrape Genius for song information"""
        try:
            # Search for the song
            search_url = f"https://api.genius.com/search?q={artist}%20{title}"
            response = requests.get(search_url, timeout=10, headers={'User-Agent': 'MusicAkenator/1.0'})
            
            if response.status_code == 200:
                data = response.json()
                if data.get('response') and data['response'].get('hits'):
                    hit = data['response']['hits'][0]
                    song_url = hit['result']['url']
                    return self._scrape_genius_page(song_url)
                    
        except Exception as e:
            logger.warning(f"Genius scrape failed: {e}")
        
        return None
    
    def _scrape_genius_page(self, url: str) -> Dict[str, Any]:
        """Scrape Genius page for song information"""
        try:
            response = requests.get(url, timeout=10, headers={'User-Agent': 'MusicAkenator/1.0'})
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                return self._extract_genius_info(soup)
                
        except Exception as e:
            logger.warning(f"Genius page scrape failed: {e}")
        
        return {}
    
    def _extract_genius_info(self, soup) -> Dict[str, Any]:
        """Extract information from Genius page"""
        info = {}
        
        # Extract song metadata
        metadata_script = soup.find('script', string=lambda text: text and 'song_page' in text)
        if metadata_script:
            try:
                import json
                script_content = metadata_script.string
                if 'song_page' in script_content and '};' in script_content:
                    json_part = script_content.split('song_page')[1].split('};')[0] + '}'
                    data = json.loads(json_part)
                else:
                    data = {}
                
                if 'song' in data:
                    song_data = data['song']
                    info['genius_primary_artists'] = song_data.get('primary_artists', [])
                    info['genius_featured_artists'] = song_data.get('featured_artists', [])
                    info['genius_producer_artists'] = song_data.get('producer_artists', [])
                    info['genius_writer_artists'] = song_data.get('writer_artists', [])
                    info['genius_release_date'] = song_data.get('release_date_for_display')
                    
                    # Extract genres from tags
                    if 'tags' in song_data:
                        info['genius_tags'] = [tag['name'] for tag in song_data['tags']]
                        
            except Exception as e:
                logger.warning(f"Failed to parse Genius metadata: {e}")
        
        return info
