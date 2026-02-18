"""Language profile loader for CodeEmitter.

Loads JSON profile trees from src/profiles/<lang>/profile.json with include support.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _deep_merge(dst: dict[str, Any], src: dict[str, Any]) -> dict[str, Any]:
    out = dict(dst)
    for key, value in src.items():
        if key in out and isinstance(out[key], dict) and isinstance(value, dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"profile json root must be object: {path}")
    return payload


def _load_profile_with_includes(path: Path) -> dict[str, Any]:
    root = _load_json(path)
    merged: dict[str, Any] = {}
    includes = root.get("include")
    if isinstance(includes, list):
        for rel in includes:
            if not isinstance(rel, str) or rel == "":
                continue
            inc_path = (path.parent / rel).resolve()
            if not inc_path.exists():
                raise RuntimeError(f"profile include not found: {inc_path}")
            merged = _deep_merge(merged, _load_profile_with_includes(inc_path))

    filtered_root = {k: v for k, v in root.items() if k != "include"}
    merged = _deep_merge(merged, filtered_root)
    return merged


def load_language_profile(language: str) -> dict[str, Any]:
    """Load merged language profile by language name (e.g. cpp)."""
    base = Path(__file__).resolve().parents[1] / "profiles"
    common_core = base / "common" / "core.json"
    lang_profile = base / language / "profile.json"

    merged: dict[str, Any] = {}
    if common_core.exists():
        merged = _deep_merge(merged, _load_profile_with_includes(common_core))
    if not lang_profile.exists():
        raise RuntimeError(f"language profile not found: {lang_profile}")
    merged = _deep_merge(merged, _load_profile_with_includes(lang_profile))
    return merged
