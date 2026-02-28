#!/usr/bin/env python3
"""EAST -> Swift transpiler CLI."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.swift.emitter import load_swift_profile, transpile_to_swift, transpile_to_swift_native
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
        target_lang="swift",
    )
    return doc3 if isinstance(doc3, dict) else {}


def _default_output_path(input_path: Path) -> Path:
    """入力パスから既定の `.swift` 出力先を決定する。"""
    out = str(input_path)
    if out.endswith(".py"):
        out = out[:-3] + ".swift"
    elif out.endswith(".json"):
        out = out[:-5] + ".swift"
    else:
        out = out + ".swift"
    return Path(out)


def _arg_get_str(args: dict[str, Any], key: str, default_value: str = "") -> str:
    """argparse(dict) から文字列値を取り出す。"""
    if key not in args:
        return default_value
    val = args[key]
    if isinstance(val, str):
        return val
    return default_value


def _swift_runtime_source_path() -> Path:
    """Swift runtime 正本のソースファイルパスを返す。"""
    return Path(__file__).resolve().parent / "runtime" / "swift" / "pytra" / "py_runtime.swift"


def _copy_swift_runtime(output_path: Path) -> None:
    """生成先ディレクトリへ Swift runtime を配置する。"""
    runtime_src = _swift_runtime_source_path()
    if not runtime_src.exists():
        raise RuntimeError("swift runtime source not found: " + str(runtime_src))
    runtime_dst = output_path.parent / "py_runtime.swift"
    runtime_dst.write_text(runtime_src.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> int:
    """CLI 入口。"""
    parser = argparse.ArgumentParser(description="Pytra EAST -> Swift transpiler")
    add_common_transpile_args(parser, parser_backends=["self_hosted"])
    parser.add_argument("--east-stage", choices=["2", "3"], help="EAST stage mode (default: 3)")
    parser.add_argument(
        "--object-dispatch-mode",
        choices=["native", "type_id"],
        help="Object boundary dispatch mode used by EAST2->EAST3 lowering",
    )
    args = parser.parse_args()
    if not isinstance(args, dict):
        raise RuntimeError("argparse result must be dict")

    input_path = Path(_arg_get_str(args, "input"))
    output_text = _arg_get_str(args, "output")
    output_path = Path(output_text) if output_text != "" else _default_output_path(input_path)
    parser_backend = _arg_get_str(args, "parser_backend")
    if parser_backend == "":
        parser_backend = "self_hosted"
    east_stage = _arg_get_str(args, "east_stage")
    if east_stage == "":
        east_stage = "3"
    object_dispatch_mode = _arg_get_str(args, "object_dispatch_mode")
    if object_dispatch_mode == "":
        object_dispatch_mode = "native"
    east3_opt_level = _arg_get_str(args, "east3_opt_level")
    if east3_opt_level == "":
        east3_opt_level = "1"
    east3_opt_pass = _arg_get_str(args, "east3_opt_pass")
    dump_east3_before_opt = _arg_get_str(args, "dump_east3_before_opt")
    dump_east3_after_opt = _arg_get_str(args, "dump_east3_after_opt")
    dump_east3_opt_trace = _arg_get_str(args, "dump_east3_opt_trace")
    if east_stage == "2":
        parser.error("--east-stage 2 is no longer supported; use EAST3 (default).")

    east = load_east(
        input_path,
        parser_backend=parser_backend,
        east_stage=east_stage,
        object_dispatch_mode=object_dispatch_mode,
        east3_opt_level=east3_opt_level,
        east3_opt_pass=east3_opt_pass,
        dump_east3_before_opt=dump_east3_before_opt,
        dump_east3_after_opt=dump_east3_after_opt,
        dump_east3_opt_trace=dump_east3_opt_trace,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    swift_src = transpile_to_swift_native(east)
    output_path.write_text(swift_src, encoding="utf-8")
    _copy_swift_runtime(output_path)
    return 0


if __name__ == "__main__":
    _ = load_swift_profile
    sys.exit(main())
