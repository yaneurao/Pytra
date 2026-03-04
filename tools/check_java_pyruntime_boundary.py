#!/usr/bin/env python3
"""Guard Java PyRuntime core boundary (phase-1).

This check prevents re-introducing legacy helper wrappers that were removed
from `pytra-core` and must not come back.
"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "src/runtime/java/pytra-core/built_in/PyRuntime.java"

FORBIDDEN: dict[str, re.Pattern[str]] = {
    "legacy_image_wrapper.pyWriteRGBPNG": re.compile(r"\bstatic\s+[^\n;]*\bpyWriteRGBPNG\s*\("),
    "legacy_image_wrapper.pySaveGif": re.compile(r"\bstatic\s+[^\n;]*\bpySaveGif\s*\("),
    "legacy_image_wrapper.pyGrayscalePalette": re.compile(r"\bstatic\s+[^\n;]*\bpyGrayscalePalette\s*\("),
}


def main() -> int:
    if not TARGET.exists():
        print("[FAIL] missing target file: " + str(TARGET.relative_to(ROOT)))
        return 1
    text = TARGET.read_text(encoding="utf-8", errors="ignore")
    violations: list[str] = []
    rel = str(TARGET.relative_to(ROOT)).replace("\\", "/")
    for label, pat in FORBIDDEN.items():
        if pat.search(text):
            violations.append(f"[{label}] {rel}")

    if len(violations) > 0:
        print("[FAIL] Java PyRuntime boundary guard failed")
        print("  forbidden symbols detected in pytra-core:")
        for item in violations:
            print("    - " + item)
        print("  fix: keep image helper entrypoints in canonical names only")
        return 1

    print("[OK] Java PyRuntime boundary guard passed")
    print("  checked symbols: " + ", ".join(FORBIDDEN.keys()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
