#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import os
from dataclasses import dataclass
from pathlib import Path
import subprocess
import tempfile
import time


ROOT = Path(__file__).resolve().parents[2]
DOC_JA = ROOT / "docs" / "ja" / "language" / "backend-test-matrix.md"
DOC_EN = ROOT / "docs" / "en" / "language" / "backend-test-matrix.md"
BACKEND_TEST_ROOT = ROOT / "test" / "unit" / "backends"
BEGIN_MARKER = "<!-- BEGIN BACKEND TEST MATRIX TABLE -->"
END_MARKER = "<!-- END BACKEND TEST MATRIX TABLE -->"
BEGIN_DETAILS_MARKER = "<!-- BEGIN BACKEND TEST MATRIX DETAILS -->"
END_DETAILS_MARKER = "<!-- END BACKEND TEST MATRIX DETAILS -->"


@dataclass(frozen=True)
class BackendSpec:
    key: str
    label: str
    suite_dir: str
    smoke_file: str
    cli_target: str
    output_ext: str


@dataclass(frozen=True)
class SuiteSpec:
    key: str
    label: str
    kind: str


@dataclass
class SuiteResult:
    backend: str
    suite: str
    status: str
    duration_sec: float
    detail: str
    command: tuple[str, ...]


BACKENDS: tuple[BackendSpec, ...] = (
    BackendSpec("cpp", "cpp", "cpp", "test_py2cpp_smoke.py", "cpp", ".cpp"),
    BackendSpec("rs", "rs", "rs", "test_py2rs_smoke.py", "rs", ".rs"),
    BackendSpec("cs", "cs", "cs", "test_py2cs_smoke.py", "cs", ".cs"),
    BackendSpec("js", "js", "js", "test_py2js_smoke.py", "js", ".js"),
    BackendSpec("ts", "ts", "ts", "test_py2ts_smoke.py", "ts", ".ts"),
    BackendSpec("go", "go", "go", "test_py2go_smoke.py", "go", ".go"),
    BackendSpec("java", "java", "java", "test_py2java_smoke.py", "java", ".java"),
    BackendSpec("swift", "swift", "swift", "test_py2swift_smoke.py", "swift", ".swift"),
    BackendSpec("kt", "kt", "kotlin", "test_py2kotlin_smoke.py", "kotlin", ".kt"),
    BackendSpec("rb", "rb", "rb", "test_py2rb_smoke.py", "ruby", ".rb"),
    BackendSpec("lua", "lua", "lua", "test_py2lua_smoke.py", "lua", ".lua"),
    BackendSpec("scala", "scala", "scala", "test_py2scala_smoke.py", "scala", ".scala"),
    BackendSpec("php", "php", "php", "test_py2php_smoke.py", "php", ".php"),
    BackendSpec("nim", "nim", "nim", "test_py2nim_smoke.py", "nim", ".nim"),
)

SUMMARY_SUITES: tuple[SuiteSpec, ...] = (
    SuiteSpec("smoke", "Primary Smoke", "smoke"),
    SuiteSpec("backend_dir", "Backend Dir Discover", "backend_dir"),
    SuiteSpec("shared_starred", "Shared Starred Smoke", "shared_starred"),
)


def _build_pythonpath() -> str:
    entries = [
        str(ROOT / "src"),
        str(ROOT / "test" / "unit"),
        str(BACKEND_TEST_ROOT),
    ]
    old = os.environ.get("PYTHONPATH", "")
    return os.pathsep.join(entries + ([old] if old else []))


def _build_unittest_command(backend: BackendSpec, pattern: str) -> tuple[str, ...]:
    return (
        "python3",
        "-m",
        "unittest",
        "discover",
        "-s",
        f"tools/unittest/emit/{backend.suite_dir}",
        "-p",
        pattern,
    )


