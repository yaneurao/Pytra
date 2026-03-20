#!/usr/bin/env python3
"""Selfhost frontend: Python/EAST3 -> C++ source.

This entrypoint is backend_registry free. It imports only the C++ emitter
directly, avoiding all non-C++ backend dependencies. For other targets,
use east2x.py.
"""

from __future__ import annotations

from backends.cpp.emitter import transpile_to_cpp
from toolchain.frontends import load_east3_document_typed
from pytra.std.pathlib import Path
from pytra.std import sys


def _fatal(msg: str) -> None:
    sys.write_stderr("error: " + msg + "\n")
    sys.exit(2)


def _print_help() -> None:
    parts = [
        "usage: py2x-selfhost.py INPUT.py [--target cpp] ",
        "[-o OUTPUT] [--parser-backend self_hosted] ",
        "[--object-dispatch-mode {native,type_id}] ",
        "[--east3-opt-level {0,1,2}] [--east3-opt-pass SPEC] ",
        "[--dump-east3-before-opt PATH] [--dump-east3-after-opt PATH] ",
        "[--dump-east3-opt-trace PATH] [--emitter-option key=value]",
    ]
    print("".join(parts))


def _take_option_value(argv: list[str], index: int, flag: str) -> tuple[str, int]:
    if index + 1 >= len(argv):
        _fatal("missing value for " + flag)
    return argv[index + 1], index + 2


def _require_choice(flag: str, value: str, choices: list[str]) -> str:
    if value not in choices:
        _fatal("invalid choice for " + flag + ": " + value)
    return value


def _parse_emitter_options(items: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items:
        pos = item.find("=")
        if pos <= 0:
            _fatal("--emitter-option must be key=value: " + item)
        key = item[:pos]
        value = item[pos + 1 :]
        if key == "":
            _fatal("--emitter-option key must not be empty")
        out[key] = value
    return out


def main() -> int:
    argv: list[str] = sys.argv[1:]
    for arg in argv:
        if arg == "-h" or arg == "--help":
            _print_help()
            return 0

    input_text = ""
    output_text = ""
    parser_backend = "self_hosted"
    object_dispatch_mode = "native"
    east3_opt_level = "1"
    east3_opt_pass = ""
    dump_east3_before_opt = ""
    dump_east3_after_opt = ""
    dump_east3_opt_trace = ""
    target = "cpp"
    emitter_items: list[str] = []

    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok == "-o" or tok == "--output":
            output_text, i = _take_option_value(argv, i, tok)
            continue
        if tok == "--parser-backend":
            value, i = _take_option_value(argv, i, tok)
            parser_backend = _require_choice(tok, value, ["self_hosted"])
            continue
        if tok == "--object-dispatch-mode":
            value, i = _take_option_value(argv, i, tok)
            object_dispatch_mode = _require_choice(tok, value, ["native", "type_id"])
            continue
        if tok == "--east3-opt-level":
            value, i = _take_option_value(argv, i, tok)
            east3_opt_level = _require_choice(tok, value, ["0", "1", "2"])
            continue
        if tok == "--east3-opt-pass":
            east3_opt_pass, i = _take_option_value(argv, i, tok)
            continue
        if tok == "--dump-east3-before-opt":
            dump_east3_before_opt, i = _take_option_value(argv, i, tok)
            continue
        if tok == "--dump-east3-after-opt":
            dump_east3_after_opt, i = _take_option_value(argv, i, tok)
            continue
        if tok == "--dump-east3-opt-trace":
            dump_east3_opt_trace, i = _take_option_value(argv, i, tok)
            continue
        if tok == "--target":
            value, i = _take_option_value(argv, i, tok)
            target = _require_choice(tok, value, ["cpp"])
            continue
        if tok == "--emitter-option":
            if i + 1 >= len(argv):
                _fatal("missing value for --emitter-option")
            emitter_items.append(argv[i + 1])
            i += 2
            continue
        # Ignore legacy flags gracefully.
        if tok == "--east-stage":
            _, i = _take_option_value(argv, i, tok)
            continue
        if tok == "--lower-option" or tok == "--optimizer-option":
            _, i = _take_option_value(argv, i, tok)
            continue
        if tok != "" and tok[0] == "-":
            _fatal("unknown option: " + tok)
        if input_text != "":
            _fatal("unexpected extra argument: " + tok)
        input_text = tok
        i += 1

    if input_text == "":
        _fatal("missing required argument: input")

    input_path = Path(input_text)
    output_path = Path(output_text) if output_text != "" else Path("out") / (input_path.stem + ".cpp")
    emitter_options = _parse_emitter_options(emitter_items)

    try:
        east = load_east3_document_typed(
            input_path,
            parser_backend=parser_backend,
            object_dispatch_mode=object_dispatch_mode,
            east3_opt_level=east3_opt_level,
            east3_opt_pass=east3_opt_pass,
            dump_east3_before_opt=dump_east3_before_opt,
            dump_east3_after_opt=dump_east3_after_opt,
            dump_east3_opt_trace=dump_east3_opt_trace,
            target_lang="cpp",
        )
        cpp_text = transpile_to_cpp(
            east,
            negative_index_mode=emitter_options.get("negative_index_mode", "const_only"),
            bounds_check_mode=emitter_options.get("bounds_check_mode", "off"),
            floor_div_mode=emitter_options.get("floor_div_mode", "native"),
            mod_mode=emitter_options.get("mod_mode", "native"),
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(cpp_text, encoding="utf-8")
    except Exception as ex:
        _fatal(str(ex))
    return 0


if __name__ == "__main__":
    sys.exit(main())
