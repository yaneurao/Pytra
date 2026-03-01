#!/usr/bin/env python3
"""Check py2lua transpile success for fixtures and sample files."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PY2LUA = ROOT / "src" / "py2lua.py"

DEFAULT_EXPECTED_FAILS = {
    "test/fixtures/collections/comprehension.py",
    "test/fixtures/collections/comprehension_dict_set.py",
    "test/fixtures/collections/comprehension_filter.py",
    "test/fixtures/collections/comprehension_if_chain.py",
    "test/fixtures/collections/comprehension_ifexp.py",
    "test/fixtures/collections/comprehension_nested.py",
    "test/fixtures/collections/comprehension_range_step.py",
    "test/fixtures/collections/comprehension_range_step_like.py",
    "test/fixtures/collections/in_membership.py",
    "test/fixtures/collections/slice_basic.py",
    "test/fixtures/control/finally.py",
    "test/fixtures/control/try_raise.py",
    "test/fixtures/control/yield_generator_min.py",
    "test/fixtures/core/lambda_as_arg.py",
    "test/fixtures/core/lambda_basic.py",
    "test/fixtures/core/lambda_capture_multiargs.py",
    "test/fixtures/core/lambda_ifexp.py",
    "test/fixtures/core/lambda_immediate.py",
    "test/fixtures/core/lambda_local_state.py",
    "test/fixtures/core/tuple_assign.py",
    "test/fixtures/signature/ng_kwargs.py",
    "test/fixtures/signature/ng_object_receiver.py",
    "test/fixtures/signature/ng_posonly.py",
    "test/fixtures/signature/ng_varargs.py",
    "test/fixtures/signature/ok_generator_tuple_target.py",
    "test/fixtures/signature/ok_lambda_default.py",
    "test/fixtures/signature/ok_list_concat_comp.py",
    "test/fixtures/signature/ok_multi_for_comp.py",
    "test/fixtures/signature/ok_top_level_tuple_assign.py",
    "test/fixtures/signature/ok_tuple_of_list_comp.py",
    "test/fixtures/stdlib/argparse_extended.py",
    "test/fixtures/stdlib/os_glob_extended.py",
    "test/fixtures/strings/str_slice.py",
    "test/fixtures/typing/any_basic.py",
    "test/fixtures/typing/any_class_alias.py",
    "test/fixtures/typing/any_dict_items.py",
    "test/fixtures/typing/any_list_mixed.py",
    "test/fixtures/typing/any_none.py",
    "test/fixtures/typing/bytearray_basic.py",
}

STAGE2_REMOVED_FRAGMENT = "--east-stage 2 is no longer supported; use EAST3 (default)."


def _run_one(src: Path, out: Path) -> tuple[bool, str]:
    cp = subprocess.run(
        ["python3", str(PY2LUA), str(src), "-o", str(out)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if cp.returncode == 0:
        return True, ""
    msg = cp.stderr.strip() or cp.stdout.strip()
    first = msg.splitlines()[0] if msg else "unknown error"
    return False, first


def _run_one_stage2_must_fail(src: Path, out: Path) -> tuple[bool, str]:
    cp = subprocess.run(
        ["python3", str(PY2LUA), str(src), "--east-stage", "2", "-o", str(out)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if cp.returncode == 0:
        return False, "unexpected success for --east-stage 2"
    stderr = cp.stderr.strip()
    if STAGE2_REMOVED_FRAGMENT in stderr:
        return True, ""
    first = stderr.splitlines()[0] if stderr else "missing stderr message"
    return False, f"unexpected stage2 error message: {first}"


def main() -> int:
    ap = argparse.ArgumentParser(description="check py2lua transpile success for fixtures/sample")
    ap.add_argument("--include-expected-failures", action="store_true", help="do not skip known expected failures")
    ap.add_argument("--verbose", action="store_true", help="print passing files")
    args = ap.parse_args()

    fixture_files = sorted((ROOT / "test" / "fixtures").rglob("*.py"))
    sample_files = sorted((ROOT / "sample" / "py").glob("*.py"))
    expected_fails = set() if args.include_expected_failures else DEFAULT_EXPECTED_FAILS

    fails: list[tuple[str, str]] = []
    skipped = 0
    ok = 0
    total = 0
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "out.lua"
        for src in fixture_files + sample_files:
            rel = str(src.relative_to(ROOT))
            if rel in expected_fails:
                skipped += 1
                continue
            total += 1
            good, msg = _run_one(src, out)
            if good:
                ok += 1
                if args.verbose:
                    print("OK", rel)
            else:
                fails.append((rel, msg))

        stage2_probe: Path | None = None
        if len(sample_files) > 0:
            stage2_probe = sample_files[0]
        elif len(fixture_files) > 0:
            stage2_probe = fixture_files[0]
        if stage2_probe is not None:
            total += 1
            good, msg = _run_one_stage2_must_fail(stage2_probe, out)
            rel = str(stage2_probe.relative_to(ROOT))
            if good:
                ok += 1
                if args.verbose:
                    print("OK", rel, "[stage2 rejected]")
            else:
                fails.append((rel + " [stage2 rejected]", msg))

    print(f"checked={total} ok={ok} fail={len(fails)} skipped={skipped}")
    if fails:
        for rel, msg in fails:
            print(f"FAIL {rel}: {msg}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
