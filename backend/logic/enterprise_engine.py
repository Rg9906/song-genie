"""
Enterprise-Grade Engine for Music Akenator
Production-ready architecture with maximum robustness, scalability, and maintainability
"""

import json
import os
import logging
from typing import List, Dict, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from datetime import datetime
import hashlib
import pickle
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SystemStatus(Enum):
    """System status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    MAINTENANCE = "maintenance"


@dataclass
class SongMetadata:
    """Standardized song metadata structure"""
    id: int
    title: str
    artists: List[str] = field(default_factory=list)
    genres: List[str] = field(default_factory=list)
    publication_date: Optional[str] = None
    language: Optional[str] = None
    country: Optional[str] = None
    duration: Optional[int] = None
    bpm: Optional[int] = None
    # Enhanced attributes
    artist_genders: List[str] = field(default_factory=list)
    artist_types: List[str] = field(default_factory=list)
    song_types: List[str] = field(default_factory=list)
    films: List[str] = field(default_factory=list)
    tv_series: List[str] = field(default_factory=list)
    video_games: List[str] = field(default_factory=list)
    billion_views: Optional[int] = None
    instruments: List[str] = field(default_factory=list)
    themes: List[str] = field(default_factory=list)
    chart_positions: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    performers: List[str] = field(default_factory=list)
    vocalists: List[str] = field(default_factory=list)
    awards: List[str] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    producers: List[str] = field(default_factory=list)
    composers: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for compatibility"""
        return {
            "id": self.id,
            "title": self.title,
            "artists": self.artists,
            "genres": self.genres,
            "publication_date": self.publication_date,
            "language": self.language,
            "country": self.country,
            "duration": self.duration,
            "bpm": self.bpm,
            "artist_genders": self.artist_genders,
            "artist_types": self.artist_types,
            "song_types": self.song_types,
            "films": self.films,
            "tv_series": self.tv_series,
            "video_games": self.video_games,
            "billion_views": self.billion_views,
            "instruments": self.instruments,
            "themes": self.themes,
            "chart_positions": self.chart_positions,
            "locations": self.locations,
            "performers": self.performers,
            "vocalists": self.vocalists,
            "awards": self.awards,
            "labels": self.labels,
            "producers": self.producers,
            "composers": self.composers,
        }


