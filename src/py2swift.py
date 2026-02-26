#!/usr/bin/env python3
"""EAST -> Swift transpiler CLI."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.swift.emitter.swift_emitter import load_swift_profile, transpile_to_swift
from hooks.swift.emitter.swift_native_emitter import transpile_to_swift_native
from hooks.js.emitter.js_emitter import transpile_to_js
from pytra.compiler.js_runtime_shims import write_js_runtime_shims
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


def _sidecar_js_path(output_path: Path) -> Path:
    """Swift 出力に対応する sidecar JS のパスを返す。"""
    out = str(output_path)
    if out.endswith(".swift"):
        return Path(out[:-6] + ".js")
    return Path(out + ".js")


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
    parser.add_argument(
        "--swift-backend",
        choices=["native", "sidecar"],
        help="Swift backend mode: native (default) or sidecar compatibility",
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
    swift_backend = _arg_get_str(args, "swift_backend")
    if swift_backend == "":
        swift_backend = "native"
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
    if swift_backend == "sidecar":
        js_output_path = _sidecar_js_path(output_path)
        js_src = transpile_to_js(east)
        swift_src = transpile_to_swift(east, js_entry_path=str(js_output_path))
        output_path.write_text(swift_src, encoding="utf-8")
        js_output_path.write_text(js_src, encoding="utf-8")
        write_js_runtime_shims(js_output_path.parent)
        return 0

    swift_src = transpile_to_swift_native(east)
    output_path.write_text(swift_src, encoding="utf-8")
    return 0


if __name__ == "__main__":
    _ = load_swift_profile
    sys.exit(main())
