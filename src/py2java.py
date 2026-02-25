#!/usr/bin/env python3
"""EAST -> Java transpiler CLI."""

from __future__ import annotations

from pytra.std.typing import Any

from hooks.java.emitter.java_emitter import load_java_profile, transpile_to_java
from hooks.js.emitter.js_emitter import transpile_to_js
from pytra.compiler.east_parts.east3_legacy_compat import normalize_east3_to_legacy
from pytra.compiler.js_runtime_shims import write_js_runtime_shims
from pytra.compiler.transpile_cli import add_common_transpile_args, load_east3_document, load_east_document_compat
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
    """入力パスから既定の `.java` 出力先を決定する。"""
    out = str(input_path)
    if out.endswith(".py"):
        out = out[:-3] + ".java"
    elif out.endswith(".json"):
        out = out[:-5] + ".java"
    else:
        out = out + ".java"
    return Path(out)


def _arg_get_str(args: dict[str, Any], key: str, default_value: str = "") -> str:
    """argparse(dict) から文字列値を取り出す。"""
    if key not in args:
        return default_value
    val = args[key]
    if isinstance(val, str):
        return val
    return default_value


def _sidecar_js_path(output_path: Path) -> Path:
    """Java 出力に対応する sidecar JS のパスを返す。"""
    out = str(output_path)
    if out.endswith(".java"):
        return Path(out[:-5] + ".js")
    return Path(out + ".js")


def _java_class_name_from_path(output_path: Path) -> str:
    """出力ファイル名から Java クラス名を決める。"""
    stem = output_path.stem
    if stem == "":
        return "Main"
    chars: list[str] = []
    i = 0
    while i < len(stem):
        ch = stem[i]
        if ch.isalnum() or ch == "_":
            chars.append(ch)
        else:
            chars.append("_")
        i += 1
    out = "".join(chars)
    if out == "":
        out = "Main"
    if out[0].isdigit():
        out = "Pytra_" + out
    return out


def main() -> int:
    """CLI 入口。"""
    parser = argparse.ArgumentParser(description="Pytra EAST -> Java transpiler")
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
    js_output_path = _sidecar_js_path(output_path)
    js_src = transpile_to_js(east)
    class_name = _java_class_name_from_path(output_path)
    java_src = transpile_to_java(east, js_entry_path=str(js_output_path), class_name=class_name)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(java_src, encoding="utf-8")
    js_output_path.write_text(js_src, encoding="utf-8")
    write_js_runtime_shims(js_output_path.parent)
    return 0


if __name__ == "__main__":
    _ = load_java_profile
    sys.exit(main())
