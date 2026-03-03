"""EAST1 stage helpers."""

from __future__ import annotations

from pytra.std.pathlib import Path
from pytra.std.typing import Any


def normalize_east1_root_document(east_doc: dict[str, object]) -> dict[str, object]:
    """`Module` ルートに `east_stage=1` を付与する。"""
    if isinstance(east_doc, dict):
        kind_obj = east_doc.get("kind")
        if isinstance(kind_obj, str) and kind_obj == "Module":
            east_doc["east_stage"] = 1
    return east_doc


def load_east1_document(
    input_path: Path,
    parser_backend: str = "self_hosted",
    load_east_document_fn: Any = None,
) -> dict[str, object]:
    """`load_east_document` 互換 loader を通して EAST1 ルートを返す。"""
    if load_east_document_fn is None:
        raise RuntimeError("load_east_document_fn is required")
    east_any = load_east_document_fn(input_path, parser_backend=parser_backend)
    if isinstance(east_any, dict):
        east_doc: dict[str, object] = east_any
        return normalize_east1_root_document(east_doc)
    raise RuntimeError("EAST1 root must be a dict")
