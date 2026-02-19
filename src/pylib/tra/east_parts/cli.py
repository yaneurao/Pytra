#!/usr/bin/env python3
"""EAST CLI entrypoint."""
from __future__ import annotations

from pylib.std import argparse

from .core import EastBuildError, convert_path
from .human import _dump_json, render_east_human_cpp
from pylib.std.pathlib import Path
from pylib.std import sys

def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for EAST JSON/human-view generation."""
    parser = argparse.ArgumentParser(description="Convert Python source into EAST JSON")
    parser.add_argument("input", help="Input Python file")
    parser.add_argument("-o", "--output", help="Output EAST JSON path")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    parser.add_argument("--human-output", help="Output human-readable C++-style EAST path")
    parser.add_argument("--parser-backend", choices=["self_hosted"], default="self_hosted", help="Parser backend")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"error: input file not found: {input_path}", file=sys.stderr)
        return 1

    try:
        east = convert_path(input_path, parser_backend=args.parser_backend)
    except SyntaxError as exc:
        err = {
            "kind": "unsupported_syntax",
            "message": str(exc),
            "source_span": {
                "lineno": exc.lineno,
                "col": exc.offset,
                "end_lineno": exc.end_lineno,
                "end_col": exc.end_offset,
            },
            "hint": "Fix Python syntax errors before EAST conversion.",
        }
        out = {"ok": False, "error": err}
        payload = _dump_json(out, pretty=True)
        if args.output:
            out_path = Path(args.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(payload + "\n", encoding="utf-8")
        else:
            print(payload)
        if args.human_output:
            human_path = Path(args.human_output)
            human_path.parent.mkdir(parents=True, exist_ok=True)
            human_path.write_text(render_east_human_cpp(out), encoding="utf-8")
        return 1
    except EastBuildError as exc:
        out = {"ok": False, "error": exc.to_payload()}
        payload = _dump_json(out, pretty=True)
        if args.output:
            out_path = Path(args.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(payload + "\n", encoding="utf-8")
        else:
            print(payload)
        if args.human_output:
            human_path = Path(args.human_output)
            human_path.parent.mkdir(parents=True, exist_ok=True)
            human_path.write_text(render_east_human_cpp(out), encoding="utf-8")
        return 1

    out = {"ok": True, "east": east}
    payload = _dump_json(out, pretty=args.pretty)
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    if args.human_output:
        human_path = Path(args.human_output)
        human_path.parent.mkdir(parents=True, exist_ok=True)
        human_path.write_text(render_east_human_cpp(out), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
