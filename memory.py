"""
memory.py
---------
Simple JSON-based conversation memory.
Stores and retrieves user preferences and previous session context
so the agent can personalise responses across conversations.
"""

import json
import os
from datetime import datetime
from typing import Any

# Path to the persistent memory file
MEMORY_FILE = "memory.json"


def _load_raw() -> dict:
    """Load the raw memory dictionary from disk. Returns empty dict if not found."""
    if not os.path.exists(MEMORY_FILE):
        return {}
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_raw(data: dict) -> None:
    """Persist the memory dictionary to disk."""
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Public API ────────────────────────────────────────────────────────────────

def save_context(key: str, value: Any) -> None:
    """
    Store a single key-value pair in memory.

    Args:
        key:   Identifier, e.g. 'last_topic', 'difficulty', 'study_style'.
        value: Any JSON-serialisable value.
    """
    data = _load_raw()
    data[key] = value
    data["last_updated"] = datetime.now().isoformat(timespec="seconds")
    _save_raw(data)


def load_context(key: str, default: Any = None) -> Any:
    """
    Retrieve a value from memory by key.

    Args:
        key:     The key to look up.
        default: Value to return if key doesn't exist.

    Returns:
        The stored value or *default*.
    """
    data = _load_raw()
    return data.get(key, default)


def get_all_context() -> dict:
    """Return the entire memory store as a dictionary."""
    return _load_raw()


def update_session(topic: str, difficulty: str, study_style: str) -> None:
    """
    Convenience function: save the three most common session fields at once.

    Args:
        topic:       Current study topic.
        difficulty:  Quiz/study difficulty ('easy' | 'medium' | 'hard').
        study_style: User's preferred style, e.g. 'visual', 'practice-heavy'.
    """
    data = _load_raw()
    data["last_topic"]    = topic
    data["difficulty"]    = difficulty
    data["study_style"]   = study_style
    data["last_updated"]  = datetime.now().isoformat(timespec="seconds")

    # Maintain a rolling history of the last 5 topics studied
    history: list = data.get("topic_history", [])
    if topic and topic not in history:
        history.append(topic)
    data["topic_history"] = history[-5:]   # keep only the 5 most recent

    _save_raw(data)


def clear_memory() -> None:
    """Wipe all stored memory (useful for testing or resetting between users)."""
    if os.path.exists(MEMORY_FILE):
        os.remove(MEMORY_FILE)


def format_memory_summary() -> str:
    """
    Return a human-readable summary of stored memory for display in the UI
    and for injection into the agent's system prompt.

    Returns:
        A formatted string, or a message indicating no memory exists yet.
    """
    data = _load_raw()
    if not data:
        return "No previous context found. This appears to be your first session."

    lines = ["📋 Previous Session Context:"]

    if data.get("last_topic"):
        lines.append(f"  • Last topic studied : {data['last_topic']}")
    if data.get("difficulty"):
        lines.append(f"  • Preferred difficulty: {data['difficulty']}")
    if data.get("study_style"):
        lines.append(f"  • Study style         : {data['study_style']}")
    if data.get("topic_history"):
        history_str = ", ".join(data["topic_history"])
        lines.append(f"  • Topics studied so far: {history_str}")
    if data.get("last_updated"):
        lines.append(f"  • Last session        : {data['last_updated']}")

    return "\n".join(lines)
