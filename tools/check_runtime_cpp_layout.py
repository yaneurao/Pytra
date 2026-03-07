#!/usr/bin/env python3
"""Verify C++ runtime layer separation rules.

Rules:
- Legacy module runtime under `src/runtime/cpp/{built_in,std,utils}` may still use `.gen/.ext`.
- New module runtime under `src/runtime/cpp/generated/**` must contain the auto-generated marker.
- New module runtime under `src/runtime/cpp/native/**` must NOT contain the auto-generated marker.
- Public shim under `src/runtime/cpp/pytra/**` must contain the auto-generated marker and stay header-only.
- `src/runtime/cpp/core/**` remains handwritten for now and must keep `.ext.*` naming.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILTIN_DIR = ROOT / "src/runtime/cpp/built_in"
CORE_DIR = ROOT / "src/runtime/cpp/core"
GENERATED_DIR = ROOT / "src/runtime/cpp/generated"
NATIVE_DIR = ROOT / "src/runtime/cpp/native"
PYTRA_DIR = ROOT / "src/runtime/cpp/pytra"
STD_DIR = ROOT / "src/runtime/cpp/std"
UTILS_DIR = ROOT / "src/runtime/cpp/utils"
PY_RUNTIME_EXT = ROOT / "src/runtime/cpp/core/py_runtime.ext.h"
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


def _is_plain_cpp_name(path: Path) -> bool:
    return ".gen." not in path.name and ".ext." not in path.name


def _check_legacy_module_files(
    files: list[Path],
    missing_marker: list[str],
    unexpected_marker: list[str],
    invalid_name: list[str],
) -> None:
    for p in files:
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


def _check_generated_files(
    files: list[Path],
    missing_marker: list[str],
    invalid_name: list[str],
) -> None:
    for p in files:
        rel = str(p.relative_to(ROOT))
        txt = p.read_text(encoding="utf-8", errors="ignore")
        if not _is_plain_cpp_name(p):
            invalid_name.append(rel)
        if MARKER not in txt:
            missing_marker.append(rel)


def _check_handwritten_files(
    files: list[Path],
    unexpected_marker: list[str],
    invalid_name: list[str],
    *,
    require_ext_name: bool,
) -> None:
    for p in files:
        rel = str(p.relative_to(ROOT))
        txt = p.read_text(encoding="utf-8", errors="ignore")
        if require_ext_name:
            if ".ext." not in p.name:
                invalid_name.append(rel)
        else:
            if not _is_plain_cpp_name(p):
                invalid_name.append(rel)
        if MARKER in txt:
            unexpected_marker.append(rel)


def _check_public_shim_files(
    files: list[Path],
    missing_marker: list[str],
    invalid_name: list[str],
) -> None:
    for p in files:
        rel = str(p.relative_to(ROOT))
        txt = p.read_text(encoding="utf-8", errors="ignore")
        if p.suffix != ".h" or not _is_plain_cpp_name(p):
            invalid_name.append(rel)
        if MARKER not in txt:
            missing_marker.append(rel)


def main() -> int:
    builtin_files = _scan_targets(BUILTIN_DIR)
    core_files = _scan_targets(CORE_DIR)
    generated_files = _scan_targets(GENERATED_DIR)
    native_files = _scan_targets(NATIVE_DIR)
    pytra_files = _scan_targets(PYTRA_DIR)
    std_files = _scan_targets(STD_DIR)
    utils_files = _scan_targets(UTILS_DIR)
    legacy_module_files = builtin_files + std_files + utils_files

    if not core_files:
        print(f"[FAIL] no C++ source/header files under: {CORE_DIR.relative_to(ROOT)}")
        return 1
    if not legacy_module_files and not generated_files and not native_files and not pytra_files:
        print("[FAIL] no module runtime files found under legacy or generated/native/pytra layout")
        return 1

    missing_marker: list[str] = []
    unexpected_marker: list[str] = []
    invalid_name: list[str] = []
    banned_runtime_duplicates: list[str] = []

    _check_legacy_module_files(legacy_module_files, missing_marker, unexpected_marker, invalid_name)
    _check_generated_files(generated_files, missing_marker, invalid_name)
    _check_handwritten_files(core_files, unexpected_marker, invalid_name, require_ext_name=True)
    _check_handwritten_files(native_files, unexpected_marker, invalid_name, require_ext_name=False)
    _check_public_shim_files(pytra_files, missing_marker, invalid_name)

    if PY_RUNTIME_EXT.exists():
        py_runtime_txt = PY_RUNTIME_EXT.read_text(encoding="utf-8", errors="ignore")
        for pattern, reason in BANNED_PY_RUNTIME_PATTERNS.items():
            if pattern in py_runtime_txt:
                banned_runtime_duplicates.append(f"{pattern} :: {reason}")

    if missing_marker or unexpected_marker or invalid_name or banned_runtime_duplicates:
        print("[FAIL] runtime cpp layout guard failed")
        print(
            "  scanned: "
            + f"legacy_module={len(legacy_module_files)} files, "
            + f"generated={len(generated_files)} files, "
            + f"native={len(native_files)} files, "
            + f"pytra={len(pytra_files)} files, "
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
    print(f"  legacy module files: {len(legacy_module_files)}")
    print(f"  generated dir files with marker: {len(generated_files)}")
    print(f"  public shim files with marker: {len(pytra_files)}")
    print(f"  native dir files without marker: {len(native_files)}")
    print(f"  core files without marker: {len(core_files)}")
    print(f"  legacy std files checked: {len(std_files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
