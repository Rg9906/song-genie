import math
import random

from backend.logic.belief import compute_likelihood, normalize
from backend.logic.analytics import compute_question_stats


def entropy(probabilities):
    """
    Shannon entropy.
    """

    e = 0.0

    for p in probabilities:

        if p > 0:
            e -= p * math.log2(p)

    return e


def extract_values(entities, attribute):
    """
    Extract unique values from KG entities.
    Supports list-valued attributes.
    """

    values = set()

    for entity in entities:

        value = entity.get(attribute)

        if isinstance(value, list):

            for v in value:
                values.add(v)

        else:

            values.add(value)

    return list(values)


def generate_all_questions(entities):
    """
    Dynamically generate all questions from KG attributes.
    """

    attributes = ["artists", "genres", "language", "country"]

    questions = []

    for attribute in attributes:

        values = extract_values(entities, attribute)

        for value in values:

            questions.append({

                "feature": attribute,

                "value": value,

                "text": f"Is it associated with {value} ({attribute})?"

            })

    return questions


def simulate_bayesian_update(songs, beliefs, feature, value, answer):
    """
    Simulates posterior belief after hypothetical answer.
    """

    new_beliefs = {}

    for song in songs:

        song_id = song["id"]

        prior = beliefs[song_id]

        song_value = song.get(feature)

        if isinstance(song_value, list):
            matches = value in song_value
        else:
            matches = song_value == value

        likelihood = compute_likelihood(matches, answer)

        new_beliefs[song_id] = prior * likelihood

    return normalize(new_beliefs)


def compute_answer_probability(songs, beliefs, feature, value, answer):
    """
    Computes marginal probability of answer.
    """

    prob = 0.0

    for song in songs:

        song_id = song["id"]

        prior = beliefs[song_id]

        song_value = song.get(feature)

        if isinstance(song_value, list):
            matches = value in song_value
        else:
            matches = song_value == value

        likelihood = compute_likelihood(matches, answer)

        prob += prior * likelihood

    return prob


def score_question(question, songs, beliefs):
    """
    Information gain score.
    """

    feature = question["feature"]

    value = question["value"]

    current_entropy = entropy(beliefs.values())

    p_yes = compute_answer_probability(
        songs,
        beliefs,
        feature,
        value,
        "yes"
    )

    p_no = compute_answer_probability(
        songs,
        beliefs,
        feature,
        value,
        "no"
    )

    expected_entropy = 0.0

    if p_yes > 0:

        yes_beliefs = simulate_bayesian_update(
            songs,
            beliefs,
            feature,
            value,
            "yes"
        )

        expected_entropy += p_yes * entropy(yes_beliefs.values())

    if p_no > 0:

        no_beliefs = simulate_bayesian_update(
            songs,
            beliefs,
            feature,
            value,
            "no"
        )

        expected_entropy += p_no * entropy(no_beliefs.values())

    return current_entropy - expected_entropy


def select_best_question(questions, songs, beliefs, asked):
    """
    Selects highest information gain question.
    """

    best_question = None

    best_score = -1.0

    for q in questions:

        key = (q["feature"], q["value"])

        if key in asked:
            continue

        score = score_question(q, songs, beliefs)

        if score > best_score:

            best_score = score

            best_question = q

    return best_question


# Override with a sturdier Thompson Sampling policy (kept here so we don't have
# to rewrite the file above; Python uses the last definition).
from backend.logic.analytics import compute_question_stats  # noqa: E402
from backend.logic.config import BANDIT_LAMBDA  # noqa: E402


def select_best_question(questions, songs, beliefs, asked):
    """
    Thompson-sampling style selection:
    - Base score = information gain (entropy drop)
    - Bandit term = sampled from Beta(successes+1, failures+1) per question
    - Final score = base_score + BANDIT_LAMBDA * bandit_sample
    """
    stats = compute_question_stats()

    best_question = None
    best_score = -1.0

    for q in questions:
        key = (q["feature"], q["value"])
        if key in asked:
            continue

        base_score = score_question(q, songs, beliefs)

        q_stats = stats.get(key, {})
        count = float(q_stats.get("count", 0.0))
        success_count = float(q_stats.get("success_count", 0.0))
        failures = max(count - success_count, 0.0)

        alpha = success_count + 1.0
        beta_param = failures + 1.0
        bandit_sample = random.betavariate(alpha, beta_param)

        score = base_score + (BANDIT_LAMBDA * bandit_sample)

        if score > best_score:
            best_score = score
            best_question = q

    return best_question
