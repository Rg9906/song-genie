"""
System Evaluation Metrics
Comprehensive evaluation and simulation of Music Akenator performance
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Any, Tuple, Optional
import logging
from collections import defaultdict
import random
import time

logger = logging.getLogger(__name__)

class GameSimulator:
    """Simulate Music Akenator games to evaluate performance"""
    
    def __init__(self, songs: List[Dict[str, Any]], hybrid_engine):
        self.songs = songs
        self.hybrid_engine = hybrid_engine
        self.evaluation_results = []
        
    def simulate_games(self, num_games: int = 100, max_questions: int = 20) -> Dict[str, Any]:
        """Simulate multiple games and collect metrics"""
        logger.info(f"🎮 Simulating {num_games} games...")
        
        results = {
            'games': [],
            'metrics': {
                'avg_questions': 0,
                'avg_confidence': 0,
                'success_rate': 0,
                'entropy_reduction': [],
                'question_effectiveness': defaultdict(list),
                'feature_usage': defaultdict(int)
            }
        }
        
        for game_id in range(num_games):
            game_result = self._simulate_single_game(game_id, max_questions)
            results['games'].append(game_result)
            
            # Update aggregate metrics
            results['metrics']['avg_questions'] += game_result['questions_asked']
            results['metrics']['avg_confidence'] += game_result['final_confidence']
            
            if game_result['success']:
                results['metrics']['success_rate'] += 1
            
            # Track entropy reduction
            if game_result['entropy_reductions']:
                results['metrics']['entropy_reduction'].extend(game_result['entropy_reductions'])
            
            # Track question effectiveness
            for question in game_result['questions']:
                feature = question['feature']
                effectiveness = question.get('effectiveness', 0)
                results['metrics']['question_effectiveness'][feature].append(effectiveness)
                results['metrics']['feature_usage'][feature] += 1
        
        # Calculate averages
        total_games = num_games
        results['metrics']['avg_questions'] /= total_games
        results['metrics']['avg_confidence'] /= total_games
        results['metrics']['success_rate'] /= total_games
        
        logger.info(f"✅ Completed {num_games} game simulations")
        return results
    
    def _simulate_single_game(self, game_id: int, max_questions: int) -> Dict[str, Any]:
        """Simulate a single game"""
        # Randomly select target song
        target_song = random.choice(self.songs)
        target_id = target_song['id']
        
        # Reset engine
        self.hybrid_engine.beliefs = self.hybrid_engine._initialize_beliefs()
        asked_questions = set()
        questions_asked = []
        entropy_reductions = []
        
        game_result = {
            'game_id': game_id,
            'target_song': target_song,
            'target_id': target_id,
            'success': False,
            'questions_asked': 0,
            'final_confidence': 0,
            'questions': [],
            'entropy_reductions': [],
            'guess_correct': False
        }
        
        # Simulate question-answer loop
        for question_num in range(max_questions):
            # Get initial entropy
            candidates = [
                song for song in self.songs 
                if self.hybrid_engine.beliefs.get(song['id'], 0) > 1e-6
            ]
            initial_entropy = self._calculate_entropy(candidates)
            
            # Get best question
            question = self.hybrid_engine.get_best_question(asked_questions)
            if not question:
                break
            
            # Simulate answer
            answer = self._simulate_answer(target_song, question)
            
            # Calculate effectiveness (how well question reduced candidates)
            new_candidates = [
                song for song in candidates 
                if self._song_matches_answer(song, question, answer)
            ]
            final_entropy = self._calculate_entropy(new_candidates)
            entropy_reduction = initial_entropy - final_entropy
            entropy_reductions.append(entropy_reduction)
            
            # Record question
            question['answer'] = answer
            question['entropy_reduction'] = entropy_reduction
            question['effectiveness'] = entropy_reduction
            questions_asked.append(question)
            
            # Update beliefs
            self.hybrid_engine.update_beliefs(question, answer)
            asked_questions.add((question['feature'], question['value']))
            
            game_result['questions_asked'] += 1
            
            # Check if engine should make guess
            should_guess, guess_id = self.hybrid_engine.should_make_guess(
                game_result['questions_asked']
            )
            
            if should_guess:
                # Evaluate guess
                game_result['guess_correct'] = (guess_id == target_id)
                game_result['success'] = game_result['guess_correct']
                
                # Get final confidence
                final_confidence, _ = self.hybrid_engine.get_confidence(guess_id)
                game_result['final_confidence'] = final_confidence
                
                break
        
        game_result['questions'] = questions_asked
        game_result['entropy_reductions'] = entropy_reductions
        
        return game_result
    
    def _simulate_answer(self, target_song: Dict[str, Any], question: Dict[str, Any]) -> str:
        """Simulate user answer for target song and question"""
        feature = question['feature']
        value = question['value']
        
        # Check if target song matches the question
        if self._song_matches_attribute(target_song, feature, value):
            # Add some noise to make it realistic
            if random.random() < 0.95:  # 95% accuracy
                return 'yes'
            else:
                return 'no'
        else:
            if random.random() < 0.95:  # 95% accuracy
                return 'no'
            else:
                return 'yes'
    
    def _song_matches_answer(self, song: Dict[str, Any], question: Dict[str, Any], answer: str) -> bool:
        """Check if song matches the answer to question"""
        feature = question['feature']
        value = question['value']
        
        matches = self._song_matches_attribute(song, feature, value)
        return (matches and answer.lower() in ['yes', 'y', 'true']) or \
               (not matches and answer.lower() in ['no', 'n', 'false'])
    
    def _song_matches_attribute(self, song: Dict[str, Any], attribute: str, value: str) -> bool:
        """Check if song matches attribute value"""
        song_attributes = self._extract_song_attributes(song)
        
        if attribute not in song_attributes:
            return False
        
        return value in song_attributes[attribute]
    
    def _extract_song_attributes(self, song: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract all meaningful attributes from song"""
        attributes = {}
        
        # Basic attributes
        for attr in ['genres', 'artists', 'country', 'language']:
            values = song.get(attr, [])
            if isinstance(values, list):
                attributes[attr] = values
            elif values:
                attributes[attr] = [str(values)]
        
        # Derived attributes
        if 'release_year' in song:
            year = song['release_year']
            attributes['decade'] = [f"{(year // 10) * 10}s"]
            attributes['era'] = [self._get_era(year)]
        
        # Boolean attributes
        boolean_attrs = ['is_collaboration', 'is_soundtrack', 'is_viral_hit']
        for attr in boolean_attrs:
            if attr in song:
                attributes[attr] = [str(song[attr])]
        
        return attributes
    
    def _calculate_entropy(self, songs: List[Dict[str, Any]]) -> float:
        """Calculate entropy of song distribution"""
        if not songs:
            return 0.0
        
        # Uniform distribution entropy
        total = len(songs)
        if total <= 1:
            return 0.0
        
        return np.log2(total)
    
    def _get_era(self, year: int) -> str:
        """Get era from year"""
        if year < 1960:
            return "Classic Era"
        elif year < 1970:
            return "60s Era"
        elif year < 1980:
            return "70s Era"
        elif year < 1990:
            return "80s Era"
        elif year < 2000:
            return "90s Era"
        elif year < 2010:
            return "2000s Era"
        else:
            return "2010s+ Era"


