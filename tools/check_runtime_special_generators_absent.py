#!/usr/bin/env python3
"""Fail if legacy per-language runtime generator scripts are reintroduced."""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
LEGACY_PATTERN = "gen_*_from_canonical.py"


def find_legacy_generators() -> list[Path]:
    paths = sorted(TOOLS_DIR.glob(LEGACY_PATTERN), key=lambda p: str(p))
    return [p for p in paths if p.is_file()]


def main() -> int:
    _ = argparse.ArgumentParser(description="check legacy runtime generator scripts are absent")
    findings = find_legacy_generators()
    if len(findings) == 0:
        print("[OK] no legacy runtime generator scripts found")
        return 0

    print("[FAIL] legacy runtime generator scripts must not exist:")
    for path in findings:
        print("  - " + str(path.relative_to(ROOT)).replace("\\", "/"))
    print("use tools/gen_runtime_from_manifest.py instead")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
