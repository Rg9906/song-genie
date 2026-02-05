import math

def entropy(probabilities):
    e = 0.0
    for p in probabilities:
        if p > 0:
            e -= p * math.log2(p)
    return e


def generate_questions(feature_values):
    questions = []

    for feature, values in feature_values.items():
        for value in values:
            questions.append({
                "feature": feature,
                "value": value,
                "text": f"Is the {feature.replace('_', ' ')} {value.replace('_', ' ')}?"
            })

    return questions


def simulate_update(songs, beliefs, feature, value, answer):
    new_beliefs = {}

    for song in songs:
        song_id = song["id"]
        p = beliefs[song_id]
        matches = (song[feature] == value)

        if answer == "yes":
            new_beliefs[song_id] = p if matches else 0.0
        elif answer == "no":
            new_beliefs[song_id] = p if not matches else 0.0

    total = sum(new_beliefs.values())
    if total == 0:
        return beliefs

    for k in new_beliefs:
        new_beliefs[k] /= total

    return new_beliefs


def score_question(question, songs, beliefs):
    feature = question["feature"]
    value = question["value"]

    current_entropy = entropy(beliefs.values())

    p_yes = 0.0
    p_no = 0.0

    for song in songs:
        song_id = song["id"]
        if song[feature] == value:
            p_yes += beliefs[song_id]
        else:
            p_no += beliefs[song_id]

    expected_entropy = 0.0

    if p_yes > 0:
        yes_beliefs = simulate_update(songs, beliefs, feature, value, "yes")
        expected_entropy += p_yes * entropy(yes_beliefs.values())

    if p_no > 0:
        no_beliefs = simulate_update(songs, beliefs, feature, value, "no")
        expected_entropy += p_no * entropy(no_beliefs.values())

    return current_entropy - expected_entropy


def select_best_question(questions, songs, beliefs, asked):
    best_question = None
    best_score = -1

    for q in questions:
        key = (q["feature"], q["value"])
        if key in asked:
            continue

        score = score_question(q, songs, beliefs)

        if score > best_score:
            best_score = score
            best_question = q

    return best_question
