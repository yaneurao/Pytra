#!/usr/bin/env python3
"""Runtime parity check across transpiler targets."""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
import shlex
import shutil
import subprocess
import sys
import time

import zlib
from dataclasses import dataclass
from pathlib import Path

if str((Path(__file__).resolve().parents[2] / "src")) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from toolchain.misc.pytra_cli_profiles import get_target_profile, list_parity_targets

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = ROOT / "test" / "fixture" / "source" / "py"
SAMPLE_ROOT = ROOT / "sample" / "py"
STDLIB_ROOT = ROOT / "test" / "stdlib" / "source" / "py"
ARTIFACT_OPTIONAL_TARGETS: set[str] = set()
_LOCAL_TOOL_FALLBACKS: dict[str, tuple[Path, ...]] = {
    "go": (ROOT / "work" / "tmp" / "go-toolchain" / "bin" / "go",),
    "rustc": (Path("/usr/local/cargo/bin/rustc"),),
    "cargo": (Path("/usr/local/cargo/bin/cargo"),),
}

# Skip list abolished — all fixtures run for all languages.
# FAIL is recorded as FAIL in .parity-results/ and shown in progress matrix.
_LANG_UNSUPPORTED_FIXTURES: dict[str, set[str]] = {}


@dataclass
class Target:
    name: str
    transpile_cmd: str
    run_cmd: str
    needs: tuple[str, ...]
    ignore_artifacts: bool = False
    output_dir: str = ""


@dataclass
class CheckRecord:
    case_stem: str
    target: str
    category: str
    detail: str
    elapsed_sec: float | None = None


def normalize(text: str) -> str:
    lines = [ln.rstrip() for ln in text.replace("\r\n", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def run_shell(
    cmd: str,
    cwd: Path,
    *,
    env: dict[str, str] | None = None,
    timeout_sec: int | None = None,
) -> subprocess.CompletedProcess[str]:
    proc_env = os.environ.copy()
    if env is not None:
        proc_env.update(env)
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=proc_env,
        start_new_session=True,
    )
    try:
        stdout_text, stderr_text = proc.communicate(timeout=timeout_sec)
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=int(proc.returncode or 0),
            stdout=stdout_text,
            stderr=stderr_text,
        )
    except subprocess.TimeoutExpired:
        # Kill the whole process group so compiled runners spawned by the shell
        # cannot continue running in the background.
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        stdout_text, stderr_text = proc.communicate()
        timeout_note = f"[TIMEOUT] exceeded {timeout_sec}s: {cmd}"
        if stderr_text == "":
            stderr_text = timeout_note
        else:
            stderr_text = stderr_text.rstrip() + "\n" + timeout_note
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=124,
            stdout=stdout_text,
            stderr=stderr_text,
        )


def _resolve_tool_path(tool: str) -> str:
    if tool.startswith("/"):
        if Path(tool).is_file():
            return tool
        return ""
    found = shutil.which(tool)
    if found is not None:
        return found
    for candidate in _LOCAL_TOOL_FALLBACKS.get(tool, ()):
        if candidate.is_file():
            return str(candidate)
    return ""


def _tool_env_for_target(target: Target) -> dict[str, str]:
    extra_dirs: list[str] = []
    for tool in target.needs:
        if tool.startswith("/"):
            continue
        if shutil.which(tool) is not None:
            continue
        resolved = _resolve_tool_path(tool)
        if resolved == "":
            continue
        tool_dir = str(Path(resolved).parent)
        if tool_dir not in extra_dirs:
            extra_dirs.append(tool_dir)
    if len(extra_dirs) == 0:
        return {}
    current_path = os.environ.get("PATH", "")
    path_parts = extra_dirs + ([current_path] if current_path != "" else [])
    return {"PATH": os.pathsep.join(path_parts)}


def can_run(target: Target) -> bool:
    for tool in target.needs:
        if _resolve_tool_path(tool) == "":
            return False
    return True


