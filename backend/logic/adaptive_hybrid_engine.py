"""
Adaptive Hybrid Decision Engine
Dynamic weighting between graph reasoning and embedding similarity with confidence estimation
"""

import json
import os
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict, deque
import hashlib

from backend.logic.enterprise_engine import EnterpriseEngine, SongMetadata, SystemStatus
from backend.logic.enterprise_graph import EnterpriseDynamicGraph
from backend.logic.enterprise_embeddings import EnterpriseEmbeddingTrainer, EmbeddingConfig

logger = logging.getLogger(__name__)


@dataclass
class DecisionMetrics:
    """Metrics for tracking decision quality"""
    graph_successes: int = 0
    graph_failures: int = 0
    embedding_successes: int = 0
    embedding_failures: int = 0
    hybrid_successes: int = 0
    hybrid_failures: int = 0
    
    # Performance tracking
    avg_graph_response_time: float = 0.0
    avg_embedding_response_time: float = 0.0
    avg_hybrid_response_time: float = 0.0
    
    # Quality metrics
    graph_question_quality: deque = field(default_factory=lambda: deque(maxlen=100))
    embedding_question_quality: deque = field(default_factory=lambda: deque(maxlen=100))
    hybrid_question_quality: deque = field(default_factory=lambda: deque(maxlen=100))
    
    def get_graph_success_rate(self) -> float:
        total = self.graph_successes + self.graph_failures
        return self.graph_successes / total if total > 0 else 0.0
    
    def get_embedding_success_rate(self) -> float:
        total = self.embedding_successes + self.embedding_failures
        return self.embedding_successes / total if total > 0 else 0.0
    
    def get_hybrid_success_rate(self) -> float:
        total = self.hybrid_successes + self.hybrid_failures
        return self.hybrid_successes / total if total > 0 else 0.0
    
    def get_avg_graph_quality(self) -> float:
        return np.mean(self.graph_question_quality) if self.graph_question_quality else 0.0
    
    def get_avg_embedding_quality(self) -> float:
        return np.mean(self.embedding_question_quality) if self.embedding_question_quality else 0.0
    
    def get_avg_hybrid_quality(self) -> float:
        return np.mean(self.hybrid_question_quality) if self.hybrid_question_quality else 0.0


@dataclass
class ConfidenceEstimate:
    """Confidence estimate for decisions"""
    confidence_score: float
    uncertainty: float
    source: str
    reasoning: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class WeightOptimizer:
    """Dynamic weight optimization based on performance"""
    
    def __init__(self, learning_rate: float = 0.1, min_weight: float = 0.1, max_weight: float = 0.9):
        self.learning_rate = learning_rate
        self.min_weight = min_weight
        self.max_weight = max_weight
        self.weights = {"graph": 0.6, "embedding": 0.4}
        self.performance_history = deque(maxlen=50)
    
    def update_weights(self, metrics: DecisionMetrics):
        """Update weights based on recent performance"""
        # Calculate performance scores
        graph_score = self._calculate_performance_score(
            metrics.get_graph_success_rate(),
            metrics.get_avg_graph_quality(),
            metrics.avg_graph_response_time
        )
        
        embedding_score = self._calculate_performance_score(
            metrics.get_embedding_success_rate(),
            metrics.get_avg_embedding_quality(),
            metrics.avg_embedding_response_time
        )
        
        # Store performance history
        self.performance_history.append({
            "graph": graph_score,
            "embedding": embedding_score,
            "timestamp": datetime.now()
        })
        
        # Calculate target weights based on performance
        total_score = graph_score + embedding_score
        if total_score > 0:
            target_graph_weight = graph_score / total_score
            target_embedding_weight = embedding_score / total_score
        else:
            target_graph_weight = 0.5
            target_embedding_weight = 0.5
        
        # Smooth weight updates
        self.weights["graph"] = self._smooth_update(
            self.weights["graph"], target_graph_weight
        )
        self.weights["embedding"] = self._smooth_update(
            self.weights["embedding"], target_embedding_weight
        )
        
        # Ensure weights sum to 1
        total_weight = self.weights["graph"] + self.weights["embedding"]
        if total_weight > 0:
            self.weights["graph"] /= total_weight
            self.weights["embedding"] /= total_weight
        
        logger.debug(f"Updated weights: graph={self.weights['graph']:.3f}, embedding={self.weights['embedding']:.3f}")
    
    def _calculate_performance_score(self, success_rate: float, quality: float, response_time: float) -> float:
        """Calculate performance score from metrics"""
        # Normalize response time (lower is better, assume 100ms as baseline)
        time_score = 1.0 / (1.0 + response_time / 100.0)
        
        # Combine metrics
        performance_score = (success_rate * 0.4 + quality * 0.4 + time_score * 0.2)
        return performance_score
    
    def _smooth_update(self, current: float, target: float) -> float:
        """Smooth weight update to avoid oscillation"""
        updated = current + self.learning_rate * (target - current)
        return max(self.min_weight, min(self.max_weight, updated))
    
    def get_weights(self) -> Dict[str, float]:
        """Get current weights"""
        return self.weights.copy()


