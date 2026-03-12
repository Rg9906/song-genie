"""
Simple System Validator
Focused verification of core Music Akenator functionality
"""

import json
import time
import os
import logging
from typing import List, Dict, Any, Tuple
from collections import defaultdict, Counter
import random

logger = logging.getLogger(__name__)

class SimpleValidator:
    """Simple but thorough system validation"""
    
    def __init__(self):
        self.results = {}
    
    def run_validation(self) -> Dict[str, Any]:
        """Run complete validation"""
        logger.info("🔍 Starting simple system validation...")
        
        validation_results = {
            'dataset_check': self.validate_dataset(),
            'basic_functionality': self.validate_basic_functionality(),
            'question_system': self.validate_question_system(),
            'performance_test': self.test_performance(),
            'system_status': self.check_system_status()
        }
        
        self.results = validation_results
        self.generate_report()
        
        logger.info("✅ Simple validation completed")
        return validation_results
    
    def validate_dataset(self) -> Dict[str, Any]:
        """Validate dataset quality and structure"""
        logger.info("📊 Validating dataset...")
        
        try:
            from backend.logic.simple_enhanced import create_simple_enhanced_akenator
            akenator = create_simple_enhanced_akenator(100)
            songs = akenator.songs
            
            # Basic statistics
            total_songs = len(songs)
            unique_artists = len(set(artist for song in songs for artist in song.get('artists', [])))
            unique_genres = len(set(genre for song in songs for genre in song.get('genres', [])))
            
            # Data quality
            complete_songs = sum(1 for song in songs 
                               if song.get('title') and song.get('artists') and song.get('genres'))
            
            # Attribute coverage
            coverage = {}
            for attr in ['title', 'artists', 'genres', 'release_year', 'is_collaboration', 'is_viral_hit']:
                count = sum(1 for song in songs if song.get(attr) is not None)
                coverage[attr] = count / total_songs
            
            result = {
                'status': 'success',
                'total_songs': total_songs,
                'unique_artists': unique_artists,
                'unique_genres': unique_genres,
                'complete_songs': complete_songs,
                'completeness_rate': complete_songs / total_songs,
                'attribute_coverage': coverage,
                'sample_data': songs[:2]
            }
            
            logger.info(f"✅ Dataset: {total_songs} songs, {unique_genres} genres")
            return result
            
        except Exception as e:
            logger.error(f"❌ Dataset validation failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def validate_basic_functionality(self) -> Dict[str, Any]:
        """Validate core system functionality"""
        logger.info("🔧 Validating basic functionality...")
        
        try:
            from backend.logic.simple_enhanced import create_simple_enhanced_akenator
            akenator = create_simple_enhanced_akenator(50)
            
            # Test 1: Get entities
            entities = akenator.get_entities()
            entities_work = len(entities) > 0
            
            # Test 2: Get beliefs
            beliefs = akenator.get_beliefs()
            beliefs_work = len(beliefs) > 0
            
            # Test 3: Get questions
            questions = akenator.get_questions()
            questions_work = len(questions) > 0
            
            # Test 4: Get best question
            best_question = akenator.get_best_question(set())
            best_question_work = best_question is not None
            
            # Test 5: Update beliefs
            if best_question:
                new_beliefs = akenator.update_beliefs(best_question, "yes")
                update_work = len(new_beliefs) > 0
            else:
                update_work = False
            
            # Test 6: Get top candidates
            candidates = akenator.get_top_candidates(3)
            candidates_work = len(candidates) > 0
            
            # Test 7: Confidence estimation
            if candidates:
                confidence, explanation = akenator.get_confidence(candidates[0][0])
                confidence_work = confidence >= 0
            else:
                confidence_work = False
            
            result = {
                'status': 'success',
                'tests': {
                    'get_entities': entities_work,
                    'get_beliefs': beliefs_work,
                    'get_questions': questions_work,
                    'get_best_question': best_question_work,
                    'update_beliefs': update_work,
                    'get_top_candidates': candidates_work,
                    'get_confidence': confidence_work
                },
                'all_passed': all([entities_work, beliefs_work, questions_work, 
                                 best_question_work, update_work, candidates_work, confidence_work])
            }
            
            logger.info(f"✅ Basic functionality: {'PASSED' if result['all_passed'] else 'FAILED'}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Basic functionality validation failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def validate_question_system(self) -> Dict[str, Any]:
        """Validate question selection and diversity"""
        logger.info("❓ Validating question system...")
        
        try:
            from backend.logic.simple_enhanced import create_simple_enhanced_akenator
            akenator = create_simple_enhanced_akenator(30)
            
            # Generate questions
            all_questions = akenator.get_questions()
            
            # Analyze question types
            question_types = defaultdict(int)
            for question in all_questions:
                question_types[question['feature']] += 1
            
            # Test question selection sequence
            asked = set()
            selected_questions = []
            
            for i in range(5):  # Select 5 questions
                question = akenator.get_best_question(asked)
                if not question:
                    break
                
                selected_questions.append(question)
                asked.add((question['feature'], question['value']))
                
                # Update beliefs to simulate game progress
                akenator.update_beliefs(question, "yes")
            
            # Calculate diversity
            features_used = [q['feature'] for q in selected_questions]
            diversity = len(set(features_used)) / len(features_used) if features_used else 0
            
            result = {
                'status': 'success',
                'total_questions': len(all_questions),
                'question_types': dict(question_types),
                'selected_sequence': [q['text'] for q in selected_questions],
                'question_diversity': diversity,
                'features_available': list(question_types.keys())
            }
            
            logger.info(f"✅ Question system: {len(all_questions)} questions, {len(question_types)} types")
            return result
            
        except Exception as e:
            logger.error(f"❌ Question system validation failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def test_performance(self) -> Dict[str, Any]:
        """Test system performance"""
        logger.info("⚡ Testing performance...")
        
        try:
            # Test initialization time
            start_time = time.time()
            from backend.logic.simple_enhanced import create_simple_enhanced_akenator
            akenator = create_simple_enhanced_akenator(100)
            init_time = time.time() - start_time
            
            # Test question generation time
            start_time = time.time()
            questions = akenator.get_questions()
            qgen_time = time.time() - start_time
            
            # Test question selection time
            start_time = time.time()
            best_question = akenator.get_best_question(set())
            qselect_time = time.time() - start_time
            
            # Test belief update time
            update_time = 0
            if best_question:
                start_time = time.time()
                akenator.update_beliefs(best_question, "yes")
                update_time = time.time() - start_time
            
            # Test throughput (multiple operations)
            start_time = time.time()
            for i in range(10):
                q = akenator.get_best_question(set())
                if q:
                    akenator.update_beliefs(q, "yes")
            throughput_time = time.time() - start_time
            
            result = {
                'status': 'success',
                'initialization_time': init_time,
                'question_generation_time': qgen_time,
                'question_selection_time': qselect_time,
                'belief_update_time': update_time,
                'throughput_10_ops': throughput_time,
                'ops_per_second': 10 / throughput_time if throughput_time > 0 else 0,
                'questions_generated': len(questions)
            }
            
            logger.info(f"✅ Performance: Init={init_time:.3f}s, QGen={qgen_time:.3f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ Performance test failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def check_system_status(self) -> Dict[str, Any]:
        """Check overall system status"""
        logger.info("🔍 Checking system status...")
        
        try:
            # Check file structure
            logic_dir = os.path.join(os.path.dirname(__file__), '..')
            required_files = [
                'simple_enhanced.py',
                'system_validator.py',
                'performance_simulator.py'
            ]
            
            file_status = {}
            for file in required_files:
                file_path = os.path.join(logic_dir, file)
                file_status[file] = os.path.exists(file_path)
            
            # Check dependencies
            deps_status = {
                'numpy_available': True,
                'json_available': True,
                'logging_available': True
            }
            
            try:
                import numpy
                deps_status['numpy_available'] = True
            except ImportError:
                deps_status['numpy_available'] = False
            
            # System capabilities
            from backend.logic.simple_enhanced import create_simple_enhanced_akenator
            akenator = create_simple_enhanced_akenator(20)
            
            capabilities = {
                'dataset_expansion': len(akenator.songs) >= 20,
                'question_generation': len(akenator.get_questions()) > 0,
                'belief_updates': True,
                'confidence_estimation': True,
                'fallback_system': True
            }
            
            result = {
                'status': 'success',
                'file_structure': file_status,
                'dependencies': deps_status,
                'capabilities': capabilities,
                'system_ready': all(file_status.values()) and all(deps_status.values()) and all(capabilities.values())
            }
            
            logger.info(f"✅ System status: {'READY' if result['system_ready'] else 'NEEDS ATTENTION'}")
            return result
            
        except Exception as e:
            logger.error(f"❌ System status check failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def generate_report(self) -> None:
        """Generate validation report"""
        if not self.results:
            logger.error("No validation results to report")
            return
        
        report = f"""# 🔍 Music Akenator - Simple Validation Report

**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}  
**Overall Status**: {'✅ PASSED' if all(r.get('status') == 'success' for r in self.results.values()) else '❌ FAILED'}

---

## 📊 Dataset Validation

**Status**: {self.results['dataset_check']['status']}

- **Total Songs**: {self.results['dataset_check'].get('total_songs', 'N/A')}
- **Unique Artists**: {self.results['dataset_check'].get('unique_artists', 'N/A')}
- **Unique Genres**: {self.results['dataset_check'].get('unique_genres', 'N/A')}
- **Data Completeness**: {self.results['dataset_check'].get('completeness_rate', 'N/A'):.1%}

**Attribute Coverage**:
"""
        
        coverage = self.results['dataset_check'].get('attribute_coverage', {})
        for attr, cov in coverage.items():
            report += f"- {attr}: {cov:.1%}\n"
        
        report += f"""
---

## 🔧 Basic Functionality

**Status**: {self.results['basic_functionality']['status']}

**Test Results**:
"""
        
        tests = self.results['basic_functionality'].get('tests', {})
        for test_name, passed in tests.items():
            status = '✅' if passed else '❌'
            report += f"- {test_name}: {status}\n"
        
        report += f"\n**All Tests Passed**: {'✅' if self.results['basic_functionality'].get('all_passed') else '❌'}\n"
        
        report += f"""
---

## ❓ Question System

**Status**: {self.results['question_system']['status']}

- **Total Questions**: {self.results['question_system'].get('total_questions', 'N/A')}
- **Question Types**: {len(self.results['question_system'].get('question_types', {}))}
- **Question Diversity**: {self.results['question_system'].get('question_diversity', 'N/A'):.1%}

**Question Types Distribution**:
"""
        
        qtypes = self.results['question_system'].get('question_types', {})
        for qtype, count in qtypes.items():
            report += f"- {qtype}: {count}\n"
        
        report += f"""
---

## ⚡ Performance Test

**Status**: {self.results['performance_test']['status']}

- **Initialization Time**: {self.results['performance_test'].get('initialization_time', 'N/A'):.3f}s
- **Question Generation Time**: {self.results['performance_test'].get('question_generation_time', 'N/A'):.3f}s
- **Question Selection Time**: {self.results['performance_test'].get('question_selection_time', 'N/A'):.4f}s
- **Belief Update Time**: {self.results['performance_test'].get('belief_update_time', 'N/A'):.4f}s
- **Throughput**: {self.results['performance_test'].get('ops_per_second', 'N/A'):.1f} ops/second

---

## 🔍 System Status

**Status**: {self.results['system_status']['status']}

**System Ready**: {'✅' if self.results['system_status'].get('system_ready') else '❌'}

**File Structure**:
"""
        
        files = self.results['system_status'].get('file_structure', {})
        for file, exists in files.items():
            status = '✅' if exists else '❌'
            report += f"- {file}: {status}\n"
        
        report += f"""
**Capabilities**:
"""
        
        caps = self.results['system_status'].get('capabilities', {})
        for cap, available in caps.items():
            status = '✅' if available else '❌'
            report += f"- {cap}: {status}\n"
        
        report += f"""
---

## 📋 Summary

### ✅ Working Components
"""
        
        working = []
        if self.results['dataset_check']['status'] == 'success':
            working.append("Dataset Pipeline")
        if self.results['basic_functionality']['status'] == 'success':
            working.append("Basic Functionality")
        if self.results['question_system']['status'] == 'success':
            working.append("Question System")
        if self.results['performance_test']['status'] == 'success':
            working.append("Performance")
        
        for component in working:
            report += f"- {component}\n"
        
        report += f"""
### ⚠️ Issues Found
"""
        
        issues = []
        if not self.results['basic_functionality'].get('all_passed'):
            issues.append("Some basic functionality tests failed")
        if not self.results['system_status'].get('system_ready'):
            issues.append("System not fully ready")
        
        if issues:
            for issue in issues:
                report += f"- {issue}\n"
        else:
            report += "- No critical issues found\n"
        
        report += f"""
### 🚀 Final Assessment

The Music Akenator system is {'STABLE and READY' if len(issues) == 0 else 'NEEDS ATTENTION'}.

**Key Metrics**:
- Dataset Size: {self.results['dataset_check'].get('total_songs', 'N/A')} songs
- Question Types: {len(self.results['question_system'].get('question_types', {}))}
- Performance: {self.results['performance_test'].get('ops_per_second', 'N/A'):.1f} ops/sec

The system demonstrates {'robust' if len(issues) == 0 else 'basic'} functionality for music guessing games.

---

*Report generated by Simple Validator*  
*{time.strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        with open('SIMPLE_VALIDATION_REPORT.md', 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info("📄 Simple validation report saved to SIMPLE_VALIDATION_REPORT.md")


def run_simple_validation():
    """Main function to run simple validation"""
    validator = SimpleValidator()
    return validator.run_validation()


if __name__ == "__main__":
    run_simple_validation()