def _normalize_output_for_compare(stdout_text: str, target_name: str = "") -> str:
    lines: list[str] = []
    for line in stdout_text.splitlines():
        low = line.strip().lower()
        if low.startswith("elapsed_sec:") or low.startswith("elapsed:") or low.startswith("time_sec:"):
            continue
        if low.startswith("build:"):
            continue
        if low.startswith("generated:"):
            continue
        if low.startswith("emitted:"):
            continue
        if target_name == "nim" and "warning:" in low:
            continue
        # C++ build via make: filter build log lines
        if target_name == "cpp":
            if low.startswith("make:") or low.startswith("g++") or low.startswith("clang"):
                continue
        lines.append(line)
    return "\n".join(lines)


def _target_output_text(target_name: str, cp: subprocess.CompletedProcess[str]) -> str:
    out = cp.stdout or ""
    if target_name == "nim" and out.strip() == "":
        # nim `c -r` prints program stdout together with compiler diagnostics
        # to stderr; parity compare should consume that stream.
        return cp.stderr or ""
    return out


def _parse_output_path(stdout_text: str) -> str:
    m = re.search(r"^output:\s*(.+)$", stdout_text, flags=re.MULTILINE)
    if m is None:
        return ""
    return m.group(1).strip()


def _resolve_output_path(cwd: Path, output_text: str) -> Path:
    p = Path(output_text)
    if p.is_absolute():
        return p
    return cwd / p


def _safe_unlink(path: Path | None) -> None:
    if path is None:
        return
    if path.exists() and path.is_file():
        path.unlink()


def _is_text_artifact(path: Path) -> bool:
    return path.suffix.lower() in {".txt", ".csv", ".log"}


def _read_artifact_bytes(path: Path) -> bytes:
    """Read artifact bytes, normalizing CRLF to LF for text files."""
    data = path.read_bytes()
    if _is_text_artifact(path):
        data = data.replace(b"\r\n", b"\n")
    return data


def _file_crc32(path: Path) -> int:
    data = _read_artifact_bytes(path)
    return zlib.crc32(data) & 0xFFFFFFFF


def _file_size_normalized(path: Path) -> int:
    return len(_read_artifact_bytes(path))


def _crc32_hex(v: int) -> str:
    return f"0x{(v & 0xFFFFFFFF):08x}"


def _run_cpp_emit_dir(
    emit_dir: Path,
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout_sec: int | None = None,
    exe_name: str = "app.out",
) -> subprocess.CompletedProcess[str]:
    if not emit_dir.exists() or not emit_dir.is_dir():
        return subprocess.CompletedProcess(
            args=str(emit_dir),
            returncode=1,
            stdout="",
            stderr="missing emit dir: " + str(emit_dir),
        )

    cpp_files: list[str] = []
    for path in sorted(emit_dir.rglob("*.cpp")):
        cpp_files.append(str(path))
    if len(cpp_files) == 0:
        return subprocess.CompletedProcess(
            args=str(emit_dir),
            returncode=1,
            stdout="",
            stderr="no .cpp files found in " + str(emit_dir),
        )

    src_dir = ROOT / "src"
    runtime_root = src_dir / "runtime" / "cpp"
    native_sources: list[str] = [str(runtime_root / "core" / "io.cpp")]
    for bucket in ("std", "utils"):
        native_dir = runtime_root / bucket
        if not native_dir.exists():
            continue
        for cpp_path in sorted(native_dir.glob("*.cpp"), key=lambda p: str(p)):
            generated_hdr = emit_dir / bucket / cpp_path.with_suffix(".h").name
            if generated_hdr.exists():
                native_sources.append(str(cpp_path))

    exe_path = emit_dir / exe_name
    compile_cmd = [
        "g++",
        "-std=c++20",
        "-O2",
        "-I", str(emit_dir),
        "-I", str(src_dir),
        "-I", str(runtime_root),
        "-o", str(exe_path),
    ] + cpp_files + native_sources
    compile_cp = run_shell(
        " ".join(shlex.quote(part) for part in compile_cmd),
        cwd=cwd,
        env=env,
        timeout_sec=timeout_sec,
    )
    if compile_cp.returncode != 0:
        return compile_cp

    return run_shell(
        shlex.quote(str(exe_path)),
        cwd=cwd,
        env=env,
        timeout_sec=timeout_sec,
    )


