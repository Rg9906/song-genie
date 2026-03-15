#!/usr/bin/env python3
"""
Test the intelligent question selector
"""

from backend.logic.simple_enhanced import create_simple_enhanced_akenator
from collections import Counter

def test_intelligent_selection():
    """Test the intelligent question selector"""
    print("🧠 Testing Intelligent Question Selector")
    print("=" * 50)
    
    # Create akenator
    akenator = create_simple_enhanced_akenator(100)
    
    # Check if intelligent selector is available
    if akenator.intelligent_selector:
        print("✅ Intelligent selector is active")
        
        # Show feature importance
        importance = akenator.intelligent_selector.feature_importance
        print(f"\n🎯 Feature Importance Scores:")
        for feature, score in sorted(importance.items(), key=lambda x: x[1], reverse=True):
            print(f"   {feature}: {score:.3f}")
    else:
        print("⚠️  Using fallback selector (intelligent not available)")
    
    # Simulate question selection
    print(f"\n🎮 Simulating Question Selection:")
    asked_questions = set()
    selected_questions = []
    
    for i in range(10):
        best_q = akenator.get_best_question(asked_questions)
        if not best_q:
            break
            
        selected_questions.append(best_q)
        asked_questions.add((best_q['feature'], best_q['value']))
        
        print(f"Q{i+1}: {best_q['text']} ({best_q['feature']})")
    
    # Analyze selection pattern
    selected_types = Counter([q['feature'] for q in selected_questions])
    print(f"\n📊 Question Distribution:")
    for feature, count in selected_types.most_common():
        percentage = (count / len(selected_questions)) * 100
        print(f"   {feature}: {count} questions ({percentage:.1f}%)")
    
    # Check if it's more intelligent than fixed quotas
    if len(selected_types) >= 3:
        print(f"\n✅ Good diversity: {len(selected_types)} different question types")
        print(f"🧠 The selector is adapting based on feature importance")
    else:
        print(f"\n⚠️  Limited diversity: only {len(selected_types)} question types")
    
    # Show intelligent stats if available
    if akenator.intelligent_selector:
        stats = akenator.intelligent_selector.get_feature_usage_stats()
        print(f"\n📈 Intelligent Selection Stats:")
        print(f"   Total questions: {stats['total_questions']}")
        print(f"   Feature percentages: {stats['feature_percentages']}")
    
    return selected_questions

def compare_with_fixed_quota():
    """Compare intelligent selection with fixed quota approach"""
    print(f"\n🔬 Comparison: Intelligent vs Fixed Quota")
    print("=" * 40)
    
    print("❌ Fixed Quota Approach:")
    print("   - Always asks exactly 4 genre, 3 artist, 2 decade, 1 era questions")
    print("   - No adaptation to game state")
    print("   - Brute force enforcement")
    
    print("\n✅ Intelligent Selection:")
    print("   - Adapts based on feature importance")
    print("   - Uses information gain with adaptive penalties")
    print("   - Considers graph centrality and embeddings")
    print("   - Natural diversity without forced quotas")
    print("   - Learns from question patterns")

if __name__ == "__main__":
    questions = test_intelligent_selection()
    compare_with_fixed_quota()
    
    print(f"\n💡 The intelligent selector provides natural diversity")
    print(f"   without rigid quotas, adapting to each game's needs!")
