from __future__ import annotations

import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.toolchain.frontends.type_expr import parse_type_expr_text
from src.toolchain.compile.core_entrypoints import convert_source_to_east_with_backend


def _const_i(v: int) -> dict[str, object]:
    return {"kind": "Constant", "value": v, "resolved_type": "int64"}


def _nominal_adt_class(
    name: str,
    *,
    role: str,
    family_name: str,
    variant_name: str = "",
    payload_style: str = "",
    field_types: dict[str, object] | None = None,
) -> dict[str, object]:
    nominal_meta: dict[str, object] = {
        "schema_version": 1,
        "role": role,
        "family_name": family_name,
    }
    if variant_name != "":
        nominal_meta["variant_name"] = variant_name
    if payload_style != "":
        nominal_meta["payload_style"] = payload_style
    out: dict[str, object] = {
        "kind": "ClassDef",
        "name": name,
        "body": [],
        "meta": {"nominal_adt_v1": nominal_meta},
    }
    if field_types is not None:
        out["field_types"] = dict(field_types)
    return out


class East23LoweringNominalAdtFixtureMixin:
    def representative_nominal_adt_east2(self) -> dict[str, object]:
        source = """
from dataclasses import dataclass

@sealed
class Maybe:
    pass

@dataclass
class Just(Maybe):
    value: int

class Nothing(Maybe):
    pass

def f(x: Maybe) -> int:
    if isinstance(x, Just):
        return x.value
    y = Just(1)
    return y.value
"""
        return convert_source_to_east_with_backend(
            source,
            filename="sample.py",
            parser_backend="self_hosted",
        )

    def representative_nominal_adt_match_east2(self) -> dict[str, object]:
        return {
            "kind": "Module",
            "meta": {"dispatch_mode": "native"},
            "body": [
                _nominal_adt_class("Maybe", role="family", family_name="Maybe"),
                _nominal_adt_class(
                    "Just",
                    role="variant",
                    family_name="Maybe",
                    variant_name="Just",
                    payload_style="dataclass",
                    field_types={"value": "int64"},
                ),
                _nominal_adt_class(
                    "Nothing",
                    role="variant",
                    family_name="Maybe",
                    variant_name="Nothing",
                ),
                {
                    "kind": "FunctionDef",
                    "name": "f",
                    "args": [{"arg": "x", "ann": "Maybe"}],
                    "returns": "int64",
                    "body": [
                        {
                            "kind": "Match",
                            "subject": {
                                "kind": "Name",
                                "id": "x",
                                "resolved_type": "Maybe",
                                "type_expr": parse_type_expr_text("Maybe"),
                            },
                            "cases": [
                                {
                                    "kind": "MatchCase",
                                    "pattern": {
                                        "kind": "VariantPattern",
                                        "family_name": "Maybe",
                                        "variant_name": "Just",
                                        "subpatterns": [
                                            {
                                                "kind": "PatternBind",
                                                "name": "value",
                                            }
                                        ],
                                    },
                                    "guard": None,
                                    "body": [
                                        {
                                            "kind": "Return",
                                            "value": {
                                                "kind": "Name",
                                                "id": "value",
                                                "resolved_type": "int64",
                                                "type_expr": parse_type_expr_text("int"),
                                            },
                                        }
                                    ],
                                },
                                {
                                    "kind": "MatchCase",
                                    "pattern": {
                                        "kind": "VariantPattern",
                                        "family_name": "Maybe",
                                        "variant_name": "Nothing",
                                        "subpatterns": [],
                                    },
                                    "guard": None,
                                    "body": [
                                        {
                                            "kind": "Return",
                                            "value": _const_i(0),
                                        }
                                    ],
                                },
                            ],
                            "meta": {
                                "match_analysis_v1": {
                                    "schema_version": 1,
                                    "family_name": "Maybe",
                                    "coverage_kind": "exhaustive",
                                    "covered_variants": ["Just", "Nothing"],
                                    "uncovered_variants": [],
                                    "duplicate_case_indexes": [],
                                    "unreachable_case_indexes": [],
                                }
                            },
                        }
                    ],
                },
            ],
        }
