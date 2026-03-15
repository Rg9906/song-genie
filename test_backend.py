#!/usr/bin/env python3
"""
Simple backend test to verify it's working
"""

import requests
import json
import time

def test_backend():
    """Test backend endpoints"""
    base_url = "http://127.0.0.1:5000"
    
    print("🔍 Testing backend endpoints...")
    
    # Test 1: Health check
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"✅ Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test 2: Start game
    try:
        response = requests.get(f"{base_url}/start", timeout=5)
        print(f"✅ Start game: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Session ID: {data.get('session_id', 'N/A')}")
            print(f"   Songs count: {data.get('songs_count', 'N/A')}")
            print(f"   Question: {data.get('question', {}).get('text', 'N/A')}")
            return True
    except Exception as e:
        print(f"❌ Start game failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing backend connection...")
    print("Make sure the backend is running with: python start_fixed.py")
    print()
    
    success = test_backend()
    
    if success:
        print("\n🎉 Backend is working correctly!")
    else:
        print("\n❌ Backend is not responding.")
        print("💡 Make sure to run: python start_fixed.py")
