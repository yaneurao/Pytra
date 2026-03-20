"""Nominal ADT ctor/projection/match metadata helpers for EAST2 -> EAST3."""

from __future__ import annotations

from typing import Any

from toolchain.compile.east2_to_east3_type_summary import _collect_nominal_adt_family_variants
from toolchain.compile.east2_to_east3_type_summary import _expr_type_summary
from toolchain.compile.east2_to_east3_type_summary import _lookup_nominal_adt_decl
from toolchain.compile.east2_to_east3_type_summary import _make_nominal_adt_type_summary
from toolchain.compile.east2_to_east3_type_summary import _normalize_type_name
from toolchain.compile.east2_to_east3_type_summary import _set_type_expr_summary
from toolchain.compile.east2_to_east3_type_summary import _type_expr_summary_from_payload


def _build_nominal_adt_ctor_meta(call: dict[str, Any]) -> dict[str, Any] | None:
    func_obj = call.get("func")
    if not isinstance(func_obj, dict) or func_obj.get("kind") != "Name":
        return None
    ctor_name = _normalize_type_name(func_obj.get("id"))
    decl = _lookup_nominal_adt_decl(ctor_name)
    if decl is None or str(decl.get("role", "")).strip() != "variant":
        return None
    payload_style = str(decl.get("payload_style", "")).strip()
    if payload_style == "":
        payload_style = "unit"
    return {
        "schema_version": 1,
        "ir_category": "NominalAdtCtorCall",
        "family_name": str(decl.get("family_name", ctor_name)),
        "variant_name": ctor_name,
        "payload_style": payload_style,
    }


def _decorate_nominal_adt_ctor_call(call: dict[str, Any]) -> dict[str, Any]:
    meta = _build_nominal_adt_ctor_meta(call)
    if meta is None:
        return call
    call["semantic_tag"] = "nominal_adt.variant_ctor"
    call["lowered_kind"] = "NominalAdtCtorCall"
    call["nominal_adt_ctor_v1"] = meta
    _set_type_expr_summary(call, _make_nominal_adt_type_summary(str(meta["variant_name"]), str(meta["family_name"])))
    return call


def _build_nominal_adt_projection_meta(attr_expr: dict[str, Any]) -> dict[str, Any] | None:
    attr_name = str(attr_expr.get("attr", "")).strip()
    if attr_name == "":
        return None
    owner_summary = _expr_type_summary(attr_expr.get("value"))
    if str(owner_summary.get("category", "unknown")).strip() != "nominal_adt":
        return None
    variant_name = _normalize_type_name(owner_summary.get("nominal_adt_name"))
    if variant_name == "unknown":
        variant_name = _normalize_type_name(owner_summary.get("mirror"))
    decl = _lookup_nominal_adt_decl(variant_name)
    if decl is None or str(decl.get("role", "")).strip() != "variant":
        return None
    field_types_obj = decl.get("field_types")
    field_types = field_types_obj if isinstance(field_types_obj, dict) else {}
    field_type = _normalize_type_name(field_types.get(attr_name))
    if field_type == "unknown":
        return None
    meta: dict[str, Any] = {
        "schema_version": 1,
        "ir_category": "NominalAdtProjection",
        "family_name": str(decl.get("family_name", variant_name)),
        "variant_name": variant_name,
        "field_name": attr_name,
        "field_type": field_type,
    }
    payload_style = str(decl.get("payload_style", "")).strip()
    if payload_style != "":
        meta["payload_style"] = payload_style
    return meta


def _decorate_nominal_adt_projection_attr(attr_expr: dict[str, Any]) -> dict[str, Any]:
    meta = _build_nominal_adt_projection_meta(attr_expr)
    if meta is None:
        return attr_expr
    field_type = str(meta.get("field_type", "unknown"))
    attr_expr["semantic_tag"] = "nominal_adt.variant_projection"
    attr_expr["lowered_kind"] = "NominalAdtProjection"
    attr_expr["nominal_adt_projection_v1"] = meta
    attr_expr["resolved_type"] = field_type
    _set_type_expr_summary(attr_expr, _type_expr_summary_from_payload(None, field_type))
    return attr_expr


