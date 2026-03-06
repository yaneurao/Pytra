#!/usr/bin/env python3
"""Verify C++ runtime layer separation rules.

Rules:
- `src/runtime/cpp/built_in/**/*.gen.h|gen.cpp` must contain the auto-generated marker.
- `src/runtime/cpp/built_in/**/*.ext.h|ext.cpp` must NOT contain the auto-generated marker.
- `src/runtime/cpp/utils/**/*.gen.h|gen.cpp` must contain the auto-generated marker.
- `src/runtime/cpp/core/**/*.ext.h|ext.cpp` must NOT contain the auto-generated marker.
- `src/runtime/cpp/std/**/*.gen.h|gen.cpp` must contain the auto-generated marker.
- `src/runtime/cpp/std/**/*.ext.h|ext.cpp` must NOT contain the auto-generated marker.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILTIN_DIR = ROOT / "src/runtime/cpp/built_in"
CORE_DIR = ROOT / "src/runtime/cpp/core"
STD_DIR = ROOT / "src/runtime/cpp/std"
UTILS_DIR = ROOT / "src/runtime/cpp/utils"
PY_RUNTIME_EXT = ROOT / "src/runtime/cpp/core/built_in/py_runtime.ext.h"
MARKER = "AUTO-GENERATED FILE. DO NOT EDIT."
TARGET_SUFFIXES = {".h", ".cpp"}
BANNED_PY_RUNTIME_PATTERNS = {
    "static inline str sub(": "re.sub duplicate must not live in py_runtime.ext.h",
    "struct ArgumentParser": "argparse duplicate must not live in py_runtime.ext.h",
    "static inline bool py_any(": "predicate duplicate must not live in py_runtime.ext.h",
    "static inline bool py_all(": "predicate duplicate must not live in py_runtime.ext.h",
    "static inline str py_lstrip(": "string_ops duplicate must not live in py_runtime.ext.h",
    "static inline str py_rstrip(": "string_ops duplicate must not live in py_runtime.ext.h",
    "static inline str py_strip(": "string_ops duplicate must not live in py_runtime.ext.h",
    "static inline bool py_startswith(": "string_ops duplicate must not live in py_runtime.ext.h",
    "static inline bool py_endswith(": "string_ops duplicate must not live in py_runtime.ext.h",
    "static inline int64 py_find(": "string_ops duplicate must not live in py_runtime.ext.h",
    "static inline int64 py_rfind(": "string_ops duplicate must not live in py_runtime.ext.h",
    "static inline str py_replace(": "string_ops duplicate must not live in py_runtime.ext.h",
    "static inline list<int64> py_range(": "sequence duplicate must not live in py_runtime.ext.h",
    "static inline str py_repeat(": "sequence duplicate must not live in py_runtime.ext.h",
    "static inline bool py_contains(const dict<": "contains duplicate must not live in py_runtime.ext.h",
    "static inline bool py_contains(const list<": "contains duplicate must not live in py_runtime.ext.h",
    "static inline bool py_contains(const set<": "contains duplicate must not live in py_runtime.ext.h",
    "static inline bool py_contains(const str&": "contains duplicate must not live in py_runtime.ext.h",
    "static inline bool py_contains(const object&": "contains duplicate must not live in py_runtime.ext.h",
}


def _scan_targets(base: Path) -> list[Path]:
    out: list[Path] = []
    if not base.exists():
        return out
    for p in sorted(base.rglob("*")):
        if p.is_file() and p.suffix in TARGET_SUFFIXES:
            out.append(p)
    return out


def main() -> int:
    builtin_files = _scan_targets(BUILTIN_DIR)
    core_files = _scan_targets(CORE_DIR)
    std_files = _scan_targets(STD_DIR)
    utils_files = _scan_targets(UTILS_DIR)

    if not core_files:
        print(f"[FAIL] no C++ source/header files under: {CORE_DIR.relative_to(ROOT)}")
        return 1
    if not builtin_files:
        print(f"[FAIL] no C++ source/header files under: {BUILTIN_DIR.relative_to(ROOT)}")
        return 1
    if not utils_files:
        print(f"[FAIL] no C++ source/header files under: {UTILS_DIR.relative_to(ROOT)}")
        return 1

    missing_marker: list[str] = []
    unexpected_marker: list[str] = []
    invalid_name: list[str] = []
    banned_runtime_duplicates: list[str] = []

    for p in builtin_files:
        rel = str(p.relative_to(ROOT))
        txt = p.read_text(encoding="utf-8", errors="ignore")
        if ".gen." in p.name:
            if MARKER not in txt:
                missing_marker.append(rel)
        elif ".ext." in p.name:
            if MARKER in txt:
                unexpected_marker.append(rel)
        else:
            invalid_name.append(rel)
    for p in utils_files:
        rel = str(p.relative_to(ROOT))
        if ".gen." not in p.name:
            invalid_name.append(rel)
            continue
        txt = p.read_text(encoding="utf-8", errors="ignore")
        if MARKER not in txt:
            missing_marker.append(rel)

    for p in core_files:
        rel = str(p.relative_to(ROOT))
        if ".ext." not in p.name:
            invalid_name.append(rel)
            continue
        txt = p.read_text(encoding="utf-8", errors="ignore")
        if MARKER in txt:
            unexpected_marker.append(rel)
    for p in std_files:
        rel = str(p.relative_to(ROOT))
        txt = p.read_text(encoding="utf-8", errors="ignore")
        if ".gen." in p.name:
            if MARKER not in txt:
                missing_marker.append(rel)
        elif ".ext." in p.name:
            if MARKER in txt:
                unexpected_marker.append(rel)
        else:
            invalid_name.append(rel)

    if PY_RUNTIME_EXT.exists():
        py_runtime_txt = PY_RUNTIME_EXT.read_text(encoding="utf-8", errors="ignore")
        for pattern, reason in BANNED_PY_RUNTIME_PATTERNS.items():
            if pattern in py_runtime_txt:
                banned_runtime_duplicates.append(f"{pattern} :: {reason}")

    if missing_marker or unexpected_marker or invalid_name or banned_runtime_duplicates:
        print("[FAIL] runtime cpp layout guard failed")
        print(
            "  scanned: "
            + f"built_in={len(builtin_files)} files, "
            + f"utils={len(utils_files)} files, "
            + f"core={len(core_files)} files, "
            + f"std={len(std_files)} files"
        )
        if missing_marker:
            print("  generated files missing marker:")
            for item in missing_marker:
                print(f"    - {item}")
        if unexpected_marker:
            print("  handwritten files containing marker:")
            for item in unexpected_marker:
                print(f"    - {item}")
        if invalid_name:
            print("  files violating .gen/.ext naming:")
            for item in invalid_name:
                print(f"    - {item}")
        if banned_runtime_duplicates:
            print("  py_runtime.ext.h still contains duplicated high-level runtime bodies:")
            for item in banned_runtime_duplicates:
                print(f"    - {item}")
        return 1

    print("[OK] runtime cpp layout guard passed")
    print(f"  built_in+utils files with marker: {len(builtin_files) + len(utils_files)}")
    print(f"  core files without marker: {len(core_files)}")
    print(f"  std generated files with marker and handwritten files without marker: {len(std_files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
