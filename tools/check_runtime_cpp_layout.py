#!/usr/bin/env python3
"""Verify C++ runtime layer separation rules.

Rules:
- `src/runtime/cpp/gen/**/*.h|cpp` must contain the auto-generated marker.
- `src/runtime/cpp/built_in/**/*.h|cpp` must contain the auto-generated marker.
- `src/runtime/cpp/core/**/*.h|cpp` must NOT contain the auto-generated marker.
- `src/runtime/cpp/std/**/*.h` must contain the auto-generated marker.
- `src/runtime/cpp/std/**/*.cpp` must NOT contain the auto-generated marker.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GEN_DIR = ROOT / "src/runtime/cpp/gen"
BUILTIN_DIR = ROOT / "src/runtime/cpp/built_in"
CORE_DIR = ROOT / "src/runtime/cpp/core"
STD_DIR = ROOT / "src/runtime/cpp/std"
MARKER = "AUTO-GENERATED FILE. DO NOT EDIT."
TARGET_SUFFIXES = {".h", ".cpp"}


def _scan_targets(base: Path) -> list[Path]:
    out: list[Path] = []
    if not base.exists():
        return out
    for p in sorted(base.rglob("*")):
        if p.is_file() and p.suffix in TARGET_SUFFIXES:
            out.append(p)
    return out


def main() -> int:
    gen_files = _scan_targets(GEN_DIR)
    builtin_files = _scan_targets(BUILTIN_DIR)
    core_files = _scan_targets(CORE_DIR)
    std_files = _scan_targets(STD_DIR)

    if not gen_files:
        print(f"[FAIL] no C++ source/header files under: {GEN_DIR.relative_to(ROOT)}")
        return 1
    if not core_files:
        print(f"[FAIL] no C++ source/header files under: {CORE_DIR.relative_to(ROOT)}")
        return 1
    if not builtin_files:
        print(f"[FAIL] no C++ source/header files under: {BUILTIN_DIR.relative_to(ROOT)}")
        return 1

    missing_marker: list[str] = []
    unexpected_marker: list[str] = []
    std_h_missing_marker: list[str] = []
    std_cpp_unexpected_marker: list[str] = []

    for p in gen_files:
        txt = p.read_text(encoding="utf-8", errors="ignore")
        if MARKER not in txt:
            missing_marker.append(str(p.relative_to(ROOT)))
    for p in builtin_files:
        txt = p.read_text(encoding="utf-8", errors="ignore")
        if MARKER not in txt:
            missing_marker.append(str(p.relative_to(ROOT)))

    for p in core_files:
        txt = p.read_text(encoding="utf-8", errors="ignore")
        if MARKER in txt:
            unexpected_marker.append(str(p.relative_to(ROOT)))
    for p in std_files:
        txt = p.read_text(encoding="utf-8", errors="ignore")
        rel = str(p.relative_to(ROOT))
        if p.suffix == ".h":
            if MARKER not in txt:
                std_h_missing_marker.append(rel)
        elif p.suffix == ".cpp":
            if MARKER in txt:
                std_cpp_unexpected_marker.append(rel)

    if missing_marker or unexpected_marker or std_h_missing_marker or std_cpp_unexpected_marker:
        print("[FAIL] runtime cpp layout guard failed")
        print(
            "  scanned: "
            + f"gen={len(gen_files)} files, "
            + f"built_in={len(builtin_files)} files, "
            + f"core={len(core_files)} files, "
            + f"std={len(std_files)} files"
        )
        if missing_marker:
            print("  gen files missing marker:")
            for item in missing_marker:
                print(f"    - {item}")
        if unexpected_marker:
            print("  core files containing marker:")
            for item in unexpected_marker:
                print(f"    - {item}")
        if std_h_missing_marker:
            print("  std headers missing marker:")
            for item in std_h_missing_marker:
                print(f"    - {item}")
        if std_cpp_unexpected_marker:
            print("  std sources containing marker:")
            for item in std_cpp_unexpected_marker:
                print(f"    - {item}")
        return 1

    print("[OK] runtime cpp layout guard passed")
    print(f"  gen+built_in files with marker: {len(gen_files) + len(builtin_files)}")
    print(f"  core files without marker: {len(core_files)}")
    print(f"  std headers with marker / sources without marker: {len(std_files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
