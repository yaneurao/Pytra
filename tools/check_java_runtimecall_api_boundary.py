#!/usr/bin/env python3
"""Guard Java emitter runtime-call API boundary.

Policy:
- runtime-call rendering helpers in `java_native_emitter.py` must not accept
  raw `expr` and must not pull callee names from raw call nodes.
- call-site specific extraction is allowed only in `_resolved_call_binding`.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JAVA_EMITTER = ROOT / "src" / "backends" / "java" / "emitter" / "java_native_emitter.py"

BANNED_MARKERS = (
    "_render_call_via_runtime_call(expr,",
    "_render_resolved_runtime_call(expr,",
    "_call_name(expr).strip()",
)


def main() -> int:
    if not JAVA_EMITTER.exists():
        print(f"[FAIL] missing target file: {JAVA_EMITTER.relative_to(ROOT)}")
        return 1
    src = JAVA_EMITTER.read_text(encoding="utf-8")
    bad: list[str] = []
    for marker in BANNED_MARKERS:
        if marker in src:
            bad.append(marker)
    if len(bad) > 0:
        print("[FAIL] java runtime-call API boundary violation(s):")
        for marker in bad:
            print(f"  - {marker}")
        return 1
    print("[OK] java runtime-call API boundary guard passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
