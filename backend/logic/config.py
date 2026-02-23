import os


def _get_bool(name: str, default: str = "false") -> bool:
    """
    Parse a boolean environment variable in a tolerant way.
    """
    value = os.getenv(name, default).strip().lower()
    return value in {"1", "true", "yes", "on"}


# Core inference / game configuration
CONFIDENCE_THRESHOLD: float = float(
    os.getenv("SONG_GENIE_CONFIDENCE_THRESHOLD", "0.85")
)
DOMINANCE_RATIO: float = float(
    os.getenv("SONG_GENIE_DOMINANCE_RATIO", "3.0")
)
MAX_QUESTIONS: int = int(
    os.getenv("SONG_GENIE_MAX_QUESTIONS", "20")
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


# Bandit / learning configuration
# Controls how much historical "question success" influences the question pick.
BANDIT_LAMBDA: float = float(os.getenv("SONG_GENIE_BANDIT_LAMBDA", "0.3"))
# Cache analytics (disk) reads for this many seconds.
ANALYTICS_CACHE_SECONDS: int = int(os.getenv("SONG_GENIE_ANALYTICS_CACHE_SECONDS", "5"))