def _pattern_bind_names(subpatterns: Any) -> list[str]:
    if not isinstance(subpatterns, list):
        return []
    out: list[str] = []
    for item in subpatterns:
        if not isinstance(item, dict) or item.get("kind") != "PatternBind":
            continue
        name = str(item.get("name", "")).strip()
        if name != "":
            out.append(name)
    return out


def _decorate_nominal_adt_pattern_bind(
    bind_pattern: dict[str, Any],
    *,
    family_name: str,
    variant_name: str,
    field_name: str,
    field_type: str,
) -> dict[str, Any]:
    if bind_pattern.get("kind") != "PatternBind":
        return bind_pattern
    meta: dict[str, Any] = {
        "schema_version": 1,
        "ir_category": "NominalAdtPatternBind",
        "family_name": family_name,
        "variant_name": variant_name,
    }
    if field_name != "":
        meta["field_name"] = field_name
    if field_type != "unknown":
        meta["field_type"] = field_type
    bind_pattern["lowered_kind"] = "NominalAdtPatternBind"
    bind_pattern["semantic_tag"] = "nominal_adt.pattern_bind"
    bind_pattern["nominal_adt_pattern_bind_v1"] = meta
    if field_type != "unknown":
        bind_pattern["resolved_type"] = field_type
        _set_type_expr_summary(bind_pattern, _type_expr_summary_from_payload(None, field_type))
    return bind_pattern


def _build_nominal_adt_variant_pattern_meta(pattern: dict[str, Any]) -> dict[str, Any] | None:
    if pattern.get("kind") != "VariantPattern":
        return None
    variant_name = _normalize_type_name(pattern.get("variant_name"))
    if variant_name == "unknown":
        return None
    decl = _lookup_nominal_adt_decl(variant_name)
    if decl is None or str(decl.get("role", "")).strip() != "variant":
        return None
    family_name = str(pattern.get("family_name", "")).strip()
    decl_family = str(decl.get("family_name", variant_name)).strip()
    if family_name == "":
        family_name = decl_family
    elif decl_family != "" and family_name != decl_family:
        return None
    payload_style = str(decl.get("payload_style", "")).strip()
    if payload_style == "":
        payload_style = "unit"
    subpatterns_obj = pattern.get("subpatterns")
    subpatterns = subpatterns_obj if isinstance(subpatterns_obj, list) else []
    return {
        "schema_version": 1,
        "ir_category": "NominalAdtVariantPattern",
        "family_name": family_name,
        "variant_name": variant_name,
        "payload_style": payload_style,
        "payload_arity": len(subpatterns),
        "bind_names": _pattern_bind_names(subpatterns),
    }


def _decorate_nominal_adt_variant_pattern(pattern: dict[str, Any]) -> dict[str, Any]:
    meta = _build_nominal_adt_variant_pattern_meta(pattern)
    if meta is None:
        return pattern
    pattern["lowered_kind"] = "NominalAdtVariantPattern"
    pattern["semantic_tag"] = "nominal_adt.variant_pattern"
    pattern["nominal_adt_pattern_v1"] = meta

    decl = _lookup_nominal_adt_decl(meta.get("variant_name"))
    field_types_obj = decl.get("field_types") if isinstance(decl, dict) else None
    field_entries = list(field_types_obj.items()) if isinstance(field_types_obj, dict) else []
    subpatterns_obj = pattern.get("subpatterns")
    subpatterns = subpatterns_obj if isinstance(subpatterns_obj, list) else []
    for index, subpattern in enumerate(subpatterns):
        if not isinstance(subpattern, dict):
            continue
        field_name = ""
        field_type = "unknown"
        if index < len(field_entries):
            field_name = str(field_entries[index][0]).strip()
            field_type = _normalize_type_name(field_entries[index][1])
        _decorate_nominal_adt_pattern_bind(
            subpattern,
            family_name=str(meta.get("family_name", "")),
            variant_name=str(meta.get("variant_name", "")),
            field_name=field_name,
            field_type=field_type,
        )
    return pattern


