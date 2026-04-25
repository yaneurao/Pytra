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

from toolchain.misc.target_profiles import get_target_profile, list_parity_targets

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = ROOT / "test" / "fixture" / "source" / "py"
SAMPLE_ROOT = ROOT / "sample" / "py"
STDLIB_ROOT = ROOT / "test" / "stdlib" / "source" / "py"
ARTIFACT_OPTIONAL_TARGETS: set[str] = set()
_LOCAL_TOOL_FALLBACKS: dict[str, tuple[Path, ...]] = {
    "go": (ROOT / "work" / "tmp" / "go-toolchain" / "bin" / "go",),
    "rustc": (Path("/usr/local/cargo/bin/rustc"),),
    "cargo": (Path("/usr/local/cargo/bin/cargo"),),
    "pwsh": (Path("/tmp/pwsh/pwsh"),),
}

# Backend-declared unsupported fixtures are tracked explicitly.
# FAIL is recorded as FAIL in .parity-results/ and shown in progress matrix.
_LANG_UNSUPPORTED_FIXTURES: dict[str, set[str]] = {}

__all__ = [
    "ROOT",
    "shutil",
    "FIXTURE_ROOT",
    "SAMPLE_ROOT",
    "STDLIB_ROOT",
    "Target",
    "CheckRecord",
    "_LANG_UNSUPPORTED_FIXTURES",
    "_LOCAL_TOOL_FALLBACKS",
    "normalize",
    "run_shell",
    "_tool_env_for_target",
    "can_run",
    "_normalize_output_for_compare",
    "_target_output_text",
    "_parse_output_path",
    "_resolve_output_path",
    "_safe_unlink",
    "_file_crc32",
    "_file_size_normalized",
    "_crc32_hex",
    "_run_cpp_emit_dir",
    "_purge_case_artifacts",
    "find_case_path",
    "collect_sample_case_stems",
    "collect_fixture_case_stems",
    "collect_stdlib_case_stems",
    "resolve_case_stems",
    "_save_parity_results",
    "_append_parity_changelog",
    "_maybe_refresh_selfhost_python",
    "_maybe_regenerate_progress",
]


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
    if target.name == "cs":
        has_mono = True
        for tool in target.needs:
            if tool in ("mcs", "mono"):
                if _resolve_tool_path(tool) == "":
                    has_mono = False
        if has_mono:
            return True
        return _resolve_tool_path("dotnet") != ""
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

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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

    if case_root == "sample":
        _maybe_regenerate_benchmark()


def _maybe_regenerate_benchmark() -> None:
    """Auto-run gen_sample_benchmark.py if >3 minutes since last generation."""
    marker = ROOT / "sample-preview" / "README-ja.md"
    if marker.exists() and (time.time() - marker.stat().st_mtime) < 180:
        return
    gen_script = ROOT / "tools" / "gen" / "gen_sample_benchmark.py"
    if not gen_script.exists():
        return
    # Only run if benchmark data exists
    if not (ROOT / ".parity-results" / "python_sample.json").exists():
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


_CHANGELOG_PATHS = [
    ROOT / "docs" / "ja" / "progress-preview" / "changelog.md",
    ROOT / "docs" / "en" / "progress-preview" / "changelog.md",
]

_CHANGELOG_HEADERS: dict[str, str] = {
    "ja": (
        '<a href="../../en/progress-preview/changelog.md">\n'
        '  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">\n'
        '</a>\n\n'
        "# Parity Changelog\n\n"
        "| 日時 | 言語 | case-root | 変化 | 備考 |\n"
        "|---|---|---|---|---|\n"
    ),
    "en": (
        '<a href="../../ja/progress-preview/changelog.md">\n'
        '  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">\n'
        '</a>\n\n'
        "# Parity Changelog\n\n"
        "| Date | Language | case-root | Change | Note |\n"
        "|---|---|---|---|---|\n"
    ),
}


_CHANGELOG_COOLDOWN_SEC = 120  # 2 minutes: prevent multiple agents from writing in the same window


