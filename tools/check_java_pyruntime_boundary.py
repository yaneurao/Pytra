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
    "core_utils_png.write_rgb_png": re.compile(r"\bstatic\s+[^\n;]*\bwrite_rgb_png\s*\("),
    "core_utils_gif.save_gif": re.compile(r"\bstatic\s+[^\n;]*\bsave_gif\s*\("),
    "core_utils_gif.grayscale_palette": re.compile(r"\bstatic\s+[^\n;]*\bgrayscale_palette\s*\("),
    "core_std_json.pyJsonDumps": re.compile(r"\bstatic\s+[^\n;]*\bpyJsonDumps\s*\("),
    "core_std_json.pyJsonLoads": re.compile(r"\bstatic\s+[^\n;]*\bpyJsonLoads\s*\("),
    "core_std_json.jsonStringify": re.compile(r"\bstatic\s+[^\n;]*\bjsonStringify\s*\("),
    "core_std_json.jsonEscapeString": re.compile(r"\bstatic\s+[^\n;]*\bjsonEscapeString\s*\("),
    "core_std_json.JsonParser": re.compile(r"\bclass\s+JsonParser\b"),
    "legacy_image_wrapper.pyWriteRGBPNG": re.compile(r"\bstatic\s+[^\n;]*\bpyWriteRGBPNG\s*\("),
    "legacy_image_wrapper.pySaveGif": re.compile(r"\bstatic\s+[^\n;]*\bpySaveGif\s*\("),
    "legacy_image_wrapper.pyGrayscalePalette": re.compile(r"\bstatic\s+[^\n;]*\bpyGrayscalePalette\s*\("),
    "core_std_time.pyPerfCounter": re.compile(r"\bstatic\s+[^\n;]*\bpyPerfCounter\s*\("),
    "core_std_math.pyMathSqrt": re.compile(r"\bstatic\s+[^\n;]*\bpyMathSqrt\s*\("),
    "core_std_math.pyMathSin": re.compile(r"\bstatic\s+[^\n;]*\bpyMathSin\s*\("),
    "core_std_math.pyMathCos": re.compile(r"\bstatic\s+[^\n;]*\bpyMathCos\s*\("),
    "core_std_math.pyMathTan": re.compile(r"\bstatic\s+[^\n;]*\bpyMathTan\s*\("),
    "core_std_math.pyMathExp": re.compile(r"\bstatic\s+[^\n;]*\bpyMathExp\s*\("),
    "core_std_math.pyMathLog": re.compile(r"\bstatic\s+[^\n;]*\bpyMathLog\s*\("),
    "core_std_math.pyMathLog10": re.compile(r"\bstatic\s+[^\n;]*\bpyMathLog10\s*\("),
    "core_std_math.pyMathFabs": re.compile(r"\bstatic\s+[^\n;]*\bpyMathFabs\s*\("),
    "core_std_math.pyMathFloor": re.compile(r"\bstatic\s+[^\n;]*\bpyMathFloor\s*\("),
    "core_std_math.pyMathCeil": re.compile(r"\bstatic\s+[^\n;]*\bpyMathCeil\s*\("),
    "core_std_math.pyMathPow": re.compile(r"\bstatic\s+[^\n;]*\bpyMathPow\s*\("),
    "core_std_math.pyMathPi": re.compile(r"\bstatic\s+[^\n;]*\bpyMathPi\s*\("),
    "core_std_math.pyMathE": re.compile(r"\bstatic\s+[^\n;]*\bpyMathE\s*\("),
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