class EmbeddingEvaluator:
    """Evaluate embedding quality and similarity"""
    
    def __init__(self, embedding_trainer):
        self.embedding_trainer = embedding_trainer
    
    def evaluate_embedding_quality(self, songs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate embedding quality using various metrics"""
        logger.info("🔍 Evaluating embedding quality...")
        
        if not self.embedding_trainer or not hasattr(self.embedding_trainer, 'embeddings'):
            return {'error': 'No embeddings available'}
        
        embeddings = self.embedding_trainer.embeddings
        
        metrics = {
            'intra_cluster_similarity': self._calculate_intra_cluster_similarity(songs, embeddings),
            'inter_cluster_distance': self._calculate_inter_cluster_distance(songs, embeddings),
            'genre_separation': self._calculate_genre_separation(songs, embeddings),
            'nearest_neighbor_accuracy': self._calculate_nearest_neighbor_accuracy(songs, embeddings),
            'embedding_statistics': self._get_embedding_statistics(embeddings)
        }
        
        logger.info("✅ Embedding evaluation completed")
        return metrics
    
    def _calculate_intra_cluster_similarity(self, songs: List[Dict[str, Any]], 
                                      embeddings: np.ndarray) -> float:
        """Calculate average similarity within genre clusters"""
        genre_to_songs = defaultdict(list)
        
        for song, embedding in zip(songs, embeddings):
            genres = song.get('genres', [])
            if genres:
                primary_genre = genres[0]
                genre_to_songs[primary_genre].append((song, embedding))
        
        similarities = []
        for genre, song_embeddings in genre_to_songs.items():
            if len(song_embeddings) < 2:
                continue
            
            # Calculate pairwise similarities within genre
            genre_similarities = []
            for i in range(len(song_embeddings)):
                for j in range(i + 1, len(song_embeddings)):
                    emb1 = song_embeddings[i][1]
                    emb2 = song_embeddings[j][1]
                    similarity = self._cosine_similarity(emb1, emb2)
                    genre_similarities.append(similarity)
            
            if genre_similarities:
                similarities.append(np.mean(genre_similarities))
        
        return np.mean(similarities) if similarities else 0.0
    
    def _calculate_inter_cluster_distance(self, songs: List[Dict[str, Any]], 
                                     embeddings: np.ndarray) -> float:
        """Calculate average distance between different genre clusters"""
        genre_centroids = {}
        
        # Calculate genre centroids
        for song, embedding in zip(songs, embeddings):
            genres = song.get('genres', [])
            if genres:
                primary_genre = genres[0]
                if primary_genre not in genre_centroids:
                    genre_centroids[primary_genre] = []
                genre_centroids[primary_genre].append(embedding)
        
        # Calculate centroids
        for genre in genre_centroids:
            genre_centroids[genre] = np.mean(genre_centroids[genre], axis=0)
        
        # Calculate distances between centroids
        distances = []
        genre_list = list(genre_centroids.keys())
        
        for i in range(len(genre_list)):
            for j in range(i + 1, len(genre_list)):
                centroid1 = genre_centroids[genre_list[i]]
                centroid2 = genre_centroids[genre_list[j]]
                distance = 1 - self._cosine_similarity(centroid1, centroid2)
                distances.append(distance)
        
        return np.mean(distances) if distances else 0.0
    
    def _calculate_genre_separation(self, songs: List[Dict[str, Any]], 
                               embeddings: np.ndarray) -> Dict[str, float]:
        """Calculate how well embeddings separate different genres"""
        genre_to_embeddings = defaultdict(list)
        
        for song, embedding in zip(songs, embeddings):
            genres = song.get('genres', [])
            if genres:
                primary_genre = genres[0]
                genre_to_embeddings[primary_genre].append(embedding)
        
        separation_scores = {}
        
        for genre1, embeddings1 in genre_to_embeddings.items():
            for genre2, embeddings2 in genre_to_embeddings.items():
                if genre1 == genre2:
                    continue
                
                # Calculate average cross-similarity
                cross_similarities = []
                for emb1 in embeddings1:
                    for emb2 in embeddings2:
                        similarity = self._cosine_similarity(emb1, emb2)
                        cross_similarities.append(similarity)
                
                if cross_similarities:
                    key = f"{genre1}_vs_{genre2}"
                    separation_scores[key] = np.mean(cross_similarities)
        
        return separation_scores
    
    def _calculate_nearest_neighbor_accuracy(self, songs: List[Dict[str, Any]], 
                                       embeddings: np.ndarray) -> float:
        """Calculate nearest neighbor classification accuracy"""
        correct_predictions = 0
        total_predictions = 0
        
        for i, (song, embedding) in enumerate(zip(songs, embeddings)):
            # Find nearest neighbors (excluding self)
            similarities = []
            for j, other_embedding in enumerate(embeddings):
                if i != j:
                    similarity = self._cosine_similarity(embedding, other_embedding)
                    similarities.append((j, similarity))
            
            if similarities:
                # Sort by similarity and get top neighbors
                similarities.sort(key=lambda x: x[1], reverse=True)
                top_k = 5
                
                # Check if any top-k neighbors share genre
                song_genres = set(song.get('genres', []))
                neighbor_genres = set()
                
                for neighbor_idx, _ in similarities[:top_k]:
                    neighbor_song = songs[neighbor_idx]
                    neighbor_genres = set(neighbor_song.get('genres', []))
                    neighbor_genres.update(neighbor_genres)
                
                # Correct if genres overlap
                if song_genres.intersection(neighbor_genres):
                    correct_predictions += 1
                
                total_predictions += 1
        
        return correct_predictions / total_predictions if total_predictions > 0 else 0.0
    
    def _get_embedding_statistics(self, embeddings: np.ndarray) -> Dict[str, float]:
        """Get basic statistics about embeddings"""
        return {
            'mean_norm': np.mean(np.linalg.norm(embeddings, axis=1)),
            'std_norm': np.std(np.linalg.norm(embeddings, axis=1)),
            'mean_value': np.mean(embeddings),
            'std_value': np.std(embeddings),
            'min_value': np.min(embeddings),
            'max_value': np.max(embeddings),
            'sparsity': np.mean(embeddings == 0.0),
            'dimension': embeddings.shape[1] if len(embeddings.shape) > 1 else 0
        }
    
    def _cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between embeddings"""
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)


