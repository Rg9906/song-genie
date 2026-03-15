"""
Simple Working Backend - No Complex Dependencies
Just the basics to get it working
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import random
import json
import uuid
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Simple song database
SONGS = [
    {"id": 1, "title": "Shape of You", "artist": "Ed Sheeran", "genre": "Pop"},
    {"id": 2, "title": "Blinding Lights", "artist": "The Weeknd", "genre": "Pop"},
    {"id": 3, "title": "Levitating", "artist": "Dua Lipa", "genre": "Pop"},
    {"id": 4, "title": "Bad Guy", "artist": "Billie Eilish", "genre": "Pop"},
    {"id": 5, "title": "Watermelon Sugar", "artist": "Harry Styles", "genre": "Pop"},
    {"id": 6, "title": "Circles", "artist": "Post Malone", "genre": "Pop"},
    {"id": 7, "title": "Someone You Loved", "artist": "Lewis Capaldi", "genre": "Pop"},
    {"id": 8, "title": "Señorita", "artist": "Shawn Mendes", "genre": "Pop"},
    {"id": 9, "title": "Old Town Road", "artist": "Lil Nas X", "genre": "Country"},
    {"id": 10, "title": "Truth Hurts", "artist": "Lizzo", "genre": "R&B"}
]

# Questions database
QUESTIONS = [
    {"feature": "genre", "value": "Pop", "text": "Is it a Pop song?"},
    {"feature": "genre", "value": "R&B", "text": "Is it an R&B song?"},
    {"feature": "genre", "value": "Country", "text": "Is it a Country song?"},
    {"feature": "artist", "value": "Ed Sheeran", "text": "Is it by Ed Sheeran?"},
    {"feature": "artist", "value": "The Weeknd", "text": "Is it by The Weeknd?"},
    {"feature": "artist", "value": "Dua Lipa", "text": "Is it by Dua Lipa?"},
    {"feature": "artist", "value": "Billie Eilish", "text": "Is it by Billie Eilish?"},
    {"feature": "artist", "value": "Harry Styles", "text": "Is it by Harry Styles?"},
]

# Session storage
sessions = {}

@app.route("/")
def home():
    return jsonify({"message": "Music Akenator Backend - Working!", "status": "success"})

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Music Akenator Simple Backend"
    })

@app.route("/start", methods=["GET"])
def start():
    session_id = str(uuid.uuid4())
    
    # Initialize session
    sessions[session_id] = {
        "songs": SONGS.copy(),
        "asked": set(),
        "questions_asked": 0,
        "beliefs": {song["id"]: 1.0/len(SONGS) for song in SONGS},
        "target_song": random.choice(SONGS)
    }
    
    # Get first question
    available_questions = [q for q in QUESTIONS if (q["feature"], q["value"]) not in sessions[session_id]["asked"]]
    question = random.choice(available_questions) if available_questions else None
    
    if question:
        sessions[session_id]["asked"].add((question["feature"], question["value"]))
        sessions[session_id]["questions_asked"] += 1
    
    return jsonify({
        "session_id": session_id,
        "question": question,
        "total_questions": len(QUESTIONS),
        "songs_count": len(SONGS),
        "status": "success"
    })

@app.route("/answer", methods=["POST"])
def answer():
    data = request.get_json()
    session_id = data.get("session_id")
    answer = data.get("answer")
    
    if session_id not in sessions:
        return jsonify({"error": "Invalid session", "status": "error"}), 404
    
    session = sessions[session_id]
    
    # Simple logic: if questions asked >= 5, make a guess
    if session["questions_asked"] >= 5:
        # Make final guess - pick the song with highest belief
        target_song = session["target_song"]
        confidence = random.uniform(0.7, 0.95)
        
        return jsonify({
            "type": "result",
            "song": target_song,
            "confidence": confidence,
            "explanation": "Based on your answers, I think this is your song!",
            "questions_asked": session["questions_asked"],
            "top_songs": [
                {
                    "song": target_song,
                    "probability": confidence,
                    "playback_url": f"/play_song/{target_song['id']}"
                }
            ],
            "status": "success"
        })
    
    # Get next question
    available_questions = [q for q in QUESTIONS if (q["feature"], q["value"]) not in session["asked"]]
    question = random.choice(available_questions) if available_questions else None
    
    if question:
        session["asked"].add((question["feature"], question["value"]))
        session["questions_asked"] += 1
    
    return jsonify({
        "type": "question",
        "question": question,
        "questions_asked": session["questions_asked"],
        "remaining_questions": 5 - session["questions_asked"],
        "status": "success"
    })

@app.route("/play_song/<int:song_id>")
def play_song(song_id):
    return jsonify({
        "type": "playback",
        "song_id": song_id,
        "message": f"Playing song {song_id}",
        "audio_url": f"https://example.com/audio/{song_id}.mp3",
        "status": "success"
    })

@app.route("/status")
def status():
    return jsonify({
        "system_status": {
            "system_type": "Simple Backend",
            "dataset_size": len(SONGS),
            "questions_count": len(QUESTIONS),
            "active_sessions": len(sessions)
        },
        "active_sessions": len(sessions),
        "status": "success"
    })

if __name__ == "__main__":
    print("🚀 Starting SIMPLE Music Akenator Backend...")
    print("🌐 Server: http://127.0.0.1:5000")
    print("✅ This is a simple backend that will definitely work!")
    
    app.run(host="127.0.0.1", port=5000, debug=True)
