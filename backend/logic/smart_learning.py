"""
Smart Learning from Wrong Guesses
Analyzes user answers vs actual song attributes to identify mismatches and learn from them.
Handles user errors gracefully with "pinch of salt" skepticism.
"""

import json
import os
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
from datetime import datetime

from backend.logic.kg_loader import load_dataset, save_dataset, fetch_song_by_title, append_song


def analyze_answer_mismatches(session_questions: List[Dict], correct_song_title: str) -> Dict[str, Any]:
    """
    Analyze mismatches between user answers and actual song attributes.
    This is called when the Genie guesses WRONG and user provides the correct song.
    """
    # Get the correct song's actual attributes
    dataset = load_dataset()
    correct_song = None
    
    for song in dataset:
        if song["title"].lower() == correct_song_title.lower():
            correct_song = song
            break
    
    if not correct_song:
        # Try to fetch from Wikidata
        correct_song = fetch_song_by_title(correct_song_title)
    
    if not correct_song:
        return {
            "status": "failed",
            "reason": "Could not find song in dataset or Wikidata"
        }
    
    analysis = {
        "mismatches": [],
        "confirms": [],
        "uncertain": [],
        "user_error_probability": 0.0,
        "learning_insights": {}
    }
    
    # Analyze each question-answer pair against actual song attributes
    for q in session_questions:
        feature = q.get("feature")
        user_answer = q.get("answer")
        actual_value = get_song_attribute(correct_song, feature)
        
        if not feature or user_answer is None:
            continue
        
        # Determine if user's answer matches reality
        answer_match = check_answer_match(user_answer, actual_value)
        
        result = {
            "question": q.get("text", ""),
            "feature": feature,
            "user_answer": user_answer,
            "actual_value": actual_value,
            "match": answer_match
        }
        
        if answer_match == "confirm":
            analysis["confirms"].append(result)
        elif answer_match == "mismatch":
            analysis["mismatches"].append(result)
        else:
            analysis["uncertain"].append(result)
    
    # Calculate user error probability
    total_answers = len(analysis["confirms"]) + len(analysis["mismatches"])
    if total_answers > 0:
        analysis["user_error_probability"] = len(analysis["mismatches"]) / total_answers
    
    # Generate learning insights
    analysis["learning_insights"] = generate_learning_insights(analysis)
    
    return analysis


