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

        # MUCH stronger evidence handling
        if answer == "yes":
            if matches:
                multiplier = 1.8 * confidence
            else:
                multiplier = 0.3
        elif answer == "no":
            if matches:
                multiplier = 0.25
            else:
                multiplier = 1.1
        else:  # unsure
            multiplier = 1.0

        beliefs[song_id] *= multiplier

    # normalize
    total = sum(beliefs.values())
    if total > 0:
        for k in beliefs:
            beliefs[k] /= total

    return beliefs
