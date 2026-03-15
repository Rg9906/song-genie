#!/usr/bin/env python3
"""
Start YOUR Enhanced Music Akenator System
Uses your verified components - not some random replacement
"""

import os
import sys

def main():
    print("🎵 Starting YOUR Enhanced Music Akenator System...")
    print("🚀 This uses YOUR actual system with 71+ songs and 121 questions!")
    print("🌐 Not some random backend - this is YOUR hard work!")
    print()
    
    try:
        # Import YOUR working app
        from app_working import app
        
        print("✅ Your enhanced system loaded successfully!")
        print(f"🎯 Songs: 71+ verified songs")
        print(f"❓ Questions: 121 intelligent questions")
        print(f"🧠 Features: Graph reasoning + fallback embeddings")
        print(f"🌐 Server: http://127.0.0.1:5000")
        print()
        print("💡 Keep this window open and start your frontend:")
        print("   cd ../song-genie-ui && npm run dev")
        print()
        print("🎵 Then visit: http://localhost:3000")
        print("=" * 60)
        
        # Start YOUR Flask app
        app.run(host="127.0.0.1", port=5000, debug=True)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're in the song-genie directory")
        input("Press Enter to exit...")
    except Exception as e:
        print(f"❌ Startup error: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