def _classify_failure(output: str) -> str:
    lower = output.lower()
    toolchain_needles = (
        "toolchain missing",
        "command not found",
        "not installed",
        "no such file or directory: 'rustc'",
        "no such file or directory: 'cargo'",
        "no such file or directory: 'mcs'",
        "no such file or directory: 'mono'",
        "no such file or directory: 'node'",
        "no such file or directory: 'tsc'",
        "no such file or directory: 'go'",
        "no such file or directory: 'javac'",
        "no such file or directory: 'java'",
        "no such file or directory: 'swiftc'",
        "no such file or directory: 'kotlinc'",
        "no such file or directory: 'ruby'",
        "no such file or directory: 'lua'",
        "no such file or directory: 'scalac'",
        "no such file or directory: 'php'",
        "no such file or directory: 'nim'",
    )
    if any(needle in lower for needle in toolchain_needles):
        return "toolchain_missing"
    return "fail"


def _extract_detail(output: str) -> str:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    for prefix in (
        "RuntimeError:",
        "AssertionError:",
        "TypeError:",
        "ValueError:",
        "ImportError:",
        "ModuleNotFoundError:",
        "FileNotFoundError:",
        "AttributeError:",
        "KeyError:",
        "IndexError:",
    ):
        for line in lines:
            if line.startswith(prefix):
                return line
    for line in lines:
        if line.startswith(("ERROR:", "FAIL:")):
            return line
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if all(ch in ".FEsx" for ch in stripped):
            continue
        if stripped.startswith(("=", "-", "Traceback", "Ran ", "OK", "FAILED ")):
            continue
        return stripped
    return "no detail"


def _run_process(
    cmd: tuple[str, ...],
    suite_key: str,
    backend: BackendSpec,
    timeout_sec: int,
    detail_label: str,
) -> SuiteResult:
    env = os.environ.copy()
    env["PYTHONPATH"] = _build_pythonpath()
    start = time.monotonic()
    try:
        proc = subprocess.run(
            cmd,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            env=env,
        )
    except subprocess.TimeoutExpired:
        duration = time.monotonic() - start
        return SuiteResult(
            backend=backend.key,
            suite=suite_key,
            status="timeout",
            duration_sec=duration,
            detail=f"timeout after {timeout_sec}s",
            command=cmd,
        )

    duration = time.monotonic() - start
    output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    if proc.returncode == 0:
        return SuiteResult(
            backend=backend.key,
            suite=suite_key,
            status="pass",
            duration_sec=duration,
            detail=detail_label,
            command=cmd,
        )
    return SuiteResult(
        backend=backend.key,
        suite=suite_key,
        status=_classify_failure(output),
        duration_sec=duration,
        detail=_extract_detail(output),
        command=cmd,
    )


def _run_shared_starred_smoke(backend: BackendSpec, timeout_sec: int) -> SuiteResult:
    matches = sorted((ROOT / "test" / "fixtures").rglob("starred_call_tuple_basic.py"))
    if not matches:
        return SuiteResult(
            backend=backend.key,
            suite="shared_starred",
            status="fail",
            duration_sec=0.0,
            detail="missing fixture: starred_call_tuple_basic.py",
            command=(),
        )
    fixture = matches[0]
    with tempfile.TemporaryDirectory() as td:
        output_path = Path(td) / f"starred_call_tuple_basic_{backend.key}{backend.output_ext}"
        cmd = (
            "python3",
            "src/pytra-cli.py",
            "--target",
            backend.cli_target,
            str(fixture),
            "-o",
            str(output_path),
        )
        result = _run_process(
            cmd,
            suite_key="shared_starred",
            backend=backend,
            timeout_sec=timeout_sec,
            detail_label="test_py2starred_smoke.py equivalent",
        )
        if result.status != "pass":
            return result
        text = output_path.read_text(encoding="utf-8")
        if "*rgb" in text:
            result.status = "fail"
            result.detail = "generated code still contains *rgb"
            return result
        if text.strip() and "mix_rgb" not in text:
            result.status = "fail"
            result.detail = "generated code lost mix_rgb call"
            return result
        return result


