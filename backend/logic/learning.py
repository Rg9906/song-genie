"""
Smart learning system that analyzes user feedback to improve the knowledge base.
Implements cautious learning with salt (skepticism) to handle potential misinformation.
"""

import json
import os
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
from datetime import datetime

from backend.logic.kg_loader import load_dataset, save_dataset, fetch_song_by_title, append_song
from backend.logic.config import REQUEST_TIMEOUT_SECONDS


def analyze_question_answer_pattern(session_questions: List[Dict], correct_song_title: str) -> Dict[str, Any]:
    """
    Analyze the question-answer pattern to identify what attributes the correct song should have.
    """
    analysis = {
        "inferred_attributes": defaultdict(list),
        "confidence_scores": {},
        "contradictions": [],
        "missing_attributes": set()
    }
    
    # Analyze each question-answer pair
    for q in session_questions:
        feature = q.get("feature")
        answer = q.get("answer")
        
        if feature and answer is not None:
            # If user said YES, the song should have this attribute
            if answer == "yes":
                analysis["inferred_attributes"][feature].append(q.get("value"))
                analysis["confidence_scores"][feature] = analysis["confidence_scores"].get(feature, 0) + 1
            
            # If user said NO, the song should NOT have this attribute
            elif answer == "no":
                analysis["inferred_attributes"][f"not_{feature}"].append(q.get("value"))
                analysis["confidence_scores"][f"not_{feature}"] = analysis["confidence_scores"].get(f"not_{feature}", 0) + 1
    
    # Calculate confidence scores (normalized by total questions per feature)
    feature_counts = Counter(q.get("feature") for q in session_questions if q.get("feature"))
    for feature in analysis["confidence_scores"]:
        base_feature = feature.replace("not_", "")
        if base_feature in feature_counts:
            analysis["confidence_scores"][feature] = analysis["confidence_scores"][feature] / feature_counts[base_feature]
    
    return analysis


def infer_song_attributes(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Infer song attributes from the analysis with confidence weighting.
    """
    inferred = {}
    
    for feature, values in analysis["inferred_attributes"].items():
        if not values:
            continue
            
        # Use the most common value for each feature
        value_counts = Counter(values)
        most_common_value, count = value_counts.most_common(1)[0]
        
        # Only include if confidence is high enough (>0.6)
        confidence = analysis["confidence_scores"].get(feature, 0)
        if confidence > 0.6:
            if feature.startswith("not_"):
                # Handle negative attributes (things the song is NOT)
                actual_feature = feature[4:]
                if actual_feature not in inferred:
                    inferred[actual_feature] = {"exclude": set()}
                inferred[actual_feature]["exclude"].add(most_common_value)
            else:
                # Handle positive attributes
                if feature not in inferred:
                    inferred[feature] = {"include": set()}
                inferred[feature]["include"].add(most_common_value)
    
    return inferred


def create_enhanced_song_from_wikidata(song_title: str, analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Create an enhanced song entry by combining Wikidata data with learned attributes.
    """
    # First, try to get basic info from Wikidata
    base_song = fetch_song_by_title(song_title)
    
    if not base_song:
        # If not found in Wikidata, create from analysis only
        base_song = {
            "title": song_title,
            "artists": [],
            "genres": [],
            "publication_date": None,
            "language": None,
            "country": None,
        }
    
    # Apply learned attributes with salt (skepticism)
    inferred = infer_song_attributes(analysis)
    
    for feature, attr_data in inferred.items():
        if "include" in attr_data and attr_data["include"]:
            # Only add if not already present and we're confident enough
            if feature in base_song:
                if isinstance(base_song[feature], list):
                    for value in attr_data["include"]:
                        if value not in base_song[feature]:
                            base_song[feature].append(value)
                else:
                    # For single-value attributes, only set if empty
                    if not base_song[feature]:
                        base_song[feature] = list(attr_data["include"])[0]
            else:
                # New attribute
                if len(attr_data["include"]) == 1:
                    base_song[feature] = list(attr_data["include"])[0]
                else:
                    base_song[feature] = list(attr_data["include"])
    
    return base_song


def learn_from_feedback(session_id: str, session_questions: List[Dict], correct_song_title: str) -> Dict[str, Any]:
    """
    Learn from user feedback with salt (skepticism) to handle potential misinformation.
    """
    try:
        # Analyze the question-answer pattern
        analysis = analyze_question_answer_pattern(session_questions, correct_song_title)
        
        # Create enhanced song entry
        enhanced_song = create_enhanced_song_from_wikidata(correct_song_title, analysis)
        
        if not enhanced_song:
            return {
                "status": "failed",
                "reason": "Could not create song entry",
                "analysis": analysis
            }
        
        # Check if song already exists
        dataset = load_dataset()
        existing_songs = [s for s in dataset if s["title"].lower() == correct_song_title.lower()]
        
        if existing_songs:
            # Update existing song with new attributes
            existing_song = existing_songs[0]
            
            # Merge attributes with salt (only add if confident)
            for key, value in enhanced_song.items():
                if key not in existing_song or not existing_song[key]:
                    if value:  # Only add non-empty values
                        existing_song[key] = value
            
            save_dataset(dataset)
            
            return {
                "status": "updated",
                "song": correct_song_title,
                "analysis_summary": {
                    "inferred_features": len(analysis["inferred_attributes"]),
                    "high_confidence_features": sum(1 for conf in analysis["confidence_scores"].values() if conf > 0.6)
                }
            }
        else:
            # Add new song
            if append_song(enhanced_song):
                return {
                    "status": "learned",
                    "song": correct_song_title,
                    "analysis_summary": {
                        "inferred_features": len(analysis["inferred_attributes"]),
                        "high_confidence_features": sum(1 for conf in analysis["confidence_scores"].values() if conf > 0.6)
                    }
                }
            else:
                return {
                    "status": "failed",
                    "reason": "Song already exists or append failed"
                }
    
    except Exception as e:
        return {
            "status": "failed", 
            "reason": f"Learning error: {str(e)}"
        }


def validate_learning_quality(analysis: Dict[str, Any]) -> float:
    """
    Calculate a quality score for the learning to determine if it should be applied.
    Returns a score between 0 and 1.
    """
    quality_score = 0.0
    
    # Number of questions answered
    total_questions = len(analysis.get("inferred_attributes", {}))
    if total_questions < 5:
        return 0.0  # Not enough data
    
    # Average confidence
    confidences = analysis.get("confidence_scores", {})
    if not confidences:
        return 0.0
    
    avg_confidence = sum(confidences.values()) / len(confidences)
    quality_score += avg_confidence * 0.4
    
    # Number of high-confidence features
    high_conf_count = sum(1 for conf in confidences.values() if conf > 0.7)
    quality_score += (high_conf_count / total_questions) * 0.3
    
    # Contradiction detection (lower score if many contradictions)
    contradictions = len(analysis.get("contradictions", []))
    quality_score -= (contradictions / total_questions) * 0.2
    
    # Bonus for diverse feature types
    feature_types = set(k.replace("not_", "") for k in analysis.get("inferred_attributes", {}).keys())
    diversity_bonus = min(len(feature_types) / 10, 0.1)
    quality_score += diversity_bonus
    
    return max(0.0, min(1.0, quality_score))
