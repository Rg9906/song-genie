"""
Diverse Question Generator with Multiple Categories and Varied Framing
Uses free language models for dynamic question generation
"""

import random
import json
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)

class DiverseQuestionGenerator:
    """Generates diverse questions from multiple song attributes"""
    
    def __init__(self, songs: List[Dict[str, Any]]):
        self.songs = songs
        self.question_templates = self._load_question_templates()
        self.attribute_categories = self._categorize_attributes()
        
    def _load_question_templates(self) -> Dict[str, List[str]]:
        """Load varied question templates for each attribute type"""
        return {
            # Genre questions with varied framing
            'genres': [
                "Is this a {value} track?",
                "Would you classify this as {value} music?",
                "Does this song fall into the {value} category?",
                "Is the {value} genre a good fit for this song?",
                "Would you find this in a {value} playlist?",
                "Could this be considered a {value} anthem?",
                "Is the sound predominantly {value}?"
            ],
            
            # Artist questions with varied framing
            'artists': [
                "Is this performed by {value}?",
                "Did {value} create this track?",
                "Is {value} the artist behind this song?",
                "Would you find this in {value}'s discography?",
                "Is {value} the credited performer?",
                "Did {value} release this as a single?",
                "Is this track associated with {value}?"
            ],
            
            # Era/Decade questions
            'decade': [
                "Was this released in the {value}?",
                "Does this song come from the {value}?",
                "Would you place this track in the {value}?",
                "Is this a {value} production?",
                "Did this emerge during the {value}?",
                "Is this characteristic of {value} music?"
            ],
            
            # Era questions
            'era': [
                "Is this from the {value}?",
                "Does this belong to the {value}?",
                "Would you categorize this as {value} music?",
                "Is this a product of the {value}?"
            ],
            
            # Theme/Mood questions
            'themes': [
                "Is this song about {value}?",
                "Does this explore themes of {value}?",
                "Would you say the lyrics focus on {value}?",
                "Is {value} a central theme here?",
                "Does this track evoke feelings of {value}?",
                "Would you describe this as a {value} anthem?"
            ],
            
            # Instrument questions
            'instruments': [
                "Does this feature {value}?",
                "Would you hear {value} in this track?",
                "Is {value} prominently used?",
                "Could you identify {value} in the arrangement?",
                "Is {value} a key instrument here?",
                "Does the production highlight {value}?"
            ],
            
            # Popularity/YouTube questions
            'billion_views': [
                "Has this song reached billions of views?",
                "Is this a viral hit with massive streaming?",
                "Did this achieve billion-view status?",
                "Is this considered a massive commercial success?",
                "Has this crossed the billion-view mark?"
            ],
            
            # BPM/Tempo questions
            'bpm': [
                "Is this a fast-paced track?",
                "Would you describe this as high-energy?",
                "Does this have an upbeat tempo?",
                "Is this suitable for dancing?",
                "Would you call this an energetic song?",
                "Does this make you want to move?"
            ],
            
            # Duration questions
            'duration': [
                "Is this a lengthy track?",
                "Would you consider this an extended song?",
                "Does this run for several minutes?",
                "Is this a full-length production?",
                "Would you call this an epic track?"
            ],
            
            # Artist gender questions
            'artist_genders': [
                "Is this performed by a {value} artist?",
                "Would you describe the vocalist as {value}?",
                "Is the main performer {value}?",
                "Does this feature {value} vocals?"
            ],
            
            # Artist type questions
            'artist_types': [
                "Is this by a {value}?",
                "Would you classify the performer as {value}?",
                "Is this created by a {value}?",
                "Does this come from a {value}?"
            ],
            
            # Country questions
            'country': [
                "Is this from {value}?",
                "Would you place this origin in {value}?",
                "Did this emerge from {value}?",
                "Is this a {value} production?"
            ],
            
            # Language questions
            'language': [
                "Is this in {value}?",
                "Are the lyrics primarily {value}?",
                "Would you hear {value} vocals?",
                "Is this performed in {value}?"
            ]
        }
    
    def _categorize_attributes(self) -> Dict[str, List[str]]:
        """Categorize attributes by type for better question generation"""
        return {
            'music_style': ['genres', 'instruments', 'bpm'],
            'artist_info': ['artists', 'artist_genders', 'artist_types'],
            'time_period': ['decade', 'era', 'publication_date'],
            'themes_mood': ['themes'],
            'popularity': ['billion_views'],
            'technical': ['duration'],
            'geographic': ['country', 'language']
        }
    
    def generate_diverse_questions(self, max_per_category: int = 3) -> List[Dict[str, Any]]:
        """Generate diverse questions from all available attributes"""
        questions = []
        category_counts = defaultdict(int)
        
        # Collect all possible attribute values
        attribute_values = defaultdict(set)
        
        for song in self.songs:
            for attr, value in song.items():
                if attr in self.question_templates:
                    if isinstance(value, list):
                        attribute_values[attr].update([str(v) for v in value])
                    elif value is not None:
                        attribute_values[attr].add(str(value))
        
        # Generate questions with category limits
        for attr, values in attribute_values.items():
            category = self._get_attribute_category(attr)
            
            for value in values:
                if category_counts[category] >= max_per_category:
                    continue
                
                # Skip empty or invalid values
                if not value or str(value).lower() in ['unknown', 'null', 'none']:
                    continue
                
                # Generate multiple template variations
                templates = self.question_templates.get(attr, ["Is it connected with {value}?"])
                
                for template in templates[:2]:  # Limit to 2 variations per value
                    question_text = template.format(value=value)
                    
                    questions.append({
                        'feature': attr,
                        'value': value,
                        'text': question_text,
                        'category': category
                    })
                
                category_counts[category] += 1
        
        # Add special computed questions
        questions.extend(self._generate_computed_questions())
        
        return questions
    
    def _get_attribute_category(self, attr: str) -> str:
        """Get the category for an attribute"""
        for category, attrs in self.attribute_categories.items():
            if attr in attrs:
                return category
        return 'other'
    
    def _generate_computed_questions(self) -> List[Dict[str, Any]]:
        """Generate questions based on computed attributes"""
        questions = []
        
        # Danceability questions (based on BPM)
        slow_songs = [s for s in self.songs if s.get('bpm', 0) < 100]
        fast_songs = [s for s in self.songs if s.get('bpm', 0) > 120]
        
        if slow_songs and len(slow_songs) < len(self.songs):
            questions.append({
                'feature': 'danceability',
                'value': 'slow',
                'text': random.choice([
                    "Is this more of a slow jam?",
                    "Would this be better for chilling than dancing?",
                    "Is this a laid-back, mellow track?"
                ]),
                'category': 'themes_mood'
            })
        
        if fast_songs and len(fast_songs) < len(self.songs):
            questions.append({
                'feature': 'danceability',
                'value': 'fast',
                'text': random.choice([
                    "Is this a dance floor filler?",
                    "Would this get people moving?",
                    "Is this high-energy and upbeat?"
                ]),
                'category': 'themes_mood'
            })
        
        # Length questions
        short_songs = [s for s in self.songs if s.get('duration', 0) < 180]
        long_songs = [s for s in self.songs if s.get('duration', 0) > 240]
        
        if short_songs and len(short_songs) < len(self.songs):
            questions.append({
                'feature': 'length_type',
                'value': 'short',
                'text': random.choice([
                    "Is this a quick, concise track?",
                    "Would you call this a short song?",
                    "Is this under 3 minutes?"
                ]),
                'category': 'technical'
            })
        
        if long_songs and len(long_songs) < len(self.songs):
            questions.append({
                'feature': 'length_type',
                'value': 'long',
                'text': random.choice([
                    "Is this an extended epic track?",
                    "Would you consider this a lengthy song?",
                    "Is this over 4 minutes?"
                ]),
                'category': 'technical'
            })
        
        return questions
    
    def select_diverse_questions(self, asked_questions: Set[Tuple[str, str]], 
                                num_questions: int = 10) -> List[Dict[str, Any]]:
        """Select diverse questions avoiding repetition"""
        all_questions = self.generate_diverse_questions()
        
        # Filter out already asked questions
        available = [
            q for q in all_questions 
            if (q['feature'], q['value']) not in asked_questions
        ]
        
        if not available:
            return []
        
        # Ensure category diversity
        selected = []
        used_categories = set()
        
        # First, try to get one from each category
        for question in available:
            if question['category'] not in used_categories and len(selected) < num_questions:
                selected.append(question)
                used_categories.add(question['category'])
        
        # Fill remaining slots randomly from available questions
        remaining = [q for q in available if q['category'] not in used_categories]
        if len(selected) < num_questions and remaining:
            additional = random.sample(
                remaining, 
                min(num_questions - len(selected), len(remaining))
            )
            selected.extend(additional)
        
        return selected[:num_questions]
