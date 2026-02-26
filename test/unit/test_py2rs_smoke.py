"""py2rs (EAST based) smoke tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.py2rs import load_east, load_rs_profile, transpile_to_rust
from src.pytra.compiler.east_parts.core import convert_path
from hooks.rs.emitter.rs_emitter import RustEmitter


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


class Py2RsSmokeTest(unittest.TestCase):
    def test_load_rs_profile_contains_core_sections(self) -> None:
        profile = load_rs_profile()
        self.assertIn("types", profile)
        self.assertIn("operators", profile)
        self.assertIn("syntax", profile)
        self.assertIn("runtime_calls", profile)

    def test_transpile_add_fixture_contains_function_signature(self) -> None:
        fixture = find_fixture_case("add")
        east = load_east(fixture, parser_backend="self_hosted")
        rust = transpile_to_rust(east)
        self.assertIn("fn add(a: i64, b: i64) -> i64 {", rust)
        self.assertIn("fn _case_main()", rust)
        self.assertIn("fn main()", rust)

    def test_transpile_for_range_fixture_lowers_to_while(self) -> None:
        fixture = find_fixture_case("for_range")
        east = load_east(fixture, parser_backend="self_hosted")
        rust = transpile_to_rust(east)
        self.assertIn("while i < n {", rust)
        self.assertIn("i += 1;", rust)

    def test_load_east_from_json(self) -> None:
        fixture = find_fixture_case("add")
        east = convert_path(fixture)
        with tempfile.TemporaryDirectory() as td:
            east_json = Path(td) / "case.east.json"
            east_json.write_text(json.dumps(east), encoding="utf-8")
            loaded = load_east(east_json)
            rust = transpile_to_rust(loaded)
        self.assertIn("fn add(a: i64, b: i64)", rust)

    def test_load_east_from_json_wrapper_payload(self) -> None:
        fixture = find_fixture_case("add")
        east = convert_path(fixture)
        with tempfile.TemporaryDirectory() as td:
            east_json = Path(td) / "case.wrapped.east.json"
            wrapped = {"ok": True, "east": east}
            east_json.write_text(json.dumps(wrapped), encoding="utf-8")
            loaded = load_east(east_json)
            rust = transpile_to_rust(loaded)
        self.assertIn("fn add(a: i64, b: i64)", rust)

    def test_load_east_defaults_to_stage3_entry_and_returns_legacy_shape(self) -> None:
        fixture = find_fixture_case("for_range")
        loaded = load_east(fixture, parser_backend="self_hosted")
        self.assertIsInstance(loaded, dict)
        self.assertEqual(loaded.get("kind"), "Module")
        self.assertEqual(loaded.get("east_stage"), 2)

    def test_for_core_static_range_plan_is_emitted(self) -> None:
        east = {
            "kind": "Module",
            "east_stage": 3,
            "body": [
                {
                    "kind": "ForCore",
                    "target_plan": {"kind": "NameTarget", "id": "i", "target_type": "int64"},
                    "iter_plan": {
                        "kind": "StaticRangeForPlan",
                        "start": {"kind": "Constant", "value": 0},
                        "stop": {"kind": "Constant", "value": 3},
                        "step": {"kind": "Constant", "value": 1},
                        "range_mode": "ascending",
                    },
                    "body": [
                        {
                            "kind": "Expr",
                            "value": {
                                "kind": "Call",
                                "func": {"kind": "Name", "id": "print"},
                                "args": [{"kind": "Name", "id": "i"}],
                                "keywords": [],
                            },
                        }
                    ],
                    "orelse": [],
                }
            ],
            "main_guard_body": [],
            "meta": {},
        }
        rust = transpile_to_rust(east)
        self.assertIn("let mut i: i64 = 0;", rust)
        self.assertIn("while i < 3 {", rust)
        self.assertIn("i += 1;", rust)

    def test_for_core_runtime_iter_tuple_target_is_emitted(self) -> None:
        east = {
            "kind": "Module",
            "east_stage": 3,
            "body": [
                {
                    "kind": "ForCore",
                    "target_plan": {
                        "kind": "TupleTarget",
                        "elements": [
                            {"kind": "NameTarget", "id": "k"},
                            {"kind": "NameTarget", "id": "v"},
                        ],
                        "target_type": "tuple[int64,int64]",
                    },
                    "iter_plan": {
                        "kind": "RuntimeIterForPlan",
                        "iter_expr": {"kind": "Name", "id": "pairs"},
                        "init_op": "ObjIterInit",
                        "next_op": "ObjIterNext",
                    },
                    "body": [
                        {
                            "kind": "Expr",
                            "value": {
                                "kind": "Call",
                                "func": {"kind": "Name", "id": "print"},
                                "args": [
                                    {"kind": "Name", "id": "k"},
                                    {"kind": "Name", "id": "v"},
                                ],
                                "keywords": [],
                            },
                        }
                    ],
                    "orelse": [],
                }
            ],
            "main_guard_body": [],
            "meta": {},
        }
        rust = transpile_to_rust(east)
        self.assertIn("for (k, v) in pairs {", rust)
        self.assertIn("println!(", rust)

    def test_cli_smoke_generates_rs_file(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_rs = Path(td) / "if_else.rs"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2rs.py", str(fixture), "-o", str(out_rs)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertTrue(out_rs.exists())
            txt = out_rs.read_text(encoding="utf-8")
            self.assertIn("fn abs_like", txt)

    def test_cli_rejects_stage2_compat_mode(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_rs = Path(td) / "if_else.rs"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2rs.py", str(fixture), "-o", str(out_rs), "--east-stage", "2"],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertIn("--east-stage 2 is no longer supported; use EAST3 (default).", proc.stderr)

    def test_imports_emit_use_lines(self) -> None:
        fixture = find_fixture_case("from_pytra_std_import_math")
        east = load_east(fixture, parser_backend="self_hosted")
        rust = transpile_to_rust(east)
        self.assertIn("use crate::pytra::std::math::floor;", rust)
        self.assertIn("use crate::pytra::std::math::sqrt as msqrt;", rust)

    def test_for_tuple_target_and_dict_items_quality(self) -> None:
        fixture = find_fixture_case("dict_get_items")
        east = load_east(fixture, parser_backend="self_hosted")
        rust = transpile_to_rust(east)
        self.assertIn("for (_k, v) in", rust)
        self.assertIn(".clone().into_iter()", rust)
        self.assertNotIn(".items()", rust)

    def test_class_struct_has_clone_debug_derive(self) -> None:
        fixture = find_fixture_case("class_instance")
        east = load_east(fixture, parser_backend="self_hosted")
        rust = transpile_to_rust(east)
        self.assertIn("#[derive(Clone, Debug)]", rust)
        self.assertIn("struct Box100 {", rust)

    def test_dict_entries_literal_is_not_dropped(self) -> None:
        fixture = find_fixture_case("any_dict_items")
        east = load_east(fixture, parser_backend="self_hosted")
        rust = transpile_to_rust(east)
        self.assertIn("BTreeMap::from([(", rust)
        self.assertIn("\"meta\"", rust)
        self.assertIn("enum PyAny", rust)
        self.assertIn("py_any_as_dict(", rust)
        self.assertIn("py_any_to_i64(&v)", rust)
        self.assertIn("py_any_to_string(&", rust)

    def test_reassigned_args_emit_mut_only_when_needed(self) -> None:
        src = """