def _purge_case_artifacts(work: Path, case_stem: str) -> None:
    # Always remove stale artifacts before each run so parity checks cannot pass
    # by reusing files left by a previous language execution.
    for out_dir in (work / "sample" / "out", work / "test" / "out", work / "out"):
        if not out_dir.exists() or not out_dir.is_dir():
            continue
        for p in sorted(out_dir.glob(f"{case_stem}.*")):
            if p.is_file():
                p.unlink()


def find_case_path(case_stem: str, case_root: str) -> Path | None:
    if case_root == "sample":
        root = SAMPLE_ROOT
    elif case_root == "stdlib":
        root = STDLIB_ROOT
    else:
        root = FIXTURE_ROOT
    matches = sorted(root.rglob(f"{case_stem}.py"))
    if not matches:
        return None
    return matches[0]


def collect_sample_case_stems() -> list[str]:
    out: list[str] = []
    for p in sorted(SAMPLE_ROOT.glob("*.py")):
        stem = p.stem
        if stem == "__init__":
            continue
        out.append(stem)
    return out


def collect_fixture_case_stems(category: str = "") -> list[str]:
    """Collect fixture case stems, excluding negative tests (ng_*) and __init__.

    If *category* is non-empty, only stems under that subdirectory are returned.
    """
    if category != "":
        cat_dir = FIXTURE_ROOT / category
        if not cat_dir.is_dir():
            return []
        search_root = cat_dir
    else:
        search_root = FIXTURE_ROOT
    seen: set[str] = set()
    for p in sorted(search_root.rglob("*.py")):
        stem = p.stem
        if stem == "__init__":
            continue
        if stem.startswith("ng_"):
            continue
        seen.add(stem)
    return sorted(seen)


def collect_stdlib_case_stems() -> list[str]:
    """Return all stdlib case stems (from test/stdlib/source/py/<module>/*.py)."""
    seen: set[str] = set()
    if not STDLIB_ROOT.exists():
        return []
    for p in sorted(STDLIB_ROOT.rglob("*.py")):
        stem = p.stem
        if stem == "__init__":
            continue
        seen.add(stem)
    return sorted(seen)


def resolve_case_stems(cases: list[str], case_root: str, all_samples: bool = False, category: str = "") -> tuple[list[str], str]:
    if category != "":
        if len(cases) > 0:
            return [], "--category cannot be combined with positional cases"
        if case_root != "fixture":
            return [], "--category requires --case-root fixture"
        stems = collect_fixture_case_stems(category)
        if len(stems) == 0:
            return [], f"no cases found in category '{category}'"
        return stems, ""
    if len(cases) > 0:
        return cases, ""
    if case_root == "sample":
        return collect_sample_case_stems(), ""
    if case_root == "fixture":
        return collect_fixture_case_stems(), ""
    if case_root == "stdlib":
        return collect_stdlib_case_stems(), ""
    return [], "no cases specified"


def build_targets(
    case_stem: str,
    case_path: Path,
    east3_opt_level: str,
    cpp_codegen_opt: str = "",
) -> list[Target]:
    case_src = case_path.as_posix()
    opt_arg = "--east3-opt-level " + shlex.quote(str(east3_opt_level))

    _pid = str(os.getpid())

    def _output_dir_for_target(target: str) -> str:
        return f"work/transpile/{target}/{case_stem}_{_pid}"

    def _pytra_cmd(target: str, out_dir: str, *, build: bool, run: bool) -> str:
        parts: list[str] = [
            "python",
            "src/pytra-cli.py",
            shlex.quote(case_src),
            "--target",
            shlex.quote(target),
            "--output-dir",
            shlex.quote(out_dir),
            opt_arg,
        ]
        if target == "cpp" and cpp_codegen_opt != "":
            parts.extend(["--codegen-opt", shlex.quote(cpp_codegen_opt)])
        if build:
            parts.append("--build")
        if run:
            parts.append("--run")
        return " ".join(parts)

    out: list[Target] = []
    for name in list_parity_targets():
        profile = get_target_profile(name)
        out_dir = _output_dir_for_target(name)
        out.append(
            Target(
                name=name,
                transpile_cmd=_pytra_cmd(name, out_dir, build=False, run=False),
                run_cmd=_pytra_cmd(name, out_dir, build=True, run=True),
                needs=profile.runner_needs,
                output_dir=out_dir,
            )
        )
    return out


