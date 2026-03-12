from datetime import datetime, timedelta
import uuid

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from backend.logic.engine import Engine
from backend.logic.belief import update_beliefs
from backend.logic.questions import select_best_question
from backend.logic.kg_loader import fetch_song_by_title, append_song
from backend.logic.analytics import log_session, log_feedback
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

# ENABLE CORS (THIS FIXES "Backend unreachable")
CORS(app)


class Session:

    def __init__(self, enable_graph: bool = True, enable_embeddings: bool = False):

        global global_engine
        
        if global_engine is None:
            from backend.logic.hybrid_engine import create_hybrid_engine
            global_engine = create_hybrid_engine(
                enable_graph=enable_graph, 
                enable_embeddings=enable_embeddings
            )

        self.engine = global_engine

        self.songs = self.engine.get_entities()

        self.beliefs = self.engine.get_beliefs()

        self.questions = self.engine.get_questions()

        self.asked = set()
        # Sequence of {"feature", "value", "answer"} for analytics
        self.history = []


class SessionManager:
    """
    Simple in-memory session store with basic time-based expiry.
    Suitable for a single-process deployment.
    """

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

    def create(self, enable_graph: bool = True, enable_embeddings: bool = False) -> Tuple[str, Session]:
        """
        Create a new session and return (session_id, session).
        """
        self.cleanup()
        session_id = str(uuid.uuid4())
        session = Session(enable_graph=enable_graph, enable_embeddings=enable_embeddings)
        self._sessions[session_id] = (session, datetime.utcnow())
        log_new_session(session_id)
        return session_id, session

    def get(self, session_id):
        """
        Return an existing session or None if missing/expired.
        """
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

# Global engine reference for reloading
global_engine = None


# Start new game with optional embedding and graph support
@app.route("/start", methods=["GET"])
def start():
    enable_graph = request.args.get("graph", "true").lower() == "true"
    enable_embeddings = request.args.get("embeddings", "false").lower() == "true"
    
    session_id, session = session_manager.create(
        enable_graph=enable_graph, 
        enable_embeddings=enable_embeddings
    )

    question = select_best_question(
        session.questions,
        session.songs,
        session.beliefs,
        session.asked,
        session.engine
    )

    session.asked.add((question["feature"], question["value"]))

    return jsonify({
        "session_id": session_id,
        "question": {
            "feature": question["feature"],
            "value": question["value"],
            "text": question["text"]
        },
        "total_questions": len(session.questions),
        "graph_enabled": enable_graph,
        "embeddings_enabled": enable_embeddings,
        "system_status": session.engine.get_system_status() if hasattr(session.engine, 'get_system_status') else None
    })


