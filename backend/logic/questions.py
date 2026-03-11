import math
import random

from backend.logic.belief import compute_likelihood, normalize
from backend.logic.analytics import compute_question_stats


# Heuristic feature-level weights so we don't over-focus
# on low-level identifiers like specific artists/countries.
# Higher weight → relatively more preferred questions.
FEATURE_WEIGHTS = {
    # High-value distinguishing features
    "artist_genders": 1.2,  # male/female splits many songs
    "artist_types": 1.1,   # solo/duo/group very powerful
    "song_types": 1.0,     # single/album track
    "films": 0.95,         # movie soundtrack
    "tv_series": 0.95,     # TV show
    "video_games": 0.9,    # video game
    "billion_views": 0.9,  # viral hits
    
    # Traditional good features
    "genres": 1.0,
    "language": 0.9,
    "era": 0.8,
    "decade": 0.8,
    "awards": 0.85,
    
    # Musical characteristics
    "instruments": 0.8,
    "bpm_category": 0.75,
    "duration_category": 0.7,
    "themes": 0.75,
    
    # Medium value
    "labels": 0.75,
    "producers": 0.7,
    "composers": 0.7,
    "chart_positions": 0.8,
    
    # Lower value (more specific)
    "artists": 0.5,
    "country": 0.6,
    "locations": 0.6,
    "performers": 0.6,
    "vocalists": 0.6,
}


def make_question_text(feature, value):
    """
    Generate slightly varied, more human-sounding question text
    based on the feature type.
    """
    if feature == "artists":
        templates = [
            f"Is the artist {value}?",
            f"Does it feature {value}?",
            f"Is {value} involved in this track?",
        ]
    elif feature == "artist_genders":
        templates = [
            f"Is the artist {value}?",
            f"Is it performed by a {value} artist?",
            f"Is the main vocalist {value}?",
        ]
    elif feature == "artist_types":
        templates = [
            f"Is it by a {value}?",
            f"Is the artist a {value}?",
            f"Is it performed by a {value}?",
        ]
    elif feature == "song_types":
        templates = [
            f"Is it a {value}?",
            f"Was it released as a {value}?",
        ]
    elif feature == "films":
        templates = [
            f"Is it from the movie {value}?",
            f"Was it featured in {value}?",
            f"Is it on the {value} soundtrack?",
        ]
    elif feature == "tv_series":
        templates = [
            f"Is it from the TV show {value}?",
            f"Was it featured in {value}?",
            f"Is it the theme for {value}?",
        ]
    elif feature == "video_games":
        templates = [
            f"Is it from the video game {value}?",
            f"Was it featured in {value}?",
            f"Is it part of the {value} soundtrack?",
        ]
    elif feature == "billion_views":
        templates = [
            f"Does it have over a billion views?",
            f"Is it a billion-view hit?",
        ]
    elif feature == "instruments":
        templates = [
            f"Does it feature {value}?",
            f"Is {value} played in this song?",
            f"Can you hear {value} in this track?",
        ]
    elif feature == "bpm_category":
        templates = [
            f"Is it a {value} tempo song?",
            f"Would you describe the tempo as {value}?",
        ]
    elif feature == "duration_category":
        templates = [
            f"Is it a {value} song?",
            f"Would you say it's {value} in length?",
        ]
    elif feature == "themes":
        templates = [
            f"Is it about {value}?",
            f"Does it have a {value} theme?",
        ]
    elif feature == "chart_positions":
        templates = [
            f"Did it reach #{value} on the charts?",
            f"Was it a chart hit at position {value}?",
        ]
    elif feature == "genres":
        templates = [
            f"Is it a {value} song?",
            f"Would you call it {value}?",
            f"Is the overall vibe {value}?",
        ]
    elif feature == "language":
        templates = [
            f"Is the song mainly in {value}?",
            f"Is {value} the primary language?",
            f"Would you say it's sung in {value}?",
        ]
    elif feature == "country":
        templates = [
            f"Is it strongly associated with {value}?",
            f"Is the artist from {value}?",
            f"Does it originate from {value}?",
        ]
    elif feature == "era":
        templates = [
            f"Is it from the {value.replace('_', ' ')} era?",
            f"Was it released around the {value.replace('_', ' ')} period?",
        ]
    elif feature == "decade":
        templates = [
            f"Was it released in the {value}?",
            f"Does it feel like a {value} song?",
        ]
    elif feature == "awards":
        templates = [
            f"Has this song won {value}?",
            f"Did it receive the {value} award?",
        ]
    elif feature == "labels":
        templates = [
            f"Was it released under {value}?",
            f"Is it on the {value} label?",
        ]
    else:
        templates = [
            f"Is it connected with {value}?",
            f"Would you associate it with {value}?",
        ]

    return random.choice(templates)


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


