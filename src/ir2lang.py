#!/usr/bin/env python3
"""Backend-only frontend: EAST3(JSON) -> target source."""

from __future__ import annotations

from typing import Any

from toolchain.compiler.backend_registry import (
    apply_runtime_hook_typed as apply_runtime_hook,
    build_program_artifact_typed as build_program_artifact,
    collect_program_modules_typed as collect_program_modules,
    default_output_path,
    emit_module_typed as emit_module,
    get_program_writer_typed as get_program_writer,
    get_backend_spec_typed as get_backend_spec,
    list_backend_targets,
    lower_ir_typed as lower_ir,
    optimize_ir_typed as optimize_ir,
    resolve_layer_options_typed as resolve_layer_options,
)
from toolchain.compiler.typed_boundary import coerce_module_artifact
from toolchain.compiler.typed_boundary import export_module_artifact_any
from toolchain.compiler.typed_boundary import export_program_artifact_any
from toolchain.frontends.extern_var import validate_ambient_global_target_support
from toolchain.frontends.runtime_abi import validate_runtime_abi_module
from toolchain.frontends.runtime_abi import validate_runtime_abi_target_support
from toolchain.link import LINK_OUTPUT_SCHEMA
from toolchain.link import load_linked_output_bundle
from backends.cpp.emitter.multifile_writer import write_multi_file_cpp
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


def _arg_get_bool(args: dict[str, Any], key: str) -> bool:
    if key not in args:
        return False
    val = args[key]
    if isinstance(val, bool):
        return bool(val)
    return False


def _fatal(msg: str) -> None:
    sys.write_stderr("error: " + msg + "\n")
    raise SystemExit(2)


