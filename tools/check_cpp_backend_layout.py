#!/usr/bin/env python3
"""Check C++ backend layout: no legacy dirs/imports outside lower/optimizer/emitter."""

from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]

LEGACY_DIRS = [
    ROOT / "src" / "backends" / "cpp" / "hooks",
    ROOT / "src" / "backends" / "cpp" / "header",
    ROOT / "src" / "backends" / "cpp" / "multifile",
    ROOT / "src" / "backends" / "cpp" / "profile",
    ROOT / "src" / "backends" / "cpp" / "runtime_emit",
]

LEGACY_IMPORT_RE = re.compile(
    r"\b(from|import)\s+backends\.cpp\.(hooks|header|multifile|profile|runtime_emit)\b"
)


def _iter_py_files() -> list[Path]:
    files: list[Path] = []
    for top in (ROOT / "src", ROOT / "tools", ROOT / "test"):
        if not top.exists():
            continue
        for p in top.rglob("*.py"):
            if "__pycache__" in p.parts:
                continue
            files.append(p)
    files.sort()
    return files


def _check_legacy_dirs() -> list[str]:
    fails: list[str] = []
    for path in LEGACY_DIRS:
        if path.exists():
            fails.append(f"legacy dir still exists: {path.relative_to(ROOT)}")
    return fails


def _check_legacy_imports() -> list[str]:
    fails: list[str] = []
    for path in _iter_py_files():
        text = path.read_text(encoding="utf-8")
        m = LEGACY_IMPORT_RE.search(text)
        if not m:
            continue
        line = text.count("\n", 0, m.start()) + 1
        rel = path.relative_to(ROOT)
        snippet = text.splitlines()[line - 1].strip()
        fails.append(f"legacy import in {rel}:{line}: {snippet}")
    return fails


def main() -> int:
    fails = _check_legacy_dirs()
    fails.extend(_check_legacy_imports())
    if fails:
        print(f"failed={len(fails)}")
        for msg in fails:
            print("FAIL", msg)
        return 1
    print("checked=cpp_backend_layout ok=1 fail=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
