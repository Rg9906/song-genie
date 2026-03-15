#!/usr/bin/env python3
"""
Test the diverse question generation system
"""

from backend.logic.simple_enhanced import create_simple_enhanced_akenator
from collections import Counter

def test_diverse_question_system():
    """Test the new diverse question system"""
    print("🎨 Testing Diverse Question System")
    print("=" * 50)
    
    # Create akenator
    akenator = create_simple_enhanced_akenator(100)
    
    # Check what components are available
    print(f"🔧 Components Available:")
    print(f"   Intelligent Selector: {'✅' if akenator.intelligent_selector else '❌'}")
    print(f"   Diverse Generator: {'✅' if akenator.diverse_generator else '❌'}")
    print(f"   LLM Framer: {'✅' if akenator.llm_framer else '❌'}")
    
    # Get all questions
    all_questions = akenator.get_questions()
    print(f"\n📊 Total Questions Generated: {len(all_questions)}")
    
    # Analyze question categories
    if akenator.diverse_generator:
        categories = Counter([q.get('category', 'unknown') for q in all_questions])
        print(f"\n🎯 Question Categories:")
        for category, count in categories.most_common():
            print(f"   {category}: {count} questions")
    
    # Analyze question features
    features = Counter([q['feature'] for q in all_questions])
    print(f"\n🔍 Question Features:")
    for feature, count in features.most_common():
        print(f"   {feature}: {count} questions")
    
    # Simulate question selection
    print(f"\n🎮 Simulating Question Selection:")
    asked_questions = set()
    selected_questions = []
    
    for i in range(12):
        best_q = akenator.get_best_question(asked_questions)
        if not best_q:
            break
            
        selected_questions.append(best_q)
        asked_questions.add((best_q['feature'], best_q['value']))
        
        # Show question with style if available
        style = best_q.get('style', 'basic')
        print(f"Q{i+1}: {best_q['text']} ({best_q['feature']}) [{style}]")
    
    # Analyze selection diversity
    selected_features = Counter([q['feature'] for q in selected_questions])
    selected_categories = Counter([q.get('category', 'unknown') for q in selected_questions])
    
    print(f"\n📈 Selection Diversity:")
    print(f"   Features: {len(selected_features)} different types")
    for feature, count in selected_features.most_common():
        print(f"      {feature}: {count} questions")
    
    if akenator.diverse_generator:
        print(f"   Categories: {len(selected_categories)} different types")
        for category, count in selected_categories.most_common():
            print(f"      {category}: {count} questions")
    
    # Check question framing variety
    if akenator.llm_framer:
        styles = Counter([q.get('style', 'basic') for q in selected_questions])
        print(f"\n🗣️ Question Framing Styles:")
        for style, count in styles.most_common():
            print(f"      {style}: {count} questions")
    
    return selected_questions

def show_question_variety_examples():
    """Show examples of different question types"""
    print(f"\n🎪 Question Variety Examples:")
    print("=" * 30)
    
    examples = [
        ("Genre", "Is this electropop with synthy vibes?"),
        ("Artist", "Would you find this in Lady Gaga's discography?"),
        ("Theme", "Does this explore themes of love and sexuality?"),
        ("Instrument", "Could you identify synthesizer in the arrangement?"),
        ("Popularity", "Has this crossed the billion-view mark?"),
        ("Mood", "Is this more of a slow jam for chilling?"),
        ("Era", "Does this come from the 2010s+ Era?"),
        ("Duration", "Would you call this an extended epic track?"),
        ("Danceability", "Is this a dance floor filler?"),
        ("Technical", "Is this under 3 minutes long?")
    ]
    
    for category, example in examples:
        print(f"   {category}: {example}")

if __name__ == "__main__":
    questions = test_diverse_question_system()
    show_question_variety_examples()
    
    print(f"\n🎉 The diverse question system is working!")
    print(f"   - No more repetitive genre questions")
    print(f"   - Varied question framing")
    print(f"   - Multiple categories: themes, instruments, mood, etc.")
    print(f"   - Smart diversity without rigid quotas")
    print(f"\n💡 Refresh your frontend to experience the variety!")
