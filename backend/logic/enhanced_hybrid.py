"""
Enhanced Hybrid Inference Engine
Combines graph reasoning and neural embeddings with dynamic weighting
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Set
import logging
from collections import defaultdict
import math

logger = logging.getLogger(__name__)

class EnhancedHybridEngine:
    """Enhanced hybrid engine combining graph reasoning and neural embeddings"""
    
    def __init__(self, songs: List[Dict[str, Any]], 
                 graph_intelligence=None, 
                 embedding_trainer=None):
        self.songs = songs
        self.graph_intelligence = graph_intelligence
        self.embedding_trainer = embedding_trainer
        
        # Dynamic weighting parameters
        self.graph_weight = 0.6
        self.embedding_weight = 0.4
        
        # Performance tracking
        self.performance_history = {
            'graph_successes': 0,
            'embedding_successes': 0,
            'total_predictions': 0
        }
        
        # Confidence estimation parameters
        self.confidence_threshold = 0.8
        self.min_questions_for_confidence = 5
        
        # Initialize belief system
        self.beliefs = self._initialize_beliefs()
        
        logger.info("🚀 Enhanced Hybrid Engine initialized")
        logger.info(f"   Graph weight: {self.graph_weight}")
        logger.info(f"   Embedding weight: {self.embedding_weight}")
        logger.info(f"   Songs: {len(songs)}")
    
    def _initialize_beliefs(self) -> Dict[int, float]:
        """Initialize uniform beliefs for all songs"""
        return {song['id']: 1.0 / len(self.songs) for song in self.songs}
    
    def update_beliefs(self, question: Dict[str, Any], answer: str) -> Dict[int, float]:
        """Update beliefs using hybrid reasoning"""
        feature = question['feature']
        value = question['value']
        
        # Get current beliefs
        current_beliefs = self.beliefs
        
        # Update using graph reasoning
        graph_beliefs = self._update_graph_beliefs(current_beliefs, feature, value, answer)
        
        # Update using embedding similarity
        embedding_beliefs = self._update_embedding_beliefs(current_beliefs, feature, value, answer)
        
        # Combine using dynamic weighting
        new_beliefs = {}
        for song_id in current_beliefs:
            graph_score = graph_beliefs.get(song_id, current_beliefs[song_id])
            embedding_score = embedding_beliefs.get(song_id, current_beliefs[song_id])
            
            # Dynamic weighting based on question type
            weight = self._get_dynamic_weight(feature)
            new_beliefs[song_id] = (
                weight * graph_score + (1 - weight) * embedding_score
            )
        
        # Normalize beliefs
        self.beliefs = self._normalize_beliefs(new_beliefs)
        
        return self.beliefs
    
    def _update_graph_beliefs(self, beliefs: Dict[int, float], 
                           feature: str, value: str, answer: str) -> Dict[int, float]:
        """Update beliefs using graph reasoning"""
        if not self.graph_intelligence:
            return beliefs
        
        new_beliefs = beliefs.copy()
        
        for song in self.songs:
            song_id = song['id']
            
            # Check if song matches the attribute
            matches = self._song_matches_attribute(song, feature, value)
            
            # Apply Bayesian update
            if answer.lower() in ['yes', 'y', 'true']:
                likelihood = 0.9 if matches else 0.1
            else:  # no
                likelihood = 0.1 if matches else 0.9
            
            new_beliefs[song_id] *= likelihood
        
        return new_beliefs
    
    def _update_embedding_beliefs(self, beliefs: Dict[int, float], 
                             feature: str, value: str, answer: str) -> Dict[int, float]:
        """Update beliefs using embedding similarity"""
        if not self.embedding_trainer:
            return beliefs
        
        new_beliefs = beliefs.copy()
        
        # Find songs that match the attribute
        matching_songs = []
        for song in self.songs:
            if self._song_matches_attribute(song, feature, value):
                matching_songs.append(song)
        
        if not matching_songs:
            return beliefs
        
        # Get average embedding of matching songs
        avg_embedding = self._get_average_embedding(matching_songs)
        if avg_embedding is None:
            return beliefs
        
        # Update beliefs based on similarity to average embedding
        for song in self.songs:
            song_id = song['id']
            song_embedding = self._get_song_embedding(song)
            
            if song_embedding is not None:
                similarity = self._cosine_similarity(song_embedding, avg_embedding)
                
                # Apply similarity-based update
                if answer.lower() in ['yes', 'y', 'true']:
                    update_factor = 1.0 + similarity * 0.5
                else:
                    update_factor = 1.0 - similarity * 0.5
                
                new_beliefs[song_id] *= update_factor
        
        return new_beliefs
    
    def _get_dynamic_weight(self, feature: str) -> float:
        """Get dynamic weight for feature based on its effectiveness"""
        # Graph performs better for categorical attributes
        graph_features = ['genres', 'artists', 'country', 'decade', 'era']
        
        # Embeddings perform better for semantic similarity
        embedding_features = ['themes', 'instruments', 'mood']
        
        if feature in graph_features:
            return self.graph_weight
        elif feature in embedding_features:
            return self.embedding_weight
        else:
            # Use balanced weight for other features
            return 0.5
    
    def get_best_question(self, asked_questions: Set[Tuple[str, str]], 
                        max_questions: int = 20) -> Optional[Dict[str, Any]]:
        """Get best question using hybrid intelligence"""
        # Get current candidates (songs with non-zero beliefs)
        candidate_songs = [
            song for song in self.songs 
            if self.beliefs.get(song['id'], 0) > 1e-6
        ]
        
        if len(candidate_songs) <= 1:
            return None
        
        # Get questions from both systems
        graph_questions = []
        embedding_questions = []
        
        # Graph-based questions
        if self.graph_intelligence:
            graph_questions = self.graph_intelligence.get_best_questions(
                candidate_songs, asked_questions, max_questions // 2
            )
        
        # Embedding-based questions (simplified for now)
        embedding_questions = self._get_embedding_questions(
            candidate_songs, asked_questions, max_questions // 2
        )
        
        # Score and combine questions
        all_questions = graph_questions + embedding_questions
        
        if not all_questions:
            return None
        
        # Score questions using hybrid approach
        for question in all_questions:
            question['hybrid_score'] = self._score_hybrid_question(
                question, candidate_songs, asked_questions
            )
        
        # Sort by hybrid score and return best
        all_questions.sort(key=lambda q: q.get('hybrid_score', 0), reverse=True)
        best_question = all_questions[0]
        
        # Add debug information
        best_question['debug_info'] = self._get_hybrid_debug_info(
            best_question, candidate_songs
        )
        
        logger.info(f"🎯 Best hybrid question: {best_question.get('text', 'Unknown')}")
        logger.info(f"   Score: {best_question.get('hybrid_score', 0):.3f}")
        
        return best_question
    
    def _get_embedding_questions(self, candidate_songs: List[Dict[str, Any]], 
                             asked_questions: Set[Tuple[str, str]], 
                             max_questions: int) -> List[Dict[str, Any]]:
        """Generate questions based on embedding clusters"""
        if not self.embedding_trainer:
            return []
        
        questions = []
        
        # Find clusters in embedding space
        clusters = self._find_embedding_clusters(candidate_songs)
        
        # Generate questions based on cluster characteristics
        for cluster_id, cluster_songs in clusters.items():
            if len(cluster_songs) < 2:
                continue
            
            # Find distinguishing features of this cluster
            distinguishing_features = self._find_cluster_features(cluster_songs, candidate_songs)
            
            for feature, value in distinguishing_features:
                if (feature, value) not in asked_questions:
                    questions.append({
                        'feature': feature,
                        'value': value,
                        'text': f"Is it connected with {value}?",
                        'source': 'embedding',
                        'cluster_id': cluster_id
                    })
        
        return questions[:max_questions]
    
    def _find_embedding_clusters(self, songs: List[Dict[str, Any]], 
                            num_clusters: int = 5) -> Dict[int, List[Dict[str, Any]]]:
        """Find clusters in embedding space"""
        if not self.embedding_trainer or len(songs) < num_clusters:
            return {i: [song] for i, song in enumerate(songs)}
        
        # Get embeddings for songs
        embeddings = []
        valid_songs = []
        
        for song in songs:
            embedding = self._get_song_embedding(song)
            if embedding is not None:
                embeddings.append(embedding)
                valid_songs.append(song)
        
        if len(embeddings) < num_clusters:
            return {i: [song] for i, song in enumerate(valid_songs)}
        
        # Simple k-means clustering
        from sklearn.cluster import KMeans
        
        kmeans = KMeans(n_clusters=num_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(embeddings)
        
        # Group songs by cluster
        clusters = defaultdict(list)
        for song, label in zip(valid_songs, cluster_labels):
            clusters[label].append(song)
        
        return dict(clusters)
    
    def _find_cluster_features(self, cluster_songs: List[Dict[str, Any]], 
                           all_songs: List[Dict[str, Any]]) -> List[Tuple[str, str]]:
        """Find features that distinguish this cluster"""
        distinguishing_features = []
        
        # Check each attribute
        attributes = ['genres', 'artists', 'decade', 'era', 'country']
        
        for attribute in attributes:
            # Get value distribution in cluster
            cluster_values = set()
            for song in cluster_songs:
                values = song.get(attribute, [])
                if isinstance(values, list):
                    cluster_values.update(values)
            
            # Get value distribution outside cluster
            other_values = set()
            for song in all_songs:
                if song not in cluster_songs:
                    values = song.get(attribute, [])
                    if isinstance(values, list):
                        other_values.update(values)
            
            # Find distinguishing values
            for value in cluster_values:
                if value not in other_values or len(cluster_values) < len(other_values) / 2:
                    distinguishing_features.append((attribute, value))
        
        return distinguishing_features
    
    def _score_hybrid_question(self, question: Dict[str, Any], 
                           candidate_songs: List[Dict[str, Any]], 
                           asked_questions: Set[Tuple[str, str]]) -> float:
        """Score question using hybrid approach"""
        feature = question['feature']
        value = question['value']
        
        # Information gain (primary factor)
        info_gain = self._calculate_information_gain(feature, value, candidate_songs)
        
        # Graph centrality (if available)
        graph_score = 0.0
        if self.graph_intelligence and question.get('source') != 'embedding':
            centrality = self.graph_intelligence.get_attribute_centrality(feature, value)
            graph_score = centrality.get('betweenness', 0.0)
        
        # Embedding cluster coherence (if from embedding)
        embedding_score = 0.0
        if question.get('source') == 'embedding':
            embedding_score = self._calculate_cluster_coherence(question, candidate_songs)
        
        # Feature importance
        feature_weights = {
            'genres': 1.0,
            'artists': 0.8,
            'decade': 0.9,
            'era': 0.8,
            'is_collaboration': 0.7,
            'is_soundtrack': 0.8,
            'is_viral_hit': 0.9,
        }
        feature_weight = feature_weights.get(feature, 0.5)
        
        # Diversity bonus
        asked_features = {f for f, _ in asked_questions}
        diversity_bonus = 0.2 if feature not in asked_features else 0.0
        
        # Combine scores
        hybrid_score = (
            info_gain * 0.4 +
            graph_score * 0.2 +
            embedding_score * 0.2 +
            feature_weight * 0.1 +
            diversity_bonus * 0.1
        )
        
        return hybrid_score
    
    def _calculate_cluster_coherence(self, question: Dict[str, Any], 
                               candidate_songs: List[Dict[str, Any]]) -> float:
        """Calculate how coherent the question is with embedding clusters"""
        # This is a simplified version - in practice, you'd use more sophisticated metrics
        cluster_id = question.get('cluster_id', 0)
        return 0.5 + 0.1 * math.sin(cluster_id)  # Placeholder
    
    def get_confidence(self, song_id: int) -> Tuple[float, str]:
        """Get confidence and explanation for a song prediction"""
        if song_id not in self.beliefs:
            return 0.0, "Song not found"
        
        belief = self.beliefs[song_id]
        
        # Calculate confidence metrics
        max_belief = max(self.beliefs.values())
        confidence = belief / max_belief if max_belief > 0 else 0.0
        
        # Generate explanation
        if confidence >= self.confidence_threshold:
            explanation = "High confidence"
        elif confidence >= 0.5:
            explanation = "Medium confidence"
        else:
            explanation = "Low confidence"
        
        return confidence, explanation
    
    def get_top_candidates(self, top_k: int = 5) -> List[Tuple[int, float, str]]:
        """Get top candidate songs with confidence scores"""
        # Sort songs by belief
        sorted_songs = sorted(
            self.beliefs.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        candidates = []
        for song_id, belief in sorted_songs[:top_k]:
            confidence, explanation = self.get_confidence(song_id)
            candidates.append((song_id, belief, explanation))
        
        return candidates
    
    def should_make_guess(self, questions_asked: int) -> Tuple[bool, Optional[int]]:
        """Determine if system should make a guess"""
        if questions_asked < self.min_questions_for_confidence:
            return False, None
        
        # Get top candidates
        top_candidates = self.get_top_candidates(2)
        
        if len(top_candidates) < 2:
            return True, top_candidates[0][0] if top_candidates else None
        
        top_confidence = top_candidates[0][1]
        second_confidence = top_candidates[1][1]
        
        # Check confidence threshold and dominance
        if (top_confidence >= self.confidence_threshold and 
            top_confidence / second_confidence >= 2.0):
            return True, top_candidates[0][0]
        
        return False, None
    
    def fallback_to_graph_only(self) -> bool:
        """Fallback to graph-only reasoning if embeddings fail"""
        if not self.embedding_trainer:
            return True
        
        # Check if embeddings are performing poorly
        if (self.performance_history['total_predictions'] > 10 and
            self.performance_history['embedding_successes'] / self.performance_history['total_predictions'] < 0.3):
            logger.warning("🔄 Embeddings performing poorly, falling back to graph-only")
            return True
        
        return False
    
    def _song_matches_attribute(self, song: Dict[str, Any], attribute: str, value: str) -> bool:
        """Check if song matches attribute value"""
        song_values = song.get(attribute, [])
        if isinstance(song_values, list):
            return value in song_values
        return str(song_values) == value
    
    def _calculate_information_gain(self, feature: str, value: str, 
                                candidate_songs: List[Dict[str, Any]]) -> float:
        """Calculate information gain for attribute split"""
        matches = [s for s in candidate_songs if self._song_matches_attribute(s, feature, value)]
        non_matches = [s for s in candidate_songs if not self._song_matches_attribute(s, feature, value)]
        
        if not matches or not non_matches:
            return 0.0
        
        total = len(candidate_songs)
        entropy_before = self._entropy([total])
        entropy_after = (
            (len(matches) / total) * self._entropy([len(matches)]) +
            (len(non_matches) / total) * self._entropy([len(non_matches)])
        )
        
        return entropy_before - entropy_after
    
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
    
    def _normalize_beliefs(self, beliefs: Dict[int, float]) -> Dict[int, float]:
        """Normalize beliefs to sum to 1"""
        total = sum(beliefs.values())
        if total <= 0:
            return beliefs
        
        return {song_id: belief / total for song_id, belief in beliefs.items()}
    
    def _get_average_embedding(self, songs: List[Dict[str, Any]]) -> Optional[np.ndarray]:
        """Get average embedding of a list of songs"""
        if not self.embedding_trainer:
            return None
        
        embeddings = []
        for song in songs:
            embedding = self._get_song_embedding(song)
            if embedding is not None:
                embeddings.append(embedding)
        
        if not embeddings:
            return None
        
        return np.mean(embeddings, axis=0)
    
    def _get_song_embedding(self, song: Dict[str, Any]) -> Optional[np.ndarray]:
        """Get embedding for a specific song"""
        if not self.embedding_trainer or not hasattr(self.embedding_trainer, 'embeddings'):
            return None
        
        try:
            song_idx = song['id']
            if song_idx < len(self.embedding_trainer.embeddings):
                return self.embedding_trainer.embeddings[song_idx]
        except:
            pass
        
        return None
    
    def _cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between embeddings"""
        if embedding1 is None or embedding2 is None:
            return 0.0
        
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _get_hybrid_debug_info(self, question: Dict[str, Any], 
                             candidate_songs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get debug information for hybrid question"""
        feature = question['feature']
        value = question['value']
        
        matches = sum(1 for s in candidate_songs if self._song_matches_attribute(s, feature, value))
        total = len(candidate_songs)
        
        info_gain = self._calculate_information_gain(feature, value, candidate_songs)
        
        debug_info = {
            'matches': matches,
            'total': total,
            'split_ratio': matches / total,
            'information_gain': info_gain,
            'source': question.get('source', 'graph'),
            'hybrid_score': question.get('hybrid_score', 0)
        }
        
        # Add graph-specific debug info
        if self.graph_intelligence and question.get('source') != 'embedding':
            centrality = self.graph_intelligence.get_attribute_centrality(feature, value)
            debug_info['graph_centrality'] = centrality.get('betweenness', 0.0)
        
        return debug_info
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            'total_songs': len(self.songs),
            'graph_available': self.graph_intelligence is not None,
            'embeddings_available': self.embedding_trainer is not None,
            'graph_weight': self.graph_weight,
            'embedding_weight': self.embedding_weight,
            'performance_history': self.performance_history,
            'confidence_threshold': self.confidence_threshold,
            'current_beliefs': len([b for b in self.beliefs.values() if b > 1e-6])
        }


def create_enhanced_hybrid_engine(songs: List[Dict[str, Any]], 
                               graph_intelligence=None, 
                               embedding_trainer=None) -> EnhancedHybridEngine:
    """Factory function to create enhanced hybrid engine"""
    return EnhancedHybridEngine(songs, graph_intelligence, embedding_trainer)
