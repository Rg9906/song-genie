#!/usr/bin/env python3
"""
Simple startup script for Music Akenator
Uses the fixed app with verified components
"""

import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Start the Music Akenator Flask app"""
    try:
        print("🚀 Starting Music Akenator...")
        print("🌐 Using fixed app with verified components")
        
        # Import the fixed app
        from app_fixed import app
        
        # Get configuration
        from backend.logic.config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG
        
        print(f"🌐 Server: http://{FLASK_HOST}:{FLASK_PORT}")
        print(f"🐛 Debug mode: {FLASK_DEBUG}")
        print("✅ Ready to start!")
        
        # Start the app
        app.run(
            host=FLASK_HOST,
            port=FLASK_PORT,
            debug=FLASK_DEBUG
        )
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're in the song-genie directory")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Startup error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
