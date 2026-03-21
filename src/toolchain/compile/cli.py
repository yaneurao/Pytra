#!/usr/bin/env python3
"""pytra compile: .py → .east (EAST3 JSON)."""

from __future__ import annotations

from pytra.std import sys
from pytra.std import json
from pytra.std.pathlib import Path
from toolchain.misc.typed_boundary import export_compiler_root_document
from toolchain.frontends import load_east3_document_typed


def main(argv: list[str] | None = None) -> int:
    argv = list(argv) if argv is not None else sys.argv[1:]
    input_text = ""
    output_text = ""
    east3_opt_level = "1"
    east3_opt_pass = ""
    target_lang = ""

    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok == "-o" or tok == "--output":
            if i + 1 >= len(argv):
                print("error: missing value for " + tok, file=__import__("sys").stderr)
                return 1
            output_text = argv[i + 1]
            i += 2
            continue
        if tok == "--east3-opt-level":
            if i + 1 >= len(argv):
                print("error: missing value for " + tok, file=__import__("sys").stderr)
                return 1
            east3_opt_level = argv[i + 1]
            i += 2
            continue
        if tok == "--east3-opt-pass":
            if i + 1 >= len(argv):
                print("error: missing value for " + tok, file=__import__("sys").stderr)
                return 1
            east3_opt_pass = argv[i + 1]
            i += 2
            continue
        if tok == "--target-lang":
            if i + 1 >= len(argv):
                print("error: missing value for " + tok, file=__import__("sys").stderr)
                return 1
            target_lang = argv[i + 1]
            i += 2
            continue
        if tok == "-h" or tok == "--help":
            print("usage: pytra compile INPUT.py [-o OUTPUT.east] [--east3-opt-level {0,1,2}]")
            return 0
        if not tok.startswith("-") and input_text == "":
            input_text = tok
        i += 1

    if input_text == "":
        print("error: input file is required", file=__import__("sys").stderr)
        return 1
    if output_text == "":
        output_text = input_text.removesuffix(".py") + ".east"

    input_path = Path(input_text)
    output_path = Path(output_text)

    east_doc = export_compiler_root_document(
        load_east3_document_typed(
            input_path,
            parser_backend="self_hosted",
            object_dispatch_mode="native",
            east3_opt_level=east3_opt_level,
            east3_opt_pass=east3_opt_pass,
            dump_east3_before_opt="",
            dump_east3_after_opt="",
            dump_east3_opt_trace="",
            target_lang=target_lang,
        )
    )
    import json as _json
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        _json.dumps(east_doc, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    print("compiled: " + str(output_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