def f(x: int, y: int) -> int:
    x = x + 1
    return x + y

def g(a: int, b: int) -> int:
    return a + b
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "arg_usage_case.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            rust = transpile_to_rust(east)

        self.assertIn("fn f(mut x: i64, y: i64) -> i64 {", rust)
        self.assertIn("fn g(a: i64, b: i64) -> i64 {", rust)
        self.assertNotIn("fn f(mut x: i64, mut y: i64) -> i64 {", rust)

    def test_py2rs_does_not_import_src_common(self) -> None:
        src = (ROOT / "src" / "py2rs.py").read_text(encoding="utf-8")
        self.assertNotIn("src.common", src)
        self.assertNotIn("from common.", src)

    def test_render_expr_kind_specific_hook_precedes_leaf_hook(self) -> None:
        emitter = RustEmitter({"kind": "Module", "body": [], "meta": {}})
        emitter.hooks["on_render_expr_name"] = (
            lambda _em, _kind, _expr_node: "specific_name_hook()"
        )
        emitter.hooks["on_render_expr_leaf"] = (
            lambda _em, _kind, _expr_node: "leaf_hook()"
        )
        rendered = emitter.render_expr({"kind": "Name", "id": "x"})
        self.assertEqual(rendered, "specific_name_hook()")

    def test_isinstance_lowering_for_any_uses_type_id_runtime_api(self) -> None:
        src = """
from pytra.std.typing import Any

def is_int(x: Any) -> bool:
    return isinstance(x, int)

def is_dict(x: Any) -> bool:
    return isinstance(x, dict)
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "isinstance_any.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            rust = transpile_to_rust(east)

        self.assertNotIn("return isinstance(", rust)
        self.assertIn("py_isinstance(&x, PYTRA_TID_INT)", rust)
        self.assertIn("py_isinstance(&x, PYTRA_TID_DICT)", rust)
        self.assertIn("fn py_is_subtype(actual_type_id: i64, expected_type_id: i64) -> bool {", rust)

    def test_isinstance_lowering_for_static_builtin_type(self) -> None:
        src = """
