from flask import Flask, jsonify, request
from logic.game import Game
import csv

app = Flask(__name__)
game = Game()

SONGS_PATH = "backend/data/songs.csv"


@app.route("/start")
def start():
    return jsonify(game.next_question())


@app.route("/answer", methods=["POST"])
def answer():
    data = request.json
    user_answer = data.get("answer")
    return jsonify(game.answer(user_answer))


@app.route("/learn", methods=["POST"])
def learn():
    global game

    data = request.json
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

    # reset game so new song is used
    game = Game()

    return jsonify({
        "status": "learned",
        "song_id": new_id,
        "title": title,
        "artist": artist
    })


if __name__ == "__main__":
    app.run(debug=True)
