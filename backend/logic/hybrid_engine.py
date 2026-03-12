"""
Hybrid Engine - Combines Dynamic Graph + Neural Embeddings
Maximum robustness with multiple intelligence sources
"""

import json
import os
from typing import List, Dict, Any, Optional, Tuple, Set
import numpy as np
from collections import defaultdict
import random

try:
    import torch
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

from backend.logic.engine import Engine as BaseEngine
from backend.logic.dynamic_graph import DynamicWikidataGraph, build_dynamic_graph
from backend.logic.embeddings import EmbeddingTrainer, MetadataEncoder
from backend.logic.embedding_questions import EmbeddingQuestionSystem


class HybridIntelligence:
    """Combines graph-based and embedding-based intelligence"""
    
    def __init__(self, songs: List[Dict[str, Any]]):
        self.songs = songs
        self.title_to_idx = {song["title"]: i for i, song in enumerate(songs)}
        
        # Initialize both systems
        self.graph_system = None
        self.embedding_system = None
        
        # Confidence weights for each system
        self.graph_weight = 0.6  # Graph is primary
        self.embedding_weight = 0.4  # Embeddings enhance
        
        # Performance tracking
        self.system_performance = {
            "graph": {"successes": 0, "failures": 0},
            "embedding": {"successes": 0, "failures": 0}
        }
    
    def initialize_graph_system(self):
        """Initialize the dynamic graph system"""
        try:
            print("🌐 Initializing dynamic graph system...")
            self.graph_system = DynamicWikidataGraph()
            
            # Try to load existing graph
            graph_path = os.path.join(os.path.dirname(__file__), "..", "data", "dynamic_graph.json")
            self.graph_system.load_graph(graph_path)
            
            # If empty or doesn't exist, build it
            if not self.graph_system.graph["songs"]:
                print("🏗️ Building comprehensive Wikidata graph...")
                self.graph_system = build_dynamic_graph(limit=300)  # More songs for robustness
                self.graph_system.save_graph(graph_path)
            
            print(f"✅ Graph system: {len(self.graph_system.graph['songs'])} songs, {len(self.graph_system.graph['attributes'])} attribute types")
            return True
            
        except Exception as e:
            print(f"⚠️ Graph system failed: {e}")
            return False
    
    def initialize_embedding_system(self):
        """Initialize the neural embedding system"""
        if not EMBEDDINGS_AVAILABLE:
            print("⚠️ PyTorch not available for embeddings")
            return False
        
        try:
            print("🧠 Initializing neural embedding system...")
            
            # Try to load existing embeddings
            model_path = os.path.join(os.path.dirname(__file__), "..", "data", "song_embeddings.pt")
            
            if os.path.exists(model_path):
                trainer = EmbeddingTrainer(self.songs, embedding_dim=128)
                trainer.load_model(model_path)
                self.embedding_system = EmbeddingQuestionSystem(trainer, self.songs)
                print(f"✅ Embedding system: {len(trainer.song_embeddings)} song embeddings")
                return True
            else:
                print("⚠️ No pre-trained embeddings found. Run 'python train_embeddings.py' first")
                return False
                
        except Exception as e:
            print(f"⚠️ Embedding system failed: {e}")
            return False
    
    def calculate_hybrid_similarity(self, song1: str, song2: str) -> float:
        """Calculate combined similarity from both systems"""
        similarities = []
        weights = []
        
        # Graph-based similarity
        if self.graph_system:
            graph_sim = self._calculate_graph_similarity(song1, song2)
            similarities.append(graph_sim)
            weights.append(self.graph_weight)
        
        # Embedding-based similarity
        if self.embedding_system:
            embed_sim = self.embedding_system._get_similarity(song1, song2)
            similarities.append(embed_sim)
            weights.append(self.embedding_weight)
        
        if not similarities:
            return 0.0
        
        # Weighted average
        total_weight = sum(weights)
        weighted_sim = sum(s * w for s, w in zip(similarities, weights)) / total_weight
        
        return weighted_sim
    
    def _calculate_graph_similarity(self, song1: str, song2: str) -> float:
        """Calculate similarity using dynamic graph"""
        if not self.graph_system:
            return 0.0
        
        # Get attributes for both songs
        attrs1 = self.graph_system.get_song_attributes(song1)
        attrs2 = self.graph_system.get_song_attributes(song2)
        
        if not attrs1 or not attrs2:
            return 0.0
        
        # Calculate Jaccard similarity of attributes
        common_attrs = set(attrs1.items()) & set(attrs2.items())
        total_attrs = set(attrs1.items()) | set(attrs2.items())
        
        if not total_attrs:
            return 0.0
        
        return len(common_attrs) / len(total_attrs)
    
    def generate_optimal_question(self, candidate_songs: List[str], asked_questions: Set[Tuple[str, str]]) -> Optional[Dict[str, Any]]:
        """Generate the optimal question using both systems"""
        if len(candidate_songs) <= 1:
            return None
        
        # Get questions from both systems
        questions = []
        
        # Graph-based questions
        if self.graph_system:
            graph_questions = self.graph_system.generate_smart_questions(candidate_songs, asked_questions)
            for q in graph_questions:
                q["source"] = "graph"
                q["confidence"] = 0.8  # High confidence in graph
                questions.append(q)
        
        # Embedding-based questions
        if self.embedding_system:
            embed_question = self.embedding_system.generate_smart_question(candidate_songs, asked_questions)
            if embed_question:
                embed_question["source"] = "embedding"
                embed_question["confidence"] = 0.7  # Slightly lower confidence
                questions.append(embed_question)
        
        if not questions:
            return None
        
        # Select the best question based on confidence and performance
        best_question = self._select_best_question(questions)
        
        return best_question
    
    def _select_best_question(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select the best question from candidates"""
        if len(questions) == 1:
            return questions[0]
        
        # Score each question
        scored_questions = []
        for q in questions:
            score = q.get("confidence", 0.5)
            
            # Adjust based on system performance
            source = q.get("source", "unknown")
            if source in self.system_performance:
                perf = self.system_performance[source]
                if perf["successes"] + perf["failures"] > 0:
                    success_rate = perf["successes"] / (perf["successes"] + perf["failures"])
                    score *= success_rate
            
            # Add distinguishing score if available
            if "distinguishing_score" in q:
                score *= (1 + q["distinguishing_score"])
            
            scored_questions.append((score, q))
        
        # Return the highest scoring question
        scored_questions.sort(key=lambda x: x[0], reverse=True)
        return scored_questions[0][1]
    
    def update_performance(self, source: str, success: bool):
        """Update system performance tracking"""
        if source in self.system_performance:
            if success:
                self.system_performance[source]["successes"] += 1
            else:
                self.system_performance[source]["failures"] += 1
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get status of both systems"""
        status = {
            "graph_available": self.graph_system is not None,
            "embedding_available": self.embedding_system is not None,
            "performance": self.system_performance,
            "weights": {
                "graph": self.graph_weight,
                "embedding": self.embedding_weight
            }
        }
        
        # Add system-specific stats
        if self.graph_system:
            status["graph_stats"] = {
                "songs": len(self.graph_system.graph["songs"]),
                "attribute_types": len(self.graph_system.graph["attributes"])
            }
        
        if self.embedding_system:
            status["embedding_stats"] = {
                "songs": len(self.embedding_system.trainer.song_embeddings),
                "embedding_dim": self.embedding_system.trainer.embedding_dim
            }
        
        return status
    
    def explain_similarity(self, song1: str, song2: str) -> Dict[str, Any]:
        """Explain similarity using both systems"""
        explanations = []
        
        # Graph explanation
        if self.graph_system:
            attrs1 = self.graph_system.get_song_attributes(song1)
            attrs2 = self.graph_system.get_song_attributes(song2)
            
            if attrs1 and attrs2:
                common_attrs = set(attrs1.items()) & set(attrs2.items())
                if common_attrs:
                    explanations.append({
                        "source": "graph",
                        "reason": f"Share {len(common_attrs)} attributes: {', '.join([f'{k}={v}' for k, v in list(common_attrs)[:3]])}"
                    })
        
        # Embedding explanation
        if self.embedding_system:
            embed_explanation = self.embedding_system.explain_embedding_similarity(song1, song2)
            if embed_explanation.get("common_features"):
                explanations.append({
                    "source": "embedding",
                    "reason": embed_explanation["explanation"]
                })
        
        return {
            "similarity": self.calculate_hybrid_similarity(song1, song2),
            "explanations": explanations,
            "systems_used": [exp["source"] for exp in explanations]
        }


class HybridEngine(BaseEngine):
    """Enhanced engine with hybrid graph + embedding intelligence"""
    
    def __init__(self, enable_graph: bool = True, enable_embeddings: bool = True):
        super().__init__()
        
        self.enable_graph = enable_graph
        self.enable_embeddings = enable_embeddings
        
        # Initialize hybrid intelligence
        self.hybrid = HybridIntelligence(self.entities)
        
        # Initialize systems
        if enable_graph:
            self.hybrid.initialize_graph_system()
        
        if enable_embeddings:
            self.hybrid.initialize_embedding_system()
        
        print(f"🚀 Hybrid Engine initialized")
        print(f"   Graph: {'✅' if self.hybrid.graph_system else '❌'}")
        print(f"   Embeddings: {'✅' if self.hybrid.embedding_system else '❌'}")
    
    def get_optimal_question(self, candidate_songs: List[str], asked_questions: Set[Tuple[str, str]]) -> Optional[Dict[str, Any]]:
        """Get the optimal question using hybrid intelligence"""
        return self.hybrid.generate_optimal_question(candidate_songs, asked_questions)
    
    def calculate_similarity(self, song1: str, song2: str) -> float:
        """Calculate hybrid similarity between songs"""
        return self.hybrid.calculate_hybrid_similarity(song1, song2)
    
    def find_similar_songs(self, song_title: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """Find similar songs using hybrid approach"""
        all_titles = [song["title"] for song in self.entities]
        similarities = []
        
        for title in all_titles:
            if title != song_title:
                sim = self.calculate_similarity(song_title, title)
                similarities.append((title, sim))
        
        # Sort by similarity and return top-k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def explain_similarity(self, song1: str, song2: str) -> Dict[str, Any]:
        """Explain similarity using both systems"""
        return self.hybrid.explain_similarity(song1, song2)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = self.hybrid.get_system_status()
        status.update({
            "total_songs": len(self.entities),
            "total_questions": len(self.questions),
            "engine_type": "hybrid"
        })
        return status
    
    def update_learning_performance(self, question_source: str, was_correct: bool):
        """Update learning performance based on feedback"""
        self.hybrid.update_performance(question_source, was_correct)
    
    def reload(self):
        """Reload with enhanced capabilities"""
        super().reload()
        
        # Reinitialize hybrid systems
        self.hybrid = HybridIntelligence(self.entities)
        
        if self.enable_graph:
            self.hybrid.initialize_graph_system()
        
        if self.enable_embeddings:
            self.hybrid.initialize_embedding_system()


def create_hybrid_engine(enable_graph: bool = True, enable_embeddings: bool = True) -> HybridEngine:
    """Create a hybrid engine with specified capabilities"""
    return HybridEngine(enable_graph=enable_graph, enable_embeddings=enable_embeddings)
