"""
Hybrid Question Selection System
Combines multiple intelligence sources for optimal question generation
"""

import math
import random
from typing import List, Dict, Any, Set, Tuple, Optional
from collections import defaultdict

from backend.logic.hybrid_engine import HybridEngine


def select_best_hybrid_question(
    questions: List[Dict[str, Any]], 
    songs: List[Dict[str, Any]], 
    beliefs: List[float], 
    asked: Set[Tuple[str, str]],
    engine: HybridEngine
) -> Optional[Dict[str, Any]]:
    """
    Select the best question using hybrid intelligence
    """
    
    # Get current top candidates
    candidate_indices = sorted(range(len(beliefs)), key=lambda i: beliefs[i], reverse=True)[:10]
    candidate_titles = [songs[i]["title"] for i in candidate_indices]
    
    # Try hybrid question generation first
    if hasattr(engine, 'get_optimal_question'):
        hybrid_question = engine.get_optimal_question(candidate_titles, asked)
        if hybrid_question:
            return hybrid_question
    
    # Fallback to enhanced traditional selection
    return select_enhanced_traditional_question(questions, songs, beliefs, asked)


def select_enhanced_traditional_question(
    questions: List[Dict[str, Any]], 
    songs: List[Dict[str, Any]], 
    beliefs: List[float], 
    asked: Set[Tuple[str, str]]
) -> Optional[Dict[str, Any]]:
    """
    Enhanced traditional question selection with multiple improvements
    """
    
    # Enhanced feature weights
    FEATURE_WEIGHTS = {
        # High-value distinguishing features
        "artist_genders": 1.3,
        "artist_types": 1.2,
        "song_types": 1.1,
        "billion_views": 1.0,
        
        # Media connections
        "films": 0.95,
        "tv_series": 0.95,
        "video_games": 0.9,
        
        # Traditional good features
        "genres": 1.0,
        "language": 0.9,
        "era": 0.85,
        "decade": 0.85,
        "awards": 0.85,
        
        # Musical characteristics
        "instruments": 0.8,
        "bpm_category": 0.75,
        "duration_category": 0.7,
        "themes": 0.75,
        
        # Medium value
        "labels": 0.75,
        "producers": 0.7,
        "composers": 0.7,
        "chart_positions": 0.8,
        
        # Lower value (more specific)
        "artists": 0.5,
        "country": 0.6,
        "locations": 0.6,
        "performers": 0.6,
        "vocalists": 0.6,
    }
    
    # Get top candidates for analysis
    top_n = min(10, len(songs))
    candidate_indices = sorted(range(len(beliefs)), key=lambda i: beliefs[i], reverse=True)[:top_n]
    candidate_songs = [songs[i] for i in candidate_indices]
    
    best_question = None
    best_score = -1.0
    
    # Extract answered features for logical filtering
    answered_features = {}
    for (feature, value) in asked:
        if feature not in answered_features:
            answered_features[feature] = []
        answered_features[feature].append(value)
    
    for q in questions:
        key = (q["feature"], q["value"])
        if key in asked:
            continue
        
        # Enhanced logical filtering
        feature = q["feature"]
        value = q["value"]
        
        # Skip redundant questions
        if feature in ["era", "decade"] and "era" in answered_features:
            continue
        if feature == "year" and ("era" in answered_features or "decade" in answered_features):
            continue
        if feature == "language" and "language" in answered_features:
            continue
        if feature == "country" and "country" in answered_features:
            continue
        
        # Calculate information gain
        base_score = score_question_enhanced(q, candidate_songs, beliefs, candidate_indices)
        
        # Apply feature weights
        feature_weight = FEATURE_WEIGHTS.get(feature, 1.0)
        
        # Apply diversity penalty
        asked_feature_count = sum(1 for (f, _) in asked if f == feature)
        diversity_factor = 1.0 / (1.0 + asked_feature_count * 0.3)
        
        # Apply balance bonus (questions that split candidates evenly)
        balance_bonus = calculate_balance_bonus(q, candidate_songs)
        
        # Apply confidence bonus based on question type
        confidence_bonus = get_confidence_bonus(feature, value, candidate_songs)
        
        # Final score calculation
        adjusted_score = (
            base_score * feature_weight * diversity_factor + 
            balance_bonus + confidence_bonus
        )
        
        if adjusted_score > best_score:
            best_score = adjusted_score
            best_question = q
    
    return best_question


def score_question_enhanced(
    question: Dict[str, Any], 
    candidate_songs: List[Dict[str, Any]], 
    beliefs: List[float], 
    candidate_indices: List[int]
) -> float:
    """
    Enhanced information gain calculation
    """
    
    feature = question["feature"]
    value = question["value"]
    
    # Count how many candidates have this feature
    yes_count = 0
    no_count = 0
    
    for song in candidate_songs:
        if song_has_feature(song, feature, value):
            yes_count += 1
        else:
            no_count += 1
    
    if yes_count == 0 or no_count == 0:
        return 0.0  # No information gain
    
    # Calculate entropy reduction
    total_count = yes_count + no_count
    p_yes = yes_count / total_count
    p_no = no_count / total_count
    
    # Current entropy
    current_entropy = -sum(b * math.log2(b) for b in beliefs[i] for i in candidate_indices if b > 0)
    
    # Expected entropy after asking question
    yes_entropy = 0.0
    no_entropy = 0.0
    
    for i, song_idx in enumerate(candidate_indices):
        belief = beliefs[song_idx]
        if song_has_feature(candidate_songs[i], feature, value):
            yes_entropy -= belief * math.log2(belief) if belief > 0 else 0
        else:
            no_entropy -= belief * math.log2(belief) if belief > 0 else 0
    
    # Weighted average entropy
    expected_entropy = (p_yes * yes_entropy + p_no * no_entropy)
    
    # Information gain
    information_gain = current_entropy - expected_entropy
    
    return information_gain


