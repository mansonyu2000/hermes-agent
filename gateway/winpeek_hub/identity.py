"""
identity.py — WinPeek MIM identity management with JSONL persistence.

Stores identities at ~/.hermes/winpeek/identities.jsonl.
Provides: register, login, get_identity, list_identities.
"""
import json
import os
import time
from pathlib import Path
from typing import Optional

IDENTITIES_PATH = Path.home() / ".hermes" / "winpeek" / "identities.jsonl"

ROLES = ["Developer", "Architect", "Ops", "QA", "PM", "Director", "Boss"]


def _ensure_dir():
    IDENTITIES_PATH.parent.mkdir(parents=True, exist_ok=True)


def _read_all() -> list[dict]:
    """Read all identities from JSONL file."""
    _ensure_dir()
    if not IDENTITIES_PATH.exists():
        return []
    results = []
    with open(IDENTITIES_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return results


def _append(entry: dict):
    """Append one identity to JSONL file."""
    _ensure_dir()
    with open(IDENTITIES_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def register(nickname: str, role: str = "Developer", host: str = "local") -> dict | None:
    """
    Register a new identity. Returns the created identity, or None if nickname taken.
    """
    if role not in ROLES:
        role = "Developer"

    all_ids = _read_all()
    for entry in all_ids:
        if entry.get("nickname", "").lower() == nickname.lower():
            return None  # already exists

    uid = 2000 + len(all_ids) + 1
    identity = {
        "uid": uid,
        "nickname": nickname,
        "role": role,
        "host": host,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    _append(identity)
    return identity


def login(nickname: str) -> dict | None:
    """
    Login by nickname. Returns identity if found.
    """
    all_ids = _read_all()
    for entry in all_ids:
        if entry.get("nickname", "").lower() == nickname.lower():
            return entry
    return None


def get_by_uid(uid: int) -> Optional[dict]:
    """Get identity by uid."""
    for entry in _read_all():
        if entry.get("uid") == uid:
            return entry
    return None


def list_all() -> list[dict]:
    """List all registered identities."""
    return _read_all()
