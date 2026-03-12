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

logger = logging.getLogger(__name__)

class SimpleEnhancedAkenator:
    """Simple enhanced Music Akenator that works with basic dependencies"""
    
    def __init__(self, target_dataset_size: int = 200):
        self.target_dataset_size = target_dataset_size
        self.songs = []
        self.beliefs = {}
        
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
        """Get all possible questions"""
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
        """Get best question using information gain"""
        all_questions = self.get_questions()
        
        # Filter out already asked questions
        available_questions = [
            q for q in all_questions 
            if (q['feature'], q['value']) not in asked_questions
        ]
        
        if not available_questions:
            return None
        
        # Score questions using information gain
        best_question = None
        best_score = -1.0
        
        for question in available_questions:
            score = self._calculate_information_gain(question)
            if score > best_score:
                best_score = score
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
