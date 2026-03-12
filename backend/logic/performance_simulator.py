"""
Performance Simulator for Music Akenator
Comprehensive testing of question selection and game performance
"""

import random
import time
import logging
from typing import List, Dict, Any, Tuple
import numpy as np
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

class PerformanceSimulator:
    """Simulate Music Akenator games to measure performance"""
    
    def __init__(self, akenator):
        self.akenator = akenator
        self.simulation_results = []
        
    def run_comprehensive_simulation(self, num_games: int = 100) -> Dict[str, Any]:
        """Run comprehensive simulation with detailed metrics"""
        logger.info(f"🎮 Running {num_games} game simulations...")
        
        results = {
            'games': [],
            'metrics': self._initialize_metrics(),
            'question_analysis': defaultdict(list),
            'performance_tracking': []
        }
        
        for game_id in range(num_games):
            game_result = self._simulate_single_game(game_id)
            results['games'].append(game_result)
            
            # Update aggregate metrics
            self._update_aggregate_metrics(results['metrics'], game_result)
            
            # Track question effectiveness
            for question in game_result['questions']:
                feature = question['feature']
                results['question_analysis'][feature].append(question['effectiveness'])
        
        # Calculate final metrics
        self._calculate_final_metrics(results)
        
        logger.info(f"✅ Completed {num_games} game simulations")
        return results
    
    def _initialize_metrics(self) -> Dict[str, Any]:
        """Initialize metrics tracking"""
        return {
            'total_games': 0,
            'successful_guesses': 0,
            'total_questions_asked': 0,
            'avg_questions_per_game': 0,
            'success_rate': 0,
            'avg_confidence': 0,
            'entropy_reductions': [],
            'candidate_reductions': [],
            'question_diversity': 0,
            'feature_usage': defaultdict(int),
            'avg_time_per_question': 0,
            'avg_time_per_game': 0
        }
    
    def _simulate_single_game(self, game_id: int) -> Dict[str, Any]:
        """Simulate a single game with detailed tracking"""
        # Select random target song
        target_song = random.choice(self.akenator.songs)
        target_id = target_song['id']
        
        # Reset beliefs
        self.akenator.beliefs = {song['id']: 1.0/len(self.akenator.songs) for song in self.akenator.songs}
        
        game_result = {
            'game_id': game_id,
            'target_song': target_song,
            'target_id': target_id,
            'success': False,
            'questions_asked': 0,
            'final_confidence': 0,
            'questions': [],
            'start_time': time.time(),
            'end_time': None,
            'question_times': [],
            'entropy_reductions': [],
            'candidate_reductions': []
        }
        
        asked_questions = set()
        max_questions = 20
        
        # Simulate question-answer loop
        for question_num in range(max_questions):
            # Measure question selection time
            q_start = time.time()
            question = self.akenator.get_best_question(asked_questions)
            q_time = time.time() - q_start
            
            if not question:
                break
            
            # Simulate user answer
            answer = self._simulate_answer(target_song, question)
            
            # Calculate effectiveness metrics
            effectiveness = self._calculate_question_effectiveness(
                question, answer, self.akenator.beliefs
            )
            
            # Record question
            question_record = {
                'feature': question['feature'],
                'value': question['value'],
                'text': question['text'],
                'answer': answer,
                'effectiveness': effectiveness,
                'selection_time': q_time,
                'candidates_before': len([b for b in self.akenator.beliefs.values() if b > 1e-6])
            }
            
            # Update beliefs
            self.akenator.update_beliefs(question, answer)
            asked_questions.add((question['feature'], question['value']))
            
            # Calculate metrics after update
            candidates_after = len([b for b in self.akenator.beliefs.values() if b > 1e-6])
            question_record['candidates_after'] = candidates_after
            question_record['candidate_reduction'] = (question_record['candidates_before'] - candidates_after) / question_record['candidates_before'] if question_record['candidates_before'] > 0 else 0
            
            game_result['questions'].append(question_record)
            game_result['question_times'].append(q_time)
            game_result['candidate_reductions'].append(question_record['candidate_reduction'])
            game_result['questions_asked'] += 1
            
            # Check if should make guess
            should_guess, guess_id = self.akenator.should_make_guess(game_result['questions_asked'])
            
            if should_guess:
                game_result['guess_correct'] = (guess_id == target_id)
                game_result['success'] = game_result['guess_correct']
                
                # Get final confidence
                confidence, explanation = self.akenator.get_confidence(guess_id)
                game_result['final_confidence'] = confidence
                game_result['confidence_explanation'] = explanation
                
                break
        
        game_result['end_time'] = time.time()
        game_result['total_time'] = game_result['end_time'] - game_result['start_time']
        
        return game_result
    
    def _simulate_answer(self, target_song: Dict[str, Any], question: Dict[str, Any]) -> str:
        """Simulate realistic user answer"""
        feature = question['feature']
        value = question['value']
        
        # Check if target song matches
        matches = self._song_matches_attribute(target_song, feature, value)
        
        # Add noise for realism (95% accuracy)
        if random.random() < 0.95:
            return 'yes' if matches else 'no'
        else:
            return 'no' if matches else 'yes'
    
    def _song_matches_attribute(self, song: Dict[str, Any], attribute: str, value: str) -> bool:
        """Check if song matches attribute value"""
        song_value = song.get(attribute)
        
        if isinstance(song_value, list):
            return value in song_value
        else:
            return str(song_value) == value
    
    def _calculate_question_effectiveness(self, question: Dict[str, Any], 
                                        answer: str, beliefs_before: Dict[int, float]) -> float:
        """Calculate how effective a question was at reducing uncertainty"""
        # This would be calculated after beliefs are updated
        # For now, return a placeholder based on question type
        feature_weights = {
            'genres': 0.8,
            'artists': 0.7,
            'decade': 0.6,
            'era': 0.5
        }
        return feature_weights.get(question['feature'], 0.5)
    
    def _update_aggregate_metrics(self, metrics: Dict[str, Any], game_result: Dict[str, Any]):
        """Update aggregate metrics with game result"""
        metrics['total_games'] += 1
        metrics['total_questions_asked'] += game_result['questions_asked']
        
        if game_result['success']:
            metrics['successful_guesses'] += 1
        
        metrics['avg_confidence'] += game_result['final_confidence']
        metrics['entropy_reductions'].extend(game_result['entropy_reductions'])
        metrics['candidate_reductions'].extend(game_result['candidate_reductions'])
        
        # Track feature usage
        for question in game_result['questions']:
            metrics['feature_usage'][question['feature']] += 1
    
    def _calculate_final_metrics(self, results: Dict[str, Any]):
        """Calculate final aggregate metrics"""
        metrics = results['metrics']
        
        if metrics['total_games'] > 0:
            metrics['success_rate'] = metrics['successful_guesses'] / metrics['total_games']
            metrics['avg_questions_per_game'] = metrics['total_questions_asked'] / metrics['total_games']
            metrics['avg_confidence'] = metrics['avg_confidence'] / metrics['total_games']
        
        # Calculate question diversity
        all_features = []
        for game in results['games']:
            all_features.extend([q['feature'] for q in game['questions']])
        
        if all_features:
            unique_features = len(set(all_features))
            total_features = len(all_features)
            metrics['question_diversity'] = unique_features / total_features
        
        # Calculate average times
        total_time = sum(game['total_time'] for game in results['games'])
        total_q_time = sum(sum(game['question_times']) for game in results['games'])
        total_questions = sum(len(game['questions']) for game in results['games'])
        
        if metrics['total_games'] > 0:
            metrics['avg_time_per_game'] = total_time / metrics['total_games']
        
        if total_questions > 0:
            metrics['avg_time_per_question'] = total_q_time / total_questions
    
    def analyze_question_patterns(self, simulation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze question patterns and effectiveness"""
        question_analysis = simulation_results['question_analysis']
        
        analysis = {
            'feature_effectiveness': {},
            'feature_frequency': {},
            'most_effective_features': [],
            'least_effective_features': []
        }
        
        # Calculate average effectiveness per feature
        for feature, effectiveness_list in question_analysis.items():
            if effectiveness_list:
                avg_effectiveness = np.mean(effectiveness_list)
                analysis['feature_effectiveness'][feature] = avg_effectiveness
                analysis['feature_frequency'][feature] = len(effectiveness_list)
        
        # Sort features by effectiveness
        sorted_features = sorted(
            analysis['feature_effectiveness'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        analysis['most_effective_features'] = sorted_features[:3]
        analysis['least_effective_features'] = sorted_features[-3:] if len(sorted_features) > 3 else []
        
        return analysis
    
    def generate_performance_report(self, simulation_results: Dict[str, Any], 
                                  output_file: str = "PERFORMANCE_REPORT.md"):
        """Generate detailed performance report"""
        metrics = simulation_results['metrics']
        question_analysis = self.analyze_question_patterns(simulation_results)
        
        report = f"""# 🎮 Music Akenator - Performance Simulation Report

**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}  
**Games Simulated**: {metrics['total_games']}

