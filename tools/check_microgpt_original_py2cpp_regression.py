#!/usr/bin/env python3
"""Regression guard for py2cpp against original microgpt source (P3-MSP-09)."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PY2CPP = ROOT / "src" / "py2cpp.py"
DEFAULT_SOURCE = ROOT / "materials" / "refs" / "microgpt" / "microgpt-20260222.py"

KNOWN_STAGES = ("A", "B", "C", "D", "E", "F")
KNOWN_PHASES = ("transpile", "syntax-check", "transpile-only", "transpile+syntax-check")

STAGE_LABELS = {
    "A": "parser.untyped-parameter",
    "B": "parser.inline-class-method",
    "C": "parser.top-level-or-lower-gap",
    "D": "east.range-in-comprehension",
    "E": "emitter.object-receiver-collapse",
    "F": "runtime-or-compile-compat",
    "SUCCESS": "transpile-and-syntax-check-passed",
}

STAGE_OWNERS = {
    "A": "parser",
    "B": "parser",
    "C": "lower",
    "D": "lower",
    "E": "lower",
    "F": "runtime",
    "SUCCESS": "success",
}


def _run(cmd: list[str]) -> tuple[int, str]:
    cp = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    msg = cp.stderr.strip() or cp.stdout.strip()
    return cp.returncode, msg


def _diagnostic_line(msg: str) -> str:
    if msg == "":
        return ""
    lines: list[str] = []
    for raw in msg.splitlines():
        line = raw.strip()
        if line != "":
            lines.append(line)
    if len(lines) == 0:
        return ""
    for line in lines:
        low = line.lower()
        if "unsupported_syntax:" in low:
            return line
        if "requires type annotation for parameter" in low:
            return line
        if "unexpected raw range call in east" in low:
            return line
        if "object receiver" in low:
            return line
    for line in lines:
        low = line.lower()
        if low == "error: this syntax is not implemented yet.":
            continue
        if low.startswith("[not_implemented]"):
            continue
        return line
    return lines[0]


def _classify_parser_failure(msg: str) -> str:
    low = msg.lower()
    if "requires type annotation for parameter" in low:
        return "A"
    if "unexpected raw range call in east" in low:
        return "D"
    if "object receiver" in low:
        return "E"
    if "unsupported_syntax" in low and "class" in low:
        return "B"
    if (
        "list.index" in low
        or "random.shuffle" in low
        or "open(" in low
        or "no matching function" in low
        or "not declared in this scope" in low
    ):
        return "F"
    if "unsupported_syntax" in low or "parse" in low:
        return "C"
    return "UNKNOWN"


def _classify_compile_failure(msg: str) -> str:
    # Once transpile succeeds, remaining blockers for this task group are treated
    # as runtime/std or C++ compile compatibility issues (stage F).
    if msg.strip() == "":
        return "F"
    return "F"


def _owner_for_stage(stage: str) -> str:
    return STAGE_OWNERS.get(stage, "unknown")


def _matches_expectation(expect: str, stage: str) -> bool:
    if expect == "any-known":
        return stage in KNOWN_STAGES or stage == "SUCCESS"
    if expect == "success":
        return stage == "SUCCESS"
    return stage == expect


def _matches_phase_expectation(expect_phase: str, actual_phase: str) -> bool:
    if expect_phase == "any":
        return True
    return expect_phase == actual_phase


def _build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="check regression stage for original materials/refs/microgpt/microgpt-20260222.py"
    )
    ap.add_argument(
        "--source",
        default=str(DEFAULT_SOURCE),
        help="python source to transpile (default: materials/refs/microgpt/microgpt-20260222.py)",
    )
    ap.add_argument(
        "--expect-stage",
        default="F",
        choices=["any-known", "success", "A", "B", "C", "D", "E", "F"],
        help="expected stage (default: F for current baseline)",
    )
    ap.add_argument(
        "--expect-phase",
        default="syntax-check",
        choices=["any", "transpile", "syntax-check", "transpile-only", "transpile+syntax-check"],
        help="expected phase (default: syntax-check for current baseline)",
    )
    ap.add_argument(
        "--skip-syntax-check",
        action="store_true",
        help="skip g++ -fsyntax-only even when transpile succeeds",
    )
    ap.add_argument("--verbose", action="store_true", help="print executed commands")
    return ap


def main() -> int:
    args = _build_parser().parse_args()
    src = Path(args.source)
    if not src.is_absolute():
        src = ROOT / src
    if not src.exists():
        print(f"missing source: {src}")
        return 2

    with tempfile.TemporaryDirectory() as tmpdir:
        out_cpp = Path(tmpdir) / "microgpt.original.cpp"
        transpile_cmd = ["python3", str(PY2CPP), str(src), "-o", str(out_cpp)]
        if args.verbose:
            print("CMD", " ".join(transpile_cmd))
        code, msg = _run(transpile_cmd)
        if code != 0:
            stage = _classify_parser_failure(msg)
            first = _diagnostic_line(msg)
            phase = "transpile"
            print("result=fail phase=transpile")
            print(f"stage={stage} label={STAGE_LABELS.get(stage, 'unknown')}")
            print(f"owner={_owner_for_stage(stage)}")
            if first != "":
                print(f"error={first}")
            if stage == "UNKNOWN":
                print("unexpected failure signature; update stage classifier.")
                return 1
            if not _matches_expectation(args.expect_stage, stage):
                print(f"expectation_mismatch expected={args.expect_stage} actual={stage}")
                return 1
            if not _matches_phase_expectation(args.expect_phase, phase):
                print(f"phase_mismatch expected={args.expect_phase} actual={phase}")
                return 1
            return 0

        if args.skip_syntax_check:
            stage = "SUCCESS"
            phase = "transpile-only"
            print("result=ok phase=transpile-only")
            print(f"stage={stage} label={STAGE_LABELS[stage]}")
            print(f"owner={_owner_for_stage(stage)}")
            if not _matches_expectation(args.expect_stage, stage):
                print(f"expectation_mismatch expected={args.expect_stage} actual={stage}")
                return 1
            if not _matches_phase_expectation(args.expect_phase, phase):
                print(f"phase_mismatch expected={args.expect_phase} actual={phase}")
                return 1
            return 0

        compile_cmd = [
            "g++",
            "-std=c++20",
            "-I",
            "src",
            "-I",
            "src/runtime/cpp",
            "-fsyntax-only",
            str(out_cpp),
        ]
        if args.verbose:
            print("CMD", " ".join(compile_cmd))
        code, msg = _run(compile_cmd)
        if code != 0:
            stage = _classify_compile_failure(msg)
            first = _diagnostic_line(msg)
            phase = "syntax-check"
            print("result=fail phase=syntax-check")
            print(f"stage={stage} label={STAGE_LABELS.get(stage, 'unknown')}")
            print(f"owner={_owner_for_stage(stage)}")
            if first != "":
                print(f"error={first}")
            if not _matches_expectation(args.expect_stage, stage):
                print(f"expectation_mismatch expected={args.expect_stage} actual={stage}")
                return 1
            if not _matches_phase_expectation(args.expect_phase, phase):
                print(f"phase_mismatch expected={args.expect_phase} actual={phase}")
                return 1
            return 0

        stage = "SUCCESS"
        phase = "transpile+syntax-check"
        print("result=ok phase=transpile+syntax-check")
        print(f"stage={stage} label={STAGE_LABELS[stage]}")
        print(f"owner={_owner_for_stage(stage)}")
        if not _matches_expectation(args.expect_stage, stage):
            print(f"expectation_mismatch expected={args.expect_stage} actual={stage}")
            return 1
        if not _matches_phase_expectation(args.expect_phase, phase):
            print(f"phase_mismatch expected={args.expect_phase} actual={phase}")
            return 1
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