def check_case(
    case_stem: str,
    enabled_targets: set[str],
    *,
    case_root: str,
    ignore_stdout: bool,
    east3_opt_level: str,
    cpp_codegen_opt: str = "",
    cmd_timeout_sec: int = 120,
    records: list[CheckRecord] | None = None,
) -> int:
    # Compatibility note:
    # parity compare always ignores unstable timing lines (elapsed_sec / elapsed / time_sec).
    # This parameter remains for backward compatibility with old callers.
    _ = ignore_stdout

    def _record(target: str, category: str, detail: str) -> None:
        if records is None:
            return
        records.append(CheckRecord(case_stem=case_stem, target=target, category=category, detail=detail))

    case_path = find_case_path(case_stem, case_root)
    if case_path is None:
        print(f"[ERROR] missing case: {case_stem}")
        _record("-", "case_missing", "missing case")
        return 1

    enabled_supported_targets = [
        target_name
        for target_name in enabled_targets
        if case_stem not in _LANG_UNSUPPORTED_FIXTURES.get(target_name, set())
    ]
    if len(enabled_supported_targets) == 0:
        for target_name in sorted(enabled_targets):
            print(f"[SKIP] {case_stem}:{target_name} (unsupported feature)")
            _record(target_name, "unsupported_feature", "unsupported feature")
        return 0

    work = ROOT / "work" / "transpile" / "parity" / (case_stem + "_" + str(os.getpid()))
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True, exist_ok=True)
    try:
        (work / "src").symlink_to(ROOT / "src", target_is_directory=True)
        (work / "test").symlink_to(ROOT / "test", target_is_directory=True)
        (work / "out").mkdir(parents=True, exist_ok=True)
        if case_root == "sample":
            # Keep outputs isolated in temp dir while reusing sample sources.
            (work / "sample").mkdir(parents=True, exist_ok=True)
            (work / "sample" / "py").symlink_to(ROOT / "sample" / "py", target_is_directory=True)
            (work / "sample" / "out").mkdir(parents=True, exist_ok=True)

        _purge_case_artifacts(work, case_stem)
        run_expr = f"python {shlex.quote(case_path.as_posix())}"
        run_env = {"PYTHONPATH": "src"}
        py = run_shell(run_expr, cwd=work, env=run_env, timeout_sec=cmd_timeout_sec)

        if py.returncode != 0:
            print(f"[ERROR] python:{case_stem} failed")
            print(py.stderr.strip())
            _record("python", "python_failed", py.stderr.strip())
            return 1
        expected = _normalize_output_for_compare(py.stdout)
        expected_artifact_size: int | None = None
        expected_artifact_crc32: int | None = None
        expected_artifact_path: Path | None = None
        expected_out_txt = _parse_output_path(py.stdout)
        if expected_out_txt != "":
            expected_artifact_path = _resolve_output_path(work, expected_out_txt)
            if not expected_artifact_path.exists() or not expected_artifact_path.is_file():
                _record("python", "python_artifact_missing", str(expected_artifact_path))
                print(f"[ERROR] python:{case_stem} artifact missing: {expected_artifact_path}")
                return 1
            expected_artifact_size = _file_size_normalized(expected_artifact_path)
            expected_artifact_crc32 = _file_crc32(expected_artifact_path)

        mismatches: list[str] = []
        for target in build_targets(case_stem, case_path, east3_opt_level, cpp_codegen_opt):
            if target.name not in enabled_targets:
                continue
            if not can_run(target):
                print(f"[SKIP] {case_stem}:{target.name} (missing toolchain)")
                _record(target.name, "toolchain_missing", "missing toolchain")
                continue
            target_env = _tool_env_for_target(target)
            unsupported = _LANG_UNSUPPORTED_FIXTURES.get(target.name, set())
            if case_stem in unsupported:
                print(f"[SKIP] {case_stem}:{target.name} (unsupported feature)")
                _record(target.name, "unsupported_feature", "unsupported feature")
                continue

            # Always wipe previous transpile outputs for this target/case pair.
            if target.output_dir != "":
                target_out_dir = work / target.output_dir
                if target_out_dir.exists():
                    shutil.rmtree(target_out_dir)

            tr = run_shell(target.transpile_cmd, cwd=work, env=target_env, timeout_sec=cmd_timeout_sec)
            if tr.returncode != 0:
                msg = tr.stderr.strip()
                mismatches.append(f"{case_stem}:{target.name}: transpile failed: {msg}")
                _record(target.name, "transpile_failed", msg)
                continue

            # Ensure target artifact validation is never masked by stale outputs.
            _purge_case_artifacts(work, case_stem)
            _safe_unlink(expected_artifact_path)

            if target.name == "cpp":
                rr = _run_cpp_emit_dir(
                    work / target.output_dir / "emit",
                    cwd=work,
                    env=target_env,
                    timeout_sec=cmd_timeout_sec,
                )
            else:
                rr = run_shell(target.run_cmd, cwd=work, env=target_env, timeout_sec=cmd_timeout_sec)
            if rr.returncode != 0:
                msg = rr.stderr.strip()
                mismatches.append(f"{case_stem}:{target.name}: run failed: {msg}")
                _record(target.name, "run_failed", msg)
                continue

            raw_actual_output = _target_output_text(target.name, rr)
            actual = _normalize_output_for_compare(raw_actual_output, target.name)
            if actual != expected:
                _record(target.name, "output_mismatch", "stdout mismatch")
                mismatches.append(
                    f"{case_stem}:{target.name}: output mismatch\n"
                    f"  expected: {expected!r}\n"
                    f"  actual  : {actual!r}"
                )
                continue

            if target.ignore_artifacts or target.name in ARTIFACT_OPTIONAL_TARGETS:
                print(f"[OK] {case_stem}:{target.name}")
                _record(target.name, "ok", "")
                continue

            actual_out_txt = _parse_output_path(raw_actual_output)
            if expected_artifact_size is None:
                if actual_out_txt != "":
                    actual_artifact_path = _resolve_output_path(work, actual_out_txt)
                    if actual_artifact_path.exists() and actual_artifact_path.is_file():
                        _record(target.name, "artifact_presence_mismatch", "unexpected artifact")
                        mismatches.append(
                            f"{case_stem}:{target.name}: artifact presence mismatch "
                            "(python:none target:exists)"
                        )
                        continue
                print(f"[OK] {case_stem}:{target.name}")
                _record(target.name, "ok", "")
                continue

            if actual_out_txt == "":
                _record(target.name, "artifact_presence_mismatch", "missing output line")
                mismatches.append(
                    f"{case_stem}:{target.name}: artifact presence mismatch (python:exists target:none)"
                )
                continue

            actual_artifact_path = _resolve_output_path(work, actual_out_txt)
            if not actual_artifact_path.exists() or not actual_artifact_path.is_file():
                _record(target.name, "artifact_missing", str(actual_artifact_path))
                mismatches.append(
                    f"{case_stem}:{target.name}: output artifact missing: {actual_artifact_path}"
                )
                continue

            actual_artifact_size = _file_size_normalized(actual_artifact_path)
            if actual_artifact_size != expected_artifact_size:
                _record(target.name, "artifact_size_mismatch", "size mismatch")
                mismatches.append(
                    f"{case_stem}:{target.name}: artifact size mismatch "
                    f"(python:{expected_artifact_size} target:{actual_artifact_size})"
                )
                continue

            actual_artifact_crc32 = _file_crc32(actual_artifact_path)
            if expected_artifact_crc32 is None:
                expected_artifact_crc32 = _file_crc32(expected_artifact_path)
            if actual_artifact_crc32 != expected_artifact_crc32:
                _record(
                    target.name,
                    "artifact_crc32_mismatch",
                    (
                        f"python:{_crc32_hex(expected_artifact_crc32)} "
                        f"target:{_crc32_hex(actual_artifact_crc32)}"
                    ),
                )
                mismatches.append(
                    f"{case_stem}:{target.name}: artifact crc32 mismatch "
                    f"(python:{_crc32_hex(expected_artifact_crc32)} "
                    f"target:{_crc32_hex(actual_artifact_crc32)})"
                )
                continue

            artifact_info = (
                f"artifact_size={actual_artifact_size} "
                f"artifact_crc32={_crc32_hex(actual_artifact_crc32)}"
            )
            print(f"[OK] {case_stem}:{target.name} {artifact_info}")
            _record(target.name, "ok", artifact_info)

    finally:
        # Clean up work directory after parity check
        if work.exists():
            shutil.rmtree(work, ignore_errors=True)

    if mismatches:
        print("\n[FAIL] mismatches")
        for m in mismatches:
            print(f"- {m}")
        return 1

    print(f"[PASS] {case_stem}")
    return 0


