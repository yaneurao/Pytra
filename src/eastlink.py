#!/usr/bin/env python3
"""Linked-program frontend: link-input.json -> link-output.json + linked modules."""

from __future__ import annotations

from typing import Any

from pytra.std import argparse
from pytra.std.pathlib import Path
from pytra.std import sys

from toolchain.link import LINK_OUTPUT_SCHEMA
from toolchain.link import load_linked_program
from toolchain.link import optimize_linked_program
from toolchain.link import write_link_output_bundle


def _arg_get_str(args: dict[str, Any], key: str, default_value: str = "") -> str:
    if key not in args:
        return default_value
    value = args[key]
    if isinstance(value, str):
        return value
    return default_value


def _fatal(msg: str) -> int:
    sys.write_stderr("error: " + msg + "\n")
    return 1


def main(argv: list[str] | None = None) -> int:
    argv_list = list(argv) if isinstance(argv, list) else (sys.argv[1:] if isinstance(sys.argv, list) else [])

    parser = argparse.ArgumentParser(description="Pytra linked-program optimizer frontend")
    parser.add_argument("input", help="Input link-input.json")
    parser.add_argument("--output-dir", default="out/linked", help="Output directory for link-output and linked modules")
    args = parser.parse_args(argv_list)
    if not isinstance(args, dict):
        raise RuntimeError("argparse result must be dict")

    input_path = Path(_arg_get_str(args, "input"))
    if input_path == Path(""):
        return _fatal("input is required")
    output_dir_txt = _arg_get_str(args, "output_dir", "out/linked")
    output_dir = Path(output_dir_txt) if output_dir_txt != "" else Path("out/linked")

    try:
        program = load_linked_program(input_path)
        result = optimize_linked_program(program)
        link_output_doc = result.link_output_doc
        if not isinstance(link_output_doc, dict) or link_output_doc.get("schema") != LINK_OUTPUT_SCHEMA:
            return _fatal("invalid linked optimizer output")
        link_output_path, linked_paths = write_link_output_bundle(output_dir, result)
    except Exception as ex:
        return _fatal(str(ex))

    print("generated: " + str(link_output_path))
    for path in linked_paths:
        print("generated: " + str(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
