"""Explicit JSON-object adapter seams for compiler tooling."""

from __future__ import annotations

from pytra.std import json
from pytra.std.pathlib import Path


def _jv_to_object(v: json._JsonVal) -> object:
    """Recursively convert a _JsonVal to a Python-native object."""
    tag = v.tag
    if tag == json._JV_NULL:
        return None
    if tag == json._JV_BOOL:
        return v.bool_val
    if tag == json._JV_INT:
        return v.int_val
    if tag == json._JV_FLOAT:
        return v.float_val
    if tag == json._JV_STR:
        return v.str_val
    if tag == json._JV_ARR:
        return [_jv_to_object(x) for x in v.arr_val]
    if tag == json._JV_OBJ:
        return {k: _jv_to_object(vv) for k, vv in v.obj_val.items()}
    return None


def _object_to_jv(v: object) -> json._JsonVal:
    """Recursively convert a Python-native object to a _JsonVal."""
    if v is None:
        return json._jv_null()
    if isinstance(v, bool):
        return json._jv_bool(v)
    if isinstance(v, int):
        return json._jv_int(v)
    if isinstance(v, float):
        return json._jv_float(v)
    if isinstance(v, str):
        return json._jv_str(v)
    if isinstance(v, list):
        return json._jv_arr([_object_to_jv(x) for x in v])
    if isinstance(v, dict):
        return json._jv_obj({k: _object_to_jv(vv) for k, vv in v.items() if isinstance(k, str)})
    return json._jv_null()


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
    raw: dict[str, json._JsonVal] = {}
    for key, value in doc.items():
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


def unwrap_east_root_json_doc(doc: json.JsonObj) -> json.JsonObj | None:
    east_doc = doc.get_obj("east")
    if doc.get_bool("ok") is True and east_doc is not None:
        return east_doc
    if doc.get_str("kind") == "Module":
        return doc
    return None
