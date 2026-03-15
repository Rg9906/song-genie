"""
Dynamic AI Question Engine
Fully dynamic question generation using AI APIs and pattern discovery
No static categories - everything discovered and generated dynamically
"""

import json
import random
import requests
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict, Counter
import logging
import re

logger = logging.getLogger(__name__)

class DynamicAIQuestionEngine:
    """Fully dynamic AI-powered question generation"""
    
    def __init__(self, songs: List[Dict[str, Any]], use_ai: bool = True):
        self.songs = songs
        self.use_ai = use_ai
        self.discovered_patterns = {}
        self.question_history = []
        
        # Discover patterns dynamically
        self._discover_song_patterns()
        
    def _discover_song_patterns(self):
        """Dynamically discover patterns in the song data"""
        logger.info("🔍 Discovering dynamic song patterns...")
        
        # Collect all attributes and their values
        attribute_analysis = defaultdict(lambda: {
            'values': set(),
            'types': set(),
            'patterns': [],
            'relationships': []
        })
        
        for song in self.songs:
            for attr, value in song.items():
                if attr == 'id' or attr == 'title':
                    continue
                
                analysis = attribute_analysis[attr]
                
                # Analyze value types
                if isinstance(value, list):
                    analysis['types'].add('list')
                    analysis['values'].update([str(v) for v in value if v])
                elif isinstance(value, (int, float)):
                    analysis['types'].add('numeric')
                    analysis['values'].add(str(value))
                elif isinstance(value, str):
                    analysis['types'].add('string')
                    if value:
                        analysis['values'].add(value)
                elif value is not None:
                    analysis['types'].add('other')
                    analysis['values'].add(str(value))
        
        # Discover patterns for each attribute
        for attr, analysis in attribute_analysis.items():
            patterns = self._analyze_attribute_patterns(attr, analysis)
            analysis['patterns'] = patterns
            
            # Discover relationships between attributes
            relationships = self._discover_attribute_relationships(attr)
            analysis['relationships'] = relationships
        
        self.discovered_patterns = dict(attribute_analysis)
        
        logger.info(f"✅ Discovered patterns for {len(self.discovered_patterns)} attributes")
    
    def _analyze_attribute_patterns(self, attr: str, analysis: Dict) -> List[Dict]:
        """Dynamically analyze patterns in an attribute"""
        patterns = []
        values = list(analysis['values'])
        
        if not values:
            return patterns
        
        # Numeric patterns
        if 'numeric' in analysis['types']:
            numeric_values = [float(v) for v in values if self._is_numeric(v)]
            if numeric_values:
                patterns.extend(self._discover_numeric_patterns(attr, numeric_values))
        
        # String patterns
        if 'string' in analysis['types'] or 'list' in analysis['types']:
            string_values = [v for v in values if isinstance(v, str)]
            if string_values:
                patterns.extend(self._discover_string_patterns(attr, string_values))
        
        # List patterns
        if 'list' in analysis['types']:
            patterns.extend(self._discover_list_patterns(attr, values))
        
        return patterns
    
    def _discover_numeric_patterns(self, attr: str, values: List[float]) -> List[Dict]:
        """Discover patterns in numeric attributes"""
        patterns = []
        
        if len(values) < 2:
            return patterns
        
        # Range patterns
        min_val, max_val = min(values), max(values)
        
        # Quartiles
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        q1 = sorted_vals[n // 4]
        median = sorted_vals[n // 2]
        q3 = sorted_vals[3 * n // 4]
        
        patterns.append({
            'type': 'range_quartile',
            'attribute': attr,
            'ranges': [
                (min_val, q1, f"low {attr}"),
                (q1, median, f"medium-low {attr}"),
                (median, q3, f"medium-high {attr}"),
                (q3, max_val, f"high {attr}")
            ]
        })
        
        # Outlier detection
        mean_val = sum(values) / len(values)
        std_dev = (sum((x - mean_val) ** 2 for x in values) / len(values)) ** 0.5
        
        outliers = [v for v in values if abs(v - mean_val) > 2 * std_dev]
        if outliers:
            patterns.append({
                'type': 'outliers',
                'attribute': attr,
                'outlier_values': outliers,
                'description': f"unusual {attr} values"
            })
        
        return patterns
    
    def _discover_string_patterns(self, attr: str, values: List[str]) -> List[Dict]:
        """Discover patterns in string attributes"""
        patterns = []
        
        if not values:
            return patterns
        
        # Length patterns
        lengths = [len(v) for v in values if v]
        if lengths:
            avg_length = sum(lengths) / len(lengths)
            patterns.append({
                'type': 'length_analysis',
                'attribute': attr,
                'average_length': avg_length,
                'short_values': [v for v in values if len(v) < avg_length * 0.5],
                'long_values': [v for v in values if len(v) > avg_length * 1.5]
            })
        
        # Word patterns
        all_words = []
        for value in values:
            if value:
                words = re.findall(r'\b\w+\b', value.lower())
                all_words.extend(words)
        
        if all_words:
            word_freq = Counter(all_words)
            common_words = [word for word, freq in word_freq.most_common(10)]
            patterns.append({
                'type': 'word_frequency',
                'attribute': attr,
                'common_words': common_words,
                'word_patterns': word_freq
            })
        
        # Category patterns (for things like genres)
        unique_values = set(values)
        if len(unique_values) > 5:  # Likely categorical
            patterns.append({
                'type': 'categorical',
                'attribute': attr,
                'categories': list(unique_values),
                'diversity_score': len(unique_values) / len(values)
            })
        
        return patterns
    
    def _discover_list_patterns(self, attr: str, values: List[str]) -> List[Dict]:
        """Discover patterns in list attributes"""
        patterns = []
        
        # List length patterns
        list_lengths = []
        for song in self.songs:
            song_value = song.get(attr, [])
            if isinstance(song_value, list):
                list_lengths.append(len(song_value))
        
        if list_lengths:
            avg_length = sum(list_lengths) / len(list_lengths)
            patterns.append({
                'type': 'list_length',
                'attribute': attr,
                'average_items': avg_length,
                'single_items': [song for song in self.songs 
                               if isinstance(song.get(attr, []), list) and len(song[attr]) == 1],
                'many_items': [song for song in self.songs 
                              if isinstance(song.get(attr, []), list) and len(song[attr]) > 3]
            })
        
        return patterns
    
    def _discover_attribute_relationships(self, attr: str) -> List[Dict]:
        """Discover relationships between attributes"""
        relationships = []
        
        # Correlation with other attributes
        for other_attr in self.discovered_patterns.keys():
            if other_attr == attr:
                continue
            
            correlation = self._calculate_attribute_correlation(attr, other_attr)
            if correlation:
                relationships.append({
                    'attribute': other_attr,
                    'correlation': correlation,
                    'type': 'statistical'
                })
        
        return relationships
    
    def _calculate_attribute_correlation(self, attr1: str, attr2: str) -> Optional[Dict]:
        """Calculate correlation between two attributes"""
        # Simplified correlation analysis
        attr1_values = defaultdict(list)
        attr2_values = defaultdict(list)
        
        for song in self.songs:
            val1 = song.get(attr1)
            val2 = song.get(attr2)
            
            if val1 is not None and val2 is not None:
                if isinstance(val1, list):
                    for v1 in val1:
                        attr1_values[str(v1)].append(song)
                else:
                    attr1_values[str(val1)].append(song)
                
                if isinstance(val2, list):
                    for v2 in val2:
                        attr2_values[str(v2)].append(song)
                else:
                    attr2_values[str(val2)].append(song)
        
        # Check for co-occurrence patterns
        co_occurrences = {}
        for v1, songs1 in attr1_values.items():
            for v2, songs2 in attr2_values.items():
                overlap = len(set(songs1) & set(songs2))
                if overlap > 0:
                    co_occurrences[f"{v1} + {v2}"] = overlap
        
        if co_occurrences:
            return {
                'co_occurrences': co_occurrences,
                'strength': max(co_occurrences.values()) / len(self.songs)
            }
        
        return None
    
    def generate_dynamic_questions(self, asked_questions: Set[Tuple[str, str]], 
                                 max_questions: int = 10) -> List[Dict[str, Any]]:
        """Generate completely dynamic questions"""
        questions = []
        
        # Generate questions from discovered patterns
        for attr, analysis in self.discovered_patterns.items():
            pattern_questions = self._generate_pattern_questions(attr, analysis, asked_questions)
            questions.extend(pattern_questions)
        
        # Generate AI-powered questions if enabled
        if self.use_ai:
            ai_questions = self._generate_ai_questions(asked_questions)
            questions.extend(ai_questions)
        
        # Generate relationship-based questions
        relationship_questions = self._generate_relationship_questions(asked_questions)
        questions.extend(relationship_questions)
        
        # Remove duplicates and already asked questions
        unique_questions = []
        seen = set()
        
        for q in questions:
            key = (q['feature'], q['value'])
            if key not in seen and key not in asked_questions:
                seen.add(key)
                unique_questions.append(q)
        
        # Return diverse selection
        if len(unique_questions) > max_questions:
            # Ensure diversity by sampling different attribute types
            selected = []
            used_attrs = set()
            
            # First, pick one from each attribute type
            for q in unique_questions:
                if q['feature'] not in used_attrs and len(selected) < max_questions:
                    selected.append(q)
                    used_attrs.add(q['feature'])
            
            # Fill remaining slots
            remaining = [q for q in unique_questions if q['feature'] not in used_attrs]
            if len(selected) < max_questions and remaining:
                additional = random.sample(
                    remaining, 
                    min(max_questions - len(selected), len(remaining))
                )
                selected.extend(additional)
            
            return selected
        
        return unique_questions
    
    def _generate_pattern_questions(self, attr: str, analysis: Dict, 
                                   asked_questions: Set[Tuple[str, str]]) -> List[Dict[str, Any]]:
        """Generate questions from discovered patterns"""
        questions = []
        
        for pattern in analysis['patterns']:
            if pattern['type'] == 'range_quartile':
                questions.extend(self._generate_range_questions(attr, pattern))
            elif pattern['type'] == 'outliers':
                questions.extend(self._generate_outlier_questions(attr, pattern))
            elif pattern['type'] == 'categorical':
                questions.extend(self._generate_categorical_questions(attr, pattern))
            elif pattern['type'] == 'word_frequency':
                questions.extend(self._generate_word_based_questions(attr, pattern))
            elif pattern['type'] == 'length_analysis':
                questions.extend(self._generate_length_questions(attr, pattern))
        
        return questions
    
    def _generate_range_questions(self, attr: str, pattern: Dict) -> List[Dict[str, Any]]:
        """Generate questions from numeric range patterns"""
        questions = []
        
        for min_val, max_val, label in pattern['ranges']:
            questions.append({
                'feature': f"{attr}_range",
                'value': label,
                'text': f"Does this have {label}?",
                'pattern_type': 'range',
                'min_value': min_val,
                'max_value': max_val
            })
        
        return questions
    
    def _generate_outlier_questions(self, attr: str, pattern: Dict) -> List[Dict[str, Any]]:
        """Generate questions about outlier values"""
        questions = []
        
        for outlier in pattern['outlier_values'][:3]:  # Limit to 3 outliers
            questions.append({
                'feature': f"{attr}_outlier",
                'value': str(outlier),
                'text': f"Is this unusually {attr}?",
                'pattern_type': 'outlier',
                'outlier_value': outlier
            })
        
        return questions
    
    def _generate_categorical_questions(self, attr: str, pattern: Dict) -> List[Dict[str, Any]]:
        """Generate questions from categorical patterns"""
        questions = []
        
        # Select diverse categories based on frequency
        categories = pattern['categories'][:10]  # Limit to 10
        
        for category in categories:
            questions.append({
                'feature': attr,
                'value': category,
                'text': f"Is this connected with {category}?",
                'pattern_type': 'categorical'
            })
        
        return questions
    
    def _generate_word_based_questions(self, attr: str, pattern: Dict) -> List[Dict[str, Any]]:
        """Generate questions based on word patterns"""
        questions = []
        
        for word in pattern['common_words'][:5]:  # Top 5 words
            questions.append({
                'feature': f"{attr}_word",
                'value': word,
                'text': f"Does this mention {word}?",
                'pattern_type': 'word_based'
            })
        
        return questions
    
    def _generate_length_questions(self, attr: str, pattern: Dict) -> List[Dict[str, Any]]:
        """Generate questions based on length patterns"""
        questions = []
        
        if pattern['short_values']:
            questions.append({
                'feature': f"{attr}_length",
                'value': 'short',
                'text': f"Is this notably brief?",
                'pattern_type': 'length'
            })
        
        if pattern['long_values']:
            questions.append({
                'feature': f"{attr}_length",
                'value': 'long',
                'text': f"Is this particularly extensive?",
                'pattern_type': 'length'
            })
        
        return questions
    
    def _generate_ai_questions(self, asked_questions: Set[Tuple[str, str]]) -> List[Dict[str, Any]]:
        """Generate AI-powered questions using free APIs"""
        questions = []
        
        if not self.use_ai:
            return questions
        
        try:
            # Use a free text generation API
            questions.extend(self._call_free_ai_api(asked_questions))
        except Exception as e:
            logger.warning(f"AI question generation failed: {e}")
        
        return questions
    
    def _call_free_ai_api(self, asked_questions: Set[Tuple[str, str]]) -> List[Dict[str, Any]]:
        """Call free AI API for question generation"""
        questions = []
        
        # Example using a hypothetical free API
        # You could replace this with actual APIs like:
        # - Groq (free tier)
        # - Hugging Face Inference API
        # - OpenRouter (free models)
        
        # For now, generate some creative questions based on patterns
        sample_songs = random.sample(self.songs, min(5, len(self.songs)))
        
        for song in sample_songs:
            # Generate creative questions about song attributes
            for attr, value in song.items():
                if attr in ['id', 'title']:
                    continue
                
                if value and isinstance(value, str):
                    questions.append({
                        'feature': f"ai_generated_{attr}",
                        'value': value,
                        'text': f"Would you say this has a unique {attr} signature?",
                        'pattern_type': 'ai_generated'
                    })
        
        return questions[:5]  # Limit AI questions
    
    def _generate_relationship_questions(self, asked_questions: Set[Tuple[str, str]]) -> List[Dict[str, Any]]:
        """Generate questions based on attribute relationships"""
        questions = []
        
        for attr, analysis in self.discovered_patterns.items():
            for relationship in analysis['relationships']:
                other_attr = relationship['attribute']
                
                # Generate questions about the relationship
                questions.append({
                    'feature': f"{attr}_{other_attr}_relation",
                    'value': "correlated",
                    'text': f"Is there a connection between {attr} and {other_attr}?",
                    'pattern_type': 'relationship'
                })
        
        return questions
    
    def _is_numeric(self, value: str) -> bool:
        """Check if a string represents a number"""
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def get_dynamic_statistics(self) -> Dict[str, Any]:
        """Get statistics about the dynamic patterns discovered"""
        stats = {
            'total_attributes': len(self.discovered_patterns),
            'pattern_types': defaultdict(int),
            'attribute_diversity': {},
            'relationship_count': 0
        }
        
        for attr, analysis in self.discovered_patterns.items():
            for pattern in analysis['patterns']:
                stats['pattern_types'][pattern['type']] += 1
            
            stats['attribute_diversity'][attr] = len(analysis['values'])
            stats['relationship_count'] += len(analysis['relationships'])
        
        return dict(stats)
