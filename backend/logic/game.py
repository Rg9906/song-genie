from logic.engine import load_songs
from logic.belief import initialize_beliefs, update_beliefs
from logic.features import FEATURE_VALUES
from logic.questions import generate_questions, select_best_question


class Game:
    def __init__(self):
        self.songs = load_songs("backend/data/songs.csv")
        self.beliefs = initialize_beliefs(self.songs)
        self.questions = generate_questions(FEATURE_VALUES)
        self.asked = set()
        self.current_question = None

    def next_question(self):
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
        return best

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

        return self.next_question()
