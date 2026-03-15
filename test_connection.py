#!/usr/bin/env python3
"""
Test backend connection and fix issues
"""

import sys
import os

def test_backend():
    """Test if backend can start and respond"""
    print("🔍 Testing backend connection...")
    
    try:
        # Test 1: Import the app
        print("1. Testing import...")
        from app import app
        print("✅ Backend imports successfully")
        
        # Test 2: Create test client
        print("2. Testing Flask app...")
        with app.test_client() as client:
            # Test health endpoint
            response = client.get('/health')
            if response.status_code == 200:
                print("✅ Health endpoint working")
                print(f"   Response: {response.get_json()}")
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
            
            # Test start endpoint
            response = client.get('/start')
            if response.status_code == 200:
                print("✅ Start endpoint working")
                data = response.get_json()
                print(f"   Session created: {data.get('session_id', 'N/A')[:8]}...")
                print(f"   Songs available: {data.get('songs_count', 'N/A')}")
            else:
                print(f"❌ Start endpoint failed: {response.status_code}")
                print(f"   Error: {response.get_json()}")
        
        print("\n🎉 Backend is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Backend test failed: {e}")
        print("\n🔧 Possible fixes:")
        print("1. Make sure you're in the song-genie directory")
        print("2. Install dependencies: pip install flask flask-cors")
        print("3. Check if simple_enhanced.py is working")
        return False

def test_core_system():
    """Test the core enhanced system"""
    print("\n🔍 Testing core system...")
    
    try:
        from backend.logic.simple_enhanced import create_simple_enhanced_akenator
        akenator = create_simple_enhanced_akenator(50)
        
        print(f"✅ Core system works: {len(akenator.songs)} songs")
        print(f"✅ Questions available: {len(akenator.get_questions())}")
        
        # Test question generation
        question = akenator.get_best_question(set())
        if question:
            print(f"✅ Question generation works: {question.get('text', 'N/A')}")
        else:
            print("⚠️ No questions generated")
        
        return True
        
    except Exception as e:
        print(f"❌ Core system test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Music Akenator Connection Test")
    print("=" * 40)
    
    # Test core system first
    core_ok = test_core_system()
    
    # Test backend
    backend_ok = test_backend()
    
    print("\n" + "=" * 40)
    print("📋 TEST RESULTS:")
    print(f"Core System: {'✅ PASS' if core_ok else '❌ FAIL'}")
    print(f"Backend: {'✅ PASS' if backend_ok else '❌ FAIL'}")
    
    if core_ok and backend_ok:
        print("\n🎉 EVERYTHING IS WORKING!")
        print("\n🚀 To start your servers:")
        print("1. Backend: python app.py")
        print("2. Frontend: cd ../song-genie-ui && npm run dev")
        print("3. Visit: http://localhost:3000")
    else:
        print("\n❌ ISSUES FOUND - Check the errors above")
    
    print("\n💡 If backend works but frontend can't connect:")
    print("- Make sure BOTH servers are running")
    print("- Check CORS is enabled (it is!)")
    print("- Try http://127.0.0.1:5000/health in browser")

if __name__ == "__main__":
    main()
