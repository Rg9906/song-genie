from logic.engine import load_songs
from logic.belief import initialize_beliefs, update_beliefs
from logic.features import FEATURE_VALUES
from logic.questions import generate_questions, select_best_question


CONFIDENCE_THRESHOLD = 0.55
MAX_QUESTIONS = 20


class Game:
    def __init__(self):
        self.songs = load_songs("data/songs.csv")
        self.beliefs = initialize_beliefs(self.songs)
        self.questions = generate_questions(FEATURE_VALUES)

        self.asked = set()
        self.current_question = None
        self.question_count = 0

        self.answer_history = {}

    def record_answer(self, feature, value, answer):
        if feature not in self.answer_history:
            self.answer_history[feature] = {}
        self.answer_history[feature][value] = answer

    def infer_features(self):
        inferred = {}
        for feature, values in FEATURE_VALUES.items():
            answers = self.answer_history.get(feature, {})
            yes_values = [v for v, a in answers.items() if a == "yes"]

            if len(yes_values) == 1:
                inferred[feature] = yes_values[0]
            else:
                inferred[feature] = "Other"

        return inferred

    # 🔥 SYMBOLIC CERTAINTY
    def get_logical_match(self):
        inferred = self.infer_features()
        candidates = []

        for song in self.songs:
            ok = True
            for feature, value in inferred.items():
                if value == "Other":
                    continue
                if song[feature] != value:
                    ok = False
                    break
            if ok:
                candidates.append(song)

        if len(candidates) == 1:
            return candidates[0]["id"]

        return None

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
            {"song_id": song_id, "prob": prob}
            for song_id, prob in sorted_items[:k]
        ]

    def next_question(self):
        # 🔥 1. HARD LOGICAL GUESS (HIGHEST PRIORITY)
        logical_id = self.get_logical_match()
        if logical_id is not None:
            return {
                "type": "guess",
                "song_id": logical_id,
                "confidence": 0.99,
                "top_candidates": self.get_top_candidates()
            }

        # 🔥 2. PROBABILISTIC GUESS
        if self.should_guess():
            song_id, confidence = self.get_top_guess()
            top_candidates = self.get_top_candidates()

            total = sum(c["prob"] for c in top_candidates)
            relative_confidence = confidence / total if total > 0 else confidence

            return {
                "type": "guess",
                "song_id": song_id,
                "confidence": round(relative_confidence, 2),
                "top_candidates": top_candidates
            }

        # 🔥 3. LEARNING MODE
        if self.question_count >= MAX_QUESTIONS:
            return {
                "type": "learn",
                "message": "I couldn't guess your song. What song were you thinking of?",
                "ask": {
                    "title": True,
                    "artist": True
                },
                "inferred_features": self.infer_features()
            }

        # 🔥 4. ASK NEXT QUESTION
        best = select_best_question(
            self.questions,
            self.songs,
            self.beliefs,
            self.asked
        )

        if best is None:
            song_id, confidence = self.get_top_guess()
            return {
                "type": "guess",
                "song_id": song_id,
                "confidence": round(confidence, 2),
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

    def answer(self, user_answer):
        if self.current_question is None:
            return None

        feature = self.current_question["feature"]
        value = self.current_question["value"]

        self.record_answer(feature, value, user_answer)

        self.beliefs = update_beliefs(
            self.beliefs,
            self.songs,
            feature,
            value,
            user_answer
        )

        return self.next_question()
