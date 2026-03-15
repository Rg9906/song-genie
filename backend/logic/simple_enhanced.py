"""
Simple Enhanced Music Akenator
Works with basic dependencies only
"""

import json
import numpy as np
from typing import List, Dict, Any, Optional, Set, Tuple
import logging
import random
import os
from collections import Counter

# Try to import intelligent selector
try:
    from .intelligent_question_selector import IntelligentQuestionSelector
    INTELLIGENT_SELECTOR_AVAILABLE = True
except ImportError:
    INTELLIGENT_SELECTOR_AVAILABLE = False
    logging.warning("Intelligent selector not available, using fallback")

# Try to import diverse question generator
try:
    from .diverse_question_generator import DiverseQuestionGenerator
    DIVERSE_GENERATOR_AVAILABLE = True
except ImportError:
    DIVERSE_GENERATOR_AVAILABLE = False
    logging.warning("Diverse generator not available, using fallback")

# Try to import LLM framer
try:
    from .free_llm_question_framer import FreeLLMQuestionFramer
    LLM_FRAMER_AVAILABLE = True
except ImportError:
    LLM_FRAMER_AVAILABLE = False
    logging.warning("LLM framer not available, using fallback")

# Try to import dynamic AI engine
try:
    from .simple_dynamic_engine import SimpleDynamicEngine
    DYNAMIC_AI_ENGINE_AVAILABLE = True
except ImportError:
    DYNAMIC_AI_ENGINE_AVAILABLE = False
    logging.warning("Simple dynamic engine not available, using fallback")

# Try to import free AI integrator
try:
    from .free_ai_integrator import FreeAIIntegrator
    FREE_AI_AVAILABLE = True
except ImportError:
    FREE_AI_AVAILABLE = False
    logging.warning("Free AI integrator not available, using fallback")

# Try to import ultimate dynamic system
try:
    from .ultimate_dynamic_simple import UltimateDynamicSimple
    ULTIMATE_DYNAMIC_AVAILABLE = True
except ImportError:
    ULTIMATE_DYNAMIC_AVAILABLE = False
    logging.warning("Ultimate dynamic system not available, using fallback")

logger = logging.getLogger(__name__)

