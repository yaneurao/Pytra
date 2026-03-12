"""py2cs (EAST based) smoke tests."""

# Language-specific smoke suite.
# Shared py2x target-parameterized checks live in test_py2x_smoke_common.py.

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from backends.cs.emitter.cs_emitter import load_cs_profile, transpile_to_csharp
from toolchain.compiler.relative_import_firstwave_smoke_contract import (
    RELATIVE_IMPORT_FIRST_WAVE_SCENARIOS_V1,
)
from toolchain.compiler.transpile_cli import load_east3_document
from src.toolchain.ir.core_entrypoints import convert_path
from src.toolchain.frontends.type_expr import parse_type_expr_text
from backends.cs.emitter.cs_emitter import CSharpEmitter
from comment_fidelity import assert_no_generated_comments, assert_sample01_module_comments


def load_east(
    input_path: Path,
    parser_backend: str = "self_hosted",
    east_stage: str = "3",
    object_dispatch_mode: str = "native",
    east3_opt_level: str = "1",
    east3_opt_pass: str = "",
    dump_east3_before_opt: str = "",
    dump_east3_after_opt: str = "",
    dump_east3_opt_trace: str = "",
):
    if east_stage != "3":
        raise RuntimeError("unsupported east_stage: " + east_stage)
    doc3 = load_east3_document(
        input_path,
        parser_backend=parser_backend,
        object_dispatch_mode=object_dispatch_mode,
        east3_opt_level=east3_opt_level,
        east3_opt_pass=east3_opt_pass,
        dump_east3_before_opt=dump_east3_before_opt,
        dump_east3_after_opt=dump_east3_after_opt,
        dump_east3_opt_trace=dump_east3_opt_trace,
        target_lang="cs",
    )
    return doc3 if isinstance(doc3, dict) else {}


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


def _relative_import_firstwave_scenarios() -> dict[str, dict[str, object]]:
    return {
        str(entry["scenario_id"]): entry
        for entry in RELATIVE_IMPORT_FIRST_WAVE_SCENARIOS_V1
    }


