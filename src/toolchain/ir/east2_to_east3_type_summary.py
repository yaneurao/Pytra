"""Shared type-summary and nominal/json contract helpers for EAST2 -> EAST3 lowering."""

from __future__ import annotations

from typing import Any

from toolchain.frontends.type_expr import summarize_type_expr
from toolchain.frontends.type_expr import summarize_type_text


_NOMINAL_ADT_DECL_SUMMARY_TABLE_HOLDER: list[dict[str, dict[str, Any]]] = [{}]
_TYPE_EXPR_SUMMARY_KEY = "type_expr_summary_v1"
_JSON_DECODE_META_KEY = "json_decode_v1"
_JSON_RECEIVER_NAME_PREFIXES = {
    "json.value.": "JsonValue",
    "json.obj.": "JsonObj",
    "json.arr.": "JsonArr",
}


def _swap_nominal_adt_decl_summary_table(table: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    prev = dict(_NOMINAL_ADT_DECL_SUMMARY_TABLE_HOLDER[0])
    _NOMINAL_ADT_DECL_SUMMARY_TABLE_HOLDER[0] = dict(table)
    return prev


def _normalize_type_name(value: Any) -> str:
    if isinstance(value, str):
        s: str = value
        t = s.strip()
        if t != "":
            return t
    return "unknown"


def _unknown_type_summary() -> dict[str, Any]:
    return {"kind": "unknown", "category": "unknown", "mirror": "unknown"}


def _type_expr_summary_from_payload(type_expr: Any, mirror: Any) -> dict[str, Any]:
    summary = summarize_type_expr(type_expr)
    if str(summary.get("category", "unknown")) != "unknown":
        return _hydrate_nominal_adt_summary(dict(summary), mirror)
    return _hydrate_nominal_adt_summary(dict(summarize_type_text(mirror)), mirror)


def _type_expr_summary_from_node(node: Any) -> dict[str, Any]:
    if not isinstance(node, dict):
        return _unknown_type_summary()
    nd: dict[str, Any] = node
    return _type_expr_summary_from_payload(nd.get("type_expr"), nd.get("resolved_type"))


def _lookup_nominal_adt_decl(name: Any) -> dict[str, Any] | None:
    type_name = _normalize_type_name(name)
    if type_name == "unknown":
        return None
    entry = _NOMINAL_ADT_DECL_SUMMARY_TABLE_HOLDER[0].get(type_name)
    if not isinstance(entry, dict):
        return None
    return dict(entry)


def _make_nominal_adt_type_summary(name: str, family_name: str) -> dict[str, Any]:
    return {
        "kind": "NominalAdtType",
        "category": "nominal_adt",
        "mirror": name,
        "nominal_adt_name": name,
        "nominal_adt_family": family_name,
        "nominal_variant_domain": "closed",
    }


def _hydrate_nominal_adt_summary(summary: dict[str, Any], mirror: Any) -> dict[str, Any]:
    category = str(summary.get("category", "unknown")).strip()
    summary_mirror = _normalize_type_name(summary.get("mirror"))
    if summary_mirror == "unknown":
        summary_mirror = _normalize_type_name(mirror)
    if category == "nominal_adt":
        return summary
    if category == "static":
        decl = _lookup_nominal_adt_decl(summary_mirror)
        if decl is None:
            return summary
        return _make_nominal_adt_type_summary(summary_mirror, str(decl.get("family_name", summary_mirror)))
    if category == "optional" and str(summary.get("nominal_adt_name", "")).strip() == "":
        if not summary_mirror.endswith(" | None"):
            return summary
        inner_name = summary_mirror[:-7].strip()
        decl = _lookup_nominal_adt_decl(inner_name)
        if decl is None:
            return summary
        out = dict(summary)
        out["nominal_adt_name"] = inner_name
        out["nominal_adt_family"] = str(decl.get("family_name", inner_name))
        out["nominal_variant_domain"] = "closed"
        out["inner_category"] = "nominal_adt"
        return out
    return summary


def _set_type_expr_summary(node: dict[str, Any], summary: dict[str, Any]) -> None:
    category = str(summary.get("category", "unknown")).strip()
    if category == "" or category == "unknown":
        return
    payload = {"schema_version": 1}
    for key, value in summary.items():
        payload[key] = value
    node[_TYPE_EXPR_SUMMARY_KEY] = payload


def _bridge_lane_payload(target_summary: dict[str, Any], value_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "target": dict(target_summary),
        "target_category": target_summary.get("category", "unknown"),
        "value": dict(value_summary),
        "value_category": value_summary.get("category", "unknown"),
    }


def _is_dynamic_like_summary(summary: dict[str, Any]) -> bool:
    category = str(summary.get("category", "unknown")).strip()
    if category == "dynamic" or category == "dynamic_union":
        return True
    mirror = str(summary.get("mirror", "unknown")).strip()
    return mirror == "Any" or mirror == "object" or mirror == "unknown"


def _collect_nominal_adt_decl_summary_table(east_module: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    body_obj = east_module.get("body")
    body: list[Any] = body_obj if isinstance(body_obj, list) else []
    for item in body:
        if not isinstance(item, dict):
            continue
        id2: dict[str, Any] = item
        if id2.get("kind") != "ClassDef":
            continue
        class_name = _normalize_type_name(id2.get("name"))
        if class_name == "unknown":
            continue
        meta_obj = id2.get("meta")
        meta = meta_obj if isinstance(meta_obj, dict) else {}
        nominal_obj = meta.get("nominal_adt_v1")
        nominal = nominal_obj if isinstance(nominal_obj, dict) else {}
        role = str(nominal.get("role", "")).strip()
        family_name = str(nominal.get("family_name", "")).strip()
        if (role != "family" and role != "variant") or family_name == "":
            continue
        entry: dict[str, Any] = {
            "role": role,
            "family_name": family_name,
        }
        variant_name = str(nominal.get("variant_name", "")).strip()
        if variant_name != "":
            entry["variant_name"] = variant_name
        payload_style = str(nominal.get("payload_style", "")).strip()
        if payload_style != "":
            entry["payload_style"] = payload_style
        field_types_obj = id2.get("field_types")
        if isinstance(field_types_obj, dict):
            ftd: dict[str, Any] = field_types_obj
            field_types: dict[str, str] = {}
            for field_name_obj, field_type_obj in ftd.items():
                field_name = str(field_name_obj).strip()
                if field_name == "":
                    continue
                field_type = _normalize_type_name(field_type_obj)
                if field_type == "unknown":
                    continue
                field_types[field_name] = field_type
            if len(field_types) != 0:
                entry["field_types"] = field_types
        out[class_name] = entry
    return out


def _collect_nominal_adt_family_variants(family_name: str) -> list[str]:
    variants: list[str] = []
    for type_name, entry in _NOMINAL_ADT_DECL_SUMMARY_TABLE_HOLDER[0].items():
        if not isinstance(entry, dict):
            continue
        if str(entry.get("role", "")).strip() != "variant":
            continue
        if str(entry.get("family_name", "")).strip() != family_name:
            continue
        if type_name not in variants:
            variants.append(type_name)
    return variants


def _expr_type_name(expr: Any) -> str:
    summary = _expr_type_summary(expr)
    mirror = _normalize_type_name(summary.get("mirror"))
    if mirror != "unknown":
        return mirror
    if isinstance(expr, dict):
        ed: dict[str, Any] = expr
        return _normalize_type_name(ed.get("resolved_type"))
    return "unknown"


def _expr_type_summary(expr: Any) -> dict[str, Any]:
    return _type_expr_summary_from_node(expr)


def _json_nominal_type_name(summary: dict[str, Any]) -> str:
    category = str(summary.get("category", "unknown")).strip()
    if category != "nominal_adt":
        return ""
    family = str(summary.get("nominal_adt_family", "")).strip()
    if family != "json":
        return ""
    nominal_name = str(summary.get("nominal_adt_name", "")).strip()
    if nominal_name != "":
        return nominal_name
    mirror = _normalize_type_name(summary.get("mirror"))
    if mirror in {"JsonValue", "JsonObj", "JsonArr"}:
        return mirror
    return ""


def _expected_json_receiver_type_name(semantic_tag: str) -> str:
    for prefix, nominal_name in _JSON_RECEIVER_NAME_PREFIXES.items():
        if semantic_tag.startswith(prefix):
            return nominal_name
    return ""


def _raise_json_contract_violation(semantic_tag: str, owner_summary: dict[str, Any]) -> None:
    expected = _expected_json_receiver_type_name(semantic_tag)
    if expected == "":
        return
    actual = _json_nominal_type_name(owner_summary)
    if actual == expected:
        return
    mirror = _normalize_type_name(owner_summary.get("mirror"))
    category = str(owner_summary.get("category", "unknown")).strip()
    actual_desc = actual if actual != "" else mirror
    if actual_desc == "":
        actual_desc = "unknown"
    raise RuntimeError(
        "json_decode_contract_violation: "
        + semantic_tag
        + " requires "
        + expected
        + " nominal receiver TypeExpr, got "
        + actual_desc
        + " ("
        + category
        + ")"
    )


def _structured_type_expr_summary_from_node(node: Any) -> dict[str, Any]:
    if not isinstance(node, dict):
        return _unknown_type_summary()
    nd2: dict[str, Any] = node
    return dict(summarize_type_expr(nd2.get("type_expr")))


def _representative_json_contract_metadata(call: dict[str, Any], receiver_node: Any) -> tuple[str, dict[str, Any], dict[str, Any]]:
    result_summary = _structured_type_expr_summary_from_node(call)
    receiver_summary = _structured_type_expr_summary_from_node(receiver_node)
    result_category = str(result_summary.get("category", "unknown"))
    result_family = str(result_summary.get("nominal_adt_family", ""))
    result_name = str(result_summary.get("nominal_adt_name", ""))
    receiver_category = str(receiver_summary.get("category", "unknown"))
    receiver_family = str(receiver_summary.get("nominal_adt_family", ""))
    receiver_name = str(receiver_summary.get("nominal_adt_name", ""))
    if (
        result_category == "optional"
        and result_family == "json"
        and result_name == "JsonObj"
        and receiver_category == "nominal_adt"
        and receiver_family == "json"
        and receiver_name == "JsonValue"
    ):
        return "type_expr", result_summary, receiver_summary
    compat_result = _type_expr_summary_from_node(call)
    compat_receiver = _expr_type_summary(receiver_node)
    compat_result_category = str(compat_result.get("category", "unknown"))
    compat_result_family = str(compat_result.get("nominal_adt_family", ""))
    compat_result_name = str(compat_result.get("nominal_adt_name", ""))
    compat_receiver_category = str(compat_receiver.get("category", "unknown"))
    compat_receiver_family = str(compat_receiver.get("nominal_adt_family", ""))
    compat_receiver_name = str(compat_receiver.get("nominal_adt_name", ""))
    if (
        compat_result_category == "optional"
        and compat_result_family == "json"
        and compat_result_name == "JsonObj"
        and compat_receiver_category == "nominal_adt"
        and compat_receiver_family == "json"
        and compat_receiver_name == "JsonValue"
    ):
        return "resolved_type_compat", compat_result, compat_receiver
    raise RuntimeError(
        "json.value.as_obj representative lane requires json nominal contract: "
        + "receiver="
        + compat_receiver_category
        + "/"
        + compat_receiver_family
        + "/"
        + compat_receiver_name
        + ", result="
        + compat_result_category
        + "/"
        + compat_result_family
        + "/"
        + compat_result_name
    )
