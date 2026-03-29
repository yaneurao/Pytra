#!/usr/bin/env python3
"""Fail-fast guard for legacy `py2*.py` wrapper reintroduction.

The canonical CLI entrypoints are `src/pytra-cli.py` and `src/pytra-cli.py`.
Any reintroduced `src/py2*.py` wrapper file, path literal, or `import py2*`
reference (except `py2x`) should fail fast.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCAN_DIRS = [ROOT / "src", ROOT / "tools", ROOT / "test"]
SRC_ROOT = ROOT / "src"

CANONICAL_PY2_ENTRYPOINTS = {"pytra-cli.py", "pytra-cli.py"}
REMOVED_WRAPPER_MODULES = {
    ROOT / "src" / "toolchain" / "compiler" / "py2x_wrapper.py",
}

# `src/pytra-cli.py` / `src/pytra-cli.py` are canonical entrypoints and excluded.
LEGACY_CLI_PATH_RE = re.compile(r"src/py2(?!x(?:-selfhost)?\.py)[A-Za-z0-9_]*\.py")
# `import py2x` / `from py2x ...` are canonical and excluded.
LEGACY_CLI_IMPORT_RE = re.compile(r"(?m)^\s*(?:from|import)\s+(py2(?!x(?:\b|_))\w+)")

ALLOWED_PATH_REF_FILES: set[str] = set()

ALLOWED_IMPORT_REF_FILES: set[str] = set()


def _iter_py_files() -> list[Path]:
    files: list[Path] = []
    for root in SCAN_DIRS:
        if not root.exists():
            continue
        for p in sorted(root.rglob("*.py")):
            files.append(p)
    return files


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _find_reintroduced_wrapper_files() -> list[str]:
    hits: list[str] = []
    for path in sorted(SRC_ROOT.glob("py2*.py")):
        if path.name in CANONICAL_PY2_ENTRYPOINTS:
            continue
        hits.append(_rel(path))
    for removed_module in sorted(REMOVED_WRAPPER_MODULES):
        if removed_module.exists():
            hits.append(_rel(removed_module))
    return hits


def main() -> int:
    unexpected: list[str] = []
    for rel in _find_reintroduced_wrapper_files():
        unexpected.append(f"wrapper-file {rel}")
    for p in _iter_py_files():
        rel = _rel(p)
        txt = p.read_text(encoding="utf-8")
        path_hits = LEGACY_CLI_PATH_RE.findall(txt)
        if len(path_hits) > 0 and rel not in ALLOWED_PATH_REF_FILES:
            unexpected.append(f"path-ref {rel}: {path_hits[0]}")
        import_hits = LEGACY_CLI_IMPORT_RE.findall(txt)
        if len(import_hits) > 0 and rel not in ALLOWED_IMPORT_REF_FILES:
            unexpected.append(f"import-ref {rel}: {import_hits[0]}")

    if len(unexpected) > 0:
        print("[FAIL] legacy py2 wrapper reintroduction detected:")
        for line in unexpected:
            print(" -", line)
        print("Use src/pytra-cli.py or src/pytra-cli.py as canonical entrypoints.")
        return 1

    print("[OK] legacy CLI reference guard passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
