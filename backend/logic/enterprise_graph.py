"""
Enterprise-Grade Dynamic Graph System
Advanced graph intelligence with automatic node discovery, weighted edges, and centrality metrics
"""

import json
import os
import logging
from typing import Dict, List, Any, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import networkx as nx
import numpy as np
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class GraphNode:
    """Enhanced graph node with metadata"""
    id: str
    type: str  # 'song', 'attribute', 'value'
    label: str
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class GraphEdge:
    """Enhanced graph edge with weights and metadata"""
    source: str
    target: str
    weight: float = 1.0
    relationship_type: str = "related"
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)


class AttributeNormalizer:
    """Normalizes and standardizes attributes for graph construction"""
    
    # Genre synonym mapping
    GENRE_SYNONYMS = {
        "electropop": ["electro-pop", "electro pop"],
        "dance-pop": ["dance pop", "dancepop"],
        "electro house": ["electro-house", "electro house"],
        "hip-hop": ["hip hop", "hiphop"],
        "r&b": ["rnb", "rhythm and blues"],
        "rock": ["rock music", "rock and roll"],
        "pop": ["pop music", "popular music"],
        "classical": ["classical music", "orchestral"],
        "jazz": ["jazz music", "jazz blues"],
        "electronic": ["electronic music", "edm"],
    }
    
    # Era normalization
    ERA_NORMALIZATION = {
        "1960s": ["1960-1969", "60s", "sixties"],
        "1970s": ["1970-1979", "70s", "seventies"],
        "1980s": ["1980-1989", "80s", "eighties"],
        "1990s": ["1990-1999", "90s", "nineties"],
        "2000s": ["2000-2009", "00s", "two thousands"],
        "2010s": ["2010-2019", "10s", "twenty tens"],
        "2020s": ["2020-2029", "20s", "twenty twenties"],
    }
    
    @classmethod
    def normalize_genre(cls, genre: str) -> str:
        """Normalize genre name"""
        genre_lower = genre.lower().strip()
        
        # Check for synonyms
        for canonical, synonyms in cls.GENRE_SYNONYMS.items():
            if genre_lower in [s.lower() for s in synonyms]:
                return canonical
        
        # Return original if no synonym found
        return genre.title()
    
    @classmethod
    def normalize_era(cls, year: int) -> str:
        """Normalize year to era"""
        for era, ranges in cls.ERA_NORMALIZATION.items():
            for range_str in ranges:
                if "-" in range_str:
                    start_year, end_year = map(int, range_str.split("-"))
                    if start_year <= year <= end_year:
                        return era
                else:
                    # Handle simple patterns like "60s"
                    if range_str.endswith("s"):
                        decade_start = int(range_str[:-1])
                        if decade_start <= year <= decade_start + 9:
                            return era
                    elif range_str.isdigit():
                        decade_start = int(range_str)
                        if decade_start <= year <= decade_start + 9:
                            return era
        
        # Default era calculation
        decade_start = (year // 10) * 10
        return f"{decade_start}s"
    
    @classmethod
    def normalize_artist_type(cls, artist_type: str) -> str:
        """Normalize artist type"""
        normalized = artist_type.lower().strip()
        
        # Common normalizations
        if normalized in ["solo", "solo artist", "individual"]:
            return "solo artist"
        elif normalized in ["band", "group", "duo", "trio", "quartet"]:
            return "group"
        elif normalized in ["collaboration", "collab", "featuring"]:
            return "collaboration"
        
        return artist_type.title()


class GraphAnalytics:
    """Advanced graph analytics for question selection and insights"""
    
    def __init__(self, graph: nx.Graph):
        self.graph = graph
        self._centrality_cache = {}
        self._community_cache = {}
    
    def calculate_node_centrality(self, node_id: str, metric: str = "betweenness") -> float:
        """Calculate centrality metrics for nodes"""
        cache_key = f"{metric}_{node_id}"
        if cache_key in self._centrality_cache:
            return self._centrality_cache[cache_key]
        
        try:
            if metric == "betweenness":
                centrality = nx.betweenness_centrality(self.graph, normalized=True)
            elif metric == "closeness":
                centrality = nx.closeness_centrality(self.graph)
            elif metric == "degree":
                centrality = nx.degree_centrality(self.graph)
            elif metric == "eigenvector":
                centrality = nx.eigenvector_centrality_numpy(self.graph)
            else:
                centrality = nx.degree_centrality(self.graph)
            
            value = centrality.get(node_id, 0.0)
            self._centrality_cache[cache_key] = value
            return value
            
        except Exception as e:
            logger.warning(f"Centrality calculation failed for {node_id}: {e}")
            return 0.0
    
    def find_communities(self) -> Dict[str, int]:
        """Find communities in the graph using Louvain algorithm"""
        try:
            import community as community_louvain
            
            if not self._community_cache:
                communities = community_louvain.best_partition(self.graph)
                self._community_cache = communities
            
            return self._community_cache
            
        except ImportError:
            # Fallback to simple connected components
            communities = {}
            for i, component in enumerate(nx.connected_components(self.graph)):
                for node in component:
                    communities[node] = i
            return communities
        except Exception as e:
            logger.warning(f"Community detection failed: {e}")
            return {}
    
    def calculate_attribute_importance(self, attribute_type: str) -> float:
        """Calculate importance score for an attribute type"""
        # Get all nodes of this type
        attribute_nodes = [n for n, d in self.graph.nodes(data=True) 
                          if d.get("type") == "attribute" and d.get("label") == attribute_type]
        
        if not attribute_nodes:
            return 0.0
        
        # Calculate average centrality for this attribute type
        total_centrality = sum(self.calculate_node_centrality(node) for node in attribute_nodes)
        return total_centrality / len(attribute_nodes)
    
    def get_optimal_splitting_questions(self, candidate_songs: List[str], top_k: int = 5) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Find questions that optimally split candidate songs"""
        questions = []
        
        # Get all attributes that connect to candidate songs
        candidate_attributes = set()
        for song in candidate_songs:
            if song in self.graph:
                candidate_attributes.update(self.graph.neighbors(song))
        
        # Evaluate each attribute for splitting quality
        for attribute in candidate_attributes:
            if self.graph.nodes[attribute].get("type") != "attribute":
                continue
            
            # Calculate split quality
            split_score, split_info = self._calculate_split_quality(attribute, candidate_songs)
            
            if split_score > 0:
                questions.append((attribute, split_score, split_info))
        
        # Sort by split score and return top-k
        questions.sort(key=lambda x: x[1], reverse=True)
        return questions[:top_k]
    
    def _calculate_split_quality(self, attribute: str, candidate_songs: List[str]) -> Tuple[float, Dict[str, Any]]:
        """Calculate how well an attribute splits candidate songs"""
        # Count yes/no for this attribute
        yes_songs = []
        no_songs = []
        
        for song in candidate_songs:
            if song in self.graph and attribute in self.graph.neighbors(song):
                yes_songs.append(song)
            else:
                no_songs.append(song)
        
        if len(yes_songs) == 0 or len(no_songs) == 0:
            return 0.0, {"yes_count": 0, "no_count": 0, "balance": 0.0}
        
        # Calculate balance (ideal is 50/50)
        total = len(yes_songs) + len(no_songs)
        balance = 1.0 - abs(len(yes_songs) - len(no_songs)) / total
        
        # Calculate attribute importance
        attribute_type = self.graph.nodes[attribute].get("label", attribute)
        importance = self.calculate_attribute_importance(attribute_type)
        
        # Calculate information gain (simplified)
        entropy_before = -total * 0.5 * np.log2(0.5)  # Maximum entropy
        entropy_after = -(len(yes_songs) * (len(yes_songs)/total) * np.log2(len(yes_songs)/total) if len(yes_songs) > 0 else 0) - \
                       (len(no_songs) * (len(no_songs)/total) * np.log2(len(no_songs)/total) if len(no_songs) > 0 else 0)
        
        information_gain = entropy_before - entropy_after
        
        # Combine metrics
        split_score = (balance * 0.4) + (importance * 0.3) + (information_gain * 0.3)
        
        split_info = {
            "yes_count": len(yes_songs),
            "no_count": len(no_songs),
            "balance": balance,
            "importance": importance,
            "information_gain": information_gain,
            "yes_songs": yes_songs,
            "no_songs": no_songs
        }
        
        return split_score, split_info


class EnterpriseDynamicGraph:
    """Enterprise-grade dynamic graph with advanced features"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.graph_path = os.path.join(data_dir, "enterprise_graph.json")
        self.graph = nx.Graph()
        self.analytics = None
        self.normalizer = AttributeNormalizer()
        
        # Performance tracking
        self.node_count = 0
        self.edge_count = 0
        self.last_updated = datetime.now()
        
        logger.info("EnterpriseDynamicGraph initialized")
    
    def build_from_songs(self, songs: List[Dict[str, Any]]) -> bool:
        """Build graph from song data with automatic node discovery"""
        try:
            logger.info(f"Building graph from {len(songs)} songs")
            
            # Clear existing graph
            self.graph.clear()
            
            # Add song nodes
            for song in songs:
                self._add_song_node(song)
            
            # Discover and add attribute nodes
            self._discover_and_add_attributes(songs)
            
            # Add weighted edges
            self._add_weighted_edges(songs)
            
            # Calculate graph metrics
            self._calculate_graph_metrics()
            
            # Initialize analytics
            self.analytics = GraphAnalytics(self.graph)
            
            # Save graph
            self.save_graph()
            
            logger.info(f"Graph built: {self.node_count} nodes, {self.edge_count} edges")
            return True
            
        except Exception as e:
            logger.error(f"Graph construction failed: {e}")
            return False
    
    def _add_song_node(self, song: Dict[str, Any]):
        """Add a song node to the graph"""
        song_id = f"song_{song.get('id', hash(song.get('title', '')))}"
        
        node = GraphNode(
            id=song_id,
            type="song",
            label=song.get("title", "Unknown"),
            metadata={
                "artists": song.get("artists", []),
                "genres": song.get("genres", []),
                "duration": song.get("duration"),
                "bpm": song.get("bpm"),
                "publication_date": song.get("publication_date"),
                "country": song.get("country"),
                "language": song.get("language")
            }
        )
        
        self.graph.add_node(song_id, **node.__dict__)
        self.node_count += 1
    
    def _discover_and_add_attributes(self, songs: List[Dict[str, Any]]):
        """Automatically discover and add attribute nodes"""
        attribute_stats = defaultdict(lambda: defaultdict(int))
        
        # Collect all attributes and their frequencies
        for song in songs:
            for attr, value in song.items():
                if attr in ["id", "title"] or not value:
                    continue
                
                if isinstance(value, list):
                    for v in value:
                        if v:
                            attribute_stats[attr][v] += 1
                else:
                    attribute_stats[attr][value] += 1
        
        # Add attribute nodes for significant attributes
        for attr, values in attribute_stats.items():
            for value, count in values.items():
                # Skip very rare attributes (less than 2 occurrences)
                if count < 2:
                    continue
                
                # Normalize the attribute value
                normalized_value = self._normalize_attribute_value(attr, value)
                
                attr_id = f"attr_{attr}_{hash(normalized_value)}"
                
                node = GraphNode(
                    id=attr_id,
                    type="attribute",
                    label=attr,
                    weight=count,  # Weight by frequency
                    metadata={
                        "value": normalized_value,
                        "frequency": count,
                        "normalized": True
                    }
                )
                
                self.graph.add_node(attr_id, **node.__dict__)
                self.node_count += 1
    
    def _normalize_attribute_value(self, attr: str, value: str) -> str:
        """Normalize attribute values"""
        if attr == "genres":
            return self.normalizer.normalize_genre(value)
        elif attr == "publication_date" and isinstance(value, str):
            try:
                year = int(value[:4])
                return self.normalizer.normalize_era(year)
            except (ValueError, TypeError):
                return value
        elif attr == "artist_types":
            return self.normalizer.normalize_artist_type(value)
        else:
            return str(value).strip()
    
    def _add_weighted_edges(self, songs: List[Dict[str, Any]]):
        """Add weighted edges between songs and attributes"""
        for song in songs:
            song_id = f"song_{song.get('id', hash(song.get('title', '')))}"
            
            for attr, value in song.items():
                if attr in ["id", "title"] or not value:
                    continue
                
                if isinstance(value, list):
                    for v in value:
                        if v:
                            self._add_song_attribute_edge(song_id, attr, v)
                else:
                    self._add_song_attribute_edge(song_id, attr, value)
    
    def _add_song_attribute_edge(self, song_id: str, attr: str, value: str):
        """Add edge between song and attribute"""
        normalized_value = self._normalize_attribute_value(attr, value)
        attr_id = f"attr_{attr}_{hash(normalized_value)}"
        
        if attr_id in self.graph:
            # Calculate edge weight based on attribute importance
            edge_weight = self._calculate_edge_weight(attr, normalized_value)
            
            edge = GraphEdge(
                source=song_id,
                target=attr_id,
                weight=edge_weight,
                relationship_type="has_attribute",
                confidence=1.0,
                metadata={"attribute_type": attr, "value": normalized_value}
            )
            
            self.graph.add_edge(song_id, attr_id, **edge.__dict__)
            self.edge_count += 1
    
    def _calculate_edge_weight(self, attr: str, value: str) -> float:
        """Calculate edge weight based on attribute importance"""
        # Base weights for different attribute types
        attribute_weights = {
            "genres": 1.0,
            "artists": 0.8,
            "artist_genders": 0.9,
            "artist_types": 0.7,
            "era": 0.8,
            "country": 0.6,
            "language": 0.5,
            "billion_views": 1.2,
            "awards": 1.1,
            "films": 0.9,
            "tv_series": 0.9,
            "instruments": 0.7,
            "themes": 0.6,
            "duration": 0.4,
            "bpm": 0.4,
        }
        
        base_weight = attribute_weights.get(attr, 0.5)
        
        # Adjust based on value frequency (rarer values get higher weight)
        attr_id = f"attr_{attr}_{hash(value)}"
        if attr_id in self.graph:
            frequency = self.graph.nodes[attr_id].get("weight", 1)
            frequency_bonus = 1.0 / (1.0 + np.log(frequency))
            return base_weight * (1.0 + frequency_bonus * 0.5)
        
        return base_weight
    
    def _calculate_graph_metrics(self):
        """Calculate graph-level metrics"""
        self.node_count = self.graph.number_of_nodes()
        self.edge_count = self.graph.number_of_edges()
        self.last_updated = datetime.now()
        
        # Calculate density
        if self.node_count > 1:
            max_edges = self.node_count * (self.node_count - 1) / 2
            self.density = self.edge_count / max_edges
        else:
            self.density = 0.0
        
        # Calculate connected components
        self.connected_components = nx.number_connected_components(self.graph)
        
        logger.info(f"Graph metrics: {self.node_count} nodes, {self.edge_count} edges, density={self.density:.3f}")
    
    def generate_smart_questions(self, candidate_songs: List[str], asked_questions: Set[Tuple[str, str]]) -> List[Dict[str, Any]]:
        """Generate smart questions using graph analytics"""
        if not self.analytics:
            logger.warning("Graph analytics not initialized")
            return []
        
        try:
            # Get optimal splitting questions
            optimal_questions = self.analytics.get_optimal_splitting_questions(candidate_songs, top_k=10)
            
            generated_questions = []
            for attribute, score, split_info in optimal_questions:
                # Skip if already asked
                question_key = (self.graph.nodes[attribute].get("label"), 
                              self.graph.nodes[attribute].get("metadata", {}).get("value"))
                if question_key in asked_questions:
                    continue
                
                # Generate question text
                question_text = self._generate_question_text(attribute, split_info)
                
                question = {
                    "feature": self.graph.nodes[attribute].get("label"),
                    "value": self.graph.nodes[attribute].get("metadata", {}).get("value"),
                    "text": question_text,
                    "split_score": score,
                    "confidence": min(score, 1.0),
                    "split_info": split_info,
                    "source": "graph_analytics"
                }
                
                generated_questions.append(question)
            
            return generated_questions
            
        except Exception as e:
            logger.error(f"Smart question generation failed: {e}")
            return []
    
    def _generate_question_text(self, attribute: str, split_info: Dict[str, Any]) -> str:
        """Generate natural language question text"""
        node_data = self.graph.nodes[attribute]
        feature = node_data.get("label", "")
        value = node_data.get("metadata", {}).get("value", "")
        
        # Question templates based on attribute type
        if feature == "genres":
            return f"Is it a {value} song?"
        elif feature == "artists":
            return f"Is it by {value}?"
        elif feature == "artist_genders":
            return f"Is the artist {value}?"
        elif feature == "artist_types":
            return f"Is it by a {value}?"
        elif feature == "era":
            return f"Is it from the {value}?"
        elif feature == "country":
            return f"Is it from {value}?"
        elif feature == "billion_views":
            return f"Does it have over a billion views?"
        elif feature == "awards":
            return f"Has it won any awards?"
        elif feature == "films":
            return f"Is it from the movie {value}?"
        elif feature == "tv_series":
            return f"Is it from the TV show {value}?"
        elif feature == "instruments":
            return f"Does it feature {value}?"
        elif feature == "themes":
            return f"Is it about {value}?"
        else:
            return f"Is it connected with {value}?"
    
    def save_graph(self):
        """Save graph to file with metadata"""
        try:
            # Convert NetworkX graph to serializable format
            graph_data = {
                "nodes": [
                    {
                        "id": node,
                        **data
                    }
                    for node, data in self.graph.nodes(data=True)
                ],
                "edges": [
                    {
                        "source": edge[0],
                        "target": edge[1],
                        **data
                    }
                    for edge, data in self.graph.edges(data=True)
                ],
                "metadata": {
                    "node_count": self.node_count,
                    "edge_count": self.edge_count,
                    "density": getattr(self, 'density', 0.0),
                    "connected_components": getattr(self, 'connected_components', 0),
                    "last_updated": self.last_updated.isoformat(),
                    "version": "2.0"
                }
            }
            
            with open(self.graph_path, 'w', encoding='utf-8') as f:
                json.dump(graph_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Graph saved to {self.graph_path}")
            
        except Exception as e:
            logger.error(f"Failed to save graph: {e}")
    
    def load_graph(self) -> bool:
        """Load graph from file"""
        try:
            if not os.path.exists(self.graph_path):
                logger.info("No existing graph file found")
                return False
            
            with open(self.graph_path, 'r', encoding='utf-8') as f:
                graph_data = json.load(f)
            
            # Rebuild NetworkX graph
            self.graph.clear()
            
            # Add nodes
            for node_data in graph_data["nodes"]:
                node_id = node_data.pop("id")
                self.graph.add_node(node_id, **node_data)
            
            # Add edges
            for edge_data in graph_data["edges"]:
                source = edge_data.pop("source")
                target = edge_data.pop("target")
                self.graph.add_edge(source, target, **edge_data)
            
            # Load metadata
            metadata = graph_data.get("metadata", {})
            self.node_count = metadata.get("node_count", 0)
            self.edge_count = metadata.get("edge_count", 0)
            self.density = metadata.get("density", 0.0)
            self.connected_components = metadata.get("connected_components", 0)
            
            if "last_updated" in metadata:
                self.last_updated = datetime.fromisoformat(metadata["last_updated"])
            
            # Initialize analytics
            self.analytics = GraphAnalytics(self.graph)
            
            logger.info(f"Graph loaded: {self.node_count} nodes, {self.edge_count} edges")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load graph: {e}")
            return False
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get comprehensive graph statistics"""
        if not self.graph:
            return {"error": "Graph not initialized"}
        
        stats = {
            "basic_metrics": {
                "nodes": self.graph.number_of_nodes(),
                "edges": self.graph.number_of_edges(),
                "density": getattr(self, 'density', 0.0),
                "connected_components": getattr(self, 'connected_components', 0),
                "last_updated": self.last_updated.isoformat()
            },
            "node_types": {},
            "top_attributes": {},
            "centrality_metrics": {}
        }
        
        # Node type distribution
        node_types = Counter()
        for node, data in self.graph.nodes(data=True):
            node_type = data.get("type", "unknown")
            node_types[node_type] += 1
        stats["node_types"] = dict(node_types)
        
        # Top attributes by frequency
        attribute_nodes = [(node, data) for node, data in self.graph.nodes(data=True) 
                         if data.get("type") == "attribute"]
        attribute_nodes.sort(key=lambda x: x[1].get("weight", 0), reverse=True)
        stats["top_attributes"] = [
            {"id": node, "label": data.get("label"), "value": data.get("metadata", {}).get("value"), "weight": data.get("weight")}
            for node, data in attribute_nodes[:10]
        ]
        
        # Centrality metrics for top nodes
        if self.analytics:
            top_nodes = [node for node, _ in attribute_nodes[:5]]
            for node in top_nodes:
                stats["centrality_metrics"][node] = {
                    "betweenness": self.analytics.calculate_node_centrality(node, "betweenness"),
                    "closeness": self.analytics.calculate_node_centrality(node, "closeness"),
                    "degree": self.analytics.calculate_node_centrality(node, "degree")
                }
        
        return stats
