from flask import Flask, jsonify, request
from logic.game import Game

app = Flask(__name__)
game = Game()

@app.route("/start")
def start():
    return jsonify(game.next_question())

@app.route("/answer", methods=["POST"])
def answer():
    data = request.json
    user_answer = data.get("answer")  # "yes", "no", or "unsure"
    next_q = game.answer(user_answer)
    return jsonify(next_q)

if __name__ == "__main__":
    app.run(debug=True)
