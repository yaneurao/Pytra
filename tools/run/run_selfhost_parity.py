#!/usr/bin/env python3
"""selfhost parity check: verify that a selfhost compiler emits correct code.

For --selfhost-lang python, aggregates results from existing parity results files
and writes selfhost_python.json.

For other selfhost langs (cpp, go, rs, swift, ts, js), builds or locates a selfhost binary,
then transpiles fixture/sample .py files via the binary and checks parity.

Usage:
    # Python selfhost: aggregate from existing .parity-results/*.json
    python3 tools/run/run_selfhost_parity.py --selfhost-lang python

    # C++ selfhost with Go emit
    python3 tools/run/run_selfhost_parity.py \\
        --selfhost-lang cpp --emit-target go --case-root fixture

    # C++ selfhost with pre-built binary
    python3 tools/run/run_selfhost_parity.py \\
        --selfhost-lang cpp --emit-target go,rs \\
        --selfhost-bin work/selfhost/bin/cpp

[P3-SELFHOST-PARITY]
"""
from __future__ import annotations

import argparse
import datetime
import importlib.util
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))
if str(ROOT / "tools" / "check") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools" / "check"))
if str(ROOT / "tools" / "unregistered") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools" / "unregistered"))

def _fallback_collect_runtime_cpp_sources(_cpp_files: list[str], _include_dir: Path) -> list[str]:
    runtime_root = ROOT / "src" / "runtime" / "cpp"
    return sorted(str(path.relative_to(ROOT)) for path in runtime_root.rglob("*.cpp"))


def _filter_runtime_cpp_sources(runtime_sources: list[str], emit_dir: Path) -> list[str]:
    kept: list[str] = []
    runtime_cpp_root = ROOT / "src" / "runtime" / "cpp"
    runtime_east_root = ROOT / "src" / "runtime" / "east"
    for rel in runtime_sources:
        src_path = ROOT / rel
        if src_path.suffix != ".cpp" or not src_path.is_relative_to(runtime_cpp_root):
            kept.append(rel)
            continue
        parent_rel = src_path.parent.relative_to(runtime_cpp_root)
        stem = src_path.stem
        candidate_headers = (
            src_path.with_suffix(".h"),
            emit_dir / parent_rel / f"{stem}.h",
            runtime_east_root / parent_rel / f"{stem}.h",
        )
        if any(path.exists() for path in candidate_headers):
            kept.append(rel)
    return kept


def _load_collect_runtime_cpp_sources():
    try:
        from cpp_runtime_deps import collect_runtime_cpp_sources as helper  # type: ignore
        return helper
    except ModuleNotFoundError:
        pass

    pyc_path = ROOT / "tools" / "__pycache__" / f"cpp_runtime_deps.cpython-{sys.version_info.major}{sys.version_info.minor}.pyc"
    if pyc_path.exists():
        spec = importlib.util.spec_from_file_location("cpp_runtime_deps_pyc", pyc_path)
        if spec is not None and spec.loader is not None:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            helper = getattr(module, "collect_runtime_cpp_sources", None)
            if callable(helper):
                return helper

    return _fallback_collect_runtime_cpp_sources


try:
    collect_runtime_cpp_sources = _load_collect_runtime_cpp_sources()  # type: ignore
except Exception:
    collect_runtime_cpp_sources = _fallback_collect_runtime_cpp_sources  # type: ignore

PARITY_DIR = ROOT / ".parity-results"

# Emit targets supported by the selfhost binary
SUPPORTED_EMIT_TARGETS = ["cpp", "go", "rs", "swift", "ts", "js"]

# Parity targets used to populate the Python row
PARITY_LANGS = [
    "cpp", "rs", "cs", "powershell", "js", "ts", "dart", "go", "java",
    "swift", "kotlin", "ruby", "lua", "scala", "php", "nim", "julia", "zig",
]


# ---------------------------------------------------------------------------
# Timestamp helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------------------
# Python selfhost: aggregate from existing parity results
# ---------------------------------------------------------------------------

_LANG_SHORT: dict[str, str] = {
    "powershell": "ps1",
}


