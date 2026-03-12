import math
import random

from backend.logic.belief import compute_likelihood, normalize

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


def select_best_question(questions, songs, beliefs, asked, engine=None):
    """
    Select the best question using enhanced graph intelligence.
    Now integrates better with dynamic graph and provides debugging output.
    """
    if not songs:
        return None
    
    # Filter out already asked questions
    available_questions = [q for q in questions if (q["feature"], q["value"]) not in asked]
    
    if not available_questions:
        return None
    
    # Calculate scores for each question
    scored_questions = []
    for question in available_questions:
        score = calculate_question_score(question, songs, beliefs, engine)
        question["score"] = score
        question["debug_info"] = get_debug_info(question, songs, beliefs)
        scored_questions.append(question)
    
    # Sort by score (highest first)
    scored_questions.sort(key=lambda q: q["score"], reverse=True)
    
    # Get best question
    best_question = scored_questions[0]
    
    # Debug output
    print(f"🔍 Best Question Selected:")
    print(f"   Question: {best_question['text']}")
    print(f"   Feature: {best_question['feature']}")
    print(f"   Value: {best_question['value']}")
    print(f"   Score: {best_question['score']:.3f}")
    print(f"   Covers: {best_question['debug_info']['covers_songs']} songs")
    print(f"   Splits: {best_question['debug_info']['split_ratio']:.2f}")
    print(f"   Entropy: {best_question['debug_info']['entropy']:.3f}")
    
    return best_question

def calculate_question_score(question, songs, beliefs, engine=None):
    """
    Calculate question score combining multiple factors.
    Enhanced for better graph integration.
    """
    feature = question["feature"]
    value = question["value"]
    
    # 1. Information gain (how well it splits candidates)
    info_score = calculate_information_gain(feature, value, songs, beliefs)
    
    # 2. Feature weight (importance of this feature type)
    feature_weight = FEATURE_WEIGHTS.get(feature, 0.5)
    
    # 3. Candidate reduction (how many songs it eliminates)
    reduction_score = calculate_candidate_reduction(feature, value, songs, beliefs)
    
    # 4. Graph centrality (if graph is available)
    centrality_score = 0.0
    if engine and hasattr(engine, 'graph_system') and engine.graph_system:
        centrality_score = calculate_graph_centrality(feature, value, engine.graph_system)
    
    # 5. Diversity bonus (prefer different feature types)
    diversity_bonus = calculate_diversity_bonus(feature, beliefs)
    
    # Combine scores with weights
    total_score = (
        info_score * 0.3 +           # Information gain is most important
        reduction_score * 0.25 +       # How well it reduces candidates
        feature_weight * 0.2 +         # Feature importance
        centrality_score * 0.15 +       # Graph centrality
        diversity_bonus * 0.1            # Question diversity
    )
    
    return total_score

def calculate_information_gain(feature, value, songs, beliefs):
    """Calculate information gain (entropy reduction) for this question."""
    # Split songs by answer
    yes_songs = []
    no_songs = []
    
    for song in songs:
        if matches_feature(song, feature, value):
            yes_songs.append(song)
        else:
            no_songs.append(song)
    
    # Calculate entropy before and after
    total_songs = len(songs)
    entropy_before = calculate_entropy([total_songs])
    entropy_after = (
        (len(yes_songs) / total_songs) * calculate_entropy([len(yes_songs)]) +
        (len(no_songs) / total_songs) * calculate_entropy([len(no_songs)])
    )
    
    # Information gain = reduction in entropy
    return entropy_before - entropy_after

def calculate_candidate_reduction(feature, value, songs, beliefs):
    """Calculate how well this question reduces candidates."""
    matches = sum(1 for song in songs if matches_feature(song, feature, value))
    total = len(songs)
    
    # Ideal split is 50/50, so score based on how close to that
    split_ratio = matches / total
    if split_ratio > 0.5:
        split_ratio = 1 - split_ratio
    
    return split_ratio * 2  # Normalize to 0-1 range

def calculate_graph_centrality(feature, value, graph_system):
    """Calculate centrality score for graph attributes."""
    try:
        # Get centrality metrics for this attribute
        centrality = graph_system.get_attribute_centrality(feature, value)
        if centrality:
            # Higher centrality = more important attribute
            return min(centrality.get('betweenness', 0) / 10, 1.0)
    except:
        pass
    
    return 0.0

def calculate_diversity_bonus(feature, beliefs):
    """Give bonus to diverse feature types."""
    # Count how many times this feature has been asked
    feature_count = sum(1 for f, _ in beliefs.get('asked_questions', []) if f == feature)
    
    # Fewer questions of this type = higher diversity bonus
    if feature_count == 0:
        return 0.2
    elif feature_count == 1:
        return 0.1
    else:
        return 0.0
