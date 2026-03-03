#!/usr/bin/env python3
"""EAST -> Lua transpiler CLI."""

from __future__ import annotations

from pytra.std.typing import Any

from backends.lua.emitter import load_lua_profile, transpile_to_lua, transpile_to_lua_native
from backends.lua.lower import lower_east3_to_lua_ir
from backends.lua.optimizer import optimize_lua_ir
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
        target_lang="lua",
    )
    return doc3 if isinstance(doc3, dict) else {}


def _default_output_path(input_path: Path) -> Path:
    """入力パスから既定の `.lua` 出力先を決定する。"""
    out = str(input_path)
    if out.endswith(".py"):
        out = out[:-3] + ".lua"
    elif out.endswith(".json"):
        out = out[:-5] + ".lua"
    else:
        out = out + ".lua"
    return Path(out)


def _arg_get_str(args: dict[str, Any], key: str, default_value: str = "") -> str:
    """argparse(dict) から文字列値を取り出す。"""
    if key not in args:
        return default_value
    val = args[key]
    if isinstance(val, str):
        return val
    return default_value


def _lua_runtime_source_path() -> Path:
    """Lua runtime 正本のソースファイルパスを返す。"""
    return Path(__file__).resolve().parent / "runtime" / "lua" / "pytra" / "py_runtime.lua"


def _copy_lua_runtime(output_path: Path) -> None:
    """生成先ディレクトリへ Lua runtime を配置する。"""
    runtime_src = _lua_runtime_source_path()
    if not runtime_src.exists():
        raise RuntimeError("lua runtime source not found: " + str(runtime_src))
    runtime_dst = output_path.parent / "py_runtime.lua"
    runtime_dst.write_text(runtime_src.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> int:
    """CLI 入口。互換ラッパとして py2x へ委譲する。"""
    return run_py2x_for_target("lua")


if __name__ == "__main__":
    _ = load_lua_profile
    _ = transpile_to_lua
    sys.exit(main())