def _load_parity_counts(lang: str, case_root: str) -> tuple[int, int]:
    """Return (pass_count, fail_count) from .parity-results/{lang}_{case_root}.json.

    Only counts cases whose category is 'ok' as pass; everything else as fail.
    Returns (-1, -1) if file not found (untested).
    """
    path = PARITY_DIR / f"{lang}_{case_root}.json"
    if not path.exists():
        # Try short name (e.g. powershell → ps1_fixture.json)
        short = _LANG_SHORT.get(lang, lang)
        if short != lang:
            path = PARITY_DIR / f"{short}_{case_root}.json"
    if not path.exists():
        return -1, -1
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return -1, -1
    results = doc.get("results", {})
    if not isinstance(results, dict):
        return -1, -1
    ok = 0
    fail = 0
    for entry in results.values():
        if not isinstance(entry, dict):
            continue
        cat = entry.get("category", "")
        if cat == "ok":
            ok += 1
        elif cat in ("unsupported_feature", "toolchain_missing"):
            pass  # skip: not a failure of the transpiler
        else:
            fail += 1
    return ok, fail


def run_python_selfhost(emit_targets: list[str], dry_run: bool = False) -> int:
    """Aggregate existing parity results into selfhost_python.json.

    Python is always 'ok' for emit and build stages (no compilation needed).
    """
    now = _now()
    emit_targets_doc: dict[str, object] = {}

    any_tested = False
    for lang in emit_targets:
        fix_ok, fix_fail = _load_parity_counts(lang, "fixture")
        sam_ok, sam_fail = _load_parity_counts(lang, "sample")

        if fix_ok == -1 and sam_ok == -1:
            # Neither fixture nor sample results exist
            emit_targets_doc[lang] = {"status": "not_tested", "timestamp": ""}
            continue

        any_tested = True
        # fixture_fail / sample_fail: if file missing, treat as 0 (not tested ≠ fail)
        f_fail = max(0, fix_fail)
        s_fail = max(0, sam_fail)
        f_ok   = max(0, fix_ok)
        s_ok   = max(0, sam_ok)

        status = "ok" if (f_fail == 0 and s_fail == 0) else "fail"
        entry: dict[str, object] = {
            "status": status,
            "timestamp": now,
        }
        if fix_ok >= 0:
            entry["fixture_pass"] = f_ok
            entry["fixture_fail"] = f_fail
        if sam_ok >= 0:
            entry["sample_pass"] = s_ok
            entry["sample_fail"] = s_fail
        emit_targets_doc[lang] = entry

    parity_status = "ok" if any_tested else "not_tested"
    if any_tested:
        for lang, et in emit_targets_doc.items():
            if isinstance(et, dict) and et.get("status") == "fail":
                parity_status = "fail"
                break

    doc: dict[str, object] = {
        "selfhost_lang": "python",
        "stages": {
            "emit":   {"status": "ok",           "timestamp": now},
            "build":  {"status": "ok",            "timestamp": now},
            "parity": {"status": parity_status,   "timestamp": now},
        },
        "emit_targets": emit_targets_doc,
    }

    out_path = PARITY_DIR / "selfhost_python.json"
    if dry_run:
        print("[dry-run] would write:", out_path.relative_to(ROOT))
        print(json.dumps(doc, ensure_ascii=False, indent=2))
        return 0

    PARITY_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[INFO] wrote {out_path.relative_to(ROOT)}")
    for lang, et in emit_targets_doc.items():
        if isinstance(et, dict):
            status = et.get("status", "not_tested")
            if status == "not_tested":
                print(f"  {lang}: ⬜ not tested")
            elif status == "ok":
                fp = et.get("fixture_pass", "?")
                ff = et.get("fixture_fail", "?")
                sp = et.get("sample_pass",  "?")
                sf = et.get("sample_fail",  "?")
                print(f"  {lang}: 🟩 fixture={fp}+{ff} sample={sp}+{sf}")
            else:
                fp = et.get("fixture_fail", "?")
                sf = et.get("sample_fail", "?")
                print(f"  {lang}: 🟥 fixture_fail={fp} sample_fail={sf}")
    return 0


