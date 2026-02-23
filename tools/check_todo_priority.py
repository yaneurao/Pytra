#!/usr/bin/env python3
"""Enforce TODO execution order by checking newly added progress IDs.

Rule:
- Read docs-jp/todo.md and find the first unfinished task ID in the highest
  priority bucket (smallest P<number>).
- Read newly added progress memo IDs from git diff of docs-jp/todo.md.
- Every newly added progress ID must match that target ID exactly.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TODO_PATH = ROOT / "docs-jp" / "todo.md"

TASK_RE = re.compile(r"^\s*\d+\.\s+\[( |x)\]\s+\[ID:\s*([A-Za-z0-9-]+)\]")
PROGRESS_RE = re.compile(r"^\s*-\s*`(P[0-9]+-[A-Za-z0-9-]+)`")
PRIO_RE = re.compile(r"^P([0-9]+)-")


def _priority_of(task_id: str) -> int | None:
    m = PRIO_RE.match(task_id)
    if m is None:
        return None
    return int(m.group(1))


def _highest_unfinished_id(lines: list[str]) -> str | None:
    best_priority: int | None = None
    best_id: str | None = None
    for line in lines:
        m = TASK_RE.match(line)
        if m is None:
            continue
        status = m.group(1)
        task_id = m.group(2)
        if status != " ":
            continue
        prio = _priority_of(task_id)
        if prio is None:
            continue
        if best_priority is None or prio < best_priority:
            best_priority = prio
            best_id = task_id
    return best_id


def _added_progress_ids_from_diff() -> list[str]:
    rel = TODO_PATH.relative_to(ROOT).as_posix()
    cmd = ["git", "diff", "--unified=0", "--", rel]
    p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if p.returncode != 0:
        return []
    out_ids: list[str] = []
    for raw in p.stdout.splitlines():
        if not raw.startswith("+") or raw.startswith("+++"):
            continue
        line = raw[1:]
        m = PROGRESS_RE.match(line)
        if m is None:
            continue
        out_ids.append(m.group(1))
    return out_ids


def main() -> int:
    if not TODO_PATH.exists():
        print(f"[FAIL] missing: {TODO_PATH}", file=sys.stderr)
        return 1

    lines = TODO_PATH.read_text(encoding="utf-8").splitlines()
    target_id = _highest_unfinished_id(lines)
    if target_id is None:
        print("[OK] no unfinished todo item found")
        return 0

    added_ids = _added_progress_ids_from_diff()
    if not added_ids:
        print("[OK] no new progress entry in docs-jp/todo.md diff (skip)")
        return 0

    mismatched: list[str] = []
    for progress_id in added_ids:
        if progress_id != target_id:
            mismatched.append(progress_id)

    if mismatched:
        print("[FAIL] todo priority guard failed")
        print(f"  highest unfinished id: {target_id}")
        print("  newly added progress ids:")
        for item in added_ids:
            print(f"    - {item}")
        print("  mismatched ids:")
        for item in mismatched:
            print(f"    - {item}")
        return 1

    print("[OK] todo priority guard passed")
    print(f"  highest unfinished id: {target_id}")
    for item in added_ids:
        print(f"  added progress id: {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