class UncertaintyEstimator:
    """Estimate uncertainty in predictions"""
    
    def __init__(self):
        self.uncertainty_history = deque(maxlen=100)
    
    def estimate_uncertainty(self, graph_confidence: float, embedding_confidence: float, 
                           candidate_count: int, question_diversity: float) -> ConfidenceEstimate:
        """Estimate uncertainty for a decision"""
        
        # Base uncertainty from component confidences
        component_uncertainty = 1.0 - (graph_confidence + embedding_confidence) / 2.0
        
        # Uncertainty from candidate count (more candidates = more uncertainty)
        candidate_uncertainty = min(candidate_count / 20.0, 1.0)  # Normalize to max 20 candidates
        
        # Uncertainty from question diversity (less diversity = more uncertainty)
        diversity_uncertainty = 1.0 - question_diversity
        
        # Combine uncertainties
        total_uncertainty = (component_uncertainty * 0.5 + 
                            candidate_uncertainty * 0.3 + 
                            diversity_uncertainty * 0.2)
        
        # Overall confidence
        confidence = 1.0 - total_uncertainty
        
        # Generate reasoning
        reasoning = []
        if component_uncertainty > 0.3:
            reasoning.append(f"Low component confidence: {graph_confidence:.2f}/{embedding_confidence:.2f}")
        if candidate_uncertainty > 0.3:
            reasoning.append(f"High candidate uncertainty: {candidate_count} candidates")
        if diversity_uncertainty > 0.3:
            reasoning.append(f"Low question diversity: {question_diversity:.2f}")
        
        estimate = ConfidenceEstimate(
            confidence_score=confidence,
            uncertainty=total_uncertainty,
            source="adaptive_hybrid",
            reasoning=reasoning,
            metadata={
                "graph_confidence": graph_confidence,
                "embedding_confidence": embedding_confidence,
                "candidate_count": candidate_count,
                "question_diversity": question_diversity
            }
        )
        
        self.uncertainty_history.append(estimate)
        return estimate


