"""Explicit JSON-object adapter seams for compiler tooling."""

from __future__ import annotations

from pytra.std import json
from pytra.std.pathlib import Path


def _jv_to_object(v: json.JsonVal) -> object:
    """Recursively convert a JsonVal to a Python-native object."""
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        return v
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        vl: list[json.JsonVal] = v
        out_list: list[object] = []
        for x in vl:
            out_list.append(_jv_to_object(x))
        return out_list
    if isinstance(v, dict):
        vd: dict[str, json.JsonVal] = v
        out_dict: dict[str, object] = {}
        for k, vv in vd.items():
            out_dict[k] = _jv_to_object(vv)
        return out_dict
    return None


def _object_to_jv(v: object) -> json.JsonVal:
    """Recursively convert a Python-native object to a JsonVal."""
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        return v
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        vl2: list[object] = v
        out_list2: list[json.JsonVal] = []
        for x in vl2:
            out_list2.append(_object_to_jv(x))
        return out_list2
    if isinstance(v, dict):
        vd2: dict[str, object] = v
        out_dict2: dict[str, json.JsonVal] = {}
        for k, vv in vd2.items():
            if isinstance(k, str):
                out_dict2[k] = _object_to_jv(vv)
        return out_dict2
    return None


def empty_json_object_doc() -> json.JsonObj:
    return json.JsonObj({})


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
    dd: dict[str, object] = doc
    raw: dict[str, json.JsonVal] = {}
    for key, value in dd.items():
        if isinstance(key, str):
            raw[key] = _object_to_jv(value)
    return json.JsonObj(raw)


def json_value_as_object_doc_or_empty(value: json.JsonValue | None) -> json.JsonObj:
    if value is None:
        return empty_json_object_doc()
    doc = value.as_obj()
    if doc is None:
        return empty_json_object_doc()
    return doc


def export_json_object_dict(doc: json.JsonObj) -> dict[str, object]:
    out: dict[str, object] = {}
    for k, v in doc.raw.items():
        out[k] = _jv_to_object(v)
    return out


def coerce_json_object_dict(doc: object, *, label: str) -> dict[str, object]:
    return export_json_object_dict(coerce_json_object_doc(doc, label=label))


def json_array_length(doc: json.JsonArr) -> int:
    return len(doc.raw)


def export_json_value_raw(value: json.JsonValue | None) -> object | None:
    if value is None:
        return None
    return _jv_to_object(value.raw)


def dumps_object(
    obj: object,
    *,
    ensure_ascii: bool = True,
    indent: int | None = None,
    separators: tuple[str, str] | None = None,
) -> str:
    """Serialize a plain Python object (dict/list/str/int/float/bool/None) as JSON."""
    jv = _object_to_jv(obj)
    return json.dumps_jv(jv, ensure_ascii=ensure_ascii, indent=indent, separators=separators)


def unwrap_east_root_json_doc(doc: json.JsonObj) -> json.JsonObj | None:
    east_doc = doc.get_obj("east")
    if doc.get_bool("ok") is True and east_doc is not None:
        return east_doc
    if doc.get_str("kind") == "Module":
        return doc
    return None