def _nominal_adt_family_name_from_summary(summary: dict[str, Any]) -> str:
    family_name = str(summary.get("nominal_adt_family", "")).strip()
    if family_name != "":
        return family_name
    if str(summary.get("category", "unknown")).strip() != "nominal_adt":
        return ""
    nominal_name = str(summary.get("nominal_adt_name", "")).strip()
    if nominal_name != "":
        return nominal_name
    mirror = _normalize_type_name(summary.get("mirror"))
    if mirror != "unknown":
        return mirror
    return ""


def _build_nominal_adt_match_analysis(match_stmt: dict[str, Any]) -> dict[str, Any] | None:
    subject_summary = _expr_type_summary(match_stmt.get("subject"))
    family_name = _nominal_adt_family_name_from_summary(subject_summary)
    if family_name == "":
        return None
    family_variants = _collect_nominal_adt_family_variants(family_name)
    if len(family_variants) == 0:
        return None

    cases_obj = match_stmt.get("cases")
    cases: list[Any] = cases_obj if isinstance(cases_obj, list) else []
    covered_set: set[str] = set()
    duplicate_case_indexes: list[int] = []
    unreachable_case_indexes: list[int] = []
    invalid = False
    wildcard_seen = False

    for idx in range(len(cases)):
        case = cases[idx]
        case_pattern: Any = None
        if isinstance(case, dict):
            cd: dict[str, Any] = case
            case_pattern = cd.get("pattern")
        pattern = case_pattern
        if not isinstance(pattern, dict):
            invalid = True
            continue
        pd: dict[str, Any] = pattern
        pattern_kind = str(pd.get("kind", "")).strip()
        if pattern_kind == "VariantPattern":
            variant_family = str(pd.get("family_name", "")).strip()
            variant_name = _normalize_type_name(pd.get("variant_name"))
            if variant_family != family_name or variant_name not in family_variants:
                invalid = True
                continue
            decl = _lookup_nominal_adt_decl(variant_name)
            if decl is None:
                invalid = True
                continue
            subpatterns_obj = pd.get("subpatterns")
            subpatterns: list[Any] = subpatterns_obj if isinstance(subpatterns_obj, list) else []
            field_types_obj = decl.get("field_types")
            field_types = field_types_obj if isinstance(field_types_obj, dict) else {}
            if len(subpatterns) != len(field_types):
                invalid = True
            if wildcard_seen and idx not in unreachable_case_indexes:
                unreachable_case_indexes.append(idx)
            if variant_name in covered_set:
                duplicate_case_indexes.append(idx)
                if idx not in unreachable_case_indexes:
                    unreachable_case_indexes.append(idx)
                continue
            covered_set.add(variant_name)
            continue
        if pattern_kind == "PatternWildcard":
            if wildcard_seen:
                duplicate_case_indexes.append(idx)
                if idx not in unreachable_case_indexes:
                    unreachable_case_indexes.append(idx)
                continue
            wildcard_seen = True
            continue
        invalid = True

    covered_variants = [variant for variant in family_variants if variant in covered_set]
    if wildcard_seen:
        covered_variants = list(family_variants)
        uncovered_variants: list[str] = []
        coverage_kind = "wildcard_terminal"
    else:
        uncovered_variants = [variant for variant in family_variants if variant not in covered_set]
        coverage_kind = "exhaustive" if len(uncovered_variants) == 0 else "partial"
    if invalid or len(duplicate_case_indexes) != 0 or len(unreachable_case_indexes) != 0:
        coverage_kind = "invalid"

    return {
        "schema_version": 1,
        "family_name": family_name,
        "coverage_kind": coverage_kind,
        "covered_variants": covered_variants,
        "uncovered_variants": uncovered_variants,
        "duplicate_case_indexes": duplicate_case_indexes,
        "unreachable_case_indexes": unreachable_case_indexes,
    }


