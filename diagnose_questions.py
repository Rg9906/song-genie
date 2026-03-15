#!/usr/bin/env python3
"""
Diagnose why only genre questions are being asked
"""

from backend.logic.simple_enhanced import create_simple_enhanced_akenator
from collections import Counter, defaultdict

def diagnose_question_diversity():
    """Analyze question generation and selection"""
    print("🔍 Diagnosing Question Diversity Issue")
    print("=" * 50)
    
    # Create akenator
    akenator = create_simple_enhanced_akenator(100)
    
    # Get all questions
    all_questions = akenator.get_questions()
    print(f"📊 Total questions available: {len(all_questions)}")
    
    # Analyze question types
    question_types = Counter()
    question_by_type = defaultdict(list)
    
    for q in all_questions:
        question_types[q['feature']] += 1
        question_by_type[q['feature']].append(q)
    
    print(f"\n🎯 Question Types Available:")
    for feature, count in question_types.most_common():
        print(f"   {feature}: {count} questions")
        # Show sample questions
        samples = question_by_type[feature][:3]
        for sample in samples:
            print(f"      - {sample['text']}")
    
    # Simulate question selection
    print(f"\n🎮 Simulating Question Selection...")
    asked_questions = set()
    selected_questions = []
    
    for i in range(10):
        best_q = akenator.get_best_question(asked_questions)
        if not best_q:
            break
            
        selected_questions.append(best_q)
        asked_questions.add((best_q['feature'], best_q['value']))
        
        # Calculate information gain
        score = akenator._calculate_information_gain(best_q)
        
        print(f"   Q{i+1}: {best_q['text']} (score: {score:.3f})")
    
    # Analyze selection pattern
    selected_types = Counter([q['feature'] for q in selected_questions])
    print(f"\n📈 Selected Question Types:")
    for feature, count in selected_types.most_common():
        print(f"   {feature}: {count} times")
    
    # Check if there's a bias
    if len(selected_types) == 1:
        print(f"\n⚠️  PROBLEM: Only {list(selected_types.keys())[0]} questions selected!")
        print(f"💡 This suggests information gain calculation is biased")
        
        # Let's analyze why
        print(f"\n🔍 Analyzing Information Gain Bias...")
        
        # Sample a few questions of each type and compare scores
        for feature in question_types.keys():
            if feature in question_by_type and question_by_type[feature]:
                sample_q = question_by_type[feature][0]
                score = akenator._calculate_information_gain(sample_q)
                matches = sum(1 for song in akenator.songs 
                            if akenator._song_matches_attribute(song, sample_q['feature'], sample_q['value']))
                print(f"   {feature}: score={score:.3f}, matches={matches}/{len(akenator.songs)}")
    
    else:
        print(f"\n✅ Good diversity: {len(selected_types)} different question types")
    
    return selected_questions

def suggest_fix():
    """Suggest fixes for the question diversity issue"""
    print(f"\n🔧 SUGGESTED FIXES:")
    print(f"1. Add diversity penalty to prevent asking same feature repeatedly")
    print(f"2. Balance information gain with question variety")
    print(f"3. Add more artist and decade questions to dataset")
    print(f"4. Use round-robin for first few questions, then optimize")

if __name__ == "__main__":
    selected = diagnose_question_diversity()
    suggest_fix()
    
    print(f"\n💡 Quick fix: Modify get_best_question to prefer different features")
