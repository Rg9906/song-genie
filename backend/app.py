from flask import Flask, jsonify, request
from logic.game import Game
import csv
import uuid

app = Flask(__name__)

SONGS_PATH = "backend/data/songs.csv"

# 🔥 store active games per session
games = {}


def get_game(session_id):
    return games.get(session_id)


@app.route("/start")
def start():
    # 🔥 create new session
    session_id = str(uuid.uuid4())
    games[session_id] = Game()

    game = games[session_id]
    first_step = game.next_question()

    return jsonify({
        "session_id": session_id,
        "data": first_step
    })


@app.route("/answer", methods=["POST"])
def answer():
    data = request.json
    session_id = data.get("session_id")
    user_answer = data.get("answer")

    if not session_id or session_id not in games:
        return jsonify({"error": "invalid session"}), 400

    game = games[session_id]
    return jsonify(game.answer(user_answer))


@app.route("/learn", methods=["POST"])
def learn():
    data = request.json
    session_id = data.get("session_id")

    if not session_id or session_id not in games:
        return jsonify({"error": "invalid session"}), 400

    game = games[session_id]

    title = data.get("title")
    artist = data.get("artist", "Unknown")

    if not title:
        return jsonify({"error": "title is required"}), 400

    inferred = game.infer_features()

    # generate new ID
    with open(SONGS_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        new_id = max(int(row["id"]) for row in rows) + 1

    # append new song with low confidence
    with open(SONGS_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            new_id,
            title,
            artist,
            inferred["language"], 0.6,
            inferred["era"], 0.6,
            inferred["genre"], 0.6,
            inferred["mood"], 0.6,
            inferred["tempo"], 0.6,
            inferred["vocal_type"], 0.6,
            inferred["artist_type"], 0.6,
            inferred["popularity"], 0.6
        ])

    # 🔥 reset only THIS session
    games[session_id] = Game()

    return jsonify({
        "status": "learned",
        "song_id": new_id,
        "title": title,
        "artist": artist
    })

from flask import send_from_directory

@app.route("/")
def index():
    return send_from_directory("../frontend", "index.html")


if __name__ == "__main__":
    app.run(debug=True)
