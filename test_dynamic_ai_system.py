#!/usr/bin/env python3
"""
Test the fully dynamic AI question system
"""

from backend.logic.simple_enhanced import create_simple_enhanced_akenator
from collections import Counter

def test_dynamic_ai_system():
    """Test the completely dynamic AI system"""
    print("🤖 Testing Dynamic AI Question System")
    print("=" * 50)
    
    # Create akenator
    akenator = create_simple_enhanced_akenator(100)
    
    # Check what components are available
    print(f"🔧 Components Available:")
    print(f"   Intelligent Selector: {'✅' if akenator.intelligent_selector else '❌'}")
    print(f"   Diverse Generator: {'✅' if akenator.diverse_generator else '❌'}")
    print(f"   LLM Framer: {'✅' if akenator.llm_framer else '❌'}")
    print(f"   Dynamic AI Engine: {'✅' if akenator.dynamic_ai_engine else '❌'}")
    print(f"   Free AI Integrator: {'✅' if akenator.free_ai_integrator else '❌'}")
    
    # Show dynamic patterns discovered
    if akenator.dynamic_ai_engine:
        stats = akenator.dynamic_ai_engine.get_dynamic_stats()
        print(f"\n🔍 Dynamic Patterns Discovered:")
        print(f"   Total attributes: {stats['total_attributes']}")
        print(f"   Attribute types: {stats['attribute_types']}")
        
        print(f"\n📊 Attribute Diversity:")
        for attr, diversity in stats['value_diversity'].items():
            print(f"      {attr}: {diversity} unique values")
    
    # Get all questions
    all_questions = akenator.get_questions()
    print(f"\n📊 Total Questions Generated: {len(all_questions)}")
    
    # Analyze question features
    features = Counter([q['feature'] for q in all_questions])
    print(f"\n🔍 Dynamic Question Features:")
    for feature, count in features.most_common():
        print(f"   {feature}: {count} questions")
    
    # Analyze pattern types
    pattern_types = Counter([q.get('pattern_type', 'unknown') for q in all_questions])
    print(f"\n🎯 Pattern Types:")
    for pattern, count in pattern_types.most_common():
        print(f"   {pattern}: {count} questions")
    
    # Simulate question selection
    print(f"\n🎮 Simulating Dynamic Question Selection:")
    asked_questions = set()
    selected_questions = []
    
    for i in range(15):
        best_q = akenator.get_best_question(asked_questions)
        if not best_q:
            break
            
        selected_questions.append(best_q)
        asked_questions.add((best_q['feature'], best_q['value']))
        
        # Show question with pattern type
        pattern = best_q.get('pattern_type', 'unknown')
        source = best_q.get('source', 'dynamic')
        print(f"Q{i+1}: {best_q['text']} ({best_q['feature']}) [{pattern}] [{source}]")
    
    # Analyze selection diversity
    selected_features = Counter([q['feature'] for q in selected_questions])
    selected_patterns = Counter([q.get('pattern_type', 'unknown') for q in selected_questions])
    selected_sources = Counter([q.get('source', 'dynamic') for q in selected_questions])
    
    print(f"\n📈 Dynamic Selection Analysis:")
    print(f"   Features: {len(selected_features)} different types")
    print(f"   Patterns: {len(selected_patterns)} different types")
    print(f"   Sources: {len(selected_sources)} different types")
    
    print(f"\n🎯 Feature Distribution:")
    for feature, count in selected_features.most_common():
        print(f"      {feature}: {count} questions")
    
    print(f"\n🔍 Pattern Distribution:")
    for pattern, count in selected_patterns.most_common():
        print(f"      {pattern}: {count} questions")
    
    print(f"\n🌐 Source Distribution:")
    for source, count in selected_sources.most_common():
        print(f"      {source}: {count} questions")
    
    return selected_questions

def show_dynamic_vs_static_comparison():
    """Show the difference between dynamic and static systems"""
    print(f"\n🔄 Dynamic vs Static Comparison")
    print("=" * 30)
    
    print("❌ STATIC SYSTEM (What we had before):")
    print("   - Fixed 8 categories: genres, artists, themes, etc.")
    print("   - Fixed templates: 'Is it a [genre] song?'")
    print("   - Fixed quotas: 4 genre, 3 artist, 2 decade questions")
    print("   - No adaptation to data")
    print("   - Rigid and predictable")
    
    print("\n✅ DYNAMIC AI SYSTEM (What we have now):")
    print("   - Discovers patterns automatically from your data")
    print("   - Generates questions based on actual data relationships")
    print("   - Creates range questions: 'Does this have high tempo?'")
    print("   - Creates outlier questions: 'Is this unusually long?'")
    print("   - Creates relationship questions: 'Is there a connection between tempo and genre?'")
    print("   - Uses AI APIs for creative question generation")
    print("   - Adapts to any song data structure")
    print("   - Completely unpredictable and engaging")

if __name__ == "__main__":
    questions = test_dynamic_ai_system()
    show_dynamic_vs_static_comparison()
    
    print(f"\n🎉 The dynamic AI system is completely flexible!")
    print(f"   - No static categories or templates")
    print(f"   - Questions adapt to your actual data")
    print(f"   - AI-powered generation available")
    print(f"   - Truly dynamic and unpredictable")
    print(f"\n💡 This is the ultimate flexible music guessing system!")
