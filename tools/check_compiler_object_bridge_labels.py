#!/usr/bin/env python3
"""Guard remaining compiler object-bridge usages with explicit labels."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TARGET_PATHS = [
    ROOT / "src" / "toolchain",
    ROOT / "src" / "py2x.py",
    ROOT / "src" / "ir2lang.py",
    ROOT / "src" / "runtime" / "cpp" / "native" / "compiler",
]

TARGET_SUFFIXES = {".py", ".cpp", ".h"}
ALLOWED_LABELS = {
    "user_boundary",
    "json_adapter",
    "legacy_migration_adapter",
    "extern_hook",
}
LABEL_RE = re.compile(r"(?:#|//)\s*P2-object-bridge:\s*([a-z_]+)")
BRIDGE_PATTERNS = (
    re.compile(r"\bmake_object\("),
    re.compile(r"\bpy_to<"),
    re.compile(r"\bobj_to_[A-Za-z0-9_]+\("),
)


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.name


def _iter_target_files() -> list[Path]:
    out: list[Path] = []
    for target in TARGET_PATHS:
        if target.is_dir():
            for path in sorted(target.rglob("*")):
                if path.is_file() and path.suffix in TARGET_SUFFIXES:
                    out.append(path)
            continue
        if target.is_file():
            out.append(target)
    return out


def _line_has_bridge_usage(line: str) -> bool:
    return any(pattern.search(line) is not None for pattern in BRIDGE_PATTERNS)


def _label_for_usage(lines: list[str], index: int) -> str:
    match = LABEL_RE.search(lines[index])
    if match is not None:
        return match.group(1)
    probe = index - 1
    while probe >= 0:
        stripped = lines[probe].strip()
        if stripped == "":
            probe -= 1
            continue
        match = LABEL_RE.search(lines[probe])
        if match is not None:
            return match.group(1)
        return ""
    return ""


def _has_labeled_usage_ahead(lines: list[str], index: int) -> bool:
    probe = index + 1
    while probe < len(lines):
        stripped = lines[probe].strip()
        if stripped == "":
            probe += 1
            continue
        if LABEL_RE.search(lines[probe]) is not None:
            return False
        return _line_has_bridge_usage(lines[probe])
    return False


def _collect_file_issues(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    issues: list[str] = []
    for index, line in enumerate(lines):
        label_match = LABEL_RE.search(line)
        if label_match is not None:
            label = label_match.group(1)
            if label not in ALLOWED_LABELS:
                issues.append(
                    f"{_display_path(path)}:{index + 1}: unsupported bridge label: {label}"
                )
            elif not _has_labeled_usage_ahead(lines, index):
                issues.append(
                    f"{_display_path(path)}:{index + 1}: bridge label is not attached to a bridge usage"
                )
        if not _line_has_bridge_usage(line):
            continue
        label = _label_for_usage(lines, index)
        if label == "":
            issues.append(
                f"{_display_path(path)}:{index + 1}: unlabeled compiler object bridge usage"
            )
            continue
        if label not in ALLOWED_LABELS:
            issues.append(
                f"{_display_path(path)}:{index + 1}: unsupported bridge label on usage: {label}"
            )
    return issues


def _collect_file_labeled_usages(path: Path) -> list[tuple[str, int, str]]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    usages: list[tuple[str, int, str]] = []
    for index, line in enumerate(lines):
        if not _line_has_bridge_usage(line):
            continue
        label = _label_for_usage(lines, index)
        if label == "" or label not in ALLOWED_LABELS:
            continue
        usages.append((_display_path(path), index + 1, label))
    return usages


def _collect_all_issues() -> list[str]:
    issues: list[str] = []
    for path in _iter_target_files():
        issues.extend(_collect_file_issues(path))
    return issues


def _collect_all_labeled_usages() -> list[tuple[str, int, str]]:
    usages: list[tuple[str, int, str]] = []
    for path in _iter_target_files():
        usages.extend(_collect_file_labeled_usages(path))
    return usages


def main() -> int:
    parser = argparse.ArgumentParser(description="Check compiler object-bridge labels")
    parser.parse_args()
    issues = _collect_all_issues()
    if len(issues) == 0:
        print("[OK] compiler object-bridge usages are explicitly labeled")
        return 0
    for issue in issues:
        print(issue, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