def is_int(x: int) -> bool:
    return isinstance(x, int)

def is_float(x: int) -> bool:
    return isinstance(x, float)
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "isinstance_builtin.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            rust = transpile_to_rust(east)

        self.assertNotIn("return isinstance(", rust)
        self.assertIn("return py_isinstance(&x, PYTRA_TID_INT);", rust)
        self.assertIn("return py_isinstance(&x, PYTRA_TID_FLOAT);", rust)

    def test_isinstance_lowering_for_class_inheritance(self) -> None:
        src = """
class A:
    def __init__(self) -> None:
        pass

class B(A):
    def __init__(self) -> None:
        pass

def is_base(x: B) -> bool:
    return isinstance(x, A)

def is_child(x: A) -> bool:
    return isinstance(x, B)
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "isinstance_class.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            rust = transpile_to_rust(east)

        self.assertNotIn("return isinstance(", rust)
        self.assertIn("const PYTRA_TYPE_ID: i64 = 1000;", rust)
        self.assertIn("const PYTRA_TYPE_ID: i64 = 1001;", rust)
        self.assertIn("impl PyRuntimeTypeId for A {", rust)
        self.assertIn("impl PyRuntimeTypeId for B {", rust)
        self.assertIn("return py_isinstance(&x, A::PYTRA_TYPE_ID);", rust)
        self.assertIn("return py_isinstance(&x, B::PYTRA_TYPE_ID);", rust)
        self.assertIn("1000 => Some(PyTypeInfo { order: 9, min: 9, max: 10 }),", rust)
        self.assertIn("1001 => Some(PyTypeInfo { order: 10, min: 10, max: 10 }),", rust)

    def test_isinstance_sibling_classes_emit_non_overlapping_type_ranges(self) -> None:
        src = """
class A:
    def __init__(self) -> None:
        pass

class B:
    def __init__(self) -> None:
        pass

def is_a(x: B) -> bool:
    return isinstance(x, A)
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "isinstance_sibling_class.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            rust = transpile_to_rust(east)

        self.assertIn("return py_isinstance(&x, A::PYTRA_TYPE_ID);", rust)
        self.assertIn("1000 => Some(PyTypeInfo { order: 9, min: 9, max: 9 }),", rust)
        self.assertIn("1001 => Some(PyTypeInfo { order: 10, min: 10, max: 10 }),", rust)

    def test_isinstance_lowering_for_object_type(self) -> None:
        src = """
from pytra.std.typing import Any

def from_static(x: int) -> bool:
    return isinstance(x, object)

def from_any(x: Any) -> bool:
    return isinstance(x, object)
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "isinstance_object.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            rust = transpile_to_rust(east)

        self.assertNotIn("return isinstance(", rust)
        self.assertIn("return py_isinstance(&x, PYTRA_TID_OBJECT);", rust)

    def test_isinstance_tuple_lowering_for_any_uses_or_of_type_id_checks(self) -> None:
        src = """
from pytra.std.typing import Any

def f(x: Any) -> bool:
    return isinstance(x, (int, dict))
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "isinstance_tuple_any.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            rust = transpile_to_rust(east)

        self.assertNotIn("return isinstance(", rust)
        self.assertIn("py_isinstance(&x, PYTRA_TID_INT)", rust)
        self.assertIn("py_isinstance(&x, PYTRA_TID_DICT)", rust)
        self.assertIn("||", rust)

    def test_isinstance_set_lowering_for_any_uses_type_id_runtime_api(self) -> None:
        src = """
from pytra.std.typing import Any

def f(x: Any) -> bool:
    return isinstance(x, set)
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "isinstance_set_any.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            rust = transpile_to_rust(east)

        self.assertNotIn("return isinstance(", rust)
        self.assertIn("py_isinstance(&x, PYTRA_TID_SET)", rust)


if __name__ == "__main__":
    unittest.main()
