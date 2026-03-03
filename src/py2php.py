#!/usr/bin/env python3
"""EAST -> PHP transpiler CLI."""

from __future__ import annotations

from pytra.std.typing import Any

from backends.php.emitter import load_php_profile, transpile_to_php, transpile_to_php_native
from backends.php.lower import lower_east3_to_php_ir
from backends.php.optimizer import optimize_php_ir
from toolchain.compiler.py2x_wrapper import run_py2x_for_target
from toolchain.compiler.transpile_cli import add_common_transpile_args, load_east3_document
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
        target_lang="php",
    )
    return doc3 if isinstance(doc3, dict) else {}


def _default_output_path(input_path: Path) -> Path:
    """入力パスから既定の `.php` 出力先を決定する。"""
    out = str(input_path)
    if out.endswith(".py"):
        out = out[:-3] + ".php"
    elif out.endswith(".json"):
        out = out[:-5] + ".php"
    else:
        out = out + ".php"
    return Path(out)


def _arg_get_str(args: dict[str, Any], key: str, default_value: str = "") -> str:
    """argparse(dict) から文字列値を取り出す。"""
    if key not in args:
        return default_value
    val = args[key]
    if isinstance(val, str):
        return val
    return default_value


def _php_runtime_source_root() -> Path:
    """PHP runtime 正本ルートディレクトリを返す。"""
    return Path(__file__).resolve().parent / "runtime" / "php" / "pytra"


def _copy_runtime_file(runtime_root: Path, runtime_dst_root: Path, rel_path: str) -> None:
    src = runtime_root / rel_path
    if not src.exists():
        return
    dst = runtime_dst_root / rel_path
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def _copy_php_runtime(output_path: Path) -> None:
    """生成先ディレクトリへ PHP runtime を配置する。"""
    runtime_root = _php_runtime_source_root()
    if not runtime_root.exists():
        raise RuntimeError("php runtime source root not found: " + str(runtime_root))
    runtime_dst_root = output_path.parent / "pytra"
    runtime_dst_root.mkdir(parents=True, exist_ok=True)
    files = [
        "py_runtime.php",
        "runtime/png.php",
        "runtime/gif.php",
        "std/time.php",
    ]
    i = 0
    while i < len(files):
        _copy_runtime_file(runtime_root, runtime_dst_root, files[i])
        i += 1


def main() -> int:
    """CLI 入口。互換ラッパとして py2x へ委譲する。"""
    return run_py2x_for_target("php")


if __name__ == "__main__":
    _ = load_php_profile
    _ = transpile_to_php
    sys.exit(main())
