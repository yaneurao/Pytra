#!/usr/bin/env python3
"""Unified Pytra frontend: Python/EAST3 -> multi-target source."""

from __future__ import annotations

from pytra.std.typing import Any

from pytra.compiler.backend_registry import (
    apply_runtime_hook,
    default_output_path,
    emit_source,
    get_backend_spec,
    list_backend_targets,
    lower_ir,
    optimize_ir,
)
from pytra.compiler.transpile_cli import add_common_transpile_args, load_east3_document
from pytra.std import argparse
from pytra.std.pathlib import Path
from pytra.std import sys


def _arg_get_str(args: dict[str, Any], key: str, default_value: str = "") -> str:
    if key not in args:
        return default_value
    val = args[key]
    if isinstance(val, str):
        return val
    return default_value


def _print_help() -> None:
    print(
        "usage: py2x.py INPUT.py --target {cpp,rs,cs,js,ts,go,java,kotlin,swift,ruby,lua,scala,php,nim} "
        "[-o OUTPUT] [--parser-backend self_hosted] [--east-stage 3] "
        "[--object-dispatch-mode {native,type_id}] [--east3-opt-level {0,1,2}] "
        "[--east3-opt-pass SPEC] [--dump-east3-before-opt PATH] "
        "[--dump-east3-after-opt PATH] [--dump-east3-opt-trace PATH]"
    )


def main() -> int:
    argv = sys.argv[1:] if isinstance(sys.argv, list) else []
    for arg in argv:
        if arg == "-h" or arg == "--help":
            _print_help()
            return 0

    parser = argparse.ArgumentParser(description="Pytra unified transpiler frontend")
    add_common_transpile_args(
        parser,
        parser_backends=["self_hosted"],
        enable_object_dispatch_mode=True,
    )
    parser.add_argument("--target", choices=list_backend_targets(), help="Target backend language")
    parser.add_argument("--east-stage", choices=["2", "3"], help="EAST stage mode (default: 3)")
    args = parser.parse_args()
    if not isinstance(args, dict):
        raise RuntimeError("argparse result must be dict")

    target = _arg_get_str(args, "target")
    if target == "":
        parser.error("--target is required")

    input_path = Path(_arg_get_str(args, "input"))
    output_text = _arg_get_str(args, "output")
    output_path = Path(output_text) if output_text != "" else default_output_path(input_path, target)

    parser_backend = _arg_get_str(args, "parser_backend")
    if parser_backend == "":
        parser_backend = "self_hosted"

    east_stage = _arg_get_str(args, "east_stage")
    if east_stage == "":
        east_stage = "3"
    if east_stage == "2":
        parser.error("--east-stage 2 is no longer supported; use EAST3 (default).")

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

    spec = get_backend_spec(target)
    target_lang = str(spec.get("target_lang", target))
    east_doc = load_east3_document(
        input_path,
        parser_backend=parser_backend,
        object_dispatch_mode=object_dispatch_mode,
        east3_opt_level=east3_opt_level,
        east3_opt_pass=east3_opt_pass,
        dump_east3_before_opt=dump_east3_before_opt,
        dump_east3_after_opt=dump_east3_after_opt,
        dump_east3_opt_trace=dump_east3_opt_trace,
        target_lang=target_lang,
    )
    east = east_doc if isinstance(east_doc, dict) else {}
    ir = lower_ir(spec, east)
    ir = optimize_ir(spec, ir)
    out_src = emit_source(spec, ir, output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(out_src, encoding="utf-8")
    apply_runtime_hook(spec, output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
