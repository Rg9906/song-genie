from logic.engine import load_songs
from logic.belief import initialize_beliefs, update_beliefs
from logic.features import FEATURE_VALUES
from logic.questions import generate_questions, select_best_question


CONFIDENCE_THRESHOLD = 0.7
MAX_QUESTIONS = 20


class Game:
    def __init__(self):
        self.songs = load_songs("backend/data/songs.csv")
        self.beliefs = initialize_beliefs(self.songs)
        self.questions = generate_questions(FEATURE_VALUES)
        self.asked = set()
        self.current_question = None
        self.question_count = 0

    def get_top_guess(self):
        best_song_id = None
        best_prob = -1.0

        for song_id, prob in self.beliefs.items():
            if prob > best_prob:
                best_prob = prob
                best_song_id = song_id

        return best_song_id, best_prob

    def should_guess(self):
        _, best_prob = self.get_top_guess()
        return best_prob >= CONFIDENCE_THRESHOLD

    def get_top_candidates(self, k=3):
        sorted_items = sorted(
            self.beliefs.items(),
            key=lambda item: item[1],
            reverse=True
        )

        top = []
        count = 0

        for song_id, prob in sorted_items:
            if count >= k:
                break
            top.append({
                "song_id": song_id,
                "prob": prob
            })
            count += 1

        return top

    def next_question(self):
        # If we've asked too many questions and still aren't confident, trigger learning
        if self.question_count >= MAX_QUESTIONS:
            return {
                "type": "learn",
                "message": "I couldn't identify the song confidently. Please help me learn it."
            }

        # Check if we should guess instead of asking
        if self.should_guess():
            song_id, confidence = self.get_top_guess()

            return {
                "type": "guess",
                "song_id": song_id,
                "confidence": confidence,
                "top_candidates": self.get_top_candidates()
            }

        best = select_best_question(
            self.questions,
            self.songs,
            self.beliefs,
            self.asked
        )

        if best is None:
            return None

        key = (best["feature"], best["value"])
        self.asked.add(key)
        self.current_question = best
        self.question_count += 1

        return {
            "type": "question",
            "question": best
        }

    def answer(self, user_answer):
        if self.current_question is None:
            return None

        feature = self.current_question["feature"]
        value = self.current_question["value"]

        self.beliefs = update_beliefs(
            self.beliefs,
            self.songs,
            feature,
            value,
            user_answer
        )

        # After updating beliefs, decide again
        return self.next_question()