def song_has_feature(song: Dict[str, Any], feature: str, value: str) -> bool:
    """Check if a song has a specific feature value"""
    
    if feature == "genres":
        return value in song.get("genres", [])
    elif feature == "artists":
        return value in song.get("artists", [])
    elif feature == "language":
        return song.get("language") == value
    elif feature == "country":
        return song.get("country") == value
    elif feature == "era":
        pub_date = song.get("publication_date")
        if pub_date and isinstance(pub_date, str) and len(pub_date) >= 4:
            try:
                year = int(pub_date[:4])
                if year < 2000:
                    return value == "Before_2000"
                elif 2000 <= year < 2010:
                    return value == "2000_2010"
                elif 2010 <= year < 2020:
                    return value == "2010_2020"
                else:
                    return value == "After_2020"
            except ValueError:
                pass
        return False
    elif feature == "decade":
        pub_date = song.get("publication_date")
        if pub_date and isinstance(pub_date, str) and len(pub_date) >= 4:
            try:
                year = int(pub_date[:4])
                decade_start = (year // 10) * 10
                decade_label = f"{decade_start}s"
                return value == decade_label
            except ValueError:
                pass
        return False
    elif feature == "billion_views":
        return (value == "yes" and song.get("billion_views")) or \
               (value == "no" and not song.get("billion_views"))
    elif feature == "duration_category":
        duration = song.get("duration")
        if not duration:
            return False
        if value == "short":
            return duration < 120
        elif value == "medium":
            return 120 <= duration < 240
        elif value == "long":
            return duration >= 240
    elif feature == "bpm_category":
        bpm = song.get("bpm")
        if not bpm:
            return False
        if value == "slow":
            return bpm < 90
        elif value == "medium":
            return 90 <= bpm < 130
        elif value == "fast":
            return bpm >= 130
    else:
        # Handle other features generically
        feature_values = song.get(feature, [])
        if isinstance(feature_values, list):
            return value in feature_values
        else:
            return song.get(feature) == value
    
    return False


def calculate_balance_bonus(question: Dict[str, Any], candidate_songs: List[Dict[str, Any]]) -> float:
    """
    Calculate bonus for questions that split candidates evenly
    """
    feature = question["feature"]
    value = question["value"]
    
    yes_count = sum(1 for song in candidate_songs if song_has_feature(song, feature, value))
    no_count = len(candidate_songs) - yes_count
    
    if yes_count == 0 or no_count == 0:
        return 0.0
    
    # Ideal split is 50/50
    ideal_split = len(candidate_songs) / 2
    deviation = abs(yes_count - ideal_split)
    
    # Bonus decreases with deviation from ideal
    bonus = 1.0 - (deviation / ideal_split)
    
    return bonus * 0.1  # Scale down to not overwhelm other factors


def get_confidence_bonus(feature: str, value: str, candidate_songs: List[Dict[str, Any]]) -> float:
    """
    Get confidence bonus based on feature reliability
    """
    # High-confidence features
    high_confidence_features = {
        "artist_genders", "artist_types", "song_types", 
        "billion_views", "films", "tv_series"
    }
    
    # Medium-confidence features
    medium_confidence_features = {
        "genres", "era", "decade", "awards", "instruments"
    }
    
    if feature in high_confidence_features:
        return 0.05
    elif feature in medium_confidence_features:
        return 0.02
    else:
        return 0.0


def make_question_text_enhanced(feature: str, value: str) -> str:
    """
    Generate enhanced question text with more variety
    """
    
    # Enhanced templates for different features
    templates = {
        "artist_genders": [
            f"Is the artist {value}?",
            f"Is it performed by a {value} artist?",
            f"Would you say the main vocalist is {value}?"
        ],
        "artist_types": [
            f"Is it by a {value}?",
            f"Is the artist a {value}?",
            f"Would you classify this as a {value} performance?"
        ],
        "song_types": [
            f"Is it a {value}?",
            f"Was this released as a {value}?",
            f"Is this considered a {value} recording?"
        ],
        "films": [
            f"Is it from the movie {value}?",
            f"Was it featured in {value}?",
            f"Can you hear this in the film {value}?"
        ],
        "tv_series": [
            f"Is it from the TV show {value}?",
            f"Was this used in {value}?",
            f"Is this associated with the series {value}?"
        ],
        "billion_views": [
            f"Does it have over a billion views?",
            f"Is this a billion-view hit?",
            f"Has it crossed the billion-view mark?"
        ],
        "genres": [
            f"Is it a {value} song?",
            f"Would you classify this as {value}?",
            f"Does this have a {value} sound?"
        ],
        "era": [
            f"Is it from the {value.replace('_', ' ')} era?",
            f"Does this sound like it's from the {value.replace('_', ' ')}?",
            f"Was this recorded around the {value.replace('_', ' ')} period?"
        ],
        "instruments": [
            f"Does it feature {value}?",
            f"Can you hear {value} in this song?",
            f"Is {value} prominently featured?"
        ],
        "bpm_category": [
            f"Is it a {value} tempo song?",
            f"Would you describe the tempo as {value}?",
            f"Does this have a {value} pace?"
        ],
        "duration_category": [
            f"Is it a {value} song?",
            f"Would you say it's {value} in length?",
            f"Does this feel {value}?"
        ]
    }
    
    # Get appropriate templates or use default
    if feature in templates:
        return random.choice(templates[feature])
    else:
        # Default templates
        default_templates = [
            f"Is it connected with {value}?",
            f"Would you associate it with {value}?",
            f"Is {value} relevant here?"
        ]
        return random.choice(default_templates)
