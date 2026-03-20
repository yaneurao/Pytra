#!/usr/bin/env python3
"""Guard representative JsonValue TypeExpr contract lanes against regression."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from toolchain.compile.east2_to_east3_lowering import lower_east2_to_east3
from toolchain.frontends.type_expr import parse_type_expr_text


@dataclass(frozen=True)
class Finding:
    key: str
    detail: str


def _lower_expr(expr: dict[str, object]) -> dict[str, object]:
    east2 = {
        "kind": "Module",
        "meta": {"dispatch_mode": "native"},
        "body": [{"kind": "Expr", "value": expr}],
    }
    out = lower_east2_to_east3(east2)
    return out.get("body", [])[0].get("value", {})


def _probe_typeexpr_lane() -> dict[str, object]:
    return _lower_expr(
        {
            "kind": "Call",
            "resolved_type": "JsonObj | None",
            "type_expr": parse_type_expr_text("JsonObj | None"),
            "func": {
                "kind": "Attribute",
                "attr": "as_obj",
                "value": {
                    "kind": "Name",
                    "id": "payload",
                    "resolved_type": "unknown",
                    "type_expr": parse_type_expr_text("JsonValue"),
                },
            },
            "args": [],
            "keywords": [],
        }
    )


def _probe_resolved_type_compat_lane() -> dict[str, object]:
    return _lower_expr(
        {
            "kind": "Call",
            "resolved_type": "JsonObj | None",
            "func": {
                "kind": "Attribute",
                "attr": "as_obj",
                "value": {"kind": "Name", "id": "payload", "resolved_type": "JsonValue"},
            },
            "args": [],
            "keywords": [],
            "semantic_tag": "json.value.as_obj",
        }
    )


def _probe_json_obj_lane() -> dict[str, object]:
    return _lower_expr(
        {
            "kind": "Call",
            "resolved_type": "int64 | None",
            "type_expr": parse_type_expr_text("int | None"),
            "func": {
                "kind": "Attribute",
                "attr": "get_int",
                "value": {
                    "kind": "Name",
                    "id": "payload",
                    "resolved_type": "unknown",
                    "type_expr": parse_type_expr_text("JsonObj"),
                },
            },
            "args": [{"kind": "Constant", "value": "age", "resolved_type": "str"}],
            "keywords": [],
        }
    )


def _probe_json_arr_lane() -> dict[str, object]:
    return _lower_expr(
        {
            "kind": "Call",
            "resolved_type": "bool | None",
            "type_expr": parse_type_expr_text("bool | None"),
            "func": {
                "kind": "Attribute",
                "attr": "get_bool",
                "value": {
                    "kind": "Name",
                    "id": "payload",
                    "resolved_type": "unknown",
                    "type_expr": parse_type_expr_text("JsonArr"),
                },
            },
            "args": [{"kind": "Constant", "value": 0, "resolved_type": "int64"}],
            "keywords": [],
        }
    )


def _probe_loads_obj_lane() -> dict[str, object]:
    return _lower_expr(
        {
            "kind": "Call",
            "resolved_type": "JsonObj | None",
            "type_expr": parse_type_expr_text("JsonObj | None"),
            "func": {
                "kind": "Attribute",
                "value": {"kind": "Name", "id": "json", "resolved_type": "unknown"},
                "attr": "loads_obj",
                "resolved_type": "unknown",
            },
            "args": [{"kind": "Name", "id": "text", "resolved_type": "str"}],
            "keywords": [],
            "runtime_module_id": "pytra.std.json",
            "runtime_symbol": "loads_obj",
        }
    )


def _lower_mismatch_error(expr: dict[str, object]) -> str:
    try:
        _lower_expr(expr)
    except RuntimeError as ex:
        return str(ex)
    return ""


def _probe_representative_mismatch_error() -> str:
    return _lower_mismatch_error(
        {
            "kind": "Call",
            "resolved_type": "JsonObj | None",
            "type_expr": parse_type_expr_text("JsonObj | None"),
            "semantic_tag": "json.value.as_obj",
            "func": {
                "kind": "Attribute",
                "attr": "as_obj",
                "value": {
                    "kind": "Name",
                    "id": "payload",
                    "resolved_type": "JsonObj",
                    "type_expr": parse_type_expr_text("JsonObj"),
                },
            },
            "args": [],
            "keywords": [],
        }
    )


def _probe_json_obj_mismatch_error() -> str:
    return _lower_mismatch_error(
        {
            "kind": "Call",
            "resolved_type": "int64 | None",
            "type_expr": parse_type_expr_text("int | None"),
            "semantic_tag": "json.obj.get_int",
            "func": {
                "kind": "Attribute",
                "attr": "get_int",
                "value": {
                    "kind": "Name",
                    "id": "payload",
                    "resolved_type": "JsonValue",
                    "type_expr": parse_type_expr_text("JsonValue"),
                },
            },
            "args": [{"kind": "Constant", "value": "age", "resolved_type": "str"}],
            "keywords": [],
        }
    )


def _collect_findings() -> list[Finding]:
    findings: list[Finding] = []

    typeexpr_lane = _probe_typeexpr_lane()
    if typeexpr_lane.get("lowered_kind") != "JsonDecodeCall":
        findings.append(Finding("typeexpr_lane_kind", "representative TypeExpr lane must lower to JsonDecodeCall"))
    typeexpr_meta = typeexpr_lane.get("json_decode_v1", {})
    if not isinstance(typeexpr_meta, dict) or typeexpr_meta.get("contract_source") != "type_expr":
        findings.append(Finding("typeexpr_lane_contract", "representative TypeExpr lane must report contract_source=type_expr"))
    if not isinstance(typeexpr_meta, dict) or typeexpr_meta.get("receiver_nominal_adt_name") != "JsonValue":
        findings.append(
            Finding("typeexpr_lane_receiver_name", "representative TypeExpr lane must retain receiver_nominal_adt_name=JsonValue")
        )

    compat_lane = _probe_resolved_type_compat_lane()
    if compat_lane.get("lowered_kind") != "JsonDecodeCall":
        findings.append(Finding("compat_lane_kind", "migration compat lane must still lower to JsonDecodeCall"))
    compat_meta = compat_lane.get("json_decode_v1", {})
    if not isinstance(compat_meta, dict) or compat_meta.get("contract_source") != "resolved_type_compat":
        findings.append(
            Finding("compat_lane_contract", "migration compat lane must be labeled contract_source=resolved_type_compat")
        )

    obj_lane = _probe_json_obj_lane()
    obj_meta = obj_lane.get("json_decode_v1", {})
    if obj_lane.get("semantic_tag") != "json.obj.get_int":
        findings.append(Finding("json_obj_semantic_tag", "JsonObj helper lane must keep semantic_tag=json.obj.get_int"))
    if not isinstance(obj_meta, dict) or obj_meta.get("receiver_nominal_adt_name") != "JsonObj":
        findings.append(Finding("json_obj_receiver", "JsonObj helper lane must retain receiver_nominal_adt_name=JsonObj"))

    arr_lane = _probe_json_arr_lane()
    arr_meta = arr_lane.get("json_decode_v1", {})
    if arr_lane.get("semantic_tag") != "json.arr.get_bool":
        findings.append(Finding("json_arr_semantic_tag", "JsonArr helper lane must keep semantic_tag=json.arr.get_bool"))
    if not isinstance(arr_meta, dict) or arr_meta.get("receiver_nominal_adt_name") != "JsonArr":
        findings.append(Finding("json_arr_receiver", "JsonArr helper lane must retain receiver_nominal_adt_name=JsonArr"))

    loads_obj_lane = _probe_loads_obj_lane()
    loads_obj_meta = loads_obj_lane.get("json_decode_v1", {})
    if loads_obj_lane.get("semantic_tag") != "json.loads_obj":
        findings.append(Finding("loads_obj_semantic_tag", "module load lane must keep semantic_tag=json.loads_obj"))
    if not isinstance(loads_obj_meta, dict) or loads_obj_meta.get("decode_kind") != "module_load":
        findings.append(Finding("loads_obj_decode_kind", "module load lane must keep decode_kind=module_load"))
    result_type = loads_obj_meta.get("result_type", {})
    if not isinstance(result_type, dict) or result_type.get("nominal_adt_name") != "JsonObj":
        findings.append(Finding("loads_obj_result_type", "module load lane must retain JsonObj nominal result metadata"))

    rep_mismatch_err = _probe_representative_mismatch_error()
    if "json_decode_contract_violation" not in rep_mismatch_err:
        findings.append(
            Finding("representative_mismatch_guard", "representative receiver mismatch must fail with json_decode_contract_violation")
        )

    obj_mismatch_err = _probe_json_obj_mismatch_error()
    if "json_decode_contract_violation" not in obj_mismatch_err:
        findings.append(Finding("json_obj_mismatch_guard", "JsonObj helper mismatch must fail with json_decode_contract_violation"))

    return findings


def main() -> int:
    findings = _collect_findings()
    if len(findings) > 0:
        print("[FAIL] jsonvalue TypeExpr contract guard failed")
        for item in findings:
            print(" -", item.key + ":", item.detail)
        return 1

    print("[OK] jsonvalue TypeExpr contract guard passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
