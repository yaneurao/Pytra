#!/usr/bin/env python3
"""Verify C++ runtime layer separation rules.

Rules:
- `src/runtime/cpp/pytra-gen/**/*.h|cpp` must contain the auto-generated marker.
- `src/runtime/cpp/pytra-core/**/*.h|cpp` must NOT contain the auto-generated marker.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GEN_DIR = ROOT / "src/runtime/cpp/pytra-gen"
CORE_DIR = ROOT / "src/runtime/cpp/pytra-core"
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
    core_files = _scan_targets(CORE_DIR)

    if not gen_files:
        print(f"[FAIL] no C++ source/header files under: {GEN_DIR.relative_to(ROOT)}")
        return 1
    if not core_files:
        print(f"[FAIL] no C++ source/header files under: {CORE_DIR.relative_to(ROOT)}")
        return 1

    missing_marker: list[str] = []
    unexpected_marker: list[str] = []

    for p in gen_files:
        txt = p.read_text(encoding="utf-8", errors="ignore")
        if MARKER not in txt:
            missing_marker.append(str(p.relative_to(ROOT)))

    for p in core_files:
        txt = p.read_text(encoding="utf-8", errors="ignore")
        if MARKER in txt:
            unexpected_marker.append(str(p.relative_to(ROOT)))

    if missing_marker or unexpected_marker:
        print("[FAIL] runtime cpp layout guard failed")
        print(
            f"  scanned: pytra-gen={len(gen_files)} files, pytra-core={len(core_files)} files"
        )
        if missing_marker:
            print("  pytra-gen files missing marker:")
            for item in missing_marker:
                print(f"    - {item}")
        if unexpected_marker:
            print("  pytra-core files containing marker:")
            for item in unexpected_marker:
                print(f"    - {item}")
        return 1

    print("[OK] runtime cpp layout guard passed")
    print(f"  pytra-gen files with marker: {len(gen_files)}")
    print(f"  pytra-core files without marker: {len(core_files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
