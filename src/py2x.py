#!/usr/bin/env python3
"""Unified Pytra frontend: Python/EAST3 -> multi-target source."""

from __future__ import annotations

from pytra.std.typing import Any

from toolchain.compiler.backend_registry import (
    apply_runtime_hook,
    default_output_path,
    emit_source,
    get_backend_spec,
    list_backend_targets,
    lower_ir,
    optimize_ir,
    resolve_layer_options,
)
from toolchain.compiler.transpile_cli import add_common_transpile_args, load_east3_document
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


def _fatal(msg: str) -> None:
    sys.write_stderr("error: " + msg + "\n")
    raise SystemExit(2)


def _print_help() -> None:
    print(
        "usage: py2x.py INPUT.py --target {cpp,rs,cs,js,ts,go,java,kotlin,swift,ruby,lua,scala,php,nim} "
        "[-o OUTPUT] [--parser-backend self_hosted] [--east-stage 3] "
        "[--object-dispatch-mode {native,type_id}] [--east3-opt-level {0,1,2}] "
        "[--east3-opt-pass SPEC] [--dump-east3-before-opt PATH] "
        "[--dump-east3-after-opt PATH] [--dump-east3-opt-trace PATH] "
        "[--lower-option key=value] [--optimizer-option key=value] [--emitter-option key=value]\n"
        "note: for --target cpp, py2cpp compatibility flags (e.g. --multi-file, --header-output, "
        "--emit-runtime-cpp, --dump-deps, --dump-options, -O*) are also accepted."
    )


def _extract_layer_options(argv: list[str]) -> tuple[list[str], dict[str, list[str]]]:
    cleaned: list[str] = []
    options: dict[str, list[str]] = {
        "lower": [],
        "optimizer": [],
        "emitter": [],
    }
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok == "--lower-option" or tok == "--optimizer-option" or tok == "--emitter-option":
            if i + 1 >= len(argv):
                _fatal("missing value for " + tok)
            val = argv[i + 1]
            if tok == "--lower-option":
                options["lower"].append(val)
            elif tok == "--optimizer-option":
                options["optimizer"].append(val)
            else:
                options["emitter"].append(val)
            i += 2
            continue
        cleaned.append(tok)
        i += 1
    return cleaned, options


def _peek_target(argv: list[str]) -> str:
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok == "--target":
            if i + 1 >= len(argv):
                _fatal("missing value for --target")
            return argv[i + 1]
        if tok.startswith("--target="):
            return tok[len("--target=") :]
        i += 1
    return ""


def _strip_target(argv: list[str]) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok == "--target":
            if i + 1 >= len(argv):
                _fatal("missing value for --target")
            i += 2
            continue
        if tok.startswith("--target="):
            i += 1
            continue
        out.append(tok)
        i += 1
    return out


def _has_flag(argv: list[str], flag: str) -> bool:
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok == flag:
            return True
        if tok.startswith(flag + "="):
            return True
        i += 1
    return False


def _invoke_py2cpp_main(argv: list[str]) -> int:
    from backends.cpp.cli import main as py2cpp_main

    return py2cpp_main(argv)


