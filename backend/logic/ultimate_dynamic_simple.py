"""
Ultimate Dynamic System (Simple Version)
Integrates human relevance validation and redundancy management without web scraping
"""

import json
import random
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)

class UltimateDynamicSimple:
    """The ultimate dynamic question generation system (simple version)"""
    
    def __init__(self, songs: List[Dict[str, Any]]):
        self.songs = songs
        
        # Initialize components
        self.relevance_validator = None
        self.redundancy_manager = None
        
        self._initialize_components()
        
        # Dynamic attribute discovery
        self.dynamic_attributes = self._discover_dynamic_attributes()
        
        # Question generation patterns
        self.question_patterns = self._load_dynamic_patterns()
        
    def _initialize_components(self):
        """Initialize all system components"""
        try:
            from .human_relevance_validator import HumanRelevanceValidator
            self.relevance_validator = HumanRelevanceValidator(use_ai=True)
            logger.info("🧠 Human relevance validator initialized with AI")
        except ImportError:
            logger.warning("Human relevance validator not available")
        
        try:
            from .redundancy_manager import RedundancyManager
            self.redundancy_manager = RedundancyManager()
            logger.info("🔄 Redundancy manager initialized")
        except ImportError:
            logger.warning("Redundancy manager not available")
    
    def _discover_dynamic_attributes(self) -> Dict[str, Dict]:
        """Discover attributes from songs"""
        attributes = {}
        
        for song in self.songs:
            for attr, value in song.items():
                if attr in ['id', 'title']:
                    continue
                
                if attr not in attributes:
                    attributes[attr] = {
                        'values': set(),
                        'types': set(),
                        'count': 0,
                        'source': 'existing'
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
        
        logger.info(f"🔍 Discovered {len(attributes)} dynamic attributes")
        return attributes
    
    def _load_dynamic_patterns(self) -> Dict[str, List[str]]:
        """Load dynamic question patterns"""
        patterns = {
            'human_friendly': [
                "Does this sound like {value}?",
                "Would you say this has a {value} feel?",
                "Is this more of a {value} type of song?",
                "Could you imagine hearing this at a {value}?",
                "Does this give you {value} vibes?",
                "Would this be good for {value}?",
                "Is this the kind of song that makes you feel {value}?"
            ],
            'experience_based': [
                "Would you hear this at {value}?",
                "Is this popular during {value}?",
                "Does this remind you of {value}?",
                "Could this be played at {value}?",
                "Is this associated with {value}?"
            ],
            'time_based': [
                "Does this sound like it's from {value}?",
                "Would you guess this was made in {value}?",
                "Is this typical of {value} music?",
                "Does this have that {value} sound?"
            ],
            'artist_based': [
                "Is this similar to what {value} would make?",
                "Does this sound like something {value} would sing?",
                "Would you find this in {value}'s collection?",
                "Is this in the style of {value}?"
            ],
            'emotional': [
                "Does this make you feel {value}?",
                "Is this a {value} kind of mood?",
                "Would this be good for when you're feeling {value}?",
                "Does this capture the feeling of {value}?"
            ]
        }
        
        return patterns
    
    def generate_ultimate_questions(self, asked_questions: Set[Tuple[str, str]], 
                                  current_beliefs: Dict[int, float],
                                  max_questions: int = 10) -> List[Dict[str, Any]]:
        """Generate the ultimate dynamic questions"""
        
        # Generate base questions from dynamic attributes
        base_questions = self._generate_base_questions(asked_questions)
        
        # Filter for human relevance
        if self.relevance_validator:
            relevant_questions = self.relevance_validator.filter_relevant_questions(base_questions)
            logger.info(f"🧠 Filtered to {len(relevant_questions)} human-relevant questions")
        else:
            relevant_questions = base_questions
        
        # Improve question text
        if self.relevance_validator:
            for question in relevant_questions:
                improved_text = self.relevance_validator.improve_question_text(question)
                question['text'] = improved_text
        
        # Manage redundancy
        if self.redundancy_manager:
            selected_questions = self.redundancy_manager.select_best_questions(
                relevant_questions, current_beliefs, max_questions
            )
            logger.info(f"🔄 Selected {len(selected_questions)} diverse questions")
        else:
            selected_questions = relevant_questions[:max_questions]
        
        return selected_questions
    
    def _generate_base_questions(self, asked_questions: Set[Tuple[str, str]]) -> List[Dict[str, Any]]:
        """Generate base questions from dynamic attributes"""
        questions = []
        
        for attr, info in self.dynamic_attributes.items():
            attr_questions = self._generate_attribute_questions(attr, info, asked_questions)
            questions.extend(attr_questions)
        
        # Remove already asked questions
        available_questions = [
            q for q in questions 
            if (q['feature'], q['value']) not in asked_questions
        ]
        
        return available_questions
    
    def _generate_attribute_questions(self, attr: str, info: Dict, 
                                   asked_questions: Set[Tuple[str, str]]) -> List[Dict[str, Any]]:
        """Generate questions for a specific attribute"""
        questions = []
        values = list(info['values'])
        
        if not values:
            return questions
        
        # Select diverse values
        sample_values = values[:5]  # Limit to 5 values per attribute
        
        for value in sample_values:
            if not value or len(str(value)) == 0:
                continue
            
            # Skip if already asked
            if (attr, value) in asked_questions:
                continue
            
            # Generate questions based on attribute type and patterns
            generated_questions = self._generate_patterned_questions(attr, value, info)
            questions.extend(generated_questions)
        
        return questions
    
    def _generate_patterned_questions(self, attr: str, value: str, info: Dict) -> List[Dict[str, Any]]:
        """Generate questions using appropriate patterns"""
        questions = []
        
        # Determine which patterns to use based on attribute
        patterns_to_use = self._select_patterns_for_attribute(attr, info)
        
        for pattern_type, templates in patterns_to_use.items():
            # Select 1-2 templates from each pattern type
            selected_templates = random.sample(templates, min(2, len(templates)))
            
            for template in selected_templates:
                try:
                    question_text = template.format(value=value)
                    
                    questions.append({
                        'feature': attr,
                        'value': value,
                        'text': question_text,
                        'pattern_type': pattern_type,
                        'attribute_source': info.get('source', 'existing'),
                        'relevance_score': 0.0  # Will be calculated by validator
                    })
                except (KeyError, ValueError):
                    # Skip if template formatting fails
                    continue
        
        return questions
    
    def _select_patterns_for_attribute(self, attr: str, info: Dict) -> Dict[str, List[str]]:
        """Select appropriate patterns for an attribute"""
        patterns = {}
        
        # Map attributes to pattern types
        if attr in ['genres', 'style', 'type']:
            patterns['human_friendly'] = self.question_patterns['human_friendly']
        elif attr in ['artists', 'singer', 'band']:
            patterns['artist_based'] = self.question_patterns['artist_based']
        elif attr in ['decade', 'era', 'year', 'time', 'period']:
            patterns['time_based'] = self.question_patterns['time_based']
        elif attr in ['themes', 'mood', 'feeling', 'emotion', 'vibe']:
            patterns['emotional'] = self.question_patterns['emotional']
        elif attr in ['energy', 'tempo', 'pace']:
            patterns['experience_based'] = self.question_patterns['experience_based']
        else:
            # Default to human-friendly patterns for unknown attributes
            patterns['human_friendly'] = self.question_patterns['human_friendly']
        
        return patterns
    
    def record_question_asked(self, question: Dict[str, Any]):
        """Record that a question was asked"""
        if self.redundancy_manager:
            self.redundancy_manager.record_question_usage(question)
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the system"""
        stats = {
            'dynamic_attributes': {
                'total': len(self.dynamic_attributes),
                'existing': len([a for a, info in self.dynamic_attributes.items() if info.get('source') == 'existing']),
                'scraped': len([a for a, info in self.dynamic_attributes.items() if info.get('source') == 'scraped'])
            },
            'attribute_details': {}
        }
        
        # Add details for each attribute
        for attr, info in self.dynamic_attributes.items():
            stats['attribute_details'][attr] = {
                'value_count': len(info['values']),
                'types': list(info['types']),
                'source': info.get('source', 'unknown')
            }
        
        # Add relevance statistics
        if self.relevance_validator:
            # Generate sample questions to validate
            sample_questions = self._generate_base_questions(set())[:20]
            relevance_stats = self.relevance_validator.get_relevance_statistics(sample_questions)
            stats['relevance_validation'] = relevance_stats
        
        # Add redundancy statistics
        if self.redundancy_manager:
            stats['redundancy_management'] = self.redundancy_manager.get_usage_statistics()
        
        return stats
    
    def reset_for_new_game(self):
        """Reset system for a new game"""
        if self.redundancy_manager:
            self.redundancy_manager.reset_usage_counts()
        logger.info("🔄 Ultimate dynamic system reset for new game")
