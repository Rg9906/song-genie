"""
Scalable Dataset Pipeline for Music Akenator
Automated song metadata collection, normalization, and validation
"""

import json
import requests
import time
from typing import List, Dict, Any, Set, Optional, Tuple
from collections import defaultdict, Counter
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DatasetPipeline:
    """Scalable pipeline for expanding song dataset from 71 to 500-1000+ songs"""
    
    def __init__(self):
        self.genre_normalization = self._build_genre_normalization_map()
        self.artist_normalization = self._build_artist_normalization_map()
        self.required_fields = {
            'title', 'artists', 'genres', 'publication_date'
        }
        self.optional_fields = {
            'duration', 'bpm', 'billion_views', 'themes', 
            'instruments', 'artist_genders', 'artist_types', 'song_types'
        }
        
    def expand_dataset(self, target_size: int = 500, batch_size: int = 100) -> List[Dict[str, Any]]:
        """Expand dataset to target size using multiple sources"""
        logger.info(f"🎵 Expanding dataset to {target_size} songs...")
        
        # Load existing dataset
        existing_songs = self._load_existing_dataset()
        logger.info(f"📊 Current dataset: {len(existing_songs)} songs")
        
        # Collect new songs from multiple sources
        new_songs = []
        
        # 1. Wikidata expansion
        wikidata_songs = self._fetch_from_wikidata(target_size - len(existing_songs))
        new_songs.extend(wikidata_songs)
        logger.info(f"🌐 Fetched {len(wikidata_songs)} songs from Wikidata")
        
        # 2. MusicBrainz expansion (if needed)
        if len(new_songs) + len(existing_songs) < target_size:
            remaining = target_size - len(new_songs) - len(existing_songs)
            musicbrainz_songs = self._fetch_from_musicbrainz(remaining)
            new_songs.extend(musicbrainz_songs)
            logger.info(f"🎼 Fetched {len(musicbrainz_songs)} songs from MusicBrainz")
        
        # 3. Normalize and validate all songs
        all_songs = existing_songs + new_songs
        normalized_songs = self._normalize_dataset(all_songs)
        validated_songs = self._validate_dataset(normalized_songs)
        
        # 4. Remove duplicates
        deduplicated_songs = self._remove_duplicates(validated_songs)
        
        # 5. Limit to target size
        final_songs = deduplicated_songs[:target_size]
        
        logger.info(f"✅ Final dataset: {len(final_songs)} songs")
        return final_songs
    
    def _fetch_from_wikidata(self, limit: int) -> List[Dict[str, Any]]:
        """Fetch songs from Wikidata with enhanced SPARQL query"""
        # Enhanced SPARQL query for comprehensive song metadata
        query = f"""
        SELECT DISTINCT ?song ?songLabel ?artistLabel ?genreLabel ?pubDate ?duration ?bpm
               ?awardLabel ?labelLabel ?producerLabel ?composerLabel
               ?filmLabel ?tvSeriesLabel ?videoGameLabel ?countryLabel
        WHERE {{
          ?song wdt:P31 wd:Q7366.  # is a song
          ?song rdfs:label ?songLabel.
          FILTER(LANG(?songLabel) = "en")
          
          OPTIONAL {{ ?song wdt:P175 ?artist. ?artist rdfs:label ?artistLabel. FILTER(LANG(?artistLabel) = "en") }}
          OPTIONAL {{ ?song wdt:P136 ?genre. ?genre rdfs:label ?genreLabel. FILTER(LANG(?genreLabel) = "en") }}
          OPTIONAL {{ ?song wdt:P577 ?pubDate. }}
          OPTIONAL {{ ?song wdt:P2047 ?duration. }}
          OPTIONAL {{ ?song wdt:P1813 ?bpm. }}
          OPTIONAL {{ ?song wdt:P166 ?award. ?award rdfs:label ?awardLabel. FILTER(LANG(?awardLabel) = "en") }}
          OPTIONAL {{ ?song wdt:P264 ?label. ?label rdfs:label ?labelLabel. FILTER(LANG(?labelLabel) = "en") }}
          OPTIONAL {{ ?song wdt:P98 ?producer. ?producer rdfs:label ?producerLabel. FILTER(LANG(?producerLabel) = "en") }}
          OPTIONAL {{ ?song wdt:P86 ?composer. ?composer rdfs:label ?composerLabel. FILTER(LANG(?composerLabel) = "en") }}
          OPTIONAL {{ ?song wdt:P361 ?film. ?film rdfs:label ?filmLabel. FILTER(LANG(?filmLabel) = "en") }}
          OPTIONAL {{ ?song wdt:P361 ?tvSeries. ?tvSeries rdfs:label ?tvSeriesLabel. FILTER(LANG(?tvSeriesLabel) = "en") }}
          OPTIONAL {{ ?song wdt:P6647 ?videoGame. ?videoGame rdfs:label ?videoGameLabel. FILTER(LANG(?videoGameLabel) = "en") }}
          OPTIONAL {{ ?song wdt:P495 ?country. ?country rdfs:label ?countryLabel. FILTER(LANG(?countryLabel) = "en") }}
          
          FILTER(?pubDate >= "2000-01-01T00:00:00Z"^^xsd:dateTime)
        }}
        LIMIT {limit}
        """
        
        try:
            response = requests.post(
                'https://query.wikidata.org/sparql',
                data={'query': query, 'format': 'json'},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            songs = []
            for binding in data.get('results', {}).get('bindings', []):
                song = self._parse_wikidata_binding(binding)
                if song:
                    songs.append(song)
            
            return songs
            
        except Exception as e:
            logger.error(f"Error fetching from Wikidata: {e}")
            return []
    
    def _fetch_from_musicbrainz(self, limit: int) -> List[Dict[str, Any]]:
        """Fetch songs from MusicBrainz API"""
        songs = []
        
        try:
            # Get popular releases from MusicBrainz
            url = f"https://musicbrainz.org/ws/2/release?limit={limit}&fmt=json"
            headers = {'User-Agent': 'MusicAkenator/1.0'}
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            for release in data.get('releases', []):
                song = self._parse_musicbrainz_release(release)
                if song:
                    songs.append(song)
            
            return songs
            
        except Exception as e:
            logger.error(f"Error fetching from MusicBrainz: {e}")
            return []
    
    def _parse_wikidata_binding(self, binding: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse individual Wikidata result binding"""
        try:
            song = {
                'title': self._get_value(binding, 'songLabel'),
                'artists': [self._get_value(binding, 'artistLabel')] if self._get_value(binding, 'artistLabel') else [],
                'genres': [self._get_value(binding, 'genreLabel')] if self._get_value(binding, 'genreLabel') else [],
                'publication_date': self._get_value(binding, 'pubDate'),
                'duration': int(self._get_value(binding, 'duration', '0')),
                'bpm': int(self._get_value(binding, 'bpm', '0')),
                'country': self._get_value(binding, 'countryLabel'),
                'source': 'wikidata'
            }
            
            # Add optional fields
            if self._get_value(binding, 'awardLabel'):
                song['awards'] = [self._get_value(binding, 'awardLabel')]
            
            if self._get_value(binding, 'labelLabel'):
                song['labels'] = [self._get_value(binding, 'labelLabel')]
            
            return song if song['title'] and song['artists'] else None
            
        except Exception as e:
            logger.warning(f"Error parsing Wikidata binding: {e}")
            return None
    
    def _parse_musicbrainz_release(self, release: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse MusicBrainz release data"""
        try:
            song = {
                'title': release.get('title', ''),
                'artists': [artist.get('name', '') for artist in release.get('artist-credit', [])],
                'genres': [],  # MusicBrainz doesn't provide genres in basic API
                'publication_date': release.get('date', ''),
                'source': 'musicbrainz'
            }
            
            return song if song['title'] and song['artists'] else None
            
        except Exception as e:
            logger.warning(f"Error parsing MusicBrainz release: {e}")
            return None
    
    def _normalize_dataset(self, songs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize metadata consistency across all songs"""
        logger.info("🔧 Normalizing dataset...")
        
        normalized_songs = []
        for song in songs:
            normalized = self._normalize_single_song(song)
            if normalized:
                normalized_songs.append(normalized)
        
        logger.info(f"✅ Normalized {len(normalized_songs)} songs")
        return normalized_songs
    
    def _normalize_single_song(self, song: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize individual song metadata"""
        try:
            normalized = song.copy()
            
            # Normalize genres
            if 'genres' in normalized:
                normalized['genres'] = [
                    self.genre_normalization.get(genre.lower(), genre) 
                    for genre in normalized['genres']
                ]
            
            # Normalize artist names
            if 'artists' in normalized:
                normalized['artists'] = [
                    self._normalize_artist_name(artist) 
                    for artist in normalized['artists']
                ]
            
            # Extract decade/era from release year
            if 'publication_date' in normalized and normalized['publication_date']:
                year = self._extract_year(normalized['publication_date'])
                if year:
                    normalized['release_year'] = year
                    normalized['decade'] = f"{(year // 10) * 10}s"
                    normalized['era'] = self._get_era(year)
            
            # Add boolean attributes
            normalized['is_collaboration'] = len(normalized.get('artists', [])) > 1
            normalized['is_soundtrack'] = bool(normalized.get('films') or normalized.get('tv_series') or normalized.get('video_games'))
            normalized['is_viral_hit'] = normalized.get('billion_views', 0) >= 1000000000
            
            # Normalize duration
            if 'duration' in normalized and normalized['duration']:
                normalized['duration'] = int(normalized['duration'])
                normalized['duration_category'] = self._categorize_duration(normalized['duration'])
            
            # Normalize BPM
            if 'bpm' in normalized and normalized['bpm']:
                normalized['bpm'] = int(normalized['bpm'])
                normalized['bpm_category'] = self._categorize_bpm(normalized['bpm'])
            
            return normalized
            
        except Exception as e:
            logger.warning(f"Error normalizing song {song.get('title', 'Unknown')}: {e}")
            return None
    
    def _validate_dataset(self, songs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate required fields and data quality"""
        logger.info("✅ Validating dataset...")
        
        validated_songs = []
        for i, song in enumerate(songs):
            if self._validate_single_song(song):
                song['id'] = i  # Assign sequential ID
                validated_songs.append(song)
            else:
                logger.warning(f"⚠️  Skipping invalid song: {song.get('title', 'Unknown')}")
        
        logger.info(f"✅ Validated {len(validated_songs)}/{len(songs)} songs")
        return validated_songs
    
    def _validate_single_song(self, song: Dict[str, Any]) -> bool:
        """Validate individual song has required fields"""
        # Check required fields
        for field in self.required_fields:
            if field not in song or not song[field]:
                return False
        
        # Validate title
        title = song.get('title', '').strip()
        if not title or len(title) < 2:
            return False
        
        # Validate artists
        artists = song.get('artists', [])
        if not artists or not isinstance(artists, list):
            return False
        
        # Validate genres
        genres = song.get('genres', [])
        if genres and not isinstance(genres, list):
            return False
        
        # Validate publication date
        pub_date = song.get('publication_date', '')
        if pub_date and not self._is_valid_date(pub_date):
            return False
        
        return True
    
    def _remove_duplicates(self, songs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate songs based on title + artist combination"""
        logger.info("🔄 Removing duplicates...")
        
        seen = set()
        unique_songs = []
        
        for song in songs:
            # Create unique key from title + primary artist
            title = song.get('title', '').lower().strip()
            artists = song.get('artists', [])
            primary_artist = artists[0].lower().strip() if artists else ''
            
            key = f"{title}_{primary_artist}"
            
            if key not in seen:
                seen.add(key)
                unique_songs.append(song)
            else:
                logger.debug(f"Removing duplicate: {title} by {primary_artist}")
        
        logger.info(f"✅ Removed {len(songs) - len(unique_songs)} duplicates")
        return unique_songs
    
    def _load_existing_dataset(self) -> List[Dict[str, Any]]:
        """Load existing dataset from file"""
        try:
            from backend.logic.kg_loader import load_dataset
            return load_dataset()
        except Exception as e:
            logger.error(f"Error loading existing dataset: {e}")
            return []
    
    def _save_dataset(self, songs: List[Dict[str, Any]]) -> None:
        """Save expanded dataset to file"""
        try:
            from backend.logic.kg_loader import save_dataset
            save_dataset(songs)
            logger.info(f"💾 Saved {len(songs)} songs to dataset")
        except Exception as e:
            logger.error(f"Error saving dataset: {e}")
    
    def _get_value(self, binding: Dict[str, Any], key: str, default: str = '') -> str:
        """Extract value from Wikidata binding"""
        return binding.get(key, {}).get('value', default)
    
    def _extract_year(self, date_str: str) -> Optional[int]:
        """Extract year from date string"""
        if not date_str:
            return None
        
        # Try different date formats
        patterns = [
            r'(\d{4})',  # YYYY
            r'(\d{4})-\d{2}-\d{2}',  # YYYY-MM-DD
            r'(\d{4})-\d{2}-\d{2}T',  # YYYY-MM-DDT
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_str)
            if match:
                return int(match.group(1))
        
        return None
    
    def _get_era(self, year: int) -> str:
        """Get era from year"""
        if year < 1960:
            return "Classic Era"
        elif year < 1970:
            return "60s Era"
        elif year < 1980:
            return "70s Era"
        elif year < 1990:
            return "80s Era"
        elif year < 2000:
            return "90s Era"
        elif year < 2010:
            return "2000s Era"
        else:
            return "2010s+ Era"
    
    def _categorize_duration(self, duration: int) -> str:
        """Categorize song duration"""
        if duration < 120:
            return "Short"
        elif duration < 240:
            return "Medium"
        elif duration < 360:
            return "Long"
        else:
            return "Very Long"
    
    def _categorize_bpm(self, bpm: int) -> str:
        """Categorize BPM"""
        if bpm < 90:
            return "Slow"
        elif bpm < 120:
            return "Moderate"
        elif bpm < 140:
            return "Fast"
        else:
            return "Very Fast"
    
    def _normalize_artist_name(self, artist: str) -> str:
        """Normalize artist name variations"""
        if not artist:
            return ""
        
        normalized = artist.strip()
        
        # Apply normalization map
        normalized = self.artist_normalization.get(normalized.lower(), normalized)
        
        # Clean up extra spaces and capitalization
        normalized = ' '.join(normalized.split())
        return normalized
    
    def _is_valid_date(self, date_str: str) -> bool:
        """Validate date string format"""
        if not date_str:
            return True  # Optional field
        
        # Check for common date patterns
        patterns = [
            r'\d{4}-\d{2}-\d{2}',
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
            r'\d{4}'
        ]
        
        return any(re.match(pattern, date_str) for pattern in patterns)
    
    def _build_genre_normalization_map(self) -> Dict[str, str]:
        """Build genre synonym normalization map"""
        return {
            # Electronic subgenres -> pop
            'electropop': 'pop',
            'synth-pop': 'pop',
            'dance-pop': 'pop',
            'electro house': 'pop',
            'tropical house': 'pop',
            
            # Rock subgenres -> rock
            'pop rock': 'rock',
            'indie rock': 'rock',
            'alternative rock': 'rock',
            'hard rock': 'rock',
            
            # Hip-hop variations
            'hip hop': 'hip-hop',
            'rap': 'hip-hop',
            
            # R&B variations
            'rhythm and blues': 'r&b',
            'rnb': 'r&b',
            
            # Electronic variations
            'edm': 'electronic',
            'techno': 'electronic',
            'house': 'electronic',
            'trance': 'electronic',
            
            # Pop variations
            'indie pop': 'pop',
            'art pop': 'pop',
            'dream pop': 'pop',
            
            # Country variations
            'country pop': 'country',
            'bro-country': 'country',
            'country rock': 'country',
        }
    
    def _build_artist_normalization_map(self) -> Dict[str, str]:
        """Build artist name normalization map"""
        return {
            # Common variations
            'lady gaga': 'Lady Gaga',
            'taylor swift': 'Taylor Swift',
            'ed sheeran': 'Ed Sheeran',
            'the weeknd': 'The Weeknd',
            'dua lipa': 'Dua Lipa',
            'harry styles': 'Harry Styles',
            'olivia rodrigo': 'Olivia Rodrigo',
            'ariana grande': 'Ariana Grande',
            'post malone': 'Post Malone',
            'miley cyrus': 'Miley Cyrus',
            'sza': 'SZA',
            'sam smith': 'Sam Smith',
            'beyoncé': 'Beyoncé',
            'justin bieber': 'Justin Bieber',
        }


def expand_dataset_pipeline(target_size: int = 500) -> List[Dict[str, Any]]:
    """Main function to expand dataset"""
    pipeline = DatasetPipeline()
    expanded_songs = pipeline.expand_dataset(target_size)
    pipeline._save_dataset(expanded_songs)
    return expanded_songs


if __name__ == "__main__":
    # Example usage
    expanded_songs = expand_dataset_pipeline(500)
    print(f"🎉 Expanded dataset to {len(expanded_songs)} songs!")