def _apply_cpp_layer_options(
    cpp_argv: list[str],
    *,
    lower_raw: dict[str, str],
    optimizer_raw: dict[str, str],
    emitter_raw: dict[str, str],
) -> list[str]:
    out = list(cpp_argv)
    unsupported: list[str] = []
    if len(lower_raw) > 0:
        for key in lower_raw.keys():
            unsupported.append("--lower-option " + key)

    optimizer_map: dict[str, str] = {
        "cpp_opt_level": "--cpp-opt-level",
        "cpp_opt_pass": "--cpp-opt-pass",
        "dump_cpp_ir_before_opt": "--dump-cpp-ir-before-opt",
        "dump_cpp_ir_after_opt": "--dump-cpp-ir-after-opt",
        "dump_cpp_opt_trace": "--dump-cpp-opt-trace",
    }
    emitter_map: dict[str, str] = {
        "negative_index_mode": "--negative-index-mode",
        "bounds_check_mode": "--bounds-check-mode",
        "floor_div_mode": "--floor-div-mode",
        "mod_mode": "--mod-mode",
        "int_width": "--int-width",
        "str_index_mode": "--str-index-mode",
        "str_slice_mode": "--str-slice-mode",
        "cpp_list_model": "--cpp-list-model",
    }

    def _append_mapped_options(raw: dict[str, str], mapping: dict[str, str], label: str) -> None:
        for key, value in raw.items():
            normalized_key = key.replace("-", "_")
            flag = mapping.get(normalized_key, "")
            if flag == "":
                unsupported.append(label + " " + key)
                continue
            if _has_flag(out, flag):
                continue
            out.append(flag)
            out.append(value)

    _append_mapped_options(optimizer_raw, optimizer_map, "--optimizer-option")
    _append_mapped_options(emitter_raw, emitter_map, "--emitter-option")

    if len(unsupported) > 0:
        _fatal("unsupported cpp layer option(s): " + ", ".join(unsupported))

    return out


def _run_cpp_compat(
    cleaned_argv: list[str],
    *,
    layer_option_items: dict[str, list[str]],
) -> int:
    cpp_argv = _strip_target(cleaned_argv)
    lower_raw = _parse_layer_option_items(layer_option_items["lower"], "--lower-option")
    optimizer_raw = _parse_layer_option_items(layer_option_items["optimizer"], "--optimizer-option")
    emitter_raw = _parse_layer_option_items(layer_option_items["emitter"], "--emitter-option")
    forwarded = _apply_cpp_layer_options(
        cpp_argv,
        lower_raw=lower_raw,
        optimizer_raw=optimizer_raw,
        emitter_raw=emitter_raw,
    )
    return _invoke_py2cpp_main(forwarded)


def _parse_layer_option_items(items: list[str], label: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items:
        pos = item.find("=")
        if pos <= 0:
            _fatal(label + " must be key=value: " + item)
        key = item[:pos]
        value = item[pos + 1 :]
        if key == "":
            _fatal(label + " key must not be empty")
        out[key] = value
    return out


def main() -> int:
    argv = sys.argv[1:] if isinstance(sys.argv, list) else []
    for arg in argv:
        if arg == "-h" or arg == "--help":
            _print_help()
            return 0

    cleaned_argv, layer_option_items = _extract_layer_options(argv)
    target_hint = _peek_target(cleaned_argv)
    if target_hint == "cpp":
        return _run_cpp_compat(cleaned_argv, layer_option_items=layer_option_items)

    parser = argparse.ArgumentParser(description="Pytra unified transpiler frontend")
    add_common_transpile_args(
        parser,
        parser_backends=["self_hosted"],
        enable_object_dispatch_mode=True,
    )
    parser.add_argument("--target", choices=list_backend_targets(), help="Target backend language")
    parser.add_argument("--east-stage", choices=["2", "3"], help="EAST stage mode (default: 3)")
    args = parser.parse_args(cleaned_argv)
    if not isinstance(args, dict):
        raise RuntimeError("argparse result must be dict")

    target = _arg_get_str(args, "target")
    if target == "":
        _fatal("--target is required")

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
        _fatal("--east-stage 2 is no longer supported; use EAST3 (default).")

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
    lower_raw = _parse_layer_option_items(layer_option_items["lower"], "--lower-option")
    optimizer_raw = _parse_layer_option_items(layer_option_items["optimizer"], "--optimizer-option")
    emitter_raw = _parse_layer_option_items(layer_option_items["emitter"], "--emitter-option")
    try:
        lower_options = resolve_layer_options(spec, "lower", lower_raw)
        optimizer_options = resolve_layer_options(spec, "optimizer", optimizer_raw)
        emitter_options = resolve_layer_options(spec, "emitter", emitter_raw)
    except Exception as ex:
        _fatal(str(ex))

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
    ir = lower_ir(spec, east, lower_options)
    ir = optimize_ir(spec, ir, optimizer_options)
    out_src = emit_source(spec, ir, output_path, emitter_options)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(out_src, encoding="utf-8")
    apply_runtime_hook(spec, output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
