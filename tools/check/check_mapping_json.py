#!/usr/bin/env python3
"""Validate all src/runtime/<lang>/mapping.json files.

Checks (per spec-emitter-guide §7.1–7.3):
  - valid JSON
  - top-level "calls" key exists
  - top-level "builtin_prefix" key exists
  - required entry "env.target" exists in "calls"
  - no empty-string values in "calls"

Exit code: 0 = all OK, 1 = validation errors found.

Usage:
    python3 tools/check_mapping_json.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNTIME_ROOT = ROOT / "src" / "runtime"


def check_mapping(path: Path) -> list[str]:
    """Return list of error messages for a single mapping.json."""
    errors: list[str] = []

    # Valid JSON
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"invalid JSON: {e}"]

    if not isinstance(doc, dict):
        return ["top-level value is not an object"]

    # "calls" key exists
    if "calls" not in doc:
        errors.append('missing required key "calls"')

    # "builtin_prefix" key exists
    if "builtin_prefix" not in doc:
        errors.append('missing required key "builtin_prefix"')

    calls = doc.get("calls", {})
    if not isinstance(calls, dict):
        errors.append('"calls" is not an object')
        return errors

    # "env.target" must be in calls
    if "env.target" not in calls:
        errors.append('"calls" is missing required entry "env.target" (see spec-emitter-guide §7.3)')

    # No empty-string values in calls
    for key, value in calls.items():
        if value == "":
            errors.append(f'"calls["{key}"]" is an empty string')

    return errors


def main() -> int:
    mapping_files = sorted(RUNTIME_ROOT.rglob("mapping.json"))
    if not mapping_files:
        print("[WARN] no mapping.json files found under src/runtime/")
        return 0

    has_error = False
    for path in mapping_files:
        rel = path.relative_to(ROOT)
        errors = check_mapping(path)
        if errors:
            has_error = True
            for err in errors:
                print(f"[FAIL] {rel}: {err}")
        else:
            print(f"[OK]   {rel}")

    if has_error:
        return 1
    print("[OK] all mapping.json files passed validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
