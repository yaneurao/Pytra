#!/usr/bin/env python3
"""Fail when source/tooling code references legacy `src/runtime2` paths."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST_FILE = ROOT / "tools" / "runtime2_reference_allowlist.txt"
SCAN_DIRS = ("src", "tools", "test", "pytra")
TEXT_SUFFIXES = {
    ".py",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".sh",
    ".ps1",
    ".bat",
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".h",
    ".hpp",
    ".hh",
    ".cs",
    ".go",
    ".java",
    ".kt",
    ".swift",
    ".rs",
    ".rb",
    ".lua",
    ".scala",
    ".nim",
    ".php",
    ".js",
    ".ts",
    ".tsx",
}
NEEDLES = ("src/runtime2/", "runtime2/cpp/")


def _load_allowlist() -> set[str]:
    if not ALLOWLIST_FILE.exists():
        return set()
    out: set[str] = set()
    for raw in ALLOWLIST_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        out.add(line)
    return out


def _iter_files() -> list[Path]:
    files: list[Path] = []
    for rel in SCAN_DIRS:
        base = ROOT / rel
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in TEXT_SUFFIXES:
                continue
            if p == Path(__file__) or p == ALLOWLIST_FILE:
                continue
            try:
                relp = p.relative_to(ROOT)
            except ValueError:
                continue
            if relp.parts[:2] == ("src", "runtime2"):
                continue
            files.append(p)
    return files


def main() -> int:
    allowlist = _load_allowlist()
    findings: list[str] = []
    for path in _iter_files():
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        rel = path.relative_to(ROOT).as_posix()
        for lineno, line in enumerate(text.splitlines(), start=1):
            for needle in NEEDLES:
                if needle not in line:
                    continue
                key = f"{rel}:{lineno}"
                if key in allowlist:
                    continue
                findings.append(f"{key}: {line.strip()}")
                break
    if findings:
        print("[FAIL] runtime2 legacy references detected")
        for item in findings:
            print("-", item)
        if allowlist:
            print(f"[hint] allowlist: {ALLOWLIST_FILE.relative_to(ROOT).as_posix()}")
        return 1
    print("[OK] no runtime2 legacy references in source/tooling/test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
