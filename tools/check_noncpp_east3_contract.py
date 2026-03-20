#!/usr/bin/env python3
"""Check non-C++ transpiler EAST3 + 3-layer contract and regression route."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

@dataclass(frozen=True)
class Target:
    lang: str
    smoke_rel: str
    transpile_check_cmd: list[str]


TARGETS: list[Target] = [
    Target(
        "rs",
        "test/unit/toolchain/emit/rs/test_py2rs_smoke.py",
        ["python3", "tools/check_py2x_transpile.py", "--target", "rs"],
    ),
    Target(
        "cs",
        "test/unit/toolchain/emit/cs/test_py2cs_smoke.py",
        ["python3", "tools/check_py2x_transpile.py", "--target", "cs"],
    ),
    Target(
        "js",
        "test/unit/toolchain/emit/js/test_py2js_smoke.py",
        [
            "python3",
            "tools/check_py2x_transpile.py",
            "--target",
            "js",
            "--skip-east3-contract-tests",
        ],
    ),
    Target(
        "ts",
        "test/unit/toolchain/emit/ts/test_py2ts_smoke.py",
        [
            "python3",
            "tools/check_py2x_transpile.py",
            "--target",
            "ts",
            "--skip-east3-contract-tests",
        ],
    ),
    Target(
        "go",
        "test/unit/toolchain/emit/go/test_py2go_smoke.py",
        ["python3", "tools/check_py2x_transpile.py", "--target", "go"],
    ),
    Target(
        "java",
        "test/unit/toolchain/emit/java/test_py2java_smoke.py",
        ["python3", "tools/check_py2x_transpile.py", "--target", "java"],
    ),
    Target(
        "kotlin",
        "test/unit/toolchain/emit/kotlin/test_py2kotlin_smoke.py",
        ["python3", "tools/check_py2x_transpile.py", "--target", "kotlin"],
    ),
    Target(
        "swift",
        "test/unit/toolchain/emit/swift/test_py2swift_smoke.py",
        ["python3", "tools/check_py2x_transpile.py", "--target", "swift"],
    ),
    Target(
        "ruby",
        "test/unit/toolchain/emit/rb/test_py2rb_smoke.py",
        ["python3", "tools/check_py2x_transpile.py", "--target", "ruby"],
    ),
    Target(
        "lua",
        "test/unit/toolchain/emit/lua/test_py2lua_smoke.py",
        ["python3", "tools/check_py2x_transpile.py", "--target", "lua"],
    ),
    Target(
        "php",
        "test/unit/toolchain/emit/php/test_py2php_smoke.py",
        ["python3", "tools/check_py2x_transpile.py", "--target", "php"],
    ),
    Target(
        "scala",
        "test/unit/toolchain/emit/scala/test_py2scala_smoke.py",
        ["python3", "tools/check_py2x_transpile.py", "--target", "scala"],
    ),
    Target(
        "nim",
        "test/unit/toolchain/emit/nim/test_py2nim_smoke.py",
        ["python3", "tools/check_py2x_transpile.py", "--target", "nim"],
    ),
]

PY2X_REQUIRED_PATTERNS = [
    "--target",
    "--east-stage",
    'choices=["2", "3"]',
    "--object-dispatch-mode",
    "--east-stage 2 is no longer supported; use EAST3 (default).",
    "resolve_layer_options_typed(",
    "lower_ir_typed(",
    "optimize_ir_typed(",
    "emit_module_typed(",
    "build_program_artifact_typed(",
    "get_program_writer_typed(",
]

COMMON_SMOKE_PATH = "test/unit/common/test_py2x_smoke_common.py"

COMMON_SMOKE_REQUIRED_PATTERNS = [
    "test_cli_smoke_generates_output_for_all_targets",
    "test_cli_rejects_stage2_mode_for_all_targets",
    "test_load_east_defaults_to_stage3_for_non_cpp_targets",
    "test_load_east_from_json_roundtrip_for_non_cpp_targets",
    "test_add_fixture_transpile_via_py2x_for_non_cpp_targets",
    "--east-stage 2 is no longer supported; use EAST3 (default).",
]

TARGET_SMOKE_REQUIRED_PATTERNS = [
    "# Language-specific smoke suite.",
    "test_py2x_smoke_common.py",
]

TARGET_SMOKE_FORBIDDEN_PATTERNS = [
    "def test_load_east_defaults_to_stage3_entry_and_returns_east3_shape(",
    "def test_load_east_from_json(",
    "def test_cli_rejects_stage2_compat_mode(",
    "def test_cli_smoke_defaults_to_native_without_sidecar(",
    "def test_cli_smoke_defaults_to_native_and_copies_runtime(",
    "def test_cli_smoke_defaults_to_native_and_copies_runtime_tree(",
    "def test_cli_smoke_generates_cs_file(",
    "def test_cli_smoke_generates_js_file(",
    "def test_cli_smoke_generates_rs_file(",
    "def test_cli_smoke_generates_ts_file(",
    "def test_transpile_add_fixture_uses_native_output(",
    "def test_transpile_add_fixture_contains_function_signature(",
]

SMOKE_FORBIDDEN_PATTERNS = [
    "test_cli_warns_when_stage2_compat_mode_is_selected",
    "warning: --east-stage 2 is compatibility mode; default is 3.",
]

LAYER_REVERSE_IMPORT_RE_TPL = r"\b(from|import)\s+backends\.{lang}\.(lower|optimizer)\b"
LOWER_OPT_TO_EMITTER_IMPORT_RE_TPL = r"\b(from|import)\s+backends\.{lang}\.emitter\b"


def _missing_patterns(path: Path, patterns: list[str]) -> list[str]:
    if not path.exists():
        return ["<missing file>"]
    text = path.read_text(encoding="utf-8")
    return [pattern for pattern in patterns if pattern not in text]


def _present_patterns(path: Path, patterns: list[str]) -> list[str]:
    if not path.exists():
        return ["<missing file>"]
    text = path.read_text(encoding="utf-8")
    return [pattern for pattern in patterns if pattern in text]


def _run(cmd: list[str]) -> tuple[bool, str]:
    print("+", " ".join(cmd))
    cp = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if cp.returncode == 0:
        return True, ""
    msg = cp.stderr.strip() or cp.stdout.strip()
    first = msg.splitlines()[0] if msg else "unknown error"
    return False, first


def _layer_files(lang: str, layer: str) -> list[Path]:
    base = ROOT / "src" / "backends" / lang / layer
    if not base.exists():
        return []
    return sorted(path for path in base.rglob("*.py") if "__pycache__" not in path.parts)


def _check_layer_import_directions(target: Target) -> list[str]:
    failures: list[str] = []

    emitter_import_re = re.compile(
        LOWER_OPT_TO_EMITTER_IMPORT_RE_TPL.format(lang=re.escape(target.lang))
    )
    reverse_import_re = re.compile(
        LAYER_REVERSE_IMPORT_RE_TPL.format(lang=re.escape(target.lang))
    )

    for layer in ("lower", "optimizer"):
        for path in _layer_files(target.lang, layer):
            text = path.read_text(encoding="utf-8")
            m = emitter_import_re.search(text)
            if not m:
                continue
            line = text.count("\n", 0, m.start()) + 1
            snippet = text.splitlines()[line - 1].strip()
            failures.append(
                f"{target.lang}: {path.relative_to(ROOT)}:{line} imports emitter from {layer}: {snippet}"
            )

    for path in _layer_files(target.lang, "emitter"):
        text = path.read_text(encoding="utf-8")
        m = reverse_import_re.search(text)
        if not m:
            continue
        line = text.count("\n", 0, m.start()) + 1
        snippet = text.splitlines()[line - 1].strip()
        failures.append(
            f"{target.lang}: {path.relative_to(ROOT)}:{line} imports lower/optimizer from emitter: {snippet}"
        )
    return failures


def main() -> int:
    ap = argparse.ArgumentParser(description="check non-cpp EAST3 defaults/warnings and transpile route")
    ap.add_argument(
        "--skip-transpile",
        action="store_true",
        help="only check static source/smoke contracts",
    )
    args = ap.parse_args()

    failures: list[str] = []
    py2x_path = ROOT / "src" / "py2x.py"
    py2x_text = py2x_path.read_text(encoding="utf-8") if py2x_path.exists() else ""
    missing_py2x = _missing_patterns(py2x_path, PY2X_REQUIRED_PATTERNS)
    if missing_py2x:
        failures.append(f"py2x: src/py2x.py missing {missing_py2x}")

    common_smoke_path = ROOT / COMMON_SMOKE_PATH
    missing_common_smoke = _missing_patterns(common_smoke_path, COMMON_SMOKE_REQUIRED_PATTERNS)
    if missing_common_smoke:
        failures.append(f"common-smoke: {COMMON_SMOKE_PATH} missing {missing_common_smoke}")
    present_common_forbidden = _present_patterns(common_smoke_path, SMOKE_FORBIDDEN_PATTERNS)
    if present_common_forbidden:
        failures.append(
            f"common-smoke: {COMMON_SMOKE_PATH} contains forbidden {present_common_forbidden}"
        )

    for target in TARGETS:
        target_token_re = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(target.lang)}(?![A-Za-z0-9_])")
        if target_token_re.search(py2x_text) is None:
            failures.append(f"py2x: target literal missing for {target.lang}")
        smoke_path = ROOT / target.smoke_rel
        missing_smoke = _missing_patterns(smoke_path, TARGET_SMOKE_REQUIRED_PATTERNS)
        if missing_smoke:
            failures.append(f"{target.lang}: {target.smoke_rel} missing {missing_smoke}")
        present_smoke = _present_patterns(
            smoke_path,
            TARGET_SMOKE_FORBIDDEN_PATTERNS + SMOKE_FORBIDDEN_PATTERNS,
        )
        if present_smoke:
            failures.append(
                f"{target.lang}: {target.smoke_rel} contains forbidden {present_smoke}"
            )
        failures.extend(_check_layer_import_directions(target))

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        return 1
    print(f"[OK] static contract checks passed for {len(TARGETS)} non-cpp transpilers")

    if args.skip_transpile:
        return 0

    transpile_failures: list[str] = []
    for target in TARGETS:
        ok, msg = _run(target.transpile_check_cmd)
        if not ok:
            transpile_failures.append(f"{target.lang}: {msg}")
    if transpile_failures:
        for failure in transpile_failures:
            print(f"FAIL {failure}")
        return 1
    print(f"[OK] transpile checks passed for {len(TARGETS)} non-cpp transpilers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
