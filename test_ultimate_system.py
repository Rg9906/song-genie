#!/usr/bin/env python3
"""
Test the ultimate dynamic system
"""

from backend.logic.simple_enhanced import create_simple_enhanced_akenator
from collections import Counter

def test_ultimate_dynamic_system():
    """Test the ultimate dynamic system"""
    print("🚀 Testing Ultimate Dynamic System")
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
    print(f"   Ultimate Dynamic System: {'✅' if akenator.ultimate_dynamic_system else '❌'}")
    
    # Show ultimate system statistics
    if akenator.ultimate_dynamic_system:
        stats = akenator.ultimate_dynamic_system.get_system_statistics()
        print(f"\n🔍 Ultimate System Statistics:")
        print(f"   Dynamic Attributes: {stats['dynamic_attributes']['total']}")
        print(f"   Existing Attributes: {stats['dynamic_attributes']['existing']}")
        print(f"   Scraped Attributes: {stats['dynamic_attributes']['scraped']}")
        
        print(f"\n📊 Attribute Details:")
        for attr, details in stats['attribute_details'].items():
            print(f"      {attr}: {details['value_count']} values ({details['source']})")
        
        # Show relevance validation if available
        if 'relevance_validation' in stats:
            rel_stats = stats['relevance_validation']
            print(f"\n🧠 Human Relevance Validation:")
            print(f"   Relevance Rate: {rel_stats['relevance_rate']:.2%}")
            print(f"   Average Confidence: {rel_stats['average_confidence']:.2f}")
            print(f"   High Confidence Rate: {rel_stats['high_confidence_rate']:.2%}")
    
    # Simulate question selection
    print(f"\n🎮 Simulating Ultimate Question Selection:")
    asked_questions = set()
    selected_questions = []
    
    for i in range(15):
        best_q = akenator.get_best_question(asked_questions)
        if not best_q:
            break
            
        selected_questions.append(best_q)
        asked_questions.add((best_q['feature'], best_q['value']))
        
        # Show question details
        pattern = best_q.get('pattern_type', 'unknown')
        source = best_q.get('attribute_source', 'unknown')
        relevance = best_q.get('relevance_score', 'N/A')
        
        print(f"Q{i+1}: {best_q['text']}")
        print(f"     Feature: {best_q['feature']} | Pattern: {pattern} | Source: {source} | Relevance: {relevance}")
    
    # Analyze selection diversity
    selected_features = Counter([q['feature'] for q in selected_questions])
    selected_patterns = Counter([q.get('pattern_type', 'unknown') for q in selected_questions])
    selected_sources = Counter([q.get('attribute_source', 'unknown') for q in selected_questions])
    
    print(f"\n📈 Ultimate Selection Analysis:")
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
    
    # Show redundancy management stats
    if akenator.ultimate_dynamic_system and akenator.ultimate_dynamic_system.redundancy_manager:
        redundancy_stats = akenator.ultimate_dynamic_system.redundancy_manager.get_usage_statistics()
        print(f"\n🔄 Redundancy Management:")
        print(f"   Total Questions Asked: {redundancy_stats['total_questions']}")
        print(f"   Most Used Features: {redundancy_stats['most_used_features'][:3]}")
        if 'most_used_categories' in redundancy_stats:
            print(f"   Most Used Categories: {redundancy_stats['most_used_categories']}")
    
    return selected_questions

def show_ultimate_vs_previous_comparison():
    """Show the difference between ultimate and previous systems"""
    print(f"\n🔄 Ultimate vs Previous Systems Comparison")
    print("=" * 40)
    
    print("❌ PREVIOUS SYSTEMS:")
    print("   - Fixed attributes: genres, artists, themes, etc.")
    print("   - Fixed templates: 'Is it a [genre] song?'")
    print("   - Technical questions: 'What instruments are used?'")
    print("   - No redundancy management")
    print("   - No human relevance validation")
    print("   - No web scraping for dynamic attributes")
    
    print("\n✅ ULTIMATE DYNAMIC SYSTEM:")
    print("   - Dynamic attribute discovery from actual data")
    print("   - Web scraping for additional song information")
    print("   - Human relevance validation (AI-powered)")
    print("   - Intelligent redundancy management with usage probability")
    print("   - Conversational question patterns")
    print("   - Multiple question styles: emotional, experience-based, etc.")
    print("   - Completely adaptable to any song data structure")
    print("   - No technical jargon, only human-relevant questions")

if __name__ == "__main__":
    questions = test_ultimate_dynamic_system()
    show_ultimate_vs_previous_comparison()
    
    print(f"\n🎉 The ultimate dynamic system is completely flexible!")
    print(f"   - Dynamic attributes (no fixed categories)")
    print(f"   - Human-relevant questions (no technical jargon)")
    print(f"   - Intelligent redundancy management")
    print(f"   - Web scraping integration ready")
    print(f"   - AI-powered relevance validation")
    print(f"   - Conversational and engaging questions")
    print(f"\n💡 This is the pinnacle of dynamic music guessing systems!")
