#!/usr/bin/env python3
"""
Test Gemini API integration
"""

from backend.logic.gemini_service import GeminiService

def test_gemini():
    print("🤖 Testing Gemini API Integration")
    print("=" * 40)
    
    # Initialize Gemini service
    gemini = GeminiService()
    
    print(f"🔑 API Key Available: {'✅' if gemini.is_available else '❌'}")
    print(f"📊 Service Status: {gemini.get_status()}")
    
    if not gemini.is_available:
        print("❌ Gemini API not available")
        return
    
    # Sample song data for testing
    sample_songs = [
        {'artists': ['Taylor Swift'], 'genres': ['pop'], 'themes': ['love']},
        {'artists': ['Drake'], 'genres': ['hip-hop'], 'themes': ['relationships']},
        {'artists': ['Ed Sheeran'], 'genres': ['pop'], 'themes': ['romance']},
        {'artists': ['Billie Eilish'], 'genres': ['alternative'], 'themes': ['dark']}
    ]
    
    print(f"\n🎵 Testing with {len(sample_songs)} sample songs")
    
    # Test question generation
    print(f"\n🎯 Generating AI Questions:")
    for i in range(3):
        question = gemini.generate_question(sample_songs, set())
        if question:
            print(f"Q{i+1}: \"{question['text']}\"")
            print(f"     Source: {question['source']} | Model: {question['model']}")
        else:
            print(f"Q{i+1}: ❌ Failed to generate question")
    
    # Test question improvement
    print(f"\n🔧 Testing Question Improvement:")
    original = "Is this a pop song?"
    improved = gemini.improve_question_text(original)
    if improved:
        print(f"Original: \"{original}\"")
        print(f"Improved: \"{improved}\"")
    else:
        print("❌ Failed to improve question")

if __name__ == "__main__":
    test_gemini()
