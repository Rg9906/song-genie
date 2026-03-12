"""
Enhanced Engine with Embedding Support
Can switch between tag-based and embedding-based question generation
"""

import json
import os
from typing import List, Dict, Any, Optional
import numpy as np

try:
    import torch
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

from backend.logic.engine import Engine as BaseEngine
from backend.logic.embeddings import EmbeddingTrainer, MetadataEncoder
from backend.logic.embedding_questions import EmbeddingQuestionSystem


class EmbeddingEngine(BaseEngine):
    """Enhanced engine that can use neural embeddings for question generation"""
    
    def __init__(self, use_embeddings: bool = False):
        super().__init__()
        
        self.use_embeddings = use_embeddings and EMBEDDINGS_AVAILABLE
        
        if self.use_embeddings:
            self.embedding_trainer = self._load_embeddings()
            if self.embedding_trainer:
                self.question_system = EmbeddingQuestionSystem(self.embedding_trainer, self.entities)
                print(f"🧠 Embedding engine loaded with {len(self.embedding_trainer.song_embeddings)} song embeddings")
            else:
                print("⚠️ Could not load embeddings, falling back to tag-based system")
                self.use_embeddings = False
        else:
            self.embedding_trainer = None
            self.question_system = None
    
    def _load_embeddings(self) -> Optional[EmbeddingTrainer]:
        """Load pre-trained embeddings"""
        if not EMBEDDINGS_AVAILABLE:
            return None
        
        model_path = os.path.join(os.path.dirname(__file__), "..", "data", "song_embeddings.pt")
        
        if not os.path.exists(model_path):
            print(f"❌ No embeddings found at {model_path}")
            print("Run 'python train_embeddings.py' first to train embeddings")
            return None
        
        try:
            # Create a dummy trainer to load the model
            trainer = EmbeddingTrainer(self.entities, embedding_dim=128)
            trainer.load_model(model_path)
            return trainer
        except Exception as e:
            print(f"❌ Error loading embeddings: {e}")
            return None
    
    def get_embedding_similarity(self, song1: str, song2: str) -> float:
        """Get neural similarity between two songs"""
        if not self.use_embeddings or not self.embedding_trainer:
            return 0.0
        
        return self.question_system._get_similarity(song1, song2)
    
    def find_similar_songs(self, song_title: str, top_k: int = 10) -> List[tuple]:
        """Find songs similar to a given song using embeddings"""
        if not self.use_embeddings or not self.embedding_trainer:
            return []
        
        return self.embedding_trainer.find_similar_songs(song_title, top_k)
    
    def generate_embedding_question(self, candidate_songs: List[str], asked_questions: set) -> Optional[Dict[str, Any]]:
        """Generate a question based on embedding analysis"""
        if not self.use_embeddings or not self.question_system:
            return None
        
        return self.question_system.generate_smart_question(candidate_songs, asked_questions)
    
    def explain_similarity(self, song1: str, song2: str) -> Dict[str, Any]:
        """Explain why two songs are considered similar"""
        if not self.use_embeddings or not self.question_system:
            return {"similarity": 0.0, "explanation": "Embeddings not available"}
        
        return self.question_system.explain_embedding_similarity(song1, song2)
    
    def get_enhanced_question_stats(self, song_beliefs: List[float], top_n: int = 5) -> Dict[str, Any]:
        """Get enhanced statistics about current beliefs using embeddings"""
        if not self.use_embeddings:
            return {"error": "Embeddings not enabled"}
        
        # Get top candidate songs
        song_indices = sorted(range(len(song_beliefs)), key=lambda i: song_beliefs[i], reverse=True)[:top_n]
        candidate_titles = [self.entities[i]["title"] for i in song_indices]
        
        # Analyze similarity patterns
        similarity_matrix = {}
        for i, title1 in enumerate(candidate_titles):
            similarity_matrix[title1] = {}
            for j, title2 in enumerate(candidate_titles):
                if i != j:
                    similarity_matrix[title1][title2] = self.get_embedding_similarity(title1, title2)
        
        # Find clusters of similar songs
        clusters = self._find_similarity_clusters(candidate_titles)
        
        return {
            "top_candidates": candidate_titles,
            "similarities": similarity_matrix,
            "clusters": clusters,
            "embedding_available": True
        }
    
    def _find_similarity_clusters(self, songs: List[str], threshold: float = 0.7) -> List[List[str]]:
        """Find clusters of similar songs among candidates"""
        if not self.use_embeddings:
            return []
        
        clusters = []
        unvisited = set(songs)
        
        while unvisited:
            # Start a new cluster with the first unvisited song
            current_song = unvisited.pop()
            cluster = [current_song]
            
            # Find all songs similar to the current cluster
            to_check = [current_song]
            
            while to_check:
                check_song = to_check.pop()
                
                for other_song in list(unvisited):
                    similarity = self.get_embedding_similarity(check_song, other_song)
                    if similarity > threshold:
                        cluster.append(other_song)
                        unvisited.remove(other_song)
                        to_check.append(other_song)
            
            if len(cluster) > 1:  # Only keep clusters with multiple songs
                clusters.append(cluster)
        
        return clusters
    
    def reload(self):
        """Reload the engine"""
        super().reload()
        
        if self.use_embeddings:
            self.embedding_trainer = self._load_embeddings()
            if self.embedding_trainer:
                self.question_system = EmbeddingQuestionSystem(self.embedding_trainer, self.entities)


# Factory function to create the appropriate engine
def create_engine(use_embeddings: bool = False) -> BaseEngine:
    """Create either a regular engine or embedding-enhanced engine"""
    if use_embeddings:
        return EmbeddingEngine(use_embeddings=True)
    else:
        return BaseEngine()