class AdaptiveHybridEngine(EnterpriseEngine):
    """Adaptive hybrid engine with dynamic weighting and confidence estimation"""
    
    def __init__(self, data_dir: str, enable_graph: bool = True, enable_embeddings: bool = True):
        super().__init__(data_dir)
        
        self.enable_graph = enable_graph
        self.enable_embeddings = enable_embeddings
        
        # Adaptive components
        self.weight_optimizer = WeightOptimizer()
        self.uncertainty_estimator = UncertaintyEstimator()
        self.decision_metrics = DecisionMetrics()
        
        # Subsystems
        self.graph_system = None
        self.embedding_system = None
        self.embeddings_cache = {}
        
        # Performance tracking
        self.session_history = deque(maxlen=1000)
        self.question_history = deque(maxlen=500)
        
        # Adaptive thresholds
        self.confidence_threshold = 0.7
        self.uncertainty_threshold = 0.4
        
        logger.info("AdaptiveHybridEngine initialized with adaptive capabilities")
    
    def initialize(self) -> bool:
        """Initialize all subsystems with adaptive setup"""
        try:
            # Initialize graph system
            if self.enable_graph:
                self.graph_system = EnterpriseDynamicGraph(self.data_dir)
                
                # Try to load existing graph
                if not self.graph_system.load_graph():
                    # Build from songs
                    songs = [song.to_dict() for song in self.songs]
                    if not self.graph_system.build_from_songs(songs):
                        logger.warning("Failed to build graph system")
                        self.graph_system = None
                else:
                    logger.info("Graph system loaded successfully")
            
            # Initialize embedding system
            if self.enable_embeddings:
                try:
                    embedding_config = EmbeddingConfig(
                        embedding_dim=128,
                        epochs=50,  # Reduced for faster initialization
                        batch_size=16
                    )
                    
                    self.embedding_system = EnterpriseEmbeddingTrainer(embedding_config)
                    
                    # Try to load existing embeddings
                    embedding_path = os.path.join(self.data_dir, "enterprise_embeddings.pt")
                    if os.path.exists(embedding_path):
                        if self.embedding_system.load_model(embedding_path):
                            # Compute embeddings for songs
                            songs = [song.to_dict() for song in self.songs]
                            self.embeddings_cache = self.embedding_system.compute_embeddings(songs)
                            logger.info("Embedding system loaded successfully")
                        else:
                            logger.warning("Failed to load embedding system")
                            self.embedding_system = None
                    else:
                        logger.info("No existing embeddings found - training new ones")
                        if self._train_embeddings():
                            songs = [song.to_dict() for song in self.songs]
                            self.embeddings_cache = self.embedding_system.compute_embeddings(songs)
                        else:
                            self.embedding_system = None
                            
                except Exception as e:
                    logger.warning(f"Embedding system initialization failed: {e}")
                    self.embedding_system = None
            
            # Initialize with balanced weights
            self._initialize_weights()
            
            self.is_initialized = True
            logger.info("AdaptiveHybridEngine initialization completed")
            return True
            
        except Exception as e:
            logger.error(f"Adaptive engine initialization failed: {e}")
            return False
    
    def _train_embeddings(self) -> bool:
        """Train embeddings on current songs"""
        try:
            songs = [song.to_dict() for song in self.songs]
            if len(songs) < 10:
                logger.warning("Insufficient songs for embedding training")
                return False
            
            logger.info("Training embeddings on current song dataset")
            metrics = self.embedding_system.train(songs)
            
            # Save trained model
            embedding_path = os.path.join(self.data_dir, "enterprise_embeddings.pt")
            self.embedding_system.save_model(embedding_path)
            
            logger.info(f"Embedding training completed: loss={metrics.train_loss:.4f}")
            return True
            
        except Exception as e:
            logger.error(f"Embedding training failed: {e}")
            return False
    
    def _initialize_weights(self):
        """Initialize weights based on available subsystems"""
        available_systems = []
        if self.graph_system:
            available_systems.append("graph")
        if self.embedding_system:
            available_systems.append("embedding")
        
        if len(available_systems) == 2:
            self.weight_optimizer.weights = {"graph": 0.6, "embedding": 0.4}
        elif len(available_systems) == 1:
            self.weight_optimizer.weights = {available_systems[0]: 1.0}
        else:
            self.weight_optimizer.weights = {"fallback": 1.0}
    
    def generate_question(self, candidates: List[str], context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate question using adaptive hybrid intelligence"""
        start_time = datetime.now()
        
        try:
            if not self.is_initialized:
                logger.error("Engine not initialized")
                return None
            
            # Get current weights
            weights = self.weight_optimizer.get_weights()
            
            # Generate questions from available systems
            graph_questions = []
            embedding_questions = []
            
            # Graph-based questions
            if self.graph_system and weights.get("graph", 0) > 0:
                try:
                    graph_start = datetime.now()
                    asked_questions = context.get("asked_questions", set())
                    graph_questions = self.graph_system.generate_smart_questions(candidates, asked_questions)
                    
                    # Record performance
                    response_time = (datetime.now() - graph_start).total_seconds() * 1000
                    self.decision_metrics.avg_graph_response_time = (
                        self.decision_metrics.avg_graph_response_time * 0.9 + response_time * 0.1
                    )
                    
                except Exception as e:
                    logger.warning(f"Graph question generation failed: {e}")
                    self.decision_metrics.graph_failures += 1
            
            # Embedding-based questions
            if self.embedding_system and weights.get("embedding", 0) > 0:
                try:
                    embedding_start = datetime.now()
                    # This would need to be implemented in the embedding system
                    # For now, create placeholder questions
                    embedding_questions = self._generate_embedding_questions(candidates, context)
                    
                    # Record performance
                    response_time = (datetime.now() - embedding_start).total_seconds() * 1000
                    self.decision_metrics.avg_embedding_response_time = (
                        self.decision_metrics.avg_embedding_response_time * 0.9 + response_time * 0.1
                    )
                    
                except Exception as e:
                    logger.warning(f"Embedding question generation failed: {e}")
                    self.decision_metrics.embedding_failures += 1
            
            # Adaptive question selection
            selected_question = self._adaptive_question_selection(
                graph_questions, embedding_questions, weights, candidates, context
            )
            
            # Record performance
            total_time = (datetime.now() - start_time).total_seconds() * 1000
            self.decision_metrics.avg_hybrid_response_time = (
                self.decision_metrics.avg_hybrid_response_time * 0.9 + total_time * 0.1
            )
            
            # Update question history
            if selected_question:
                self.question_history.append({
                    "question": selected_question,
                    "candidates": candidates,
                    "weights": weights,
                    "timestamp": datetime.now(),
                    "response_time": total_time
                })
            
            return selected_question
            
        except Exception as e:
            logger.error(f"Adaptive question generation failed: {e}")
            self.decision_metrics.hybrid_failures += 1
            return None
    
    def _generate_embedding_questions(self, candidates: List[str], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate questions using embedding similarity"""
        if not self.embeddings_cache:
            return []
        
        questions = []
        asked_questions = context.get("asked_questions", set())
        
        # Find clusters in embedding space
        candidate_embeddings = []
        valid_candidates = []
        
        for title in candidates:
            if title in self.embeddings_cache:
                candidate_embeddings.append(self.embeddings_cache[title])
                valid_candidates.append(title)
        
        if len(candidate_embeddings) < 2:
            return []
        
        # Simple clustering based on similarity
        embeddings_array = np.array(candidate_embeddings)
        
        # Generate questions based on embedding clusters
        for i, title1 in enumerate(valid_candidates):
            for j, title2 in enumerate(valid_candidates[i+1:], i+1):
                # Calculate similarity
                similarity = np.dot(embeddings_array[i], embeddings_array[j]) / (
                    np.linalg.norm(embeddings_array[i]) * np.linalg.norm(embeddings_array[j])
                )
                
                # If songs are similar, generate distinguishing questions
                if similarity > 0.7:
                    # Find attributes that differ between these songs
                    song1_data = next((song.to_dict() for song in self.songs if song.title == title1), None)
                    song2_data = next((song.to_dict() for song in self.songs if song.title == title2), None)
                    
                    if song1_data and song2_data:
                        distinguishing_attrs = self._find_distinguishing_attributes(song1_data, song2_data)
                        
                        for attr, value in distinguishing_attrs:
                            question_key = (attr, value)
                            if question_key not in asked_questions:
                                question = {
                                    "feature": attr,
                                    "value": value,
                                    "text": f"Is it {attr} {value}?",
                                    "source": "embedding_clustering",
                                    "similarity": similarity,
                                    "confidence": similarity
                                }
                                questions.append(question)
        
        return questions
    
    def _find_distinguishing_attributes(self, song1: Dict[str, Any], song2: Dict[str, Any]) -> List[Tuple[str, str]]:
        """Find attributes that distinguish between two songs"""
        distinguishing = []
        
        for attr in set(song1.keys()) | set(song2.keys()):
            val1 = song1.get(attr)
            val2 = song2.get(attr)
            
            if val1 != val2:
                if val1:
                    distinguishing.append((attr, str(val1)))
                if val2:
                    distinguishing.append((attr, str(val2)))
        
        return distinguishing[:5]  # Limit to top 5
    
    def _adaptive_question_selection(self, graph_questions: List[Dict[str, Any]], 
                                   embedding_questions: List[Dict[str, Any]], 
                                   weights: Dict[str, float],
                                   candidates: List[str], 
                                   context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Adaptive question selection based on weights and confidence"""
        all_questions = []
        
        # Add graph questions with weights
        for q in graph_questions:
            q["system_weight"] = weights.get("graph", 0)
            q["system_source"] = "graph"
            all_questions.append(q)
        
        # Add embedding questions with weights
        for q in embedding_questions:
            q["system_weight"] = weights.get("embedding", 0)
            q["system_source"] = "embedding"
            all_questions.append(q)
        
        if not all_questions:
            return None
        
        # Calculate adaptive scores
        for q in all_questions:
            base_score = q.get("split_score", q.get("confidence", 0.5))
            system_weight = q["system_weight"]
            
            # Apply system performance weighting
            if q["system_source"] == "graph":
                performance_multiplier = self.decision_metrics.get_graph_success_rate()
            elif q["system_source"] == "embedding":
                performance_multiplier = self.decision_metrics.get_embedding_success_rate()
            else:
                performance_multiplier = 0.5
            
            adaptive_score = base_score * system_weight * performance_multiplier
            q["adaptive_score"] = adaptive_score
        
        # Select best question
        best_question = max(all_questions, key=lambda q: q.get("adaptive_score", 0))
        
        # Estimate confidence
        confidence = self._estimate_question_confidence(best_question, candidates, context)
        best_question["confidence_estimate"] = confidence
        
        return best_question
    
    def _estimate_question_confidence(self, question: Dict[str, Any], candidates: List[str], 
                                   context: Dict[str, Any]) -> ConfidenceEstimate:
        """Estimate confidence in question quality"""
        # Base confidence from question score
        base_confidence = question.get("adaptive_score", 0.5)
        
        # System confidence
        system_confidence = 1.0
        if question["system_source"] == "graph":
            system_confidence = self.decision_metrics.get_graph_success_rate()
        elif question["system_source"] == "embedding":
            system_confidence = self.decision_metrics.get_embedding_success_rate()
        
        # Question diversity
        asked_features = set(q.get("feature") for q in self.question_history)
        feature_diversity = 1.0 - (question.get("feature", "") in asked_features)
        
        # Candidate uncertainty
        candidate_uncertainty = min(len(candidates) / 10.0, 1.0)
        
        # Overall confidence
        overall_confidence = (base_confidence * 0.4 + 
                            system_confidence * 0.4 + 
                            feature_diversity * 0.1 + 
                            (1.0 - candidate_uncertainty) * 0.1)
        
        return ConfidenceEstimate(
            confidence_score=overall_confidence,
            uncertainty=1.0 - overall_confidence,
            source="adaptive_selection",
            reasoning=[
                f"Base score: {base_confidence:.3f}",
                f"System confidence: {system_confidence:.3f}",
                f"Feature diversity: {feature_diversity:.3f}",
                f"Candidate uncertainty: {candidate_uncertainty:.3f}"
            ]
        )
    
    def update_beliefs(self, question: Dict[str, Any], answer: str) -> None:
        """Update beliefs and track performance"""
        try:
            # Record question outcome
            question_source = question.get("system_source", "unknown")
            was_successful = self._evaluate_question_success(question, answer)
            
            # Update metrics
            if question_source == "graph":
                if was_successful:
                    self.decision_metrics.graph_successes += 1
                    self.decision_metrics.graph_question_quality.append(1.0)
                else:
                    self.decision_metrics.graph_failures += 1
                    self.decision_metrics.graph_question_quality.append(0.0)
            elif question_source == "embedding":
                if was_successful:
                    self.decision_metrics.embedding_successes += 1
                    self.decision_metrics.embedding_question_quality.append(1.0)
                else:
                    self.decision_metrics.embedding_failures += 1
                    self.decision_metrics.embedding_question_quality.append(0.0)
            
            # Update weights based on performance
            if len(self.question_history) % 10 == 0:  # Update every 10 questions
                self.weight_optimizer.update_weights(self.decision_metrics)
            
            # This would integrate with the actual belief system
            logger.info(f"Belief update: {question.get('feature')} = {answer} (source: {question_source})")
            
        except Exception as e:
            logger.error(f"Belief update failed: {e}")
            self.decision_metrics.hybrid_failures += 1
    
    def _evaluate_question_success(self, question: Dict[str, Any], answer: str) -> bool:
        """Evaluate if a question was successful (simplified)"""
        # This is a simplified evaluation
        # In practice, this would track whether the question reduced uncertainty
        confidence = question.get("confidence_estimate", ConfidenceEstimate(0.5, 0.5, "unknown"))
        return confidence.confidence_score > 0.5
    
    def get_top_candidates(self, n: int = 3) -> List[Tuple[str, float]]:
        """Get top N candidates with confidence scores"""
        # This would integrate with the belief system
        # For now, return top N songs with equal confidence
        candidates = [(song.title, 1.0) for song in self.songs[:n]]
        return candidates
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            base_status = super().get_system_status()
            
            # Add adaptive components
            adaptive_status = {
                "adaptive_engine": {
                    "weights": self.weight_optimizer.get_weights(),
                    "decision_metrics": {
                        "graph_success_rate": self.decision_metrics.get_graph_success_rate(),
                        "embedding_success_rate": self.decision_metrics.get_embedding_success_rate(),
                        "hybrid_success_rate": self.decision_metrics.get_hybrid_success_rate(),
                        "avg_graph_quality": self.decision_metrics.get_avg_graph_quality(),
                        "avg_embedding_quality": self.decision_metrics.get_avg_embedding_quality(),
                        "avg_hybrid_quality": self.decision_metrics.get_avg_hybrid_quality()
                    },
                    "performance": {
                        "avg_graph_response_time": self.decision_metrics.avg_graph_response_time,
                        "avg_embedding_response_time": self.decision_metrics.avg_embedding_response_time,
                        "avg_hybrid_response_time": self.decision_metrics.avg_hybrid_response_time
                    },
                    "history": {
                        "sessions_count": len(self.session_history),
                        "questions_count": len(self.question_history)
                    },
                    "thresholds": {
                        "confidence_threshold": self.confidence_threshold,
                        "uncertainty_threshold": self.uncertainty_threshold
                    }
                }
            }
            
            # Merge with base status
            base_status.update(adaptive_status)
            return base_status
            
        except Exception as e:
            logger.error(f"Status check failed: {e}")
            return {
                "engine_type": "AdaptiveHybrid",
                "status": SystemStatus.FAILED,
                "error": str(e)
            }
    
    def adaptive_switch(self) -> str:
        """Adaptively switch between subsystems based on performance"""
        weights = self.weight_optimizer.get_weights()
        
        # Check if one system is significantly underperforming
        graph_rate = self.decision_metrics.get_graph_success_rate()
        embedding_rate = self.decision_metrics.get_embedding_success_rate()
        
        if graph_rate < 0.3 and embedding_rate > 0.7:
            return "embedding_primary"
        elif embedding_rate < 0.3 and graph_rate > 0.7:
            return "graph_primary"
        elif graph_rate < 0.3 and embedding_rate < 0.3:
            return "both_degraded"
        else:
            return "balanced"
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get detailed performance report"""
        return {
            "system_weights": self.weight_optimizer.get_weights(),
            "decision_metrics": {
                "graph": {
                    "successes": self.decision_metrics.graph_successes,
                    "failures": self.decision_metrics.graph_failures,
                    "success_rate": self.decision_metrics.get_graph_success_rate(),
                    "avg_quality": self.decision_metrics.get_avg_graph_quality(),
                    "avg_response_time": self.decision_metrics.avg_graph_response_time
                },
                "embedding": {
                    "successes": self.decision_metrics.embedding_successes,
                    "failures": self.decision_metrics.embedding_failures,
                    "success_rate": self.decision_metrics.get_embedding_success_rate(),
                    "avg_quality": self.decision_metrics.get_avg_embedding_quality(),
                    "avg_response_time": self.decision_metrics.avg_embedding_response_time
                },
                "hybrid": {
                    "successes": self.decision_metrics.hybrid_successes,
                    "failures": self.decision_metrics.hybrid_failures,
                    "success_rate": self.decision_metrics.get_hybrid_success_rate(),
                    "avg_quality": self.decision_metrics.get_avg_hybrid_quality(),
                    "avg_response_time": self.decision_metrics.avg_hybrid_response_time
                }
            },
            "adaptive_mode": self.adaptive_switch(),
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate system improvement recommendations"""
        recommendations = []
        
        graph_rate = self.decision_metrics.get_graph_success_rate()
        embedding_rate = self.decision_metrics.get_embedding_success_rate()
        
        if graph_rate < 0.5:
            recommendations.append("Consider improving graph data quality or adding more attributes")
        
        if embedding_rate < 0.5:
            recommendations.append("Consider retraining embeddings with more data or different parameters")
        
        if self.decision_metrics.avg_graph_response_time > 100:
            recommendations.append("Graph response time is high, consider optimization")
        
        if self.decision_metrics.avg_embedding_response_time > 100:
            recommendations.append("Embedding response time is high, consider caching")
        
        if not recommendations:
            recommendations.append("System performing optimally")
        
        return recommendations