def _run_suite(backend: BackendSpec, suite: SuiteSpec, timeout_sec: int) -> SuiteResult:
    if suite.kind == "backend_dir":
        return _run_process(
            _build_unittest_command(backend, "*.py"),
            suite_key=suite.key,
            backend=backend,
            timeout_sec=timeout_sec,
            detail_label="all backend-owned modules",
        )
    if suite.kind == "shared_starred":
        return _run_shared_starred_smoke(backend, timeout_sec)
    if suite.kind == "module":
        return _run_process(
            _build_unittest_command(backend, suite.label),
            suite_key=suite.key,
            backend=backend,
            timeout_sec=timeout_sec,
            detail_label=suite.label,
        )
    return _run_process(
        _build_unittest_command(backend, backend.smoke_file),
        suite_key=suite.key,
        backend=backend,
        timeout_sec=timeout_sec,
        detail_label=backend.smoke_file,
    )


def _cell_label(status: str) -> str:
    return {
        "pass": "PASS",
        "fail": "FAIL",
        "toolchain_missing": "TM",
        "timeout": "TO",
    }[status]


def _cell_icon(status: str) -> str:
    return {
        "pass": "🟩",
        "fail": "🟥",
        "toolchain_missing": "🟨",
        "timeout": "🟪",
    }[status]


def _discover_module_patterns() -> dict[str, tuple[str, ...]]:
    return {
        backend.key: tuple(
            path.name
            for path in sorted((BACKEND_TEST_ROOT / backend.suite_dir).glob("test_*.py"))
        )
        for backend in BACKENDS
    }


def _render_matrix(results: dict[tuple[str, str], SuiteResult]) -> str:
    lines: list[str] = []
    lines.append(BEGIN_MARKER)
    lines.append("")
    header = ["suite"]
    for backend in BACKENDS:
        header.append(backend.label)
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(["---"] * len(header)) + " |")
    for suite in SUMMARY_SUITES:
        row = [suite.label]
        for backend in BACKENDS:
            result = results[(backend.key, suite.key)]
            row.append(f"{_cell_icon(result.status)} `{_cell_label(result.status)}`")
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    lines.append(END_MARKER)
    return "\n".join(lines)


