"""py2js (EAST based) smoke tests."""

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

from src.py2js import load_east, load_js_profile, transpile_to_js
from src.pytra.compiler.east_parts.core import convert_path
from hooks.js.emitter.js_emitter import JsEmitter


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

    def test_transpile_add_fixture_contains_function_signature(self) -> None:
        fixture = find_fixture_case("add")
        east = load_east(fixture, parser_backend="self_hosted")
        js = transpile_to_js(east)
        self.assertIn("function add(a, b) {", js)
        self.assertIn("console.log(", js)

    def test_load_east_from_json(self) -> None:
        fixture = find_fixture_case("add")
        east = convert_path(fixture)
        with tempfile.TemporaryDirectory() as td:
            east_json = Path(td) / "case.east.json"
            east_json.write_text(json.dumps(east), encoding="utf-8")
            loaded = load_east(east_json)
            js = transpile_to_js(loaded)
        self.assertIn("function add(a, b)", js)

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
        js = transpile_to_js(east)
        self.assertIn("for (let i = ", js)
        self.assertIn("i < 3", js)
        self.assertIn("i += 1", js)

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
                [sys.executable, "src/py2js.py", str(fixture), "-o", str(out_js)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertTrue((Path(td) / "pytra" / "std" / "time.js").exists())
            self.assertTrue((Path(td) / "pytra" / "runtime.js").exists())

    def test_cli_smoke_generates_js_file(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_js = Path(td) / "if_else.js"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2js.py", str(fixture), "-o", str(out_js)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertTrue(out_js.exists())
            txt = out_js.read_text(encoding="utf-8")
            self.assertIn("function abs_like", txt)

    def test_cli_rejects_stage2_compat_mode(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_js = Path(td) / "if_else.js"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2js.py", str(fixture), "-o", str(out_js), "--east-stage", "2"],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertIn("--east-stage 2 is no longer supported; use EAST3 (default).", proc.stderr)

    def test_py2js_does_not_import_src_common(self) -> None:
        src = (ROOT / "src" / "py2js.py").read_text(encoding="utf-8")
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
        self.assertIn("this[PYTRA_TYPE_ID] = Base.PYTRA_TYPE_ID;", js)
        self.assertIn("this[PYTRA_TYPE_ID] = Child.PYTRA_TYPE_ID;", js)
        self.assertIn("pyIsInstance(x, PY_TYPE_NUMBER)", js)
        self.assertIn("pyIsInstance(x, Base.PYTRA_TYPE_ID)", js)
        self.assertIn("pyIsInstance(x, Child.PYTRA_TYPE_ID)", js)

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