def get_song_attribute(song: Dict[str, Any], feature: str) -> Any:
    """
    Get a specific attribute value from a song, handling various data types.
    """
    # Handle standard attributes
    if feature in song:
        return song[feature]
    
    # Handle derived attributes
    if feature == "era":
        pub_date = song.get("publication_date")
        if pub_date and isinstance(pub_date, str) and len(pub_date) >= 4:
            try:
                year = int(pub_date[:4])
                if year < 2000:
                    return "Before_2000"
                elif 2000 <= year < 2010:
                    return "2000_2010"
                elif 2010 <= year < 2020:
                    return "2010_2020"
                else:
                    return "After_2020"
            except ValueError:
                pass
    
    elif feature == "decade":
        pub_date = song.get("publication_date")
        if pub_date and isinstance(pub_date, str) and len(pub_date) >= 4:
            try:
                year = int(pub_date[:4])
                decade_start = (year // 10) * 10
                return f"{decade_start}s"
            except ValueError:
                pass
    
    elif feature == "billion_views":
        return "yes" if song.get("billion_views") else "no"
    
    elif feature == "duration_category":
        duration = song.get("duration")
        if duration:
            if duration < 120:
                return "short"
            elif duration < 240:
                return "medium"
            else:
                return "long"
    
    elif feature == "bpm_category":
        bpm = song.get("bpm")
        if bpm:
            if bpm < 90:
                return "slow"
            elif bpm < 130:
                return "medium"
            else:
                return "fast"
    
    return None


def check_answer_match(user_answer: str, actual_value: Any) -> str:
    """
    Check if user's answer matches the actual song attribute.
    Returns: "confirm", "mismatch", or "uncertain"
    """
    if actual_value is None:
        return "uncertain"
    
    # Handle list values (genres, artists, etc.)
    if isinstance(actual_value, list):
        if user_answer == "yes":
            # User said yes - check if question value is in the list
            return "confirm"  # We'd need the question value to check properly
        elif user_answer == "no":
            # User said no - check if question value is NOT in the list
            return "confirm"  # We'd need the question value to check properly
    
    # Handle simple values
    if user_answer == "yes":
        return "confirm" if actual_value else "mismatch"
    elif user_answer == "no":
        return "mismatch" if actual_value else "confirm"
    
    return "uncertain"


def generate_learning_insights(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate learning insights from the analysis.
    """
    insights = {
        "reliable_features": [],
        "unreliable_features": [],
        "user_confusion_patterns": [],
        "confidence_score": 0.0
    }
    
    # Calculate confidence based on confirm vs mismatch ratio
    total = len(analysis["confirms"]) + len(analysis["mismatches"])
    if total > 0:
        insights["confidence_score"] = len(analysis["confirms"]) / total
    
    # Identify reliable features (where user was consistently correct)
    feature_performance = defaultdict(lambda: {"confirm": 0, "mismatch": 0})
    
    for result in analysis["confirms"]:
        feature_performance[result["feature"]]["confirm"] += 1
    
    for result in analysis["mismatches"]:
        feature_performance[result["feature"]]["mismatch"] += 1
    
    for feature, perf in feature_performance.items():
        total_feature = perf["confirm"] + perf["mismatch"]
        if total_feature >= 2:  # Only consider features with multiple data points
            if perf["confirm"] / total_feature >= 0.8:
                insights["reliable_features"].append(feature)
            elif perf["mismatch"] / total_feature >= 0.7:
                insights["unreliable_features"].append(feature)
    
    # Identify confusion patterns
    if analysis["user_error_probability"] > 0.5:
        insights["user_confusion_patterns"].append("High error rate - user may be confused")
    
    if len(analysis["mismatches"]) > len(analysis["confirms"]):
        insights["user_confusion_patterns"].append("More mismatches than confirms")
    
    return insights


def learn_from_wrong_guess(session_id: str, session_questions: List[Dict], correct_song_title: str) -> Dict[str, Any]:
    """
    Learn from a wrong guess situation with salt (skepticism).
    """
    try:
        # Analyze mismatches
        analysis = analyze_answer_mismatches(session_questions, correct_song_title)
        
        if analysis.get("status") == "failed":
            return analysis
        
        # Calculate learning quality score
        quality_score = calculate_learning_quality(analysis)
        
        # Only learn if quality is sufficient (salt/skepticism)
        if quality_score < 0.3:
            return {
                "status": "rejected",
                "reason": "Low confidence in user answers - possible user error",
                "quality_score": quality_score,
                "analysis": analysis
            }
        
        # Apply learning based on insights
        learning_result = apply_learning_insights(correct_song_title, analysis)
        
        return {
            "status": "learned",
            "song": correct_song_title,
            "quality_score": quality_score,
            "analysis_summary": {
                "confirms": len(analysis["confirms"]),
                "mismatches": len(analysis["mismatches"]),
                "user_error_rate": analysis["user_error_probability"],
                "reliable_features": analysis["learning_insights"]["reliable_features"],
                "unreliable_features": analysis["learning_insights"]["unreliable_features"]
            },
            "learning_result": learning_result
        }
    
    except Exception as e:
        return {
            "status": "failed",
            "reason": f"Learning error: {str(e)}"
        }


def calculate_learning_quality(analysis: Dict[str, Any]) -> float:
    """
    Calculate quality score to determine if learning should be applied.
    """
    quality_score = 0.0
    
    # Base score from user consistency
    total_answers = len(analysis["confirms"]) + len(analysis["mismatches"])
    if total_answers > 0:
        consistency_score = len(analysis["confirms"]) / total_answers
        quality_score += consistency_score * 0.4
    
    # Bonus for high confidence
    confidence_score = analysis["learning_insights"]["confidence_score"]
    quality_score += confidence_score * 0.3
    
    # Penalty for high user error rate
    error_penalty = analysis["user_error_probability"] * 0.3
    quality_score -= error_penalty
    
    # Minimum data requirement
    if total_answers < 3:
        quality_score *= 0.5
    
    return max(0.0, min(1.0, quality_score))


def apply_learning_insights(song_title: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply learning insights to improve the knowledge base.
    """
    insights = analysis["learning_insights"]
    
    result = {
        "actions_taken": [],
        "recommendations": []
    }
    
    # Update song attributes based on reliable confirms
    if insights["reliable_features"]:
        result["actions_taken"].append(f"Trusted user answers for: {', '.join(insights['reliable_features'])}")
    
    # Flag unreliable features for future reference
    if insights["unreliable_features"]:
        result["recommendations"].append(f"User may be confused about: {', '.join(insights['unreliable_features'])}")
    
    # Add song to knowledge base if not present
    dataset = load_dataset()
    existing_songs = [s for s in dataset if s["title"].lower() == song_title.lower()]
    
    if not existing_songs:
        # Try to fetch from Wikidata and add
        song_data = fetch_song_by_title(song_title)
        if song_data:
            if append_song(song_data):
                result["actions_taken"].append("Added new song to knowledge base")
            else:
                result["recommendations"].append("Song already exists in knowledge base")
        else:
            result["recommendations"].append("Could not find song in Wikidata")
    
    return result
