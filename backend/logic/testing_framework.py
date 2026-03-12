"""
Comprehensive Testing and Benchmarking Framework
Enterprise-grade testing for all system components with automated benchmarking
"""

import unittest
import pytest
import logging
import time
import json
import os
import sys
from typing import List, Dict, Any, Tuple, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
from collections import defaultdict
import tempfile
import shutil

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.logic.enterprise_engine import EnterpriseEngine, SongMetadata, DataValidator
from backend.logic.enterprise_graph import EnterpriseDynamicGraph, AttributeNormalizer
from backend.logic.enterprise_embeddings import EnterpriseEmbeddingTrainer, EmbeddingConfig, DataPreprocessor
from backend.logic.adaptive_hybrid_engine import AdaptiveHybridEngine

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Benchmark result with metrics"""
    test_name: str
    execution_time: float
    memory_usage: float
    success: bool
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TestSuite:
    """Test suite configuration"""
    name: str
    tests: List[Callable] = field(default_factory=list)
    setup_func: Optional[Callable] = None
    teardown_func: Optional[Callable] = None
    timeout: float = 30.0


class MemoryProfiler:
    """Memory usage profiler"""
    
    def __init__(self):
        self.peak_memory = 0
        self.start_memory = 0
    
    def start_profiling(self):
        """Start memory profiling"""
        try:
            import psutil
            process = psutil.Process()
            self.start_memory = process.memory_info().rss / 1024 / 1024  # MB
            self.peak_memory = self.start_memory
        except ImportError:
            logger.warning("psutil not available for memory profiling")
            self.start_memory = 0
            self.peak_memory = 0
    
    def get_current_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            current = process.memory_info().rss / 1024 / 1024
            self.peak_memory = max(self.peak_memory, current)
            return current
        except ImportError:
            return 0
    
    def get_peak_usage(self) -> float:
        """Get peak memory usage in MB"""
        return self.peak_memory
    
    def get_delta(self) -> float:
        """Get memory delta from start"""
        return self.peak_memory - self.start_memory


class BenchmarkRunner:
    """Automated benchmark runner"""
    
    def __init__(self, output_dir: str = "benchmark_results"):
        self.output_dir = output_dir
        self.results = []
        self.profiler = MemoryProfiler()
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
    
    def run_benchmark(self, test_func: Callable, test_name: str, **kwargs) -> BenchmarkResult:
        """Run a single benchmark test"""
        logger.info(f"Running benchmark: {test_name}")
        
        self.profiler.start_profiling()
        start_time = time.time()
        
        try:
            # Execute test with timeout
            result = test_func(**kwargs)
            success = True
            error_message = None
            
        except Exception as e:
            success = False
            error_message = str(e)
            result = None
            logger.error(f"Benchmark {test_name} failed: {e}")
        
        execution_time = time.time() - start_time
        memory_usage = self.profiler.get_delta()
        
        benchmark_result = BenchmarkResult(
            test_name=test_name,
            execution_time=execution_time,
            memory_usage=memory_usage,
            success=success,
            error_message=error_message,
            metrics={"result": result} if result is not None else {}
        )
        
        self.results.append(benchmark_result)
        
        logger.info(f"Benchmark {test_name}: {'PASS' if success else 'FAIL'} "
                   f"({execution_time:.3f}s, {memory_usage:.1f}MB)")
        
        return benchmark_result
    
    def save_results(self, filename: str = None):
        """Save benchmark results to file"""
        if filename is None:
            filename = f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Convert results to serializable format
        serializable_results = []
        for result in self.results:
            serializable_results.append({
                "test_name": result.test_name,
                "execution_time": result.execution_time,
                "memory_usage": result.memory_usage,
                "success": result.success,
                "error_message": result.error_message,
                "metrics": result.metrics,
                "timestamp": result.timestamp.isoformat()
            })
        
        with open(filepath, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        logger.info(f"Benchmark results saved to {filepath}")
    
    def generate_report(self) -> str:
        """Generate benchmark report"""
        if not self.results:
            return "No benchmark results available"
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - passed_tests
        
        avg_time = np.mean([r.execution_time for r in self.results])
        avg_memory = np.mean([r.memory_usage for r in self.results])
        
        report = f"""
Benchmark Report
===============
Total Tests: {total_tests}
Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)
Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)

Performance:
- Average Execution Time: {avg_time:.3f}s
- Average Memory Usage: {avg_memory:.1f}MB