import datetime


def _save_parity_results(records: list[CheckRecord], case_root: str, targets: set[str]) -> None:
    """Save parity check results to .parity-results/<target>_<case-root>.json.

    Existing files are merged on a per-case basis so partial runs accumulate.
    Each case entry carries a timestamp.
    """
    parity_dir = ROOT / ".parity-results"
    parity_dir.mkdir(parents=True, exist_ok=True)

    # Group records by target
    by_target: dict[str, list[CheckRecord]] = {t: [] for t in targets}
    for rec in records:
        if rec.target in by_target:
            by_target[rec.target].append(rec)

    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    for target, recs in by_target.items():
        out_path = parity_dir / f"{target}_{case_root}.json"

        # Load existing data for merge
        existing: dict[str, object] = {}
        if out_path.exists():
            try:
                loaded = json.loads(out_path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict) and "results" in loaded:
                    existing = loaded["results"]  # type: ignore[assignment]
            except Exception:
                pass

        prev_pass = sum(1 for v in existing.values() if isinstance(v, dict) and v.get("category") == "ok")

        results: dict[str, object] = dict(existing)
        for rec in recs:
            entry: dict[str, object] = {"category": rec.category, "timestamp": now}
            if rec.detail:
                entry["detail"] = rec.detail
            if rec.elapsed_sec is not None:
                entry["elapsed_sec"] = round(rec.elapsed_sec, 3)
            results[rec.case_stem] = entry

        curr_pass = sum(1 for v in results.values() if isinstance(v, dict) and v.get("category") == "ok")

        doc = {
            "target": target,
            "case_root": case_root,
            "results": results,
        }
        out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        _append_parity_changelog(target, case_root, prev_pass, curr_pass, now)


