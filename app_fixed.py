"""
Fixed Music Akenator Flask App
Uses verified simple_enhanced.py system
"""

from datetime import datetime, timedelta
import uuid
import logging
from typing import Tuple

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from backend.logic.config import (
    CONFIDENCE_THRESHOLD,
    DOMINANCE_RATIO,
    FLASK_DEBUG,
    FLASK_HOST,
    FLASK_PORT,
    SESSION_TTL_SECONDS,
    MIN_QUESTIONS_BEFORE_GUESS,
    MIN_CONFIDENCE_MARGIN,
    MAX_QUESTIONS,
)

# Create Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ENABLE CORS (THIS FIXES "Backend unreachable")
CORS(app)


class Session:
    """Game session using verified simple_enhanced system"""
    
    def __init__(self, target_dataset_size: int = 100):
        try:
            from backend.logic.simple_enhanced import create_simple_enhanced_akenator
            self.akenator = create_simple_enhanced_akenator(target_dataset_size)
            self.songs = self.akenator.get_entities()
            self.beliefs = self.akenator.get_beliefs()
            self.questions = self.akenator.get_questions()
            self.asked = set()
            self.history = []
            self.target_dataset_size = target_dataset_size
            logger.info(f"✅ Session created with {len(self.songs)} songs")
        except Exception as e:
            logger.error(f"❌ Failed to create session: {e}")
            self.akenator = None
            self.songs = []
            self.beliefs = {}
            self.questions = []
            self.asked = set()
            self.history = []
            self.target_dataset_size = 100


class SessionManager:
    """Simple in-memory session store with basic time-based expiry."""
    
    def __init__(self):
        self._sessions = {}
        self._ttl = timedelta(seconds=SESSION_TTL_SECONDS)

    def _is_expired(self, created_at: datetime) -> bool:
        return datetime.utcnow() - created_at > self._ttl

    def cleanup(self) -> None:
        now = datetime.utcnow()
        expired_keys = [
            key
            for key, (_, created_at) in self._sessions.items()
            if now - created_at > self._ttl
        ]
        for key in expired_keys:
            self._sessions.pop(key, None)

    def create(self, target_dataset_size: int = 100) -> Tuple[str, Session]:
        """Create a new session and return (session_id, session)."""
        self.cleanup()
        session_id = str(uuid.uuid4())
        session = Session(target_dataset_size)
        self._sessions[session_id] = (session, datetime.utcnow())
        logger.info(f"🆔 Created session {session_id}")
        return session_id, session

    def get(self, session_id):
        """Return an existing session or None if missing/expired."""
        self.cleanup()
        value = self._sessions.get(session_id)
        if value is None:
            return None
        session, created_at = value
        if self._is_expired(created_at):
            self._sessions.pop(session_id, None)
            return None
        return session


session_manager = SessionManager()


@app.route("/")
def index():
    """Serve the frontend."""
    return send_from_directory("frontend", "index.html")