def _print_help() -> None:
    print(
        "usage: ir2lang.py INPUT.json --target {cpp,rs,cs,js,ts,go,java,kotlin,swift,ruby,lua,scala,php,nim} "
        "[-o OUTPUT] [--output-dir DIR] [--no-runtime-hook] "
        "[--lower-option key=value] [--optimizer-option key=value] [--emitter-option key=value]"
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


def _load_json_root(input_path: Path) -> json.JsonObj:
    if str(input_path).endswith(".json") is False:
        _fatal("input must be a .json EAST3 document")
    if input_path.exists() is False:
        _fatal("input not found: " + str(input_path))
    try:
        payload = json.loads_obj(input_path.read_text(encoding="utf-8"))
    except Exception as ex:
        _fatal("failed to parse json: " + str(ex))
    if payload is not None:
        return payload
    _fatal("invalid EAST JSON root: expected dict")
    return json.JsonObj({})


def _unwrap_east_module(root: json.JsonObj) -> dict[str, Any]:
    ok_any = root.get_bool("ok")
    east_any = root.get_obj("east")
    if ok_any is True and east_any is not None:
        return dict(east_any.raw)
    if root.get_str("kind") == "Module":
        return dict(root.raw)
    _fatal("invalid EAST JSON structure: expected {'ok': true, 'east': {...}} or {'kind': 'Module', ...}")
    return {}


def _validate_east3_module(east: dict[str, Any]) -> dict[str, Any]:
    if east.get("kind") != "Module":
        _fatal("invalid EAST root: kind must be 'Module'")

    stage_any = east.get("east_stage")
    if not isinstance(stage_any, int):
        _fatal("invalid EAST root: east_stage must be int(3)")
    if int(stage_any) != 3:
        _fatal("invalid EAST stage: ir2lang accepts EAST3 only (east_stage=3)")

    body_any = east.get("body")
    if not isinstance(body_any, list):
        _fatal("invalid EAST root: body must be a list")

    if "schema_version" in east:
        schema_any = east.get("schema_version")
        if not isinstance(schema_any, int) or int(schema_any) < 1:
            _fatal("invalid EAST root: schema_version must be int >= 1")

    if "meta" in east and not isinstance(east.get("meta"), dict):
        _fatal("invalid EAST root: meta must be an object")
    return validate_runtime_abi_module(east)


def _module_id_from_east(east: dict[str, Any], output_path: Path) -> str:
    meta_any = east.get("meta", {})
    meta = meta_any if isinstance(meta_any, dict) else {}
    module_id_any = meta.get("module_id")
    if isinstance(module_id_any, str) and module_id_any.strip() != "":
        return module_id_any.strip()
    if output_path.stem != "":
        return output_path.stem
    return "module"


def _is_link_output_doc(root: json.JsonObj) -> bool:
    return root.get_str("schema") == LINK_OUTPUT_SCHEMA


def _entry_linked_module(
    linked_modules: tuple[Any, ...],
    entry_modules: list[str] | tuple[str, ...],
) -> dict[str, Any]:
    entry_set = {item for item in entry_modules if isinstance(item, str)}
    for module in linked_modules:
        module_id = getattr(module, "module_id", "")
        is_entry = bool(getattr(module, "is_entry", False))
        east_doc = getattr(module, "east_doc", {})
        if is_entry and isinstance(module_id, str) and module_id in entry_set and isinstance(east_doc, dict):
            return east_doc
    raise RuntimeError("linked entry module not found")


def _entry_source_path(
    linked_modules: tuple[Any, ...],
    entry_modules: list[str] | tuple[str, ...],
) -> Path:
    entry_set = {item for item in entry_modules if isinstance(item, str)}
    for module in linked_modules:
        module_id = getattr(module, "module_id", "")
        source_path = getattr(module, "source_path", "")
        is_entry = bool(getattr(module, "is_entry", False))
        if is_entry and isinstance(module_id, str) and module_id in entry_set and isinstance(source_path, str):
            return Path(source_path)
    return Path("main.py")


def _emit_cpp_linked_program(
    linked_modules: tuple[Any, ...],
    entry_modules: list[str] | tuple[str, ...],
    output_root: Path,
    emitter_options: dict[str, object],
) -> dict[str, object]:
    module_east_map: dict[str, dict[str, Any]] = {}
    entry_path = Path("")
    entry_set = {item for item in entry_modules if isinstance(item, str)}
    for module in linked_modules:
        module_id = getattr(module, "module_id", "")
        source_path = getattr(module, "source_path", "")
        east_doc = getattr(module, "east_doc", {})
        is_entry = bool(getattr(module, "is_entry", False))
        if not isinstance(module_id, str) or module_id == "" or not isinstance(east_doc, dict):
            continue
        module_path = Path(source_path) if isinstance(source_path, str) and source_path != "" else Path(module_id + ".py")
        module_east_map[str(module_path)] = east_doc
        if is_entry and module_id in entry_set:
            entry_path = module_path
    if entry_path == Path(""):
        raise RuntimeError("linked C++ entry module not found")
    return write_multi_file_cpp(
        entry_path,
        module_east_map,
        output_root,
        negative_index_mode=str(emitter_options.get("negative_index_mode", "const_only")),
        bounds_check_mode=str(emitter_options.get("bounds_check_mode", "off")),
        floor_div_mode=str(emitter_options.get("floor_div_mode", "native")),
        mod_mode=str(emitter_options.get("mod_mode", "native")),
        int_width="64",
        str_index_mode="native",
        str_slice_mode="byte",
        opt_level="2",
        top_namespace="",
        emit_main=True,
    )


def main(argv: list[str] | None = None) -> int:
    argv = list(argv) if isinstance(argv, list) else (sys.argv[1:] if isinstance(sys.argv, list) else [])
    for arg in argv:
        if arg == "-h" or arg == "--help":
            _print_help()
            return 0

    parser = argparse.ArgumentParser(description="Pytra IR-to-language frontend")
    parser.add_argument("input", help="Input EAST3 .json")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("--output-dir", help="Output directory for linked-program input")
    parser.add_argument("--target", choices=list_backend_targets(), help="Target backend language")
    parser.add_argument("--no-runtime-hook", action="store_true", help="Skip runtime helper emission/copy")

    cleaned_argv, layer_option_items = _extract_layer_options(argv)
    args = parser.parse_args(cleaned_argv)
    if not isinstance(args, dict):
        raise RuntimeError("argparse result must be dict")

    target = _arg_get_str(args, "target")
    if target == "":
        _fatal("--target is required")

    input_path = Path(_arg_get_str(args, "input"))
    output_text = _arg_get_str(args, "output")
    output_dir_text = _arg_get_str(args, "output_dir")

    root = _load_json_root(input_path)
    is_link_output = _is_link_output_doc(root)
    if is_link_output is False:
        east_doc = _validate_east3_module(_unwrap_east_module(root))
        validate_ambient_global_target_support(east_doc, target=target)

    skip_runtime_hook = _arg_get_bool(args, "no_runtime_hook")
    lower_raw = _parse_layer_option_items(layer_option_items["lower"], "--lower-option")
    optimizer_raw = _parse_layer_option_items(layer_option_items["optimizer"], "--optimizer-option")
    emitter_raw = _parse_layer_option_items(layer_option_items["emitter"], "--emitter-option")

    spec: object
    lower_options: object
    optimizer_options: object
    emitter_options: object
    if is_link_output:
        link_output_doc, linked_modules = load_linked_output_bundle(input_path)
        link_target = link_output_doc.get("target")
        if isinstance(link_target, str) and link_target != "" and link_target != target:
            _fatal("target mismatch for link-output: " + link_target + " != " + target)
        for linked_module in linked_modules:
            linked_doc = getattr(linked_module, "east_doc", {})
            if isinstance(linked_doc, dict):
                validate_ambient_global_target_support(linked_doc, target=target)
                validate_runtime_abi_target_support(linked_doc, target=target)
        spec = get_backend_spec(target)
        try:
            lower_options = resolve_layer_options(spec, "lower", lower_raw)
            optimizer_options = resolve_layer_options(spec, "optimizer", optimizer_raw)
            emitter_options = resolve_layer_options(spec, "emitter", emitter_raw)
        except Exception as ex:
            _fatal(str(ex))
        entry_modules_any = link_output_doc.get("entry_modules", [])
        entry_modules = list(entry_modules_any) if isinstance(entry_modules_any, (list, tuple)) else []
        if target == "cpp":
            output_root_text = output_dir_text if output_dir_text != "" else output_text
            output_root = Path(output_root_text) if output_root_text != "" else (input_path.parent / "cpp")
            _ = _emit_cpp_linked_program(linked_modules, entry_modules, output_root, emitter_options)
            return 0

        entry_east_doc = _entry_linked_module(linked_modules, entry_modules)
        default_restart_output = default_output_path(_entry_source_path(linked_modules, entry_modules), target)
        if output_dir_text != "" and output_text != "":
            _fatal("use either --output-dir or --output with link-output input")
        if output_dir_text != "":
            output_path = Path(output_dir_text) / default_restart_output.name
        elif output_text != "":
            output_path = Path(output_text)
        else:
            output_path = default_restart_output
        east_doc = entry_east_doc
    else:
        spec = get_backend_spec(target)
        try:
            lower_options = resolve_layer_options(spec, "lower", lower_raw)
            optimizer_options = resolve_layer_options(spec, "optimizer", optimizer_raw)
            emitter_options = resolve_layer_options(spec, "emitter", emitter_raw)
        except Exception as ex:
            _fatal(str(ex))
        output_path = Path(output_text) if output_text != "" else default_output_path(input_path, target)

    validate_ambient_global_target_support(east_doc, target=target)
    validate_runtime_abi_target_support(east_doc, target=target)
    ir = lower_ir(spec, east_doc, lower_options)
    ir = optimize_ir(spec, ir, optimizer_options)
    module_id = _module_id_from_east(east_doc, output_path)
    module_artifact = emit_module(
        spec,
        ir,
        output_path,
        emitter_options,
        module_id=module_id,
        is_entry=True,
    )
    module_carrier = coerce_module_artifact(module_artifact)
    module_artifact_dict = export_module_artifact_any(module_artifact)
    module_text_any = module_artifact_dict.get("text", module_carrier.text)
    module_text = module_text_any if isinstance(module_text_any, str) else module_carrier.text
    program_modules = list(collect_program_modules(module_carrier))
    program_artifact = build_program_artifact(
        spec,
        program_modules,
        program_id=module_id,
        entry_modules=[module_id],
        layout_mode="single_file",
        link_output_schema="",
    )
    writer = get_program_writer(spec)
    if callable(writer):
        writer_program_artifact = export_program_artifact_any(program_artifact)
        _ = writer(writer_program_artifact, output_path, {})
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(module_text, encoding="utf-8")

    if not skip_runtime_hook:
        apply_runtime_hook(spec, output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
