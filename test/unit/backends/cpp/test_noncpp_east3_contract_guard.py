"""Guard tests for non-cpp EAST3 default/compatibility contract."""

from __future__ import annotations

import copy
import re
import sys
import subprocess
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from backends.cs.emitter import transpile_to_csharp
from backends.go.emitter import transpile_to_go
from backends.java.emitter import transpile_to_java
from backends.js.emitter.js_emitter import transpile_to_js
from backends.kotlin.emitter import transpile_to_kotlin
from backends.nim.emitter import transpile_to_nim
from backends.php.emitter import transpile_to_php
from backends.ruby.emitter import transpile_to_ruby
from backends.rs.emitter.rs_emitter import transpile_to_rust
from backends.scala.emitter import transpile_to_scala
from backends.swift.emitter import transpile_to_swift
from backends.ts.emitter.ts_emitter import transpile_to_typescript
from backends.lua.emitter import transpile_to_lua
from toolchain.frontends.type_expr import parse_type_expr_text


def _general_union_module() -> dict[str, object]:
    return {
        "kind": "Module",
        "east_stage": 3,
        "body": [
            {
                "kind": "FunctionDef",
                "name": "pick",
                "arg_order": ["x"],
                "args": [{"arg": "x"}],
                "arg_types": {"x": "int64|bool"},
                "arg_type_exprs": {"x": parse_type_expr_text("int | bool")},
                "return_type": "int64|bool",
                "return_type_expr": parse_type_expr_text("int | bool"),
                "body": [{"kind": "Return", "value": {"kind": "Name", "id": "x", "resolved_type": "int64|bool"}}],
            }
        ],
        "main_guard_body": [],
        "meta": {},
    }


def _typed_varargs_signature_module() -> dict[str, object]:
    return {
        "kind": "Module",
        "east_stage": 3,
        "body": [
            {
                "kind": "FunctionDef",
                "name": "merge_values",
                "arg_order": ["target"],
                "args": [{"arg": "target"}],
                "arg_types": {"target": "int64"},
                "arg_type_exprs": {"target": parse_type_expr_text("int")},
                "vararg_name": "values",
                "vararg_type": "int64",
                "vararg_type_expr": parse_type_expr_text("int"),
                "return_type": "int64",
                "return_type_expr": parse_type_expr_text("int"),
                "body": [{"kind": "Return", "value": _const_i(0)}],
            }
        ],
        "main_guard_body": [],
        "meta": {},
    }


def _homogeneous_tuple_ellipsis_module() -> dict[str, object]:
    return {
        "kind": "Module",
        "east_stage": 3,
        "body": [
            {
                "kind": "AnnAssign",
                "target": {"kind": "Name", "id": "LENGTH_TABLE"},
                "decl_type": "tuple[int64, ...]",
                "decl_type_expr": parse_type_expr_text("tuple[int, ...]"),
                "value": {
                    "kind": "Tuple",
                    "elts": [_const_i(10), _const_i(20), _const_i(30)],
                    "resolved_type": "tuple[int64, ...]",
                    "type_expr": parse_type_expr_text("tuple[int, ...]"),
                },
            },
            {
                "kind": "FunctionDef",
                "name": "head",
                "arg_order": ["xs"],
                "args": [{"arg": "xs"}],
                "arg_types": {"xs": "tuple[int64, ...]"},
                "arg_type_exprs": {"xs": parse_type_expr_text("tuple[int, ...]")},
                "return_type": "int64",
                "return_type_expr": parse_type_expr_text("int"),
                "body": [
                    {
                        "kind": "Return",
                        "value": {
                            "kind": "Subscript",
                            "value": {
                                "kind": "Name",
                                "id": "xs",
                                "resolved_type": "tuple[int64, ...]",
                                "type_expr": parse_type_expr_text("tuple[int, ...]"),
                            },
                            "slice": _const_i(0),
                            "resolved_type": "int64",
                        },
                    }
                ],
            },
        ],
        "main_guard_body": [],
        "meta": {},
    }


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
    out["class_storage_hint"] = "ref" if role == "variant" else "value"
    if role == "variant":
        out["base"] = family_name
    if payload_style == "dataclass":
        out["dataclass"] = True
    if field_types is not None:
        out["field_types"] = dict(field_types)
    return out