def transpile_relative_import_project_to_csharp(scenario_id: str) -> str:
    scenario = _relative_import_firstwave_scenarios()[scenario_id]
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        entry_path = td_path / str(scenario["entry_rel"])
        helper_path = td_path / str(scenario["helper_rel"])
        entry_path.parent.mkdir(parents=True, exist_ok=True)
        helper_path.parent.mkdir(parents=True, exist_ok=True)
        for pkg_dir in {helper_path.parent, entry_path.parent}:
            current = pkg_dir
            while current != td_path and current.is_relative_to(td_path):
                init_py = current / "__init__.py"
                if not init_py.exists():
                    init_py.write_text("", encoding="utf-8")
                current = current.parent
        helper_path.write_text("def f() -> int:\n    return 7\n", encoding="utf-8")
        entry_path.write_text(
            f"{scenario['import_form']}\nprint({scenario['representative_expr']})\n",
            encoding="utf-8",
        )
        out = td_path / "Program.cs"
        proc = subprocess.run(
            ["python3", str(ROOT / "src" / "py2x.py"), str(entry_path), "--target", "cs", "-o", str(out)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            raise AssertionError(proc.stderr)
        return out.read_text(encoding="utf-8")


class Py2CsSmokeTest(unittest.TestCase):
    def test_load_cs_profile_contains_core_sections(self) -> None:
        profile = load_cs_profile()
        self.assertIn("types", profile)
        self.assertIn("operators", profile)
        self.assertIn("syntax", profile)
        self.assertIn("runtime_calls", profile)

    def test_bitwise_invert_basic_uses_csharp_invert_operator(self) -> None:
        fixture = find_fixture_case("bitwise_invert_basic")
        east = load_east(fixture, parser_backend="self_hosted")
        cs = transpile_to_csharp(east)
        self.assertIn("~y", cs)

    def test_comment_fidelity_preserves_source_comments(self) -> None:
        sample = ROOT / "sample" / "py" / "01_mandelbrot.py"
        east = load_east(sample, parser_backend="self_hosted")
        cs = transpile_to_csharp(east)
        assert_no_generated_comments(self, cs)
        assert_sample01_module_comments(self, cs, prefix="//")

    def test_bitwise_invert_fixture_uses_csharp_bitwise_not(self) -> None:
        fixture = find_fixture_case("bitwise_invert_basic")
        east = load_east(fixture, parser_backend="self_hosted")
        cs = transpile_to_csharp(east)
        self.assertIn("~y", cs)

    def test_cli_relative_import_firstwave_scenarios_transpile_for_csharp(self) -> None:
        expectations = {
            "parent_module_alias": (
                "using h = helper;",
                "System.Console.WriteLine(h.f());",
            ),
            "parent_symbol_alias": (
                "using g = helper.f;",
                "System.Console.WriteLine(g());",
            ),
        }
        for scenario_id, expected in expectations.items():
            with self.subTest(scenario_id=scenario_id):
                cs = transpile_relative_import_project_to_csharp(scenario_id)
                self.assertIn("public static class Program", cs)
                for needle in expected:
                    self.assertIn(needle, cs)

    def test_sample_01_uses_float_division_for_typed_div(self) -> None:
        sample = ROOT / "sample" / "py" / "01_mandelbrot.py"
        east = load_east(sample, parser_backend="self_hosted")
        cs = transpile_to_csharp(east)
        self.assertIn("System.Convert.ToDouble(iter_count) / System.Convert.ToDouble(max_iter)", cs)
        self.assertNotIn("double t = iter_count / max_iter;", cs)

    def test_class_inheritance_emits_base_clause(self) -> None:
        src = """class Base:
    pass

class Child(Base):
    pass
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "class_inherit.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            cs = transpile_to_csharp(east)
        self.assertIn("public class Child : Base", cs)

    def test_inheritance_virtual_dispatch_fixture_emits_override_and_base_call(self) -> None:
        fixture = find_fixture_case("inheritance_virtual_dispatch_multilang")
        east = load_east(fixture, parser_backend="self_hosted")
        cs = transpile_to_csharp(east)
        self.assertIn("public virtual string speak()", cs)
        self.assertIn("public override string speak()", cs)
        self.assertIn('return "loud-" + base.speak();', cs)
        self.assertIn("System.Console.WriteLine(true);", cs)

    def test_super_init_lowers_to_base_constructor_initializer(self) -> None:
        src = """class Base:
    def __init__(self, x: int):
        self.x = x

class Child(Base):
    def __init__(self, x: int):
        super().__init__(x)
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "super_init.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            cs = transpile_to_csharp(east)
        self.assertIn("public Child(long x) : base(x)", cs)

    def test_tuple_assign_fixture_lowers_swap_with_temp(self) -> None:
        fixture = find_fixture_case("tuple_assign")
        east = load_east(fixture, parser_backend="self_hosted")
        cs = transpile_to_csharp(east)
        self.assertIn("var __swap", cs)
        self.assertIn("x = y;", cs)
        self.assertIn("y = __swap", cs)

    def test_lambda_fixture_uses_func_signatures_and_parameters(self) -> None:
        fixture = find_fixture_case("lambda_basic")
        east = load_east(fixture, parser_backend="self_hosted")
        cs = transpile_to_csharp(east)
        self.assertIn("System.Func<dynamic, dynamic> add_base = (x) => x + py_base;", cs)
        self.assertIn("System.Func<bool> always_true = () => true;", cs)
        self.assertIn("System.Func<dynamic, bool> is_positive = (x) => (x) > (0);", cs)

    def test_comprehension_fixture_materializes_list(self) -> None:
        fixture = find_fixture_case("comprehension")
        east = load_east(fixture, parser_backend="self_hosted")
        cs = transpile_to_csharp(east)
        self.assertIn("new System.Func<System.Collections.Generic.List<long>>", cs)
        self.assertIn("foreach (var i in new System.Collections.Generic.List<long> { 1, 2, 3, 4 })", cs)

    def test_enumerate_fixture_uses_pytra_enumerate_helper(self) -> None:
        fixture = find_fixture_case("enumerate_basic")
        east = load_east(fixture, parser_backend="self_hosted")
        cs = transpile_to_csharp(east)
        self.assertIn("foreach (var __it_1 in Program.PytraEnumerate(values)) {", cs)
        self.assertIn("foreach (var __it_3 in Program.PytraEnumerate(values, 1)) {", cs)

    def test_attribute_annassign_uses_type_hint_for_set_and_dict_literals(self) -> None:
        src = """class Holder:
    def __init__(self):
        self.names: set[str] = set(["a"])
        self.mapping: dict[str, str] = {}
        self.lines: list[str] = []
        self.scopes: list[set[str]] = [set()]
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "attr_annassign.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            cs = transpile_to_csharp(east)
        self.assertIn("this.names = new System.Collections.Generic.HashSet<string>(", cs)
        self.assertIn("this.mapping = new System.Collections.Generic.Dictionary<string, string>();", cs)
        self.assertIn("this.lines = new System.Collections.Generic.List<string>();", cs)
        self.assertIn(
            "this.scopes = new System.Collections.Generic.List<System.Collections.Generic.HashSet<string>> { new System.Collections.Generic.HashSet<string>() };",
            cs,
        )

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

    def test_csharp_emitter_fail_closed_on_unresolved_stdlib_runtime_call(self) -> None:
        east = {
            "kind": "Module",
            "east_stage": 3,
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "_case_main",
                    "arg_order": [],
                    "arg_types": {},
                    "return_type": "None",
                    "body": [
                        {
                            "kind": "Expr",
                            "value": {
                                "kind": "Call",
                                "func": {"kind": "Name", "id": "save_gif"},
                                "args": [],
                                "keywords": [],
                                "semantic_tag": "stdlib.fn.save_gif",
                            },
                        }
                    ],
                }
            ],
            "main_guard_body": [],
            "meta": {},
        }
        with self.assertRaises(RuntimeError) as cm:
            transpile_to_csharp(east)
        self.assertIn("unresolved stdlib runtime", str(cm.exception))

    def test_csharp_emitter_fail_closed_on_unresolved_resolved_runtime_call(self) -> None:
        east = {
            "kind": "Module",
            "east_stage": 3,
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "_case_main",
                    "arg_order": [],
                    "arg_types": {},
                    "return_type": "None",
                    "body": [
                        {
                            "kind": "Expr",
                            "value": {
                                "kind": "Call",
                                "func": {"kind": "Name", "id": "save_gif"},
                                "args": [],
                                "keywords": [],
                                "semantic_tag": "stdlib.fn.save_gif",
                                "resolved_runtime_call": "save_gif_not_registered",
                                "resolved_runtime_source": "resolved_runtime_call",
                            },
                        }
                    ],
                }
            ],
            "main_guard_body": [],
            "meta": {},
        }
        with self.assertRaises(RuntimeError) as cm:
            transpile_to_csharp(east)
        self.assertIn("unresolved stdlib runtime", str(cm.exception))

    def test_runtime_import_resolution_uses_canonical_runtime_helpers(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "runtime_imports.py"
            src_py.write_text(
                "import math as m\n"
                "from math import pi\n"
                "from pytra.utils import gif\n"
                "from pytra.utils.gif import save_gif\n"
                "\n"
                "def main() -> None:\n"
                "    x: float = m.sqrt(4.0)\n"
                "    y: float = pi\n"
                "    gif.save_gif('x.gif', 1, 1, [])\n"
                "    save_gif('x.gif', 1, 1, [])\n"
                "    print(x, y)\n",
                encoding="utf-8",
            )
            east = load_east(src_py, parser_backend="self_hosted")
            cs = transpile_to_csharp(east)

        self.assertIn("using m = Pytra.CsModule.math;", cs)
        self.assertIn("using gif = Pytra.CsModule.gif_helper;", cs)
        self.assertIn("double x = m.sqrt(4.0);", cs)
        self.assertIn("Pytra.CsModule.math.pi", cs)
        self.assertIn('gif.save_gif("x.gif", 1, 1, new System.Collections.Generic.List<object>());', cs)
        self.assertIn('Pytra.CsModule.gif_helper.save_gif("x.gif", 1, 1, new System.Collections.Generic.List<object>());', cs)

    def test_for_core_downcount_range_uses_descending_condition(self) -> None:
        fixture = find_fixture_case("range_downcount_len_minus1")
        east = load_east(fixture, parser_backend="self_hosted")
        cs = transpile_to_csharp(east)
        self.assertIn("for (i = (xs).Count - 1; i > -1; i += -1)", cs)
        self.assertNotIn("for (i = (xs).Count - 1; i < -1; i += -1)", cs)

    def test_dict_literal_widens_to_object_for_mixed_value_types(self) -> None:
        east = {
            "kind": "Module",
            "east_stage": 3,
            "body": [
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "func": {"kind": "Name", "id": "print"},
                        "args": [
                            {
                                "kind": "Dict",
                                "resolved_type": "dict[str,str]",
                                "entries": [
                                    {
                                        "key": {"kind": "Constant", "value": "kind"},
                                        "value": {"kind": "Constant", "value": "For"},
                                    },
                                    {
                                        "key": {"kind": "Constant", "value": "target"},
                                        "value": {"kind": "Name", "id": "target", "resolved_type": "dict[str,object]"},
                                    },
                                ],
                            }
                        ],
                        "keywords": [],
                    },
                }
            ],
            "main_guard_body": [],
            "meta": {},
        }
        cs = transpile_to_csharp(east)
        self.assertIn(
            "new System.Collections.Generic.Dictionary<string, object> { { \"kind\", \"For\" }, { \"target\", target } }",
            cs,
        )

    def test_ref_container_args_materialize_value_path_with_copy_ctor(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "ref_container_args.py"
            src.write_text(
                "def f(xs: list[int], ys: dict[str, int]) -> int:\n"
                "    a: list[int] = xs\n"
                "    b: dict[str, int] = ys\n"
                "    a.append(1)\n"
                "    b['k'] = 2\n"
                "    return len(a) + len(b)\n",
                encoding="utf-8",
            )
            east = load_east(src, parser_backend="self_hosted")
            cs = transpile_to_csharp(east)
        self.assertIn(
            "System.Collections.Generic.List<long> a = new System.Collections.Generic.List<long>(xs);",
            cs,
        )
        self.assertIn(
            "System.Collections.Generic.Dictionary<string, long> b = new System.Collections.Generic.Dictionary<string, long>(ys);",
            cs,
        )
        self.assertNotIn("System.Collections.Generic.List<long> a = xs;", cs)
        self.assertNotIn("System.Collections.Generic.Dictionary<string, long> b = ys;", cs)

    def test_bytearray_mutation_stays_on_runtime_helpers_but_list_append_does_not(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "bytearray_mutation.py"
            src.write_text(
                "def f(xs: list[int], buf: bytearray) -> int:\n"
                "    xs.append(1)\n"
                "    buf.append(2)\n"
                "    return buf.pop() + len(xs)\n",
                encoding="utf-8",
            )
            east = load_east(src, parser_backend="self_hosted")
            cs = transpile_to_csharp(east)
        self.assertIn("xs.Add(1);", cs)
        self.assertNotIn("Pytra.CsModule.py_runtime.py_append(xs", cs)
        self.assertIn("Pytra.CsModule.py_runtime.py_append(buf, 2);", cs)
        self.assertIn("Pytra.CsModule.py_runtime.py_pop(buf)", cs)

    def test_bytes_mutation_fail_closed_instead_of_using_runtime_helpers(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "bytes_mutation.py"
            src.write_text(
                "def f(buf: bytes) -> int:\n"
                "    buf.pop()\n"
                "    return 0\n",
                encoding="utf-8",
            )
            east = load_east(src, parser_backend="self_hosted")
            with self.assertRaises(RuntimeError) as cm:
                transpile_to_csharp(east)
        self.assertIn("bytes mutation helpers are unsupported", str(cm.exception))

    def test_bytearray_index_and_slice_compat_helpers_stay_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "bytearray_index_slice.py"
            src.write_text(
                "def f(buf: bytearray, i: int) -> int:\n"
                "    head = buf[i]\n"
                "    seg = buf[0:2]\n"
                "    buf[i] = head\n"
                "    return head + len(seg)\n",
                encoding="utf-8",
            )
            east = load_east(src, parser_backend="self_hosted")
            cs = transpile_to_csharp(east)
        self.assertIn("Pytra.CsModule.py_runtime.py_get(buf, i)", cs)
        self.assertIn(
            "Pytra.CsModule.py_runtime.py_slice(buf, System.Convert.ToInt64(0), System.Convert.ToInt64(2))",
            cs,
        )
        self.assertIn("Pytra.CsModule.py_runtime.py_set(buf, i, head);", cs)

    def test_try_with_multiple_except_handlers_is_emitted(self) -> None:
        east = {
            "kind": "Module",
            "east_stage": 3,
            "body": [
                {
                    "kind": "Try",
                    "body": [
                        {
                            "kind": "Raise",
                            "exc": {
                                "kind": "Call",
                                "func": {"kind": "Name", "id": "Exception"},
                                "args": [{"kind": "Constant", "value": "boom"}],
                                "keywords": [],
                            },
                        }
                    ],
                    "handlers": [
                        {
                            "kind": "ExceptHandler",
                            "type": {"kind": "Name", "id": "ValueError"},
                            "name": "ve",
                            "body": [{"kind": "Expr", "value": {"kind": "Name", "id": "ve"}}],
                        },
                        {
                            "kind": "ExceptHandler",
                            "type": {"kind": "Name", "id": "Exception"},
                            "name": "ex",
                            "body": [{"kind": "Expr", "value": {"kind": "Name", "id": "ex"}}],
                        },
                    ],
                    "orelse": [],
                    "finalbody": [],
                }
            ],
            "main_guard_body": [],
            "meta": {},
        }
        cs = transpile_to_csharp(east)
        self.assertIn("catch (System.Exception ex)", cs)
        self.assertIn("if (true) {", cs)
        self.assertIn("} else if (true) {", cs)

    def test_for_unknown_iterable_casts_to_ienumerable(self) -> None:
        east = {
            "kind": "Module",
            "east_stage": 3,
            "body": [
                {
                    "kind": "For",
                    "target": {"kind": "Name", "id": "x"},
                    "iter": {"kind": "Name", "id": "src", "resolved_type": "object"},
                    "body": [{"kind": "Expr", "value": {"kind": "Name", "id": "x"}}],
                    "orelse": [],
                }
            ],
            "main_guard_body": [],
            "meta": {},
        }
        cs = transpile_to_csharp(east)
        self.assertIn("foreach (var x in ((System.Collections.IEnumerable)(src))) {", cs)

    def test_for_dict_items_unknown_keeps_keyvalue_iteration(self) -> None:
        east = {
            "kind": "Module",
            "east_stage": 3,
            "body": [
                {
                    "kind": "For",
                    "target": {
                        "kind": "Tuple",
                        "elements": [
                            {"kind": "Name", "id": "k"},
                            {"kind": "Name", "id": "v"},
                        ],
                    },
                    "iter": {
                        "kind": "Call",
                        "func": {
                            "kind": "Attribute",
                            "value": {"kind": "Name", "id": "d", "resolved_type": "object"},
                            "attr": "items",
                        },
                        "args": [],
                        "keywords": [],
                        "resolved_type": "object",
                    },
                    "body": [{"kind": "Expr", "value": {"kind": "Name", "id": "k"}}],
                    "orelse": [],
                }
            ],
            "main_guard_body": [],
            "meta": {},
        }
        cs = transpile_to_csharp(east)
        self.assertIn("foreach (var __it", cs)
        self.assertIn(".Key;", cs)
        self.assertIn(".Value;", cs)
        self.assertNotIn("System.Collections.IEnumerable)(((System.Collections.Generic.Dictionary<string, object>)d))", cs)

    def test_sorted_builtin_is_lowered(self) -> None:
        east = {
            "kind": "Module",
            "east_stage": 3,
            "body": [
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "func": {"kind": "Name", "id": "sorted"},
                        "args": [{"kind": "Name", "id": "xs"}],
                        "keywords": [],
                    },
                }
            ],
            "main_guard_body": [],
            "meta": {},
        }
        cs = transpile_to_csharp(east)
        self.assertIn("System.Linq.Enumerable.OrderBy(xs, __x => System.Convert.ToString(__x)).ToList()", cs)

    def test_dict_builtin_with_hint_uses_dict_any_helper(self) -> None:
        east = {
            "kind": "Module",
            "east_stage": 3,
            "body": [
                {
                    "kind": "Assign",
                    "target": {"kind": "Name", "id": "d", "resolved_type": "dict[str, object]"},
                    "value": {
                        "kind": "Call",
                        "func": {"kind": "Name", "id": "dict"},
                        "args": [{"kind": "Name", "id": "src", "resolved_type": "object"}],
                        "keywords": [],
                        "resolved_type": "dict[str, object]",
                    },
                }
            ],
            "main_guard_body": [],
            "meta": {},
        }
        cs = transpile_to_csharp(east)
        self.assertIn("Program.PytraDictStringObjectFromAny(src)", cs)
        self.assertIn("PytraDictStringObjectFromAny(object source)", cs)

    def test_string_multiply_is_lowered(self) -> None:
        east = {
            "kind": "Module",
            "east_stage": 3,
            "body": [
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "BinOp",
                        "op": "Mult",
                        "left": {"kind": "Constant", "value": "ab"},
                        "right": {"kind": "Constant", "value": 3},
                    },
                }
            ],
            "main_guard_body": [],
            "meta": {},
        }
        cs = transpile_to_csharp(east)
        self.assertIn("string.Concat(System.Linq.Enumerable.Repeat(\"ab\", System.Convert.ToInt32(3)))", cs)

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
        self.assertIn("Pytra.CsModule.py_runtime.py_runtime_value_type_id(x);", cs)
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
        self.assertIn("Pytra.CsModule.py_runtime.py_runtime_value_isinstance(x, Pytra.CsModule.py_runtime.PYTRA_TID_INT);", cs)
        self.assertIn("Pytra.CsModule.py_runtime.py_runtime_value_isinstance(x, Base.PYTRA_TYPE_ID);", cs)
        self.assertIn("Pytra.CsModule.py_runtime.py_runtime_type_id_is_subtype(Pytra.CsModule.py_runtime.PYTRA_TID_BOOL, Pytra.CsModule.py_runtime.PYTRA_TID_INT);", cs)
        self.assertIn("Pytra.CsModule.py_runtime.py_runtime_type_id_issubclass(Child.PYTRA_TYPE_ID, Base.PYTRA_TYPE_ID);", cs)
        self.assertNotIn("Pytra.CsModule.py_runtime.py_runtime_type_id(", cs)
        self.assertNotIn("Pytra.CsModule.py_runtime.py_is_subtype(", cs)
        self.assertNotIn("Pytra.CsModule.py_runtime.py_issubclass(", cs)
        self.assertNotIn("Pytra.CsModule.py_runtime.py_isinstance(", cs)

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

    def test_isinstance_builtin_lowers_to_csharp_is_checks(self) -> None:
        src = """def f(x: object) -> bool:
    return isinstance(x, int) or isinstance(x, str)
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "isinstance_builtin.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            cs = transpile_to_csharp(east)

        self.assertIn("Pytra.CsModule.py_runtime.py_runtime_value_isinstance(x, Pytra.CsModule.py_runtime.PYTRA_TID_INT)", cs)
        self.assertIn("Pytra.CsModule.py_runtime.py_runtime_value_isinstance(x, Pytra.CsModule.py_runtime.PYTRA_TID_STR)", cs)
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

        self.assertIn("Pytra.CsModule.py_runtime.py_runtime_value_isinstance(x, Base.PYTRA_TYPE_ID)", cs)
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

        self.assertIn("Pytra.CsModule.py_runtime.py_runtime_value_isinstance(x, Pytra.CsModule.py_runtime.PYTRA_TID_OBJECT)", cs)
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

        self.assertIn("Pytra.CsModule.py_runtime.py_runtime_value_isinstance(x, Pytra.CsModule.py_runtime.PYTRA_TID_INT)", cs)
        self.assertIn("Pytra.CsModule.py_runtime.py_runtime_value_isinstance(x, Base.PYTRA_TYPE_ID)", cs)
        self.assertIn("Pytra.CsModule.py_runtime.py_runtime_value_isinstance(x, Pytra.CsModule.py_runtime.PYTRA_TID_DICT)", cs)
        self.assertIn("Pytra.CsModule.py_runtime.py_runtime_value_isinstance(x, Pytra.CsModule.py_runtime.PYTRA_TID_OBJECT)", cs)
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

        self.assertIn("Pytra.CsModule.py_runtime.py_runtime_value_isinstance(x, Pytra.CsModule.py_runtime.PYTRA_TID_SET)", cs)
        self.assertNotIn("return isinstance(", cs)

    def test_representative_is_instance_fixture_transpiles(self) -> None:
        fixture = find_fixture_case("is_instance")
        east = load_east(fixture, parser_backend="self_hosted")
        cs = transpile_to_csharp(east)
        self.assertIn("Pytra.CsModule.py_runtime.py_runtime_value_isinstance(", cs)
        self.assertNotIn("unsupported", cs)

    def test_representative_for_range_fixture_transpiles(self) -> None:
        fixture = find_fixture_case("for_range")
        east = load_east(fixture, parser_backend="self_hosted")
        cs = transpile_to_csharp(east)
        self.assertIn("for (i = 0; i < n; i += 1)", cs)
        self.assertIn("total += i;", cs)
        self.assertNotIn("unsupported", cs)

    def test_representative_try_raise_fixture_transpiles(self) -> None:
        fixture = find_fixture_case("try_raise")
        east = load_east(fixture, parser_backend="self_hosted")
        cs = transpile_to_csharp(east)
        self.assertIn('throw new System.Exception("fail-19");', cs)
        self.assertIn("catch (System.Exception ex)", cs)
        self.assertNotIn("unsupported", cs)

    def test_representative_zip_fixture_transpiles(self) -> None:
        fixture = find_fixture_case("ok_generator_tuple_target")
        east = load_east(fixture, parser_backend="self_hosted")
        cs = transpile_to_csharp(east)
        self.assertIn("foreach (var __it_", cs)
        self.assertIn("in zip(wo, x)", cs)
        self.assertIn("var wi = __it_", cs)
        self.assertIn(".Item1;", cs)
        self.assertIn("var xi = __it_", cs)
        self.assertIn(".Item2;", cs)
        self.assertIn("__out_1.Add(wi * xi);", cs)
        self.assertNotIn("foreach (var _ in zip(wo, x))", cs)
        self.assertNotIn("unsupported", cs)

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

        self.assertIn("new System.Collections.Generic.HashSet<string>", cs)
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

    def test_builtin_set_call_is_lowered(self) -> None:
        src = """def f(xs):
    return set(xs)
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "set_call.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            cs = transpile_to_csharp(east)

        self.assertIn("new System.Collections.Generic.HashSet<object>(xs)", cs)

    def test_for_over_string_uses_string_projection(self) -> None:
        src = """def f(text: str) -> int:
    c = 0
    for ch in text:
        if ch == "a":
            c += 1
    return c
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "for_str.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            cs = transpile_to_csharp(east)

        self.assertIn("Select(__ch => __ch.ToString())", cs)

    def test_staticmethod_in_class_is_emitted_static(self) -> None:
        src = """class A:
    @staticmethod
    def f(x: int) -> int:
        return x
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "static_method.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            cs = transpile_to_csharp(east)

        self.assertIn("public static long f(long x)", cs)

    def test_json_loads_call_is_lowered_for_cs_selfhost_compile(self) -> None:
        src = """from pytra.std import json

def f(s: str):
    return json.loads(s)
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "json_loads.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            cs = transpile_to_csharp(east)

        self.assertIn("Pytra.CsModule.json.loads(s)", cs)

    def test_string_methods_find_rfind_strip_replace_are_lowered(self) -> None:
        src = """def f(s: str) -> int:
    return s.strip().replace("x", "y").find("y") + s.rfind("y")
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "str_methods.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            cs = transpile_to_csharp(east)

        self.assertIn(".Trim()", cs)
        self.assertIn(".Replace(\"x\", \"y\")", cs)
        self.assertIn(".IndexOf(\"y\")", cs)
        self.assertIn(".LastIndexOf(\"y\")", cs)

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
        src = (ROOT / "src" / "py2x.py").read_text(encoding="utf-8")
        self.assertNotIn("src.common", src)
        self.assertNotIn("from common.", src)

    def test_transpile_rejects_general_union_type_expr_in_annassign(self) -> None:
        east = {
            "kind": "Module",
            "body": [
                {
                    "kind": "AnnAssign",
                    "target": {"kind": "Name", "id": "value", "resolved_type": "list[int64|bool]"},
                    "annotation": "list[int64|bool]",
                    "annotation_type_expr": parse_type_expr_text("list[int | bool]"),
                    "decl_type": "list[int64|bool]",
                    "decl_type_expr": parse_type_expr_text("list[int | bool]"),
                    "value": {"kind": "List", "elements": [], "resolved_type": "list[int64|bool]"},
                }
            ],
        }
        with self.assertRaisesRegex(
            RuntimeError,
            "unsupported_syntax\\|C# backend does not support general union TypeExpr yet",
        ):
            transpile_to_csharp(east)

    def test_transpile_rejects_general_union_type_expr_in_signature(self) -> None:
        east = {
            "kind": "Module",
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "pick",
                    "args": [{"arg": "x"}],
                    "arg_order": ["x"],
                    "arg_types": {"x": "int64|bool"},
                    "arg_type_exprs": {"x": parse_type_expr_text("int | bool")},
                    "arg_usage": {"x": "readonly"},
                    "return_type": "int64|bool",
                    "return_type_expr": parse_type_expr_text("int | bool"),
                    "body": [{"kind": "Return", "value": {"kind": "Name", "id": "x", "resolved_type": "int64|bool"}}],
                }
            ],
        }
        with self.assertRaisesRegex(
            RuntimeError,
            "unsupported_syntax\\|C# backend does not support general union TypeExpr yet",
        ):
            transpile_to_csharp(east)

    def test_transpile_rejects_nominal_adt_class_lane(self) -> None:
        east = {
            "kind": "Module",
            "body": [
                {
                    "kind": "ClassDef",
                    "name": "Maybe",
                    "meta": {
                        "nominal_adt_v1": {
                            "schema_version": 1,
                            "role": "family",
                            "family_name": "Maybe",
                        }
                    },
                    "body": [],
                }
            ],
        }
        with self.assertRaisesRegex(
            RuntimeError,
            "unsupported_syntax\\|C# backend does not support nominal ADT v1 lanes yet",
        ):
            transpile_to_csharp(east)

    def test_transpile_rejects_nominal_adt_match_lane(self) -> None:
        east = {
            "kind": "Module",
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "f",
                    "args": [{"arg": "x"}],
                    "arg_order": ["x"],
                    "arg_types": {"x": "Maybe"},
                    "arg_usage": {"x": "readonly"},
                    "return_type": "int64",
                    "body": [{"kind": "Match", "subject": {"kind": "Name", "id": "x", "resolved_type": "Maybe"}}],
                }
            ],
        }
        with self.assertRaisesRegex(
            RuntimeError,
            "unsupported_syntax\\|C# backend does not support nominal ADT v1 lanes yet",
        ):
            transpile_to_csharp(east)

    def test_transpile_rejects_nominal_adt_projection_lane(self) -> None:
        east = {
            "kind": "Module",
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "f",
                    "args": [{"arg": "x"}],
                    "arg_order": ["x"],
                    "arg_types": {"x": "Just"},
                    "arg_usage": {"x": "readonly"},
                    "return_type": "int64",
                    "body": [
                        {
                            "kind": "Return",
                            "value": {
                                "kind": "Attribute",
                                "value": {"kind": "Name", "id": "x", "resolved_type": "Just"},
                                "attr": "value",
                                "resolved_type": "int64",
                                "lowered_kind": "NominalAdtProjection",
                            },
                        }
                    ],
                }
            ],
        }
        with self.assertRaisesRegex(
            RuntimeError,
            "unsupported_syntax\\|C# backend does not support nominal ADT v1 lanes yet",
        ):
            transpile_to_csharp(east)


if __name__ == "__main__":
    unittest.main()
