#!/usr/bin/env python3
"""EAST -> JavaScript transpiler CLI."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.js.emitter.js_emitter import load_js_profile, transpile_to_js
from pytra.compiler.east_parts.core import convert_path
from pytra.compiler.transpile_cli import add_common_transpile_args
from pytra.std import argparse
from pytra.std import json
from pytra.std.pathlib import Path
from pytra.std import sys


def load_east(input_path: Path, parser_backend: str = "self_hosted") -> dict[str, Any]:
    """`.py` / `.json` を EAST ドキュメントへ読み込む。"""
    suffix = input_path.suffix.lower()
    if suffix == ".json":
        txt = input_path.read_text(encoding="utf-8")
        doc = json.loads(txt)
        if isinstance(doc, dict):
            return doc
        raise RuntimeError("EAST json root must be object")
    if suffix == ".py":
        return convert_path(input_path, parser_backend=parser_backend)
    raise RuntimeError("input must be .py or .json")


def _default_output_path(input_path: Path) -> Path:
    """入力パスから既定の `.js` 出力先を決定する。"""
    out = str(input_path)
    if out.endswith(".py"):
        out = out[:-3] + ".js"
    elif out.endswith(".json"):
        out = out[:-5] + ".js"
    else:
        out = out + ".js"
    return Path(out)


def _arg_get_str(args: dict[str, Any], key: str, default_value: str = "") -> str:
    """argparse(dict) から文字列値を取り出す。"""
    if key not in args:
        return default_value
    val = args[key]
    if isinstance(val, str):
        return val
    return default_value


def main() -> int:
    """CLI 入口。"""
    parser = argparse.ArgumentParser(description="Pytra EAST -> JavaScript transpiler")
    add_common_transpile_args(parser, parser_backends=["self_hosted"])
    args = parser.parse_args()
    if not isinstance(args, dict):
        raise RuntimeError("argparse result must be dict")

    input_path = Path(_arg_get_str(args, "input"))
    output_text = _arg_get_str(args, "output")
    output_path = Path(output_text) if output_text != "" else _default_output_path(input_path)
    parser_backend = _arg_get_str(args, "parser_backend")
    if parser_backend == "":
        parser_backend = "self_hosted"

    east = load_east(input_path, parser_backend=parser_backend)
    js_src = transpile_to_js(east)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(js_src, encoding="utf-8")
    return 0


if __name__ == "__main__":
    _ = load_js_profile
    sys.exit(main())

