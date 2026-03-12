#!/usr/bin/env python3
"""
Performance Benchmark Script
Measures actual system performance metrics
"""

import sys
import os
import time
import psutil
from typing import List, Dict, Any

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.logic.hybrid_engine import create_hybrid_engine
from backend.logic.questions import select_best_question
from backend.logic.kg_loader import load_dataset

def measure_memory_usage():
    """Get current memory usage in MB."""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024

def benchmark_question_generation():
    """Benchmark question generation performance."""
    print("🔍 Benchmarking Question Generation...")
    
    # Create engine
    start_time = time.time()
    engine = create_hybrid_engine()
    engine_creation_time = time.time() - start_time
    
    # Get data
    songs = engine.get_entities()
    questions = engine.get_questions()
    beliefs = engine.get_beliefs()
    
    # Benchmark question generation
    question_times = []
    for i in range(10):  # Test 10 times
        start = time.time()
        question = select_best_question(questions, songs, beliefs, set(), engine)
        duration = time.time() - start
        question_times.append(duration * 1000)  # Convert to ms
    
    # Calculate statistics
    avg_time = sum(question_times) / len(question_times)
    min_time = min(question_times)
    max_time = max(question_times)
    
    return {
        'engine_creation_time': engine_creation_time * 1000,
        'question_generation': {
            'avg_ms': avg_time,
            'min_ms': min_time,
            'max_ms': max_time,
            'samples': len(question_times)
        }
    }

def benchmark_inference():
    """Benchmark inference performance."""
    print("🧠 Benchmarking Inference...")
    
    engine = create_hybrid_engine()
    songs = engine.get_entities()
    
    # Benchmark belief updates
    inference_times = []
    for i in range(20):  # Test 20 times
        # Simulate a question and answer
        question = {
            'feature': 'genres',
            'value': 'pop',
            'text': 'Is it a pop song?'
        }
        
        start = time.time()
        engine.update_beliefs(question, 'yes')
        duration = time.time() - start
        inference_times.append(duration * 1000)  # Convert to ms
    
    # Calculate statistics
    avg_time = sum(inference_times) / len(inference_times)
    min_time = min(inference_times)
    max_time = max(inference_times)
    
    return {
        'inference': {
            'avg_ms': avg_time,
            'min_ms': min_time,
            'max_ms': max_time,
            'samples': len(inference_times)
        }
    }

def benchmark_memory():
    """Benchmark memory usage."""
    print("💾 Benchmarking Memory Usage...")
    
    # Baseline memory
    baseline_memory = measure_memory_usage()
    
    # Create engine and measure memory
    engine = create_hybrid_engine()
    after_engine_memory = measure_memory_usage()
    
    # Load dataset and measure memory
    songs = load_dataset()
    after_dataset_memory = measure_memory_usage()
    
    return {
        'memory_usage': {
            'baseline_mb': baseline_memory,
            'after_engine_mb': after_engine_memory,
            'after_dataset_mb': after_dataset_memory,
            'engine_overhead_mb': after_engine_memory - baseline_memory,
            'dataset_overhead_mb': after_dataset_memory - after_engine_memory
        }
    }

def benchmark_system_load():
    """Benchmark system under load."""
    print("⚡ Benchmarking System Load...")
    
    engine = create_hybrid_engine()
    songs = engine.get_entities()
    questions = engine.get_questions()
    beliefs = engine.get_beliefs()
    
    # Simulate multiple concurrent sessions
    session_times = []
    for session_id in range(5):  # 5 concurrent sessions
        session_start = time.time()
        
        # Simulate 10 questions per session
        for question_id in range(10):
            question = select_best_question(questions, songs, beliefs, set(), engine)
            engine.update_beliefs(question, 'yes')
        
        session_duration = time.time() - session_start
        session_times.append(session_duration * 1000)  # Convert to ms
    
    avg_session_time = sum(session_times) / len(session_times)
    
    return {
        'system_load': {
            'concurrent_sessions': 5,
            'questions_per_session': 10,
            'avg_session_time_ms': avg_session_time,
            'total_questions': 50
        }
    }

