"""
Redundancy Manager with Usage Probability Factors
Manages question redundancy using intelligent probability-based selection
"""

import random
import math
from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)

class RedundancyManager:
    """Manages question redundancy using usage probability factors"""
    
    def __init__(self):
        self.category_usage = defaultdict(float)
        self.feature_usage = defaultdict(float)
        self.question_history = []
        self.usage_decay_factor = 0.1  # How quickly usage probability decays
        self.diversity_bonus = 0.2     # Bonus for unused categories
        
    def calculate_question_priority(self, question: Dict[str, Any], 
                                  current_beliefs: Dict[int, float]) -> float:
        """
        Calculate question priority based on:
        1. Information gain (how much it splits the answer set)
        2. Usage probability (how much this category has been used)
        3. Redundancy penalty (avoid repeating similar questions)
        """
        
        # Calculate information gain
        info_gain = self._calculate_information_gain(question, current_beliefs)
        
        # Calculate usage penalty
        usage_penalty = self._calculate_usage_penalty(question)
        
        # Calculate redundancy penalty
        redundancy_penalty = self._calculate_redundancy_penalty(question)
        
        # Combine scores
        priority = (info_gain * 0.5) + (usage_penalty * 0.3) + (redundancy_penalty * 0.2)
        
        return priority
    
    def _calculate_information_gain(self, question: Dict[str, Any], 
                                  current_beliefs: Dict[int, float]) -> float:
        """Calculate how much the question splits the possible answers"""
        # This would connect to your actual belief system
        # For now, return a simplified score based on feature diversity
        
        feature = question.get('feature', '')
        value = question.get('value', '')
        
        # Questions that split the dataset well have higher information gain
        # This is a simplified version - you'd use your actual information gain calculation
        base_score = 0.5
        
        # Bonus for questions that likely split the dataset evenly
        if feature in ['genres', 'artists', 'decade']:
            base_score += 0.3
        elif feature in ['themes', 'mood', 'energy']:
            base_score += 0.2
        
        return min(base_score, 1.0)
    
    def _calculate_usage_penalty(self, question: Dict[str, Any]) -> float:
        """Calculate penalty based on category usage"""
        feature = question.get('feature', '')
        
        # Get usage count for this feature
        usage_count = self.feature_usage.get(feature, 0)
        
        # Calculate penalty (higher usage = higher penalty)
        penalty = 1.0 - math.exp(-usage_count * self.usage_decay_factor)
        
        return penalty
    
    def _calculate_redundancy_penalty(self, question: Dict[str, Any]) -> float:
        """Calculate penalty based on similarity to previous questions"""
        current_text = question.get('text', '').lower()
        
        redundancy_score = 0.0
        
        for prev_question in self.question_history[-10:]:  # Check last 10 questions
            prev_text = prev_question.get('text', '').lower()
            
            # Calculate text similarity (simplified)
            similarity = self._text_similarity(current_text, prev_text)
            
            if similarity > 0.7:  # High similarity
                redundancy_score += 0.5
            elif similarity > 0.5:  # Medium similarity
                redundancy_score += 0.2
        
        # Normalize to 0-1 (lower is better, so we return 1 - redundancy_score)
        return min(redundancy_score, 1.0)
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity (simplified Jaccard similarity)"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0
    
    def select_best_questions(self, questions: List[Dict[str, Any]], 
                            current_beliefs: Dict[int, float],
                            max_questions: int = 10) -> List[Dict[str, Any]]:
        """Select best questions while avoiding redundancy"""
        
        # Calculate priority for each question
        scored_questions = []
        for question in questions:
            priority = self.calculate_question_priority(question, current_beliefs)
            scored_questions.append((question, priority))
        
        # Sort by priority (highest first)
        scored_questions.sort(key=lambda x: x[1], reverse=True)
        
        # Select questions while ensuring diversity
        selected_questions = []
        used_categories = set()
        
        for question, priority in scored_questions:
            if len(selected_questions) >= max_questions:
                break
            
            # Check if we've used this category too much
            category = self._get_question_category(question)
            
            # Allow some repetition but prefer diversity
            if category in used_categories and len(used_categories) < min(5, max_questions):
                # Skip this question to ensure diversity
                continue
            
            selected_questions.append(question)
            used_categories.add(category)
        
        return selected_questions
    
    def _get_question_category(self, question: Dict[str, Any]) -> str:
        """Get the category of a question for diversity management"""
        feature = question.get('feature', '')
        
        # Map features to broader categories
        category_mapping = {
            'genres': 'music_style',
            'artists': 'artist_info',
            'themes': 'content',
            'mood': 'content',
            'energy': 'content',
            'decade': 'time_period',
            'era': 'time_period',
            'year': 'time_period',
            'duration': 'technical',
            'bpm': 'technical',
            'tempo': 'technical',
            'instruments': 'technical',
            'language': 'metadata',
            'country': 'metadata'
        }
        
        return category_mapping.get(feature, 'other')
    
    def record_question_usage(self, question: Dict[str, Any]):
        """Record that a question was asked"""
        feature = question.get('feature', '')
        category = self._get_question_category(question)
        
        # Update usage counts
        self.feature_usage[feature] += 1.0
        self.category_usage[category] += 1.0
        
        # Add to history
        self.question_history.append(question)
        
        # Keep history manageable
        if len(self.question_history) > 50:
            self.question_history = self.question_history[-50:]
        
        logger.debug(f"Recorded usage for {feature} (category: {category})")
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """Get statistics about question usage"""
        total_questions = len(self.question_history)
        
        if total_questions == 0:
            return {
                'total_questions': 0,
                'feature_distribution': {},
                'category_distribution': {},
                'most_used_features': [],
                'least_used_features': []
            }
        
        feature_counts = Counter(self.feature_usage)
        category_counts = Counter(self.category_usage)
        
        return {
            'total_questions': total_questions,
            'feature_distribution': dict(feature_counts),
            'category_distribution': dict(category_counts),
            'most_used_features': feature_counts.most_common(5),
            'least_used_features': feature_counts.most_common()[-5:],
            'most_used_categories': category_counts.most_common(3),
            'least_used_categories': category_counts.most_common()[-3:]
        }
    
    def reset_usage_counts(self):
        """Reset usage counts (for new game)"""
        self.category_usage.clear()
        self.feature_usage.clear()
        self.question_history.clear()
        logger.info("Reset redundancy manager usage counts")
    
    def suggest_diversity_improvements(self) -> List[str]:
        """Suggest improvements for question diversity"""
        suggestions = []
        stats = self.get_usage_statistics()
        
        # Check for overused categories
        most_used = stats['most_used_categories']
        if most_used:
            top_category, count = most_used[0]
            if count > stats['total_questions'] * 0.4:  # More than 40% from one category
                suggestions.append(f"Reduce questions from '{top_category}' category (used {count} times)")
        
        # Check for underused categories
        least_used = stats['least_used_categories']
        if least_used:
            bottom_category, count = least_used[0]
            if count == 0 and stats['total_questions'] > 5:
                suggestions.append(f"Consider adding questions from '{bottom_category}' category")
        
        # Check for feature imbalance
        feature_dist = stats['feature_distribution']
        if len(feature_dist) > 0:
            max_count = max(feature_dist.values())
            min_count = min(feature_dist.values())
            if max_count > min_count * 3:  # One feature used 3x more than others
                suggestions.append("Balance question distribution across different features")
        
        return suggestions
    
    def calculate_optimal_question_mix(self, available_questions: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate optimal mix of question categories"""
        # Count available questions by category
        category_counts = defaultdict(int)
        for question in available_questions:
            category = self._get_question_category(question)
            category_counts[category] += 1
        
        # Calculate optimal distribution (balanced but weighted by availability)
        total_categories = len(category_counts)
        if total_categories == 0:
            return {}
        
        # Base distribution: equal parts
        base_per_category = 10 // total_categories  # Assuming we want ~10 questions
        
        # Adjust based on availability
        optimal_mix = {}
        for category, count in category_counts.items():
            if count >= base_per_category:
                optimal_mix[category] = base_per_category
            else:
                # If fewer questions available, use what we have
                optimal_mix[category] = count
        
        return optimal_mix
