"""py2js (EAST based) smoke tests."""

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

from backends.js.emitter.js_emitter import load_js_profile, transpile_to_js
from toolchain.compiler.transpile_cli import load_east3_document
from src.toolchain.compiler.east_parts.core import convert_path
from backends.js.emitter.js_emitter import JsEmitter
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
        target_lang="js",
    )
    return doc3 if isinstance(doc3, dict) else {}


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


class Py2JsSmokeTest(unittest.TestCase):
    def test_load_js_profile_contains_core_sections(self) -> None:
        profile = load_js_profile()
        self.assertIn("types", profile)
        self.assertIn("operators", profile)
        self.assertIn("syntax", profile)
        self.assertIn("runtime_calls", profile)

    def test_comment_fidelity_blocks_generated_comments_and_preserves_source_comments(self) -> None:
        sample = ROOT / "sample" / "py" / "01_mandelbrot.py"
        east = load_east(sample, parser_backend="self_hosted")
        js = transpile_to_js(east)
        assert_no_generated_comments(self, js)
        assert_sample01_module_comments(self, js, prefix="//")

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
        js = transpile_to_js(east)
        self.assertIn("for (let i = ", js)
        self.assertIn("i < 3", js)
        self.assertIn("i += 1", js)

    def test_for_core_static_range_inlines_start_when_safe(self) -> None:
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
                    "body": [{"kind": "Pass"}],
                    "orelse": [],
                }
            ],
            "main_guard_body": [],
            "meta": {},
        }
        js = transpile_to_js(east)
        self.assertIn("for (let i = 0; i < 3; i += 1)", js)
        self.assertNotIn("const __start_", js)

    def test_for_core_static_range_keeps_start_tmp_when_start_mentions_target(self) -> None:
        east = {
            "kind": "Module",
            "east_stage": 3,
            "body": [
                {
                    "kind": "ForCore",
                    "target_plan": {"kind": "NameTarget", "id": "i", "target_type": "int64"},
                    "iter_plan": {
                        "kind": "StaticRangeForPlan",
                        "start": {"kind": "Name", "id": "i"},
                        "stop": {"kind": "Name", "id": "n"},
                        "step": {"kind": "Constant", "value": 1},
                        "range_mode": "ascending",
                    },
                    "body": [{"kind": "Pass"}],
                    "orelse": [],
                }
            ],
            "main_guard_body": [],
            "meta": {},
        }
        js = transpile_to_js(east)
        self.assertIn("const __start_", js)
        self.assertIn("for (let i = __start_", js)

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
        js = transpile_to_js(east)
        self.assertIn("for (const [k, v] of pairs) {", js)
        self.assertIn("console.log(k, v);", js)

    def test_js_emitter_fail_closed_on_unresolved_stdlib_runtime_call(self) -> None:
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
            transpile_to_js(east)
        self.assertIn("unresolved stdlib runtime", str(cm.exception))

    def test_js_emitter_fail_closed_on_unresolved_resolved_runtime_call(self) -> None:
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
            transpile_to_js(east)
        self.assertIn("unresolved stdlib runtime", str(cm.exception))

    def test_ref_container_args_materialize_value_path_with_copy_expr(self) -> None:
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
            js = transpile_to_js(east)
        self.assertIn("let a = (Array.isArray(xs) ? xs.slice() : Array.from(xs));", js)
        self.assertIn("let b = ((ys && typeof ys === \"object\") ? { ...ys } : {});", js)
        self.assertNotIn("let a = xs;", js)
        self.assertNotIn("let b = ys;", js)

    def test_for_core_downcount_range_uses_descending_condition(self) -> None:
        fixture = find_fixture_case("range_downcount_len_minus1")
        east = load_east(fixture, parser_backend="self_hosted")
        js = transpile_to_js(east)
        self.assertIn("for (let i = ", js)
        self.assertIn("i > -1; i += -1)", js)
        self.assertNotIn("__start_", js)
        self.assertNotIn("i < -1; i += -1)", js)

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
        js = transpile_to_js(east)
        self.assertIn('import { pyBool, pyLen, pyStr, pyTypeId } from "./pytra/py_runtime.js";', js)
        self.assertIn("pyBool(x);", js)
        self.assertIn("pyLen(x);", js)
        self.assertIn("pyStr(x);", js)
        self.assertIn("pyTypeId(x);", js)
        self.assertIn("[Symbol.iterator]()", js)
        self.assertIn("__next.done ? null : __next.value", js)

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
        js = transpile_to_js(east)
        self.assertIn("pyIsInstance(x, PY_TYPE_NUMBER);", js)
        self.assertIn("pyIsInstance(x, Base.PYTRA_TYPE_ID);", js)
        self.assertIn("pyIsSubtype(PY_TYPE_BOOL, PY_TYPE_NUMBER);", js)
        self.assertIn("pyIsSubtype(Child.PYTRA_TYPE_ID, Base.PYTRA_TYPE_ID);", js)
        self.assertIn("pyIsSubtype", js)

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
        js = transpile_to_js(east)
        self.assertIn("y = 1;", js)
        self.assertIn("z = y;", js)

    def test_browser_import_symbols_are_treated_as_external(self) -> None:
        fixture = find_fixture_case("browser_external_symbols")
        east = load_east(fixture, parser_backend="self_hosted")
        js = transpile_to_js(east)
        self.assertIn("document.title", js)
        self.assertNotIn("import { document", js)
        self.assertNotIn("browser/widgets/dialog", js)

    def test_stdlib_imports_use_pytra_runtime_shim_paths(self) -> None:
        fixture = find_fixture_case("import_time_from")
        east = load_east(fixture, parser_backend="self_hosted")
        js = transpile_to_js(east)
        self.assertIn('from "./pytra/std/time.js"', js)

    def test_cli_generates_pytra_runtime_shims(self) -> None:
        fixture = find_fixture_case("import_time_from")
        with tempfile.TemporaryDirectory() as td:
            out_js = Path(td) / "import_time_from.js"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2x.py", "--target", "js", str(fixture), "-o", str(out_js)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertTrue((Path(td) / "pytra" / "std" / "time.js").exists())
            self.assertTrue((Path(td) / "pytra" / "py_runtime.js").exists())
            self.assertTrue((Path(td) / "pytra" / "utils" / "assertions.js").exists())

    def test_py2js_does_not_import_src_common(self) -> None:
        src = (ROOT / "src" / "py2x.py").read_text(encoding="utf-8")
        self.assertNotIn("src.common", src)
        self.assertNotIn("from common.", src)

    def test_render_expr_kind_specific_hook_precedes_leaf_hook(self) -> None:
        emitter = JsEmitter({"kind": "Module", "body": [], "meta": {}})
        emitter.hooks["on_render_expr_name"] = (
            lambda _em, _kind, _expr_node: "specific_name_hook()"
        )
        emitter.hooks["on_render_expr_leaf"] = (
            lambda _em, _kind, _expr_node: "leaf_hook()"
        )
        rendered = emitter.render_expr({"kind": "Name", "id": "x"})
        self.assertEqual(rendered, "specific_name_hook()")

    def test_isinstance_lowers_to_type_id_runtime_api(self) -> None:
        src = """class Base:
    def __init__(self):
        pass

class Child(Base):
    def __init__(self):
        super().__init__()

def f(x: object) -> bool:
    return isinstance(x, int) or isinstance(x, Base) or isinstance(x, Child)
"""
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "isinstance_type_id.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            js = transpile_to_js(east)

        self.assertIn('import { PYTRA_TYPE_ID, PY_TYPE_NUMBER, PY_TYPE_OBJECT, pyRegisterClassType, pyIsInstance } from "./pytra/py_runtime.js";', js)
        self.assertIn("static PYTRA_TYPE_ID = pyRegisterClassType([PY_TYPE_OBJECT]);", js)
        self.assertIn("static PYTRA_TYPE_ID = pyRegisterClassType([Base.PYTRA_TYPE_ID]);", js)
        self.assertIn("class Child extends Base {", js)
        self.assertIn("super();", js)
        self.assertIn("this[PYTRA_TYPE_ID] = Base.PYTRA_TYPE_ID;", js)
        self.assertIn("this[PYTRA_TYPE_ID] = Child.PYTRA_TYPE_ID;", js)
        self.assertIn("pyIsInstance(x, PY_TYPE_NUMBER)", js)
        self.assertIn("pyIsInstance(x, Base.PYTRA_TYPE_ID)", js)
        self.assertIn("pyIsInstance(x, Child.PYTRA_TYPE_ID)", js)

    def test_inheritance_virtual_dispatch_lowers_extends_and_super_method(self) -> None:
        fixture = find_fixture_case("inheritance_virtual_dispatch_multilang")
        east = load_east(fixture, parser_backend="self_hosted")
        js = transpile_to_js(east)
        self.assertIn("class Dog extends Animal {", js)
        self.assertIn("class LoudDog extends Dog {", js)
        self.assertIn('return "loud-" + super.speak();', js)
        self.assertNotIn("py_super()", js)

    def test_dict_literal_has_type_id_tag_for_isinstance(self) -> None:
        src = """def f() -> bool:
    x: dict[str, int] = {"k": 1}
    return isinstance(x, dict)
"""
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "dict_type_id.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            js = transpile_to_js(east)

        self.assertIn("[PYTRA_TYPE_ID]: PY_TYPE_MAP", js)
        self.assertIn("pyIsInstance(x, PY_TYPE_MAP)", js)

    def test_isinstance_tuple_lowers_to_or_of_type_id_checks(self) -> None:
        src = """class Base:
    def __init__(self):
        pass

def f(x: object) -> bool:
    return isinstance(x, (int, Base, dict, object))
"""
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "isinstance_tuple_type_id.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            js = transpile_to_js(east)

        self.assertIn("pyIsInstance(x, PY_TYPE_NUMBER)", js)
        self.assertIn("pyIsInstance(x, Base.PYTRA_TYPE_ID)", js)
        self.assertIn("pyIsInstance(x, PY_TYPE_MAP)", js)
        self.assertIn("pyIsInstance(x, PY_TYPE_OBJECT)", js)
        self.assertNotIn("isinstance(", js)

    def test_isinstance_set_lowers_to_set_type_id_check(self) -> None:
        src = """def f(x: object) -> bool:
    return isinstance(x, set)
"""
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "isinstance_set_type_id.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            js = transpile_to_js(east)

        self.assertIn("pyIsInstance(x, PY_TYPE_SET)", js)
        self.assertNotIn("isinstance(", js)


if __name__ == "__main__":
    unittest.main()