@app.route("/start", methods=["GET"])
def start():
    """Start a new game session."""
    try:
        # Get dataset size parameter (default 100)
        target_size = int(request.args.get("size", "100"))
        target_size = max(10, min(1000, target_size))  # Limit between 10-1000
        
        logger.info(f"🚀 Starting new game with {target_size} songs")
        
        session_id, session = session_manager.create(target_dataset_size)
        
        # Get first question
        best_question = session.akenator.get_best_question(session.asked)
        
        if best_question:
            session.asked.add((best_question["feature"], best_question["value"]))
            question_data = {
                "feature": best_question["feature"],
                "value": best_question["value"],
                "text": best_question["text"]
            }
        else:
            question_data = None
        
        return jsonify({
            "session_id": session_id,
            "question": question_data,
            "total_questions": len(session.questions),
            "songs_count": len(session.songs),
            "dataset_size": target_size,
            "status": "success"
        })
        
    except Exception as e:
        logger.error(f"❌ Start endpoint error: {e}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500


@app.route("/answer", methods=["POST"])
def answer():
    """Process user answer and return next question or guess."""
    try:
        data = request.get_json()
        session_id = data.get("session_id")
        answer = data.get("answer")
        
        if not session_id or answer is None:
            return jsonify({
                "error": "Missing session_id or answer",
                "status": "error"
            }), 400
        
        session = session_manager.get(session_id)
        if not session:
            return jsonify({
                "error": "Invalid or expired session",
                "status": "error"
            }), 404
        
        if not session.akenator:
            return jsonify({
                "error": "Session not properly initialized",
                "status": "error"
            }), 500
        
        # Get last asked question from history
        if session.history:
            last_question = session.history[-1]
            
            # Update beliefs with answer
            new_beliefs = session.akenator.update_beliefs(last_question, answer)
            session.beliefs = new_beliefs
            
            # Record answer
            last_question["answer"] = answer
            logger.info(f"📝 Answer recorded: {last_question['feature']} = {answer}")
        
        # Check if should make guess
        questions_asked = len(session.asked)
        should_guess, guess_id = session.akenator.should_make_guess(questions_asked)
        
        if should_guess or questions_asked >= MAX_QUESTIONS:
            # Make final guess
            top_candidates = session.akenator.get_top_candidates(3)
            
            if top_candidates:
                # Get song details for top candidate
                guessed_song_id = top_candidates[0][0]
                guessed_song = None
                
                for song in session.songs:
                    if song['id'] == guessed_song_id:
                        guessed_song = song
                        break
                
                if guessed_song:
                    confidence, explanation = session.akenator.get_confidence(guessed_song_id)
                    
                    # Create response with top songs and playback URLs
                    response = {
                        "type": "result",
                        "song": guessed_song,
                        "confidence": confidence,
                        "explanation": explanation,
                        "questions_asked": questions_asked,
                        "top_songs": [
                            {
                                "song": session.songs[song_id] if song_id < len(session.songs) else guessed_song,
                                "probability": prob,
                                "playback_url": f"/play_song/{song_id}"
                            }
                            for song_id, prob, _ in top_candidates
                        ],
                        "status": "success"
                    }
                    
                    logger.info(f"🎯 Final guess: {guessed_song['title']} (confidence: {confidence:.3f})")
                    return jsonify(response)
            
            # Fallback if no candidates
            return jsonify({
                "type": "result",
                "error": "Unable to determine song",
                "questions_asked": questions_asked,
                "status": "error"
            })
        
        else:
            # Get next question
            best_question = session.akenator.get_best_question(session.asked)
            
            if best_question:
                session.asked.add((best_question["feature"], best_question["value"]))
                session.history.append({
                    "feature": best_question["feature"],
                    "value": best_question["value"],
                    "text": best_question["text"]
                })
                
                return jsonify({
                    "type": "question",
                    "question": {
                        "feature": best_question["feature"],
                        "value": best_question["value"],
                        "text": best_question["text"]
                    },
                    "questions_asked": questions_asked,
                    "remaining_questions": MAX_QUESTIONS - questions_asked,
                    "status": "success"
                })
            else:
                # No more questions available
                return jsonify({
                    "type": "result",
                    "error": "No more questions available",
                    "questions_asked": questions_asked,
                    "status": "error"
                })
    
    except Exception as e:
        logger.error(f"❌ Answer endpoint error: {e}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500


@app.route("/play_song/<int:song_id>", methods=["GET"])
def play_song(song_id):
    """Play song with highest probability after guess."""
    try:
        # This is a placeholder - in real implementation, you would:
        # 1. Look up the song in your database
        # 2. Return actual audio file or streaming URL
        
        return jsonify({
            "type": "playback",
            "song_id": song_id,
            "message": f"Playing song {song_id}",
            "audio_url": f"https://example.com/audio/{song_id}.mp3",
            "status": "success"
        })
        
    except Exception as e:
        logger.error(f"❌ Play song error: {e}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500


@app.route("/status", methods=["GET"])
def status():
    """Get system status."""
    try:
        from backend.logic.simple_enhanced import create_simple_enhanced_akenator
        akenator = create_simple_enhanced_akenator(50)
        system_status = akenator.get_system_status()
        
        return jsonify({
            "system_status": system_status,
            "active_sessions": len(session_manager._sessions),
            "flask_debug": FLASK_DEBUG,
            "host": FLASK_HOST,
            "port": FLASK_PORT,
            "status": "success"
        })
        
    except Exception as e:
        logger.error(f"❌ Status endpoint error: {e}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Music Akenator"
    })


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "status": "error"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"❌ Internal server error: {error}")
    return jsonify({
        "error": "Internal server error",
        "status": "error"
    }), 500


if __name__ == "__main__":
    logger.info("🚀 Starting Music Akenator Flask App...")
    logger.info(f"🌐 Server: http://{FLASK_HOST}:{FLASK_PORT}")
    logger.info(f"🐛 Debug mode: {FLASK_DEBUG}")
    
    app.run(
        host=FLASK_HOST,
        port=FLASK_PORT,
        debug=FLASK_DEBUG
    )
