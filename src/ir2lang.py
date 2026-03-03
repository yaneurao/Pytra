#!/usr/bin/env python3
"""Backend-only frontend: EAST3(JSON) -> target source."""

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
    resolve_layer_options,
)
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
        "[-o OUTPUT] [--no-runtime-hook] "
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


def _load_json_root(input_path: Path) -> dict[str, Any]:
    if str(input_path).endswith(".json") is False:
        _fatal("input must be a .json EAST3 document")
    if input_path.exists() is False:
        _fatal("input not found: " + str(input_path))
    try:
        payload_any = json.loads(input_path.read_text(encoding="utf-8"))
    except Exception as ex:
        _fatal("failed to parse json: " + str(ex))
    if isinstance(payload_any, dict):
        return payload_any
    _fatal("invalid EAST JSON root: expected dict")
    return {}


def _unwrap_east_module(root: dict[str, Any]) -> dict[str, Any]:
    ok_any = root.get("ok")
    east_any = root.get("east")
    if isinstance(ok_any, bool) and bool(ok_any) and isinstance(east_any, dict):
        return east_any
    if root.get("kind") == "Module":
        return root
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
    return east


def main() -> int:
    argv = sys.argv[1:] if isinstance(sys.argv, list) else []
    for arg in argv:
        if arg == "-h" or arg == "--help":
            _print_help()
            return 0

    parser = argparse.ArgumentParser(description="Pytra IR-to-language frontend")
    parser.add_argument("input", help="Input EAST3 .json")
    parser.add_argument("-o", "--output", help="Output file path")
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
    output_path = Path(output_text) if output_text != "" else default_output_path(input_path, target)

    root = _load_json_root(input_path)
    east_doc = _validate_east3_module(_unwrap_east_module(root))

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

    ir = lower_ir(spec, east_doc, lower_options)
    ir = optimize_ir(spec, ir, optimizer_options)
    out_src = emit_source(spec, ir, output_path, emitter_options)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(out_src, encoding="utf-8")

    skip_runtime_hook = _arg_get_bool(args, "no_runtime_hook")
    if not skip_runtime_hook:
        apply_runtime_hook(spec, output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