# ---------------------------------------------------------------------------
# Non-Python selfhost: build binary + run parity
# ---------------------------------------------------------------------------

def _find_selfhost_binary(selfhost_lang: str, explicit_bin: str) -> Path | None:
    """Return path to selfhost binary, or None if not found."""
    if explicit_bin:
        p = Path(explicit_bin)
        if not p.is_absolute():
            p = ROOT / p
        return p if p.exists() else None

    # Conventional location: work/selfhost/bin/<lang>
    convention = ROOT / "work" / "selfhost" / "bin" / selfhost_lang
    if convention.exists():
        return convention

    return None


def _build_selfhost_binary(selfhost_lang: str) -> tuple[Path | None, str]:
    """Attempt to build selfhost binary. Returns (binary_path, error_msg)."""
    build_dir = ROOT / "work" / "selfhost" / "build" / selfhost_lang
    build_dir.mkdir(parents=True, exist_ok=True)
    bin_dir = ROOT / "work" / "selfhost" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    bin_path = bin_dir / selfhost_lang

    # Step 1: emit the toolchain CLI to selfhost_lang via pytra-cli
    cli2 = ROOT / "src" / "pytra-cli.py"
    entry = ROOT / "src" / "pytra-cli.py"
    if not entry.exists():
        return None, f"no entry file for selfhost_lang={selfhost_lang}: {entry}"

    emit_dir = build_dir / "emit"
    if emit_dir.exists():
        shutil.rmtree(emit_dir)
    result = subprocess.run(
        [sys.executable, str(cli2), "-build", str(entry), "--target", selfhost_lang,
         *([] if selfhost_lang != "rs" else ["--rs-package"]),
         "-o", str(emit_dir)],
        cwd=str(ROOT), capture_output=True, text=True,
    )
    if result.returncode != 0:
        details = result.stderr.strip()
        if details == "":
            details = result.stdout.strip()
        return None, f"emit failed: {details}"

    # Step 2: compile to binary
    if selfhost_lang == "cpp":
        cpp_files = sorted(str(p) for p in emit_dir.rglob("*.cpp"))
        if not cpp_files:
            return None, "no .cpp files emitted"
        runtime_sources = [
            str(ROOT / rel)
            for rel in _filter_runtime_cpp_sources(
                collect_runtime_cpp_sources(cpp_files, emit_dir),
                emit_dir,
            )
        ]
        compile_result = subprocess.run(
            [
                "g++",
                "-O2",
                "-std=c++20",
                "-I",
                str(emit_dir),
                "-I",
                str(ROOT / "src"),
                "-I",
                str(ROOT / "src" / "runtime" / "cpp"),
                "-I",
                str(ROOT / "src" / "runtime" / "east"),
            ]
            + cpp_files
            + runtime_sources
            + ["-o", str(bin_path)],
            cwd=str(ROOT), capture_output=True, text=True,
        )
        if compile_result.returncode != 0:
            return None, f"g++ failed: {compile_result.stderr.strip()}"
        return bin_path, ""

    if selfhost_lang == "go":
        go_files = sorted(str(p) for p in emit_dir.rglob("*.go"))
        if not go_files:
            return None, "no .go files emitted"
        compile_result = subprocess.run(
            ["go", "build", "-o", str(bin_path)] + go_files,
            cwd=str(emit_dir), capture_output=True, text=True,
        )
        if compile_result.returncode != 0:
            return None, f"go build failed: {compile_result.stderr.strip()}"
        return bin_path, ""

    if selfhost_lang == "rs":
        cargo_toml = emit_dir / "Cargo.toml"
        if not cargo_toml.exists():
            return None, "missing Cargo.toml in Rust package output"
        compile_result = subprocess.run(
            ["cargo", "build", "--release"],
            cwd=str(emit_dir), capture_output=True, text=True,
        )
        if compile_result.returncode != 0:
            return None, f"cargo build failed: {compile_result.stderr.strip()}"
        built_bin = emit_dir / "target" / "release" / "pytra_selfhost"
        if not built_bin.exists():
            return None, "cargo build succeeded but binary was not produced"
        shutil.copy2(built_bin, bin_path)
        return bin_path, ""

    if selfhost_lang == "swift":
        swift_runtime = ROOT / "src" / "runtime" / "swift"
        built_in = swift_runtime / "built_in" / "py_runtime.swift"
        if built_in.exists():
            shutil.copy2(built_in, emit_dir / built_in.name)
        image_runtime = swift_runtime / "image_runtime.swift"
        if image_runtime.exists():
            shutil.copy2(image_runtime, emit_dir / image_runtime.name)
        std_dir = swift_runtime / "std"
        if std_dir.exists():
            for swift_file in sorted(std_dir.glob("*.swift")):
                shutil.copy2(swift_file, emit_dir / swift_file.name)
        swift_files = sorted(str(p) for p in emit_dir.rglob("*.swift"))
        if not swift_files:
            return None, "no .swift files emitted"
        compile_result = subprocess.run(
            ["swiftc", "-O"] + swift_files + ["-o", str(bin_path)],
            cwd=str(emit_dir), capture_output=True, text=True,
        )
        if compile_result.returncode != 0:
            return None, f"swiftc failed: {compile_result.stderr.strip()}"
        return bin_path, ""

    return None, f"unsupported selfhost_lang for build: {selfhost_lang}"