class SystemEvaluator:
    """Comprehensive system evaluation"""
    
    def __init__(self, songs: List[Dict[str, Any]], hybrid_engine, embedding_trainer=None):
        self.songs = songs
        self.hybrid_engine = hybrid_engine
        self.embedding_trainer = embedding_trainer
        
    def run_comprehensive_evaluation(self, num_games: int = 100) -> Dict[str, Any]:
        """Run comprehensive system evaluation"""
        logger.info("🚀 Starting comprehensive system evaluation...")
        
        results = {
            'dataset_stats': self._get_dataset_statistics(),
            'game_simulation': self._run_game_simulation(num_games),
            'embedding_quality': self._evaluate_embeddings(),
            'performance_metrics': self._calculate_performance_metrics(),
            'recommendations': self._generate_recommendations()
        }
        
        logger.info("✅ Comprehensive evaluation completed")
        return results
    
    def _get_dataset_statistics(self) -> Dict[str, Any]:
        """Get comprehensive dataset statistics"""
        stats = {
            'total_songs': len(self.songs),
            'unique_artists': len(set(artist for song in self.songs for artist in song.get('artists', []))),
            'unique_genres': len(set(genre for song in self.songs for genre in song.get('genres', []))),
            'year_range': self._get_year_range(),
            'attribute_coverage': self._get_attribute_coverage(),
            'data_quality': self._assess_data_quality()
        }
        
        return stats
    
    def _run_game_simulation(self, num_games: int) -> Dict[str, Any]:
        """Run game simulation"""
        simulator = GameSimulator(self.songs, self.hybrid_engine)
        return simulator.simulate_games(num_games)
    
    def _evaluate_embeddings(self) -> Dict[str, Any]:
        """Evaluate embedding quality"""
        if not self.embedding_trainer:
            return {'status': 'No embeddings available'}
        
        evaluator = EmbeddingEvaluator(self.embedding_trainer)
        return evaluator.evaluate_embedding_quality(self.songs)
    
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate system performance metrics"""
        return {
            'graph_intelligence_available': self.hybrid_engine.graph_intelligence is not None,
            'embeddings_available': self.hybrid_engine.embedding_trainer is not None,
            'hybrid_weighting': {
                'graph_weight': getattr(self.hybrid_engine, 'graph_weight', 0.6),
                'embedding_weight': getattr(self.hybrid_engine, 'embedding_weight', 0.4)
            },
            'system_status': self.hybrid_engine.get_system_status() if hasattr(self.hybrid_engine, 'get_system_status') else {}
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        # Analyze game simulation results
        simulator = GameSimulator(self.songs, self.hybrid_engine)
        sim_results = simulator.simulate_games(50)  # Quick simulation
        
        if sim_results['metrics']['avg_questions'] > 15:
            recommendations.append("Consider improving question selection to reduce average questions")
        
        if sim_results['metrics']['success_rate'] < 0.7:
            recommendations.append("Improve feature extraction and belief updates")
        
        # Check dataset size
        if len(self.songs) < 200:
            recommendations.append("Expand dataset to at least 200 songs for better evaluation")
        
        # Check embedding availability
        if not self.embedding_trainer:
            recommendations.append("Implement neural embeddings for better semantic understanding")
        
        # Check graph intelligence
        if not self.hybrid_engine.graph_intelligence:
            recommendations.append("Implement graph intelligence for better attribute reasoning")
        
        return recommendations
    
    def _get_year_range(self) -> Dict[str, Any]:
        """Get year range statistics"""
        years = []
        for song in self.songs:
            if 'release_year' in song:
                years.append(song['release_year'])
        
        if not years:
            return {'range': 'No year data'}
        
        return {
            'min': min(years),
            'max': max(years),
            'range': max(years) - min(years),
            'avg': np.mean(years)
        }
    
    def _get_attribute_coverage(self) -> Dict[str, float]:
        """Get coverage statistics for key attributes"""
        attributes = ['genres', 'artists', 'country', 'release_year', 'duration', 'bpm']
        coverage = {}
        
        for attr in attributes:
            count = sum(1 for song in self.songs if attr in song and song[attr])
            coverage[attr] = count / len(self.songs)
        
        return coverage
    
    def _assess_data_quality(self) -> Dict[str, Any]:
        """Assess overall data quality"""
        quality_metrics = {
            'complete_songs': 0,
            'missing_attributes': defaultdict(int),
            'inconsistent_formats': 0
        }
        
        for song in self.songs:
            # Check for required attributes
            required_attrs = ['title', 'artists', 'genres']
            missing = [attr for attr in required_attrs if not song.get(attr)]
            
            if not missing:
                quality_metrics['complete_songs'] += 1
            else:
                for attr in missing:
                    quality_metrics['missing_attributes'][attr] += 1
        
        quality_metrics['completeness_rate'] = quality_metrics['complete_songs'] / len(self.songs)
        
        return quality_metrics
    
    def generate_evaluation_report(self, results: Dict[str, Any], output_file: str = "evaluation_report.md"):
        """Generate comprehensive evaluation report"""
        report = f"""# Music Akenator System Evaluation Report

