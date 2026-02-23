import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from backend.logic.config import ANALYTICS_CACHE_SECONDS


_CACHE = {"loaded_at": None, "sessions": None}


def _get_analytics_path() -> str:
    base_dir = os.path.dirname(__file__)
    data_dir = os.path.join(base_dir, "..", "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "sessions_log.json")


def _load_all_sessions() -> List[Dict[str, Any]]:
    path = _get_analytics_path()
    if not os.path.exists(path):
        return []

    now = datetime.utcnow()
    loaded_at = _CACHE.get("loaded_at")
    cached = _CACHE.get("sessions")
    if loaded_at is not None and cached is not None:
        age = (now - loaded_at).total_seconds()
        if age <= ANALYTICS_CACHE_SECONDS:
            return cached

    with open(path, "r", encoding="utf-8") as f:
        try:
            sessions = json.load(f)
        except json.JSONDecodeError:
            sessions = []

    _CACHE["loaded_at"] = now
    _CACHE["sessions"] = sessions
    return sessions


def _save_all_sessions(sessions: List[Dict[str, Any]]) -> None:
    path = _get_analytics_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sessions, f, indent=2)
    _CACHE["loaded_at"] = datetime.utcnow()
    _CACHE["sessions"] = sessions


def log_session(
    session_id: str,
    questions: List[Dict[str, Any]],
    final_song_id: Optional[int],
    confidence: float,
) -> None:
    """
    Append a completed session to the analytics log.
    success is initially unknown; updated later via feedback.
    """
    sessions = _load_all_sessions()
    sessions.append(
        {
            "session_id": session_id,
            "questions": questions,
            "final_song_id": final_song_id,
            "confidence": confidence,
            "success": None,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
    )
    _save_all_sessions(sessions)


def log_feedback(
    session_id: str,
    success: bool,
    correct_song_title: Optional[str] = None,
) -> None:
    """
    Update a session with ground-truth feedback.
    """
    sessions = _load_all_sessions()
    updated = False
    for entry in sessions:
        if entry.get("session_id") == session_id:
            entry["success"] = bool(success)
            if correct_song_title:
                entry["correct_song_title"] = correct_song_title
            updated = True
            break
    if updated:
        _save_all_sessions(sessions)


def compute_question_stats() -> Dict[Tuple[str, Any], Dict[str, float]]:
    """
    Compute simple stats per (feature, value) from logged sessions.
    """
    sessions = _load_all_sessions()
    stats: Dict[Tuple[str, Any], Dict[str, float]] = {}

    for entry in sessions:
        questions = entry.get("questions", [])
        success = entry.get("success")
        for idx, q in enumerate(questions):
            key = (q.get("feature"), q.get("value"))
            if key not in stats:
                stats[key] = {
                    "count": 0.0,
                    "success_count": 0.0,
                    "avg_position_sum": 0.0,
                }
            s = stats[key]
            s["count"] += 1.0
            s["avg_position_sum"] += float(idx + 1)
            if success is True:
                s["success_count"] += 1.0

    # Finalize averages
    for key, s in stats.items():
        count = s["count"]
        if count > 0:
            s["success_rate"] = s["success_count"] / count
            s["avg_position"] = s["avg_position_sum"] / count
        else:
            s["success_rate"] = 0.0
            s["avg_position"] = 0.0

    return stats


def get_question_boosts() -> Dict[Tuple[str, Any], float]:
    """
    Derive a small score boost per question based on historical stats.
    Questions that occur in successful games more often (especially early)
    get a positive boost.
    """
    stats = compute_question_stats()
    boosts: Dict[Tuple[str, Any], float] = {}

    if not stats:
        return boosts

    # Compute global baseline success rate
    total_success = sum(s.get("success_count", 0.0) for s in stats.values())
    total_count = sum(s.get("count", 0.0) for s in stats.values())
    baseline = (total_success / total_count) if total_count > 0 else 0.0

    for key, s in stats.items():
        count = s.get("count", 0.0)
        if count < 3:
            # Ignore very low-sample questions for stability
            continue
        success_rate = s.get("success_rate", 0.0)
        avg_position = s.get("avg_position", 0.0) or 1.0

        # Center success rate around baseline and scale gently
        delta = success_rate - baseline

        # Earlier questions are slightly preferred (1 / avg_position term)
        positional_factor = 1.0 / avg_position

        boost = 0.5 * delta * positional_factor

        # Clamp to a small range so we don't overpower entropy
        boost = max(min(boost, 0.5), -0.5)
        boosts[key] = boost

    return boosts


def get_session_summaries() -> List[Dict[str, Any]]:
    """
    Lightweight session list for a history page.
    """
    sessions = _load_all_sessions()
    summaries: List[Dict[str, Any]] = []
    for entry in sessions:
        summaries.append(
            {
                "session_id": entry.get("session_id"),
                "final_song_id": entry.get("final_song_id"),
                "confidence": entry.get("confidence"),
                "success": entry.get("success"),
                "created_at": entry.get("created_at"),
                "correct_song_title": entry.get("correct_song_title"),
            }
        )
    summaries.sort(key=lambda s: s.get("created_at") or "", reverse=True)
    return summaries


def get_insights() -> Dict[str, Any]:
    """
    Insights payload for an analytics page.
    """
    stats = compute_question_stats()
    questions: List[Dict[str, Any]] = []
    for (feature, value), s in stats.items():
        questions.append(
            {
                "feature": feature,
                "value": value,
                "count": s.get("count", 0.0),
                "success_rate": s.get("success_rate", 0.0),
                "avg_position": s.get("avg_position", 0.0),
            }
        )
    questions.sort(key=lambda q: (q["success_rate"] * q["count"]), reverse=True)
    return {"questions": questions}