---

## 📊 Overall Performance Metrics

### Success Metrics
- **Success Rate**: {metrics['success_rate']:.1%}
- **Average Questions/Game**: {metrics['avg_questions_per_game']:.1f}
- **Average Final Confidence**: {metrics['avg_confidence']:.3f}

### Efficiency Metrics
- **Average Time/Game**: {metrics['avg_time_per_game']:.3f}s
- **Average Time/Question**: {metrics['avg_time_per_question']:.4f}s
- **Question Diversity**: {metrics['question_diversity']:.1%}

### Candidate Reduction
- **Average Reduction/Question**: {np.mean(metrics['candidate_reductions']):.3f} if metrics['candidate_reductions'] else 'N/A'
- **Total Questions Asked**: {metrics['total_questions_asked']}

---

## ❓ Question Analysis

### Feature Effectiveness
"""
        
        for feature, effectiveness in question_analysis['feature_effectiveness'].items():
            frequency = question_analysis['feature_frequency'][feature]
            report += f"- **{feature}**: {effectiveness:.3f} avg effectiveness ({frequency} uses)\n"
        
        report += f"""
### Most Effective Features
"""
        
        for feature, effectiveness in question_analysis['most_effective_features']:
            report += f"- {feature}: {effectiveness:.3f}\n"
        
        report += f"""
