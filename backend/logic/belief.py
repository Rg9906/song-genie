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
    conf_key = feature + "_conf"

    for song in songs:
        song_id = song["id"]
        matches = (song[feature] == value)
        confidence = song.get(conf_key, 1.0)

        base = 1.0
        if answer == "yes":
            base = 1.2 if matches else 0.8
        elif answer == "no":
            base = 0.8 if matches else 1.2

        # 🔥 KEY LINE: confidence-weighted update
        multiplier = 1 + (base - 1) * confidence

        beliefs[song_id] *= multiplier

    return normalize(beliefs)
