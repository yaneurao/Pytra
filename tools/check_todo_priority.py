#!/usr/bin/env python3
"""Enforce TODO execution order by checking newly added progress IDs.

Rule:
- Read docs-ja/todo/index.md and find the first unfinished task ID in the highest
  priority bucket (smallest P<number>).
- Read net-new progress IDs from git diff of docs-ja/todo/index.md and
  docs-ja/plans/*.md.
- For plans, only decision-log style lines ("- YYYY-MM-DD: ...") are treated
  as progress entries; structural ID references are ignored.
- Every net-new progress ID must match that target ID, or be a child ID
  that starts with "<target>-".
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TODO_PATH = ROOT / "docs-ja" / "todo" / "index.md"
PLANS_DIR = ROOT / "docs-ja" / "plans"

TASK_RE = re.compile(r"^\s*\d+\.\s+\[( |x)\]\s+\[ID:\s*([A-Za-z0-9-]+)\]")
TODO_PROGRESS_RE = re.compile(r"^\s*-\s*`(P[0-9]+-[A-Za-z0-9-]+)`")
PLAN_ID_TOKEN_RE = re.compile(r"`(P[0-9]+-[A-Za-z0-9-]+)`")
PLAN_PROGRESS_LINE_RE = re.compile(r"^\s*-\s*\d{4}-\d{2}-\d{2}:")
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


def _extract_progress_ids_from_line(*, line: str, is_todo_file: bool) -> list[str]:
    if is_todo_file:
        m = TODO_PROGRESS_RE.match(line)
        if m is None:
            return []
        return [m.group(1)]

    if PLAN_PROGRESS_LINE_RE.match(line) is None:
        return []
    return [m.group(1) for m in PLAN_ID_TOKEN_RE.finditer(line)]


def _added_progress_ids_from_diff() -> list[str]:
    rel_todo = TODO_PATH.relative_to(ROOT).as_posix()
    rel_plans = PLANS_DIR.relative_to(ROOT).as_posix()
    cmd = ["git", "diff", "--unified=0", "--", rel_todo, rel_plans]
    p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if p.returncode != 0:
        return []

    added_seq: list[str] = []
    removed_counts: dict[str, int] = {}
    current_path = ""
    for raw in p.stdout.splitlines():
        if raw.startswith("+++ b/") or raw.startswith("--- a/"):
            current_path = raw[6:]
            continue
        is_added = raw.startswith("+") and not raw.startswith("+++")
        is_removed = raw.startswith("-") and not raw.startswith("---")
        if not is_added and not is_removed:
            continue
        is_todo_file = current_path == rel_todo
        is_plan_file = current_path.startswith(rel_plans + "/")
        if not is_todo_file and not is_plan_file:
            continue
        line = raw[1:]
        ids = _extract_progress_ids_from_line(line=line, is_todo_file=is_todo_file)
        if not ids:
            continue
        if is_added:
            added_seq.extend(ids)
            continue
        for pid in ids:
            removed_counts[pid] = removed_counts.get(pid, 0) + 1

    net_new: list[str] = []
    for pid in added_seq:
        remain = removed_counts.get(pid, 0)
        if remain > 0:
            removed_counts[pid] = remain - 1
            continue
        net_new.append(pid)
    return net_new


def _is_allowed_progress_id(target_id: str, progress_id: str) -> bool:
    return progress_id == target_id or progress_id.startswith(target_id + "-")


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
        print("[OK] no new progress entry in docs-ja/todo/index.md diff (skip)")
        return 0

    mismatched: list[str] = []
    for progress_id in added_ids:
        if not _is_allowed_progress_id(target_id, progress_id):
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
