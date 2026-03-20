#!/usr/bin/env python3
"""Standalone C++ backend: linked EAST → C++ multi-file output.

This is the C++ backend entry point, independent of other language backends.
It reads a link-output.json (produced by ``pytra link --link-only``) and
emits C++ source files.

Usage:
    python3 east2cpp.py link-output.json --output-dir out/cpp/
"""

from __future__ import annotations

import sys

from backends.cpp.emitter.multifile_writer import write_multi_file_cpp
from toolchain.link import load_linked_output_bundle
from toolchain.link import LinkedProgramModule
from pytra.std.pathlib import Path


def _find_entry_path(
    linked_modules: tuple[LinkedProgramModule, ...],
    entry_modules: list[str],
) -> Path:
    entry_set = set(entry_modules)
    for module in linked_modules:
        if module.is_entry and module.module_id in entry_set:
            if module.source_path != "":
                return Path(module.source_path)
    return Path("main.py")


def _emit_cpp(
    linked_modules: tuple[LinkedProgramModule, ...],
    entry_modules: list[str],
    output_dir: Path,
    emitter_options: dict[str, str],
) -> dict[str, object]:
    module_east_map: dict[str, dict[str, object]] = {}
    entry_path = Path("")
    entry_set = set(entry_modules)
    for module in linked_modules:
        if module.module_id == "":
            continue
        mod_path = Path(module.source_path) if module.source_path != "" else Path(module.module_id + ".py")
        module_east_map[str(mod_path)] = module.east_doc
        if module.is_entry and module.module_id in entry_set:
            entry_path = mod_path
    if str(entry_path) == "":
        raise RuntimeError("linked C++ entry module not found")
    return write_multi_file_cpp(
        entry_path,
        module_east_map,
        output_dir,
        negative_index_mode=emitter_options.get("negative_index_mode", "const_only"),
        bounds_check_mode=emitter_options.get("bounds_check_mode", "off"),
        floor_div_mode=emitter_options.get("floor_div_mode", "native"),
        mod_mode=emitter_options.get("mod_mode", "native"),
        int_width=emitter_options.get("int_width", "64"),
        str_index_mode=emitter_options.get("str_index_mode", "native"),
        str_slice_mode=emitter_options.get("str_slice_mode", "byte"),
        opt_level=emitter_options.get("opt_level", "2"),
        top_namespace="",
        emit_main=True,
    )


def _parse_emitter_option(raw: str) -> tuple[str, str]:
    pos = raw.find("=")
    if pos <= 0:
        return "", ""
    return raw[:pos], raw[pos + 1 :]


def main() -> int:
    argv = sys.argv[1:]
    if len(argv) == 0 or argv[0] in ("-h", "--help"):
        print("usage: east2cpp.py LINK_OUTPUT.json --output-dir DIR [--emitter-option key=value ...]")
        return 0

    input_path = ""
    output_dir = ""
    emitter_options: dict[str, str] = {}
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok == "--output-dir" and i + 1 < len(argv):
            output_dir = argv[i + 1]
            i += 2
            continue
        if tok == "--emitter-option" and i + 1 < len(argv):
            k, v = _parse_emitter_option(argv[i + 1])
            if k != "":
                emitter_options[k] = v
            i += 2
            continue
        if not tok.startswith("-") and input_path == "":
            input_path = tok
            i += 1
            continue
        i += 1

    if input_path == "":
        print("error: input link-output.json is required", file=sys.stderr)
        return 1
    if output_dir == "":
        output_dir = "out/cpp"

    manifest_doc, linked_modules = load_linked_output_bundle(Path(input_path))
    entry_modules_any = manifest_doc.get("entry_modules", [])
    entry_modules: list[str] = []
    if isinstance(entry_modules_any, (list, tuple)):
        for item in entry_modules_any:
            if isinstance(item, str) and item != "":
                entry_modules.append(item)

    result = _emit_cpp(linked_modules, entry_modules, Path(output_dir), emitter_options)
    print("generated: " + output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
