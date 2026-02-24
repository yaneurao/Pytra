#!/usr/bin/env python3
"""Guard Rust runtime layout migration state.

Policy:
- Runtime implementation must live under `src/runtime/rs/pytra/`.
- `src/rs_module/py_runtime.rs` is allowed only as a compatibility shim.
- `src/rs_module/` must not grow additional runtime source files.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEGACY_DIR = ROOT / "src" / "rs_module"
LEGACY_SHIM = LEGACY_DIR / "py_runtime.rs"
NEW_RUNTIME = ROOT / "src" / "runtime" / "rs" / "pytra" / "built_in" / "py_runtime.rs"
SHIM_INCLUDE_LINE = 'include!("../runtime/rs/pytra/built_in/py_runtime.rs");'


def _collect_files(base: Path) -> list[Path]:
    if not base.exists():
        return []
    out: list[Path] = []
    for path in base.rglob("*"):
        if path.is_file():
            out.append(path)
    out.sort()
    return out


def main() -> int:
    if not NEW_RUNTIME.exists():
        print("[FAIL] missing new Rust runtime file")
        print(f"  - {NEW_RUNTIME.relative_to(ROOT)}")
        return 1

    if not LEGACY_SHIM.exists():
        print("[FAIL] missing legacy compatibility shim")
        print(f"  - {LEGACY_SHIM.relative_to(ROOT)}")
        return 1

    legacy_files = _collect_files(LEGACY_DIR)
    expected = [LEGACY_SHIM]
    if legacy_files != expected:
        print("[FAIL] unexpected files under src/rs_module")
        print("  expected only:")
        print(f"    - {LEGACY_SHIM.relative_to(ROOT)}")
        print("  actual:")
        for path in legacy_files:
            print(f"    - {path.relative_to(ROOT)}")
        return 1

    shim_text = LEGACY_SHIM.read_text(encoding="utf-8")
    if SHIM_INCLUDE_LINE not in shim_text:
        print("[FAIL] legacy shim does not include new runtime path")
        print(f"  expected line: {SHIM_INCLUDE_LINE}")
        return 1

    print("[OK] rs runtime layout guard passed")
    print(f"  shim: {LEGACY_SHIM.relative_to(ROOT)}")
    print(f"  runtime: {NEW_RUNTIME.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
