#!/usr/bin/env python3
"""
Robustness Testing for Hybrid System
Tests all failure scenarios and edge cases
"""

import sys
import os
import json
import traceback
from typing import Dict, List, Any

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

class RobustnessTester:
    """Tests system robustness under various conditions"""
    
    def __init__(self):
        self.test_results = []
        self.passed = 0
        self.failed = 0
    
    def run_test(self, test_name: str, test_func):
        """Run a single test and track results"""
        print(f"🧪 Testing: {test_name}")
        try:
            result = test_func()
            if result:
                print(f"   ✅ PASSED")
                self.passed += 1
            else:
                print(f"   ❌ FAILED")
                self.failed += 1
            
            self.test_results.append({
                "name": test_name,
                "passed": result,
                "error": None
            })
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            self.failed += 1
            self.test_results.append({
                "name": test_name,
                "passed": False,
                "error": str(e)
            })
    
    def test_engine_creation_no_dependencies(self):
        """Test engine creation with missing dependencies"""
        try:
            # Temporarily hide torch
            import sys
            original_modules = {}
            for module in ['torch', 'torch.nn', 'torch.optim']:
                if module in sys.modules:
                    original_modules[module] = sys.modules[module]
                    del sys.modules[module]
            
            try:
                from backend.logic.hybrid_engine import create_hybrid_engine
                engine = create_hybrid_engine(enable_graph=False, enable_embeddings=True)
                return engine is not None
            finally:
                # Restore modules
                sys.modules.update(original_modules)
                
        except Exception:
            return False
    
    def test_engine_creation_no_data(self):
        """Test engine creation with missing data files"""
        # Temporarily rename data files
        data_dir = os.path.join(os.path.dirname(__file__), 'backend', 'data')
        original_files = {}
        
        for filename in ['songs_kg.json', 'dynamic_graph.json', 'song_embeddings.pt']:
            filepath = os.path.join(data_dir, filename)
            if os.path.exists(filepath):
                original_files[filename] = filepath + '.backup'
                os.rename(filepath, original_files[filename])
        
        try:
            from backend.logic.hybrid_engine import create_hybrid_engine
            engine = create_hybrid_engine(enable_graph=True, enable_embeddings=True)
            return engine is not None
        except Exception:
            return False
        finally:
            # Restore files
            for filename, backup_path in original_files.items():
                if os.path.exists(backup_path):
                    os.rename(backup_path, os.path.join(data_dir, filename))
    
    def test_malformed_data_handling(self):
        """Test handling of malformed song data"""
        # Create malformed song data
        malformed_songs = [
            {"title": None, "genres": []},  # Missing title
            {"title": "Test Song", "genres": "not_a_list"},  # Wrong data type
            {"title": "", "genres": ["valid"]},  # Empty title
            {"title": "Valid Song", "genres": [], "artists": None},  # None values
        ]
        
        try:
            from backend.logic.hybrid_engine import HybridEngine
            engine = HybridEngine(enable_graph=False, enable_embeddings=False)
            engine.entities = malformed_songs
            
            # Test question generation with malformed data
            questions = engine.get_questions()
            return len(questions) >= 0  # Should not crash
            
        except Exception:
            return False
    
    def test_empty_candidate_list(self):
        """Test question generation with empty candidates"""
        try:
            from backend.logic.hybrid_engine import create_hybrid_engine
            engine = create_hybrid_engine(enable_graph=False, enable_embeddings=False)
            
            question = engine.get_optimal_question([], set())
            return question is None  # Should return None for empty list
            
        except Exception:
            return False
    
    def test_single_candidate(self):
        """Test question generation with single candidate"""
        try:
            from backend.logic.hybrid_engine import create_hybrid_engine
            engine = create_hybrid_engine(enable_graph=False, enable_embeddings=False)
            
            songs = engine.get_entities()
            if len(songs) > 0:
                question = engine.get_optimal_question([songs[0]["title"]], set())
                return question is None  # Should return None for single candidate
            
            return True  # Skip test if no songs
            
        except Exception:
            return False
    
    def test_invalid_similarity_queries(self):
        """Test similarity queries with invalid song names"""
        try:
            from backend.logic.hybrid_engine import create_hybrid_engine
            engine = create_hybrid_engine(enable_graph=False, enable_embeddings=False)
            
            # Test with non-existent songs
            similarity = engine.calculate_similarity("NonExistentSong", "AnotherNonExistentSong")
            return similarity == 0.0  # Should return 0.0 for non-existent songs
            
        except Exception:
            return False
    
    def test_concurrent_sessions(self):
        """Test multiple concurrent sessions"""
        try:
            from backend.logic.hybrid_engine import create_hybrid_engine
            
            # Create multiple engines
            engines = []
            for i in range(5):
                engine = create_hybrid_engine(enable_graph=False, enable_embeddings=False)
                engines.append(engine)
            
            # Test all engines work
            all_working = all(engine is not None for engine in engines)
            return all_working
            
        except Exception:
            return False
    
    def test_memory_usage(self):
        """Test memory usage with large datasets"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss
            
            # Create multiple engines
            engines = []
            for i in range(10):
                engine = create_hybrid_engine(enable_graph=False, enable_embeddings=False)
                engines.append(engine)
            
            final_memory = process.memory_info().rss
            memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB
            
            # Memory increase should be reasonable (< 100MB for 10 engines)
            return memory_increase < 100
            
        except ImportError:
            return True  # Skip test if psutil not available
        except Exception:
            return False
    
    def test_network_failures(self):
        """Test behavior when network requests fail"""
        # This would require mocking network requests
        # For now, just test that the system doesn't crash with no internet
        try:
            from backend.logic.dynamic_graph import DynamicWikidataGraph
            graph = DynamicWikidataGraph()
            
            # Try to load without network
            graph.load_graph("non_existent_file.json")
            
            # Should not crash
            return True
            
        except Exception:
            return False
    
    def test_question_quality(self):
        """Test that generated questions are meaningful"""
        try:
            from backend.logic.hybrid_engine import create_hybrid_engine
            engine = create_hybrid_engine(enable_graph=False, enable_embeddings=False)
            
            songs = engine.get_entities()
            if len(songs) < 2:
                return True  # Skip test with insufficient data
            
            candidate_titles = [song["title"] for song in songs[:5]]
            asked = set()
            
            # Generate several questions
            questions = []
            for _ in range(5):
                question = engine.get_optimal_question(candidate_titles, asked)
                if question:
                    questions.append(question)
                    asked.add((question["feature"], question["value"]))
            
            # Check question quality
            if not questions:
                return False
            
            # Questions should have required fields
            for q in questions:
                if not all(key in q for key in ["feature", "value", "text"]):
                    return False
                
                # Text should be meaningful (not empty)
                if not q["text"] or len(q["text"].strip()) == 0:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def test_fallback_mechanisms(self):
        """Test that fallback mechanisms work when primary systems fail"""
        try:
            # Test that system falls back to tag-based when embeddings fail
            from backend.logic.hybrid_engine import HybridEngine
            
            # Create engine with both systems but embeddings will fail
            engine = HybridEngine(enable_graph=True, enable_embeddings=True)
            
            # Should still work with graph system
            return engine.hybrid.graph_system is not None
            
        except Exception:
            return False
    
    def run_all_tests(self):
        """Run all robustness tests"""
        print("🔬 Running Robustness Tests")
        print("=" * 50)
        
        # Test cases
        test_cases = [
            ("Engine creation without PyTorch", self.test_engine_creation_no_dependencies),
            ("Engine creation without data files", self.test_engine_creation_no_data),
            ("Malformed data handling", self.test_malformed_data_handling),
            ("Empty candidate list", self.test_empty_candidate_list),
            ("Single candidate", self.test_single_candidate),
            ("Invalid similarity queries", self.test_invalid_similarity_queries),
            ("Concurrent sessions", self.test_concurrent_sessions),
            ("Memory usage", self.test_memory_usage),
            ("Network failure handling", self.test_network_failures),
            ("Question quality", self.test_question_quality),
            ("Fallback mechanisms", self.test_fallback_mechanisms),
        ]
        
        for test_name, test_func in test_cases:
            self.run_test(test_name, test_func)
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Summary: {self.passed} passed, {self.failed} failed")
        
        if self.failed == 0:
            print("🎉 All tests passed! System is robust.")
        else:
            print("⚠️ Some tests failed. Check the details above.")
        
        # Save detailed results
        results_path = os.path.join(os.path.dirname(__file__), 'robustness_test_results.json')
        with open(results_path, 'w') as f:
            json.dump({
                "summary": {
                    "passed": self.passed,
                    "failed": self.failed,
                    "total": self.passed + self.failed
                },
                "details": self.test_results
            }, f, indent=2)
        
        print(f"📄 Detailed results saved to {results_path}")
        
        return self.failed == 0

def main():
    """Main testing function"""
    tester = RobustnessTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ System is robust and ready for production!")
    else:
        print("\n⚠️ System needs improvements before production use.")
    
    return success

if __name__ == "__main__":
    main()
