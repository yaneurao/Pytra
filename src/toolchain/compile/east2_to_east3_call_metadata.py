"""Call metadata and representative JSON decode helpers for EAST2 -> EAST3."""

from __future__ import annotations

from typing import Any

from toolchain.compile.east2_to_east3_nominal_adt_meta import _decorate_nominal_adt_ctor_call
from toolchain.compile.east2_to_east3_type_summary import _JSON_DECODE_META_KEY
from toolchain.compile.east2_to_east3_type_summary import _expr_type_summary
from toolchain.compile.east2_to_east3_type_summary import _json_nominal_type_name
from toolchain.compile.east2_to_east3_type_summary import _raise_json_contract_violation
from toolchain.compile.east2_to_east3_type_summary import _representative_json_contract_metadata
from toolchain.compile.east2_to_east3_type_summary import _type_expr_summary_from_node


def _infer_json_semantic_tag(call: dict[str, Any], *, legacy_compat_bridge_enabled: bool) -> str:
    semantic_tag_obj = call.get("semantic_tag")
    semantic_tag = semantic_tag_obj.strip() if isinstance(semantic_tag_obj, str) else ""
    if semantic_tag.startswith("json."):
        return semantic_tag
    module_id_obj = call.get("runtime_module_id")
    runtime_symbol_obj = call.get("runtime_symbol")
    module_id = module_id_obj.strip() if isinstance(module_id_obj, str) else ""
    runtime_symbol = runtime_symbol_obj.strip() if isinstance(runtime_symbol_obj, str) else ""
    if module_id == "pytra.std.json":
        if runtime_symbol == "loads":
            return "json.loads"
        if runtime_symbol == "loads_obj":
            return "json.loads_obj"
        if runtime_symbol == "loads_arr":
            return "json.loads_arr"
    func_obj = call.get("func")
    if isinstance(func_obj, dict) and func_obj.get("kind") == "Attribute":
        attr_obj = func_obj.get("attr")
        attr = attr_obj.strip() if isinstance(attr_obj, str) else ""
        owner_obj = func_obj.get("value")
        owner_summary = _expr_type_summary(owner_obj)
        owner_nominal_name = _json_nominal_type_name(owner_summary)
        if owner_nominal_name == "JsonValue" and attr in {"as_obj", "as_arr", "as_str", "as_int", "as_float", "as_bool"}:
            return "json.value." + attr
        if owner_nominal_name == "JsonObj" and attr in {
            "get",
            "get_obj",
            "get_arr",
            "get_str",
            "get_int",
            "get_float",
            "get_bool",
        }:
            return "json.obj." + attr
        if owner_nominal_name == "JsonArr" and attr in {
            "get",
            "get_obj",
            "get_arr",
            "get_str",
            "get_int",
            "get_float",
            "get_bool",
        }:
            return "json.arr." + attr
        if legacy_compat_bridge_enabled and attr in {"loads", "loads_obj", "loads_arr"}:
            owner_name = ""
            if isinstance(owner_obj, dict) and owner_obj.get("kind") == "Name":
                owner_name_obj = owner_obj.get("id")
                owner_name = owner_name_obj.strip() if isinstance(owner_name_obj, str) else ""
            if owner_name == "json":
                return "json." + attr
    return ""


def _build_json_decode_meta(call: dict[str, Any], semantic_tag: str) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "schema_version": 1,
        "semantic_tag": semantic_tag,
        "result_type": _type_expr_summary_from_node(call),
    }
    if semantic_tag.startswith("json.loads"):
        meta["decode_kind"] = "module_load"
        return meta
    func_obj = call.get("func")
    if not isinstance(func_obj, dict) or func_obj.get("kind") != "Attribute":
        meta["decode_kind"] = "helper_call"
        return meta
    owner_obj = func_obj.get("value")
    owner_summary = _expr_type_summary(owner_obj)
    _raise_json_contract_violation(semantic_tag, owner_summary)
    meta["decode_kind"] = "narrow"
    meta["receiver_type"] = owner_summary
    receiver_category = str(owner_summary.get("category", "unknown"))
    if receiver_category != "unknown":
        meta["receiver_category"] = receiver_category
    nominal_name = str(owner_summary.get("nominal_adt_name", "")).strip()
    if nominal_name != "":
        meta["receiver_nominal_adt_name"] = nominal_name
    nominal_family = str(owner_summary.get("nominal_adt_family", ""))
    if nominal_family != "":
        meta["receiver_nominal_adt_family"] = nominal_family
    return meta


def _lower_representative_json_decode_call(out_call: dict[str, Any]) -> dict[str, Any]:
    semantic_tag_obj = out_call.get("semantic_tag")
    semantic_tag = semantic_tag_obj.strip() if isinstance(semantic_tag_obj, str) else ""
    if semantic_tag != "json.value.as_obj":
        return out_call
    args_obj = out_call.get("args")
    args: list[Any] = args_obj if isinstance(args_obj, list) else []
    if len(args) != 0:
        return out_call
    func_obj = out_call.get("func")
    if not isinstance(func_obj, dict) or func_obj.get("kind") != "Attribute":
        return out_call
    receiver_node = func_obj.get("value")
    contract_source, result_contract, receiver_contract = _representative_json_contract_metadata(out_call, receiver_node)
    out_call["lowered_kind"] = "JsonDecodeCall"
    out_call["json_decode_receiver"] = receiver_node
    meta_obj = out_call.get(_JSON_DECODE_META_KEY)
    meta = dict(meta_obj) if isinstance(meta_obj, dict) else _build_json_decode_meta(out_call, semantic_tag)
    meta["ir_category"] = "JsonDecodeCall"
    meta["decode_entry"] = "json.value.as_obj"
    meta["contract_source"] = contract_source
    meta["result_type"] = result_contract
    meta["receiver_type"] = receiver_contract
    meta["receiver_category"] = receiver_contract.get("category", "unknown")
    nominal_name = str(receiver_contract.get("nominal_adt_name", ""))
    if nominal_name != "":
        meta["receiver_nominal_adt_name"] = nominal_name
    nominal_family = str(receiver_contract.get("nominal_adt_family", ""))
    if nominal_family != "":
        meta["receiver_nominal_adt_family"] = nominal_family
    out_call[_JSON_DECODE_META_KEY] = meta
    return out_call


def _decorate_call_metadata(call: dict[str, Any], *, legacy_compat_bridge_enabled: bool) -> dict[str, Any]:
    call = _decorate_nominal_adt_ctor_call(call)
    json_tag = _infer_json_semantic_tag(call, legacy_compat_bridge_enabled=legacy_compat_bridge_enabled)
    if json_tag != "":
        call["semantic_tag"] = json_tag
        call[_JSON_DECODE_META_KEY] = _build_json_decode_meta(call, json_tag)
        call = _lower_representative_json_decode_call(call)
    return call
