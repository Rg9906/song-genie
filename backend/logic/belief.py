import json
import os


ALPHA = 0.9  # P(answer = yes | attribute is true)
BETA = 0.1   # P(answer = yes | attribute is false)


def get_memory_path():
    """
    Returns absolute path to memory.json
    """

    return os.path.join(
        os.path.dirname(__file__),
        "..",
        "data",
        "memory.json"
    )


def load_memory():
    """
    Loads memory file or creates empty memory.
    """

    path = get_memory_path()

    if os.path.exists(path):

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    else:

        return {}


def save_memory(memory):
    """
    Saves memory to disk.
    """

    path = get_memory_path()

    with open(path, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2)


def update_memory(song_id):
    """
    Increments experience count for a song.
    """

    memory = load_memory()

    key = str(song_id)

    memory[key] = memory.get(key, 0) + 1

    save_memory(memory)


def initialize_beliefs(songs):
    """
    Initializes belief distribution using past experience.
    Uses Laplace smoothing so new songs still get probability.
    """

    memory = load_memory()

    beliefs = {}

    total = 0.0

    for song in songs:

        song_id = str(song["id"])

        count = memory.get(song_id, 0)

        # Laplace smoothing
        prior = count + 1

        beliefs[song["id"]] = prior

        total += prior

    # normalize
    for song_id in beliefs:

        beliefs[song_id] /= total

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


def compute_likelihood(matches, answer):
    """
    Returns P(answer | song) using noise model.
    """

    if answer == "yes":

        if matches:
            return ALPHA
        else:
            return BETA

    elif answer == "no":

        if matches:
            return 1.0 - ALPHA
        else:
            return 1.0 - BETA

    else:  # unsure

        return 1.0


def update_beliefs(beliefs, songs, feature, value, answer):
    """
    Bayesian update:
    P(s | answer) ∝ P(answer | s) * P(s)
    """

    for song in songs:

        song_id = song["id"]

        song_value = song.get(feature)

        # handle multi-valued attributes
        if isinstance(song_value, list):

            matches = value in song_value

        else:

            matches = song_value == value

        likelihood = compute_likelihood(matches, answer)

        beliefs[song_id] *= likelihood

    return normalize(beliefs)
