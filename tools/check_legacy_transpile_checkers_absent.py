#!/usr/bin/env python3
"""Fail if legacy per-target transpile checker scripts are reintroduced."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _find_legacy_checker_scripts(root: Path) -> list[str]:
    tools_dir = root / "tools"
    out: list[str] = []
    for path in sorted(tools_dir.glob("check_py2*_transpile.py")):
        if path.name == "check_py2x_transpile.py":
            continue
        out.append(str(path.relative_to(root)).replace("\\", "/"))
    return out


def main() -> int:
    legacy = _find_legacy_checker_scripts(ROOT)
    if len(legacy) == 0:
        print("[OK] no legacy check_py2*_transpile.py scripts found")
        return 0
    for rel in legacy:
        print("FAIL legacy checker script present: " + rel)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