### Feature Usage Distribution
"""
        
        feature_usage = metrics['feature_usage']
        total_usage = sum(feature_usage.values())
        
        for feature, count in sorted(feature_usage.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_usage) * 100 if total_usage > 0 else 0
            report += f"- {feature}: {count} uses ({percentage:.1f}%)\n"
        
        report += f"""
---

## 🎯 Game Performance Distribution

### Questions per Game Distribution
"""
        
        questions_per_game = [game['questions_asked'] for game in simulation_results['games']]
        q_dist = Counter(questions_per_game)
        
        for q_count, games in sorted(q_dist.items()):
            percentage = (games / len(simulation_results['games'])) * 100
            report += f"- {q_count} questions: {games} games ({percentage:.1f}%)\n"
        
        report += f"""
### Success Rate by Questions Asked
"""
        
        success_by_questions = defaultdict(lambda: {'success': 0, 'total': 0})
        
        for game in simulation_results['games']:
            q_count = game['questions_asked']
            success_by_questions[q_count]['total'] += 1
            if game['success']:
                success_by_questions[q_count]['success'] += 1
        
        for q_count in sorted(success_by_questions.keys()):
            stats = success_by_questions[q_count]
            success_rate = (stats['success'] / stats['total']) * 100 if stats['total'] > 0 else 0
            report += f"- {q_count} questions: {success_rate:.1f}% success rate ({stats['success']}/{stats['total']})\n"
        
        report += f"""
---

## 🔍 Detailed Game Analysis

### Sample Successful Games
"""
        
        successful_games = [game for game in simulation_results['games'] if game['success']][:3]
        for game in successful_games:
            report += f"""
**Game {game['game_id']}** - SUCCESS
- Target: {game['target_song']['title']}
- Questions: {game['questions_asked']}
- Final Confidence: {game['final_confidence']:.3f}
- Time: {game['total_time']:.3f}s
"""
        
        report += f"""
### Sample Failed Games
"""
        
        failed_games = [game for game in simulation_results['games'] if not game['success']][:3]
        for game in failed_games:
            report += f"""
**Game {game['game_id']}** - FAILED
- Target: {game['target_song']['title']}
- Questions: {game['questions_asked']}
- Final Confidence: {game['final_confidence']:.3f}
- Time: {game['total_time']:.3f}s
"""
        
        report += f"""
---

## 📈 Performance Recommendations

### Strengths
"""
        
        if metrics['success_rate'] > 0.7:
            report += "- High success rate (>70%)\n"
        if metrics['avg_questions_per_game'] < 10:
            report += "- Efficient question usage (<10 avg questions)\n"
        if metrics['avg_time_per_game'] < 1.0:
            report += "- Fast response time (<1s per game)\n"
        
        report += f"""
### Areas for Improvement
"""
        
        if metrics['success_rate'] < 0.6:
            report += "- Improve success rate (currently <60%)\n"
        if metrics['avg_questions_per_game'] > 15:
            report += "- Reduce average questions per game (currently >15)\n"
        if metrics['question_diversity'] < 0.5:
            report += "- Increase question diversity (currently <50%)\n"
        
        report += f"""
---

## 🎯 Conclusion

The Music Akenator system demonstrates {'excellent' if metrics['success_rate'] > 0.8 else 'good' if metrics['success_rate'] > 0.6 else 'moderate'} performance with:

- **{metrics['success_rate']:.1%} success rate**
- **{metrics['avg_questions_per_game']:.1f} average questions per game**
- **{metrics['avg_time_per_game']:.3f}s average response time**

The system is {'highly effective' if metrics['success_rate'] > 0.8 else 'effective' if metrics['success_rate'] > 0.6 else 'moderately effective'} for music guessing games.

---

*Report generated by Performance Simulator*  
*{time.strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"📄 Performance report saved to {output_file}")


def run_performance_simulation(num_games: int = 100):
    """Main function to run performance simulation"""
    from backend.logic.simple_enhanced import create_simple_enhanced_akenator
    
    akenator = create_simple_enhanced_akenator(100)
    simulator = PerformanceSimulator(akenator)
    results = simulator.run_comprehensive_simulation(num_games)
    simulator.generate_performance_report(results)
    
    return results


if __name__ == "__main__":
    run_performance_simulation(100)
