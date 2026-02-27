"""py2cs (EAST based) smoke tests."""

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

from src.py2cs import load_east, load_cs_profile, transpile_to_csharp
from src.pytra.compiler.east_parts.core import convert_path
from hooks.cs.emitter.cs_emitter import CSharpEmitter


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


class Py2CsSmokeTest(unittest.TestCase):
    def test_load_cs_profile_contains_core_sections(self) -> None:
        profile = load_cs_profile()
        self.assertIn("types", profile)
        self.assertIn("operators", profile)
        self.assertIn("syntax", profile)
        self.assertIn("runtime_calls", profile)

    def test_transpile_add_fixture_contains_function_signature(self) -> None:
        fixture = find_fixture_case("add")
        east = load_east(fixture, parser_backend="self_hosted")
        cs = transpile_to_csharp(east)
        self.assertIn("public static long add(long a, long b)", cs)
        self.assertIn("public static class Program", cs)
        self.assertIn("public static void Main(string[] args)", cs)

    def test_load_east_from_json(self) -> None:
        fixture = find_fixture_case("add")
        east = convert_path(fixture)
        with tempfile.TemporaryDirectory() as td:
            east_json = Path(td) / "case.east.json"
            east_json.write_text(json.dumps(east), encoding="utf-8")
            loaded = load_east(east_json)
            cs = transpile_to_csharp(loaded)
        self.assertIn("public static long add(long a, long b)", cs)

    def test_load_east_defaults_to_stage3_entry_and_returns_east3_shape(self) -> None:
        fixture = find_fixture_case("for_range")
        loaded = load_east(fixture, parser_backend="self_hosted")
        self.assertIsInstance(loaded, dict)
        self.assertEqual(loaded.get("kind"), "Module")
        self.assertEqual(loaded.get("east_stage"), 3)

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
        cs = transpile_to_csharp(east)
        self.assertIn("long i = 0;", cs)
        self.assertIn("for (i = 0; i < 3; i += 1)", cs)

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
        cs = transpile_to_csharp(east)
        self.assertIn("foreach (var __it", cs)
        self.assertIn("var k = __it_", cs)
        self.assertIn(".Item1;", cs)
        self.assertIn("var v = __it_", cs)
        self.assertIn(".Item2;", cs)

    def test_object_boundary_nodes_are_lowered_without_legacy_bridge(self) -> None:
        east = {
            "kind": "Module",
            "east_stage": 3,
            "body": [
                {"kind": "Expr", "value": {"kind": "ObjBool", "value": {"kind": "Name", "id": "x"}, "resolved_type": "bool"}},
                {"kind": "Expr", "value": {"kind": "ObjLen", "value": {"kind": "Name", "id": "x"}, "resolved_type": "int64"}},
                {"kind": "Expr", "value": {"kind": "ObjStr", "value": {"kind": "Name", "id": "x"}, "resolved_type": "str"}},
                {"kind": "Expr", "value": {"kind": "ObjTypeId", "value": {"kind": "Name", "id": "x"}, "resolved_type": "int64"}},
                {"kind": "Expr", "value": {"kind": "ObjIterInit", "value": {"kind": "Name", "id": "x"}, "resolved_type": "object"}},
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "ObjIterNext",
                        "iter": {"kind": "ObjIterInit", "value": {"kind": "Name", "id": "x"}, "resolved_type": "object"},
                        "resolved_type": "object",
                    },
                },
            ],
            "main_guard_body": [],
            "meta": {},
        }
        cs = transpile_to_csharp(east)
        self.assertIn("Pytra.CsModule.py_runtime.py_bool(x);", cs)
        self.assertIn(".Count();", cs)
        self.assertIn("System.Convert.ToString(x);", cs)
        self.assertIn("Pytra.CsModule.py_runtime.py_runtime_type_id(x);", cs)
        self.assertIn("iter(x);", cs)
        self.assertIn("next(iter(x));", cs)

    def test_type_predicate_nodes_are_lowered_without_legacy_bridge(self) -> None:
        east = {
            "kind": "Module",
            "east_stage": 3,
            "body": [
                {"kind": "ClassDef", "name": "Base", "base": "", "body": []},
                {"kind": "ClassDef", "name": "Child", "base": "Base", "body": []},
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "IsInstance",
                        "value": {"kind": "Name", "id": "x"},
                        "expected_type_id": {"kind": "Name", "id": "PYTRA_TID_INT"},
                        "resolved_type": "bool",
                    },
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "IsInstance",
                        "value": {"kind": "Name", "id": "x"},
                        "expected_type_id": {"kind": "Name", "id": "Base"},
                        "resolved_type": "bool",
                    },
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "IsSubtype",
                        "actual_type_id": {"kind": "Name", "id": "PYTRA_TID_BOOL"},
                        "expected_type_id": {"kind": "Name", "id": "PYTRA_TID_INT"},
                        "resolved_type": "bool",
                    },
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "IsSubclass",
                        "actual_type_id": {"kind": "Name", "id": "Child"},
                        "expected_type_id": {"kind": "Name", "id": "Base"},
                        "resolved_type": "bool",
                    },
                },
            ],
            "main_guard_body": [],
            "meta": {},
        }
        cs = transpile_to_csharp(east)
        self.assertIn("Pytra.CsModule.py_runtime.py_isinstance(x, Pytra.CsModule.py_runtime.PYTRA_TID_INT);", cs)
        self.assertIn("Pytra.CsModule.py_runtime.py_isinstance(x, Base.PYTRA_TYPE_ID);", cs)
        self.assertIn("Pytra.CsModule.py_runtime.py_is_subtype(Pytra.CsModule.py_runtime.PYTRA_TID_BOOL, Pytra.CsModule.py_runtime.PYTRA_TID_INT);", cs)
        self.assertIn("Pytra.CsModule.py_runtime.py_is_subtype(Child.PYTRA_TYPE_ID, Base.PYTRA_TYPE_ID);", cs)

    def test_box_unbox_nodes_are_lowered_without_legacy_bridge(self) -> None:
        east = {
            "kind": "Module",
            "east_stage": 3,
            "body": [
                {
                    "kind": "Assign",
                    "targets": [{"kind": "Name", "id": "y"}],
                    "value": {
                        "kind": "Box",
                        "value": {"kind": "Constant", "value": 1},
                        "resolved_type": "object",
                    },
                },
                {
                    "kind": "Assign",
                    "targets": [{"kind": "Name", "id": "z"}],
                    "value": {
                        "kind": "Unbox",
                        "value": {"kind": "Name", "id": "y"},
                        "target": "int64",
                        "resolved_type": "int64",
                    },
                },
            ],
            "main_guard_body": [],
            "meta": {},
        }
        cs = transpile_to_csharp(east)
        self.assertIn("y = 1;", cs)
        self.assertIn("System.Convert.ToInt64(y)", cs)

    def test_cli_smoke_generates_cs_file(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_cs = Path(td) / "if_else.cs"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2cs.py", str(fixture), "-o", str(out_cs)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertTrue(out_cs.exists())
            txt = out_cs.read_text(encoding="utf-8")
            self.assertIn("public static long abs_like", txt)

    def test_cli_rejects_stage2_compat_mode(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_cs = Path(td) / "if_else.cs"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2cs.py", str(fixture), "-o", str(out_cs), "--east-stage", "2"],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertIn("--east-stage 2 is no longer supported; use EAST3 (default).", proc.stderr)

    def test_isinstance_builtin_lowers_to_csharp_is_checks(self) -> None:
        src = """def f(x: object) -> bool:
    return isinstance(x, int) or isinstance(x, str)
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "isinstance_builtin.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            cs = transpile_to_csharp(east)

        self.assertIn("Pytra.CsModule.py_runtime.py_isinstance(x, Pytra.CsModule.py_runtime.PYTRA_TID_INT)", cs)
        self.assertIn("Pytra.CsModule.py_runtime.py_isinstance(x, Pytra.CsModule.py_runtime.PYTRA_TID_STR)", cs)
        self.assertNotIn("return isinstance(", cs)

    def test_isinstance_user_class_lowers_to_is_operator(self) -> None:
        src = """class Base:
    pass

class Child(Base):
    pass

def f(x: object) -> bool:
    return isinstance(x, Base)
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "isinstance_class.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            cs = transpile_to_csharp(east)

        self.assertIn("Pytra.CsModule.py_runtime.py_isinstance(x, Base.PYTRA_TYPE_ID)", cs)
        self.assertNotIn("return isinstance(", cs)

    def test_isinstance_object_lowers_to_object_is_check(self) -> None:
        src = """def f(x: int) -> bool:
    return isinstance(x, object)
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "isinstance_object.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            cs = transpile_to_csharp(east)

        self.assertIn("Pytra.CsModule.py_runtime.py_isinstance(x, Pytra.CsModule.py_runtime.PYTRA_TID_OBJECT)", cs)
        self.assertNotIn("return isinstance(", cs)

    def test_isinstance_tuple_lowers_to_or_of_is_checks(self) -> None:
        src = """class Base:
    pass

def f(x: object) -> bool:
    return isinstance(x, (int, Base, dict, object))
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "isinstance_tuple.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            cs = transpile_to_csharp(east)

        self.assertIn("Pytra.CsModule.py_runtime.py_isinstance(x, Pytra.CsModule.py_runtime.PYTRA_TID_INT)", cs)
        self.assertIn("Pytra.CsModule.py_runtime.py_isinstance(x, Base.PYTRA_TYPE_ID)", cs)
        self.assertIn("Pytra.CsModule.py_runtime.py_isinstance(x, Pytra.CsModule.py_runtime.PYTRA_TID_DICT)", cs)
        self.assertIn("Pytra.CsModule.py_runtime.py_isinstance(x, Pytra.CsModule.py_runtime.PYTRA_TID_OBJECT)", cs)
        self.assertNotIn("return isinstance(", cs)

    def test_isinstance_set_lowers_to_iset_check(self) -> None:
        src = """def f(x: object) -> bool:
    return isinstance(x, set)
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "isinstance_set.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            cs = transpile_to_csharp(east)

        self.assertIn("Pytra.CsModule.py_runtime.py_isinstance(x, Pytra.CsModule.py_runtime.PYTRA_TID_SET)", cs)
        self.assertNotIn("return isinstance(", cs)

    def test_path_alias_constructor_and_parent_are_lowered(self) -> None:
        src = """from pytra.std.pathlib import Path

def build_path() -> Path:
    p: Path = Path("out/file.cs")
    return p.parent
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "path_case.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            cs = transpile_to_csharp(east)

        self.assertIn("using Path = Pytra.CsModule.py_path;", cs)
        self.assertIn("new Path(\"out/file.cs\")", cs)
        self.assertIn("return p.parent();", cs)

    def test_string_endswith_and_startswith_are_lowered(self) -> None:
        src = """def f(s: str) -> bool:
    return s.endswith(".py") or s.startswith("tmp")
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "str_methods.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            cs = transpile_to_csharp(east)

        self.assertIn("s.EndsWith(\".py\")", cs)
        self.assertIn("s.StartsWith(\"tmp\")", cs)

    def test_default_parameter_is_emitted_for_constant_default(self) -> None:
        src = """def pick(name: str = "") -> str:
    return name

def run() -> str:
    return pick()
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "default_param.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            cs = transpile_to_csharp(east)

        self.assertIn("public static string pick(string name = \"\")", cs)
        self.assertIn("return pick();", cs)

    def test_optional_param_is_not_emitted_before_required_param(self) -> None:
        src = """from pytra.std.pathlib import Path

def f(parser_backend: str = "self_hosted", root: Path = Path("src")) -> str:
    return parser_backend
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "param_order.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            cs = transpile_to_csharp(east)

        self.assertIn("public static string f(string parser_backend, Path root)", cs)
        self.assertNotIn("string parser_backend = \"self_hosted\"", cs)

    def test_sys_exit_is_lowered_to_environment_exit(self) -> None:
        src = """from pytra.std import sys

def stop() -> None:
    sys.exit(0)
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "sys_exit.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            cs = transpile_to_csharp(east)

        self.assertIn("System.Environment.Exit(System.Convert.ToInt32(0))", cs)
        self.assertNotIn("sys.exit(", cs)

    def test_docstring_expr_is_not_emitted_as_statement(self) -> None:
        src = '''def f() -> int:
    """doc"""
    return 1
'''
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "docstring_stmt.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            cs = transpile_to_csharp(east)

        self.assertNotIn('"doc";', cs)
        self.assertIn("return 1;", cs)

    def test_set_literal_is_lowered_to_hashset(self) -> None:
        src = """def f(k: str) -> bool:
    return k in {"A", "B"}
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "set_lit.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            cs = transpile_to_csharp(east)

        self.assertIn("new System.Collections.Generic.HashSet<object>", cs)
        self.assertIn(".Contains(k)", cs)

    def test_joinedstr_is_lowered_to_csharp_interpolated_string(self) -> None:
        src = """def f(prefix: str, n: int) -> str:
    return f"{prefix}_{n}"
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "fstring_case.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            cs = transpile_to_csharp(east)

        self.assertIn("return $\"{prefix}_{n}\";", cs)

    def test_large_tuple_is_lowered_to_list_object_for_mcs_compat(self) -> None:
        src = """def f() -> tuple[str, str, str, str, str, str, str, str]:
    return ("a", "b", "c", "d", "e", "f", "g", "h")
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "large_tuple.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            cs = transpile_to_csharp(east)

        self.assertIn("public static System.Collections.Generic.List<object> f()", cs)
        self.assertIn("return new System.Collections.Generic.List<object> { \"a\", \"b\", \"c\", \"d\", \"e\", \"f\", \"g\", \"h\" };", cs)

    def test_large_tuple_unpack_uses_indexer_instead_of_item8(self) -> None:
        src = """def f() -> str:
    a0, a1, a2, a3, a4, a5, a6, a7 = ("a", "b", "c", "d", "e", "f", "g", "h")
    return a7
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "large_tuple_unpack.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            cs = transpile_to_csharp(east)

        self.assertIn("[7]", cs)
        self.assertNotIn(".Item8", cs)

    def test_render_expr_kind_specific_hook_precedes_leaf_hook(self) -> None:
        emitter = CSharpEmitter({"kind": "Module", "body": [], "meta": {}})
        emitter.hooks["on_render_expr_name"] = (
            lambda _em, _kind, _expr_node: "specific_name_hook()"
        )
        emitter.hooks["on_render_expr_leaf"] = (
            lambda _em, _kind, _expr_node: "leaf_hook()"
        )
        rendered = emitter.render_expr({"kind": "Name", "id": "x"})
        self.assertEqual(rendered, "specific_name_hook()")

    def test_py2cs_does_not_import_src_common(self) -> None:
        src = (ROOT / "src" / "py2cs.py").read_text(encoding="utf-8")
        self.assertNotIn("src.common", src)
        self.assertNotIn("from common.", src)


if __name__ == "__main__":
    unittest.main()
