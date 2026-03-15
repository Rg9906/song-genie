import os


def _get_bool(name: str, default: str = "false") -> bool:
    """
    Parse a boolean environment variable in a tolerant way.
    """
    value = os.getenv(name, default).strip().lower()
    return value in {"1", "true", "yes", "on"}


# Core inference / game configuration
# Made more aggressive to guess earlier
CONFIDENCE_THRESHOLD: float = float(
    os.getenv("SONG_GENIE_CONFIDENCE_THRESHOLD", "0.65")  # Reduced from 0.80
)
DOMINANCE_RATIO: float = float(
    os.getenv("SONG_GENIE_DOMINANCE_RATIO", "2.0")  # Reduced from 3.0
)
MAX_QUESTIONS: int = int(
    os.getenv("SONG_GENIE_MAX_QUESTIONS", "20")
)

# Minimum number of questions before the engine
# is allowed to make a guess.
MIN_QUESTIONS_BEFORE_GUESS: int = int(
    os.getenv("SONG_GENIE_MIN_QUESTIONS_BEFORE_GUESS", "6")  # Reduced from 10
)

# Additional safety margin: how much more probable the top
# candidate must be in absolute terms compared to runner up.
MIN_CONFIDENCE_MARGIN: float = float(
    os.getenv("SONG_GENIE_MIN_CONFIDENCE_MARGIN", "0.10")  # Reduced from 0.15
)


# Session configuration
SESSION_TTL_SECONDS: int = int(
    os.getenv("SONG_GENIE_SESSION_TTL_SECONDS", "1800")  # 30 minutes
)


# Flask server configuration
FLASK_HOST: str = os.getenv("SONG_GENIE_FLASK_HOST", "127.0.0.1")
FLASK_PORT: int = int(os.getenv("SONG_GENIE_FLASK_PORT", "5000"))
FLASK_DEBUG: bool = _get_bool("SONG_GENIE_FLASK_DEBUG", "true")


# External request configuration (e.g. Wikidata)
REQUEST_TIMEOUT_SECONDS: float = float(
    os.getenv("SONG_GENIE_REQUEST_TIMEOUT_SECONDS", "5.0")
)

# Wikidata configuration
WIKIDATA_SPARQL_URL: str = "https://query.wikidata.org/sparql"


# Bandit / learning configuration
# Controls how much historical "question success" influences the question pick.
# Set to 0 to prevent bias from historical data
BANDIT_LAMBDA: float = float(os.getenv("SONG_GENIE_BANDIT_LAMBDA", "0.0"))
# Cache analytics (disk) reads for this many seconds.
ANALYTICS_CACHE_SECONDS: int = int(os.getenv("SONG_GENIE_ANALYTICS_CACHE_SECONDS", "5"))