#!/usr/bin/env python3
"""
Test the fixed question diversity in an actual game
"""

import requests
import json

def test_game_diversity():
    """Test a full game to see question diversity"""
    print("🎮 Testing Game Question Diversity")
    print("=" * 40)
    
    # Start game
    response = requests.get("http://127.0.0.1:5000/start")
    if response.status_code != 200:
        print("❌ Failed to start game")
        return
    
    data = response.json()
    session_id = data['session_id']
    print(f"✅ Game started: {session_id[:8]}...")
    
    # Play through 10 questions
    questions = []
    for i in range(10):
        if i == 0:
            # First question from start response
            question = data['question']
        else:
            # Get next question
            answer_response = requests.post("http://127.0.0.1:5000/answer", 
                json={"session_id": session_id, "answer": "no"})
            
            if answer_response.status_code != 200:
                print(f"❌ Failed to get answer {i+1}")
                break
                
            answer_data = answer_response.json()
            
            if answer_data.get('type') == 'result':
                print(f"🎯 Game ended after {i} questions")
                break
                
            question = answer_data['question']
        
        questions.append(question)
        print(f"Q{i+1}: {question['text']} ({question['feature']})")
    
    # Analyze diversity
    from collections import Counter
    question_types = Counter([q['feature'] for q in questions])
    
    print(f"\n📊 Question Diversity:")
    for feature, count in question_types.most_common():
        print(f"   {feature}: {count} questions")
    
    if len(question_types) >= 3:
        print(f"\n✅ Good diversity! {len(question_types)} different question types")
    else:
        print(f"\n⚠️  Limited diversity: only {len(question_types)} question types")
    
    return questions

if __name__ == "__main__":
    test_game_diversity()
    print(f"\n💡 Refresh your frontend to see the improved question variety!")
