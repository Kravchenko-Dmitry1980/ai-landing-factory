"""Stable candidate id generation."""

from __future__ import annotations

import hashlib


def make_candidate_id(raw_name: str, source_filename: str = "") -> str:
    """Stable id for a team review candidate."""
    key = f"{raw_name.strip().lower()}|{source_filename}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]
