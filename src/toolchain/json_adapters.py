"""Explicit JSON-object adapter seams for compiler tooling."""

from __future__ import annotations

from pytra.std import json
from pytra.std.pathlib import Path


def load_json_object_doc(path: Path, *, label: str) -> json.JsonObj:
    if path.exists() is False:
        raise RuntimeError(label + " not found: " + str(path))
    try:
        payload = json.loads_obj(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError("failed to parse " + label + ": " + str(path) + ": " + str(exc)) from exc
    if payload is None:
        raise RuntimeError(label + " root must be an object: " + str(path))
    return payload


def load_json_object_doc_or_none(path: Path) -> json.JsonObj | None:
    return json.loads_obj(path.read_text(encoding="utf-8"))


def coerce_json_object_doc(doc: object, *, label: str) -> json.JsonObj:
    if isinstance(doc, json.JsonObj):
        return doc
    if not isinstance(doc, dict):
        raise RuntimeError(label + " must be an object")
    out: dict[str, object] = {}
    for key, value in doc.items():
        if isinstance(key, str):
            out[key] = value
    return json.JsonObj(out)


def export_json_object_dict(doc: json.JsonObj) -> dict[str, object]:
    return dict(doc.raw)


def json_array_length(doc: json.JsonArr) -> int:
    return len(doc.raw)


def export_json_value_raw(value: json.JsonValue | None) -> object | None:
    if value is None:
        return None
    return value.raw


def unwrap_east_root_json_doc(doc: json.JsonObj) -> json.JsonObj | None:
    east_doc = doc.get_obj("east")
    if doc.get_bool("ok") is True and east_doc is not None:
        return east_doc
    if doc.get_str("kind") == "Module":
        return doc
    return None
