"""
Enhanced Graph Intelligence System
Improved knowledge graph with better question scoring and centrality metrics
"""

import json
import networkx as nx
import numpy as np
from typing import List, Dict, Any, Set, Tuple, Optional
from collections import defaultdict, Counter
import math
import logging

logger = logging.getLogger(__name__)

class GraphIntelligence:
    """Enhanced knowledge graph with intelligent question generation"""
    
    def __init__(self, songs: List[Dict[str, Any]]):
        self.songs = songs
        self.title_to_idx = {song["title"]: i for i, song in enumerate(songs)}
        
        # Build enhanced graph
        self.graph = nx.Graph()
        self.attribute_nodes = set()
        self.song_nodes = set()
        
        # Centrality metrics cache
        self._centrality_cache = {}
        self._information_gain_cache = {}
        
        # Build the graph
        self._build_enhanced_graph()
        
    def _build_enhanced_graph(self):
        """Build enhanced knowledge graph with all attributes as nodes"""
        logger.info("🏗️ Building enhanced knowledge graph...")
        
        # Add song nodes
        for song in self.songs:
            song_id = song["id"]
            song_label = f"song_{song_id}"
            self.graph.add_node(song_label, type='song', data=song)
            self.song_nodes.add(song_label)
        
        # Add attribute nodes and edges
        for song in self.songs:
            song_id = song["id"]
            song_label = f"song_{song_id}"
            
            # Process all attributes
            for attribute, values in self._extract_all_attributes(song).items():
                if not values:
                    continue
                    
                for value in values:
                    # Create attribute node
                    attr_label = f"{attribute}_{value}"
                    attr_label = attr_label.replace(" ", "_").replace("/", "_")
                    
                    self.graph.add_node(attr_label, type='attribute', 
                                     attribute=attribute, value=value)
                    self.attribute_nodes.add(attr_label)
                    
                    # Connect song to attribute
                    self.graph.add_edge(song_label, attr_label, weight=1.0)
        
        # Calculate initial centrality metrics
        self._calculate_centrality_metrics()
        
        logger.info(f"🌐 Built enhanced graph:")
        logger.info(f"   Songs: {len(self.song_nodes)}")
        logger.info(f"   Attributes: {len(self.attribute_nodes)}")
        logger.info(f"   Edges: {self.graph.number_of_edges()}")
    
    def _extract_all_attributes(self, song: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract all meaningful attributes from song"""
        attributes = {}
        
        # Basic attributes
        for attr in ['genres', 'artists', 'country', 'language']:
            values = song.get(attr, [])
            if isinstance(values, list):
                attributes[attr] = values
            elif values:
                attributes[attr] = [str(values)]
        
        # Derived attributes
        if 'release_year' in song:
            year = song['release_year']
            attributes['decade'] = [f"{(year // 10) * 10}s"]
            attributes['era'] = [self._get_era(year)]
        
        # Boolean attributes
        boolean_attrs = ['is_collaboration', 'is_soundtrack', 'is_viral_hit']
        for attr in boolean_attrs:
            if attr in song:
                attributes[attr] = [str(song[attr])]
        
        # Categorical attributes
        cat_attrs = ['duration_category', 'bpm_category']
        for attr in cat_attrs:
            if attr in song:
                attributes[attr] = [song[attr]]
        
        return attributes
    
    def get_attribute_centrality(self, attribute: str, value: str) -> Dict[str, float]:
        """Get centrality metrics for an attribute"""
        attr_label = f"{attribute}_{value}".replace(" ", "_").replace("/", "_")
        
        if attr_label not in self._centrality_cache:
            # Calculate centrality if not cached
            centrality = self._calculate_node_centrality(attr_label)
            self._centrality_cache[attr_label] = centrality
        
        return self._centrality_cache.get(attr_label, {})
    
    def _calculate_node_centrality(self, node: str) -> Dict[str, float]:
        """Calculate centrality metrics for a specific node"""
        try:
            if node not in self.graph:
                return {}
            
            # Betweenness centrality (how important for information flow)
            betweenness = nx.betweenness_centrality(self.graph, k=min(100, self.graph.number_of_nodes()))
            
            # Closeness centrality (how close to other nodes)
            closeness = nx.closeness_centrality(self.graph)
            
            # Degree centrality (how many connections)
            degree = nx.degree_centrality(self.graph)
            
            # Eigenvector centrality (influence)
            try:
                eigenvector = nx.eigenvector_centrality(self.graph, max_iter=1000)
            except:
                eigenvector = {node: 0.0 for node in self.graph.nodes()}
            
            return {
                'betweenness': betweenness.get(node, 0.0),
                'closeness': closeness.get(node, 0.0),
                'degree': degree.get(node, 0.0),
                'eigenvector': eigenvector.get(node, 0.0)
            }
            
        except Exception as e:
            logger.warning(f"Error calculating centrality for {node}: {e}")
            return {}
    
    def _calculate_centrality_metrics(self):
        """Pre-calculate centrality metrics for all attribute nodes"""
        logger.info("📊 Calculating centrality metrics...")
        
        # Calculate for all attribute nodes
        for node in self.attribute_nodes:
            centrality = self._calculate_node_centrality(node)
            self._centrality_cache[node] = centrality
    
    def calculate_information_gain(self, attribute: str, value: str, candidate_songs: List[Dict[str, Any]]) -> float:
        """Calculate information gain for splitting on attribute value"""
        cache_key = f"{attribute}_{value}_{len(candidate_songs)}"
        
        if cache_key in self._information_gain_cache:
            return self._information_gain_cache[cache_key]
        
        # Split songs by this attribute
        matches = []
        non_matches = []
        
        for song in candidate_songs:
            if self._song_matches_attribute(song, attribute, value):
                matches.append(song)
            else:
                non_matches.append(song)
        
        if not matches or not non_matches:
            self._information_gain_cache[cache_key] = 0.0
            return 0.0
        
        # Calculate entropy before and after split
        total_songs = len(candidate_songs)
        entropy_before = self._entropy([total_songs])
        
        entropy_after = (
            (len(matches) / total_songs) * self._entropy([len(matches)]) +
            (len(non_matches) / total_songs) * self._entropy([len(non_matches)])
        )
        
        information_gain = entropy_before - entropy_after
        self._information_gain_cache[cache_key] = information_gain
        
        return information_gain
    
    def get_best_questions(self, candidate_songs: List[Dict[str, Any]], 
                        asked_questions: Set[Tuple[str, str]], 
                        max_questions: int = 20) -> List[Dict[str, Any]]:
        """Get best questions using graph intelligence"""
        
        # Generate all possible questions from candidate songs
        all_questions = self._generate_all_questions(candidate_songs)
        
        # Score each question
        scored_questions = []
        for question in all_questions:
            if (question['feature'], question['value']) in asked_questions:
                continue
            
            score = self._score_question(question, candidate_songs, asked_questions)
            question['score'] = score
            question['debug_info'] = self._get_question_debug_info(question, candidate_songs)
            scored_questions.append(question)
        
        # Sort by score and return top questions
        scored_questions.sort(key=lambda q: q['score'], reverse=True)
        return scored_questions[:max_questions]
    
    def _generate_all_questions(self, candidate_songs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate all possible questions from candidate songs"""
        questions = []
        attribute_counts = defaultdict(set)
        
        # Collect all attribute values
        for song in candidate_songs:
            for attribute, values in self._extract_all_attributes(song).items():
                for value in values:
                    attribute_counts[attribute].add(value)
        
        # Generate questions for each attribute
        for attribute, values in attribute_counts.items():
            for value in values:
                questions.append({
                    'feature': attribute,
                    'value': value,
                    'text': self._generate_question_text(attribute, value)
                })
        
        return questions
    
    def _score_question(self, question: Dict[str, Any], 
                      candidate_songs: List[Dict[str, Any]], 
                      asked_questions: Set[Tuple[str, str]]) -> float:
        """Score question using multiple factors"""
        feature = question['feature']
        value = question['value']
        
        # 1. Information gain (most important)
        info_gain = self.calculate_information_gain(feature, value, candidate_songs)
        
        # 2. Graph centrality
        centrality = self.get_attribute_centrality(feature, value)
        centrality_score = centrality.get('betweenness', 0.0)
        
        # 3. Candidate reduction (how well it splits)
        matches = sum(1 for song in candidate_songs 
                     if self._song_matches_attribute(song, feature, value))
        total = len(candidate_songs)
        split_ratio = min(matches, total - matches) / total
        
        # 4. Feature importance weights
        feature_weights = {
            'genres': 1.0,
            'artists': 0.7,
            'decade': 0.9,
            'era': 0.8,
            'is_collaboration': 0.8,
            'is_soundtrack': 0.9,
            'is_viral_hit': 0.9,
            'country': 0.6,
            'duration_category': 0.7,
            'bpm_category': 0.6,
        }
        feature_weight = feature_weights.get(feature, 0.5)
        
        # 5. Diversity bonus (avoid asking same feature type)
        asked_features = {f for f, _ in asked_questions}
        diversity_penalty = 0.0 if feature not in asked_features else 0.2
        
        # Combine scores
        total_score = (
            info_gain * 0.4 +
            centrality_score * 0.2 +
            split_ratio * 0.2 +
            feature_weight * 0.15 +
            diversity_penalty * 0.05
        )
        
        return total_score
    
    def _get_question_debug_info(self, question: Dict[str, Any], 
                             candidate_songs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get debug information for question"""
        feature = question['feature']
        value = question['value']
        
        matches = sum(1 for song in candidate_songs 
                     if self._song_matches_attribute(song, feature, value))
        total = len(candidate_songs)
        
        centrality = self.get_attribute_centrality(feature, value)
        info_gain = self.calculate_information_gain(feature, value, candidate_songs)
        
        return {
            'matches': matches,
            'total': total,
            'split_ratio': matches / total,
            'centrality': centrality.get('betweenness', 0.0),
            'information_gain': info_gain,
            'entropy': self._entropy([matches, total - matches])
        }
    
    def _song_matches_attribute(self, song: Dict[str, Any], attribute: str, value: str) -> bool:
        """Check if song matches attribute value"""
        song_attributes = self._extract_all_attributes(song)
        
        if attribute not in song_attributes:
            return False
        
        return value in song_attributes[attribute]
    
    def _generate_question_text(self, attribute: str, value: str) -> str:
        """Generate natural language question text"""
        question_templates = {
            'genres': f"Is it a {value} song?",
            'artists': f"Is it by {value}?",
            'decade': f"Was it released in the {value}?",
            'era': f"Is it from the {value}?",
            'is_collaboration': f"Is it a collaboration song?",
            'is_soundtrack': f"Is it from a soundtrack?",
            'is_viral_hit': f"Is it a viral hit song?",
            'country': f"Is it from {value}?",
            'duration_category': f"Is it a {value.lower()} song?",
            'bpm_category': f"Does it have {value.lower()} tempo?",
        }
        
        return question_templates.get(attribute, f"Is it connected with {value}?")
    
    def _entropy(self, counts: List[int]) -> float:
        """Calculate Shannon entropy"""
        total = sum(counts)
        if total <= 1:
            return 0.0
        
        entropy = 0.0
        for count in counts:
            if count > 0:
                probability = count / total
                entropy -= probability * math.log2(probability)
        
        return entropy
    
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
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get graph statistics for analysis"""
        return {
            'nodes': self.graph.number_of_nodes(),
            'edges': self.graph.number_of_edges(),
            'song_nodes': len(self.song_nodes),
            'attribute_nodes': len(self.attribute_nodes),
            'density': nx.density(self.graph),
            'is_connected': nx.is_connected(self.graph),
            'average_clustering': nx.average_clustering(self.graph),
        }
    
    def visualize_graph(self, output_file: str = "graph_visualization.png"):
        """Create basic graph visualization"""
        try:
            import matplotlib.pyplot as plt
            
            # Create subgraph with limited nodes for visualization
            subgraph_nodes = list(self.song_nodes)[:20] + list(self.attribute_nodes)[:50]
            subgraph = self.graph.subgraph(subgraph_nodes)
            
            # Draw the graph
            plt.figure(figsize=(15, 10))
            pos = nx.spring_layout(subgraph, k=1, iterations=50)
            
            # Draw nodes with different colors
            song_nodes = [n for n in subgraph.nodes() if n.startswith('song_')]
            attr_nodes = [n for n in subgraph.nodes() if not n.startswith('song_')]
            
            nx.draw_networkx_nodes(subgraph, pos, nodelist=song_nodes, 
                                 node_color='lightblue', node_size=300, alpha=0.7)
            nx.draw_networkx_nodes(subgraph, pos, nodelist=attr_nodes, 
                                 node_color='lightgreen', node_size=200, alpha=0.7)
            nx.draw_networkx_edges(subgraph, pos, alpha=0.5, edge_color='gray')
            
            plt.title("Music Akenator Knowledge Graph")
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(output_file, dpi=150, bbox_inches='tight')
            plt.close()
            
            logger.info(f"📊 Graph visualization saved to {output_file}")
            
        except ImportError:
            logger.warning("Matplotlib not available for graph visualization")
        except Exception as e:
            logger.error(f"Error creating graph visualization: {e}")


def create_graph_intelligence(songs: List[Dict[str, Any]]) -> GraphIntelligence:
    """Factory function to create graph intelligence system"""
    return GraphIntelligence(songs)
