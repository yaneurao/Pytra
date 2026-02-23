#!/usr/bin/env python3
"""EAST -> Rust transpiler CLI."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.rs.emitter.rs_emitter import load_rs_profile, transpile_to_rust
from pytra.compiler.transpile_cli import (
    add_common_transpile_args,
    dict_any_get_str,
    load_east_document,
    parse_user_error,
)
from pytra.std import argparse
from pytra.std.pathlib import Path
from pytra.std import sys


def load_east(input_path: Path, parser_backend: str = "self_hosted") -> dict[str, Any]:
    """`.py` / `.json` を EAST ドキュメントへ読み込む。"""
    suffix = input_path.suffix.lower()
    if suffix != ".json" and suffix != ".py":
        raise RuntimeError("input must be .py or .json")
    try:
        doc = load_east_document(input_path, parser_backend=parser_backend)
    except RuntimeError as ex:
        if suffix == ".json":
            parsed = parse_user_error(str(ex))
            if dict_any_get_str(parsed, "category") == "input_invalid":
                raise RuntimeError("EAST json root must be object") from ex
        raise
    if isinstance(doc, dict):
        return doc
    if suffix == ".json":
        raise RuntimeError("EAST json root must be object")
    raise RuntimeError("EAST root must be dict")


def _default_output_path(input_path: Path) -> Path:
    """入力パスから既定の `.rs` 出力先を決定する。"""
    out = str(input_path)
    if out.endswith(".py"):
        out = out[:-3] + ".rs"
    elif out.endswith(".json"):
        out = out[:-5] + ".rs"
    else:
        out = out + ".rs"
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
    parser = argparse.ArgumentParser(description="Pytra EAST -> Rust transpiler")
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
    rust_src = transpile_to_rust(east)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rust_src, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
