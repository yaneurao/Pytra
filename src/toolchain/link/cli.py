#!/usr/bin/env python3
"""pytra link: .py → linked EAST (compile + link + optimize → link-output.json).

Takes a .py entry point, builds the full module graph, links, optimizes,
and writes link-output.json + linked module files.
"""

from __future__ import annotations

from pytra.std import sys
from pytra.std.pathlib import Path
from toolchain.misc.typed_boundary import export_compiler_root_document
from toolchain.frontends.extern_var import validate_ambient_global_target_support
from toolchain.frontends import build_module_east_map
from toolchain.frontends import load_east3_document_typed
from toolchain.link import build_linked_program_from_module_map
from toolchain.link import optimize_linked_program
from toolchain.link import write_link_output_bundle
from toolchain.link.program_loader import add_runtime_east_to_module_map


def main(argv: list[str] | None = None) -> int:
    argv = list(argv) if argv is not None else sys.argv[1:]
    input_text = ""
    output_dir_text = ""
    target = "cpp"

    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok == "--output-dir" and i + 1 < len(argv):
            output_dir_text = argv[i + 1]
            i += 2
            continue
        if tok == "--target" and i + 1 < len(argv):
            target = argv[i + 1]
            i += 2
            continue
        if tok == "-h" or tok == "--help":
            print("usage: pytra link INPUT.py --output-dir DIR [--target TARGET]")
            return 0
        if not tok.startswith("-") and input_text == "":
            input_text = tok
        i += 1

    if input_text == "":
        print("error: input file is required", file=__import__("sys").stderr)
        return 1
    if output_dir_text == "":
        output_dir_text = "out/linked"

    input_path = Path(input_text)

    def _load_for_program(
        module_path: Path,
        parser_backend: str = "self_hosted",
        east_stage: str = "3",
        object_dispatch_mode: str = "",
    ) -> dict[str, object]:
        _ = east_stage
        return export_compiler_root_document(
            load_east3_document_typed(
                module_path,
                parser_backend=parser_backend,
                object_dispatch_mode=object_dispatch_mode if object_dispatch_mode != "" else "native",
                east3_opt_level="1",
                east3_opt_pass="",
                dump_east3_before_opt="",
                dump_east3_after_opt="",
                dump_east3_opt_trace="",
                target_lang=target,
            )
        )

    module_map = build_module_east_map(
        input_path,
        _load_for_program,
        parser_backend="self_hosted",
        east_stage="3",
        object_dispatch_mode="native",
    )
    module_map = add_runtime_east_to_module_map(module_map)
    program = build_linked_program_from_module_map(
        input_path,
        module_map,
        target=target,
        dispatch_mode="native",
        options={},
    )
    for linked_module in program.modules:
        validate_ambient_global_target_support(linked_module.east_doc, target=target)

    output_dir = Path(output_dir_text)
    link_output_path, linked_paths = write_link_output_bundle(
        output_dir, optimize_linked_program(program)
    )
    print("generated: " + str(link_output_path))
    for p in linked_paths:
        print("generated: " + str(p))
    return 0


if __name__ == "__main__":
    sys.exit(main())
