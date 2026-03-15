#!/usr/bin/env python3
"""
Test that questions are being sent correctly from backend
"""

import requests
import json

def test_question_format():
    """Test the backend question format"""
    print("🔍 Testing backend question format...")
    
    try:
        # Start a new game
        response = requests.get("http://127.0.0.1:5000/start")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Backend response successful")
            print(f"📋 Response structure:")
            print(json.dumps(data, indent=2))
            
            # Check question structure
            if 'question' in data:
                question = data['question']
                print(f"\n🎯 Question object:")
                print(f"   - text: {question.get('text', 'MISSING')}")
                print(f"   - feature: {question.get('feature', 'MISSING')}")
                print(f"   - value: {question.get('value', 'MISSING')}")
                
                if question.get('text'):
                    print(f"\n✅ Question text found: '{question['text']}'")
                    return True
                else:
                    print(f"\n❌ No question text found!")
                    return False
            else:
                print(f"\n❌ No 'question' key in response!")
                return False
        else:
            print(f"❌ Backend request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Question Display Fix")
    print("=" * 40)
    
    success = test_question_format()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 Questions should now display in frontend!")
        print("\n📋 What was fixed:")
        print("- Frontend now reads data.question.text instead of data.text")
        print("- Both start and answer endpoints fixed")
        print("- Questions should appear above the answer buttons")
    else:
        print("❌ Still issues - check backend is running")
    
    print("\n💡 Refresh your frontend to see the fix!")