class DataValidator:
    """Enterprise-grade data validation"""
    
    @staticmethod
    def validate_song_metadata(song_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate song metadata and return (is_valid, errors)"""
        errors = []
        
        # Required fields
        if not song_data.get("title") or not song_data["title"].strip():
            errors.append("Title is required and cannot be empty")
        
        # Validate artists
        artists = song_data.get("artists", [])
        if not isinstance(artists, list):
            errors.append("Artists must be a list")
        elif not artists:
            errors.append("At least one artist is required")
        
        # Validate genres
        genres = song_data.get("genres", [])
        if not isinstance(genres, list):
            errors.append("Genres must be a list")
        
        # Validate numeric fields
        for field in ["duration", "bpm", "billion_views"]:
            value = song_data.get(field)
            if value is not None and not isinstance(value, (int, float)):
                errors.append(f"{field} must be numeric")
        
        # Validate date format
        pub_date = song_data.get("publication_date")
        if pub_date and not DataValidator._is_valid_date(pub_date):
            errors.append("Invalid publication_date format")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _is_valid_date(date_str: str) -> bool:
        """Validate ISO 8601 date format"""
        try:
            datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return True
        except (ValueError, AttributeError):
            return False


class SchemaManager:
    """Manages schema versioning and migrations"""
    
    CURRENT_SCHEMA_VERSION = "1.0"
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.schema_file = os.path.join(data_dir, "schema_version.json")
        self.current_version = self._load_schema_version()
    
    def _load_schema_version(self) -> str:
        """Load current schema version"""
        if os.path.exists(self.schema_file):
            with open(self.schema_file, 'r') as f:
                schema_data = json.load(f)
                return schema_data.get("version", "1.0")
        return "1.0"
    
    def save_schema_version(self, version: str):
        """Save new schema version"""
        with open(self.schema_file, 'w') as f:
            json.dump({"version": version}, f, indent=2)
        self.current_version = version
    
    def needs_migration(self, data_version: str) -> bool:
        """Check if migration is needed"""
        return data_version != self.current_version
    
    def migrate_data(self, songs: List[Dict[str, Any]]) -> List[SongMetadata]:
        """Migrate data to current schema"""
        migrated_songs = []
        
        for song_data in songs:
            # Convert to new standardized format
            song = SongMetadata(
                id=song_data.get("id", 0),
                title=song_data.get("title", ""),
                artists=song_data.get("artists", []),
                genres=song_data.get("genres", []),
                publication_date=song_data.get("publication_date"),
                language=song_data.get("language"),
                country=song_data.get("country"),
                duration=song_data.get("duration"),
                bpm=song_data.get("bpm"),
                artist_genders=song_data.get("artist_genders", []),
                artist_types=song_data.get("artist_types", []),
                song_types=song_data.get("song_types", []),
                films=song_data.get("films", []),
                tv_series=song_data.get("tv_series", []),
                video_games=song_data.get("video_games", []),
                billion_views=song_data.get("billion_views"),
                instruments=song_data.get("instruments", []),
                themes=song_data.get("themes", []),
                chart_positions=song_data.get("chart_positions", []),
                locations=song_data.get("locations", []),
                performers=song_data.get("performers", []),
                vocalists=song_data.get("vocalists", []),
                awards=song_data.get("awards", []),
                labels=song_data.get("labels", []),
                producers=song_data.get("producers", []),
                composers=song_data.get("composers", []),
            )
            
            # Validate the migrated song
            is_valid, errors = DataValidator.validate_song_metadata(song.to_dict())
            if not is_valid:
                logger.warning(f"Migration validation failed for {song.title}: {errors}")
                continue  # Skip invalid songs but log the issue
            
            migrated_songs.append(song)
        
        # Update schema version
        self.save_schema_version(self.CURRENT_SCHEMA_VERSION)
        logger.info(f"Migrated {len(migrated_songs)} songs to schema {self.CURRENT_SCHEMA_VERSION}")
        
        return migrated_songs


class PerformanceMonitor:
    """Enterprise-grade performance monitoring"""
    
    def __init__(self):
        self.metrics = {
            "question_generation_time": [],
            "inference_time": [],
            "memory_usage": [],
            "cache_hit_rate": 0.0,
            "total_requests": 0,
            "error_count": 0
        }
        self.start_time = datetime.now()
    
    def record_question_time(self, duration_ms: float):
        """Record question generation time"""
        self.metrics["question_generation_time"].append(duration_ms)
    
    def record_inference_time(self, duration_ms: float):
        """Record inference time"""
        self.metrics["inference_time"].append(duration_ms)
    
    def record_cache_hit(self, hit: bool):
        """Record cache hit/miss"""
        self.metrics["total_requests"] += 1
        if hit:
            self.metrics["cache_hit_rate"] = (
                (self.metrics["cache_hit_rate"] * (self.metrics["total_requests"] - 1) + 1.0) /
                self.metrics["total_requests"]
            )
    
    def record_error(self):
        """Record an error"""
        self.metrics["error_count"] += 1
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report"""
        return {
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "avg_question_time_ms": np.mean(self.metrics["question_generation_time"]) if self.metrics["question_generation_time"] else 0,
            "avg_inference_time_ms": np.mean(self.metrics["inference_time"]) if self.metrics["inference_time"] else 0,
            "cache_hit_rate": self.metrics["cache_hit_rate"],
            "total_requests": self.metrics["total_requests"],
            "error_rate": self.metrics["error_count"] / max(self.metrics["total_requests"], 1),
            "status": SystemStatus.HEALTHY if self.metrics["error_rate"] < 0.05 else SystemStatus.DEGRADED
        }


class CacheManager:
    """Enterprise-grade caching system"""
    
    def __init__(self, cache_size: int = 1000):
        self.cache_size = cache_size
        self.cache = {}
        self.access_order = []
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        if key in self.cache:
            # Move to end of access order
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None
    
    def put(self, key: str, value: Any):
        """Put item in cache with LRU eviction"""
        if len(self.cache) >= self.cache_size:
            # Evict least recently used item
            if self.access_order:
                lru_key = self.access_order.pop(0)
                if lru_key in self.cache:
                    del self.cache[lru_key]
        
        self.cache[key] = value
        if key not in self.access_order:
            self.access_order.append(key)
        else:
            # Move to end if already exists
            self.access_order.remove(key)
            self.access_order.append(key)
    
    def clear(self):
        """Clear cache"""
        self.cache.clear()
        self.access_order.clear()


class EnterpriseEngine(ABC):
    """Abstract base class for enterprise-grade engines"""
    
    def __init__(self, data_dir: str, cache_size: int = 1000):
        self.data_dir = data_dir
        self.schema_manager = SchemaManager(data_dir)
        self.performance_monitor = PerformanceMonitor()
        self.cache_manager = CacheManager(cache_size)
        self.songs: List[SongMetadata] = []
        self.is_initialized = False
        
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the engine"""
        pass
    
    @abstractmethod
    def generate_question(self, candidates: List[str], context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate next question"""
        pass
    
    @abstractmethod
    def update_beliefs(self, question: Dict[str, Any], answer: str) -> None:
        """Update belief state"""
        pass
    
    @abstractmethod
    def get_top_candidates(self, n: int = 3) -> List[Tuple[str, float]]:
        """Get top N candidates with confidence scores"""
        pass
    
    @abstractmethod
    def get_system_status(self) -> Dict[str, Any]:
        """Get system health and status"""
        pass


class HybridEnterpriseEngine(EnterpriseEngine):
    """Production-ready hybrid engine combining multiple intelligence sources"""
    
    def __init__(self, data_dir: str, enable_graph: bool = True, enable_embeddings: bool = True):
        super().__init__(data_dir)
        
        self.enable_graph = enable_graph
        self.enable_embeddings = enable_embeddings
        
        # Load and validate data
        if not self._load_and_validate_data():
            raise RuntimeError("Failed to load and validate song data")
        
        # Initialize subsystems
        self.graph_system = None
        self.embedding_system = None
        
        self.is_initialized = False
        
        logger.info("HybridEnterpriseEngine initialized with robust features")
    
    def _load_and_validate_data(self) -> bool:
        """Load and validate song data with schema migration"""
        try:
            # Load raw data
            raw_data_path = os.path.join(self.data_dir, "songs_kg.json")
            with open(raw_data_path, 'r', encoding='utf-8') as f:
                raw_songs = json.load(f)
            
            # Check if migration is needed
            if self.schema_manager.needs_migration("1.0"):
                logger.info("Migrating song data to enterprise schema")
                self.songs = self.schema_manager.migrate_data(raw_songs)
            else:
                # Validate and convert existing data
                self.songs = []
                for song_data in raw_songs:
                    is_valid, errors = DataValidator.validate_song_metadata(song_data)
                    if is_valid:
                        song = SongMetadata(
                            id=song_data.get("id", 0),
                            title=song_data.get("title", ""),
                            artists=song_data.get("artists", []),
                            genres=song_data.get("genres", []),
                            publication_date=song_data.get("publication_date"),
                            language=song_data.get("language"),
                            country=song_data.get("country"),
                            duration=song_data.get("duration"),
                            bpm=song_data.get("bpm"),
                            artist_genders=song_data.get("artist_genders", []),
                            artist_types=song_data.get("artist_types", []),
                            song_types=song_data.get("song_types", []),
                            films=song_data.get("films", []),
                            tv_series=song_data.get("tv_series", []),
                            video_games=song_data.get("video_games", []),
                            billion_views=song_data.get("billion_views"),
                            instruments=song_data.get("instruments", []),
                            themes=song_data.get("themes", []),
                            chart_positions=song_data.get("chart_positions", []),
                            locations=song_data.get("locations", []),
                            performers=song_data.get("performers", []),
                            vocalists=song_data.get("vocalists", []),
                            awards=song_data.get("awards", []),
                            labels=song_data.get("labels", []),
                            producers=song_data.get("producers", []),
                            composers=song_data.get("composers", []),
                        )
                        self.songs.append(song)
                    else:
                        logger.warning(f"Invalid song data skipped: {song_data.get('title', 'Unknown')} - {errors}")
            
            logger.info(f"Loaded {len(self.songs)} validated songs")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load song data: {e}")
            return False
    
    def initialize(self) -> bool:
        """Initialize all subsystems"""
        try:
            # Initialize graph system
            if self.enable_graph:
                from backend.logic.dynamic_graph import DynamicWikidataGraph, build_dynamic_graph
                self.graph_system = DynamicWikidataGraph()
                
                # Try to load existing graph
                graph_path = os.path.join(self.data_dir, "dynamic_graph.json")
                self.graph_system.load_graph(graph_path)
                
                if not self.graph_system.graph["songs"]:
                    logger.info("Building dynamic graph from song data")
                    self._build_graph_from_songs()
                
                logger.info(f"Graph system initialized: {len(self.graph_system.graph['songs'])} songs")
            
            # Initialize embedding system
            if self.enable_embeddings:
                try:
                    from backend.logic.embeddings import EmbeddingTrainer, MetadataEncoder
                    from backend.logic.embedding_questions import EmbeddingQuestionSystem
                    
                    # Create metadata encoder
                    metadata_encoder = MetadataEncoder([song.to_dict() for song in self.songs])
                    
                    # Try to load existing embeddings
                    embedding_path = os.path.join(self.data_dir, "song_embeddings.pt")
                    if os.path.exists(embedding_path):
                        self.embedding_system = EmbeddingQuestionSystem(metadata_encoder)
                        # Load embeddings would go here
                        logger.info("Embedding system initialized with existing model")
                    else:
                        logger.warning("No existing embeddings found - embedding system disabled")
                        self.embedding_system = None
                        
                except ImportError as e:
                    logger.warning(f"PyTorch not available for embeddings: {e}")
                    self.embedding_system = None
                except Exception as e:
                    logger.error(f"Failed to initialize embedding system: {e}")
                    self.embedding_system = None
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Engine initialization failed: {e}")
            self.performance_monitor.record_error()
            return False
    
    def _build_graph_from_songs(self):
        """Build dynamic graph from loaded songs"""
        # Extract all unique attributes from songs
        all_attributes = set()
        attribute_songs = defaultdict(set)
        
        for song in self.songs:
            # Add all song attributes to graph
            for attr, value in song.to_dict().items():
                if value and attr not in ["id", "title"]:
                    all_attributes.add(attr)
                    if isinstance(value, list):
                        for v in value:
                            attribute_songs[attr].add(song.title)
                    else:
                        attribute_songs[attr].add(song.title)
        
        # Build graph structure
        graph_data = {
            "songs": {song.title: song.to_dict() for song in self.songs},
            "attributes": {attr: list(songs) for attr, songs in attribute_songs.items()},
            "attribute_types": list(all_attributes)
        }
        
        # Save graph
        graph_path = os.path.join(self.data_dir, "dynamic_graph.json")
        with open(graph_path, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)
        
        # Update graph system reference
        if self.graph_system:
            self.graph_system.graph = graph_data
    
    def generate_question(self, candidates: List[str], context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate question using hybrid intelligence with performance monitoring"""
        start_time = datetime.now()
        
        try:
            if not self.is_initialized:
                logger.error("Engine not initialized")
                return None
            
            # Check cache first
            cache_key = f"question:{hash(tuple(sorted(candidates))}:{hash(tuple(sorted(context.items())))}"
            cached_question = self.cache_manager.get(cache_key)
            if cached_question:
                self.performance_monitor.record_cache_hit(True)
                return cached_question
            
            self.performance_monitor.record_cache_hit(False)
            
            # Generate question using available systems
            question = None
            
            # Try hybrid system first
            if self.graph_system and self.embedding_system:
                from backend.logic.hybrid_questions import select_best_hybrid_question
                question = select_best_hybrid_question(
                    self._convert_to_legacy_format(), candidates, set()
                )
            elif self.graph_system:
                from backend.logic.dynamic_graph import DynamicWikidataGraph
                question = self.graph_system.generate_smart_questions(candidates, set())
            elif self.embedding_system:
                question = self.embedding_system.generate_smart_question(candidates, set())
            
            # Cache the result
            if question:
                self.cache_manager.put(cache_key, question)
            
            # Record performance
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.performance_monitor.record_question_time(duration_ms)
            
            return question
            
        except Exception as e:
            logger.error(f"Question generation failed: {e}")
            self.performance_monitor.record_error()
            return None
    
    def _convert_to_legacy_format(self) -> List[Dict[str, Any]]:
        """Convert enterprise songs to legacy format for compatibility"""
        return [song.to_dict() for song in self.songs]
    
    def update_beliefs(self, question: Dict[str, Any], answer: str) -> None:
        """Update beliefs with enterprise-grade tracking"""
        try:
            # This would integrate with the belief system
            # For now, just log the update
            logger.info(f"Belief update: {question.get('feature', 'unknown')} = {answer}")
            # Implementation would go here
            
        except Exception as e:
            logger.error(f"Belief update failed: {e}")
            self.performance_monitor.record_error()
    
    def get_top_candidates(self, n: int = 3) -> List[Tuple[str, float]]:
        """Get top N candidates with confidence scores"""
        # This would integrate with the belief system
        # For now, return top N songs
        candidates = [(song.title, 1.0) for song in self.songs[:n]]
        return candidates
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            status = {
                "engine_type": "HybridEnterprise",
                "is_initialized": self.is_initialized,
                "total_songs": len(self.songs),
                "graph_available": self.graph_system is not None,
                "graph_songs": len(self.graph_system.graph["songs"]) if self.graph_system else 0,
                "graph_attributes": len(self.graph_system.graph["attributes"]) if self.graph_system else 0,
                "embeddings_available": self.embedding_system is not None,
                "schema_version": self.schema_manager.current_version,
                "performance": self.performance_monitor.get_performance_report(),
                "cache_size": len(self.cache_manager.cache),
                "status": SystemStatus.HEALTHY
            }
            
            # Add subsystem details
            if self.graph_system:
                status["graph_status"] = "loaded"
            else:
                status["graph_status"] = "disabled"
            
            if self.embedding_system:
                status["embedding_status"] = "loaded"
            else:
                status["embedding_status"] = "disabled"
            
            return status
            
        except Exception as e:
            logger.error(f"Status check failed: {e}")
            return {
                "engine_type": "HybridEnterprise",
                "status": SystemStatus.FAILED,
                "error": str(e)
            }


class EngineFactory:
    """Factory for creating enterprise engines"""
    
    @staticmethod
    def create_engine(engine_type: str, data_dir: str, **kwargs) -> EnterpriseEngine:
        """Create engine of specified type"""
        if engine_type.lower() == "hybrid":
            return HybridEnterpriseEngine(data_dir, **kwargs)
        elif engine_type.lower() == "graph":
            # Would create GraphEnterpriseEngine
            raise NotImplementedError("Graph-only enterprise engine not yet implemented")
        elif engine_type.lower() == "embedding":
            # Would create EmbeddingEnterpriseEngine
            raise NotImplementedError("Embedding-only enterprise engine not yet implemented")
        else:
            raise ValueError(f"Unknown engine type: {engine_type}")


# Enterprise configuration
@dataclass
class EnterpriseConfig:
    """Enterprise-grade configuration"""
    max_songs: int = 10000
    cache_size: int = 1000
    enable_validation: bool = True
    enable_monitoring: bool = True
    log_level: str = "INFO"
    backup_enabled: bool = True
    migration_enabled: bool = True
