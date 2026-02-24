#!/usr/bin/env python3
"""Guard Rust runtime layout state.

Policy:
- Runtime implementation must live under `src/runtime/rs/pytra/`.
- `src/rs_module/` is deprecated and must not contain source files.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEGACY_DIR = ROOT / "src" / "rs_module"
NEW_RUNTIME = ROOT / "src" / "runtime" / "rs" / "pytra" / "built_in" / "py_runtime.rs"


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

    legacy_files = _collect_files(LEGACY_DIR)
    if len(legacy_files) > 0:
        print("[FAIL] deprecated src/rs_module still contains files")
        print("  actual:")
        for path in legacy_files:
            print(f"    - {path.relative_to(ROOT)}")
        return 1

    print("[OK] rs runtime layout guard passed")
    print("  legacy: src/rs_module has no source files")
    print(f"  runtime: {NEW_RUNTIME.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
