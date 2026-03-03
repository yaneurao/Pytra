#!/usr/bin/env python3
"""EAST -> Kotlin transpiler CLI."""

from __future__ import annotations

from pytra.std.typing import Any

from backends.kotlin.emitter import load_kotlin_profile, transpile_to_kotlin, transpile_to_kotlin_native
from backends.kotlin.lower import lower_east3_to_kotlin_ir
from backends.kotlin.optimizer import optimize_kotlin_ir
from pytra.compiler.py2x_wrapper import run_py2x_for_target
from pytra.compiler.transpile_cli import add_common_transpile_args, load_east3_document
from pytra.std import argparse
from pytra.std.pathlib import Path
from pytra.std import sys


def load_east(
    input_path: Path,
    parser_backend: str = "self_hosted",
    east_stage: str = "3",
    object_dispatch_mode: str = "native",
    east3_opt_level: str = "1",
    east3_opt_pass: str = "",
    dump_east3_before_opt: str = "",
    dump_east3_after_opt: str = "",
    dump_east3_opt_trace: str = "",
) -> dict[str, Any]:
    """`.py` / `.json` を EAST ドキュメントへ読み込む。"""
    if east_stage != "3":
        raise RuntimeError("unsupported east_stage: " + east_stage)
    doc3 = load_east3_document(
        input_path,
        parser_backend=parser_backend,
        object_dispatch_mode=object_dispatch_mode,
        east3_opt_level=east3_opt_level,
        east3_opt_pass=east3_opt_pass,
        dump_east3_before_opt=dump_east3_before_opt,
        dump_east3_after_opt=dump_east3_after_opt,
        dump_east3_opt_trace=dump_east3_opt_trace,
        target_lang="kotlin",
    )
    return doc3 if isinstance(doc3, dict) else {}


def _default_output_path(input_path: Path) -> Path:
    """入力パスから既定の `.kt` 出力先を決定する。"""
    out = str(input_path)
    if out.endswith(".py"):
        out = out[:-3] + ".kt"
    elif out.endswith(".json"):
        out = out[:-5] + ".kt"
    else:
        out = out + ".kt"
    return Path(out)


def _arg_get_str(args: dict[str, Any], key: str, default_value: str = "") -> str:
    """argparse(dict) から文字列値を取り出す。"""
    if key not in args:
        return default_value
    val = args[key]
    if isinstance(val, str):
        return val
    return default_value


def _kotlin_runtime_source_path() -> Path:
    """Kotlin runtime 正本のソースファイルパスを返す。"""
    return Path(__file__).resolve().parent / "runtime" / "kotlin" / "pytra" / "py_runtime.kt"


def _copy_kotlin_runtime(output_path: Path) -> None:
    """生成先ディレクトリへ Kotlin runtime を配置する。"""
    runtime_src = _kotlin_runtime_source_path()
    if not runtime_src.exists():
        raise RuntimeError("kotlin runtime source not found: " + str(runtime_src))
    runtime_dst = output_path.parent / "py_runtime.kt"
    runtime_dst.write_text(runtime_src.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> int:
    """CLI 入口。互換ラッパとして py2x へ委譲する。"""
    return run_py2x_for_target("kotlin")


if __name__ == "__main__":
    _ = load_kotlin_profile
    sys.exit(main())
