#!/usr/bin/env python3
"""
Run both frontend and backend together
"""

import subprocess
import time
import threading
import sys
import os

def run_backend():
    """Run the backend server"""
    print("🚀 Starting backend server...")
    try:
        subprocess.run([sys.executable, "start_fixed.py"], cwd=os.getcwd())
    except KeyboardInterrupt:
        print("\n🛑 Backend stopped")

def run_frontend():
    """Run the frontend server"""
    print("🚀 Starting frontend server...")
    try:
        subprocess.run(["npm", "run", "dev"], cwd="../song-genie-ui")
    except KeyboardInterrupt:
        print("\n🛑 Frontend stopped")

def main():
    """Main function to run both servers"""
    print("🎵 Music Akenator - Starting Both Servers")
    print("=" * 50)
    
    # Check if backend directory exists
    if not os.path.exists("start_fixed.py"):
        print("❌ start_fixed.py not found. Make sure you're in the song-genie directory.")
        return
    
    # Check if frontend directory exists
    if not os.path.exists("../song-genie-ui"):
        print("❌ Frontend directory not found.")
        return
    
    print("📍 Backend will run on: http://127.0.0.1:5000")
    print("📍 Frontend will run on: http://localhost:3000")
    print()
    print("💡 Press Ctrl+C to stop both servers")
    print("=" * 50)
    
    # Start backend in a separate thread
    backend_thread = threading.Thread(target=run_backend)
    backend_thread.daemon = True
    backend_thread.start()
    
    # Wait a bit for backend to start
    time.sleep(3)
    
    # Start frontend in main thread
    try:
        run_frontend()
    except KeyboardInterrupt:
        print("\n🛑 Stopping servers...")

if __name__ == "__main__":
    main()
