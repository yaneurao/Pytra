#!/usr/bin/env python3
"""Fail-fast guard for unexpected legacy `py2*.py` references.

This guard freezes current legacy reference locations until `S3-02` removes
the wrappers entirely. New files introducing `src/py2*.py` path literals or
`import py2*` usage fail this check.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCAN_DIRS = [ROOT / "src", ROOT / "tools", ROOT / "test"]

# `src/py2x.py` / `src/py2x-selfhost.py` are canonical entrypoints and excluded.
LEGACY_CLI_PATH_RE = re.compile(r"src/py2(?!x(?:-selfhost)?\.py)[A-Za-z0-9_]*\.py")
# `import py2x` / `from py2x ...` are canonical and excluded.
LEGACY_CLI_IMPORT_RE = re.compile(r"(?m)^\s*(?:from|import)\s+(py2(?!x(?:\b|_))\w+)")

ALLOWED_PATH_REF_FILES = {
    "src/backends/cpp/emitter/header_builder.py",
    "src/backends/cpp/emitter/profile_loader.py",
    "src/backends/cpp/emitter/runtime_paths.py",
    "src/backends/cs/emitter/cs_emitter.py",
    "tools/check_multilang_selfhost_multistage.py",
    "tools/check_multilang_selfhost_stage1.py",
    "tools/check_noncpp_east3_contract.py",
    "tools/check_py2cpp_boundary.py",
    "tools/check_py2cpp_helper_guard.py",
    "tools/check_py2cpp_transpile.py",
    "tools/check_transpiler_version_gate.py",
}

ALLOWED_IMPORT_REF_FILES = {
    "src/backends/cpp/emitter/__init__.py",
    "src/py2x.py",
    "src/toolchain/compiler/backend_registry_static.py",
    "test/unit/test_error_classification_cross_lang.py",
    "tools/benchmark_cpp_list_models.py",
}


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


def main() -> int:
    unexpected: list[str] = []
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
        print("[FAIL] unexpected legacy CLI reference(s) detected:")
        for line in unexpected:
            print(" -", line)
        print("Add migration to py2x/py2x-selfhost or update this guard intentionally.")
        return 1

    print("[OK] legacy CLI reference guard passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

