"""
Simple Dynamic Question Engine
Lightweight dynamic question generation without complex dependencies
"""

import random
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)

class SimpleDynamicEngine:
    """Simple dynamic question generation"""
    
    def __init__(self, songs: List[Dict[str, Any]]):
        self.songs = songs
        self.discovered_attributes = self._discover_attributes()
        
    def _discover_attributes(self) -> Dict[str, Dict]:
        """Discover all attributes and their properties"""
        attributes = {}
        
        for song in self.songs:
            for attr, value in song.items():
                if attr in ['id', 'title']:
                    continue
                
                if attr not in attributes:
                    attributes[attr] = {
                        'values': set(),
                        'types': set(),
                        'count': 0
                    }
                
                attr_info = attributes[attr]
                attr_info['count'] += 1
                
                if isinstance(value, list):
                    attr_info['types'].add('list')
                    attr_info['values'].update([str(v) for v in value if v])
                elif isinstance(value, (int, float)):
                    attr_info['types'].add('numeric')
                    attr_info['values'].add(str(value))
                elif isinstance(value, str):
                    attr_info['types'].add('string')
                    if value:
                        attr_info['values'].add(value)
                elif value is not None:
                    attr_info['types'].add('other')
                    attr_info['values'].add(str(value))
        
        logger.info(f"✅ Discovered {len(attributes)} dynamic attributes")
        return attributes
    
    def generate_dynamic_questions(self, asked_questions: Set[Tuple[str, str]], 
                                 max_questions: int = 10) -> List[Dict[str, Any]]:
        """Generate completely dynamic questions"""
        questions = []
        
        # Generate questions for each discovered attribute
        for attr, info in self.discovered_attributes.items():
            attr_questions = self._generate_attribute_questions(attr, info, asked_questions)
            questions.extend(attr_questions)
        
        # Remove already asked questions
        available_questions = [
            q for q in questions 
            if (q['feature'], q['value']) not in asked_questions
        ]
        
        # Ensure diversity by sampling different attributes
        selected = []
        used_attrs = set()
        
        # First, pick one from each attribute
        for q in available_questions:
            if q['feature'] not in used_attrs and len(selected) < max_questions:
                selected.append(q)
                used_attrs.add(q['feature'])
        
        # Fill remaining slots
        remaining = [q for q in available_questions if q['feature'] not in used_attrs]
        if len(selected) < max_questions and remaining:
            additional = random.sample(
                remaining, 
                min(max_questions - len(selected), len(remaining))
            )
            selected.extend(additional)
        
        return selected[:max_questions]
    
    def _generate_attribute_questions(self, attr: str, info: Dict, 
                                   asked_questions: Set[Tuple[str, str]]) -> List[Dict[str, Any]]:
        """Generate questions for a specific attribute"""
        questions = []
        values = list(info['values'])
        
        if not values:
            return questions
        
        # Generate different types of questions based on attribute type
        if 'numeric' in info['types']:
            questions.extend(self._generate_numeric_questions(attr, values))
        
        if 'string' in info['types'] or 'list' in info['types']:
            questions.extend(self._generate_string_questions(attr, values))
        
        # Generate pattern-based questions
        questions.extend(self._generate_pattern_questions(attr, values, info))
        
        return questions
    
    def _generate_numeric_questions(self, attr: str, values: List[str]) -> List[Dict[str, Any]]:
        """Generate questions about numeric attributes"""
        questions = []
        
        # Convert to float
        numeric_values = []
        for v in values:
            try:
                numeric_values.append(float(v))
            except ValueError:
                continue
        
        if len(numeric_values) < 2:
            return questions
        
        # Generate range questions
        numeric_values.sort()
        n = len(numeric_values)
        
        # Quartiles
        q1 = numeric_values[n // 4]
        median = numeric_values[n // 2]
        q3 = numeric_values[3 * n // 4]
        
        questions.append({
            'feature': f"{attr}_range",
            'value': "low",
            'text': f"Is this on the lower end for {attr}?",
            'pattern_type': 'numeric_range'
        })
        
        questions.append({
            'feature': f"{attr}_range",
            'value': "high",
            'text': f"Is this on the higher end for {attr}?",
            'pattern_type': 'numeric_range'
        })
        
        # Average question
        avg = sum(numeric_values) / len(numeric_values)
        questions.append({
            'feature': f"{attr}_average",
            'value': "above_average",
            'text': f"Is this above average for {attr}?",
            'pattern_type': 'numeric_average'
        })
        
        return questions
    
    def _generate_string_questions(self, attr: str, values: List[str]) -> List[Dict[str, Any]]:
        """Generate questions about string attributes"""
        questions = []
        
        # Sample unique values
        unique_values = list(set(values))[:5]  # Limit to 5
        
        for value in unique_values:
            if value and len(str(value)) > 0:
                # Generate varied question templates
                templates = [
                    f"Is this connected with {value}?",
                    f"Would you associate this with {value}?",
                    f"Does this have elements of {value}?",
                    f"Is {value} a key aspect here?",
                    f"Could this be described as {value}?"
                ]
                
                template = random.choice(templates)
                questions.append({
                    'feature': attr,
                    'value': value,
                    'text': template,
                    'pattern_type': 'string_association'
                })
        
        return questions
    
    def _generate_pattern_questions(self, attr: str, values: List[str], info: Dict) -> List[Dict[str, Any]]:
        """Generate pattern-based questions"""
        questions = []
        
        # Length-based questions for strings
        if 'string' in info['types']:
            string_lengths = [len(v) for v in values if isinstance(v, str)]
            if string_lengths:
                avg_length = sum(string_lengths) / len(string_lengths)
                
                # Short vs long
                short_values = [v for v in values if isinstance(v, str) and len(v) < avg_length * 0.5]
                long_values = [v for v in values if isinstance(v, str) and len(v) > avg_length * 1.5]
                
                if short_values:
                    questions.append({
                        'feature': f"{attr}_length",
                        'value': "short",
                        'text': f"Is this notably brief?",
                        'pattern_type': 'length_pattern'
                    })
                
                if long_values:
                    questions.append({
                        'feature': f"{attr}_length",
                        'value': "long",
                        'text': f"Is this particularly extensive?",
                        'pattern_type': 'length_pattern'
                    })
        
        # Count-based questions for lists
        if 'list' in info['types']:
            list_lengths = []
            for song in self.songs:
                song_value = song.get(attr, [])
                if isinstance(song_value, list):
                    list_lengths.append(len(song_value))
            
            if list_lengths:
                avg_length = sum(list_lengths) / len(list_lengths)
                
                questions.append({
                    'feature': f"{attr}_count",
                    'value': "multiple",
                    'text': f"Does this have multiple {attr}?",
                    'pattern_type': 'count_pattern'
                })
                
                questions.append({
                    'feature': f"{attr}_count",
                    'value': "single",
                    'text': f"Is this focused on a single {attr}?",
                    'pattern_type': 'count_pattern'
                })
        
        return questions
    
    def get_dynamic_stats(self) -> Dict[str, Any]:
        """Get statistics about discovered attributes"""
        stats = {
            'total_attributes': len(self.discovered_attributes),
            'attribute_types': {},
            'value_diversity': {}
        }
        
        for attr, info in self.discovered_attributes.items():
            stats['attribute_types'][attr] = list(info['types'])
            stats['value_diversity'][attr] = len(info['values'])
        
        return stats
