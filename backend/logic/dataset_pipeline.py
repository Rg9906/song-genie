"""
Scalable Dataset Expansion Pipeline
Automated metadata extraction, Wikidata ingestion, data cleaning, and duplicate detection
"""

import json
import os
import logging
import requests
import time
from typing import List, Dict, Any, Set, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import sqlite3
from collections import defaultdict, Counter
import re
import unicodedata

from backend.logic.enterprise_engine import SongMetadata, DataValidator, SchemaManager

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for dataset expansion pipeline"""
    wikidata_endpoint: str = "https://query.wikidata.org/sparql"
    request_timeout: int = 30
    max_retries: int = 3
    batch_size: int = 100
    duplicate_threshold: float = 0.8
    min_data_quality: float = 0.5
    enable_caching: bool = True
    cache_ttl_hours: int = 24
    parallel_processing: bool = True
    max_workers: int = 4


@dataclass
class ExtractionResult:
    """Result of data extraction"""
    songs: List[Dict[str, Any]] = field(default_factory=list)
    total_found: int = 0
    total_processed: int = 0
    duplicates_found: int = 0
    errors: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    quality_score: float = 0.0


class WikidataExtractor:
    """Extract song data from Wikidata with advanced SPARQL queries"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Music-Akenator/1.0 (Educational Dataset Expansion)',
            'Accept': 'application/sparql-results+json'
        })
    
    def extract_songs(self, limit: int = 1000, genres: List[str] = None, 
                     era_start: int = None, era_end: int = None) -> ExtractionResult:
        """Extract songs from Wikidata with optional filtering"""
        start_time = time.time()
        result = ExtractionResult()
        
        try:
            # Build comprehensive SPARQL query
            sparql_query = self._build_comprehensive_query(limit, genres, era_start, era_end)
            
            # Execute query with retries
            data = self._execute_sparql_with_retry(sparql_query)
            
            if not data:
                logger.error("No data returned from Wikidata")
                return result
            
            # Process results
            songs = self._process_wikidata_results(data)
            result.songs = songs
            result.total_found = len(songs)
            result.total_processed = len(songs)
            
            # Calculate quality score
            result.quality_score = self._calculate_data_quality(songs)
            
            processing_time = time.time() - start_time
            result.processing_time = processing_time
            
            logger.info(f"Extracted {len(songs)} songs from Wikidata in {processing_time:.1f}s")
            
        except Exception as e:
            result.errors.append(str(e))
            logger.error(f"Wikidata extraction failed: {e}")
        
        return result
    
    def _build_comprehensive_query(self, limit: int, genres: List[str] = None, 
                                era_start: int = None, era_end: int = None) -> str:
        """Build comprehensive SPARQL query for song extraction"""
        
        # Base query structure
        query = """
        SELECT DISTINCT ?song ?songLabel ?artist ?artistLabel ?genre ?genreLabel 
               ?publicationDate ?duration ?bpm ?country ?countryLabel ?language 
               ?languageLabel ?billionViews ?award ?awardLabel ?film ?filmLabel 
               ?tvSeries ?tvSeriesLabel ?videoGame ?videoGameLabel 
               ?instrument ?instrumentLabel ?theme ?themeLabel 
               ?chartPosition ?label ?labelLabel ?producer ?producerLabel 
               ?composer ?composerLabel WHERE {
          ?song (wdt:P31/(wdt:P279*)) wd:Q134556;  # Instance of song
                rdfs:label ?songLabel.
          
          # Optional artist information
          OPTIONAL {
            ?song wdt:P175 ?artist.
            ?artist rdfs:label ?artistLabel.
            FILTER(LANG(?artistLabel) = "en")
          }
          
          # Optional genre information
          OPTIONAL {
            ?song wdt:P136 ?genre.
            ?genre rdfs:label ?genreLabel.
            FILTER(LANG(?genreLabel) = "en")
          }
          
          # Optional publication date
          OPTIONAL { ?song wdt:P577 ?publicationDate. }
          
          # Optional duration
          OPTIONAL { ?song wdt:P2047 ?duration. }
          
          # Optional BPM (for electronic music)
          OPTIONAL { ?song wdt:P2224 ?bpm. }
          
          # Optional country of origin
          OPTIONAL {
            ?song wdt:P495 ?country.
            ?country rdfs:label ?countryLabel.
            FILTER(LANG(?countryLabel) = "en")
          }
          
          # Optional language
          OPTIONAL {
            ?song wdt:P407 ?language.
            ?language rdfs:label ?languageLabel.
            FILTER(LANG(?languageLabel) = "en")
          }
          
          # Optional billion views (YouTube, etc.)
          OPTIONAL { ?song wdt:P2651 ?billionViews. }
          
          # Optional awards
          OPTIONAL {
            ?song wdt:P166 ?award.
            ?award rdfs:label ?awardLabel.
            FILTER(LANG(?awardLabel) = "en")
          }
          
          # Optional film appearances
          OPTIONAL {
            ?song wdt:P361 ?film.
            ?film rdfs:label ?filmLabel.
            FILTER(LANG(?filmLabel) = "en")
          }
          
          # Optional TV series appearances
          OPTIONAL {
            ?song wdt:P361 ?tvSeries.
            ?tvSeries rdfs:label ?tvSeriesLabel.
            FILTER(LANG(?tvSeriesLabel) = "en")
          }
          
          # Optional video game appearances
          OPTIONAL {
            ?song wdt:P361 ?videoGame.
            ?videoGame rdfs:label ?videoGameLabel.
            FILTER(LANG(?videoGameLabel) = "en")
          }
          
          # Optional instruments
          OPTIONAL {
            ?song wdt:P874 ?instrument.
            ?instrument rdfs:label ?instrumentLabel.
            FILTER(LANG(?instrumentLabel) = "en")
          }
          
          # Optional themes
          OPTIONAL {
            ?song wdt:P921 ?theme.
            ?theme rdfs:label ?themeLabel.
            FILTER(LANG(?themeLabel) = "en")
          }
          
          # Optional chart positions
          OPTIONAL { ?song wdt:P1687 ?chartPosition. }
          
          # Optional record labels
          OPTIONAL {
            ?song wdt:P264 ?label.
            ?label rdfs:label ?labelLabel.
            FILTER(LANG(?labelLabel) = "en")
          }
          
          # Optional producers
          OPTIONAL {
            ?song wdt:P162 ?producer.
            ?producer rdfs:label ?producerLabel.
            FILTER(LANG(?producerLabel) = "en")
          }
          
          # Optional composers
          OPTIONAL {
            ?song wdt:P86 ?composer.
            ?composer rdfs:label ?composerLabel.
            FILTER(LANG(?composerLabel) = "en")
          }
          
          FILTER(LANG(?songLabel) = "en")
        """
        
        # Add genre filters
        if genres:
            genre_filter = "VALUES ?genreLabel { " + " ".join([f'"{g}"' for g in genres]) + " }"
            query = genre_filter + query
        
        # Add era filters
        if era_start and era_end:
            era_filter = f"FILTER(?publicationDate >= \"{era_start}-01-01\"^^xsd:dateTime && ?publicationDate <= \"{era_end}-12-31\"^^xsd:dateTime)"
            query += era_filter
        
        # Add limit
        query += f"\nLIMIT {limit}"
        
        return query
    
    def _execute_sparql_with_retry(self, query: str) -> Optional[Dict[str, Any]]:
        """Execute SPARQL query with retry logic"""
        for attempt in range(self.config.max_retries):
            try:
                response = self.session.post(
                    self.config.wikidata_endpoint,
                    data={'query': query, 'format': 'json'},
                    timeout=self.config.request_timeout
                )
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                if attempt == self.config.max_retries - 1:
                    raise
                logger.warning(f"SPARQL query attempt {attempt + 1} failed: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def _process_wikidata_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process Wikidata results into standardized format"""
        songs = []
        
        if 'results' not in data or 'bindings' not in data['results']:
            return songs
        
        bindings = data['results']['bindings']
        
        # Group by song
        song_groups = defaultdict(list)
        for binding in bindings:
            song_uri = binding.get('song', {}).get('value', '')
            if song_uri:
                song_groups[song_uri].append(binding)
        
        # Process each song
        for song_uri, bindings in song_groups.items():
            song_data = self._extract_song_data(bindings)
            if song_data:
                songs.append(song_data)
        
        return songs
    
    def _extract_song_data(self, bindings: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Extract song data from Wikidata bindings"""
        if not bindings:
            return None
        
        # Get the first binding for basic info
        first_binding = bindings[0]
        
        song_data = {
            'id': hash(song_uri) % 1000000,  # Simple ID generation
            'title': self._clean_text(first_binding.get('songLabel', {}).get('value', '')),
            'artists': [],
            'genres': [],
            'publication_date': None,
            'duration': None,
            'bpm': None,
            'country': None,
            'language': None,
            'billion_views': None,
            'awards': [],
            'films': [],
            'tv_series': [],
            'video_games': [],
            'instruments': [],
            'themes': [],
            'chart_positions': [],
            'labels': [],
            'producers': [],
            'composers': []
        }
        
        # Process all bindings for this song
        for binding in bindings:
            # Artists
            if binding.get('artist', {}).get('value'):
                artist = self._clean_text(binding.get('artistLabel', {}).get('value', ''))
                if artist and artist not in song_data['artists']:
                    song_data['artists'].append(artist)
            
            # Genres
            if binding.get('genre', {}).get('value'):
                genre = self._clean_text(binding.get('genreLabel', {}).get('value', ''))
                if genre and genre not in song_data['genres']:
                    song_data['genres'].append(genre)
            
            # Publication date
            if not song_data['publication_date'] and binding.get('publicationDate', {}).get('value'):
                song_data['publication_date'] = binding['publicationDate']['value']
            
            # Duration
            if not song_data['duration'] and binding.get('duration', {}).get('value'):
                try:
                    song_data['duration'] = int(float(binding['duration']['value']))
                except (ValueError, TypeError):
                    pass
            
            # BPM
            if not song_data['bpm'] and binding.get('bpm', {}).get('value'):
                try:
                    song_data['bpm'] = int(float(binding['bpm']['value']))
                except (ValueError, TypeError):
                    pass
            
            # Country
            if not song_data['country'] and binding.get('country', {}).get('value'):
                song_data['country'] = self._clean_text(binding.get('countryLabel', {}).get('value', ''))
            
            # Language
            if not song_data['language'] and binding.get('language', {}).get('value'):
                song_data['language'] = self._clean_text(binding.get('languageLabel', {}).get('value', ''))
            
            # Billion views
            if not song_data['billion_views'] and binding.get('billionViews', {}).get('value'):
                try:
                    views = int(float(binding['billionViews']['value']))
                    if views >= 1000000000:
                        song_data['billion_views'] = views
                except (ValueError, TypeError):
                    pass
            
            # Awards
            if binding.get('award', {}).get('value'):
                award = self._clean_text(binding.get('awardLabel', {}).get('value', ''))
                if award and award not in song_data['awards']:
                    song_data['awards'].append(award)
            
            # Films
            if binding.get('film', {}).get('value'):
                film = self._clean_text(binding.get('filmLabel', {}).get('value', ''))
                if film and film not in song_data['films']:
                    song_data['films'].append(film)
            
            # TV Series
            if binding.get('tvSeries', {}).get('value'):
                tv_series = self._clean_text(binding.get('tvSeriesLabel', {}).get('value', ''))
                if tv_series and tv_series not in song_data['tv_series']:
                    song_data['tv_series'].append(tv_series)
            
            # Video Games
            if binding.get('videoGame', {}).get('value'):
                video_game = self._clean_text(binding.get('videoGameLabel', {}).get('value', ''))
                if video_game and video_game not in song_data['video_games']:
                    song_data['video_games'].append(video_game)
            
            # Instruments
            if binding.get('instrument', {}).get('value'):
                instrument = self._clean_text(binding.get('instrumentLabel', {}).get('value', ''))
                if instrument and instrument not in song_data['instruments']:
                    song_data['instruments'].append(instrument)
            
            # Themes
            if binding.get('theme', {}).get('value'):
                theme = self._clean_text(binding.get('themeLabel', {}).get('value', ''))
                if theme and theme not in song_data['themes']:
                    song_data['themes'].append(theme)
            
            # Labels
            if binding.get('label', {}).get('value'):
                label = self._clean_text(binding.get('labelLabel', {}).get('value', ''))
                if label and label not in song_data['labels']:
                    song_data['labels'].append(label)
            
            # Producers
            if binding.get('producer', {}).get('value'):
                producer = self._clean_text(binding.get('producerLabel', {}).get('value', ''))
                if producer and producer not in song_data['producers']:
                    song_data['producers'].append(producer)
            
            # Composers
            if binding.get('composer', {}).get('value'):
                composer = self._clean_text(binding.get('composerLabel', {}).get('value', ''))
                if composer and composer not in song_data['composers']:
                    song_data['composers'].append(composer)
        
        # Validate song data
        if not song_data['title'] or not song_data['artists']:
            return None
        
        return song_data
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove language suffixes
        text = re.sub(r'@en$', '', text)
        
        # Normalize unicode
        text = unicodedata.normalize('NFKC', text)
        
        # Strip whitespace
        text = text.strip()
        
        return text
    
    def _calculate_data_quality(self, songs: List[Dict[str, Any]]) -> float:
        """Calculate overall data quality score"""
        if not songs:
            return 0.0
        
        total_score = 0.0
        quality_factors = {
            'title': 0.2,
            'artists': 0.15,
            'genres': 0.15,
            'publication_date': 0.1,
            'duration': 0.1,
            'country': 0.05,
            'language': 0.05,
            'billion_views': 0.05,
            'awards': 0.05,
            'instruments': 0.05,
            'themes': 0.05
        }
        
        for song in songs:
            song_score = 0.0
            
            for factor, weight in quality_factors.items():
                value = song.get(factor)
                if value:
                    if isinstance(value, list):
                        song_score += weight * (min(len(value), 3) / 3)  # Cap at 3 items
                    else:
                        song_score += weight
            
            total_score += song_score
        
        return total_score / len(songs)


class DataCleaner:
    """Clean and normalize extracted data"""
    
    def __init__(self):
        self.genre_mappings = self._load_genre_mappings()
        self.country_mappings = self._load_country_mappings()
    
    def clean_songs(self, songs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean and normalize song data"""
        cleaned_songs = []
        
        for song in songs:
            cleaned_song = self._clean_song(song)
            if cleaned_song:
                cleaned_songs.append(cleaned_song)
        
        logger.info(f"Cleaned {len(cleaned_songs)} songs from {len(songs)} raw songs")
        return cleaned_songs
    
    def _clean_song(self, song: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Clean individual song data"""
        cleaned = song.copy()
        
        # Clean title
        cleaned['title'] = self._clean_title(cleaned.get('title', ''))
        if not cleaned['title']:
            return None
        
        # Clean artists
        cleaned['artists'] = self._clean_list(cleaned.get('artists', []))
        if not cleaned['artists']:
            return None
        
        # Clean genres
        cleaned['genres'] = self._normalize_genres(cleaned.get('genres', []))
        
        # Clean date
        cleaned['publication_date'] = self._clean_date(cleaned.get('publication_date'))
        
        # Clean numeric fields
        cleaned['duration'] = self._clean_numeric(cleaned.get('duration'))
        cleaned['bpm'] = self._clean_numeric(cleaned.get('bpm'))
        cleaned['billion_views'] = self._clean_numeric(cleaned.get('billion_views'))
        
        # Clean country
        cleaned['country'] = self._normalize_country(cleaned.get('country'))
        
        # Clean other lists
        for field in ['awards', 'films', 'tv_series', 'video_games', 'instruments', 
                     'themes', 'labels', 'producers', 'composers']:
            cleaned[field] = self._clean_list(cleaned.get(field, []))
        
        # Validate cleaned song
        validator = DataValidator()
        is_valid, errors = validator.validate_song_metadata(cleaned)
        
        if not is_valid:
            logger.debug(f"Song failed validation: {cleaned['title']} - {errors}")
            return None
        
        return cleaned
    
    def _clean_title(self, title: str) -> str:
        """Clean song title"""
        if not title:
            return ""
        
        # Remove common suffixes
        title = re.sub(r'\s*\([^)]*\)$', '', title)  # Remove parentheses
        title = re.sub(r'\s*\[[^\]]*\]$', '', title)  # Remove brackets
        
        # Clean whitespace
        title = re.sub(r'\s+', ' ', title).strip()
        
        return title
    
    def _clean_list(self, items: List[str]) -> List[str]:
        """Clean list of strings"""
        if not items:
            return []
        
        cleaned = []
        for item in items:
            if item:
                cleaned_item = str(item).strip()
                if cleaned_item and len(cleaned_item) > 1:
                    cleaned.append(cleaned_item)
        
        return list(set(cleaned))  # Remove duplicates
    
    def _normalize_genres(self, genres: List[str]) -> List[str]:
        """Normalize genre names"""
        normalized = []
        
        for genre in genres:
            genre_lower = genre.lower().strip()
            
            # Apply mappings
            for canonical, variants in self.genre_mappings.items():
                if genre_lower in [v.lower() for v in variants]:
                    normalized.append(canonical)
                    break
            else:
                # Use original if no mapping found
                normalized.append(genre.title())
        
        return list(set(normalized))
    
    def _normalize_country(self, country: str) -> Optional[str]:
        """Normalize country name"""
        if not country:
            return None
        
        country_clean = country.strip()
        
        # Apply mappings
        for canonical, variants in self.country_mappings.items():
            if country_clean.lower() in [v.lower() for v in variants]:
                return canonical
        
        return country_clean
    
    def _clean_date(self, date_str: str) -> Optional[str]:
        """Clean and normalize date"""
        if not date_str:
            return None
        
        try:
            # Try to parse and normalize date
            if '+' in date_str:
                date_str = date_str.split('+')[0]
            
            # Remove timezone info
            date_str = date_str.replace('Z', '')
            
            # Validate date format
            datetime.fromisoformat(date_str)
            
            return date_str
            
        except (ValueError, TypeError):
            return None
    
    def _clean_numeric(self, value: Any) -> Optional[int]:
        """Clean numeric value"""
        if value is None:
            return None
        
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None
    
    def _load_genre_mappings(self) -> Dict[str, List[str]]:
        """Load genre normalization mappings"""
        return {
            "Pop": ["pop", "pop music", "popular music"],
            "Rock": ["rock", "rock music", "rock and roll"],
            "Electronic": ["electronic", "electronic music", "edm"],
            "Hip-Hop": ["hip-hop", "hip hop", "hiphop"],
            "Jazz": ["jazz", "jazz music"],
            "Classical": ["classical", "classical music", "orchestral"],
            "Country": ["country", "country music"],
            "Blues": ["blues", "blues music"],
            "R&B": ["r&b", "rnb", "rhythm and blues"],
            "Folk": ["folk", "folk music"],
            "Reggae": ["reggae", "reggae music"],
            "Metal": ["metal", "heavy metal"],
            "Punk": ["punk", "punk rock"],
            "Dance": ["dance", "dance music"],
            "Soul": ["soul", "soul music"],
            "Funk": ["funk", "funk music"]
        }
    
    def _load_country_mappings(self) -> Dict[str, List[str]]:
        """Load country normalization mappings"""
        return {
            "United States": ["USA", "US", "United States of America", "America"],
            "United Kingdom": ["UK", "Great Britain", "Britain"],
            "Canada": ["CA"],
            "Australia": ["AU"],
            "Germany": ["DE"],
            "France": ["FR"],
            "Japan": ["JP"],
            "Brazil": ["BR"],
            "Spain": ["ES"],
            "Italy": ["IT"],
            "Netherlands": ["NL", "Holland"],
            "Sweden": ["SE"],
            "Norway": ["NO"],
            "Denmark": ["DK"],
            "Finland": ["FI"],
            "Mexico": ["MX"],
            "Argentina": ["AR"],
            "Chile": ["CL"],
            "South Korea": ["KR", "Korea"],
            "China": ["CN"],
            "India": ["IN"],
            "Russia": ["RU"]
        }


class DuplicateDetector:
    """Detect and handle duplicate songs"""
    
    def __init__(self, threshold: float = 0.8):
        self.threshold = threshold
    
    def find_duplicates(self, songs: List[Dict[str, Any]]) -> List[List[int]]:
        """Find groups of duplicate songs"""
        if len(songs) < 2:
            return []
        
        # Create similarity matrix
        similarity_matrix = self._create_similarity_matrix(songs)
        
        # Find duplicate clusters
        duplicate_groups = self._find_duplicate_clusters(similarity_matrix, self.threshold)
        
        return duplicate_groups
    
    def remove_duplicates(self, songs: List[Dict[str, Any]], keep_strategy: str = "best") -> List[Dict[str, Any]]:
        """Remove duplicates based on strategy"""
        duplicate_groups = self.find_duplicates(songs)
        
        if not duplicate_groups:
            return songs
        
        # Indices to remove
        to_remove = set()
        
        for group in duplicate_groups:
            if len(group) < 2:
                continue
            
            if keep_strategy == "best":
                # Keep the song with the most complete data
                best_idx = max(group, key=lambda i: self._calculate_completeness(songs[i]))
                to_remove.update(set(group) - {best_idx})
            elif keep_strategy == "first":
                # Keep the first one
                to_remove.update(set(group[1:]))
            elif keep_strategy == "random":
                # Keep a random one
                import random
                keep_idx = random.choice(group)
                to_remove.update(set(group) - {keep_idx})
        
        # Remove duplicates
        cleaned_songs = [song for i, song in enumerate(songs) if i not in to_remove]
        
        logger.info(f"Removed {len(to_remove)} duplicates from {len(songs)} songs")
        return cleaned_songs
    
    def _create_similarity_matrix(self, songs: List[Dict[str, Any]]) -> np.ndarray:
        """Create similarity matrix between songs"""
        n = len(songs)
        matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(i + 1, n):
                similarity = self._calculate_similarity(songs[i], songs[j])
                matrix[i][j] = similarity
                matrix[j][i] = similarity
        
        return matrix
    
    def _calculate_similarity(self, song1: Dict[str, Any], song2: Dict[str, Any]) -> float:
        """Calculate similarity between two songs"""
        similarity = 0.0
        total_weight = 0.0
        
        # Title similarity (weight: 0.4)
        title_sim = self._string_similarity(song1.get('title', ''), song2.get('title', ''))
        similarity += title_sim * 0.4
        total_weight += 0.4
        
        # Artist similarity (weight: 0.3)
        artist_sim = self._list_similarity(song1.get('artists', []), song2.get('artists', []))
        similarity += artist_sim * 0.3
        total_weight += 0.3
        
        # Genre similarity (weight: 0.2)
        genre_sim = self._list_similarity(song1.get('genres', []), song2.get('genres', []))
        similarity += genre_sim * 0.2
        total_weight += 0.2
        
        # Duration similarity (weight: 0.1)
        duration1 = song1.get('duration')
        duration2 = song2.get('duration')
        if duration1 and duration2:
            duration_sim = 1.0 - abs(duration1 - duration2) / max(duration1, duration2)
            similarity += duration_sim * 0.1
            total_weight += 0.1
        
        return similarity / total_weight if total_weight > 0 else 0.0
    
    def _string_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity using Jaccard on words"""
        if not str1 or not str2:
            return 0.0
        
        words1 = set(str1.lower().split())
        words2 = set(str2.lower().split())
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _list_similarity(self, list1: List[str], list2: List[str]) -> float:
        """Calculate list similarity using Jaccard"""
        if not list1 or not list2:
            return 0.0
        
        set1 = set(item.lower() for item in list1)
        set2 = set(item.lower() for item in list2)
        
        intersection = set1 & set2
        union = set1 | set2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _find_duplicate_clusters(self, similarity_matrix: np.ndarray, threshold: float) -> List[List[int]]:
        """Find clusters of similar songs"""
        n = similarity_matrix.shape[0]
        visited = [False] * n
        clusters = []
        
        for i in range(n):
            if visited[i]:
                continue
            
            cluster = []
            to_visit = [i]
            
            while to_visit:
                current = to_visit.pop()
                if visited[current]:
                    continue
                
                visited[current] = True
                cluster.append(current)
                
                # Find similar songs
                for j in range(n):
                    if not visited[j] and similarity_matrix[current][j] >= threshold:
                        to_visit.append(j)
            
            if len(cluster) > 1:
                clusters.append(cluster)
        
        return clusters
    
    def _calculate_completeness(self, song: Dict[str, Any]) -> int:
        """Calculate data completeness score for a song"""
        score = 0
        
        # Basic fields
        if song.get('title'):
            score += 2
        if song.get('artists'):
            score += 2
        if song.get('genres'):
            score += 2
        
        # Optional fields
        optional_fields = ['publication_date', 'duration', 'bpm', 'country', 'language',
                          'billion_views', 'awards', 'films', 'tv_series', 'instruments',
                          'themes', 'labels', 'producers', 'composers']
        
        for field in optional_fields:
            value = song.get(field)
            if value:
                if isinstance(value, list):
                    score += min(len(value), 2)
                else:
                    score += 1
        
        return score


class DatasetPipeline:
    """Complete dataset expansion pipeline"""
    
    def __init__(self, data_dir: str, config: PipelineConfig = None):
        self.data_dir = data_dir
        self.config = config or PipelineConfig()
        
        # Initialize components
        self.extractor = WikidataExtractor(self.config)
        self.cleaner = DataCleaner()
        self.duplicate_detector = DuplicateDetector(self.config.duplicate_threshold)
        
        # Database for caching
        self.cache_db = os.path.join(data_dir, "pipeline_cache.db")
        self._init_cache_db()
        
        logger.info("DatasetPipeline initialized")
    
    def _init_cache_db(self):
        """Initialize cache database"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS extraction_cache (
                query_hash TEXT PRIMARY KEY,
                data TEXT,
                timestamp DATETIME,
                ttl_hours INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def expand_dataset(self, target_size: int = 1000, genres: List[str] = None,
                      era_start: int = None, era_end: int = None) -> ExtractionResult:
        """Expand dataset to target size"""
        logger.info(f"Starting dataset expansion to {target_size} songs")
        
        start_time = time.time()
        result = ExtractionResult()
        
        try:
            # Load existing songs
            existing_songs = self._load_existing_songs()
            current_size = len(existing_songs)
            
            if current_size >= target_size:
                logger.info(f"Dataset already has {current_size} songs (target: {target_size})")
                result.songs = existing_songs
                result.total_found = current_size
                return result
            
            # Calculate how many more songs needed
            needed = target_size - current_size
            
            # Extract new songs
            extraction_result = self.extractor.extract_songs(
                limit=needed * 2,  # Extract more to account for cleaning/deduplication
                genres=genres,
                era_start=era_start,
                era_end=era_end
            )
            
            # Clean extracted data
            cleaned_songs = self.cleaner.clean_songs(extraction_result.songs)
            
            # Remove duplicates
            all_songs = existing_songs + cleaned_songs
            deduplicated_songs = self.duplicate_detector.remove_duplicates(all_songs)
            
            # Validate final dataset
            validated_songs = []
            validator = DataValidator()
            
            for song in deduplicated_songs:
                is_valid, errors = validator.validate_song_metadata(song)
                if is_valid:
                    validated_songs.append(song)
                else:
                    logger.debug(f"Song failed validation: {song.get('title', 'Unknown')}")
            
            # Save expanded dataset
            self._save_dataset(validated_songs)
            
            # Update result
            result.songs = validated_songs
            result.total_found = len(validated_songs)
            result.total_processed = len(cleaned_songs)
            result.duplicates_found = len(all_songs) - len(deduplicated_songs)
            result.quality_score = self.extractor._calculate_data_quality(validated_songs)
            result.processing_time = time.time() - start_time
            
            logger.info(f"Dataset expansion completed: {len(validated_songs)} songs "
                       f"(added {len(validated_songs) - current_size})")
            
        except Exception as e:
            result.errors.append(str(e))
            logger.error(f"Dataset expansion failed: {e}")
        
        return result
    
    def _load_existing_songs(self) -> List[Dict[str, Any]]:
        """Load existing song dataset"""
        try:
            songs_path = os.path.join(self.data_dir, "songs_kg.json")
            
            if os.path.exists(songs_path):
                with open(songs_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.info("No existing dataset found")
                return []
                
        except Exception as e:
            logger.error(f"Failed to load existing dataset: {e}")
            return []
    
    def _save_dataset(self, songs: List[Dict[str, Any]]):
        """Save expanded dataset"""
        try:
            songs_path = os.path.join(self.data_dir, "songs_kg.json")
            
            # Create backup
            if os.path.exists(songs_path):
                backup_path = f"{songs_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(songs_path, backup_path)
                logger.info(f"Created backup: {backup_path}")
            
            # Save new dataset
            with open(songs_path, 'w', encoding='utf-8') as f:
                json.dump(songs, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(songs)} songs to {songs_path}")
            
        except Exception as e:
            logger.error(f"Failed to save dataset: {e}")
            raise
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get pipeline status and statistics"""
        existing_songs = self._load_existing_songs()
        
        return {
            "current_dataset_size": len(existing_songs),
            "config": {
                "wikidata_endpoint": self.config.wikidata_endpoint,
                "duplicate_threshold": self.config.duplicate_threshold,
                "min_data_quality": self.config.min_data_quality
            },
            "components": {
                "extractor": "ready",
                "cleaner": "ready", 
                "duplicate_detector": "ready"
            },
            "cache_enabled": self.config.enable_caching,
            "cache_db": self.cache_db if os.path.exists(self.cache_db) else None
        }


def expand_dataset_command(target_size: int = 1000, data_dir: str = None) -> ExtractionResult:
    """Command-line interface for dataset expansion"""
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    
    pipeline = DatasetPipeline(data_dir)
    
    # Example: Expand with popular genres
    popular_genres = ["pop", "rock", "electronic", "hip-hop", "jazz"]
    
    result = pipeline.expand_dataset(
        target_size=target_size,
        genres=popular_genres,
        era_start=1990,
        era_end=2023
    )
    
    print(f"Dataset expansion completed!")
    print(f"Total songs: {result.total_found}")
    print(f"Processing time: {result.processing_time:.1f}s")
    print(f"Quality score: {result.quality_score:.3f}")
    print(f"Duplicates removed: {result.duplicates_found}")
    
    if result.errors:
        print(f"Errors: {len(result.errors)}")
        for error in result.errors[:5]:  # Show first 5 errors
            print(f"  - {error}")
    
    return result


if __name__ == "__main__":
    import shutil
    
    # Run dataset expansion when executed directly
    logging.basicConfig(level=logging.INFO)
    
    result = expand_dataset_command(target_size=500)
    print(f"\nExpansion result: {result.total_found} songs processed")