def _transpile_via_selfhost_binary(
    selfhost_bin: Path,
    emit_target: str,
    case_path: Path,
    out_dir: Path,
) -> tuple[bool, str]:
    """Use selfhost binary + Python bridge to emit case_path to out_dir.

    Bridge: Python parse/resolve/compile/link/optimize .py → east3 JSON
    Selfhost binary reads east3 JSON and emits to emit_target.

    Returns (success, error_msg).
    """
    try:
        # Import in-memory pipeline
        from toolchain.common.jv import deep_copy_json  # type: ignore
        from toolchain.compile.lower import lower_east2_to_east3  # type: ignore
        from toolchain.link.linker import link_modules  # type: ignore
        from toolchain.optimize.optimizer import optimize_east3_document  # type: ignore
        from toolchain.parse.py.parse_python import parse_python_file  # type: ignore
        from toolchain.resolve.py.builtin_registry import load_builtin_registry  # type: ignore
        from toolchain.resolve.py.resolver import resolve_east1_to_east2  # type: ignore

        pipeline_target = "ts" if emit_target == "js" else emit_target

        east1_doc = parse_python_file(str(case_path))
        builtins_path = (ROOT / "test" / "include" / "east1" / "py" /
                         "built_in" / "builtins.py.east1")
        containers_path = (ROOT / "test" / "include" / "east1" / "py" /
                           "built_in" / "containers.py.east1")
        stdlib_dir = ROOT / "test" / "include" / "east1" / "py" / "std"
        registry = load_builtin_registry(builtins_path, containers_path, stdlib_dir)

        east2_doc = deep_copy_json(east1_doc)
        resolve_east1_to_east2(east2_doc, registry=registry)
        east3_doc = lower_east2_to_east3(east2_doc, target_language=pipeline_target)
        east3_opt, _ = optimize_east3_document(east3_doc, opt_level=1)

        link_tmp = out_dir / "_link"
        link_tmp.mkdir(parents=True, exist_ok=True)
        link_path = link_tmp / (case_path.stem + ".east3")
        link_path.write_text(
            json.dumps(east3_opt, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        link_result = link_modules([str(link_path)], target=pipeline_target, dispatch_mode="native")

        # Write a linked-output bundle and invoke the selfhost CLI with `-emit`.
        linked_dir = out_dir / "_linked"
        linked_dir.mkdir(parents=True, exist_ok=True)
        east3_dir = linked_dir / "east3"
        east3_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = linked_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps(link_result.manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        for m in link_result.linked_modules:
            rel_path = Path("east3") / (m.module_id.replace(".", "/") + ".east3.json")
            module_east3 = linked_dir / rel_path
            module_east3.parent.mkdir(parents=True, exist_ok=True)
            module_east3.write_text(
                json.dumps(m.east_doc, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

        emit_out = out_dir / "emit"
        emit_out.mkdir(parents=True, exist_ok=True)
        cmd = [
            str(selfhost_bin),
            "-emit",
            str(linked_dir),
            "-o",
            str(emit_out),
            "--target",
            emit_target,
        ]
        rr = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=60)
        if rr.returncode != 0:
            detail = rr.stderr.strip() or rr.stdout.strip()
            return False, f"selfhost binary failed: {detail}"

        return True, ""
    except Exception as e:
        return False, str(e)


def _run_target_emit(
    emit_target: str,
    emit_dir: Path,
    case_path: Path,
    work_dir: Path,
    env: dict[str, str] | None,
    timeout_sec: int = 120,
) -> subprocess.CompletedProcess[str]:
    """Compile and run emitted code. Reuses logic from runtime_parity_check_fast."""
    # Inline the minimal subset of _run_target logic
    if emit_target == "go":
        go_files = sorted(str(p) for p in emit_dir.rglob("*.go"))
        if not go_files:
            return subprocess.CompletedProcess("", 1, "", "no .go files")
        cmd = "go run " + " ".join(shlex.quote(f) for f in go_files)
        return _shell(cmd, cwd=work_dir, env=env, timeout_sec=timeout_sec)
    if emit_target == "cpp":
        from runtime_parity_check import _run_cpp_emit_dir  # type: ignore
        return _run_cpp_emit_dir(emit_dir, cwd=work_dir, env=env, timeout_sec=timeout_sec)
    if emit_target == "rs":
        stem = case_path.stem
        entry_rs = emit_dir / (stem + ".rs")
        if not entry_rs.exists():
            return subprocess.CompletedProcess("", 1, "", f"missing {entry_rs.name}")
        exe = emit_dir / (stem + ".out")
        build = _shell(
            f"rustc -O {shlex.quote(str(entry_rs))} -o {shlex.quote(str(exe))}",
            cwd=work_dir, env=env, timeout_sec=timeout_sec,
        )
        if build.returncode != 0:
            return build
        return _shell(shlex.quote(str(exe)), cwd=work_dir, env=env, timeout_sec=timeout_sec)
    if emit_target == "swift":
        swift_files = sorted(str(p) for p in emit_dir.rglob("*.swift"))
        if not swift_files:
            return subprocess.CompletedProcess("", 1, "", "no .swift files")
        exe = emit_dir / (case_path.stem + ".out")
        build = _shell(
            "swiftc -O "
            + " ".join(shlex.quote(f) for f in swift_files)
            + " -o "
            + shlex.quote(str(exe)),
            cwd=work_dir, env=env, timeout_sec=timeout_sec,
        )
        if build.returncode != 0:
            return build
        return _shell(shlex.quote(str(exe)), cwd=work_dir, env=env, timeout_sec=timeout_sec)
    if emit_target == "ts":
        stem = case_path.stem
        entry_ts = emit_dir / (stem + ".ts")
        if not entry_ts.exists():
            return subprocess.CompletedProcess("", 1, "", f"missing {entry_ts.name}")
        ts_env = dict(env) if env else {}
        ts_env.setdefault("npm_config_cache", "/tmp/npm-cache")
        return _shell(
            f"npx -y tsx {shlex.quote(str(entry_ts))}",
            cwd=work_dir, env=ts_env, timeout_sec=timeout_sec,
        )
    if emit_target == "js":
        stem = case_path.stem
        entry_js = emit_dir / (stem + ".js")
        if not entry_js.exists():
            return subprocess.CompletedProcess("", 1, "", f"missing {entry_js.name}")
        return _shell(
            f"node {shlex.quote(str(entry_js))}",
            cwd=work_dir, env=env, timeout_sec=timeout_sec,
        )
    return subprocess.CompletedProcess("", 1, "", f"unsupported: {emit_target}")


def _shell(
    cmd: str,
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout_sec: int = 120,
) -> subprocess.CompletedProcess[str]:
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    try:
        return subprocess.run(
            cmd, shell=True, cwd=str(cwd), env=full_env,
            capture_output=True, text=True, timeout=timeout_sec,
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(cmd, 1, "", "timeout")


def _normalize(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.splitlines()).strip()


def run_compiled_selfhost(
    selfhost_lang: str,
    selfhost_bin: Path,
    emit_targets: list[str],
    case_stems: list[str],
    case_root: str,
    timeout_sec: int = 120,
) -> int:
    """Run parity check using selfhost binary and write selfhost_<lang>.json."""
    from runtime_parity_check import (  # type: ignore
        find_case_path,
        _purge_case_artifacts,
        _parse_output_path,
        _resolve_output_path,
        _normalize_output_for_compare,
        _target_output_text,
        _tool_env_for_target,
        can_run,
    )
    from toolchain.misc.target_profiles import get_target_profile
    from runtime_parity_check import Target  # type: ignore

    now = _now()
    # Emit stage: always ok (Python bridge)
    stages: dict[str, object] = {
        "emit":   {"status": "ok", "timestamp": now},
        "build":  {"status": "ok", "timestamp": now},
        "parity": {"status": "pending", "timestamp": now},
    }
    emit_targets_doc: dict[str, object] = {}

    for emit_target in emit_targets:
        # Check toolchain availability
        try:
            profile = get_target_profile(emit_target)
            dummy_target = Target(name=emit_target, transpile_cmd="", run_cmd="",
                                  needs=profile.runner_needs)
            if not can_run(dummy_target):
                emit_targets_doc[emit_target] = {
                    "status": "toolchain_missing", "timestamp": now}
                continue
            target_env = _tool_env_for_target(dummy_target)
        except Exception as e:
            emit_targets_doc[emit_target] = {"status": "toolchain_missing", "timestamp": now,
                                              "detail": str(e)}
            continue

        fix_ok = fix_fail = sam_ok = sam_fail = 0
        all_counts = {"fixture": [0, 0], "sample": [0, 0]}

        for case_stem in case_stems:
            case_path = find_case_path(case_stem, case_root)
            if case_path is None:
                continue

            work = ROOT / "work" / "transpile" / "selfhost-parity" / (
                f"{selfhost_lang}_{emit_target}_{case_stem}_{os.getpid()}")
            if work.exists():
                shutil.rmtree(work)
            work.mkdir(parents=True, exist_ok=True)

            try:
                (work / "src").symlink_to(ROOT / "src", target_is_directory=True)
                (work / "test").symlink_to(ROOT / "test", target_is_directory=True)
                (work / "out").mkdir(parents=True, exist_ok=True)
                if case_root == "sample":
                    (work / "sample").mkdir(parents=True, exist_ok=True)
                    (work / "sample" / "py").symlink_to(
                        ROOT / "sample" / "py", target_is_directory=True)
                    (work / "sample" / "out").mkdir(parents=True, exist_ok=True)

                _purge_case_artifacts(work, case_stem)
                is_emit_only = case_stem.startswith("eo_")
                if is_emit_only:
                    out_dir = work / "selfhost" / emit_target
                    ok, err = _transpile_via_selfhost_binary(
                        selfhost_bin, emit_target, case_path, out_dir)
                    if not ok:
                        print(f"[FAIL] {case_stem}:{emit_target}: selfhost transpile: {err}")
                        all_counts[case_root][1] += 1
                        continue
                    print(f"[OK] {case_stem}:{emit_target} (emit-only)")
                    all_counts[case_root][0] += 1
                    continue

                py_cmd = f"python {shlex.quote(case_path.as_posix())}"
                py_env = {"PYTHONPATH": "src"}
                py = _shell(py_cmd, cwd=work, env=py_env, timeout_sec=timeout_sec)
                if py.returncode != 0:
                    all_counts[case_root][1] += 1
                    continue

                expected = _normalize_output_for_compare(py.stdout)
                expected_out_txt = _parse_output_path(py.stdout)
                expected_artifact_size: int | None = None
                if expected_out_txt:
                    from runtime_parity_check import _resolve_output_path, _file_size_normalized  # type: ignore
                    ep = _resolve_output_path(work, expected_out_txt)
                    expected_artifact_size = _file_size_normalized(ep) if ep.exists() else None

                # Transpile via selfhost binary
                out_dir = work / "selfhost" / emit_target
                ok, err = _transpile_via_selfhost_binary(
                    selfhost_bin, emit_target, case_path, out_dir)
                if not ok:
                    print(f"[FAIL] {case_stem}:{emit_target}: selfhost transpile: {err}")
                    all_counts[case_root][1] += 1
                    continue

                # Run emitted code
                _purge_case_artifacts(work, case_stem)
                emit_dir = out_dir / "emit"
                rr = _run_target_emit(emit_target, emit_dir, case_path,
                                      work_dir=work, env=target_env,
                                      timeout_sec=timeout_sec)
                if rr.returncode != 0:
                    print(f"[FAIL] {case_stem}:{emit_target}: run: {rr.stderr.strip()[:200]}")
                    all_counts[case_root][1] += 1
                    continue

                raw_actual = _target_output_text(emit_target, rr)
                actual = _normalize_output_for_compare(raw_actual, emit_target)
                if actual != expected:
                    print(f"[FAIL] {case_stem}:{emit_target}: output mismatch")
                    all_counts[case_root][1] += 1
                    continue

                if expected_artifact_size is not None:
                    actual_out_txt = _parse_output_path(raw_actual)
                    if not actual_out_txt:
                        all_counts[case_root][1] += 1
                        continue
                    from runtime_parity_check import _resolve_output_path, _file_size_normalized  # type: ignore
                    ap = _resolve_output_path(work, actual_out_txt)
                    if not ap.exists() or _file_size_normalized(ap) != expected_artifact_size:
                        all_counts[case_root][1] += 1
                        continue

                print(f"[OK] {case_stem}:{emit_target}")
                all_counts[case_root][0] += 1

            finally:
                if work.exists():
                    shutil.rmtree(work, ignore_errors=True)

        f_ok, f_fail = all_counts.get("fixture", [0, 0])
        s_ok, s_fail = all_counts.get("sample", [0, 0])
        status = "ok" if (f_fail == 0 and s_fail == 0) else "fail"
        entry: dict[str, object] = {
            "status": status, "timestamp": now,
            "fixture_pass": f_ok, "fixture_fail": f_fail,
            "sample_pass":  s_ok, "sample_fail":  s_fail,
        }
        emit_targets_doc[emit_target] = entry

    # Determine overall parity status
    parity_ok = all(
        isinstance(et, dict) and et.get("status") in ("ok", "toolchain_missing", "not_tested")
        for et in emit_targets_doc.values()
    ) and any(
        isinstance(et, dict) and et.get("status") == "ok"
        for et in emit_targets_doc.values()
    )
    stages["parity"] = {"status": "ok" if parity_ok else "fail", "timestamp": _now()}

    doc: dict[str, object] = {
        "selfhost_lang": selfhost_lang,
        "stages": stages,
        "emit_targets": emit_targets_doc,
    }
    out_path = PARITY_DIR / f"selfhost_{selfhost_lang}.json"
    PARITY_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[INFO] wrote {out_path.relative_to(ROOT)}")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="selfhost parity check — verify selfhost compiler emits correct code"
    )
    parser.add_argument(
        "--selfhost-lang", required=True,
        help="Language toolchain is compiled to (python | cpp | go | rs | swift | ts | js)"
    )
    parser.add_argument(
        "--emit-target", default="",
        help="Comma-separated emit targets (default: all supported). "
             "For --selfhost-lang python, default is all PARITY_LANGS."
    )
    parser.add_argument(
        "--case-root", default="fixture", choices=("fixture", "sample"),
        help="Test case root (default: fixture)"
    )
    parser.add_argument("--all-samples", action="store_true")
    parser.add_argument("--category", default="",
                        help="Fixture category subdirectory (e.g. oop, control)")
    parser.add_argument(
        "--selfhost-bin", default="",
        help="Path to selfhost binary (for non-python langs). "
             "If omitted, looks at work/selfhost/bin/<lang>. "
             "If not found and --no-build is not set, tries to build it."
    )
    parser.add_argument("--no-build", action="store_true",
                        help="Do not attempt to build the selfhost binary if missing")
    parser.add_argument("--cmd-timeout-sec", default=120, type=int)
    parser.add_argument("--dry-run", action="store_true",
                        help="(python selfhost only) print what would be written without writing")
    args = parser.parse_args()

    selfhost_lang = args.selfhost_lang.strip()

    # Resolve emit targets
    if args.emit_target.strip():
        emit_targets = [t.strip() for t in args.emit_target.split(",") if t.strip()]
    elif selfhost_lang == "python":
        emit_targets = list(PARITY_LANGS)
    else:
        emit_targets = list(SUPPORTED_EMIT_TARGETS)

    # --- Python selfhost ---
    if selfhost_lang == "python":
        return run_python_selfhost(emit_targets, dry_run=args.dry_run)

    # --- Non-Python selfhost ---
    # Find or build selfhost binary
    selfhost_bin = _find_selfhost_binary(selfhost_lang, args.selfhost_bin)

    if selfhost_bin is None:
        if args.no_build:
            print(f"[WARN] selfhost binary not found for {selfhost_lang}; recording not_available")
            _write_not_available(selfhost_lang, emit_targets)
            return 0

        print(f"[INFO] selfhost binary not found; attempting to build {selfhost_lang}...")
        selfhost_bin, build_err = _build_selfhost_binary(selfhost_lang)
        if selfhost_bin is None:
            print(f"[FAIL] build failed: {build_err}")
            _write_build_fail(selfhost_lang, build_err, emit_targets)
            return 1

    print(f"[INFO] selfhost binary: {selfhost_bin}")

    # Resolve case stems
    if str(ROOT / "tools" / "check") not in sys.path:
        sys.path.insert(0, str(ROOT / "tools" / "check"))
    from runtime_parity_check import resolve_case_stems  # type: ignore
    stems, err = resolve_case_stems(
        [], args.case_root, args.all_samples, args.category)
    if err:
        print(f"[ERROR] {err}")
        return 2
    if not stems:
        print("[ERROR] no cases resolved")
        return 2

    return run_compiled_selfhost(
        selfhost_lang=selfhost_lang,
        selfhost_bin=selfhost_bin,
        emit_targets=emit_targets,
        case_stems=stems,
        case_root=args.case_root,
        timeout_sec=args.cmd_timeout_sec,
    )


def _emit_target_stage_doc(emit_targets: list[str], status: str, now: str, detail: str = "") -> dict[str, object]:
    out: dict[str, object] = {}
    for target in emit_targets:
        entry: dict[str, object] = {"status": status, "timestamp": now}
        if detail != "":
            entry["detail"] = detail
        out[target] = entry
    return out


def _write_not_available(selfhost_lang: str, emit_targets: list[str]) -> None:
    now = _now()
    doc: dict[str, object] = {
        "selfhost_lang": selfhost_lang,
        "stages": {
            "emit":   {"status": "ok", "timestamp": now},
            "build":  {"status": "not_available", "timestamp": now},
            "parity": {"status": "not_tested", "timestamp": now},
        },
        "emit_targets": _emit_target_stage_doc(emit_targets, "not_available", now),
    }
    _write_selfhost_json(selfhost_lang, doc)


def _write_build_fail(selfhost_lang: str, detail: str, emit_targets: list[str]) -> None:
    now = _now()
    doc: dict[str, object] = {
        "selfhost_lang": selfhost_lang,
        "stages": {
            "emit":   {"status": "ok",    "timestamp": now},
            "build":  {"status": "fail",  "timestamp": now, "detail": detail},
            "parity": {"status": "not_tested", "timestamp": now},
        },
        "emit_targets": _emit_target_stage_doc(emit_targets, "build_failed", now, detail),
    }
    _write_selfhost_json(selfhost_lang, doc)


def _write_selfhost_json(selfhost_lang: str, doc: dict) -> None:
    PARITY_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PARITY_DIR / f"selfhost_{selfhost_lang}.json"
    out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[INFO] wrote {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    raise SystemExit(main())
