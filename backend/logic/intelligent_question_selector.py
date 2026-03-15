"""
Intelligent Question Selector
Uses graph centrality and embedding similarity for smart question selection
"""

import numpy as np
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import Counter, defaultdict
import logging

logger = logging.getLogger(__name__)

class IntelligentQuestionSelector:
    """Smart question selection using graph and embedding models"""
    
    def __init__(self, songs: List[Dict[str, Any]], use_graph: bool = True, use_embeddings: bool = False):
        self.songs = songs
        self.use_graph = use_graph
        self.use_embeddings = use_embeddings
        
        # Build feature importance models
        self.feature_importance = self._calculate_feature_importance()
        self.question_effectiveness = defaultdict(list)
        
        # Track question history for adaptive learning
        self.asked_history = []
        
        logger.info(f"🧠 Initialized Intelligent Selector (graph={use_graph}, embeddings={use_embeddings})")
    
    def _calculate_feature_importance(self) -> Dict[str, float]:
        """Calculate importance of each feature based on discriminative power"""
        feature_stats = defaultdict(lambda: {'count': 0, 'unique_values': set(), 'entropy': 0.0})
        
        # Analyze each feature
        for song in self.songs:
            for attr in ['genres', 'artists', 'decade', 'era', 'is_collaboration', 'is_viral_hit']:
                values = song.get(attr, [])
                if isinstance(values, list):
                    feature_stats[attr]['unique_values'].update(values)
                    feature_stats[attr]['count'] += len(values)
                elif values:
                    feature_stats[attr]['unique_values'].add(str(values))
                    feature_stats[attr]['count'] += 1
        
        # Calculate discriminative power (entropy)
        total_songs = len(self.songs)
        for attr, stats in feature_stats.items():
            unique_values = len(stats['unique_values'])
            if unique_values > 0:
                # Higher entropy = more discriminative
                entropy = 0.0
                for value in stats['unique_values']:
                    # Count songs with this value
                    count = sum(1 for song in self.songs 
                              if self._song_has_value(song, attr, value))
                    if count > 0:
                        prob = count / total_songs
                        entropy -= prob * np.log2(prob)
                
                feature_stats[attr]['entropy'] = entropy
        
        # Normalize importance scores
        importance = {}
        max_entropy = max(stats['entropy'] for stats in feature_stats.values())
        
        for attr, stats in feature_stats.items():
            # Combine entropy and uniqueness
            normalized_entropy = stats['entropy'] / max_entropy if max_entropy > 0 else 0
            uniqueness = min(len(stats['unique_values']) / 10, 1.0)  # Cap at 10 unique values
            
            importance[attr] = (normalized_entropy * 0.7) + (uniqueness * 0.3)
        
        return importance
    
    def _song_has_value(self, song: Dict[str, Any], attr: str, value: str) -> bool:
        """Check if song has a specific attribute value"""
        song_value = song.get(attr)
        if isinstance(song_value, list):
            return value in song_value
        else:
            return str(song_value) == value
    
    def select_best_question(self, available_questions: List[Dict[str, Any]], 
                           asked_questions: Set[Tuple[str, str]], 
                           current_beliefs: Dict[int, float]) -> Optional[Dict[str, Any]]:
        """Select the best question using intelligent scoring"""
        
        if not available_questions:
            return None
        
        # Calculate question scores
        scored_questions = []
        
        for question in available_questions:
            feature = question['feature']
            value = question['value']
            
            # Base score from feature importance
            base_score = self.feature_importance.get(feature, 0.5)
            
            # Information gain score
            info_gain = self._calculate_adaptive_info_gain(question, current_beliefs)
            
            # Adaptive penalty based on recent questions
            adaptive_penalty = self._calculate_adaptive_penalty(feature, asked_questions)
            
            # Graph centrality bonus (if available)
            graph_bonus = 0.0
            if self.use_graph:
                graph_bonus = self._calculate_graph_centrality_bonus(feature, value)
            
            # Embedding similarity bonus (if available)
            embedding_bonus = 0.0
            if self.use_embeddings:
                embedding_bonus = self._calculate_embedding_similarity_bonus(question, current_beliefs)
            
            # Combined score with more balanced weighting
            total_score = (
                base_score * 0.4 +           # Feature importance (reduced from 0.3)
                info_gain * 0.3 +             # Information gain (reduced from 0.4)
                graph_bonus * 0.1 +           # Graph centrality
                embedding_bonus * 0.1 +       # Embedding similarity
                (1.0 - adaptive_penalty) * 0.2  # Adaptive penalty (increased from 0.1)
            )
            
            scored_questions.append((question, total_score))
        
        # Select best question
        if scored_questions:
            best_question, best_score = max(scored_questions, key=lambda x: x[1])
            
            # Record for adaptive learning
            self.asked_history.append(best_question['feature'])
            
            logger.debug(f"🎯 Selected: {best_question['text']} (score: {best_score:.3f})")
            return best_question
        
        return None
    
    def _calculate_adaptive_info_gain(self, question: Dict[str, Any], beliefs: Dict[int, float]) -> float:
        """Calculate information gain with adaptive weighting"""
        feature = question['feature']
        value = question['value']
        
        # Split songs by this question
        matches = []
        non_matches = []
        
        for song in self.songs:
            if self._song_has_value(song, feature, value):
                matches.append(song)
            else:
                non_matches.append(song)
        
        if not matches or not non_matches:
            return 0.0
        
        # Calculate weighted entropy (consider current beliefs)
        total_belief_matches = sum(beliefs.get(song['id'], 0) for song in matches)
        total_belief_non_matches = sum(beliefs.get(song['id'], 0) for song in non_matches)
        total_belief = total_belief_matches + total_belief_non_matches
        
        if total_belief <= 0:
            return 0.0
        
        # Weighted entropy calculation
        entropy_before = -sum(p * np.log2(p) for p in beliefs.values() if p > 0)
        
        entropy_after = 0.0
        if total_belief_matches > 0:
            p_matches = total_belief_matches / total_belief
            entropy_matches = -sum((beliefs.get(song['id'], 0) / total_belief_matches) * 
                                 np.log2(beliefs.get(song['id'], 0) / total_belief_matches)
                                 for song in matches if beliefs.get(song['id'], 0) > 0)
            entropy_after += p_matches * entropy_matches
        
        if total_belief_non_matches > 0:
            p_non_matches = total_belief_non_matches / total_belief
            entropy_non_matches = -sum((beliefs.get(song['id'], 0) / total_belief_non_matches) * 
                                       np.log2(beliefs.get(song['id'], 0) / total_belief_non_matches)
                                       for song in non_matches if beliefs.get(song['id'], 0) > 0)
            entropy_after += p_non_matches * entropy_non_matches
        
        return max(0, entropy_before - entropy_after)
    
    def _calculate_adaptive_penalty(self, feature: str, asked_questions: Set[Tuple[str, str]]) -> float:
        """Calculate adaptive penalty based on recent question patterns"""
        # Count recent questions by feature (last 10 questions)
        recent_features = [q[0] for q in list(asked_questions)[-10:]]
        feature_count = recent_features.count(feature)
        
        # Stronger adaptive penalty to force diversity
        if feature_count == 0:
            return 0.0  # No penalty for new features
        elif feature_count == 1:
            return 0.2  # Small penalty
        elif feature_count == 2:
            return 0.5  # Moderate penalty
        else:
            return 0.8  # High penalty for repeated features
    
    def _calculate_graph_centrality_bonus(self, feature: str, value: str) -> float:
        """Calculate bonus based on graph centrality (simplified)"""
        # This would connect to your actual graph intelligence system
        # For now, use a simplified centrality measure
        
        # Count connections (songs with this attribute)
        connected_songs = sum(1 for song in self.songs if self._song_has_value(song, feature, value))
        total_songs = len(self.songs)
        
        if total_songs == 0:
            return 0.0
        
        # Centrality bonus (moderate connectivity is good)
        connectivity = connected_songs / total_songs
        if 0.1 <= connectivity <= 0.5:  # Sweet spot
            return 0.2
        elif 0.05 <= connectivity <= 0.7:  # Acceptable range
            return 0.1
        else:
            return 0.0  # Too rare or too common
    
    def _calculate_embedding_similarity_bonus(self, question: Dict[str, Any], beliefs: Dict[int, float]) -> float:
        """Calculate bonus based on embedding similarity (placeholder)"""
        # This would connect to your actual embedding system
        # For now, return a small random bonus to simulate embedding intelligence
        
        # In a real implementation, this would:
        # 1. Find songs most similar to current belief distribution
        # 2. Check if the question helps distinguish between them
        # 3. Return a bonus based on discriminative power
        
        return np.random.uniform(0.0, 0.1)  # Placeholder
    
    def get_feature_usage_stats(self) -> Dict[str, Any]:
        """Get statistics about feature usage"""
        feature_counts = Counter(self.asked_history)
        total_questions = len(self.asked_history)
        
        return {
            'total_questions': total_questions,
            'feature_distribution': dict(feature_counts),
            'feature_percentages': {k: (v / total_questions * 100) if total_questions > 0 else 0 
                                  for k, v in feature_counts.items()},
            'feature_importance': self.feature_importance
        }
