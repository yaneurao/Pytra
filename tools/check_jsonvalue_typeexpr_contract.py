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

from src.toolchain.compiler.east_parts.east2_to_east3_lowering import lower_east2_to_east3
from src.toolchain.frontends.type_expr import parse_type_expr_text


@dataclass(frozen=True)
class Finding:
    key: str
    detail: str


def _probe_typeexpr_lane() -> dict[str, object]:
    east2 = {
        "kind": "Module",
        "meta": {"dispatch_mode": "native"},
        "body": [
            {
                "kind": "Expr",
                "value": {
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
                },
            }
        ],
    }
    out = lower_east2_to_east3(east2)
    return out.get("body", [])[0].get("value", {})


def _probe_resolved_type_compat_lane() -> dict[str, object]:
    east2 = {
        "kind": "Module",
        "meta": {"dispatch_mode": "native"},
        "body": [
            {
                "kind": "Expr",
                "value": {
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
                },
            }
        ],
    }
    out = lower_east2_to_east3(east2)
    return out.get("body", [])[0].get("value", {})


def _probe_contract_mismatch_error() -> str:
    east2 = {
        "kind": "Module",
        "meta": {"dispatch_mode": "native"},
        "body": [
            {
                "kind": "Expr",
                "value": {
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
                },
            }
        ],
    }
    try:
        lower_east2_to_east3(east2)
    except RuntimeError as ex:
        return str(ex)
    return ""


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

    mismatch_err = _probe_contract_mismatch_error()
    if "json_decode_contract_violation" not in mismatch_err:
        findings.append(Finding("mismatch_guard", "receiver/semantic_tag mismatch must fail with json_decode_contract_violation"))

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
