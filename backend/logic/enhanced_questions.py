"""
Enhanced Question Selection System
Optimized question generation with diversity and redundancy prevention
"""

import math
import random
from typing import List, Dict, Any, Set, Tuple, Optional
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)

class EnhancedQuestionSelector:
    """Enhanced question selection with optimization and diversity"""
    
    def __init__(self, songs: List[Dict[str, Any]]):
        self.songs = songs
        self.feature_history = defaultdict(int)
        self.question_effectiveness = defaultdict(list)
        
        # Feature importance weights
        self.feature_weights = {
            # High-value distinguishing features
            'genres': 1.0,
            'artists': 0.8,
            'decade': 0.9,
            'era': 0.8,
            'is_collaboration': 0.7,
            'is_soundtrack': 0.9,
            'is_viral_hit': 0.9,
            'country': 0.6,
            
            # Musical characteristics
            'duration_category': 0.7,
            'bpm_category': 0.6,
            'themes': 0.8,
            'instruments': 0.7,
            
            # Lower priority
            'language': 0.5,
            'labels': 0.6,
            'producers': 0.5,
        }
        
        # Redundancy prevention rules
        self.redundancy_rules = {
            'decade': ['era', 'release_year'],
            'era': ['decade', 'release_year'],
            'release_year': ['decade', 'era'],
            'genres': ['themes'],  # Genres and themes can be redundant
            'artists': ['artist_genders', 'artist_types'],
        }
    
    def select_best_question(self, candidates: List[Dict[str, Any]], 
                        asked_questions: Set[Tuple[str, str]],
                        hybrid_engine=None) -> Optional[Dict[str, Any]]:
        """Select the best question using enhanced scoring"""
        if not candidates or len(candidates) <= 1:
            return None
        
        # Generate all possible questions
        all_questions = self._generate_all_questions(candidates)
        
        # Filter out asked and redundant questions
        available_questions = self._filter_questions(all_questions, asked_questions, candidates)
        
        if not available_questions:
            return None
        
        # Score each question
        scored_questions = []
        for question in available_questions:
            score = self._score_question(question, candidates, asked_questions, hybrid_engine)
            question['score'] = score
            question['debug_info'] = self._get_debug_info(question, candidates)
            scored_questions.append(question)
        
        # Sort by score and return best
        scored_questions.sort(key=lambda q: q['score'], reverse=True)
        best_question = scored_questions[0]
        
        # Log selection details
        self._log_question_selection(best_question, candidates, asked_questions)
        
        return best_question
    
    def _generate_all_questions(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate all possible questions from candidates"""
        questions = []
        attribute_values = defaultdict(set)
        
        # Collect all attribute values from candidates
        for song in candidates:
            attributes = self._extract_song_attributes(song)
            for attr, values in attributes.items():
                attribute_values[attr].update(values)
        
        # Generate questions for each attribute
        for attribute, values in attribute_values.items():
            for value in values:
                if self._is_valid_question(attribute, value, candidates):
                    question = {
                        'feature': attribute,
                        'value': value,
                        'text': self._generate_question_text(attribute, value),
                        'source': 'enhanced_selector'
                    }
                    questions.append(question)
        
        return questions
    
    def _filter_questions(self, questions: List[Dict[str, Any]], 
                        asked_questions: Set[Tuple[str, str]], 
                        candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out asked and redundant questions"""
        filtered = []
        asked_features = {f for f, _ in asked_questions}
        
        for question in questions:
            feature = question['feature']
            value = question['value']
            
            # Skip if already asked
            if (feature, value) in asked_questions:
                continue
            
            # Skip if redundant with asked questions
            if self._is_redundant(feature, asked_features):
                continue
            
            # Skip if too specific (covers too few songs)
            if not self._has_sufficient_coverage(question, candidates):
                continue
            
            filtered.append(question)
        
        return filtered
    
    def _is_redundant(self, feature: str, asked_features: Set[str]) -> bool:
        """Check if question is redundant with already asked features"""
        redundant_features = self.redundancy_rules.get(feature, [])
        return any(redundant in asked_features for redundant in redundant_features)
    
    def _has_sufficient_coverage(self, question: Dict[str, Any], 
                             candidates: List[Dict[str, Any]]) -> bool:
        """Check if question covers sufficient candidates"""
        feature = question['feature']
        value = question['value']
        
        matches = sum(1 for song in candidates 
                     if self._song_matches_attribute(song, feature, value))
        total = len(candidates)
        
        # Minimum coverage requirements by feature type
        min_coverage = {
            'genres': 2,
            'artists': 2,
            'decade': 3,
            'era': 3,
            'country': 2,
            'is_collaboration': 1,
            'is_soundtrack': 1,
            'is_viral_hit': 1,
        }
        
        required_coverage = min_coverage.get(feature, 2)
        return matches >= required_coverage
    
    def _score_question(self, question: Dict[str, Any], 
                      candidates: List[Dict[str, Any]], 
                      asked_questions: Set[Tuple[str, str]],
                      hybrid_engine=None) -> float:
        """Score question using multiple factors"""
        feature = question['feature']
        value = question['value']
        
        # 1. Information gain (most important)
        info_gain = self._calculate_information_gain(feature, value, candidates)
        
        # 2. Candidate reduction (split quality)
        split_score = self._calculate_split_score(feature, value, candidates)
        
        # 3. Feature importance
        feature_weight = self.feature_weights.get(feature, 0.5)
        
        # 4. Diversity bonus (encourage different features)
        diversity_bonus = self._calculate_diversity_bonus(feature, asked_questions)
        
        # 5. Historical effectiveness (if available)
        effectiveness_bonus = self._get_effectiveness_bonus(feature, value)
        
        # 6. Hybrid engine integration (if available)
        hybrid_bonus = 0.0
        if hybrid_engine and hasattr(hybrid_engine, '_get_hybrid_debug_info'):
            try:
                hybrid_debug = hybrid_engine._get_hybrid_debug_info(question, candidates)
                hybrid_bonus = hybrid_debug.get('hybrid_score', 0) * 0.1
            except:
                pass
        
        # Combine scores
        total_score = (
            info_gain * 0.35 +
            split_score * 0.25 +
            feature_weight * 0.15 +
            diversity_bonus * 0.1 +
            effectiveness_bonus * 0.1 +
            hybrid_bonus * 0.05
        )
        
        return total_score
    
    def _calculate_information_gain(self, feature: str, value: str, 
                                candidates: List[Dict[str, Any]]) -> float:
        """Calculate information gain for question"""
        matches = [s for s in candidates if self._song_matches_attribute(s, feature, value)]
        non_matches = [s for s in candidates if not self._song_matches_attribute(s, feature, value)]
        
        if not matches or not non_matches:
            return 0.0
        
        total = len(candidates)
        entropy_before = self._entropy([total])
        entropy_after = (
            (len(matches) / total) * self._entropy([len(matches)]) +
            (len(non_matches) / total) * self._entropy([len(non_matches)])
        )
        
        return entropy_before - entropy_after
    
    def _calculate_split_score(self, feature: str, value: str, 
                           candidates: List[Dict[str, Any]]) -> float:
        """Calculate how well the question splits candidates"""
        matches = sum(1 for s in candidates if self._song_matches_attribute(s, feature, value))
        total = len(candidates)
        
        if total == 0:
            return 0.0
        
        split_ratio = matches / total
        
        # Ideal split is close to 0.5
        # Use quadratic penalty for deviation from 0.5
        ideal_split = 0.5
        deviation = abs(split_ratio - ideal_split)
        split_score = 1.0 - (deviation ** 2)
        
        return split_score
    
    def _calculate_diversity_bonus(self, feature: str, asked_questions: Set[Tuple[str, str]]) -> float:
        """Calculate diversity bonus for feature"""
        asked_features = [f for f, _ in asked_questions]
        feature_count = asked_features.count(feature)
        
        # Exponential decay for repeated features
        if feature_count == 0:
            return 0.2
        elif feature_count == 1:
            return 0.1
        elif feature_count == 2:
            return 0.05
        else:
            return 0.0
    
    def _get_effectiveness_bonus(self, feature: str, value: str) -> float:
        """Get historical effectiveness bonus for feature-value pair"""
        key = f"{feature}_{value}"
        effectiveness_history = self.question_effectiveness.get(key, [])
        
        if not effectiveness_history:
            return 0.0
        
        # Calculate average effectiveness (1.0 = perfect, 0.0 = useless)
        avg_effectiveness = sum(effectiveness_history) / len(effectiveness_history)
        
        # Bonus up to 0.1 for highly effective questions
        return min(avg_effectiveness * 0.1, 0.1)
    
    def _get_debug_info(self, question: Dict[str, Any], 
                      candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get comprehensive debug information for question"""
        feature = question['feature']
        value = question['value']
        
        matches = sum(1 for s in candidates if self._song_matches_attribute(s, feature, value))
        total = len(candidates)
        
        info_gain = self._calculate_information_gain(feature, value, candidates)
        split_score = self._calculate_split_score(feature, value, candidates)
        
        return {
            'feature': feature,
            'value': value,
            'matches': matches,
            'total': total,
            'split_ratio': matches / total,
            'information_gain': info_gain,
            'split_score': split_score,
            'feature_weight': self.feature_weights.get(feature, 0.5),
            'entropy': self._entropy([matches, total - matches])
        }
    
    def _log_question_selection(self, question: Dict[str, Any], 
                             candidates: List[Dict[str, Any]], 
                             asked_questions: Set[Tuple[str, str]]):
        """Log detailed information about question selection"""
        debug_info = question.get('debug_info', {})
        
        logger.info("🎯 Enhanced Question Selected:")
        logger.info(f"   Question: {question.get('text', 'Unknown')}")
        logger.info(f"   Feature: {debug_info.get('feature', 'Unknown')}")
        logger.info(f"   Value: {debug_info.get('value', 'Unknown')}")
        logger.info(f"   Score: {question.get('score', 0):.3f}")
        logger.info(f"   Covers: {debug_info.get('matches', 0)}/{debug_info.get('total', 0)} songs")
        logger.info(f"   Split Ratio: {debug_info.get('split_ratio', 0):.2f}")
        logger.info(f"   Information Gain: {debug_info.get('information_gain', 0):.3f}")
        logger.info(f"   Feature Weight: {debug_info.get('feature_weight', 0):.2f}")
        logger.info(f"   Previously Asked: {len(asked_questions)} questions")
    
    def record_question_effectiveness(self, question: Dict[str, Any], effectiveness: float):
        """Record how effective a question was"""
        feature = question['feature']
        value = question['value']
        key = f"{feature}_{value}"
        
        # Update effectiveness history
        self.question_effectiveness[key].append(effectiveness)
        
        # Keep only recent history (last 10 instances)
        if len(self.question_effectiveness[key]) > 10:
            self.question_effectiveness[key] = self.question_effectiveness[key][-10:]
        
        # Update feature usage count
        self.feature_history[feature] += 1
        
        logger.debug(f"Recorded effectiveness for {key}: {effectiveness:.2f}")
    
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
        
        # Categorical attributes
        cat_attrs = ['duration_category', 'bpm_category', 'themes', 'instruments']
        for attr in cat_attrs:
            if attr in song:
                values = song.get(attr, [])
                if isinstance(values, list):
                    attributes[attr] = values
                else:
                    attributes[attr] = [str(values)]
        
        return attributes
    
    def _song_matches_attribute(self, song: Dict[str, Any], attribute: str, value: str) -> bool:
        """Check if song matches attribute value"""
        song_attributes = self._extract_song_attributes(song)
        
        if attribute not in song_attributes:
            return False
        
        return value in song_attributes[attribute]
    
    def _generate_question_text(self, attribute: str, value: str) -> str:
        """Generate natural language question text"""
        # Enhanced question templates with variations
        templates = {
            'genres': [
                f"Is it a {value} song?",
                f"Would you classify it as {value}?",
                f"Does it have {value} elements?"
            ],
            'artists': [
                f"Is it by {value}?",
                f"Was {value} the artist?",
                f"Is {value} one of the performers?"
            ],
            'decade': [
                f"Was it released in the {value}?",
                f"Is it from the {value} era?",
                f"Did it come out in the {value}?"
            ],
            'era': [
                f"Is it from the {value}?",
                f"Would you say it's {value} music?",
                f"Does it represent the {value}?"
            ],
            'is_collaboration': [
                f"Is it a collaboration song?",
                f"Does it feature multiple artists?",
                f"Is it by more than one artist?"
            ],
            'is_soundtrack': [
                f"Is it from a soundtrack?",
                f"Was it made for a movie/TV show?",
                f"Is it part of a soundtrack?"
            ],
            'is_viral_hit': [
                f"Is it a viral hit song?",
                f"Did it go viral?",
                f"Is it a massively popular song?"
            ],
            'country': [
                f"Is it from {value}?",
                f"Was it released in {value}?",
                f"Is {value} the country of origin?"
            ],
            'duration_category': [
                f"Is it a {value.lower()} song?",
                f"Would you say it's {value.lower()} in length?",
                f"Does it run for {value.lower()} duration?"
            ],
            'bpm_category': [
                f"Does it have {value.lower()} tempo?",
                f"Is the tempo {value.lower()}?",
                f"Would you describe its beat as {value.lower()}?"
            ],
            'themes': [
                f"Is it about {value}?",
                f"Does it explore themes of {value}?",
                f"Are the lyrics about {value}?"
            ],
            'instruments': [
                f"Does it feature {value}?",
                f"Is {value} used in the song?",
                f"Can you hear {value} in it?"
            ]
        }
        
        # Get template for attribute or use default
        attribute_templates = templates.get(attribute, [f"Is it connected with {value}?"])
        return random.choice(attribute_templates)
    
    def _is_valid_question(self, attribute: str, value: str, 
                         candidates: List[Dict[str, Any]]) -> bool:
        """Check if question is valid and useful"""
        # Skip empty values
        if not value or str(value).strip() == "":
            return False
        
        # Skip attributes that are too specific
        if attribute in ['artists', 'producers', 'composers']:
            # Only include if multiple songs share this value
            matches = sum(1 for s in candidates 
                        if self._song_matches_attribute(s, attribute, value))
            return matches >= 2
        
        return True
    
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
    
    def get_selection_statistics(self) -> Dict[str, Any]:
        """Get statistics about question selection"""
        return {
            'feature_usage': dict(self.feature_history),
            'question_effectiveness': dict(self.question_effectiveness),
            'total_features_tracked': len(self.feature_history),
            'total_effectiveness_entries': sum(len(history) for history in self.question_effectiveness.values())
        }


def create_enhanced_question_selector(songs: List[Dict[str, Any]]) -> EnhancedQuestionSelector:
    """Factory function to create enhanced question selector"""
    return EnhancedQuestionSelector(songs)
