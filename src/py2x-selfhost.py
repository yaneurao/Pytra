#!/usr/bin/env python3
"""Selfhost-side unified frontend: Python/EAST3 -> multi-target source.

This entrypoint keeps static backend imports by using backend_registry_static.
"""

from __future__ import annotations

from toolchain.compiler.backend_registry_static import apply_runtime_hook
from toolchain.compiler.backend_registry_static import default_output_path
from toolchain.compiler.backend_registry_static import emit_source
from toolchain.compiler.backend_registry_static import get_backend_spec
from toolchain.compiler.backend_registry_static import list_backend_targets
from toolchain.compiler.backend_registry_static import lower_ir
from toolchain.compiler.backend_registry_static import optimize_ir
from toolchain.compiler.backend_registry_static import resolve_layer_options
from toolchain.compiler.transpile_cli import load_east3_document
from pytra.std.pathlib import Path
from pytra.std import sys


def _list_targets() -> list[str]:
    return list_backend_targets()


def _default_output(input_path: Path, target: str) -> Path:
    return default_output_path(input_path, target)


def _load_east3(
    input_path: Path,
    parser_backend: str,
    object_dispatch_mode: str,
    east3_opt_level: str,
    east3_opt_pass: str,
    dump_east3_before_opt: str,
    dump_east3_after_opt: str,
    dump_east3_opt_trace: str,
    target_lang: str,
) -> dict[str, object]:
    doc = load_east3_document(
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
    if isinstance(doc, dict):
        return doc
    return {}


def _get_spec(target: str) -> dict[str, object]:
    raw = get_backend_spec(target)
    if isinstance(raw, dict):
        return raw
    return {}


def _resolve_opts(spec: dict[str, object], layer: str, raw: dict[str, str]) -> dict[str, object]:
    out = resolve_layer_options(spec, layer, raw)
    if isinstance(out, dict):
        return out
    return {}


def _lower(spec: dict[str, object], east: dict[str, object], lower_options: dict[str, object]) -> dict[str, object]:
    out = lower_ir(spec, east, lower_options)
    if isinstance(out, dict):
        return out
    return {}


def _optimize(spec: dict[str, object], ir: dict[str, object], optimizer_options: dict[str, object]) -> dict[str, object]:
    out = optimize_ir(spec, ir, optimizer_options)
    if isinstance(out, dict):
        return out
    return {}


def _emit(
    spec: dict[str, object],
    ir: dict[str, object],
    output_path: Path,
    emitter_options: dict[str, object],
) -> str:
    out = emit_source(spec, ir, output_path, emitter_options)
    if isinstance(out, str):
        return out
    return ""


def _apply_runtime(spec: dict[str, object], output_path: Path) -> None:
    apply_runtime_hook(spec, output_path)


def _fatal(msg: str) -> None:
    sys.write_stderr("error: " + msg + "\n")
    sys.exit(2)


def _print_help() -> None:
    parts = [
        "usage: py2x-selfhost.py INPUT.py --target {cpp,rs,cs,js,ts,go,java,kotlin,swift,ruby,lua,scala,php,nim} ",
        "[-o OUTPUT] [--parser-backend self_hosted] [--east-stage 3] [--object-dispatch-mode {native,type_id}] ",
        "[--east3-opt-level {0,1,2}] [--east3-opt-pass SPEC] [--dump-east3-before-opt PATH] ",
        "[--dump-east3-after-opt PATH] [--dump-east3-opt-trace PATH] [--lower-option key=value] ",
        "[--optimizer-option key=value] [--emitter-option key=value]",
    ]
    print("".join(parts))


def _extract_layer_options(argv: list[str]) -> tuple[list[str], dict[str, list[str]]]:
    cleaned: list[str] = []
    lower_items: list[str] = []
    optimizer_items: list[str] = []
    emitter_items: list[str] = []
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok == "--lower-option" or tok == "--optimizer-option" or tok == "--emitter-option":
            if i + 1 >= len(argv):
                _fatal("missing value for " + tok)
            val = argv[i + 1]
            if tok == "--lower-option":
                lower_items.append(val)
            elif tok == "--optimizer-option":
                optimizer_items.append(val)
            else:
                emitter_items.append(val)
            i += 2
            continue
        cleaned.append(tok)
        i += 1
    options: dict[str, list[str]] = {
        "lower": lower_items,
        "optimizer": optimizer_items,
        "emitter": emitter_items,
    }
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


def _take_option_value(argv: list[str], index: int, flag: str) -> tuple[str, int]:
    if index + 1 >= len(argv):
        _fatal("missing value for " + flag)
    return argv[index + 1], index + 2


def _require_choice(flag: str, value: str, choices: list[str]) -> str:
    if value not in choices:
        _fatal("invalid choice for " + flag + ": " + value)
    return value


def main() -> int:
    argv: list[str] = sys.argv[1:]
    for arg in argv:
        if arg == "-h" or arg == "--help":
            _print_help()
            return 0

    cleaned_argv, layer_option_items = _extract_layer_options(argv)
    input_text = ""
    output_text = ""
    parser_backend = "self_hosted"
    object_dispatch_mode = "native"
    east3_opt_level = "1"
    east3_opt_pass = ""
    dump_east3_before_opt = ""
    dump_east3_after_opt = ""
    dump_east3_opt_trace = ""
    target = ""
    east_stage = "3"
    target_choices: list[str] = _list_targets()
    i = 0
    while i < len(cleaned_argv):
        tok = cleaned_argv[i]
        if tok == "-o" or tok == "--output":
            output_text, i = _take_option_value(cleaned_argv, i, tok)
            continue
        if tok == "--parser-backend":
            value, i = _take_option_value(cleaned_argv, i, tok)
            parser_backend = _require_choice(tok, value, ["self_hosted"])
            continue
        if tok == "--object-dispatch-mode":
            value, i = _take_option_value(cleaned_argv, i, tok)
            object_dispatch_mode = _require_choice(tok, value, ["native", "type_id"])
            continue
        if tok == "--east3-opt-level":
            value, i = _take_option_value(cleaned_argv, i, tok)
            east3_opt_level = _require_choice(tok, value, ["0", "1", "2"])
            continue
        if tok == "--east3-opt-pass":
            east3_opt_pass, i = _take_option_value(cleaned_argv, i, tok)
            continue
        if tok == "--dump-east3-before-opt":
            dump_east3_before_opt, i = _take_option_value(cleaned_argv, i, tok)
            continue
        if tok == "--dump-east3-after-opt":
            dump_east3_after_opt, i = _take_option_value(cleaned_argv, i, tok)
            continue
        if tok == "--dump-east3-opt-trace":
            dump_east3_opt_trace, i = _take_option_value(cleaned_argv, i, tok)
            continue
        if tok == "--target":
            value, i = _take_option_value(cleaned_argv, i, tok)
            target = _require_choice(tok, value, target_choices)
            continue
        if tok == "--east-stage":
            value, i = _take_option_value(cleaned_argv, i, tok)
            east_stage = _require_choice(tok, value, ["2", "3"])
            continue
        if tok != "" and tok[0] == "-":
            _fatal("unknown option: " + tok)
        if input_text != "":
            _fatal("unexpected extra argument: " + tok)
        input_text = tok
        i += 1

    if input_text == "":
        _fatal("missing required argument: input")
    if target == "":
        _fatal("--target is required")

    input_path = Path(input_text)
    output_path = Path(output_text) if output_text != "" else _default_output(input_path, target)
    if east_stage == "2":
        _fatal("--east-stage 2 is no longer supported; use EAST3 (default).")

    spec = _get_spec(target)
    lower_raw = _parse_layer_option_items(layer_option_items["lower"], "--lower-option")
    optimizer_raw = _parse_layer_option_items(layer_option_items["optimizer"], "--optimizer-option")
    emitter_raw = _parse_layer_option_items(layer_option_items["emitter"], "--emitter-option")
    lower_options: dict[str, object] = {}
    optimizer_options: dict[str, object] = {}
    emitter_options: dict[str, object] = {}
    try:
        lower_options = _resolve_opts(spec, "lower", lower_raw)
        optimizer_options = _resolve_opts(spec, "optimizer", optimizer_raw)
        emitter_options = _resolve_opts(spec, "emitter", emitter_raw)
    except Exception as ex:
        _fatal(str(ex))

    target_lang = str(spec.get("target_lang", target))
    east = _load_east3(
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
    ir = _lower(spec, east, lower_options)
    ir = _optimize(spec, ir, optimizer_options)
    out_src = _emit(spec, ir, output_path, emitter_options)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(out_src, encoding="utf-8")
    _apply_runtime(spec, output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
