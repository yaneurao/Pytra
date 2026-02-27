#!/usr/bin/env python3
"""Fail when multilang quality metrics regress versus recorded baseline."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import measure_multilang_quality as mmq  # noqa: E402


@dataclass
class Row:
    lang: str
    files: int
    lines: int
    mut: int
    paren: int
    cast: int
    clone: int
    imports: int
    unused_import_est: int


PREVIEW_MARKERS = {
    "go": "TODO: 専用 GoEmitter 実装へ段階移行する。",
    "kotlin": "TODO: 専用 KotlinEmitter 実装へ段階移行する。",
    "swift": "TODO: 専用 SwiftEmitter 実装へ段階移行する。",
}


def _parse_int_cell(text: str) -> int:
    t = text.strip()
    if not re.fullmatch(r"-?\d+", t):
        raise ValueError(f"not int: {text!r}")
    return int(t)


def _parse_baseline_rows(path: Path) -> dict[str, Row]:
    if not path.exists():
        raise RuntimeError(f"missing baseline file: {path}")
    lines = path.read_text(encoding="utf-8").splitlines()
    header = "| lang | files | lines | mut | paren | cast | clone | imports | unused_import_est |"
    start = -1
    i = 0
    while i < len(lines):
        if lines[i].strip() == header:
            start = i
            break
        i += 1
    if start < 0:
        raise RuntimeError("baseline table header not found")
    rows: dict[str, Row] = {}
    i = start + 2
    while i < len(lines):
        s = lines[i].strip()
        if not s.startswith("|"):
            break
        parts = [p.strip() for p in s.split("|")[1:-1]]
        if len(parts) != 9:
            break
        lang = parts[0]
        row = Row(
            lang=lang,
            files=_parse_int_cell(parts[1]),
            lines=_parse_int_cell(parts[2]),
            mut=_parse_int_cell(parts[3]),
            paren=_parse_int_cell(parts[4]),
            cast=_parse_int_cell(parts[5]),
            clone=_parse_int_cell(parts[6]),
            imports=_parse_int_cell(parts[7]),
            unused_import_est=_parse_int_cell(parts[8]),
        )
        rows[lang] = row
        i += 1
    if len(rows) == 0:
        raise RuntimeError("baseline table rows not found")
    return rows


def _measure_current() -> dict[str, Row]:
    out: dict[str, Row] = {}
    for cfg in mmq.LANGS:
        m = mmq._measure_lang(cfg)
        out[cfg.name] = Row(
            lang=cfg.name,
            files=m.files,
            lines=m.lines,
            mut=m.mut_count,
            paren=m.paren_count,
            cast=m.cast_count,
            clone=m.clone_count,
            imports=m.import_count,
            unused_import_est=m.unused_import_est,
        )
    return out


def _check_preview_markers() -> list[str]:
    failures: list[str] = []
    sample_dir = ROOT / "sample"
    for lang, marker in PREVIEW_MARKERS.items():
        ext = {
            "go": ".go",
            "kotlin": ".kt",
            "swift": ".swift",
        }[lang]
        for path in sorted((sample_dir / lang).glob(f"*{ext}")):
            text = path.read_text(encoding="utf-8")
            if marker in text:
                rel = str(path.relative_to(ROOT))
                failures.append(f"{lang}: {rel} still contains preview marker")
    return failures


def main() -> int:
    ap = argparse.ArgumentParser(description="check multilang quality regression against baseline")
    ap.add_argument(
        "--baseline",
        default="docs/ja/plans/p1-multilang-output-quality-baseline.md",
        help="baseline markdown path",
    )
    ap.add_argument(
        "--allow-increase",
        type=int,
        default=0,
        help="allow this many count increase per metric",
    )
    args = ap.parse_args()

    marker_failures = _check_preview_markers()
    if marker_failures:
        print("[FAIL] preview marker check")
        for line in marker_failures:
            print("  - " + line)
        return 1

    baseline_path = ROOT / args.baseline
    try:
        baseline = _parse_baseline_rows(baseline_path)
    except Exception as exc:
        print(f"[FAIL] baseline parse error: {exc}")
        return 2

    current = _measure_current()
    metrics = ["mut", "paren", "cast", "clone", "imports", "unused_import_est"]
    failures: list[str] = []
    checks = 0
    for cfg in mmq.LANGS:
        lang = cfg.name
        if lang == "cpp":
            continue
        if lang not in baseline:
            failures.append(f"{lang}: missing baseline row")
            continue
        if lang not in current:
            failures.append(f"{lang}: missing current row")
            continue
        b = baseline[lang]
        c = current[lang]
        for key in metrics:
            checks += 1
            bv = int(getattr(b, key))
            cv = int(getattr(c, key))
            if cv > bv + int(args.allow_increase):
                failures.append(f"{lang}.{key}: {bv} -> {cv}")

    if len(failures) > 0:
        print("[FAIL] multilang quality regression")
        for line in failures:
            print("  - " + line)
        return 1

    print(f"[OK] multilang quality regression check passed ({checks} comparisons)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
