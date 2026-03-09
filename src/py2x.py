#!/usr/bin/env python3
"""Unified Pytra frontend: Python/EAST3 -> multi-target source."""

from __future__ import annotations

from typing import Any

from toolchain.compiler.backend_registry import apply_runtime_hook_typed
from toolchain.compiler.backend_registry import build_program_artifact_typed
from toolchain.compiler.backend_registry import collect_program_modules_typed
from toolchain.compiler.backend_registry import default_output_path
from toolchain.compiler.backend_registry import emit_module_typed
from toolchain.compiler.backend_registry import get_program_writer_typed
from toolchain.compiler.backend_registry import get_backend_spec_typed
from toolchain.compiler.backend_registry import list_backend_targets
from toolchain.compiler.backend_registry import lower_ir_typed
from toolchain.compiler.backend_registry import optimize_ir_typed
from toolchain.compiler.backend_registry import resolve_layer_options_typed
from toolchain.compiler.typed_boundary import backend_spec_target
from toolchain.compiler.typed_boundary import compiler_root_module_id
from toolchain.compiler.typed_boundary import coerce_module_artifact
from toolchain.compiler.typed_boundary import export_compiler_root_document
from toolchain.compiler.typed_boundary import export_program_artifact_any
from toolchain.compiler.transpile_cli import add_common_transpile_args, build_module_east_map, load_east3_document_typed
from toolchain.frontends.extern_var import validate_ambient_global_target_support
from toolchain.frontends.runtime_abi import validate_runtime_abi_target_support
from toolchain.link import LINK_INPUT_SCHEMA
from toolchain.link import build_linked_program_from_module_map
from toolchain.link import LinkedProgram
from toolchain.link import load_linked_program
from toolchain.link import optimize_linked_program
from toolchain.link import write_link_input_bundle
from toolchain.link import write_link_output_bundle
from pytra.std import argparse
from pytra.std import json
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
        "[--dump-east3-after-opt PATH] [--dump-east3-opt-trace PATH] [--dump-east3-dir DIR] [--link-only] "
        "[--from-link-output] [--output-dir DIR] "
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


def _load_json_root(path: Path) -> json.JsonObj:
    try:
        payload = json.loads_obj(path.read_text(encoding="utf-8"))
    except Exception:
        return json.JsonObj({})
    if payload is None:
        return json.JsonObj({})
    return payload


def _write_generated_paths(paths: list[Path]) -> None:
    for path in paths:
        print("generated: " + str(path))


def _use_linked_program_route(target_hint: str, argv: list[str]) -> bool:
    if target_hint != "cpp":
        return True
    for flag in ("--dump-east3-dir", "--link-only", "--from-link-output"):
        if _has_flag(argv, flag):
            return True
    return False


def _invoke_py2cpp_main(argv: list[str]) -> int:
    from backends.cpp.cli import main as py2cpp_main

    return py2cpp_main(argv)


def _invoke_ir2lang_main(argv: list[str]) -> int:
    import ir2lang as ir2lang_mod

    return ir2lang_mod.main(argv)


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


def _build_linked_program_for_input(
    input_path: Path,
    *,
    parser_backend: str,
    object_dispatch_mode: str,
    east3_opt_level: str,
    east3_opt_pass: str,
    dump_east3_before_opt: str,
    dump_east3_after_opt: str,
    dump_east3_opt_trace: str,
    target_lang: str,
) -> LinkedProgram:
    def _load_for_program(
        module_path: Path,
        parser_backend: str = "self_hosted",
        east_stage: str = "3",
        object_dispatch_mode: str = "",
    ) -> dict[str, object]:
        _ = east_stage
        enable_dump = module_path.resolve() == input_path.resolve()
        return export_compiler_root_document(
            load_east3_document_typed(
                module_path,
                parser_backend=parser_backend,
                object_dispatch_mode=object_dispatch_mode,
                east3_opt_level=east3_opt_level,
                east3_opt_pass=east3_opt_pass,
                dump_east3_before_opt=dump_east3_before_opt if enable_dump else "",
                dump_east3_after_opt=dump_east3_after_opt if enable_dump else "",
                dump_east3_opt_trace=dump_east3_opt_trace if enable_dump else "",
                target_lang=target_lang,
            )
        )

    input_txt = str(input_path)
    module_map: dict[str, dict[str, object]] = {}
    if input_txt.endswith(".py"):
        module_map = build_module_east_map(
            input_path,
            _load_for_program,
            parser_backend=parser_backend,
            east_stage="3",
            object_dispatch_mode=object_dispatch_mode,
        )
    elif input_txt.endswith(".json"):
        root = _load_json_root(input_path)
        if root.get_str("schema") == LINK_INPUT_SCHEMA:
            return load_linked_program(input_path)
        module_map = {
            str(input_path.resolve()): _load_for_program(
                input_path,
                parser_backend=parser_backend,
                east_stage="3",
                object_dispatch_mode=object_dispatch_mode,
            )
        }
    else:
        module_map = {
            str(input_path.resolve()): _load_for_program(
                input_path,
                parser_backend=parser_backend,
                east_stage="3",
                object_dispatch_mode=object_dispatch_mode,
            )
        }

    return build_linked_program_from_module_map(
        input_path,
        module_map,
        target=target_lang,
        dispatch_mode=object_dispatch_mode,
        options={
            "east3_opt_level": east3_opt_level,
            "east3_opt_pass": east3_opt_pass,
        },
    )


def _entry_module_east_doc(program: LinkedProgram) -> dict[str, object]:
    entry_module_ids = set(program.entry_modules)
    for module in program.modules:
        if module.is_entry and module.module_id in entry_module_ids:
            return module.east_doc
    raise RuntimeError("linked program entry module not found")


