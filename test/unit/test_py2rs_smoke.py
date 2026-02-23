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

    def test_isinstance_lowering_for_any_uses_pyany_matches(self) -> None:
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

        self.assertNotIn("isinstance(", rust)
        self.assertIn("matches!(x, PyAny::Int(_))", rust)
        self.assertIn("matches!(x, PyAny::Dict(_))", rust)

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

        self.assertNotIn("isinstance(", rust)
        int_fn = rust[rust.index("fn is_int(") : rust.index("fn is_float(")]
        float_fn = rust[rust.index("fn is_float(") :]
        self.assertIn("return true;", int_fn)
        self.assertIn("return false;", float_fn)

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

        self.assertNotIn("isinstance(", rust)
        base_fn = rust[rust.index("fn is_base(") : rust.index("fn is_child(")]
        child_fn = rust[rust.index("fn is_child(") :]
        self.assertIn("return true;", base_fn)
        self.assertIn("return false;", child_fn)

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

        self.assertNotIn("isinstance(", rust)
        static_fn = rust[rust.index("fn from_static(") : rust.index("fn from_any(")]
        any_fn = rust[rust.index("fn from_any(") :]
        self.assertIn("return true;", static_fn)
        self.assertIn("return true;", any_fn)

    def test_isinstance_tuple_lowering_for_any_uses_or_of_matches(self) -> None:
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

        self.assertNotIn("isinstance(", rust)
        self.assertIn("matches!(x, PyAny::Int(_))", rust)
        self.assertIn("matches!(x, PyAny::Dict(_))", rust)
        self.assertIn("||", rust)


if __name__ == "__main__":
    unittest.main()
