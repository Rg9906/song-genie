#!/usr/bin/env python3
"""
Start Simple Backend - Guaranteed to Work
"""

import os
import sys

def main():
    print("🚀 Starting SIMPLE Music Akenator Backend...")
    print("🌐 This will definitely fix the 'backend unreachable' problem!")
    print()
    
    try:
        # Import and run the simple backend
        from simple_backend import app
        
        print("✅ Backend loaded successfully!")
        print("🌐 Server will start on: http://127.0.0.1:5000")
        print("🎯 Frontend should connect to this automatically")
        print()
        print("💡 Keep this window open and start your frontend in another window")
        print("💡 Then visit: http://localhost:3000")
        print()
        print("🎵 Let's get this working!")
        print("=" * 50)
        
        # Start the Flask app
        app.run(host="127.0.0.1", port=5000, debug=True)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure you have Flask installed: pip install flask flask-cors")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