def main():
    """Run all benchmarks."""
    print("🚀 Music Akenator Performance Benchmark")
    print("=" * 50)
    
    try:
        # Get system info
        print(f"📊 System Info:")
        print(f"   Python version: {sys.version}")
        print(f"   Songs in dataset: {len(load_dataset())}")
        print(f"   Available memory: {psutil.virtual_memory().total / 1024 / 1024 / 1024:.1f} GB")
        print()
        
        # Run benchmarks
        results = {}
        
        # Question generation benchmark
        results.update(benchmark_question_generation())
        print()
        
        # Inference benchmark
        results.update(benchmark_inference())
        print()
        
        # Memory benchmark
        results.update(benchmark_memory())
        print()
        
        # System load benchmark
        results.update(benchmark_system_load())
        print()
        
        # Print results
        print("📈 BENCHMARK RESULTS")
        print("=" * 50)
        
        print(f"🏗️  Engine Creation:")
        print(f"   Time: {results['engine_creation_time']:.2f} ms")
        print()
        
        print(f"❓ Question Generation:")
        qg = results['question_generation']
        print(f"   Average: {qg['avg_ms']:.2f} ms")
        print(f"   Min: {qg['min_ms']:.2f} ms")
        print(f"   Max: {qg['max_ms']:.2f} ms")
        print(f"   Samples: {qg['samples']}")
        print()
        
        print(f"🧠 Inference (Belief Updates):")
        inf = results['inference']
        print(f"   Average: {inf['avg_ms']:.2f} ms")
        print(f"   Min: {inf['min_ms']:.2f} ms")
        print(f"   Max: {inf['max_ms']:.2f} ms")
        print(f"   Samples: {inf['samples']}")
        print()
        
        print(f"💾 Memory Usage:")
        mem = results['memory_usage']
        print(f"   Baseline: {mem['baseline_mb']:.1f} MB")
        print(f"   After Engine: {mem['after_engine_mb']:.1f} MB")
        print(f"   After Dataset: {mem['after_dataset_mb']:.1f} MB")
        print(f"   Engine Overhead: {mem['engine_overhead_mb']:.1f} MB")
        print(f"   Dataset Overhead: {mem['dataset_overhead_mb']:.1f} MB")
        print()
        
        print(f"⚡ System Load:")
        load = results['system_load']
        print(f"   Concurrent Sessions: {load['concurrent_sessions']}")
        print(f"   Questions per Session: {load['questions_per_session']}")
        print(f"   Avg Session Time: {load['avg_session_time_ms']:.2f} ms")
        print(f"   Total Questions: {load['total_questions']}")
        print()
        
        # Performance assessment
        qg_avg = qg['avg_ms']
        inf_avg = inf['avg_ms']
        total_memory = mem['after_dataset_mb']
        
        print("🎯 PERFORMANCE ASSESSMENT")
        print("=" * 50)
        
        if qg_avg < 20:
            print("✅ Question generation: EXCELLENT (< 20ms)")
        elif qg_avg < 50:
            print("✅ Question generation: GOOD (< 50ms)")
        else:
            print("⚠️  Question generation: NEEDS IMPROVEMENT (> 50ms)")
        
        if inf_avg < 10:
            print("✅ Inference: EXCELLENT (< 10ms)")
        elif inf_avg < 25:
            print("✅ Inference: GOOD (< 25ms)")
        else:
            print("⚠️  Inference: NEEDS IMPROVEMENT (> 25ms)")
        
        if total_memory < 100:
            print("✅ Memory usage: EXCELLENT (< 100MB)")
        elif total_memory < 200:
            print("✅ Memory usage: GOOD (< 200MB)")
        else:
            print("⚠️  Memory usage: NEEDS OPTIMIZATION (> 200MB)")
        
        print()
        print("🎉 Benchmark completed successfully!")
        
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
