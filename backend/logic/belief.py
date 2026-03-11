import json
import os


ALPHA = 0.9  # default P(answer = yes | attribute is true)
BETA = 0.1   # default P(answer = yes | attribute is false)

# Feature-specific noise model.
# Each tuple is (alpha, beta) where:
# - alpha = P(answer=yes | fact is true)
# - beta  = P(answer=yes | fact is false)
#
# Higher alpha & lower beta = more reliable user responses for that feature.
FEATURE_NOISE = {
    "artists": (0.95, 0.05),
    "genres": (0.9, 0.1),
    "language": (0.95, 0.05),
    "country": (0.85, 0.15),
    "era": (0.8, 0.2),
    "decade": (0.8, 0.2),
    "awards": (0.85, 0.15),
    "labels": (0.8, 0.2),
    "producers": (0.8, 0.2),
    "composers": (0.8, 0.2),
    "part_of": (0.75, 0.25),
}


# Memory functions removed to prevent bias loops
# The system should rely purely on Bayesian inference


def initialize_beliefs(songs):
    """
    Initializes belief distribution.
    For now we use a uniform prior so that no single song
    (e.g. one that happened to be guessed often in the past)
    dominates from the start.
    """

    beliefs = {}

    if not songs:
        return beliefs

    n = float(len(songs))
    uniform_p = 1.0 / n

    for song in songs:
        beliefs[song["id"]] = uniform_p

    return beliefs


def normalize(beliefs):
    """
    Normalizes belief distribution so sum = 1.
    """

    total = sum(beliefs.values())

    if total == 0:
        return beliefs

    for k in beliefs:
        beliefs[k] /= total

    return beliefs


def compute_likelihood(matches, answer, feature=None):
    """
    Returns P(answer | song) using noise model.
    """

    alpha, beta = FEATURE_NOISE.get(feature, (ALPHA, BETA))

    if answer == "yes":

        if matches:
            return alpha
        else:
            return beta

    elif answer == "no":

        if matches:
            return 1.0 - alpha
        else:
            return 1.0 - beta

    else:  # unsure

        return 1.0


def update_beliefs(beliefs, songs, feature, value, answer):
    """
    Bayesian update:
    P(s | answer) ∝ P(answer | s) * P(s)
    """

    for song in songs:

        song_id = song["id"]

        # Prefer graph-like sparse facts if present; otherwise fall back
        # to fixed-attribute matching for older in-memory/test objects.
        facts = song.get("facts")
        if facts is not None:
            matches = (feature, value) in facts
        else:
            song_value = song.get(feature)

            # handle multi-valued attributes
            if isinstance(song_value, list):

                matches = value in song_value

            else:

                matches = song_value == value

        likelihood = compute_likelihood(matches, answer, feature=feature)

        beliefs[song_id] *= likelihood

    return normalize(beliefs)