_CHANGELOG_PATHS = [
    ROOT / "docs" / "ja" / "progress-preview" / "changelog.md",
    ROOT / "docs" / "en" / "progress-preview" / "changelog.md",
]

_CHANGELOG_HEADER = (
    "# Parity Changelog\n\n"
    "| 日時 | 言語 | case-root | 変化 | 備考 |\n"
    "|---|---|---|---|---|\n"
)


def _append_parity_changelog(target: str, case_root: str, prev_pass: int, curr_pass: int, now: str) -> None:
    """Append a row to progress-preview/changelog.md when PASS count changes."""
    diff = curr_pass - prev_pass
    if diff == 0:
        return
    sign = "+" if diff > 0 else ""
    note = "regression" if diff < 0 else ""
    ts = now[:16]  # "YYYY-MM-DDTHH:MM"
    row = f"| {ts} | {target} | {case_root} | {prev_pass}→{curr_pass} ({sign}{diff}) | {note} |"
    sep_marker = "|---|---|---|---|---|"
    for cl_path in _CHANGELOG_PATHS:
        try:
            cl_path.parent.mkdir(parents=True, exist_ok=True)
            if not cl_path.exists():
                content = _CHANGELOG_HEADER + row + "\n"
            else:
                content = cl_path.read_text(encoding="utf-8")
                idx = content.find(sep_marker)
                if idx == -1:
                    content = content.rstrip("\n") + "\n" + row + "\n"
                else:
                    nl_pos = content.find("\n", idx)
                    insert_after = (nl_pos + 1) if nl_pos != -1 else len(content)
                    content = content[:insert_after] + row + "\n" + content[insert_after:]
            cl_path.write_text(content, encoding="utf-8")
        except Exception:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Run runtime parity checks for stdlib/runtime cases")
    parser.add_argument(
        "cases",
        nargs="*",
        default=[],
        help="case stems (case names without .py).",
    )
    parser.add_argument(
        "--case-root",
        default="fixture",
        choices=("fixture", "sample", "stdlib"),
        help="source root to read cases from (fixture: test/fixture/source/py, sample: sample/py, stdlib: test/stdlib/source/py)",
    )
    parser.add_argument(
        "--ignore-unstable-stdout",
        action="store_true",
        help="deprecated compatibility flag; unstable timing lines are always ignored",
    )
    parser.add_argument(
        "--targets",
        default="cpp",
        help="comma separated targets (default: cpp)",
    )
    parser.add_argument(
        "--category",
        default="",
        help="run only fixtures in this subdirectory (e.g. oop, control, typing). requires --case-root fixture",
    )
    parser.add_argument(
        "--summary-json",
        default="",
        help="optional path to write machine-readable summary json",
    )
    parser.add_argument(
        "--east3-opt-level",
        default="1",
        choices=("0", "1", "2"),
        help="EAST3 optimizer level passed to transpilers (default: 1)",
    )
    parser.add_argument(
        "--cpp-codegen-opt",
        type=int,
        choices=(0, 1, 2, 3),
        default=None,
        help="optional --codegen-opt passed only to C++ parity runs",
    )
    parser.add_argument(
        "--cmd-timeout-sec",
        type=int,
        default=120,
        help="timeout seconds applied to python/transpile/run commands per case (default: 120)",
    )
    args = parser.parse_args()

    enabled_targets: set[str] = set()
    for raw in args.targets.split(","):
        name = raw.strip()
        if name != "":
            enabled_targets.add(name)
    if len(enabled_targets) == 0:
        print("[ERROR] --targets must include at least one target")
        return 1

    stems, err = resolve_case_stems(args.cases, args.case_root, category=args.category)
    if err != "":
        print(f"[ERROR] {err}")
        return 2
    if len(stems) == 0:
        print("[ERROR] no cases resolved")
        return 2

    exit_code = 0
    pass_cases = 0
    fail_cases = 0
    records: list[CheckRecord] = []
    for stem in stems:
        code = check_case(
            stem,
            enabled_targets,
            case_root=args.case_root,
            ignore_stdout=args.ignore_unstable_stdout,
            east3_opt_level=args.east3_opt_level,
            cpp_codegen_opt="" if args.cpp_codegen_opt is None else str(args.cpp_codegen_opt),
            cmd_timeout_sec=args.cmd_timeout_sec,
            records=records,
        )
        if code != 0:
            exit_code = code
            fail_cases += 1
        else:
            pass_cases += 1

    category_counts: dict[str, int] = {}
    for rec in records:
        category_counts[rec.category] = category_counts.get(rec.category, 0) + 1

    print(
        "SUMMARY "
        + f"cases={len(stems)} pass={pass_cases} fail={fail_cases} "
        + f"targets={','.join(sorted(enabled_targets))} "
        + f"east3_opt_level={args.east3_opt_level}"
    )
    if len(category_counts) > 0:
        print("SUMMARY_CATEGORIES")
        for category in sorted(category_counts.keys()):
            print(f"- {category}: {category_counts[category]}")

    if args.summary_json != "":
        summary_obj = {
            "case_root": args.case_root,
            "east3_opt_level": args.east3_opt_level,
            "targets": sorted(enabled_targets),
            "cases": stems,
            "case_total": len(stems),
            "case_pass": pass_cases,
            "case_fail": fail_cases,
            "category_counts": category_counts,
            "records": [
                {
                    "case": rec.case_stem,
                    "target": rec.target,
                    "category": rec.category,
                    "detail": rec.detail,
                }
                for rec in records
            ],
        }
        out_path = Path(args.summary_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(summary_obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    _save_parity_results(records, args.case_root, enabled_targets)
    _maybe_regenerate_progress()
    return exit_code


def _maybe_regenerate_progress() -> None:
    """Regenerate backend progress pages if the last generation was more than 3 minutes ago."""
    marker = ROOT / "docs" / "ja" / "progress-preview" / "backend-progress-fixture.md"
    if marker.exists() and (time.time() - marker.stat().st_mtime) < 180:
        return
    gen_script = ROOT / "tools" / "gen" / "gen_backend_progress.py"
    if not gen_script.exists():
        return
    try:
        subprocess.run(
            ["python3", str(gen_script)],
            cwd=str(ROOT),
            timeout=30,
            capture_output=True,
        )
    except Exception:
        pass


if __name__ == "__main__":
    raise SystemExit(main())
