def initialize_beliefs(songs):
    beliefs = {}
    n = len(songs)
    for song in songs:
        beliefs[song["id"]] = 1.0 / n
    return beliefs


def normalize(beliefs):
    total = sum(beliefs.values())
    if total == 0:
        return beliefs
    for k in beliefs:
        beliefs[k] /= total
    return beliefs


def update_beliefs(beliefs, songs, feature, value, answer):
    for song in songs:
        song_id = song["id"]
        matches = (song[feature] == value)

        if answer == "yes":
            multiplier = 1.2 if matches else 0.8
        elif answer == "no":
            multiplier = 0.8 if matches else 1.2
        else:  # unsure
            multiplier = 1.0

        beliefs[song_id] *= multiplier

    return normalize(beliefs)