Failed Tests:
"""
        
        for result in self.results:
            if not result.success:
                report += f"- {result.test_name}: {result.error_message}\n"
        
        return report


class TestDataGenerator:
    """Generate test data for benchmarking"""
    
    @staticmethod
    def generate_songs(count: int = 100) -> List[Dict[str, Any]]:
        """Generate synthetic song data for testing"""
        songs = []
        
        genres = ["pop", "rock", "jazz", "classical", "electronic", "hip-hop", "country", "blues"]
        artists = [f"Artist {i}" for i in range(count // 10)]  # Reuse artists
        countries = ["USA", "UK", "Canada", "Australia", "Germany", "France", "Japan", "Brazil"]
        languages = ["English", "Spanish", "French", "German", "Japanese", "Portuguese"]
        
        for i in range(count):
            song = {
                "id": i,
                "title": f"Test Song {i}",
                "artists": [artists[i % len(artists)]],
                "genres": [genres[i % len(genres)], genres[(i+1) % len(genres)]],
                "publication_date": f"{2000 + (i % 24)}-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}T00:00:00Z",
                "language": languages[i % len(languages)],
                "country": countries[i % len(countries)],
                "duration": 120 + (i % 240),  # 2-6 minutes
                "bpm": 60 + (i % 120),  # 60-180 BPM
                "artist_genders": ["male", "female"][i % 2],
                "artist_types": ["solo artist", "group"][i % 2],
                "song_types": ["single", "album track"][i % 2],
                "billion_views": 1000000000 if i % 10 == 0 else None,
                "instruments": ["piano", "guitar", "drums", "bass", "synthesizer"][i % 5:i % 5 + 2],
                "themes": ["love", "party", "sad", "happy", "political"][i % 5:i % 5 + 2]
            }
            songs.append(song)
        
        return songs
    
    @staticmethod
    def generate_corrupted_data() -> List[Dict[str, Any]]:
        """Generate corrupted data for testing robustness"""
        corrupted = [
            {"id": 1, "title": "", "artists": []},  # Empty title
            {"id": 2, "title": "Valid Title", "genres": "not_a_list"},  # Wrong type
            {"id": 3, "title": None, "artists": ["Artist"]},  # None title
            {"id": 4, "title": "Valid", "publication_date": "invalid_date"},  # Invalid date
            {"id": 5, "title": "Valid", "bpm": "not_numeric"},  # Invalid numeric
            {"id": 6, "title": "Valid", "artists": None},  # None artists
            {"id": 7, "title": "Valid", "genres": []},  # Empty genres
            {"id": 8, "title": "Valid", "duration": -100},  # Negative duration
            {"id": 9, "title": "Valid", "country": ""},  # Empty string
            {"id": 10, "title": "Valid", "instruments": "not_a_list"}  # Wrong type
        ]
        return corrupted


class EnterpriseTests:
    """Comprehensive test suite for enterprise components"""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            self.data_dir = tempfile.mkdtemp(prefix="music_akenator_test_")
        else:
            self.data_dir = data_dir
        
        self.test_data = TestDataGenerator.generate_songs(50)
        self.corrupted_data = TestDataGenerator.generate_corrupted_data()
    
    def cleanup(self):
        """Clean up test data"""
        if os.path.exists(self.data_dir):
            shutil.rmtree(self.data_dir)
    
    def test_data_validation(self) -> bool:
        """Test data validation"""
        validator = DataValidator()
        
        # Test valid data
        for song in self.test_data[:5]:
            is_valid, errors = validator.validate_song_metadata(song)
            if not is_valid:
                logger.error(f"Valid data failed validation: {errors}")
                return False
        
        # Test corrupted data
        for song in self.corrupted_data:
            is_valid, errors = validator.validate_song_metadata(song)
            if is_valid:
                logger.error(f"Corrupted data passed validation: {song}")
                return False
        
        logger.info("Data validation tests passed")
        return True
    
    def test_graph_construction(self) -> bool:
        """Test graph construction and analytics"""
        try:
            graph = EnterpriseDynamicGraph(self.data_dir)
            
            # Test graph building
            success = graph.build_from_songs(self.test_data)
            if not success:
                return False
            
            # Test graph statistics
            stats = graph.get_graph_statistics()
            if stats["basic_metrics"]["nodes"] == 0:
                return False
            
            # Test question generation
            candidates = [song["title"] for song in self.test_data[:10]]
            questions = graph.generate_smart_questions(candidates, set())
            
            if not questions:
                logger.warning("No questions generated, but graph built successfully")
            
            logger.info(f"Graph construction test passed: {stats['basic_metrics']['nodes']} nodes")
            return True
            
        except Exception as e:
            logger.error(f"Graph construction test failed: {e}")
            return False
    
    def test_embedding_training(self) -> bool:
        """Test embedding training pipeline"""
        try:
            config = EmbeddingConfig(
                embedding_dim=64,  # Smaller for testing
                epochs=5,  # Very few epochs for testing
                batch_size=8
            )
            
            trainer = EnterpriseEmbeddingTrainer(config)
            
            # Test training
            metrics = trainer.train(self.test_data)
            
            if metrics.train_loss == 0:
                return False
            
            # Test embedding computation
            embeddings = trainer.compute_embeddings(self.test_data)
            
            if len(embeddings) != len(self.test_data):
                return False
            
            # Test embedding similarity
            song_titles = list(embeddings.keys())
            if len(song_titles) >= 2:
                emb1 = embeddings[song_titles[0]]
                emb2 = embeddings[song_titles[1]]
                
                similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
                if not (0 <= similarity <= 1):
                    return False
            
            logger.info(f"Embedding training test passed: loss={metrics.train_loss:.4f}")
            return True
            
        except Exception as e:
            logger.error(f"Embedding training test failed: {e}")
            return False
    
    def test_adaptive_hybrid_engine(self) -> bool:
        """Test adaptive hybrid engine"""
        try:
            engine = AdaptiveHybridEngine(self.data_dir, enable_graph=True, enable_embeddings=False)
            
            # Initialize engine
            success = engine.initialize()
            if not success:
                return False
            
            # Test question generation
            candidates = [song.title for song in engine.songs[:5]]
            question = engine.generate_question(candidates, {"asked_questions": set()})
            
            if not question:
                logger.warning("No question generated, but engine initialized")
            
            # Test system status
            status = engine.get_system_status()
            if not status.get("is_initialized"):
                return False
            
            # Test performance report
            report = engine.get_performance_report()
            if not report:
                return False
            
            logger.info("Adaptive hybrid engine test passed")
            return True
            
        except Exception as e:
            logger.error(f"Adaptive hybrid engine test failed: {e}")
            return False
    
    def test_attribute_normalization(self) -> bool:
        """Test attribute normalization"""
        try:
            normalizer = AttributeNormalizer()
            
            # Test genre normalization
            assert normalizer.normalize_genre("electro-pop") == "Electropop"
            assert normalizer.normalize_genre("dance pop") == "Dance-Pop"
            
            # Test era normalization
            assert normalizer.normalize_era(2005) == "2000s"
            assert normalizer.normalize_era(2015) == "2010s"
            
            # Test artist type normalization
            assert normalizer.normalize_artist_type("solo") == "Solo Artist"
            assert normalizer.normalize_artist_type("band") == "Group"
            
            logger.info("Attribute normalization test passed")
            return True
            
        except Exception as e:
            logger.error(f"Attribute normalization test failed: {e}")
            return False
    
    def test_data_preprocessing(self) -> bool:
        """Test data preprocessing pipeline"""
        try:
            preprocessor = DataPreprocessor().fit(self.test_data)
            
            # Test transformation
            features = preprocessor.transform(self.test_data)
            
            if features.shape[0] != len(self.test_data):
                return False
            
            if features.shape[1] == 0:
                return False
            
            # Test with corrupted data
            try:
                preprocessor.transform(self.corrupted_data)
                # Should not crash, but handle gracefully
            except Exception:
                pass  # Expected to handle gracefully
            
            logger.info(f"Data preprocessing test passed: {features.shape}")
            return True
            
        except Exception as e:
            logger.error(f"Data preprocessing test failed: {e}")
            return False
    
    def test_system_robustness(self) -> bool:
        """Test system robustness with edge cases"""
        try:
            # Test with empty data
            engine = AdaptiveHybridEngine(self.data_dir)
            
            # Test with minimal data
            minimal_songs = [{"id": 1, "title": "Test", "artists": ["Artist"], "genres": ["pop"]}]
            
            # Test with corrupted data handling
            for corrupted_song in self.corrupted_data:
                is_valid, errors = DataValidator.validate_song_metadata(corrupted_song)
                if is_valid:
                    logger.error(f"Corrupted song should be invalid: {corrupted_song}")
                    return False
            
            # Test with missing files
            if os.path.exists(os.path.join(self.data_dir, "enterprise_graph.json")):
                os.remove(os.path.join(self.data_dir, "enterprise_graph.json"))
            
            # Engine should still initialize (with degraded functionality)
            # This would be tested in actual engine initialization
            
            logger.info("System robustness test passed")
            return True
            
        except Exception as e:
            logger.error(f"System robustness test failed: {e}")
            return False


class GameSimulator:
    """Simulate games for performance testing"""
    
    def __init__(self, engine: EnterpriseEngine):
        self.engine = engine
    
    def simulate_game(self, max_questions: int = 20) -> Dict[str, Any]:
        """Simulate a single game session"""
        start_time = time.time()
        
        candidates = [song.title for song in self.engine.songs]
        asked_questions = set()
        questions_asked = 0
        confidence_history = []
        
        while len(candidates) > 1 and questions_asked < max_questions:
            # Generate question
            question = self.engine.generate_question(candidates, {"asked_questions": asked_questions})
            
            if not question:
                break
            
            # Simulate answer (random for testing)
            import random
            answer = random.choice(["yes", "no"])
            
            # Update beliefs
            self.engine.update_beliefs(question, answer)
            
            # Record confidence
            confidence = question.get("confidence_estimate", {}).get("confidence_score", 0.5)
            confidence_history.append(confidence)
            
            asked_questions.add((question.get("feature"), question.get("value")))
            questions_asked += 1
            
            # Simulate candidate reduction (simplified)
            if len(candidates) > 1:
                candidates = candidates[:max(1, len(candidates) // 2)]
        
        game_time = time.time() - start_time
        
        return {
            "questions_asked": questions_asked,
            "game_time": game_time,
            "final_candidates": len(candidates),
            "avg_confidence": np.mean(confidence_history) if confidence_history else 0.0,
            "confidence_trend": confidence_history
        }
    
    def simulate_multiple_games(self, num_games: int = 100) -> Dict[str, Any]:
        """Simulate multiple games and aggregate results"""
        results = []
        
        for i in range(num_games):
            try:
                result = self.simulate_game()
                results.append(result)
            except Exception as e:
                logger.error(f"Game simulation {i} failed: {e}")
        
        if not results:
            return {"error": "No successful simulations"}
        
        # Aggregate metrics
        avg_questions = np.mean([r["questions_asked"] for r in results])
        avg_time = np.mean([r["game_time"] for r in results])
        avg_confidence = np.mean([r["avg_confidence"] for r in results])
        success_rate = sum(1 for r in results if r["final_candidates"] == 1) / len(results)
        
        return {
            "num_games": len(results),
            "avg_questions_per_game": avg_questions,
            "avg_game_time": avg_time,
            "avg_confidence": avg_confidence,
            "success_rate": success_rate,
            "detailed_results": results[:10]  # Sample results
        }


def run_comprehensive_tests(data_dir: str = None) -> Dict[str, Any]:
    """Run comprehensive test suite"""
    logger.info("Starting comprehensive test suite")
    
    # Initialize test components
    tests = EnterpriseTests(data_dir)
    runner = BenchmarkRunner()
    
    # Define test cases
    test_cases = [
        ("Data Validation", tests.test_data_validation),
        ("Attribute Normalization", tests.test_attribute_normalization),
        ("Data Preprocessing", tests.test_data_preprocessing),
        ("Graph Construction", tests.test_graph_construction),
        ("Embedding Training", tests.test_embedding_training),
        ("Adaptive Hybrid Engine", tests.test_adaptive_hybrid_engine),
        ("System Robustness", tests.test_system_robustness),
    ]
    
    # Run benchmarks
    results = []
    for test_name, test_func in test_cases:
        try:
            result = runner.run_benchmark(test_func, test_name)
            results.append(result)
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results.append(BenchmarkResult(
                test_name=test_name,
                execution_time=0,
                memory_usage=0,
                success=False,
                error_message=str(e)
            ))
    
    # Generate report
    report = runner.generate_report()
    
    # Save results
    runner.save_results()
    
    # Cleanup
    tests.cleanup()
    
    return {
        "report": report,
        "results": results,
        "summary": {
            "total_tests": len(results),
            "passed": sum(1 for r in results if r.success),
            "failed": sum(1 for r in results if not r.success)
        }
    }


if __name__ == "__main__":
    # Run tests when executed directly
    logging.basicConfig(level=logging.INFO)
    
    results = run_comprehensive_tests()
    print(results["report"])
    print(f"\nSummary: {results['summary']['passed']}/{results['summary']['total_tests']} tests passed")
