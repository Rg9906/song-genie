from backend.logic.engine import Engine
from backend.logic.belief import update_beliefs
from backend.logic.questions import select_best_question
from backend.logic.config import CONFIDENCE_THRESHOLD, MAX_QUESTIONS


class Game:
    def __init__(self):
        # Initialize Engine (loads songs_kg.json)
        self.engine = Engine()

        self.entities = self.engine.get_entities()
        self.beliefs = self.engine.get_beliefs()
        self.questions = self.engine.get_questions()

        self.asked = set()
        self.current_question = None
        self.question_count = 0

        self.answer_history = {}

    # ---------------------------------------
    # Answer Tracking
    # ---------------------------------------

    def record_answer(self, feature, value, answer):
        if feature not in self.answer_history:
            self.answer_history[feature] = {}
        self.answer_history[feature][value] = answer

    # ---------------------------------------
    # Guessing Logic
    # ---------------------------------------

    def get_top_guess(self):
        best_song_id = None
        best_prob = -1.0

        for song_id, prob in self.beliefs.items():
            if prob > best_prob:
                best_prob = prob
                best_song_id = song_id

        return best_song_id, best_prob

    def should_guess(self):
        probs = sorted(self.beliefs.values(), reverse=True)

        if probs[0] >= CONFIDENCE_THRESHOLD:
            return True

        if len(probs) > 1 and (probs[0] - probs[1]) >= 0.2:
            return True

        return False

    def get_top_candidates(self, k=3):
        sorted_items = sorted(
            self.beliefs.items(),
            key=lambda item: item[1],
            reverse=True
        )

        return [
            {"song_id": song_id, "prob": round(prob, 3)}
            for song_id, prob in sorted_items[:k]
        ]

    # ---------------------------------------
    # Question Flow
    # ---------------------------------------

    def next_question(self):

        # 1️⃣ If confident → guess
        if self.should_guess():
            song_id, confidence = self.get_top_guess()

            return {
                "type": "guess",
                "song_id": song_id,
                "confidence": round(confidence, 3),
                "top_candidates": self.get_top_candidates()
            }

        # 2️⃣ If max questions reached → learning mode
        if self.question_count >= MAX_QUESTIONS:
            return {
                "type": "learn",
                "message": "I couldn't guess your song. What song were you thinking of?"
            }

        # 3️⃣ Ask best entropy question
        best = select_best_question(
            self.questions,
            self.entities,
            self.beliefs,
            self.asked
        )

        if best is None:
            song_id, confidence = self.get_top_guess()
            return {
                "type": "guess",
                "song_id": song_id,
                "confidence": round(confidence, 3),
                "top_candidates": self.get_top_candidates()
            }

        key = (best["feature"], best["value"])
        self.asked.add(key)
        self.current_question = best
        self.question_count += 1

        return {
            "type": "question",
            "question": best
        }

    # ---------------------------------------
    # Answer Handling
    # ---------------------------------------

    def answer(self, user_answer):

        if self.current_question is None:
            return None

        feature = self.current_question["feature"]
        value = self.current_question["value"]

        self.record_answer(feature, value, user_answer)

        self.beliefs = update_beliefs(
            self.beliefs,
            self.entities,
            feature,
            value,
            user_answer
        )

        return self.next_question()

    # ---------------------------------------
    # Reset Game
    # ---------------------------------------

    def reset(self):
        self.engine.reload()

        self.entities = self.engine.get_entities()
        self.beliefs = self.engine.get_beliefs()
        self.questions = self.engine.get_questions()

        self.asked = set()
        self.current_question = None
        self.question_count = 0
        self.answer_history = {}