# Get song similarities using embeddings
@app.route("/similar", methods=["GET"])
def similar_songs():
    song_title = request.args.get("song")
    top_k = int(request.args.get("top_k", 5))
    
    if not song_title:
        return jsonify({"error": "song parameter required"}), 400
    
    global global_engine
    if not global_engine or not hasattr(global_engine, 'find_similar_songs'):
        return jsonify({"error": "Embeddings not available"}), 400
    
    try:
        similar = global_engine.find_similar_songs(song_title, top_k)
        return jsonify({
            "song": song_title,
            "similar_songs": similar,
            "embeddings_available": True
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Explain similarity between two songs
@app.route("/explain", methods=["GET"])
def explain_similarity():
    song1 = request.args.get("song1")
    song2 = request.args.get("song2")
    
    if not song1 or not song2:
        return jsonify({"error": "song1 and song2 parameters required"}), 400
    
    global global_engine
    if not global_engine or not hasattr(global_engine, 'explain_similarity'):
        return jsonify({"error": "Embeddings not available"}), 400
    
    try:
        explanation = global_engine.explain_similarity(song1, song2)
        return jsonify(explanation)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Submit answer
@app.route("/answer", methods=["POST"])
def answer():

    data = request.json

    session_id = data.get("session_id")

    feature = data.get("feature")

    value = data.get("value")

    answer = data.get("answer")

    session = session_manager.get(session_id)

    if session is None:

        return jsonify({"error": "invalid or expired session"}), 400

    # Record this Q&A for analytics
    session.history.append({
        "feature": feature,
        "value": value,
        "answer": answer,
    })

    session.beliefs = update_beliefs(
        session.beliefs,
        session.songs,
        feature,
        value,
        answer
    )

    session.asked.add((feature, value))

    sorted_beliefs = sorted(
        session.beliefs.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    best_id, p1 = sorted_beliefs[0]
    p2 = sorted_beliefs[1][1] if len(sorted_beliefs) > 1 else 0.0

    # Precompute top-k candidates for result payloads
    top_k = 3
    top_candidates = sorted_beliefs[:top_k]
    id_to_song = {song["id"]: song for song in session.songs}

    # How many questions have been answered so far in this session.
    num_questions = len(session.history)

    # Hard cap: after MAX_QUESTIONS, stop asking and go to learn mode.
    if num_questions >= MAX_QUESTIONS:

        # Log this as a low-confidence session for analytics.
        log_session(
            session_id=session_id,
            questions=session.history,
            final_song_id=best_id,
            confidence=p1,
        )

        return jsonify({

            "type": "learn",
            "message": "I couldn't confidently guess your song within the question limit. What song were you thinking of?",
            "top_songs": [
                {
                    "song": id_to_song.get(song_id),
                    "probability": prob,
                }
                for song_id, prob in top_candidates
                if id_to_song.get(song_id) is not None
            ],

        })

    # Confidence condition met → return result.
    # We now require:
    # - enough questions asked (MIN_QUESTIONS_BEFORE_GUESS)
    # - AND high absolute confidence
    # - AND clear dominance over the runner-up (ratio)
    # - AND a minimum absolute margin over the runner-up
    if (
        num_questions >= MIN_QUESTIONS_BEFORE_GUESS
        and p1 >= CONFIDENCE_THRESHOLD
        and (p2 == 0.0 or p1 / p2 >= DOMINANCE_RATIO)
        and (p1 - p2) >= MIN_CONFIDENCE_MARGIN
    ):

        # Only log the session here; actual learning
        # (updating memory) happens when the user
        # confirms via the /feedback endpoint.
        log_session(
            session_id=session_id,
            questions=session.history,
            final_song_id=best_id,
            confidence=p1,
        )

        primary_song = id_to_song.get(best_id)

        return jsonify({

            "type": "result",

            # Backwards compatible primary guess
            "song": primary_song,
            "confidence": p1,

            # New: top-k candidates with probabilities
            "top_songs": [
                {
                    "song": id_to_song.get(song_id),
                    "probability": prob,
                }
                for song_id, prob in top_candidates
                if id_to_song.get(song_id) is not None
            ],

        })


    # Otherwise ask next question (or admit we don't know)
    question = select_best_question(
        session.questions,
        session.songs,
        session.beliefs,
        session.asked,
        session.engine
    )

    if question is None:

        # We've exhausted discriminative questions without
        # reaching a confident guess. Signal that we don't
        # know and let the frontend trigger learning mode.
        return jsonify({

            "type": "learn",
            "message": "I couldn't confidently guess your song. What song were you thinking of?"

        })


    return jsonify({

        "type": "question",

        "feature": question["feature"],

        "value": question["value"],

        "text": question["text"]

    })


# Learn new song from Wikidata with smart pattern analysis
@app.route("/learn", methods=["POST"])
def learn():
    global global_engine

    data = request.json
    title = data.get("title")
    session_id = data.get("session_id")  # Get session ID for analysis
    
    if not title:
        return jsonify({"error": "title required"}), 400

    # Get session data for pattern analysis
    session = session_manager.get(session_id) if session_id else None
    session_questions = session.history if session else []
    
    # Use smart learning system
    from backend.logic.learning import learn_from_feedback
    
    result = learn_from_feedback(session_id, session_questions, title.strip())
    
    if result["status"] in ["learned", "updated"]:
        # Reload the global engine to include the new/updated song
        if global_engine:
            global_engine.reload()
        
        return jsonify({
            "status": result["status"],
            "song": title,
            "analysis": result.get("analysis_summary", {})
        })
    else:
        return jsonify({
            "status": "failed",
            "reason": result.get("reason", "Unknown error"),
            "song": title
        })


# Health check (VERY useful)
@app.route("/health", methods=["GET"])
def health():

    return jsonify({

        "status": "ok"

    })


# Submit feedback with smart learning for wrong guesses
@app.route("/feedback", methods=["POST"])
def feedback():
    """
    Handle user feedback with smart learning for wrong guesses.
    """
    data = request.json
    session_id = data.get("session_id")
    correct = data.get("correct")
    correct_song_title = data.get("correct_song_title")  # User-provided correct song
    
    if not session_id or correct is None:
        return jsonify({"error": "session_id and correct required"}), 400

    session = session_manager.get(session_id)
    if not session:
        return jsonify({"error": "session not found"}), 404

    # Log basic feedback
    log_feedback(session_id, correct, correct_song_title)

    # If the guess was wrong and user provided correct song, apply smart learning
    if not correct and correct_song_title:
        try:
            from backend.logic.smart_learning import learn_from_wrong_guess
            
            learning_result = learn_from_wrong_guess(
                session_id, 
                session.history, 
                correct_song_title.strip()
            )
            
            # Reload engine if learning was successful
            if learning_result.get("status") == "learned":
                global global_engine
                if global_engine:
                    global_engine.reload()
            
            return jsonify({
                "status": "processed",
                "learning": learning_result
            })
            
        except Exception as e:
            # Log error but don't fail the feedback
            print(f"Smart learning error: {e}")
            return jsonify({
                "status": "processed",
                "learning": {"status": "failed", "reason": "Learning system error"}
            })
    
    return jsonify({"status": "processed"})


@app.route("/sessions", methods=["GET"])
def sessions_view():
    from backend.logic.analytics import get_session_summaries
    return jsonify({"sessions": get_session_summaries()})


@app.route("/insights", methods=["GET"])
def insights_view():
    from backend.logic.analytics import get_insights
    return jsonify(get_insights())


# Serve frontend (optional)
@app.route("/")
def index():

    return send_from_directory("frontend", "index.html")


# Run server
if __name__ == "__main__":

    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
