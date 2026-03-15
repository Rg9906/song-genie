"""
Human Relevance Validator
Uses AI to validate if questions are human-relevant (not too technical)
"""

import json
import random
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class HumanRelevanceValidator:
    """Validates if questions are relevant to normal humans"""
    
    def __init__(self, use_ai: bool = True):
        self.use_ai = use_ai
        self.human_relevant_keywords = self._load_human_relevant_keywords()
        self.technical_keywords = self._load_technical_keywords()
        
    def _load_human_relevant_keywords(self) -> set:
        """Keywords that indicate human-relevant questions"""
        return {
            # Music experience
            'feel', 'sound', 'vibe', 'energy', 'mood', 'emotion', 'feeling',
            'dance', 'party', 'chill', 'relax', 'workout', 'study', 'sleep',
            'happy', 'sad', 'energetic', 'calm', 'intense', 'upbeat', 'mellow',
            
            # General music knowledge
            'popular', 'famous', 'well-known', 'hit', 'classic', 'modern',
            'old', 'new', 'recent', 'vintage', 'timeless', 'trending',
            
            # Artist/genre
            'artist', 'singer', 'band', 'group', 'genre', 'style', 'type',
            'music', 'song', 'track', 'album', 'record', 'release',
            
            # Time/place
            'year', 'decade', 'era', 'period', 'time', 'when', 'where',
            'country', 'origin', 'from', 'made', 'created', 'released',
            
            # General characteristics
            'fast', 'slow', 'long', 'short', 'loud', 'quiet', 'soft', 'hard',
            'simple', 'complex', 'catchy', 'memorable', 'boring', 'exciting',
            
            # Common musical elements
            'beat', 'rhythm', 'melody', 'harmony', 'vocals', 'singing',
            'words', 'lyrics', 'theme', 'story', 'meaning', 'message'
        }
    
    def _load_technical_keywords(self) -> set:
        """Keywords that indicate technical questions (avoid these)"""
        return {
            # Technical music terms
            'bpm', 'tempo', 'key', 'scale', 'chord', 'progression',
            'synthesizer', 'oscillator', 'filter', 'envelope', 'lfo',
            'compression', 'reverb', 'delay', 'eq', 'mixing', 'mastering',
            'frequency', 'hertz', 'decibel', 'waveform', 'bitrate',
            
            # Production terms
            'producer', 'engineer', 'studio', 'equipment', 'gear',
            'analog', 'digital', 'midi', 'daw', 'plugin', 'sample',
            
            # Complex theory
            'polyrhythm', 'syncopation', 'modulation', 'tonic', 'dominant',
            'subdominant', 'cadence', 'counterpoint', 'fugue', 'sonata',
            
            # Obscure instruments
            'oboe', 'bassoon', 'trombone', 'tuba', 'harpsichord',
            'theremin', 'sitar', 'didgeridoo', 'bagpipes', 'accordion'
        }
    
    def validate_question_relevance(self, question: Dict[str, Any]) -> Tuple[bool, float, str]:
        """
        Validate if a question is human-relevant
        Returns: (is_relevant, confidence_score, reason)
        """
        question_text = question.get('text', '').lower()
        feature = question.get('feature', '').lower()
        value = question.get('value', '').lower()
        
        # Check for technical keywords
        technical_score = self._calculate_technical_score(question_text, feature, value)
        
        # Check for human-relevant keywords
        relevance_score = self._calculate_relevance_score(question_text, feature, value)
        
        # Check question complexity
        complexity_score = self._calculate_complexity_score(question_text)
        
        # Calculate overall confidence
        overall_score = (relevance_score - technical_score - complexity_score) / 3
        overall_score = max(0, min(1, overall_score))  # Normalize to 0-1
        
        # Determine if relevant
        is_relevant = overall_score >= 0.3  # Threshold for relevance
        
        # Generate reason
        if technical_score > 0.5:
            reason = "Too technical for normal listeners"
        elif relevance_score < 0.3:
            reason = "Not relevant to typical music experience"
        elif complexity_score > 0.6:
            reason = "Too complex for casual listeners"
        else:
            reason = "Human-relevant question"
        
        return is_relevant, overall_score, reason
    
    def _calculate_technical_score(self, text: str, feature: str, value: str) -> float:
        """Calculate how technical the question is"""
        technical_count = 0
        total_words = len(text.split()) + len(feature.split()) + len(value.split())
        
        if total_words == 0:
            return 0
        
        # Count technical keywords
        all_text = f"{text} {feature} {value}"
        for keyword in self.technical_keywords:
            if keyword in all_text:
                technical_count += 1
        
        return technical_count / total_words
    
    def _calculate_relevance_score(self, text: str, feature: str, value: str) -> float:
        """Calculate how human-relevant the question is"""
        relevant_count = 0
        total_words = len(text.split()) + len(feature.split()) + len(value.split())
        
        if total_words == 0:
            return 0
        
        # Count relevant keywords
        all_text = f"{text} {feature} {value}"
        for keyword in self.human_relevant_keywords:
            if keyword in all_text:
                relevant_count += 1
        
        return relevant_count / total_words
    
    def _calculate_complexity_score(self, text: str) -> float:
        """Calculate how complex the question is"""
        # Factors that increase complexity
        complexity_factors = 0
        
        # Long questions are more complex
        if len(text.split()) > 15:
            complexity_factors += 0.3
        
        # Questions with multiple clauses
        if ',' in text and text.count(',') > 1:
            complexity_factors += 0.2
        
        # Questions with specific numbers/dates
        import re
        if re.search(r'\b\d{4}\b', text):  # Years
            complexity_factors += 0.1
        if re.search(r'\b\d+\s*(bpm|hz|khz)\b', text):  # Technical measurements
            complexity_factors += 0.3
        
        # Questions with obscure terms
        obscure_words = ['oscillator', 'envelope', 'modulation', 'frequency']
        for word in obscure_words:
            if word in text.lower():
                complexity_factors += 0.2
        
        return min(complexity_factors, 1.0)
    
    def filter_relevant_questions(self, questions: List[Dict[str, Any]], 
                                 min_confidence: float = 0.3) -> List[Dict[str, Any]]:
        """Filter out questions that aren't human-relevant"""
        relevant_questions = []
        
        for question in questions:
            is_relevant, confidence, reason = self.validate_question_relevance(question)
            
            if is_relevant and confidence >= min_confidence:
                question['relevance_confidence'] = confidence
                question['relevance_reason'] = reason
                relevant_questions.append(question)
            else:
                logger.debug(f"Filtered out question: {question['text']} - {reason}")
        
        return relevant_questions
    
    def improve_question_text(self, question: Dict[str, Any]) -> str:
        """Improve question text to be more human-relevant"""
        original_text = question.get('text', '')
        feature = question.get('feature', '')
        value = question.get('value', '')
        
        # If question is already good, return as-is
        is_relevant, confidence, reason = self.validate_question_relevance(question)
        if is_relevant and confidence >= 0.7:
            return original_text
        
        # Try to improve the question
        improved_text = self._make_more_human_friendly(original_text, feature, value)
        
        return improved_text
    
    def _make_more_human_friendly(self, text: str, feature: str, value: str) -> str:
        """Make question more human-friendly"""
        # Convert technical terms to everyday language
        replacements = {
            'bpm': 'tempo',
            'tempo': 'speed',
            'duration': 'length',
            'instruments': 'sound',
            'themes': 'about',
            'publication_date': 'when it came out',
            'release_year': 'what year it came out'
        }
        
        improved_text = text
        for technical, friendly in replacements.items():
            improved_text = improved_text.replace(technical, friendly)
        
        # Add conversational prefixes
        prefixes = [
            "Would you say this ",
            "Does this sound like ",
            "Is this more of a ",
            "Would you describe this as "
        ]
        
        # If question doesn't start with a question word, add a prefix
        if not any(improved_text.strip().startswith(word) for word in ['Is', 'Does', 'Would', 'Can', 'Has', 'Are']):
            prefix = random.choice(prefixes)
            improved_text = prefix + improved_text.lower()
        
        # Ensure it ends with a question mark
        if not improved_text.endswith('?'):
            improved_text += '?'
        
        return improved_text
    
    def get_relevance_statistics(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about question relevance"""
        total = len(questions)
        relevant_count = 0
        confidence_scores = []
        
        for question in questions:
            is_relevant, confidence, reason = self.validate_question_relevance(question)
            if is_relevant:
                relevant_count += 1
            confidence_scores.append(confidence)
        
        return {
            'total_questions': total,
            'relevant_questions': relevant_count,
            'relevance_rate': relevant_count / total if total > 0 else 0,
            'average_confidence': sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0,
            'high_confidence_rate': sum(1 for c in confidence_scores if c >= 0.7) / len(confidence_scores) if confidence_scores else 0
        }
