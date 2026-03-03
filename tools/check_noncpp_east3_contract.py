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
    src_rel: str
    smoke_rel: str
    transpile_check_rel: str
    lower_import_pattern: str
    optimizer_import_pattern: str
    lower_call_pattern: str
    optimizer_call_pattern: str


TARGETS: list[Target] = [
    Target(
        "rs",
        "src/py2rs.py",
        "test/unit/test_py2rs_smoke.py",
        "tools/check_py2rs_transpile.py",
        "from backends.rs.lower import lower_east3_to_rs_ir",
        "from backends.rs.optimizer import optimize_rs_ir",
        "lower_east3_to_rs_ir(",
        "optimize_rs_ir(",
    ),
    Target(
        "cs",
        "src/py2cs.py",
        "test/unit/test_py2cs_smoke.py",
        "tools/check_py2cs_transpile.py",
        "from backends.cs.lower import lower_east3_to_cs_ir",
        "from backends.cs.optimizer import optimize_cs_ir",
        "lower_east3_to_cs_ir(",
        "optimize_cs_ir(",
    ),
    Target(
        "js",
        "src/py2js.py",
        "test/unit/test_py2js_smoke.py",
        "tools/check_py2js_transpile.py",
        "from backends.js.lower import lower_east3_to_js_ir",
        "from backends.js.optimizer import optimize_js_ir",
        "lower_east3_to_js_ir(",
        "optimize_js_ir(",
    ),
    Target(
        "ts",
        "src/py2ts.py",
        "test/unit/test_py2ts_smoke.py",
        "tools/check_py2ts_transpile.py",
        "from backends.ts.lower import lower_east3_to_ts_ir",
        "from backends.ts.optimizer import optimize_ts_ir",
        "lower_east3_to_ts_ir(",
        "optimize_ts_ir(",
    ),
    Target(
        "go",
        "src/py2go.py",
        "test/unit/test_py2go_smoke.py",
        "tools/check_py2go_transpile.py",
        "from backends.go.lower import lower_east3_to_go_ir",
        "from backends.go.optimizer import optimize_go_ir",
        "lower_east3_to_go_ir(",
        "optimize_go_ir(",
    ),
    Target(
        "java",
        "src/py2java.py",
        "test/unit/test_py2java_smoke.py",
        "tools/check_py2java_transpile.py",
        "from backends.java.lower import lower_east3_to_java_ir",
        "from backends.java.optimizer import optimize_java_ir",
        "lower_east3_to_java_ir(",
        "optimize_java_ir(",
    ),
    Target(
        "kotlin",
        "src/py2kotlin.py",
        "test/unit/test_py2kotlin_smoke.py",
        "tools/check_py2kotlin_transpile.py",
        "from backends.kotlin.lower import lower_east3_to_kotlin_ir",
        "from backends.kotlin.optimizer import optimize_kotlin_ir",
        "lower_east3_to_kotlin_ir(",
        "optimize_kotlin_ir(",
    ),
    Target(
        "swift",
        "src/py2swift.py",
        "test/unit/test_py2swift_smoke.py",
        "tools/check_py2swift_transpile.py",
        "from backends.swift.lower import lower_east3_to_swift_ir",
        "from backends.swift.optimizer import optimize_swift_ir",
        "lower_east3_to_swift_ir(",
        "optimize_swift_ir(",
    ),
    Target(
        "ruby",
        "src/py2rb.py",
        "test/unit/test_py2rb_smoke.py",
        "tools/check_py2rb_transpile.py",
        "from backends.ruby.lower import lower_east3_to_ruby_ir",
        "from backends.ruby.optimizer import optimize_ruby_ir",
        "lower_east3_to_ruby_ir(",
        "optimize_ruby_ir(",
    ),
    Target(
        "lua",
        "src/py2lua.py",
        "test/unit/test_py2lua_smoke.py",
        "tools/check_py2lua_transpile.py",
        "from backends.lua.lower import lower_east3_to_lua_ir",
        "from backends.lua.optimizer import optimize_lua_ir",
        "lower_east3_to_lua_ir(",
        "optimize_lua_ir(",
    ),
    Target(
        "php",
        "src/py2php.py",
        "test/unit/test_py2php_smoke.py",
        "tools/check_py2php_transpile.py",
        "from backends.php.lower import lower_east3_to_php_ir",
        "from backends.php.optimizer import optimize_php_ir",
        "lower_east3_to_php_ir(",
        "optimize_php_ir(",
    ),
    Target(
        "scala",
        "src/py2scala.py",
        "test/unit/test_py2scala_smoke.py",
        "tools/check_py2scala_transpile.py",
        "from backends.scala.lower import lower_east3_to_scala_ir",
        "from backends.scala.optimizer import optimize_scala_ir",
        "lower_east3_to_scala_ir(",
        "optimize_scala_ir(",
    ),
]

