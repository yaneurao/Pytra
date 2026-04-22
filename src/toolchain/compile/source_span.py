"""Source span normalization for EAST2 → EAST3.

Renames col → col_offset, end_col → end_col_offset.
Removes Module-level source_span (which has null fields).

§5.1: Any/object 禁止。
"""

from __future__ import annotations

from toolchain.compile.jv import JsonVal, Node, jv_is_dict, jv_is_list, jv_dict, jv_list, jv_str
from toolchain.common.kinds import MODULE


def normalize_source_span(span: JsonVal) -> JsonVal:
    """Rename col -> col_offset, end_col -> end_col_offset in a source_span."""
    if not jv_is_dict(span):
        return span
    d: Node = jv_dict(span)
    out: dict[str, JsonVal] = {}
    for k, v in d.items():
        if k == "col":
            out["col_offset"] = v
        elif k == "end_col":
            out["end_col_offset"] = v
        else:
            out[k] = v
    return out


def walk_normalize_spans(node: JsonVal) -> JsonVal:
    """Recursively rename source_span fields and remove Module source_span."""
    if jv_is_list(node):
        result: list[JsonVal] = []
        for item in jv_list(node):
            result.append(walk_normalize_spans(item))
        return result
    if not jv_is_dict(node):
        return node
    d: Node = jv_dict(node)
    kind = jv_str(d.get("kind", ""))
    out: dict[str, JsonVal] = {}
    for k, v in d.items():
        if k == "source_span":
            if kind == MODULE:
                continue
            out[k] = normalize_source_span(v)
        else:
            out[k] = walk_normalize_spans(v)
    return out
