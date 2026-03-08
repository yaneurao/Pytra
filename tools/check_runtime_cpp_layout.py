#!/usr/bin/env python3
"""Verify C++ runtime ownership rules.

Rules:
- Module runtime under `src/runtime/cpp/{built_in,std,utils}` is legacy-closed and must not contain `.h/.cpp`.
- Compiler runtime under `src/runtime/cpp/{generated,native,pytra}/compiler` is the stage1 bootstrap lane.
- Module runtime under `src/runtime/cpp/generated/{built_in,std,utils,compiler}` must contain the auto-generated marker.
- Module runtime under `src/runtime/cpp/native/{built_in,std,utils,compiler}` must NOT contain the auto-generated marker.
- Public shim under `src/runtime/cpp/pytra/{built_in,std,utils,compiler}` must contain the auto-generated marker and stay header-only.
- `src/runtime/cpp/core/**` is the stable include surface and must not contain implementation `.cpp`.
- Future `src/runtime/cpp/generated/core/**` and `src/runtime/cpp/native/core/**` must obey generated/handwritten marker rules without reintroducing ownership mixing under `core/`.
"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKER = "AUTO-GENERATED FILE. DO NOT EDIT."
TARGET_SUFFIXES = {".h", ".cpp"}
BANNED_PY_RUNTIME_PATTERNS = {
    "static inline str sub(": "re.sub duplicate must not live in the py_runtime core header",
    "struct ArgumentParser": "argparse duplicate must not live in the py_runtime core header",
    "static inline bool py_any(": "predicate duplicate must not live in the py_runtime core header",
    "static inline bool py_all(": "predicate duplicate must not live in the py_runtime core header",
    "static inline str py_lstrip(": "string_ops duplicate must not live in the py_runtime core header",
    "static inline str py_rstrip(": "string_ops duplicate must not live in the py_runtime core header",
    "static inline str py_strip(": "string_ops duplicate must not live in the py_runtime core header",
    "static inline bool py_startswith(": "string_ops duplicate must not live in the py_runtime core header",
    "static inline bool py_endswith(": "string_ops duplicate must not live in the py_runtime core header",
    "static inline int64 py_find(": "string_ops duplicate must not live in the py_runtime core header",
    "static inline int64 py_rfind(": "string_ops duplicate must not live in the py_runtime core header",
    "static inline str py_replace(": "string_ops duplicate must not live in the py_runtime core header",
    "sum(const list<T>& values)": "numeric template helper duplicate must not live in the py_runtime core header",
    "py_min(const T& a, const T& b)": "numeric template helper duplicate must not live in the py_runtime core header",
    "py_max(const T& a, const T& b)": "numeric template helper duplicate must not live in the py_runtime core header",
    "zip(const list<A>& lhs, const list<B>& rhs)": "zip template helper duplicate must not live in the py_runtime core header",
    "static inline list<int64> py_range(": "sequence duplicate must not live in the py_runtime core header",
    "static inline str py_repeat(": "sequence duplicate must not live in the py_runtime core header",
    "static inline bool py_contains(const dict<": "contains duplicate must not live in the py_runtime core header",
    "static inline bool py_contains(const list<": "contains duplicate must not live in the py_runtime core header",
    "static inline bool py_contains(const set<": "contains duplicate must not live in the py_runtime core header",
    "static inline bool py_contains(const str&": "contains duplicate must not live in the py_runtime core header",
    "static inline bool py_contains(const object&": "contains duplicate must not live in the py_runtime core header",
}
BANNED_PY_RUNTIME_INCLUDE_PATTERNS = {
    '#include "runtime/cpp/generated/built_in/predicates.h"': (
        "predicate helper companions must not be re-aggregated via py_runtime"
    ),
    '#include "runtime/cpp/generated/built_in/sequence.h"': (
        "sequence helper companions must not be re-aggregated via py_runtime"
    ),
    '#include "runtime/cpp/native/built_in/sequence.h"': (
        "sequence native helpers must not be re-aggregated via py_runtime"
    ),
    '#include "runtime/cpp/generated/built_in/iter_ops.h"': (
        "iter helper companions must not be re-aggregated via py_runtime"
    ),
    '#include "runtime/cpp/native/built_in/iter_ops.h"': (
        "iter native helpers must not be re-aggregated via py_runtime"
    ),
}
DIRECT_NATIVE_CORE_INCLUDE_RE = re.compile(r'^\s*#include\s+"(runtime/cpp/native/core/[^"]+)"', re.MULTILINE)


def _runtime_cpp_path(*parts: str) -> Path:
    return ROOT / "src" / "runtime" / "cpp" / Path(*parts)


def _scan_targets(base: Path) -> list[Path]:
    out: list[Path] = []
    if not base.exists():
        return out
    for p in sorted(base.rglob("*")):
        if p.is_file() and p.suffix in TARGET_SUFFIXES:
            out.append(p)
    return out


def _scan_bucketed_targets(base: Path, allowed_buckets: set[str]) -> tuple[list[Path], list[Path]]:
    files: list[Path] = []
    unexpected: list[Path] = []
    if not base.exists():
        return files, unexpected
    for p in sorted(base.rglob("*")):
        if not p.is_file() or p.suffix not in TARGET_SUFFIXES:
            continue
        rel = p.relative_to(base)
        bucket = rel.parts[0] if len(rel.parts) > 0 else ""
        if bucket not in allowed_buckets:
            unexpected.append(p)
            continue
        files.append(p)
    return files, unexpected


def _is_plain_cpp_name(path: Path) -> bool:
    return ".gen." not in path.name and ".ext." not in path.name


def _matches_name_policy(path: Path, policy: str) -> bool:
    if policy == "plain":
        return _is_plain_cpp_name(path)
    if policy == "ext_only":
        return ".ext." in path.name
    raise ValueError(f"unknown name policy: {policy}")


def _check_generated_files(
    files: list[Path],
    missing_marker: list[str],
    invalid_name: list[str],
    *,
    name_policy: str,
) -> None:
    for p in files:
        rel = str(p.relative_to(ROOT))
        txt = p.read_text(encoding="utf-8", errors="ignore")
        if not _matches_name_policy(p, name_policy):
            invalid_name.append(rel)
        if MARKER not in txt:
            missing_marker.append(rel)


def _check_handwritten_files(
    files: list[Path],
    unexpected_marker: list[str],
    invalid_name: list[str],
    *,
    name_policy: str,
) -> None:
    for p in files:
        rel = str(p.relative_to(ROOT))
        txt = p.read_text(encoding="utf-8", errors="ignore")
        if not _matches_name_policy(p, name_policy):
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


def _check_core_surface_files(
    files: list[Path],
    unexpected_marker: list[str],
    invalid_name: list[str],
    unexpected_core_impl_files: list[str],
) -> None:
    for p in files:
        rel = str(p.relative_to(ROOT))
        txt = p.read_text(encoding="utf-8", errors="ignore")
        if not _matches_name_policy(p, "plain"):
            invalid_name.append(rel)
        if MARKER in txt:
            unexpected_marker.append(rel)
        if p.suffix == ".cpp":
            unexpected_core_impl_files.append(rel)


def _check_direct_native_core_includes(
    files: list[Path],
    direct_native_core_include_violations: list[str],
    *,
    core_dir: Path,
) -> None:
    for p in files:
        txt = p.read_text(encoding="utf-8", errors="ignore")
        rel = str(p.relative_to(ROOT))
        includes = DIRECT_NATIVE_CORE_INCLUDE_RE.findall(txt)
        if len(includes) == 0:
            continue
        is_core_forwarder = p.parent == core_dir and p.suffix == ".h"
        if is_core_forwarder:
            continue
        for include_txt in includes:
            direct_native_core_include_violations.append(f"{rel} -> {include_txt}")


def main() -> int:
    builtin_dir = _runtime_cpp_path("built_in")
    core_dir = _runtime_cpp_path("core")
    generated_dir = _runtime_cpp_path("generated")
    generated_core_dir = generated_dir / "core"
    native_dir = _runtime_cpp_path("native")
    native_core_dir = native_dir / "core"
    pytra_dir = _runtime_cpp_path("pytra")
    std_dir = _runtime_cpp_path("std")
    utils_dir = _runtime_cpp_path("utils")
    py_runtime_header = _runtime_cpp_path("native", "core", "py_runtime.h")
    if not py_runtime_header.exists():
        py_runtime_header = _runtime_cpp_path("core", "py_runtime.h")

    builtin_files = _scan_targets(builtin_dir)
    core_files = _scan_targets(core_dir)
    generated_files, unexpected_generated_bucket_files = _scan_bucketed_targets(
        generated_dir, {"built_in", "std", "utils", "compiler", "core"}
    )
    native_files, unexpected_native_bucket_files = _scan_bucketed_targets(
        native_dir, {"built_in", "std", "utils", "compiler", "core"}
    )
    pytra_files, unexpected_pytra_bucket_files = _scan_bucketed_targets(
        pytra_dir, {"built_in", "std", "utils", "compiler"}
    )
    std_files = _scan_targets(std_dir)
    utils_files = _scan_targets(utils_dir)
    legacy_module_files = builtin_files + std_files + utils_files
    generated_core_files = [
        p for p in generated_files if p.relative_to(generated_dir).parts[0] == "core"
    ]
    generated_module_files = [p for p in generated_files if p not in generated_core_files]
    native_core_files = [p for p in native_files if p.relative_to(native_dir).parts[0] == "core"]
    native_module_files = [p for p in native_files if p not in native_core_files]

    if not core_files:
        print(f"[FAIL] no C++ source/header files under: {core_dir.relative_to(ROOT)}")
        return 1
    if not generated_module_files and not native_module_files and not pytra_files:
        print("[FAIL] no module runtime files found under generated/native/pytra layout")
        return 1

    missing_marker: list[str] = []
    unexpected_marker: list[str] = []
    invalid_name: list[str] = []
    unexpected_bucket_files = [
        str(p.relative_to(ROOT))
        for p in (
            unexpected_generated_bucket_files
            + unexpected_native_bucket_files
            + unexpected_pytra_bucket_files
        )
    ]
    unexpected_core_impl_files: list[str] = []
    banned_runtime_duplicates: list[str] = []
    direct_native_core_include_violations: list[str] = []
    missing_core_lane_dirs: list[str] = []
    unexpected_legacy_module_files = [str(p.relative_to(ROOT)) for p in legacy_module_files]
    runtime_tree_files = _scan_targets(_runtime_cpp_path())

    for path in (generated_core_dir, native_core_dir):
        if not path.is_dir():
            missing_core_lane_dirs.append(str(path.relative_to(ROOT)))

    _check_generated_files(
        generated_module_files, missing_marker, invalid_name, name_policy="plain"
    )
    _check_generated_files(generated_core_files, missing_marker, invalid_name, name_policy="plain")
    _check_core_surface_files(
        core_files,
        unexpected_marker,
        invalid_name,
        unexpected_core_impl_files,
    )
    _check_handwritten_files(
        native_module_files,
        unexpected_marker,
        invalid_name,
        name_policy="plain",
    )
    _check_handwritten_files(
        native_core_files,
        unexpected_marker,
        invalid_name,
        name_policy="plain",
    )
    _check_public_shim_files(pytra_files, missing_marker, invalid_name)
    _check_direct_native_core_includes(
        runtime_tree_files,
        direct_native_core_include_violations,
        core_dir=core_dir,
    )

    if py_runtime_header.exists():
        py_runtime_txt = py_runtime_header.read_text(encoding="utf-8", errors="ignore")
        for pattern, reason in BANNED_PY_RUNTIME_PATTERNS.items():
            if pattern in py_runtime_txt:
                banned_runtime_duplicates.append(f"{pattern} :: {reason}")
        for pattern, reason in BANNED_PY_RUNTIME_INCLUDE_PATTERNS.items():
            if pattern in py_runtime_txt:
                banned_runtime_duplicates.append(f"{pattern} :: {reason}")

    if (
        missing_marker
        or unexpected_marker
        or invalid_name
        or unexpected_bucket_files
        or unexpected_core_impl_files
        or banned_runtime_duplicates
        or direct_native_core_include_violations
        or missing_core_lane_dirs
        or unexpected_legacy_module_files
    ):
        print("[FAIL] runtime cpp layout guard failed")
        print(
            "  scanned: "
            + f"legacy_module={len(legacy_module_files)} files, "
            + f"generated_module={len(generated_module_files)} files, "
            + f"generated_core={len(generated_core_files)} files, "
            + f"native_module={len(native_module_files)} files, "
            + f"native_core={len(native_core_files)} files, "
            + f"pytra={len(pytra_files)} files, "
            + f"core={len(core_files)} files, "
            + f"std={len(std_files)} files"
        )
        if unexpected_legacy_module_files:
            print("  legacy-closed module dirs still contain source/header files:")
            for item in unexpected_legacy_module_files:
                print(f"    - {item}")
        if missing_marker:
            print("  generated files missing marker:")
            for item in missing_marker:
                print(f"    - {item}")
        if unexpected_marker:
            print("  handwritten files containing marker:")
            for item in unexpected_marker:
                print(f"    - {item}")
        if unexpected_bucket_files:
            print("  ownership roots contain unsupported top-level buckets:")
            for item in unexpected_bucket_files:
                print(f"    - {item}")
        if unexpected_core_impl_files:
            print("  core compatibility surface unexpectedly contains implementation sources:")
            for item in unexpected_core_impl_files:
                print(f"    - {item}")
        if invalid_name:
            print("  files violating runtime naming policy:")
            for item in invalid_name:
                print(f"    - {item}")
        if banned_runtime_duplicates:
            print("  py_runtime core header still contains duplicated high-level runtime bodies:")
            for item in banned_runtime_duplicates:
                print(f"    - {item}")
        if direct_native_core_include_violations:
            print("  non-forwarder runtime files directly include native/core headers:")
            for item in direct_native_core_include_violations:
                print(f"    - {item}")
        if missing_core_lane_dirs:
            print("  required core ownership directories are missing:")
            for item in missing_core_lane_dirs:
                print(f"    - {item}")
        return 1

    print("[OK] runtime cpp layout guard passed")
    print(f"  legacy-closed module files: {len(legacy_module_files)}")
    print(f"  generated module dir files with marker: {len(generated_module_files)}")
    print(f"  generated core dir files with marker: {len(generated_core_files)}")
    print(f"  public shim files with marker: {len(pytra_files)}")
    print(f"  native module dir files without marker: {len(native_module_files)}")
    print(f"  native core dir files without marker: {len(native_core_files)}")
    print(f"  core surface files without marker: {len(core_files)}")
    print(f"  legacy-closed std files: {len(std_files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