def _const_i(v: int) -> dict[str, object]:
    return {
        "kind": "Constant",
        "resolved_type": "int64",
        "borrow_kind": "value",
        "casts": [],
        "repr": str(v),
        "value": v,
    }


def _representative_nominal_adt_match_module() -> dict[str, object]:
    return {
        "kind": "Module",
        "east_stage": 3,
        "main_guard_body": [],
        "meta": {},
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
                "arg_order": ["x"],
                "args": [{"arg": "x"}],
                "arg_types": {"x": "Maybe"},
                "arg_type_exprs": {"x": parse_type_expr_text("Maybe")},
                "return_type": "int64",
                "return_type_expr": parse_type_expr_text("int"),
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
                                    "subpatterns": [{"kind": "PatternBind", "name": "value"}],
                                },
                                "guard": None,
                                "body": [
                                    {
                                        "kind": "Return",
                                        "value": {
                                            "kind": "Name",
                                            "id": "value",
                                            "resolved_type": "int64",
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
                                "body": [{"kind": "Return", "value": _const_i(0)}],
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


class NonCppEast3ContractGuardTest(unittest.TestCase):
    def test_noncpp_east3_contract_static_check_passes(self) -> None:
        cp = subprocess.run(
            ["python3", "tools/check_noncpp_east3_contract.py", "--skip-transpile"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(cp.returncode, 0, msg=f"{cp.stdout}\n{cp.stderr}")
        self.assertIn("static contract checks passed", cp.stdout)

    def test_static_noncpp_backends_fail_closed_on_general_union_type_expr(self) -> None:
        east = _general_union_module()
        backends = [
            ("Rust backend", transpile_to_rust),
            ("C# backend", transpile_to_csharp),
            ("Go backend", transpile_to_go),
            ("Java backend", transpile_to_java),
            ("Kotlin backend", transpile_to_kotlin),
            ("Scala backend", transpile_to_scala),
            ("Swift backend", transpile_to_swift),
            ("Nim backend", transpile_to_nim),
        ]
        for backend_name, transpile in backends:
            with self.subTest(backend=backend_name):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "unsupported_syntax\\|" + re.escape(backend_name) + " does not support general union TypeExpr yet",
                ) as cm:
                    transpile(copy.deepcopy(east))
                self.assertIn("unsupported general-union lane: int64|bool", str(cm.exception))

    def test_all_noncpp_backends_fail_closed_on_typed_varargs_signature(self) -> None:
        east = _typed_varargs_signature_module()
        backends = [
            ("Rust backend", transpile_to_rust),
            ("C# backend", transpile_to_csharp),
            ("Go backend", transpile_to_go),
            ("Java backend", transpile_to_java),
            ("Kotlin backend", transpile_to_kotlin),
            ("Scala backend", transpile_to_scala),
            ("Swift backend", transpile_to_swift),
            ("Nim backend", transpile_to_nim),
            ("PHP backend", transpile_to_php),
            ("Ruby backend", transpile_to_ruby),
            ("Lua backend", transpile_to_lua),
            ("JS backend", transpile_to_js),
            ("TS backend", transpile_to_typescript),
        ]
        for backend_name, transpile in backends:
            with self.subTest(backend=backend_name):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "unsupported_syntax\\|" + re.escape(backend_name) + " does not support typed \\*args signatures yet",
                ) as cm:
                    transpile(copy.deepcopy(east))
                self.assertIn(
                    "unsupported typed varargs lane: FunctionDef merge_values(*values: int64)",
                    str(cm.exception),
                )

    def test_all_noncpp_backends_fail_closed_on_homogeneous_tuple_ellipsis_type_expr(self) -> None:
        east = _homogeneous_tuple_ellipsis_module()
        backends = [
            ("Rust backend", transpile_to_rust),
            ("C# backend", transpile_to_csharp),
            ("Go backend", transpile_to_go),
            ("Java backend", transpile_to_java),
            ("Kotlin backend", transpile_to_kotlin),
            ("Scala backend", transpile_to_scala),
            ("Swift backend", transpile_to_swift),
            ("Nim backend", transpile_to_nim),
            ("PHP backend", transpile_to_php),
            ("Ruby backend", transpile_to_ruby),
            ("Lua backend", transpile_to_lua),
            ("JS backend", transpile_to_js),
            ("TS backend", transpile_to_typescript),
        ]
        for backend_name, transpile in backends:
            with self.subTest(backend=backend_name):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "unsupported_syntax\\|" + re.escape(backend_name) + " does not support homogeneous tuple ellipsis TypeExpr yet",
                ) as cm:
                    transpile(copy.deepcopy(east))
                self.assertIn(
                    "unsupported homogeneous tuple lane: tuple[int64, ...]",
                    str(cm.exception),
                )

    def test_native_noncpp_backends_fail_closed_on_nominal_adt_match_stmt(self) -> None:
        east = _representative_nominal_adt_match_module()
        strict_lane_backends = [
            (
                "Rust backend",
                transpile_to_rust,
                r"unsupported_syntax\|Rust backend does not support nominal ADT v1 lanes yet",
            ),
            (
                "C# backend",
                transpile_to_csharp,
                r"unsupported_syntax\|C# backend does not support nominal ADT v1 lanes yet",
            ),
        ]
        for backend_name, transpile, pattern in strict_lane_backends:
            with self.subTest(backend=backend_name):
                with self.assertRaisesRegex(RuntimeError, pattern) as cm:
                    transpile(copy.deepcopy(east))
                self.assertIn("unsupported nominal ADT lane: declaration", str(cm.exception))

        backends = [
            ("Go backend", transpile_to_go, r"go native emitter: unsupported stmt kind: Match"),
            ("Java backend", transpile_to_java, r"java native emitter: unsupported stmt kind: Match"),
            ("Kotlin backend", transpile_to_kotlin, r"kotlin native emitter: unsupported stmt kind: Match"),
            ("Scala backend", transpile_to_scala, r"scala native emitter: unsupported stmt kind Match"),
            ("Swift backend", transpile_to_swift, r"swift native emitter: unsupported stmt kind: Match"),
            ("Nim backend", transpile_to_nim, r"nim native emitter: unsupported stmt kind: Match"),
            ("PHP backend", transpile_to_php, r"php native emitter: unsupported stmt kind: Match"),
            ("Ruby backend", transpile_to_ruby, r"ruby native emitter: unsupported stmt kind: Match"),
            ("Lua backend", transpile_to_lua, r"lang=lua unsupported stmt kind: Match"),
        ]
        for backend_name, transpile, pattern in backends:
            with self.subTest(backend=backend_name):
                with self.assertRaisesRegex(RuntimeError, pattern):
                    transpile(copy.deepcopy(east))

    def test_js_family_noncpp_backends_fail_closed_on_nominal_adt_match_stmt(self) -> None:
        east = _representative_nominal_adt_match_module()
        backends = [
            ("JS backend", transpile_to_js, r"js emitter: unsupported stmt kind: Match"),
            ("TS backend", transpile_to_typescript, r"js emitter: unsupported stmt kind: Match"),
        ]
        for backend_name, transpile, pattern in backends:
            with self.subTest(backend=backend_name):
                with self.assertRaisesRegex(RuntimeError, pattern):
                    transpile(copy.deepcopy(east))


if __name__ == "__main__":
    unittest.main()
