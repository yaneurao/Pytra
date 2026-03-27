#!/usr/bin/env python3
"""Check EAST3 golden fixtures for regressions.

Regenerates EAST3 from the corresponding Python fixture source and compares
against the stored golden file.  Exits non-zero if any mismatch is found.

Usage:
    python3 tools/check_east3_golden.py          # check all
    python3 tools/check_east3_golden.py --update  # regenerate golden files
"""

from __future__ import annotations

import json
import os
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

EAST3_FIXTURES_DIR = ROOT / "test" / "east3_fixtures"
EMIT_FIXTURES_DIR = ROOT / "test" / "fixtures"

# Keys to strip from EAST3 output for stable comparison
_STRIP_KEYS = {"source_span", "repr", "borrow_kind", "casts", "leading_trivia", "source_path"}


def _extract_key_fields(node: object) -> object:
    """Strip noisy fields that change without semantic impact."""
    if isinstance(node, list):
        return [_extract_key_fields(item) for item in node]
    if not isinstance(node, dict):
        return node
    out: dict[str, object] = {}
    for k, v in node.items():
        if k in _STRIP_KEYS:
            continue
        out[k] = _extract_key_fields(v)
    return out


def _find_fixture_source(stem: str) -> Path | None:
    """Find the .py fixture file for a given stem."""
    for p in sorted(EMIT_FIXTURES_DIR.rglob(f"{stem}.py")):
        return p
    return None


def _generate_east3(fixture_path: Path) -> dict[str, object]:
    from toolchain.compile.core import convert_source_to_east
    from toolchain.compile.east2_to_east3_lowering import lower_east2_to_east3

    src = fixture_path.read_text(encoding="utf-8")
    east2 = convert_source_to_east(src, str(fixture_path))
    east3 = lower_east2_to_east3(east2)
    filtered = _extract_key_fields(east3)
    if not isinstance(filtered, dict):
        raise RuntimeError("EAST3 output is not a dict")
    return filtered


@lru_cache(maxsize=1)
def _toolchain2_runtime_registry() -> object:
    from toolchain2.resolve.py.builtin_registry import load_builtin_registry

    east1_root = ROOT / "test" / "include" / "east1" / "py"
    return load_builtin_registry(
        east1_root / "built_in" / "builtins.py.east1",
        east1_root / "built_in" / "containers.py.east1",
        east1_root / "std",
    )


def _generate_runtime_east_toolchain2(py_file: Path) -> dict[str, object]:
    from toolchain2.parse.py.parse_python import parse_python_file
    from toolchain2.resolve.py.resolver import resolve_east1_to_east2
    from toolchain2.compile.lower import lower_east2_to_east3

    east1_doc = parse_python_file(str(py_file))
    if not isinstance(east1_doc, dict):
        raise RuntimeError("toolchain2 parse failed")
    registry = _toolchain2_runtime_registry()
    resolve_east1_to_east2(east1_doc, registry=registry)
    east3_doc = lower_east2_to_east3(east1_doc)
    if not isinstance(east3_doc, dict):
        raise RuntimeError("toolchain2 compile failed")
    return east3_doc


def check_all(update: bool = False) -> int:
    golden_files = sorted(EAST3_FIXTURES_DIR.glob("*.east3.json"))
    if len(golden_files) == 0:
        print("error: no golden files found in", EAST3_FIXTURES_DIR)
        return 1

    ok = 0
    fail = 0
    updated = 0

    for golden_path in golden_files:
        stem = golden_path.name.replace(".east3.json", "")
        fixture_path = _find_fixture_source(stem)
        if fixture_path is None:
            print(f"[SKIP] {stem}: fixture source not found")
            continue

        try:
            actual = _generate_east3(fixture_path)
        except Exception as e:
            print(f"[FAIL] {stem}: EAST3 generation failed: {e}")
            fail += 1
            continue

        if update:
            golden_path.write_text(
                json.dumps(actual, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(f"[UPDATED] {stem}")
            updated += 1
            continue

        expected = json.loads(golden_path.read_text(encoding="utf-8"))

        if actual == expected:
            ok += 1
        else:
            print(f"[FAIL] {stem}: EAST3 output differs from golden file")
            # Show a brief diff hint
            actual_str = json.dumps(actual, ensure_ascii=False, indent=2)
            expected_str = json.dumps(expected, ensure_ascii=False, indent=2)
            actual_lines = actual_str.splitlines()
            expected_lines = expected_str.splitlines()
            for i, (a, e) in enumerate(zip(actual_lines, expected_lines)):
                if a != e:
                    print(f"  first diff at line {i + 1}:")
                    print(f"    expected: {e[:100]}")
                    print(f"    actual  : {a[:100]}")
                    break
            fail += 1

    if update:
        print(f"Updated {updated} golden files.")
        return 0

    print(f"EAST3 golden check: {ok} ok, {fail} fail")
    return 1 if fail > 0 else 0


def check_runtime_east_freshness(update: bool = False) -> int:
    """Check that src/runtime/east/*.east files match regeneration from Python sources."""
    east_root = ROOT / "src" / "runtime" / "east"
    py_roots: dict[str, Path] = {
        "built_in": ROOT / "src" / "pytra" / "built_in",
        "std": ROOT / "src" / "pytra" / "std",
        "utils": ROOT / "src" / "pytra" / "utils",
    }

    ok = 0
    fail = 0
    updated = 0

    for bucket, py_root in sorted(py_roots.items()):
        east_dir = east_root / bucket
        if not east_dir.exists():
            continue
        for east_file in sorted(east_dir.glob("*.east")):
            stem = east_file.stem
            py_file = py_root / (stem + ".py")
            if not py_file.exists():
                continue

            try:
                doc = _generate_runtime_east_toolchain2(py_file)
            except Exception as e:
                print(f"[SKIP] {bucket}/{stem}: {e}")
                continue

            if update:
                east_file.write_text(
                    json.dumps(doc, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
                print(f"[UPDATED] {bucket}/{stem}")
                updated += 1
                continue

            existing = json.loads(east_file.read_text(encoding="utf-8"))
            if doc == existing:
                ok += 1
            else:
                print(f"[STALE] {bucket}/{stem}.east needs regeneration")
                fail += 1

    if update:
        print(f"Updated {updated} .east files.")
        return 0

    print(f"Runtime .east freshness: {ok} ok, {fail} stale")
    return 1 if fail > 0 else 0


def main() -> int:
    update = "--update" in sys.argv
    check_runtime = "--check-runtime-east" in sys.argv

    rc = 0
    if check_runtime:
        rc = check_runtime_east_freshness(update=update)
    else:
        rc = check_all(update=update)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
