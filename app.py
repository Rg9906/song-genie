from flask import Flask, jsonify, request, send_from_directory
import uuid

from backend.logic.engine import Engine
from backend.logic.belief import update_beliefs, update_memory
from backend.logic.questions import select_best_question
from backend.logic.kg_loader import fetch_song_by_title, append_song


app = Flask(__name__)

# Store active sessions
sessions = {}

CONFIDENCE_THRESHOLD = 0.85
DOMINANCE_RATIO = 3.0


# Session object
class Session:

    def __init__(self):

        self.engine = Engine()

        self.songs = self.engine.get_entities()

        self.beliefs = self.engine.get_beliefs()

        self.questions = self.engine.get_questions()

        self.asked = set()


# Start new game
@app.route("/start")

def start():

    session_id = str(uuid.uuid4())

    session = Session()

    sessions[session_id] = session

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

    if session_id not in sessions:

        return jsonify({"error": "invalid session"}), 400

    session = sessions[session_id]

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
    if p1 >= CONFIDENCE_THRESHOLD or (p2 > 0 and p1/p2 >= DOMINANCE_RATIO):

        for song in session.songs:

            if song["id"] == best_id:

                update_memory(best_id)

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


# Serve frontend
@app.route("/")

def index():

    return send_from_directory("frontend", "index.html")


# Run server
if __name__ == "__main__":

    app.run(debug=True)
