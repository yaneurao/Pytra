"""EAST2 stage helpers."""

from __future__ import annotations


def is_east_module_root(east_doc: dict[str, object]) -> bool:
    """`Module` ルートかどうかを判定する。"""
    if not isinstance(east_doc, dict):
        return False
    kind_obj = east_doc.get("kind")
    return isinstance(kind_obj, str) and kind_obj == "Module"


def normalize_east1_to_east2_document(east_doc: dict[str, object]) -> dict[str, object]:
    """`EAST1` ルートを `EAST2` 契約（stage=2）へ正規化する。"""
    if is_east_module_root(east_doc):
        stage_obj = east_doc.get("east_stage")
        if isinstance(stage_obj, int) and stage_obj == 1:
            east_doc["east_stage"] = 2
    return east_doc