SOURCE_REQUIRED_PATTERNS = [
    "--east-stage",
    'choices=["2", "3"]',
    "--object-dispatch-mode",
    "load_east3_document",
    'east_stage = "3"',
    "--east-stage 2 is no longer supported; use EAST3 (default).",
]

SOURCE_FORBIDDEN_PATTERNS = [
    "load_east_document_compat",
    "normalize_east3_to_legacy",
    "warning: --east-stage 2 is compatibility mode; default is 3.",
]

LEGACY_RUNTIME_CALL_PATTERNS: dict[str, str] = {
    "rs": "_copy_rust_runtime(output_path)",
    "js": "write_js_runtime_shims(output_path.parent)",
    "ts": "write_js_runtime_shims(output_path.parent)",
    "go": "_copy_go_runtime(output_path)",
    "java": "_copy_java_runtime(output_path)",
    "kotlin": "_copy_kotlin_runtime(output_path)",
    "swift": "_copy_swift_runtime(output_path)",
    "ruby": "_copy_ruby_runtime(output_path)",
    "lua": "_copy_lua_runtime(output_path)",
    "php": "_copy_php_runtime(output_path)",
    "scala": "_copy_scala_runtime(output_path)",
}

PY2X_REQUIRED_PATTERNS = [
    "--target",
    "--east-stage",
    'choices=["2", "3"]',
    "--object-dispatch-mode",
    "--east-stage 2 is no longer supported; use EAST3 (default).",
    "resolve_layer_options(",
    "lower_ir(",
    "optimize_ir(",
    "emit_source(",
]

SMOKE_REQUIRED_PATTERNS = [
    "test_load_east_defaults_to_stage3_entry_and_returns_east3_shape",
    "test_cli_rejects_stage2_compat_mode",
    "--east-stage 2 is no longer supported; use EAST3 (default).",
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
    missing_py2x = _missing_patterns(py2x_path, PY2X_REQUIRED_PATTERNS)
    if missing_py2x:
        failures.append(f"py2x: src/py2x.py missing {missing_py2x}")

    for target in TARGETS:
        src_path = ROOT / target.src_rel
        smoke_path = ROOT / target.smoke_rel
        src_text = src_path.read_text(encoding="utf-8") if src_path.exists() else ""
        wrapper_patterns = [
            "from toolchain.compiler.py2x_wrapper import run_py2x_for_target",
            f'run_py2x_for_target("{target.lang}"',
        ]
        is_wrapper = src_text != "" and all(pattern in src_text for pattern in wrapper_patterns)
        if is_wrapper:
            missing_wrapper = _missing_patterns(src_path, wrapper_patterns)
            if missing_wrapper:
                failures.append(f"{target.lang}: {target.src_rel} missing {missing_wrapper}")
            present_legacy_calls = _present_patterns(
                src_path,
                [
                    target.lower_call_pattern,
                    target.optimizer_call_pattern,
                ],
            )
            if present_legacy_calls:
                failures.append(
                    f"{target.lang}: {target.src_rel} wrapper contains legacy lower/optimizer calls {present_legacy_calls}"
                )
            runtime_call_pattern = LEGACY_RUNTIME_CALL_PATTERNS.get(target.lang, "")
            if runtime_call_pattern != "" and runtime_call_pattern in src_text:
                failures.append(
                    f"{target.lang}: {target.src_rel} wrapper contains legacy runtime copy call {runtime_call_pattern}"
                )
        else:
            missing_src = _missing_patterns(src_path, SOURCE_REQUIRED_PATTERNS)
            missing_src.extend(
                _missing_patterns(
                    src_path,
                    [
                        target.lower_import_pattern,
                        target.optimizer_import_pattern,
                        target.lower_call_pattern,
                        target.optimizer_call_pattern,
                    ],
                )
            )
            if missing_src:
                failures.append(f"{target.lang}: {target.src_rel} missing {missing_src}")

            if src_path.exists():
                lower_pos = src_text.find(target.lower_call_pattern)
                optimizer_pos = src_text.find(target.optimizer_call_pattern)
                if lower_pos >= 0 and optimizer_pos >= 0 and lower_pos > optimizer_pos:
                    failures.append(
                        f"{target.lang}: {target.src_rel} lower/optimizer call order reversed"
                    )

        present_src = _present_patterns(src_path, SOURCE_FORBIDDEN_PATTERNS)
        if present_src:
            failures.append(f"{target.lang}: {target.src_rel} contains forbidden {present_src}")
        missing_smoke = _missing_patterns(smoke_path, SMOKE_REQUIRED_PATTERNS)
        if missing_smoke:
            failures.append(f"{target.lang}: {target.smoke_rel} missing {missing_smoke}")
        present_smoke = _present_patterns(smoke_path, SMOKE_FORBIDDEN_PATTERNS)
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
        ok, msg = _run(["python3", target.transpile_check_rel])
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
