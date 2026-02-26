"""EAST3 stage helpers."""

from __future__ import annotations

from pytra.compiler.east_parts.east2_to_east3_lowering import lower_east2_to_east3
from pytra.compiler.east_parts.east3_optimizer import optimize_east3_document
from pytra.compiler.east_parts.east3_optimizer import render_east3_opt_trace
from pytra.std import json
from pytra.std.pathlib import Path
from pytra.std.typing import Any


def lower_east2_to_east3_document(
    east2_doc: dict[str, object],
    object_dispatch_mode: str = "",
) -> dict[str, object]:
    """公開委譲: `EAST2 -> EAST3` lower を実行する。"""
    out_any = lower_east2_to_east3(east2_doc, object_dispatch_mode=object_dispatch_mode)
    if isinstance(out_any, dict):
        out_doc: dict[str, object] = out_any
        return out_doc
    raise RuntimeError("EAST3 root must be a dict")


def load_east3_document(
    input_path: Path,
    parser_backend: str = "self_hosted",
    object_dispatch_mode: str = "",
    east3_opt_level: str | int | object = 1,
    east3_opt_pass: str = "",
    dump_east3_before_opt: str = "",
    dump_east3_after_opt: str = "",
    dump_east3_opt_trace: str = "",
    target_lang: str = "",
    load_east_document_fn: Any = None,
    make_user_error_fn: Any = None,
) -> dict[str, object]:
    """入力ファイルを読み込み、`EAST2 -> EAST3` lower を適用して返す。"""
    if load_east_document_fn is None:
        raise RuntimeError("load_east_document_fn is required")
    east2_any = load_east_document_fn(input_path, parser_backend=parser_backend)
    if isinstance(east2_any, dict):
        east2_doc: dict[str, object] = east2_any
        east3_doc = lower_east2_to_east3_document(east2_doc, object_dispatch_mode=object_dispatch_mode)
        if dump_east3_before_opt != "":
            before_path = Path(dump_east3_before_opt)
            before_path.parent.mkdir(parents=True, exist_ok=True)
            before_path.write_text(json.dumps(east3_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        optimized_doc, report = optimize_east3_document(
            east3_doc,
            opt_level=east3_opt_level,
            target_lang=target_lang,
            opt_pass_spec=east3_opt_pass,
        )
        if dump_east3_after_opt != "":
            after_path = Path(dump_east3_after_opt)
            after_path.parent.mkdir(parents=True, exist_ok=True)
            after_path.write_text(json.dumps(optimized_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if dump_east3_opt_trace != "":
            trace_path = Path(dump_east3_opt_trace)
            trace_path.parent.mkdir(parents=True, exist_ok=True)
            trace_path.write_text(render_east3_opt_trace(report), encoding="utf-8")
        return optimized_doc
    if callable(make_user_error_fn):
        raise make_user_error_fn(
            "input_invalid",
            "Failed to build EAST3.",
            ["EAST3 root must be a dict."],
        )
    raise RuntimeError("Failed to build EAST3.")
