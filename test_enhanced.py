#!/usr/bin/env python3
"""
Test script for Enhanced Music Akenator
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from backend.logic.simple_enhanced import create_simple_enhanced_akenator

def test_enhanced_system():
    """Test the enhanced Music Akenator system"""
    print("🚀 Testing Enhanced Music Akenator...")
    
    # Create enhanced system
    akenator = create_simple_enhanced_akenator(100)
    print(f"✅ Created system with {len(akenator.songs)} songs")
    
    # Test question generation
    questions = akenator.get_questions()
    print(f"✅ Generated {len(questions)} questions")
    
    # Test best question selection
    best_question = akenator.get_best_question(set())
    if best_question:
        print(f"✅ Best question: {best_question['text']}")
        print(f"   Feature: {best_question['feature']}")
        print(f"   Value: {best_question['value']}")
    else:
        print("⚠️  No best question found")
    
    # Test belief update
    if best_question:
        print("\n🔄 Testing belief update...")
        initial_beliefs = akenator.get_beliefs()
        print(f"Initial beliefs: {len(initial_beliefs)} songs")
        
        # Simulate answer
        answer = "yes"
        new_beliefs = akenator.update_beliefs(best_question, answer)
        print(f"✅ Updated beliefs after answer: {answer}")
        
        # Test confidence
        top_candidates = akenator.get_top_candidates(3)
        print(f"✅ Top 3 candidates:")
        for i, (song_id, belief, explanation) in enumerate(top_candidates):
            song = akenator.songs[song_id]
            print(f"   {i+1}. {song['title']} - {belief:.3f} ({explanation})")
    
    # Test system status
    status = akenator.get_system_status()
    print(f"\n📊 System Status:")
    print(f"   System Type: {status['system_type']}")
    print(f"   Dataset Size: {status['dataset_size']}")
    print(f"   Target Size: {status['target_dataset_size']}")
    print(f"   Active Songs: {status['active_songs']}")
    print(f"   Features: {', '.join(status['features'])}")
    
    print("\n🎉 Enhanced Music Akenator test completed successfully!")

if __name__ == "__main__":
    test_enhanced_system()
