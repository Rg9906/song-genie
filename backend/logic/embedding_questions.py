"""
Embedding-based Question System
Uses neural embeddings to generate intelligent questions based on vector similarity
"""

import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
import json

from backend.logic.embeddings import EmbeddingTrainer


class EmbeddingQuestionSystem:
    """Generates questions based on embedding similarity analysis"""
    
    def __init__(self, trainer: EmbeddingTrainer, songs: List[Dict[str, Any]]):
        self.trainer = trainer
        self.songs = songs
        self.title_to_idx = {song["title"]: i for i, song in enumerate(songs)}
        self.feature_importance = self._analyze_feature_importance()
    
    def _analyze_feature_importance(self) -> Dict[str, float]:
        """Analyze which features contribute most to embedding similarity"""
        importance = defaultdict(float)
        
        # Sample some song pairs and analyze their differences
        sample_songs = self.songs[:20]  # Sample first 20 songs
        
        for i, song1 in enumerate(sample_songs):
            for j, song2 in enumerate(sample_songs[i+1:], i+1):
                # Get similarity
                similarity = self._get_similarity(song1["title"], song2["title"])
                
                # Analyze feature differences
                features = self._compare_features(song1, song2)
                
                # Weight by similarity
                for feature, diff_score in features.items():
                    importance[feature] += diff_score * (1 - similarity)
        
        # Normalize
        total = sum(importance.values())
        if total > 0:
            importance = {k: v/total for k, v in importance.items()}
        
        return importance
    
    def _get_similarity(self, title1: str, title2: str) -> float:
        """Get embedding similarity between two songs"""
        if title1 not in self.trainer.song_embeddings or title2 not in self.trainer.song_embeddings:
            return 0.0
        
        emb1 = self.trainer.song_embeddings[title1]
        emb2 = self.trainer.song_embeddings[title2]
        
        return np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
    
    def _compare_features(self, song1: Dict[str, Any], song2: Dict[str, Any]) -> Dict[str, float]:
        """Compare features between two songs"""
        features = {}
        
        # Genre difference
        genres1 = set(song1.get("genres", []))
        genres2 = set(song2.get("genres", []))
        features["genres"] = len(genres1.symmetric_difference(genres2)) / max(len(genres1.union(genres2)), 1)
        
        # Artist difference
        artists1 = set(song1.get("artists", []))
        artists2 = set(song2.get("artists", []))
        features["artists"] = len(artists1.symmetric_difference(artists2)) / max(len(artists1.union(artists2)), 1)
        
        # Era difference
        era1 = self._get_era(song1)
        era2 = self._get_era(song2)
        features["era"] = 0.0 if era1 == era2 else 1.0
        
        # Country difference
        country1 = song1.get("country")
        country2 = song2.get("country")
        features["country"] = 0.0 if country1 == country2 else 1.0
        
        # Duration difference
        duration1 = song1.get("duration", 0)
        duration2 = song2.get("duration", 0)
        if duration1 and duration2:
            features["duration"] = abs(duration1 - duration2) / max(duration1, duration2)
        
        return features
    
    def _get_era(self, song: Dict[str, Any]) -> Optional[str]:
        """Extract era from song"""
        pub_date = song.get("publication_date")
        if pub_date and isinstance(pub_date, str) and len(pub_date) >= 4:
            try:
                year = int(pub_date[:4])
                if year < 1990:
                    return "classic"
                elif year < 2000:
                    return "90s"
                elif year < 2010:
                    return "2000s"
                else:
                    return "2010s"
            except ValueError:
                pass
        return None
    
    def generate_smart_question(self, candidate_songs: List[str], asked_questions: set) -> Optional[Dict[str, Any]]:
        """Generate the most informative question based on embeddings"""
        if len(candidate_songs) <= 1:
            return None
        
        # Find the best feature to split the candidates
        best_question = None
        best_score = -1
        
        # Analyze candidates to find distinguishing features
        candidates_data = [self.songs[self.title_to_idx[title]] for title in candidate_songs]
        
        # Try different question types
        question_candidates = self._generate_question_candidates(candidates_data, asked_questions)
        
        for question in question_candidates:
            # Calculate how well this question splits the candidates
            score = self._evaluate_question_split(question, candidate_songs)
            
            if score > best_score:
                best_score = score
                best_question = question
        
        return best_question
    
    def _generate_question_candidates(self, candidates_data: List[Dict[str, Any]], asked_questions: set) -> List[Dict[str, Any]]:
        """Generate potential questions for the candidates"""
        questions = []
        
        # Genre questions
        genre_counts = defaultdict(int)
        for song in candidates_data:
            for genre in song.get("genres", []):
                genre_counts[genre] += 1
        
        for genre, count in genre_counts.items():
            if 0.3 <= count / len(candidates_data) <= 0.7:  # Balanced split
                key = ("genres", genre)
                if key not in asked_questions:
                    questions.append({
                        "feature": "genres",
                        "value": genre,
                        "text": f"Is it a {genre} song?",
                        "split_score": abs(count / len(candidates_data) - 0.5),
                        "importance": self.feature_importance.get("genres", 0.2)
                    })
        
        # Era questions
        era_counts = defaultdict(int)
        for song in candidates_data:
            era = self._get_era(song)
            if era:
                era_counts[era] += 1
        
        for era, count in era_counts.items():
            if 0.3 <= count / len(candidates_data) <= 0.7:
                key = ("era", era)
                if key not in asked_questions:
                    questions.append({
                        "feature": "era",
                        "value": era,
                        "text": f"Is it from the {era}?",
                        "split_score": abs(count / len(candidates_data) - 0.5),
                        "importance": self.feature_importance.get("era", 0.15)
                    })
        
        # Artist questions (only for popular artists)
        artist_counts = defaultdict(int)
        for song in candidates_data:
            for artist in song.get("artists", []):
                artist_counts[artist] += 1
        
        for artist, count in artist_counts.items():
            if 0.2 <= count / len(candidates_data) <= 0.8:  # Broader range for artists
                key = ("artists", artist)
                if key not in asked_questions:
                    questions.append({
                        "feature": "artists",
                        "value": artist,
                        "text": f"Is it by {artist}?",
                        "split_score": abs(count / len(candidates_data) - 0.5),
                        "importance": self.feature_importance.get("artists", 0.1)
                    })
        
        # Duration questions
        durations = [song.get("duration", 0) for song in candidates_data if song.get("duration")]
        if durations:
            avg_duration = sum(durations) / len(durations)
            key = ("duration", "long")
            if key not in asked_questions:
                questions.append({
                    "feature": "duration",
                    "value": "long",
                    "text": f"Is it longer than {int(avg_duration)} seconds?",
                    "split_score": 0.3,  # Fixed score
                    "importance": self.feature_importance.get("duration", 0.05)
                })
        
        return questions
    
    def _evaluate_question_split(self, question: Dict[str, Any], candidate_songs: List[str]) -> float:
        """Evaluate how well a question splits the candidates using embeddings"""
        feature = question["feature"]
        value = question["value"]
        
        # Split candidates based on the question
        yes_candidates = []
        no_candidates = []
        
        for title in candidate_songs:
            song = self.songs[self.title_to_idx[title]]
            has_feature = self._song_has_feature(song, feature, value)
            
            if has_feature:
                yes_candidates.append(title)
            else:
                no_candidates.append(title)
        
        # Calculate embedding-based split quality
        if len(yes_candidates) == 0 or len(no_candidates) == 0:
            return 0.0
        
        # Average similarity within groups vs between groups
        yes_similarity = self._average_group_similarity(yes_candidates)
        no_similarity = self._average_group_similarity(no_candidates)
        between_similarity = self._average_cross_similarity(yes_candidates, no_candidates)
        
        # Good split: high within-group similarity, low between-group similarity
        split_quality = (yes_similarity + no_similarity) / 2 - between_similarity
        
        # Weight by feature importance and split balance
        balance_score = 1 - abs(len(yes_candidates) - len(no_candidates)) / len(candidate_songs)
        
        final_score = split_quality * balance_score * question["importance"]
        
        return final_score
    
    def _song_has_feature(self, song: Dict[str, Any], feature: str, value: str) -> bool:
        """Check if a song has a specific feature value"""
        if feature == "genres":
            return value in song.get("genres", [])
        elif feature == "artists":
            return value in song.get("artists", [])
        elif feature == "era":
            return self._get_era(song) == value
        elif feature == "duration":
            if value == "long":
                duration = song.get("duration", 0)
                return duration > 240  # Longer than 4 minutes
        return False
    
    def _average_group_similarity(self, songs: List[str]) -> float:
        """Calculate average similarity within a group of songs"""
        if len(songs) <= 1:
            return 1.0
        
        similarities = []
        for i, song1 in enumerate(songs):
            for song2 in songs[i+1:]:
                sim = self._get_similarity(song1, song2)
                similarities.append(sim)
        
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    def _average_cross_similarity(self, group1: List[str], group2: List[str]) -> float:
        """Calculate average similarity between two groups"""
        similarities = []
        
        for song1 in group1:
            for song2 in group2:
                sim = self._get_similarity(song1, song2)
                similarities.append(sim)
        
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    def explain_embedding_similarity(self, song1: str, song2: str) -> Dict[str, Any]:
        """Explain why two songs are considered similar based on embeddings"""
        similarity = self._get_similarity(song1, song2)
        
        if song1 not in self.title_to_idx or song2 not in self.title_to_idx:
            return {"similarity": similarity, "explanation": "One or both songs not found"}
        
        s1_data = self.songs[self.title_to_idx[song1]]
        s2_data = self.songs[self.title_to_idx[song2]]
        
        # Find common features
        common_features = []
        feature_diffs = self._compare_features(s1_data, s2_data)
        
        for feature, diff_score in feature_diffs.items():
            if diff_score < 0.3:  # Low difference = similar
                if feature == "genres":
                    common_genres = set(s1_data.get("genres", [])) & set(s2_data.get("genres", []))
                    if common_genres:
                        common_features.append(f"Both are {', '.join(common_genres)}")
                elif feature == "era":
                    era = self._get_era(s1_data)
                    if era and era == self._get_era(s2_data):
                        common_features.append(f"Both from the {era}")
                elif feature == "artists":
                    common_artists = set(s1_data.get("artists", [])) & set(s2_data.get("artists", []))
                    if common_artists:
                        common_features.append(f"Both feature {', '.join(common_artists)}")
        
        return {
            "similarity": similarity,
            "common_features": common_features,
            "explanation": f"Similarity: {similarity:.3f}. " + (". ".join(common_features) if common_features else "Different genres but similar neural patterns")
        }
