import math
from typing import Dict, List, Tuple

from backend.logic.engine import Engine
from backend.logic.belief import update_beliefs, normalize
from backend.logic.analytics import _load_all_sessions


def entropy(dist: Dict[int, float]) -> float:
    e = 0.0
    for p in dist.values():
        if p > 0:
            e -= p * math.log2(p)
    return e


def get_top_k(beliefs: Dict[int, float], k: int = 3) -> List[Tuple[int, float]]:
    return sorted(beliefs.items(), key=lambda x: x[1], reverse=True)[:k]


def replay_sessions() -> None:
    """
    Offline evaluation: replay all logged sessions using the *current*
    inference engine and report calibration / efficiency style stats.
    """
    engine = Engine()
    songs = engine.get_entities()

    sessions = _load_all_sessions()
    if not sessions:
        print("No sessions to replay.")
        return

    total_sessions = 0
    total_questions = 0
    entropy_before_sum = 0.0
    entropy_after_sum = 0.0

    for entry in sessions:
        questions = entry.get("questions", [])
        if not questions:
            continue

        beliefs = normalize(engine.get_beliefs().copy())
        h0 = entropy(beliefs)

        for q in questions:
            feature = q.get("feature")
            value = q.get("value")
            answer = q.get("answer")
            beliefs = update_beliefs(beliefs, songs, feature, value, answer)

        hT = entropy(beliefs)

        total_sessions += 1
        total_questions += len(questions)
        entropy_before_sum += h0
        entropy_after_sum += hT

        top = get_top_k(beliefs, k=3)
        print(
            f"Session {entry.get('session_id')}: "
            f"{len(questions)} questions, "
            f"H0={h0:.3f} -> HT={hT:.3f}, "
            f"top-3={top}"
        )

    if total_sessions > 0:
        print("\n=== Aggregate stats ===")
        print(f"Sessions replayed: {total_sessions}")
        print(f"Avg questions per session: {total_questions / total_sessions:.2f}")
        print(f"Avg entropy before: {entropy_before_sum / total_sessions:.3f}")
        print(f"Avg entropy after:  {entropy_after_sum / total_sessions:.3f}")


if __name__ == "__main__":
    replay_sessions()