def _decorate_nominal_adt_match_stmt(match_stmt: dict[str, Any]) -> dict[str, Any]:
    analysis = _build_nominal_adt_match_analysis(match_stmt)
    if analysis is None:
        return match_stmt
    subject_summary = _expr_type_summary(match_stmt.get("subject"))
    match_stmt["lowered_kind"] = "NominalAdtMatch"
    match_stmt["semantic_tag"] = "nominal_adt.match"
    match_stmt["nominal_adt_match_v1"] = {
        "schema_version": 1,
        "ir_category": "NominalAdtMatch",
        "family_name": analysis.get("family_name", ""),
        "coverage_kind": analysis.get("coverage_kind", "invalid"),
        "covered_variants": list(analysis.get("covered_variants", [])),
        "uncovered_variants": list(analysis.get("uncovered_variants", [])),
        "subject_type": dict(subject_summary),
    }
    meta_obj = match_stmt.get("meta")
    meta = dict(meta_obj) if isinstance(meta_obj, dict) else {}
    meta["match_analysis_v1"] = analysis
    match_stmt["meta"] = meta
    cases_obj = match_stmt.get("cases")
    cases: list[Any] = cases_obj if isinstance(cases_obj, list) else []
    for case in cases:
        if not isinstance(case, dict):
            continue
        cd2: dict[str, Any] = case
        pattern2 = cd2.get("pattern")
        if not isinstance(pattern2, dict):
            continue
        pd2: dict[str, Any] = pattern2
        if pd2.get("kind") != "VariantPattern":
            continue
        variant_name = _normalize_type_name(pd2.get("variant_name"))
        decl = _lookup_nominal_adt_decl(variant_name)
        if decl is None:
            continue
        payload_style = str(decl.get("payload_style", "")).strip()
        if payload_style == "":
            payload_style = "unit"
        field_types_obj = decl.get("field_types")
        field_types = field_types_obj if isinstance(field_types_obj, dict) else {}
        field_names = list(field_types.keys())
        bind_names: list[str] = []
        pd2["lowered_kind"] = "NominalAdtVariantPattern"
        pd2["semantic_tag"] = "nominal_adt.variant_pattern"
        pd2["nominal_adt_pattern_v1"] = {
            "schema_version": 1,
            "ir_category": "NominalAdtVariantPattern",
            "family_name": str(decl.get("family_name", variant_name)),
            "variant_name": variant_name,
            "payload_style": payload_style,
            "bind_names": bind_names,
        }
        subpatterns_obj = pd2.get("subpatterns")
        subpatterns: list[Any] = subpatterns_obj if isinstance(subpatterns_obj, list) else []
        for idx in range(len(subpatterns)):
            subpattern = subpatterns[idx]
            if not isinstance(subpattern, dict):
                continue
            spd: dict[str, Any] = subpattern
            if spd.get("kind") != "PatternBind":
                continue
            field_name = field_names[idx] if idx < len(field_names) else ""
            field_type = _normalize_type_name(field_types.get(field_name))
            bind_name = str(spd.get("name", "")).strip()
            if bind_name != "":
                bind_names.append(bind_name)
            spd["lowered_kind"] = "NominalAdtPatternBind"
            spd["semantic_tag"] = "nominal_adt.pattern_bind"
            spd["nominal_adt_pattern_bind_v1"] = {
                "schema_version": 1,
                "field_name": field_name,
                "field_type": field_type,
            }
            if field_type != "unknown":
                spd["resolved_type"] = field_type
                _set_type_expr_summary(spd, _type_expr_summary_from_payload(None, field_type))
    return match_stmt
