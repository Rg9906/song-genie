"""
Enhanced Main Engine Integration
Combines all enhanced systems into a unified, modular architecture
"""

import logging
from typing import List, Dict, Any, Optional, Set, Tuple
import numpy as np

logger = logging.getLogger(__name__)

# Import enhanced systems
from backend.logic.data_pipeline import DatasetPipeline, expand_dataset_pipeline
from backend.logic.graph_intelligence import create_graph_intelligence
from backend.logic.enhanced_embeddings import create_enhanced_trainer
from backend.logic.enhanced_hybrid import create_enhanced_hybrid_engine
from backend.logic.enhanced_questions import create_enhanced_question_selector
from backend.logic.evaluation_system import create_system_evaluator
from backend.logic.visualization_tools import create_system_visualizer

class EnhancedMusicAkenator:
    """Enhanced Music Akenator with all improvements integrated"""
    
    def __init__(self, target_dataset_size: int = 500):
        self.target_dataset_size = target_dataset_size
        self.songs = []
        self.graph_intelligence = None
        self.embedding_trainer = None
        self.hybrid_engine = None
        self.question_selector = None
        self.evaluator = None
        self.visualizer = None
        
        # Initialize system
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize all system components"""
        logger.info("🚀 Initializing Enhanced Music Akenator...")
        
        # 1. Expand dataset
        logger.info(f"📊 Expanding dataset to {self.target_dataset_size} songs...")
        self.songs = expand_dataset_pipeline(self.target_dataset_size)
        
        # 2. Initialize graph intelligence
        logger.info("🌐 Initializing graph intelligence...")
        self.graph_intelligence = create_graph_intelligence(self.songs)
        
        # 3. Initialize embedding trainer
        logger.info("🧠 Initializing enhanced embeddings...")
        self.embedding_trainer = create_enhanced_trainer(embedding_dim=128)
        
        # 4. Train embeddings if we have enough songs
        if len(self.songs) >= 50:
            logger.info("🏋 Training neural embeddings...")
            training_results = self.embedding_trainer.train_embeddings(self.songs, epochs=50)
            logger.info(f"✅ Embeddings trained with best validation loss: {training_results.get('best_val_loss', 'N/A')}")
        else:
            logger.warning("⚠️  Insufficient songs for embedding training (need ≥50)")
        
        # 5. Initialize hybrid engine
        logger.info("🔄 Initializing enhanced hybrid engine...")
        self.hybrid_engine = create_enhanced_hybrid_engine(
            self.songs, self.graph_intelligence, self.embedding_trainer
        )
        
        # 6. Initialize question selector
        logger.info("❓ Initializing enhanced question selector...")
        self.question_selector = create_enhanced_question_selector(self.songs)
        
        # 7. Initialize evaluator
        logger.info("📊 Initializing system evaluator...")
        self.evaluator = create_system_evaluator(
            self.songs, self.hybrid_engine, self.embedding_trainer
        )
        
        # 8. Initialize visualizer
        logger.info("🎨 Initializing visualization tools...")
        self.visualizer = create_system_visualizer(
            self.graph_intelligence, self.embedding_trainer
        )
        
        logger.info("✅ Enhanced Music Akenator initialized successfully!")
        logger.info(f"   Dataset size: {len(self.songs)} songs")
        logger.info(f"   Graph intelligence: {'Available' if self.graph_intelligence else 'Unavailable'}")
        logger.info(f"   Neural embeddings: {'Available' if self.embedding_trainer else 'Unavailable'}")
        logger.info(f"   Hybrid engine: {'Available' if self.hybrid_engine else 'Unavailable'}")
    
    def get_entities(self) -> List[Dict[str, Any]]:
        """Get all songs (for compatibility with existing API)"""
        return self.songs
    
    def get_beliefs(self) -> Dict[int, float]:
        """Get current beliefs (for compatibility with existing API)"""
        if self.hybrid_engine:
            return self.hybrid_engine.beliefs
        return {song['id']: 1.0/len(self.songs) for song in self.songs}
    
    def get_questions(self) -> List[Dict[str, Any]]:
        """Get all possible questions (for compatibility with existing API)"""
        if self.question_selector:
            return self.question_selector._generate_all_questions(self.songs)
        return []
    
    def update_beliefs(self, question: Dict[str, Any], answer: str) -> Dict[int, float]:
        """Update beliefs using enhanced hybrid engine"""
        if self.hybrid_engine:
            return self.hybrid_engine.update_beliefs(question, answer)
        
        # Fallback to simple Bayesian update
        return self._simple_bayesian_update(question, answer)
    
    def _simple_bayesian_update(self, question: Dict[str, Any], answer: str) -> Dict[int, float]:
        """Simple Bayesian update as fallback"""
        current_beliefs = self.get_beliefs()
        new_beliefs = {}
        
        feature = question['feature']
        value = question['value']
        
        for song in self.songs:
            song_id = song['id']
            prior = current_beliefs.get(song_id, 1.0/len(self.songs))
            
            # Check if song matches
            matches = self._song_matches_attribute(song, feature, value)
            
            # Apply likelihood
            if answer.lower() in ['yes', 'y', 'true']:
                likelihood = 0.9 if matches else 0.1
            else:
                likelihood = 0.1 if matches else 0.9
            
            new_beliefs[song_id] = prior * likelihood
        
        # Normalize
        total = sum(new_beliefs.values())
        if total > 0:
            new_beliefs = {song_id: belief/total for song_id, belief in new_beliefs.items()}
        
        return new_beliefs
    
    def _song_matches_attribute(self, song: Dict[str, Any], attribute: str, value: str) -> bool:
        """Check if song matches attribute value"""
        song_attributes = self._extract_song_attributes(song)
        
        if attribute not in song_attributes:
            return False
        
        return value in song_attributes[attribute]
    
    def _extract_song_attributes(self, song: Dict[str, Any]) -> Dict[str, List[str]]:
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
        
        return attributes
    
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
    
    def get_best_question(self, asked_questions: Set[Tuple[str, str]]) -> Optional[Dict[str, Any]]:
        """Get best question using enhanced systems"""
        if self.question_selector:
            return self.question_selector.select_best_question(
                self.songs, asked_questions, self.hybrid_engine
            )
        return None
    
    def should_make_guess(self, questions_asked: int) -> Tuple[bool, Optional[int]]:
        """Determine if system should make a guess"""
        if self.hybrid_engine:
            return self.hybrid_engine.should_make_guess(questions_asked)
        
        # Simple fallback
        if questions_asked < 5:
            return False, None
        
        beliefs = self.get_beliefs()
        sorted_beliefs = sorted(beliefs.items(), key=lambda x: x[1], reverse=True)
        
        if len(sorted_beliefs) >= 2:
            top_confidence = sorted_beliefs[0][1]
            second_confidence = sorted_beliefs[1][1]
            
            if top_confidence >= 0.8 and top_confidence / second_confidence >= 2.0:
                return True, sorted_beliefs[0][0]
        
        return False, None
    
    def get_confidence(self, song_id: int) -> Tuple[float, str]:
        """Get confidence for song prediction"""
        if self.hybrid_engine:
            return self.hybrid_engine.get_confidence(song_id)
        
        # Simple fallback
        beliefs = self.get_beliefs()
        if song_id in beliefs:
            belief = beliefs[song_id]
            max_belief = max(beliefs.values())
            confidence = belief / max_belief if max_belief > 0 else 0.0
            
            if confidence >= 0.8:
                return confidence, "High confidence"
            elif confidence >= 0.5:
                return confidence, "Medium confidence"
            else:
                return confidence, "Low confidence"
        
        return 0.0, "Song not found"
    
    def get_top_candidates(self, top_k: int = 5) -> List[Tuple[int, float, str]]:
        """Get top candidate songs with confidence scores"""
        if self.hybrid_engine:
            return self.hybrid_engine.get_top_candidates(top_k)
        
        # Simple fallback
        beliefs = self.get_beliefs()
        sorted_songs = sorted(beliefs.items(), key=lambda x: x[1], reverse=True)
        
        candidates = []
        for song_id, belief in sorted_songs[:top_k]:
            confidence, explanation = self.get_confidence(song_id)
            candidates.append((song_id, belief, explanation))
        
        return candidates
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = {
            'enhanced_system': True,
            'dataset_size': len(self.songs),
            'target_dataset_size': self.target_dataset_size,
            'graph_intelligence': self.graph_intelligence is not None,
            'neural_embeddings': self.embedding_trainer is not None,
            'hybrid_engine': self.hybrid_engine is not None,
            'question_selector': self.question_selector is not None,
            'evaluator': self.evaluator is not None,
            'visualizer': self.visualizer is not None,
        }
        
        if self.hybrid_engine:
            status.update(self.hybrid_engine.get_system_status())
        
        return status
    
    def run_evaluation(self, num_games: int = 100, output_dir: str = "evaluation_results"):
        """Run comprehensive system evaluation"""
        if self.evaluator:
            results = self.evaluator.run_comprehensive_evaluation(num_games)
            self.evaluator.generate_evaluation_report(results, f"{output_dir}/evaluation_report.md")
            
            # Generate visualizations
            if self.visualizer:
                self.visualizer.create_comprehensive_visualization(output_dir)
            
            return results
        
        return {'error': 'Evaluator not available'}
    
    def train_embeddings(self, epochs: int = 100, batch_size: int = 32) -> Dict[str, Any]:
        """Train neural embeddings"""
        if self.embedding_trainer:
            return self.embedding_trainer.train_embeddings(self.songs, epochs, batch_size)
        return {'error': 'Embedding trainer not available'}
    
    def save_embeddings(self, filepath: str):
        """Save trained embeddings"""
        if self.embedding_trainer:
            self.embedding_trainer.save_embeddings(filepath)
        else:
            logger.warning("No embedding trainer available to save")


def create_enhanced_akenator(target_dataset_size: int = 500) -> EnhancedMusicAkenator:
    """Factory function to create enhanced Music Akenator"""
    return EnhancedMusicAkenator(target_dataset_size)
