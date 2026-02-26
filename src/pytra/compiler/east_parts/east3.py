"""EAST3 stage helpers."""

from __future__ import annotations

from pytra.compiler.east_parts.east2_to_east3_lowering import lower_east2_to_east3
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
    load_east_document_fn: Any = None,
    make_user_error_fn: Any = None,
) -> dict[str, object]:
    """入力ファイルを読み込み、`EAST2 -> EAST3` lower を適用して返す。"""
    if load_east_document_fn is None:
        raise RuntimeError("load_east_document_fn is required")
    east2_any = load_east_document_fn(input_path, parser_backend=parser_backend)
    if isinstance(east2_any, dict):
        east2_doc: dict[str, object] = east2_any
        return lower_east2_to_east3_document(east2_doc, object_dispatch_mode=object_dispatch_mode)
    if callable(make_user_error_fn):
        raise make_user_error_fn(
            "input_invalid",
            "Failed to build EAST3.",
            ["EAST3 root must be a dict."],
        )
    raise RuntimeError("Failed to build EAST3.")
