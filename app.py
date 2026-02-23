from datetime import datetime, timedelta
import uuid

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from backend.logic.engine import Engine
from backend.logic.belief import update_beliefs, update_memory
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
)


# Create Flask app
app = Flask(__name__)

# ENABLE CORS (THIS FIXES "Backend unreachable")
CORS(app)


class Session:

    def __init__(self):

        self.engine = Engine()

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

    def create(self):
        """
        Create a new session and return (session_id, session).
        """
        self.cleanup()
        session_id = str(uuid.uuid4())
        session = Session()
        self._sessions[session_id] = (session, datetime.utcnow())
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


# Start new game
@app.route("/start", methods=["GET"])
def start():

    session_id, session = session_manager.create()

    question = select_best_question(
        session.questions,
        session.songs,
        session.beliefs,
        session.asked
    )

    return jsonify({

        "session_id": session_id,

        "type": "question",

        "feature": question["feature"],

        "value": question["value"],

        "text": question["text"]

    })


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
        reverse=True
    )

    best_id, p1 = sorted_beliefs[0]

    p2 = sorted_beliefs[1][1] if len(sorted_beliefs) > 1 else 0


    # Confidence condition met → return result
    if p1 >= CONFIDENCE_THRESHOLD or (p2 > 0 and p1 / p2 >= DOMINANCE_RATIO):

        for song in session.songs:

            if song["id"] == best_id:

                update_memory(best_id)

                log_session(
                    session_id=session_id,
                    questions=session.history,
                    final_song_id=best_id,
                    confidence=p1,
                )

                return jsonify({

                    "type": "result",

                    "song": song,

                    "confidence": p1

                })


    # Otherwise ask next question
    question = select_best_question(
        session.questions,
        session.songs,
        session.beliefs,
        session.asked
    )

    if question is None:

        return jsonify({

            "type": "unknown"

        })


    return jsonify({

        "type": "question",

        "feature": question["feature"],

        "value": question["value"],

        "text": question["text"]

    })


# Learn new song from Wikidata
@app.route("/learn", methods=["POST"])
def learn():

    data = request.json

    title = data.get("title")

    if not title:

        return jsonify({"error": "title required"}), 400

    song = fetch_song_by_title(title)

    if song:

        append_song(song)

        return jsonify({

            "status": "learned",

            "song": song["title"]

        })

    else:

        return jsonify({

            "status": "not_found"

        })


# Health check (VERY useful)
@app.route("/health", methods=["GET"])
def health():

    return jsonify({

        "status": "ok"

    })


# Serve frontend (optional)
@app.route("/")
def index():

    return send_from_directory("frontend", "index.html")


# Run server
if __name__ == "__main__":

    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
