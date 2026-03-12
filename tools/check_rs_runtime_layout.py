#!/usr/bin/env python3
"""Guard Rust runtime layout state.

Policy:
- Canonical handwritten runtime for Rust lives under `src/runtime/rs/native/**`.
- `src/runtime/rs/pytra/**` may remain only as a compatibility lane and must not be
  treated as the ownership source of truth.
- `src/rs_module/` is deprecated and must not contain source files.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEGACY_DIR = ROOT / "src" / "rs_module"
CANONICAL_RUNTIME = ROOT / "src" / "runtime" / "rs" / "native" / "built_in" / "py_runtime.rs"
COMPAT_RUNTIME = ROOT / "src" / "runtime" / "rs" / "pytra" / "built_in" / "py_runtime.rs"


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
    if not CANONICAL_RUNTIME.exists():
        print("[FAIL] missing canonical Rust runtime file")
        print(f"  - {CANONICAL_RUNTIME.relative_to(ROOT)}")
        return 1

    legacy_files = _collect_files(LEGACY_DIR)
    if len(legacy_files) > 0:
        print("[FAIL] deprecated src/rs_module still contains files")
        print("  actual:")
        for path in legacy_files:
            print(f"    - {path.relative_to(ROOT)}")
        return 1

    print("[OK] rs runtime layout guard passed")
    print("  legacy: src/rs_module has no source files")
    print(f"  canonical runtime: {CANONICAL_RUNTIME.relative_to(ROOT)}")
    if COMPAT_RUNTIME.exists():
        print(f"  compat runtime: {COMPAT_RUNTIME.relative_to(ROOT)}")
    else:
        print("  compat runtime: absent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