def extract_value_counts(entities, attribute):
    """
    Count how many entities contain each value for an attribute.
    Supports list-valued attributes.
    """
    counts = {}

    for entity in entities:

        value = entity.get(attribute)
        if value is None:
            continue

        if isinstance(value, list):

            for v in value:
                if v is None:
                    continue
                counts[v] = counts.get(v, 0) + 1

        else:

            counts[value] = counts.get(value, 0) + 1

    return counts


def generate_all_questions(entities):
    """
    Dynamically generate all questions from KG attributes.
    Enhanced with diverse attributes for better questioning.
    """

    # Prioritized attributes for optimal question selection
    attributes = [
        # High-value distinguishing features (ask early)
        "artist_genders",
        "artist_types", 
        "song_types",
        "billion_views",
        
        # Media connections (very distinguishing)
        "films",
        "tv_series", 
        "video_games",
        
        # Traditional good features
        "genres",
        "language",
        "era",
        "decade",
        "awards",
        
        # Musical characteristics
        "instruments",
        "bpm_category",
        "duration_category",
        "themes",
        "chart_positions",
        
        # Production details
        "labels",
        "producers",
        "composers",
        
        # Location and performance
        "locations",
        "performers",
        "vocalists",
        
        # Lower priority (more specific)
        "part_of",
        "country", 
        "artists",
    ]

    questions = []

    # Per-feature minimum support to avoid ultra-rare questions.
    min_support = {
        "artists": 2,
        "genres": 2,
        "country": 2,
        "awards": 2,
        "labels": 2,
        "producers": 2,
        "composers": 2,
        "part_of": 2,
        "performers": 2,
        "vocalists": 2,
        "locations": 2,
        "themes": 2,
        "instruments": 2,
        # Enhanced attributes with lower thresholds
        "artist_genders": 1,  # Even 1 is valuable
        "artist_types": 1,
        "song_types": 1,
        "films": 1,
        "tv_series": 1,
        "video_games": 1,
        "chart_positions": 2,
    }

    for attribute in attributes:

        counts = extract_value_counts(entities, attribute)
        values = list(counts.keys())

        for value in values:
            if value is None:
                continue
            if attribute not in {"era", "decade", "language"}:
                if counts.get(value, 0) < min_support.get(attribute, 2):
                    continue

            questions.append(
                {
                    "feature": attribute,
                    "value": value,
                    "text": make_question_text(attribute, value),
                }
            )

    return questions


def simulate_bayesian_update(songs, beliefs, feature, value, answer):
    """
    Simulates posterior belief after hypothetical answer.
    """

    new_beliefs = {}

    for song in songs:

        song_id = song["id"]

        prior = beliefs[song_id]

        facts = song.get("facts")
        if facts is not None:
            matches = (feature, value) in facts
        else:
            song_value = song.get(feature)

            if isinstance(song_value, list):
                matches = value in song_value
            else:
                matches = song_value == value

        likelihood = compute_likelihood(matches, answer, feature=feature)

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

        facts = song.get("facts")
        if facts is not None:
            matches = (feature, value) in facts
        else:
            song_value = song.get(feature)

            if isinstance(song_value, list):
                matches = value in song_value
            else:
                matches = song_value == value

        likelihood = compute_likelihood(matches, answer, feature=feature)

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
    Pure information gain selection - no bandit to prevent bias
    With logical filtering to prevent redundant questions
    """
    best_question = None
    best_score = -1.0

    # Extract answered features for logical filtering
    answered_features = {}
    for (feature, value) in asked:
        if feature not in answered_features:
            answered_features[feature] = []
        answered_features[feature].append(value)

    for q in questions:
        key = (q["feature"], q["value"])
        if key in asked:
            continue

        # Skip redundant questions based on logical filtering
        feature = q["feature"]
        value = q["value"]
        
        # Time period filtering
        if feature in ["era", "decade"] and "era" in answered_features:
            # If we already got an answer about era, don't ask other eras
            continue
        if feature == "year" and ("era" in answered_features or "decade" in answered_features):
            # If we know era/decade, don't ask specific year
            continue
            
        # Language filtering - if we know the language, don't ask other languages
        if feature == "language" and "language" in answered_features:
            continue
            
        # Country filtering - if we know the country, don't ask other countries  
        if feature == "country" and "country" in answered_features:
            continue

        base_score = score_question(q, songs, beliefs)

        # Apply heuristic feature preferences and diversity penalty so we
        # don't spam the same kind of question (e.g. artist, country).
        feature_weight = FEATURE_WEIGHTS.get(feature, 1.0)
        asked_feature_count = sum(1 for (f, _) in asked if f == feature)
        diversity_factor = 1.0 / (1.0 + asked_feature_count)
        adjusted_score = base_score * feature_weight * diversity_factor

        if adjusted_score > best_score:
            best_score = adjusted_score
            best_question = q

    return best_question