def main() -> int:
    argv = sys.argv[1:] if isinstance(sys.argv, list) else []
    for arg in argv:
        if arg == "-h" or arg == "--help":
            _print_help()
            return 0

    cleaned_argv, layer_option_items = _extract_layer_options(argv)
    target_hint = _peek_target(cleaned_argv)
    if _use_linked_program_route(target_hint, cleaned_argv) is False:
        return _run_cpp_compat(cleaned_argv, layer_option_items=layer_option_items)

    parser = argparse.ArgumentParser(description="Pytra unified transpiler frontend")
    add_common_transpile_args(
        parser,
        parser_backends=["self_hosted"],
        enable_object_dispatch_mode=True,
    )
    parser.add_argument("--target", choices=list_backend_targets(), help="Target backend language")
    parser.add_argument("--east-stage", choices=["2", "3"], help="EAST stage mode (default: 3)")
    parser.add_argument("--dump-east3-dir", help="Write raw EAST3 modules + link-input.json to DIR and exit")
    parser.add_argument("--link-only", action="store_true", help="Write link-output.json + linked modules to --output-dir and exit")
    parser.add_argument("--from-link-output", action="store_true", help="Treat INPUT.json as link-output.json and restart backend emit")
    parser.add_argument("--output-dir", help="Output directory for linked-program artifacts")
    args = parser.parse_args(cleaned_argv)
    if not isinstance(args, dict):
        raise RuntimeError("argparse result must be dict")

    target = _arg_get_str(args, "target")
    if target == "":
        _fatal("--target is required")

    input_path = Path(_arg_get_str(args, "input"))
    dump_east3_dir = _arg_get_str(args, "dump_east3_dir")
    link_only = bool(args.get("link_only", False))
    from_link_output = bool(args.get("from_link_output", False))
    output_dir_txt = _arg_get_str(args, "output_dir")
    if dump_east3_dir != "" and link_only:
        _fatal("--dump-east3-dir and --link-only cannot be combined")
    if from_link_output and (dump_east3_dir != "" or link_only):
        _fatal("--from-link-output cannot be combined with --dump-east3-dir or --link-only")
    output_text = _arg_get_str(args, "output")

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
    if from_link_output:
        forwarded = [str(input_path), "--target", target]
        if output_text != "":
            forwarded.extend(["-o", output_text])
        if output_dir_txt != "":
            forwarded.extend(["--output-dir", output_dir_txt])
        for item in layer_option_items["lower"]:
            forwarded.extend(["--lower-option", item])
        for item in layer_option_items["optimizer"]:
            forwarded.extend(["--optimizer-option", item])
        for item in layer_option_items["emitter"]:
            forwarded.extend(["--emitter-option", item])
        return _invoke_ir2lang_main(forwarded)
    target_lang = target
    program = _build_linked_program_for_input(
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
    for linked_module in program.modules:
        linked_doc = getattr(linked_module, "east_doc", {})
        if isinstance(linked_doc, dict):
            validate_ambient_global_target_support(linked_doc, target=target)
    if dump_east3_dir != "":
        manifest_path, module_paths = write_link_input_bundle(Path(dump_east3_dir), program)
        _write_generated_paths([manifest_path] + module_paths)
        return 0
    if link_only:
        output_dir = Path(output_dir_txt) if output_dir_txt != "" else Path("out/linked")
        link_output_path, linked_paths = write_link_output_bundle(output_dir, optimize_linked_program(program))
        _write_generated_paths([link_output_path] + linked_paths)
        return 0

    output_path = Path(output_text) if output_text != "" else default_output_path(input_path, target)
    spec = get_backend_spec_typed(target)
    lower_raw = _parse_layer_option_items(layer_option_items["lower"], "--lower-option")
    optimizer_raw = _parse_layer_option_items(layer_option_items["optimizer"], "--optimizer-option")
    emitter_raw = _parse_layer_option_items(layer_option_items["emitter"], "--emitter-option")
    lower_options = {}
    optimizer_options = {}
    emitter_options = {}
    try:
        lower_options = resolve_layer_options_typed(spec, "lower", lower_raw)
        optimizer_options = resolve_layer_options_typed(spec, "optimizer", optimizer_raw)
        emitter_options = resolve_layer_options_typed(spec, "emitter", emitter_raw)
    except Exception as ex:
        _fatal(str(ex))

    optimized_program = optimize_linked_program(program).linked_program
    east = _entry_module_east_doc(optimized_program)
    validate_ambient_global_target_support(east, target=target)
    validate_runtime_abi_target_support(east, target=target)
    ir = lower_ir_typed(spec, east, lower_options)
    ir = optimize_ir_typed(spec, ir, optimizer_options)
    module_id = compiler_root_module_id(east, fallback_output_path=output_path)
    module_artifact = emit_module_typed(
        spec,
        ir,
        output_path,
        emitter_options,
        module_id=module_id,
        is_entry=True,
    )
    module_carrier = coerce_module_artifact(module_artifact)
    program_artifact = build_program_artifact_typed(
        spec,
        list(collect_program_modules_typed(module_carrier)),
        program_id=module_id,
        entry_modules=[module_id],
        layout_mode="single_file",
        link_output_schema="",
    )
    writer = get_program_writer_typed(spec)
    spec_target = backend_spec_target(spec)
    program_artifact_any = export_program_artifact_any(
        program_artifact,
        fallback_target=spec_target,
        fallback_program_id=module_id,
        fallback_entry_modules=[module_id],
    )
    if callable(writer):
        _ = writer(program_artifact_any, output_path, {})
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(module_carrier.text, encoding="utf-8")
    apply_runtime_hook_typed(spec, output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