## Dataset Statistics
- Total Songs: {results['dataset_stats']['total_songs']}
- Unique Artists: {results['dataset_stats']['unique_artists']}
- Unique Genres: {results['dataset_stats']['unique_genres']}
- Year Range: {results['dataset_stats']['year_range'].get('min', 'N/A')} - {results['dataset_stats']['year_range'].get('max', 'N/A')}
- Data Completeness: {results['dataset_stats']['data_quality']['completeness_rate']:.2%}

## Game Simulation Results
- Average Questions per Game: {results['game_simulation']['metrics']['avg_questions']:.2f}
- Success Rate: {results['game_simulation']['metrics']['success_rate']:.2%}
- Average Final Confidence: {results['game_simulation']['metrics']['avg_confidence']:.2f}

## Embedding Quality
{self._format_embedding_results(results['embedding_quality'])}

## Performance Metrics
- Graph Intelligence: {'Available' if results['performance_metrics']['graph_intelligence_available'] else 'Not Available'}
- Neural Embeddings: {'Available' if results['performance_metrics']['embeddings_available'] else 'Not Available'}
- Hybrid Weights: Graph={results['performance_metrics']['hybrid_weighting']['graph_weight']}, Embeddings={results['performance_metrics']['hybrid_weighting']['embedding_weight']}

## Recommendations
{chr(10).join(f"- {rec}" for rec in results['recommendations'])}

---
*Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        with open(output_file, 'w') as f:
            f.write(report)
        
        logger.info(f"📄 Evaluation report saved to {output_file}")
    
    def _format_embedding_results(self, embedding_results: Dict[str, Any]) -> str:
        """Format embedding results for report"""
        if 'error' in embedding_results:
            return f"- Embeddings: {embedding_results['error']}"
        
        return f"""- Intra-Cluster Similarity: {embedding_results.get('intra_cluster_similarity', 0):.3f}
- Inter-Cluster Distance: {embedding_results.get('inter_cluster_distance', 0):.3f}
- Nearest Neighbor Accuracy: {embedding_results.get('nearest_neighbor_accuracy', 0):.3f}"""


def create_system_evaluator(songs: List[Dict[str, Any]], hybrid_engine, embedding_trainer=None) -> SystemEvaluator:
    """Factory function to create system evaluator"""
    return SystemEvaluator(songs, hybrid_engine, embedding_trainer)