def _append_parity_changelog(target: str, case_root: str, prev_pass: int, curr_pass: int, now: str) -> None:
    """Append a row to progress-preview/changelog.md when PASS count changes.

    changelog.md は全エージェント共有の単一ファイルのため、fcntl.flock で排他制御する。
    クールダウン判定は lock 内で行い、待機中のエージェントが続けて書き込むのを防ぐ。
    クールダウンは target+case_root 単位で管理する。
    """
    import fcntl

    diff = curr_pass - prev_pass
    if diff == 0:
        return
    sign = "+" if diff > 0 else ""
    note = "regression" if diff < 0 else ""
    ts = now[:16]  # "YYYY-MM-DDTHH:MM"
    row = f"| {ts} | {target} | {case_root} | {prev_pass}→{curr_pass} ({sign}{diff}) | {note} |"
    sep_marker = "|---|---|---|---|---|"
    lock_path = ROOT / ".parity-results" / ".changelog.lock"
    marker_path = ROOT / ".parity-results" / f".changelog_last_{target}_{case_root}"
    try:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with open(lock_path, "w") as lf:
            fcntl.flock(lf, fcntl.LOCK_EX)
            # クールダウン判定は lock 内で行う。
            # lock 待ち中のエージェントはここで「まだ期限切れでない」と判定してスキップする。
            if marker_path.exists() and time.time() - marker_path.stat().st_mtime < _CHANGELOG_COOLDOWN_SEC:
                return
            for cl_path in _CHANGELOG_PATHS:
                lang = "en" if "/en/" in cl_path.as_posix() else "ja"
                header = _CHANGELOG_HEADERS[lang]
                try:
                    cl_path.parent.mkdir(parents=True, exist_ok=True)
                    if not cl_path.exists():
                        content = header + row + "\n"
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
            marker_path.touch()
    except Exception:
        pass


def main() -> int:
    from runtime_parity_check_fast import main as fast_main  # type: ignore

    return fast_main()


def _maybe_refresh_selfhost_python() -> None:
    """Auto-re-aggregate selfhost_python.json if >2 minutes since last update.

    Reads existing .parity-results/*.json and writes selfhost_python.json so
    that gen_backend_progress.py always has up-to-date selfhost matrix data.
    呼び出しは _maybe_regenerate_progress() の前に置くこと。
    こうすることで「今サイクルの parity 結果 → selfhost_python.json → progress summary」
    の順に反映され、1サイクル遅延なく最新状態が summary に出る。
    クールダウンは changelog 書き込みと同じ 120 秒に統一。
    """
    marker = ROOT / ".parity-results" / "selfhost_python.json"
    if marker.exists() and (time.time() - marker.stat().st_mtime) < _CHANGELOG_COOLDOWN_SEC:
        return
    run_script = ROOT / "tools" / "run" / "run_selfhost_parity.py"
    if not run_script.exists():
        return
    parity_dir = ROOT / ".parity-results"
    if not parity_dir.exists() or not any(parity_dir.glob("*_sample.json")):
        return
    try:
        subprocess.run(
            ["python3", str(run_script), "--selfhost-lang", "python"],
            cwd=str(ROOT),
            timeout=60,
            capture_output=True,
        )
    except Exception:
        pass


def _maybe_regenerate_progress() -> None:
    """Regenerate backend progress pages if parity results are newer than the last generation."""
    marker = ROOT / ".parity-results" / ".progress_generated"
    parity_dir = ROOT / ".parity-results"
    gen_script = ROOT / "tools" / "gen" / "gen_backend_progress.py"
    if not gen_script.exists():
        return
    # Skip if marker exists and no parity result file is newer than it
    if marker.exists():
        marker_mtime = marker.stat().st_mtime
        has_newer = False
        if parity_dir.exists():
            for p in parity_dir.iterdir():
                if p.name.startswith("."):
                    continue
                if p.stat().st_mtime > marker_mtime:
                    has_newer = True
                    break
        if not has_newer:
            return
    try:
        subprocess.run(
            ["python3", str(gen_script)],
            cwd=str(ROOT),
            timeout=30,
            capture_output=True,
        )
        # Update marker timestamp
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(str(time.time()), encoding="utf-8")
    except Exception:
        pass


if __name__ == "__main__":
    raise SystemExit(main())
