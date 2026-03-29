#!/usr/bin/env python3
"""Fast runtime parity check using in-memory pipeline (no CLI subprocess for transpile).

This is the high-speed variant of runtime_parity_check.py.  The transpile stage
calls toolchain2 Python APIs directly instead of spawning ``python pytra-cli.py``
subprocesses, eliminating per-case process startup and intermediate file I/O.

Compile + run still uses subprocesses (g++, go run, etc.).

Usage:
    python3 tools/runtime_parity_check_fast.py --targets cpp --category oop
    python3 tools/runtime_parity_check_fast.py --targets go
    python3 tools/runtime_parity_check_fast.py --case-root sample --all-samples --targets cpp
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import time
import zlib
from dataclasses import dataclass
from pathlib import Path

# --- repo bootstrap ---
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

# --- toolchain2 imports (in-memory pipeline) ---
from toolchain2.common.jv import deep_copy_json  # type: ignore
from toolchain2.compile.lower import lower_east2_to_east3  # type: ignore
from toolchain2.emit.cpp.emitter import emit_cpp_module  # type: ignore
from toolchain2.emit.cpp.header_gen import build_cpp_header_from_east3  # type: ignore
from toolchain2.emit.cpp.runtime_bundle import emit_runtime_module_artifacts  # type: ignore
from toolchain2.emit.go.emitter import emit_go_module  # type: ignore
from toolchain2.link.linker import link_modules  # type: ignore
from toolchain2.emit.cpp.runtime_paths import runtime_rel_tail_for_module  # type: ignore
from toolchain2.optimize.optimizer import optimize_east3_document  # type: ignore
from toolchain2.parse.py.parse_python import parse_python_file  # type: ignore
from toolchain2.resolve.py.builtin_registry import load_builtin_registry  # type: ignore
from toolchain2.resolve.py.resolver import resolve_east1_to_east2  # type: ignore

# --- reuse existing parity infrastructure ---
from runtime_parity_check import (  # type: ignore
    FIXTURE_ROOT,
    SAMPLE_ROOT,
    CheckRecord,
    _LANG_UNSUPPORTED_FIXTURES,
    _crc32_hex,
    _file_crc32,
    _file_size_normalized,
    _normalize_output_for_compare,
    _parse_output_path,
    _purge_case_artifacts,
    _resolve_output_path,
    _run_cpp_emit_dir,
    _safe_unlink,
    _target_output_text,
    _tool_env_for_target,
    can_run,
    collect_fixture_case_stems,
    collect_sample_case_stems,
    find_case_path,
    normalize,
    run_shell,
)
from toolchain.misc.pytra_cli_profiles import get_target_profile, list_parity_targets  # type: ignore


# ---------------------------------------------------------------------------
# Registry singleton (loaded once, shared across all cases)
# ---------------------------------------------------------------------------

_REGISTRY = None


def _get_registry():
    global _REGISTRY
    if _REGISTRY is not None:
        return _REGISTRY
    root = ROOT
    east1_root = root / "test" / "include" / "east1" / "py"
    builtins_path = east1_root / "built_in" / "builtins.py.east1"
    containers_path = east1_root / "built_in" / "containers.py.east1"
    stdlib_dir = east1_root / "std"
    _REGISTRY = load_builtin_registry(builtins_path, containers_path, stdlib_dir)
    return _REGISTRY


# ---------------------------------------------------------------------------
# In-memory transpile
# ---------------------------------------------------------------------------


def _transpile_in_memory(
    case_path: Path,
    target: str,
    output_dir: Path,
    east3_opt_level: int = 1,
) -> tuple[bool, str]:
    """Transpile a .py file to target language using in-memory pipeline.

    Returns (success, error_message).
    """
    try:
        # 1. Parse
        east1_doc = parse_python_file(str(case_path))

        # 2. Resolve
        registry = _get_registry()
        east2_doc = deep_copy_json(east1_doc)
        if not isinstance(east2_doc, dict):
            return False, "invalid east1 document"
        resolve_east1_to_east2(east2_doc, registry=registry)

        # 3. Compile (lower)
        east3_doc = lower_east2_to_east3(east2_doc, target_language=target)

        # 4. Optimize
        east3_opt, _report = optimize_east3_document(east3_doc, opt_level=east3_opt_level)

        # 5. Link — write east3-opt to temp file for link_modules
        link_dir = output_dir / "_link"
        link_dir.mkdir(parents=True, exist_ok=True)
        link_path = link_dir / (case_path.stem + ".east3")
        link_path.write_text(
            json.dumps(east3_opt, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        link_result = link_modules([str(link_path)], target=target, dispatch_mode="native")

        # 6. Emit
        emit_dir = output_dir / "emit"
        emit_dir.mkdir(parents=True, exist_ok=True)

        if target == "go":
            for m in link_result.linked_modules:
                code = emit_go_module(m.east_doc)
                if code.strip() == "":
                    continue
                out_name = m.module_id.replace(".", "_") + ".go"
                emit_dir.joinpath(out_name).write_text(code, encoding="utf-8")
            _copy_go_runtime(emit_dir)
        elif target == "cpp":
            for m in link_result.linked_modules:
                if m.module_kind == "runtime":
                    emit_runtime_module_artifacts(
                        m.module_id,
                        m.east_doc,
                        output_dir=emit_dir,
                        source_path=m.source_path,
                    )
                    continue
                if m.module_kind == "helper":
                    _emit_helper_cpp(m, emit_dir)
                    continue
                code = emit_cpp_module(m.east_doc)
                if code.strip() == "":
                    continue
                emit_dir.joinpath(m.module_id.replace(".", "_") + ".cpp").write_text(
                    code, encoding="utf-8"
                )
        else:
            return False, f"unsupported target: {target}"

        return True, ""
    except Exception as e:
        return False, str(e)


def _copy_go_runtime(emit_dir: Path) -> None:
    """Copy Go runtime files to emit directory (flat, all in same package dir)."""
    go_runtime = ROOT / "src" / "runtime" / "go"
    if not go_runtime.exists():
        return
    for f in sorted(go_runtime.rglob("*.go")):
        dest = emit_dir / f.name
        shutil.copy2(f, dest)


def _emit_helper_cpp(m, emit_dir: Path) -> None:
    """Emit a C++ helper module (header + source)."""
    rel = runtime_rel_tail_for_module(m.module_id)
    if rel == "":
        rel = "/".join(m.module_id.split("."))
    cpp_path = emit_dir / (rel + ".cpp")
    h_path = emit_dir / (rel + ".h")
    cpp_path.parent.mkdir(parents=True, exist_ok=True)
    h_path.parent.mkdir(parents=True, exist_ok=True)
    cpp_path.write_text(emit_cpp_module(m.east_doc), encoding="utf-8")
    h_path.write_text(
        build_cpp_header_from_east3(m.module_id, m.east_doc, rel_header_path=rel + ".h"),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Run target (compile + execute)
# ---------------------------------------------------------------------------


def _run_target(
    target: str,
    output_dir: Path,
    case_path: Path,
    *,
    work_dir: Path,
    env: dict[str, str] | None = None,
    timeout_sec: int = 120,
) -> subprocess.CompletedProcess[str]:
    """Compile and run the emitted code.

    *work_dir* is the parity check working directory, used as cwd for all
    target executions so that relative output paths match the Python run.
    """
    emit_dir = output_dir / "emit"

    if target == "cpp":
        return _run_cpp_emit_dir(emit_dir, cwd=work_dir, env=env, timeout_sec=timeout_sec)

    if target == "go":
        go_files = sorted(str(p) for p in emit_dir.rglob("*.go"))
        if len(go_files) == 0:
            return subprocess.CompletedProcess("", 1, "", "no .go files found")
        cmd = "go run " + " ".join(shlex.quote(f) for f in go_files)
        return run_shell(cmd, cwd=work_dir, env=env, timeout_sec=timeout_sec)

    return subprocess.CompletedProcess("", 1, "", f"unsupported target: {target}")


# ---------------------------------------------------------------------------
# Main check logic
# ---------------------------------------------------------------------------


def check_case(
    case_stem: str,
    enabled_targets: set[str],
    *,
    case_root: str,
    east3_opt_level: int = 1,
    cmd_timeout_sec: int = 120,
    records: list[CheckRecord] | None = None,
) -> int:
    def _record(target: str, category: str, detail: str) -> None:
        if records is not None:
            records.append(CheckRecord(case_stem=case_stem, target=target, category=category, detail=detail))

    case_path = find_case_path(case_stem, case_root)
    if case_path is None:
        print(f"[ERROR] missing case: {case_stem}")
        _record("-", "case_missing", "missing case")
        return 1

    work = ROOT / "work" / "transpile" / "parity-fast" / (case_stem + "_" + str(os.getpid()))
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True, exist_ok=True)

    try:
        # Run Python reference
        (work / "src").symlink_to(ROOT / "src", target_is_directory=True)
        (work / "test").symlink_to(ROOT / "test", target_is_directory=True)
        (work / "out").mkdir(parents=True, exist_ok=True)
        if case_root == "sample":
            (work / "sample").mkdir(parents=True, exist_ok=True)
            (work / "sample" / "py").symlink_to(ROOT / "sample" / "py", target_is_directory=True)
            (work / "sample" / "out").mkdir(parents=True, exist_ok=True)

        _purge_case_artifacts(work, case_stem)
        py = run_shell(
            f"python {shlex.quote(case_path.as_posix())}",
            cwd=work,
            env={"PYTHONPATH": "src"},
            timeout_sec=cmd_timeout_sec,
        )
        if py.returncode != 0:
            print(f"[ERROR] python:{case_stem} failed")
            _record("python", "python_failed", py.stderr.strip())
            return 1

        expected = _normalize_output_for_compare(py.stdout)
        expected_artifact_path: Path | None = None
        expected_artifact_size: int | None = None
        expected_artifact_crc32: int | None = None
        expected_out_txt = _parse_output_path(py.stdout)
        if expected_out_txt != "":
            expected_artifact_path = _resolve_output_path(work, expected_out_txt)
            if not expected_artifact_path.exists():
                _record("python", "python_artifact_missing", str(expected_artifact_path))
                return 1
            expected_artifact_size = _file_size_normalized(expected_artifact_path)
            expected_artifact_crc32 = _file_crc32(expected_artifact_path)

        mismatches: list[str] = []
        for target_name in sorted(enabled_targets):
            if case_stem in _LANG_UNSUPPORTED_FIXTURES.get(target_name, set()):
                print(f"[SKIP] {case_stem}:{target_name} (unsupported feature)")
                _record(target_name, "unsupported_feature", "unsupported feature")
                continue

            profile = get_target_profile(target_name)
            target_obj_needs = profile.runner_needs
            from runtime_parity_check import Target
            dummy_target = Target(name=target_name, transpile_cmd="", run_cmd="", needs=target_obj_needs)
            if not can_run(dummy_target):
                print(f"[SKIP] {case_stem}:{target_name} (missing toolchain)")
                _record(target_name, "toolchain_missing", "missing toolchain")
                continue

            target_env = _tool_env_for_target(dummy_target)

            # In-memory transpile
            out_dir = work / "transpile" / target_name
            ok, err_msg = _transpile_in_memory(case_path, target_name, out_dir, east3_opt_level)
            if not ok:
                mismatches.append(f"{case_stem}:{target_name}: transpile failed: {err_msg}")
                _record(target_name, "transpile_failed", err_msg)
                continue

            # Compile + run (subprocess)
            _purge_case_artifacts(work, case_stem)
            _safe_unlink(expected_artifact_path)
            rr = _run_target(target_name, out_dir, case_path, work_dir=work, env=target_env, timeout_sec=cmd_timeout_sec)
            if rr.returncode != 0:
                msg = rr.stderr.strip()
                mismatches.append(f"{case_stem}:{target_name}: run failed: {msg}")
                _record(target_name, "run_failed", msg)
                continue

            raw_actual = _target_output_text(target_name, rr)
            actual = _normalize_output_for_compare(raw_actual, target_name)
            if actual != expected:
                mismatches.append(f"{case_stem}:{target_name}: output mismatch")
                _record(target_name, "output_mismatch", "stdout mismatch")
                continue

            # Artifact check
            actual_out_txt = _parse_output_path(raw_actual)
            if expected_artifact_size is None:
                print(f"[OK] {case_stem}:{target_name}")
                _record(target_name, "ok", "")
                continue

            if actual_out_txt == "":
                mismatches.append(f"{case_stem}:{target_name}: artifact presence mismatch")
                _record(target_name, "artifact_presence_mismatch", "missing output line")
                continue

            actual_artifact_path = _resolve_output_path(work, actual_out_txt)
            if not actual_artifact_path.exists():
                mismatches.append(f"{case_stem}:{target_name}: artifact missing")
                _record(target_name, "artifact_missing", str(actual_artifact_path))
                continue

            actual_size = _file_size_normalized(actual_artifact_path)
            if actual_size != expected_artifact_size:
                mismatches.append(f"{case_stem}:{target_name}: artifact size mismatch")
                _record(target_name, "artifact_size_mismatch", "size mismatch")
                continue

            actual_crc = _file_crc32(actual_artifact_path)
            if expected_artifact_crc32 is not None and actual_crc != expected_artifact_crc32:
                mismatches.append(f"{case_stem}:{target_name}: artifact crc32 mismatch")
                _record(target_name, "artifact_crc32_mismatch", "crc32 mismatch")
                continue

            info = f"artifact_size={actual_size} artifact_crc32={_crc32_hex(actual_crc)}"
            print(f"[OK] {case_stem}:{target_name} {info}")
            _record(target_name, "ok", info)

    finally:
        if work.exists():
            shutil.rmtree(work, ignore_errors=True)

    if mismatches:
        print("\n[FAIL] mismatches")
        for m in mismatches:
            print(f"- {m}")
        return 1

    print(f"[PASS] {case_stem}")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fast runtime parity check (in-memory pipeline, no CLI subprocess for transpile)"
    )
    parser.add_argument("cases", nargs="*", default=[], help="case stems (without .py)")
    parser.add_argument("--case-root", default="fixture", choices=("fixture", "sample"))
    parser.add_argument("--targets", default="cpp", help="comma separated targets (default: cpp)")
    parser.add_argument("--all-samples", action="store_true")
    parser.add_argument("--category", default="", help="fixture subdirectory (e.g. oop, control)")
    parser.add_argument("--east3-opt-level", default=1, type=int, choices=(0, 1, 2))
    parser.add_argument("--cmd-timeout-sec", default=120, type=int)
    parser.add_argument("--summary-json", default="")
    args = parser.parse_args()

    enabled_targets: set[str] = set()
    for raw in args.targets.split(","):
        name = raw.strip()
        if name != "":
            enabled_targets.add(name)
    if len(enabled_targets) == 0:
        print("[ERROR] --targets must include at least one target")
        return 1

    # Resolve case stems (reuse logic from runtime_parity_check)
    from runtime_parity_check import resolve_case_stems
    stems, err = resolve_case_stems(args.cases, args.case_root, args.all_samples, args.category)
    if err != "":
        print(f"[ERROR] {err}")
        return 2
    if len(stems) == 0:
        print("[ERROR] no cases resolved")
        return 2

    # Pre-load registry once
    t0 = time.monotonic()
    _get_registry()
    t_reg = time.monotonic() - t0
    print(f"[INFO] registry loaded in {t_reg:.2f}s ({len(stems)} cases, targets={args.targets})")

    exit_code = 0
    pass_cases = 0
    fail_cases = 0
    records: list[CheckRecord] = []

    t_start = time.monotonic()
    for stem in stems:
        code = check_case(
            stem,
            enabled_targets,
            case_root=args.case_root,
            east3_opt_level=args.east3_opt_level,
            cmd_timeout_sec=args.cmd_timeout_sec,
            records=records,
        )
        if code != 0:
            exit_code = code
            fail_cases += 1
        else:
            pass_cases += 1
    elapsed = time.monotonic() - t_start

    category_counts: dict[str, int] = {}
    for rec in records:
        category_counts[rec.category] = category_counts.get(rec.category, 0) + 1

    print(
        f"SUMMARY cases={len(stems)} pass={pass_cases} fail={fail_cases} "
        f"targets={','.join(sorted(enabled_targets))} "
        f"east3_opt_level={args.east3_opt_level} "
        f"elapsed={elapsed:.1f}s"
    )
    if len(category_counts) > 0:
        print("SUMMARY_CATEGORIES")
        for cat in sorted(category_counts.keys()):
            print(f"- {cat}: {category_counts[cat]}")

    if args.summary_json != "":
        summary = {
            "case_root": args.case_root,
            "east3_opt_level": args.east3_opt_level,
            "targets": sorted(enabled_targets),
            "cases": stems,
            "case_total": len(stems),
            "case_pass": pass_cases,
            "case_fail": fail_cases,
            "elapsed_sec": round(elapsed, 2),
            "category_counts": category_counts,
            "records": [
                {"case": r.case_stem, "target": r.target, "category": r.category, "detail": r.detail}
                for r in records
            ],
        }
        out_path = Path(args.summary_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    from runtime_parity_check import _save_parity_results, _maybe_regenerate_progress  # type: ignore
    _save_parity_results(records, args.case_root, enabled_targets)
    _maybe_regenerate_progress()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