class SimpleEnhancedAkenator:
    """Simple enhanced Music Akenator that works with basic dependencies"""
    
    def __init__(self, target_dataset_size: int = 200):
        self.target_dataset_size = target_dataset_size
        self.songs = []
        self.beliefs = {}
        self.intelligent_selector = None
        self.diverse_generator = None
        self.llm_framer = None
        self.dynamic_ai_engine = None
        self.free_ai_integrator = None
        self.ultimate_dynamic_system = None
        
        # Initialize system
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize system components"""
        logger.info("🚀 Initializing Simple Enhanced Music Akenator...")
        
        # Load existing songs
        self.songs = self._load_existing_songs()
        
        # Expand dataset if needed
        if len(self.songs) < self.target_dataset_size:
            logger.info(f"📊 Expanding dataset from {len(self.songs)} to {self.target_dataset_size} songs...")
            self.songs = self._expand_dataset(self.target_dataset_size)
        
        # Initialize beliefs
        self.beliefs = {song['id']: 1.0/len(self.songs) for song in self.songs}
        
        # Initialize intelligent question selector
        if INTELLIGENT_SELECTOR_AVAILABLE:
            try:
                self.intelligent_selector = IntelligentQuestionSelector(
                    self.songs, 
                    use_graph=True, 
                    use_embeddings=False  # Set to True if you want embeddings
                )
                logger.info("🧠 Using intelligent question selector")
            except Exception as e:
                logger.warning(f"Failed to initialize intelligent selector: {e}")
                self.intelligent_selector = None
        else:
            logger.info("📊 Using basic question selection")
        
        # Initialize diverse question generator
        if DIVERSE_GENERATOR_AVAILABLE:
            try:
                self.diverse_generator = DiverseQuestionGenerator(self.songs)
                logger.info("🎨 Using diverse question generator")
            except Exception as e:
                logger.warning(f"Failed to initialize diverse generator: {e}")
                self.diverse_generator = None
        else:
            logger.info("📝 Using basic question generation")
        
        # Initialize LLM framer
        if LLM_FRAMER_AVAILABLE:
            try:
                self.llm_framer = FreeLLMQuestionFramer(use_llm=False)  # Set to True to use actual LLM
                logger.info("🗣️ Using LLM question framer")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM framer: {e}")
                self.llm_framer = None
        else:
            logger.info("💬 Using basic question framing")
        
        # Initialize dynamic AI engine
        if DYNAMIC_AI_ENGINE_AVAILABLE:
            try:
                self.dynamic_ai_engine = SimpleDynamicEngine(self.songs)
                logger.info("🤖 Using simple dynamic question engine")
            except Exception as e:
                logger.warning(f"Failed to initialize simple dynamic engine: {e}")
                self.dynamic_ai_engine = None
        else:
            logger.info("📊 Using basic question engine")
        
        # Initialize free AI integrator
        if FREE_AI_AVAILABLE:
            try:
                self.free_ai_integrator = FreeAIIntegrator()
                logger.info("🌐 Using free AI integrator")
            except Exception as e:
                logger.warning(f"Failed to initialize free AI integrator: {e}")
                self.free_ai_integrator = None
        else:
            logger.info("🔧 Using local generation only")
        
        # Initialize ultimate dynamic system
        if ULTIMATE_DYNAMIC_AVAILABLE:
            try:
                self.ultimate_dynamic_system = UltimateDynamicSimple(self.songs)
                logger.info("🚀 Using ultimate dynamic system")
            except Exception as e:
                logger.warning(f"Failed to initialize ultimate dynamic system: {e}")
                self.ultimate_dynamic_system = None
        else:
            logger.info("📊 Using fallback systems")
        
        logger.info(f"✅ Simple Enhanced Akenator initialized with {len(self.songs)} songs")
    
    def _load_existing_songs(self) -> List[Dict[str, Any]]:
        """Load existing songs from dataset"""
        try:
            # Try to load from standard location
            data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'songs_kg.json')
            
            if os.path.exists(data_path):
                with open(data_path, 'r', encoding='utf-8') as f:
                    songs = json.load(f)
                
                # Validate and normalize songs
                valid_songs = []
                for i, song in enumerate(songs):
                    if self._validate_song(song):
                        song['id'] = i
                        song = self._normalize_song(song)
                        valid_songs.append(song)
                
                logger.info(f"📊 Loaded {len(valid_songs)} valid songs from existing dataset")
                return valid_songs
            else:
                logger.warning("No existing dataset found, using minimal dataset")
                return self._create_minimal_dataset()
        
        except Exception as e:
            logger.error(f"Error loading existing dataset: {e}")
            return self._create_minimal_dataset()
    
    def _create_minimal_dataset(self) -> List[Dict[str, Any]]:
        """Create a minimal dataset for testing"""
        return [
            {
                'id': 0,
                'title': 'Shape of You',
                'artists': ['Ed Sheeran'],
                'genres': ['pop'],
                'release_year': 2017,
                'decade': '2010s',
                'era': '2010s+ Era',
                'is_collaboration': False,
                'is_viral_hit': True
            },
            {
                'id': 1,
                'title': 'Blinding Lights',
                'artists': ['The Weeknd'],
                'genres': ['pop', 'synth-pop'],
                'release_year': 2020,
                'decade': '2020s',
                'era': '2010s+ Era',
                'is_collaboration': False,
                'is_viral_hit': True
            },
            {
                'id': 2,
                'title': 'Levitating',
                'artists': ['Dua Lipa'],
                'genres': ['pop', 'disco'],
                'release_year': 2020,
                'decade': '2020s',
                'era': '2010s+ Era',
                'is_collaboration': False,
                'is_viral_hit': True
            }
        ]
    
    def _expand_dataset(self, target_size: int) -> List[Dict[str, Any]]:
        """Expand dataset with synthetic songs"""
        current_songs = self.songs.copy()
        
        # Create synthetic songs to reach target size
        synthetic_songs = []
        
        # Templates for synthetic songs
        artist_templates = [
            'Taylor Swift', 'Drake', 'Billie Eilish', 'Ariana Grande', 
            'Post Malone', 'Olivia Rodrigo', 'Harry Styles', 'BTS'
        ]
        
        genre_templates = [
            'pop', 'rock', 'hip-hop', 'r&b', 'electronic', 'country'
        ]
        
        for i in range(target_size - len(current_songs)):
            song = {
                'id': len(current_songs) + i,
                'title': f'Synthetic Song {i+1}',
                'artists': [random.choice(artist_templates)],
                'genres': [random.choice(genre_templates)],
                'release_year': random.randint(2010, 2023),
                'is_collaboration': random.choice([True, False]),
                'is_viral_hit': random.choice([True, False])
            }
            
            # Add derived attributes
            song['decade'] = f"{(song['release_year'] // 10) * 10}s"
            song['era'] = self._get_era(song['release_year'])
            
            synthetic_songs.append(song)
        
        expanded_songs = current_songs + synthetic_songs
        logger.info(f"✅ Expanded dataset to {len(expanded_songs)} songs")
        return expanded_songs
    
    def _validate_song(self, song: Dict[str, Any]) -> bool:
        """Validate song has required fields"""
        required_fields = ['title', 'artists']
        
        for field in required_fields:
            if field not in song or not song[field]:
                return False
        
        return True
    
    def _normalize_song(self, song: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize song attributes"""
        normalized = song.copy()
        
        # Ensure lists for certain fields
        for field in ['artists', 'genres']:
            if field in normalized and isinstance(normalized[field], str):
                normalized[field] = [normalized[field]]
            elif field not in normalized:
                normalized[field] = []
        
        # Add derived attributes
        if 'release_year' in normalized:
            year = normalized['release_year']
            normalized['decade'] = f"{(year // 10) * 10}s"
            normalized['era'] = self._get_era(year)
        
        # Add boolean attributes
        normalized['is_collaboration'] = normalized.get('is_collaboration', False)
        normalized['is_soundtrack'] = normalized.get('is_soundtrack', False)
        normalized['is_viral_hit'] = normalized.get('is_viral_hit', False)
        
        return normalized
    
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
    
    def get_entities(self) -> List[Dict[str, Any]]:
        """Get all songs"""
        return self.songs
    
    def get_beliefs(self) -> Dict[int, float]:
        """Get current beliefs"""
        return self.beliefs
    
    def get_questions(self) -> List[Dict[str, Any]]:
        """Get questions using dynamic AI engine or fallback"""
        if self.dynamic_ai_engine:
            try:
                questions = self.dynamic_ai_engine.generate_dynamic_questions(set(), max_questions=50)
                logger.info(f"🤖 Generated {len(questions)} dynamic AI questions")
                return questions
            except Exception as e:
                logger.warning(f"Dynamic AI engine failed: {e}")
        
        # Fallback to diverse generator
        if self.diverse_generator:
            try:
                questions = self.diverse_generator.generate_diverse_questions(max_per_category=3)
                logger.info(f"🎨 Generated {len(questions)} diverse questions")
                return questions
            except Exception as e:
                logger.warning(f"Diverse generator failed: {e}")
        
        # Final fallback to basic question generation
        return self._generate_basic_questions()
    
    def _generate_basic_questions(self) -> List[Dict[str, Any]]:
        """Fallback basic question generation"""
        questions = []
        attribute_values = {}
        
        # Collect all attribute values
        for song in self.songs:
            for attr in ['genres', 'artists', 'decade', 'era']:
                if attr not in attribute_values:
                    attribute_values[attr] = set()
                
                values = song.get(attr, [])
                if isinstance(values, list):
                    attribute_values[attr].update(values)
                elif values:
                    attribute_values[attr].add(str(values))
        
        # Generate questions
        for attr, values in attribute_values.items():
            for value in values:
                if value and str(value).strip():
                    questions.append({
                        'feature': attr,
                        'value': str(value),
                        'text': self._generate_question_text(attr, str(value))
                    })
        
        return questions
    
    def _generate_question_text(self, attribute: str, value: str) -> str:
        """Generate natural language question"""
        templates = {
            'genres': f"Is it a {value} song?",
            'artists': f"Is it by {value}?",
            'decade': f"Was it released in the {value}?",
            'era': f"Is it from the {value}?",
            'is_collaboration': "Is it a collaboration song?",
            'is_soundtrack': "Is it from a soundtrack?",
            'is_viral_hit': "Is it a viral hit song?"
        }
        
        return templates.get(attribute, f"Is it connected with {value}?")
    
    def update_beliefs(self, question: Dict[str, Any], answer: str) -> Dict[int, float]:
        """Update beliefs using Bayesian inference"""
        feature = question['feature']
        value = question['value']
        
        new_beliefs = {}
        
        for song in self.songs:
            song_id = song['id']
            prior = self.beliefs.get(song_id, 1.0/len(self.songs))
            
            # Check if song matches the question
            matches = self._song_matches_attribute(song, feature, value)
            
            # Apply likelihood
            if answer.lower() in ['yes', 'y', 'true']:
                likelihood = 0.9 if matches else 0.1
            else:
                likelihood = 0.1 if matches else 0.9
            
            new_beliefs[song_id] = prior * likelihood
        
        # Normalize beliefs
        total = sum(new_beliefs.values())
        if total > 0:
            new_beliefs = {song_id: belief/total for song_id, belief in new_beliefs.items()}
        
        self.beliefs = new_beliefs
        return new_beliefs
    
    def _song_matches_attribute(self, song: Dict[str, Any], attribute: str, value: str) -> bool:
        """Check if song matches attribute value"""
        song_value = song.get(attribute)
        
        if isinstance(song_value, list):
            return value in song_value
        else:
            return str(song_value) == value
    
    def get_best_question(self, asked_questions: Set[Tuple[str, str]]) -> Optional[Dict[str, Any]]:
        """Get best question using ultimate dynamic system"""
        # Try ultimate dynamic system first
        if self.ultimate_dynamic_system:
            try:
                ultimate_questions = self.ultimate_dynamic_system.generate_ultimate_questions(
                    asked_questions, self.beliefs, max_questions=10
                )
                if ultimate_questions:
                    best_question = ultimate_questions[0]
                    # Record usage
                    self.ultimate_dynamic_system.record_question_asked(best_question)
                    logger.debug(f"🚀 Ultimate question: {best_question['text']}")
                    return best_question
            except Exception as e:
                logger.warning(f"Ultimate system failed: {e}")
        
        # Try simple dynamic engine
        if self.dynamic_ai_engine:
            try:
                dynamic_questions = self.dynamic_ai_engine.generate_dynamic_questions(
                    asked_questions, max_questions=10
                )
                if dynamic_questions:
                    best_question = dynamic_questions[0]
                    logger.debug(f"🤖 Dynamic question: {best_question['text']}")
                    return best_question
            except Exception as e:
                logger.warning(f"Dynamic selection failed: {e}")
        
        # Try free AI integrator
        if self.free_ai_integrator:
            try:
                ai_questions = self.free_ai_integrator.generate_dynamic_questions(
                    self.songs, asked_questions
                )
                if ai_questions:
                    best_question = ai_questions[0]
                    logger.debug(f"🌐 Free AI question: {best_question['text']}")
                    return best_question
            except Exception as e:
                logger.warning(f"Free AI selection failed: {e}")
        
        # Fallback to intelligent selector
        all_questions = self.get_questions()
        available_questions = [
            q for q in all_questions 
            if (q['feature'], q['value']) not in asked_questions
        ]
        
        if not available_questions:
            return None
        
        # Use intelligent selector if available
        if self.intelligent_selector:
            best_question = self.intelligent_selector.select_best_question(
                available_questions, 
                asked_questions, 
                self.beliefs
            )
        else:
            # Fallback to basic selection with diversity
            best_question = self._fallback_question_selection(available_questions, asked_questions)
        
        if not best_question:
            return None
        
        # Apply LLM framing if available
        if self.llm_framer:
            try:
                framed_question = self.llm_framer.frame_question(best_question)
                logger.debug(f"🗣️ Framed question: {framed_question['text']}")
                return framed_question
            except Exception as e:
                logger.warning(f"LLM framing failed: {e}")
        
        return best_question
    
    def _fallback_question_selection(self, available_questions: List[Dict[str, Any]], 
                                   asked_questions: Set[Tuple[str, str]]) -> Optional[Dict[str, Any]]:
        """Fallback question selection with basic diversity"""
        # Count asked questions by feature to ensure diversity
        asked_features = Counter([q[0] for q in asked_questions])
        
        # Score questions using information gain + diversity penalty
        best_question = None
        best_score = -1.0
        
        for question in available_questions:
            # Base information gain score
            info_gain = self._calculate_information_gain(question)
            
            # Add diversity penalty (prefer features we haven't asked much)
            feature = question['feature']
            diversity_penalty = asked_features.get(feature, 0) * 0.1
            
            # Combined score
            combined_score = info_gain - diversity_penalty
            
            # Bonus for asking different features
            if asked_features.get(feature, 0) == 0:
                combined_score += 0.01  # Small bonus for new features
            
            if combined_score > best_score:
                best_score = combined_score
                best_question = question
        
        return best_question
    
    def _calculate_information_gain(self, question: Dict[str, Any]) -> float:
        """Calculate information gain for a question"""
        feature = question['feature']
        value = question['value']
        
        # Split songs by this question
        matches = []
        non_matches = []
        
        for song in self.songs:
            if self._song_matches_attribute(song, feature, value):
                matches.append(song)
            else:
                non_matches.append(song)
        
        if not matches or not non_matches:
            return 0.0
        
        # Calculate entropy
        total = len(self.songs)
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
                entropy -= probability * np.log2(probability)
        
        return entropy
    
    def should_make_guess(self, questions_asked: int) -> Tuple[bool, Optional[int]]:
        """Determine if system should make a guess"""
        if questions_asked < 3:
            return False, None
        
        # Get top candidates
        sorted_beliefs = sorted(self.beliefs.items(), key=lambda x: x[1], reverse=True)
        
        if len(sorted_beliefs) >= 2:
            top_confidence = sorted_beliefs[0][1]
            second_confidence = sorted_beliefs[1][1]
            
            if top_confidence >= 0.8 and top_confidence / second_confidence >= 2.0:
                return True, sorted_beliefs[0][0]
        
        return False, None
    
    def get_confidence(self, song_id: int) -> Tuple[float, str]:
        """Get confidence for song prediction"""
        if song_id not in self.beliefs:
            return 0.0, "Song not found"
        
        belief = self.beliefs[song_id]
        max_belief = max(self.beliefs.values())
        confidence = belief / max_belief if max_belief > 0 else 0.0
        
        if confidence >= 0.8:
            return confidence, "High confidence"
        elif confidence >= 0.5:
            return confidence, "Medium confidence"
        else:
            return confidence, "Low confidence"
    
    def get_top_candidates(self, top_k: int = 5) -> List[Tuple[int, float, str]]:
        """Get top candidate songs with confidence scores"""
        sorted_songs = sorted(self.beliefs.items(), key=lambda x: x[1], reverse=True)
        
        candidates = []
        for song_id, belief in sorted_songs[:top_k]:
            confidence, explanation = self.get_confidence(song_id)
            candidates.append((song_id, belief, explanation))
        
        return candidates
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            'system_type': 'Simple Enhanced',
            'dataset_size': len(self.songs),
            'target_dataset_size': self.target_dataset_size,
            'active_songs': len([b for b in self.beliefs.values() if b > 1e-6]),
            'features': ['genres', 'artists', 'decade', 'era', 'is_collaboration', 'is_viral_hit']
        }


def create_simple_enhanced_akenator(target_dataset_size: int = 200) -> SimpleEnhancedAkenator:
    """Factory function to create simple enhanced akenator"""
    return SimpleEnhancedAkenator(target_dataset_size)
