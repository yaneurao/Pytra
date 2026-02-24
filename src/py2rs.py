#!/usr/bin/env python3
"""EAST -> Rust transpiler CLI."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.rs.emitter.rs_emitter import load_rs_profile, transpile_to_rust
from pytra.compiler.east_parts.east3_legacy_compat import normalize_east3_to_legacy
from pytra.compiler.transpile_cli import (
    add_common_transpile_args,
    load_east3_document,
    load_east_document_compat,
)
from pytra.std import argparse
from pytra.std.pathlib import Path
from pytra.std import sys


def load_east(
    input_path: Path,
    parser_backend: str = "self_hosted",
    east_stage: str = "3",
    object_dispatch_mode: str = "native",
) -> dict[str, Any]:
    """`.py` / `.json` を EAST ドキュメントへ読み込む。"""
    if east_stage == "3":
        doc3 = load_east3_document(
            input_path,
            parser_backend=parser_backend,
            object_dispatch_mode=object_dispatch_mode,
        )
        normalized = normalize_east3_to_legacy(doc3)
        return normalized if isinstance(normalized, dict) else {}
    if east_stage == "2":
        doc2 = load_east_document_compat(input_path, parser_backend=parser_backend)
        return doc2
    raise RuntimeError("invalid east_stage: " + east_stage)


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
    parser.add_argument("--east-stage", choices=["2", "3"], help="EAST stage mode (default: 3)")
    parser.add_argument(
        "--object-dispatch-mode",
        choices=["native", "type_id"],
        help="Object boundary dispatch mode used by EAST2->EAST3 lowering",
    )
    args = parser.parse_args()
    if not isinstance(args, dict):
        raise RuntimeError("argparse result must be dict")

    input_path = Path(_arg_get_str(args, "input"))
    output_text = _arg_get_str(args, "output")
    output_path = Path(output_text) if output_text != "" else _default_output_path(input_path)
    parser_backend = _arg_get_str(args, "parser_backend")
    if parser_backend == "":
        parser_backend = "self_hosted"
    east_stage = _arg_get_str(args, "east_stage")
    if east_stage == "":
        east_stage = "3"
    object_dispatch_mode = _arg_get_str(args, "object_dispatch_mode")
    if object_dispatch_mode == "":
        object_dispatch_mode = "native"
    if east_stage == "2":
        print("warning: --east-stage 2 is compatibility mode; default is 3.", file=sys.stderr)

    east = load_east(
        input_path,
        parser_backend=parser_backend,
        east_stage=east_stage,
        object_dispatch_mode=object_dispatch_mode,
    )
    rust_src = transpile_to_rust(east)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rust_src, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