def _render_details(
    summary_results: dict[tuple[str, str], SuiteResult],
    module_results: dict[tuple[str, str], SuiteResult],
    module_patterns: dict[str, tuple[str, ...]],
    locale: str,
) -> str:
    localized = {
        "ja": {
            "execution": "## 実行詳細",
            "scope": "## Scope",
            "scope_rows": (
                "- overview matrix は `Primary Smoke` / `Backend Dir Discover` / `Shared Starred Smoke` の 3 行です。",
                "- `Module Detail` は `tools/unittest/emit/<backend>/test_*.py` を 1 module ずつ実行した結果です。",
                "- `Shared Starred Smoke` は `tools/unittest/emit/test_py2starred_smoke.py` と同じ fixture/assertion を backend ごとに再実行しています。",
                "- `tools/unittest/emit/` 直下の support helper (`*_support.py`) は実行対象に含めません。",
            ),
        },
        "en": {
            "execution": "## Execution Details",
            "scope": "## Scope",
            "scope_rows": (
                "- The overview matrix uses three rows: `Primary Smoke`, `Backend Dir Discover`, and `Shared Starred Smoke`.",
                "- `Module Detail` runs each `tools/unittest/emit/<backend>/test_*.py` module individually.",
                "- `Shared Starred Smoke` re-runs the same fixture and assertions as `tools/unittest/emit/test_py2starred_smoke.py` for each backend.",
                "- Support helpers under `tools/unittest/emit/` (`*_support.py`) are excluded from execution.",
            ),
        },
    }[locale]
    lines: list[str] = []
    lines.append("## Backend Summary")
    lines.append("")
    lines.append("| backend | passing modules | failing modules | toolchain missing | timeout | total modules |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
    for backend in BACKENDS:
        counts = {"pass": 0, "fail": 0, "toolchain_missing": 0, "timeout": 0}
        for pattern in module_patterns[backend.key]:
            counts[module_results[(backend.key, pattern)].status] += 1
        total = len(module_patterns[backend.key])
        lines.append(
            f"| {backend.label} | {counts['pass']} | {counts['fail']} | {counts['toolchain_missing']} | {counts['timeout']} | {total} |"
        )
    lines.append("")
    lines.append(localized["execution"])
    lines.append("")
    lines.append("### Summary Suites")
    lines.append("")
    lines.append("| backend | suite | status | sec | detail |")
    lines.append("| --- | --- | --- | ---: | --- |")
    for backend in BACKENDS:
        for suite in SUMMARY_SUITES:
            result = summary_results[(backend.key, suite.key)]
            lines.append(
                "| "
                + " | ".join(
                    (
                        backend.label,
                        suite.label,
                        result.status,
                        f"{result.duration_sec:.1f}",
                        result.detail.replace("|", "/"),
                    )
                )
                + " |"
            )
    lines.append("")
    lines.append("### Module Detail")
    lines.append("")
    lines.append("| backend | module | status | sec | detail |")
    lines.append("| --- | --- | --- | ---: | --- |")
    for backend in BACKENDS:
        for pattern in module_patterns[backend.key]:
            result = module_results[(backend.key, pattern)]
            lines.append(
                "| "
                + " | ".join(
                    (
                        backend.label,
                        f"`{backend.suite_dir}/{pattern}`",
                        result.status,
                        f"{result.duration_sec:.1f}",
                        result.detail.replace("|", "/"),
                    )
                )
                + " |"
            )
    lines.append("")
    lines.append(localized["scope"])
    lines.append("")
    lines.extend(localized["scope_rows"])
    return "\n".join(lines)


def _replace_block(text: str, begin: str, end: str, replacement: str) -> str:
    start = text.index(begin)
    finish = text.index(end) + len(end)
    return text[:start] + replacement + text[finish:]


def refresh_doc(timeout_sec: int, max_workers: int) -> dict[tuple[str, str], SuiteResult]:
    module_patterns = _discover_module_patterns()
    summary_jobs = [(backend, suite) for suite in SUMMARY_SUITES for backend in BACKENDS]
    module_jobs = [
        (backend, pattern)
        for backend in BACKENDS
        for pattern in module_patterns[backend.key]
    ]
    summary_results: dict[tuple[str, str], SuiteResult] = {}
    module_results: dict[tuple[str, str], SuiteResult] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        summary_future_map = {
            executor.submit(_run_suite, backend, suite, timeout_sec): (backend, suite)
            for backend, suite in summary_jobs
        }
        module_future_map = {
            executor.submit(
                _run_suite,
                backend,
                SuiteSpec(pattern, pattern, "module"),
                timeout_sec,
            ): (backend, pattern)
            for backend, pattern in module_jobs
        }
        for future in concurrent.futures.as_completed(summary_future_map):
            backend, suite = summary_future_map[future]
            summary_results[(backend.key, suite.key)] = future.result()
        for future in concurrent.futures.as_completed(module_future_map):
            backend, pattern = module_future_map[future]
            module_results[(backend.key, pattern)] = future.result()

    for locale, doc_path in (("ja", DOC_JA), ("en", DOC_EN)):
        doc_text = doc_path.read_text(encoding="utf-8")
        doc_text = _replace_block(doc_text, BEGIN_MARKER, END_MARKER, _render_matrix(summary_results))
        doc_text = _replace_block(
            doc_text,
            BEGIN_DETAILS_MARKER,
            END_DETAILS_MARKER,
            BEGIN_DETAILS_MARKER
            + "\n"
            + _render_details(summary_results, module_results, module_patterns, locale)
            + "\n"
            + END_DETAILS_MARKER,
        )
        doc_path.write_text(doc_text, encoding="utf-8")
    return summary_results


def main() -> int:
    ap = argparse.ArgumentParser(description="refresh backend test matrix doc from backend-owned unittest suites")
    ap.add_argument("--timeout-sec", type=int, default=300)
    ap.add_argument("--max-workers", type=int, default=4)
    args = ap.parse_args()
    refresh_doc(timeout_sec=args.timeout_sec, max_workers=args.max_workers)
    print(
        "[OK] refreshed "
        + f"{DOC_JA.relative_to(ROOT)} and {DOC_EN.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
