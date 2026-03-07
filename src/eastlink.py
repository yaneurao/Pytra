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
from toolchain.link import save_manifest_doc


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


def _module_output_map(link_output_doc: dict[str, object]) -> dict[str, str]:
    modules_any = link_output_doc.get("modules", [])
    out: dict[str, str] = {}
    if not isinstance(modules_any, list):
        return out
    for item in modules_any:
        if not isinstance(item, dict):
            continue
        module_id = item.get("module_id")
        output = item.get("output")
        if isinstance(module_id, str) and module_id != "" and isinstance(output, str) and output != "":
            out[module_id] = output
    return out


def _write_linked_output(output_dir: Path, link_output_doc: dict[str, object]) -> Path:
    output_path = output_dir / "link-output.json"
    save_manifest_doc(output_path, link_output_doc)
    return output_path


def _write_linked_modules(output_dir: Path, linked_modules: tuple[Any, ...], link_output_doc: dict[str, object]) -> list[Path]:
    output_map = _module_output_map(link_output_doc)
    written: list[Path] = []
    for module in linked_modules:
        module_id = getattr(module, "module_id", "")
        east_doc = getattr(module, "east_doc", {})
        if not isinstance(module_id, str) or module_id == "" or not isinstance(east_doc, dict):
            continue
        rel_path = output_map.get(module_id, "linked/" + module_id.replace(".", "/") + ".east3.json")
        output_path = output_dir / rel_path
        save_manifest_doc(output_path, east_doc)
        written.append(output_path)
    return written


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
        output_dir.mkdir(parents=True, exist_ok=True)
        link_output_path = _write_linked_output(output_dir, link_output_doc)
        linked_paths = _write_linked_modules(output_dir, result.linked_program.modules, link_output_doc)
    except Exception as ex:
        return _fatal(str(ex))

    print("generated: " + str(link_output_path))
    for path in linked_paths:
        print("generated: " + str(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
