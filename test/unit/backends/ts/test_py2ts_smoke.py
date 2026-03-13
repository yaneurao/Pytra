"""py2ts (EAST based) smoke tests."""

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
if str(ROOT / "test" / "unit" / "backends") not in sys.path:
    sys.path.insert(0, str(ROOT / "test" / "unit" / "backends"))

from backends.ts.emitter.ts_emitter import load_ts_profile, transpile_to_typescript
from toolchain.compiler.transpile_cli import load_east3_document
from src.toolchain.ir.core_entrypoints import convert_path
from backends.ts.emitter import ts_emitter as ts_emitter_mod
from comment_fidelity import assert_no_generated_comments, assert_sample01_module_comments
from relative_import_secondwave_smoke_support import (
    relative_import_secondwave_expected_needles,
    transpile_relative_import_project,
)


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
        target_lang="ts",
    )
    return doc3 if isinstance(doc3, dict) else {}


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


class Py2TsSmokeTest(unittest.TestCase):
    def test_load_ts_profile_contains_core_sections(self) -> None:
        profile = load_ts_profile()
        self.assertIn("types", profile)
        self.assertIn("operators", profile)
        self.assertIn("syntax", profile)
        self.assertIn("runtime_calls", profile)

    def test_bitwise_invert_basic_uses_ts_invert_operator(self) -> None:
        fixture = find_fixture_case("bitwise_invert_basic")
        east = load_east(fixture, parser_backend="self_hosted")
        ts = transpile_to_typescript(east)
        self.assertIn("~y", ts)

    def test_comment_fidelity_preserves_source_comments(self) -> None:
        sample = ROOT / "sample" / "py" / "01_mandelbrot.py"
        east = load_east(sample, parser_backend="self_hosted")
        ts = transpile_to_typescript(east)
        assert_no_generated_comments(self, ts)
        assert_sample01_module_comments(self, ts, prefix="//")

    def test_bitwise_invert_fixture_uses_typescript_bitwise_not(self) -> None:
        fixture = find_fixture_case("bitwise_invert_basic")
        east = load_east(fixture, parser_backend="self_hosted")
        ts = transpile_to_typescript(east)
        self.assertIn("~y", ts)

    def test_secondary_bundle_representative_fixtures_transpile_for_typescript(self) -> None:
        for stem in (
            "tuple_assign",
            "lambda_basic",
            "comprehension",
            "for_range",
            "try_raise",
            "inheritance_virtual_dispatch_multilang",
            "enumerate_basic",
            "ok_generator_tuple_target",
            "is_instance",
            "json_extended",
            "pathlib_extended",
            "enum_extended",
            "argparse_extended",
            "pytra_std_import_math",
            "re_extended",
        ):
            with self.subTest(stem=stem):
                fixture = find_fixture_case(stem)
                east = load_east(fixture, parser_backend="self_hosted")
                ts = transpile_to_typescript(east)
                self.assertTrue(ts.strip())

    def test_representative_property_method_call_fixture_transpiles(self) -> None:
        try:
            from test.unit.backends.representative_contract_support import (
                assert_no_representative_escape,
            )
        except ModuleNotFoundError:
            from representative_contract_support import assert_no_representative_escape

        fixture = find_fixture_case("property_method_call")
        east = load_east(fixture, parser_backend="self_hosted")
        ts = transpile_to_typescript(east)
        assert_no_representative_escape(self, ts, backend="ts", fixture="property_method_call")

    def test_representative_list_bool_index_fixture_transpiles(self) -> None:
        try:
            from test.unit.backends.representative_contract_support import (
                assert_no_representative_escape,
            )
        except ModuleNotFoundError:
            from representative_contract_support import assert_no_representative_escape

        fixture = find_fixture_case("list_bool_index")
        east = load_east(fixture, parser_backend="self_hosted")
        ts = transpile_to_typescript(east)
        assert_no_representative_escape(self, ts, backend="ts", fixture="list_bool_index")

    def test_tuple_assign_fixture_lowers_swap_via_temp_for_typescript(self) -> None:
        fixture = find_fixture_case("tuple_assign")
        east = load_east(fixture, parser_backend="self_hosted")
        ts = transpile_to_typescript(east)
        self.assertIn("const __swap_", ts)
        self.assertIn("x = y;", ts)
        self.assertRegex(ts, r"y = __swap_\d+;")

    def test_cli_relative_import_secondwave_scenarios_transpile_for_typescript(self) -> None:
        for scenario_id in ("parent_module_alias", "parent_symbol_alias"):
            with self.subTest(scenario_id=scenario_id):
                ts = transpile_relative_import_project(ROOT, scenario_id, "ts")
                for needle in relative_import_secondwave_expected_needles(scenario_id):
                    self.assertIn(needle, ts)

    def test_stdlib_imports_use_pytra_runtime_shim_paths(self) -> None:
        fixture = find_fixture_case("import_time_from")
        east = load_east(fixture, parser_backend="self_hosted")
        ts = transpile_to_typescript(east)
        self.assertIn('from "./pytra/std/time.js"', ts)

    def test_stdlib_json_import_uses_pytra_runtime_shim_path(self) -> None:
        fixture = find_fixture_case("json_extended")
        east = load_east(fixture, parser_backend="self_hosted")
        ts = transpile_to_typescript(east)
        self.assertIn('from "./pytra/std/json.js"', ts)

    def test_ts_preview_ambient_global_extern_is_lowered_without_decl_or_import(self) -> None:
        src = """
from pytra.std import extern

document: Any = extern()
doc: Any = extern("document")

def main() -> None:
    title = document.title
    node = doc.getElementById("app")
"""
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "ts_ambient_global_extern.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            ts = transpile_to_typescript(east)
        self.assertIn("let title = document.title;", ts)
        self.assertIn('let node = document.getElementById("app");', ts)
        self.assertNotIn("let document = ", ts)
        self.assertNotIn("let doc = ", ts)
        self.assertNotIn("import { document", ts)

    def test_cli_generates_pytra_runtime_shims(self) -> None:
        fixture = find_fixture_case("import_time_from")
        with tempfile.TemporaryDirectory() as td:
            out_ts = Path(td) / "import_time_from.ts"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2x.py", "--target", "ts", str(fixture), "-o", str(out_ts)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertTrue((Path(td) / "pytra" / "std" / "json.js").exists())
            self.assertTrue((Path(td) / "pytra" / "std" / "time.js").exists())
            self.assertTrue((Path(td) / "pytra" / "std" / "pathlib.js").exists())
            self.assertTrue((Path(td) / "pytra" / "py_runtime.js").exists())
            json_shim = (Path(td) / "pytra" / "std" / "json.js").read_text(encoding="utf-8")
            self.assertIn("generated/std/json.js", json_shim)
            pathlib_shim = (Path(td) / "pytra" / "std" / "pathlib.js").read_text(encoding="utf-8")
            self.assertIn("generated/std/pathlib.js", pathlib_shim)

    def test_ts_repo_compat_lane_reexports_runtime_helpers(self) -> None:
        compat_runtime = ROOT / "src" / "runtime" / "ts" / "pytra" / "py_runtime.ts"
        compat_json = ROOT / "src" / "runtime" / "ts" / "pytra" / "std" / "json.ts"
        compat_math = ROOT / "src" / "runtime" / "ts" / "pytra" / "std" / "math.ts"
        compat_pathlib = ROOT / "src" / "runtime" / "ts" / "pytra" / "std" / "pathlib.ts"
        compat_time = ROOT / "src" / "runtime" / "ts" / "pytra" / "std" / "time.ts"
        compat_png = ROOT / "src" / "runtime" / "ts" / "pytra" / "utils" / "png.ts"
        compat_gif = ROOT / "src" / "runtime" / "ts" / "pytra" / "utils" / "gif.ts"
        self.assertTrue(compat_runtime.exists())
        self.assertTrue(compat_json.exists())
        self.assertTrue(compat_math.exists())
        self.assertTrue(compat_pathlib.exists())
        self.assertTrue(compat_time.exists())
        self.assertTrue(compat_png.exists())
        self.assertTrue(compat_gif.exists())
        self.assertEqual(
            compat_runtime.read_text(encoding="utf-8").strip(),
            'export * from "../native/built_in/py_runtime";',
        )
        self.assertEqual(
            compat_json.read_text(encoding="utf-8").strip(),
            'export * from "../../generated/std/json";',
        )
        self.assertEqual(
            compat_math.read_text(encoding="utf-8").strip(),
            'export * from "../../generated/std/math";',
        )
        self.assertEqual(
            compat_pathlib.read_text(encoding="utf-8").strip(),
            'export * from "../../generated/std/pathlib";',
        )
        self.assertEqual(
            compat_time.read_text(encoding="utf-8").strip(),
            'export { perf_counter, perfCounter } from "../../generated/std/time";',
        )
        self.assertEqual(
            compat_png.read_text(encoding="utf-8").strip(),
            'export * from "../../generated/utils/png";',
        )
        self.assertEqual(
            compat_gif.read_text(encoding="utf-8").strip(),
            'export * from "../../generated/utils/gif";',
        )

    def test_ts_generated_built_in_compare_lane_rehomes_native_runtime_import(self) -> None:
        generated_contains = ROOT / "src" / "runtime" / "ts" / "generated" / "built_in" / "contains.ts"
        generated_sequence = ROOT / "src" / "runtime" / "ts" / "generated" / "built_in" / "sequence.ts"
        self.assertTrue(generated_contains.exists())
        self.assertTrue(generated_sequence.exists())
        contains_text = generated_contains.read_text(encoding="utf-8")
        sequence_text = generated_sequence.read_text(encoding="utf-8")
        self.assertIn('require("../../native/built_in/py_runtime.js")', contains_text)
        self.assertIn(
            "module.exports = {py_contains_dict_object, py_contains_list_object, py_contains_set_object, py_contains_str_object};",
            contains_text,
        )
        self.assertIn("module.exports = {py_range, py_repeat};", sequence_text)
        self.assertNotIn("./pytra/py_runtime.js", contains_text)
        self.assertNotIn("./pytra/py_runtime.js", sequence_text)

    def test_ts_generated_std_baseline_source_guard_materializes_new_compare_modules(self) -> None:
        runtime_root = ROOT / "src" / "runtime" / "ts" / "generated"
        guarded_targets = {
            runtime_root / "std" / "argparse.ts": ("class Namespace", "class ArgumentParser"),
            runtime_root / "std" / "glob.ts": ("function glob(",),
            runtime_root / "std" / "os.ts": ("function getcwd(",),
            runtime_root / "std" / "os_path.ts": ("function basename(",),
            runtime_root / "std" / "random.ts": ("function randint(",),
            runtime_root / "std" / "re.ts": ("class Match", '"\\r"'),
            runtime_root / "std" / "sys.ts": ("function write_stderr(",),
            runtime_root / "std" / "timeit.ts": ("function default_timer(",),
            runtime_root / "utils" / "assertions.ts": ("function py_assert_true(",),
        }
        for path, needles in guarded_targets.items():
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                text = path.read_text(encoding="utf-8")
                self.assertIn("AUTO-GENERATED FILE. DO NOT EDIT.", text)
                for needle in needles:
                    self.assertIn(needle, text)

    def test_pathlib_runtime_symbol_uses_factory_and_property_access(self) -> None:
        fixture = find_fixture_case("math_path_runtime_ir")
        east = load_east(fixture, parser_backend="self_hosted")
        ts = transpile_to_typescript(east)
        self.assertIn('import { Path } from "./pytra/std/pathlib.js";', ts)
        self.assertIn('let p = Path("tmp/a.txt");', ts)
        self.assertIn("let q = p.parent;", ts)
        self.assertIn("let n = p.name;", ts)
        self.assertIn("let s = p.stem;", ts)

    def test_py2ts_does_not_import_src_common(self) -> None:
        src = (ROOT / "src" / "py2x.py").read_text(encoding="utf-8")
        self.assertNotIn("src.common", src)
        self.assertNotIn("from common.", src)

    def test_ts_preview_uses_js_transpile_pipeline(self) -> None:
        original = ts_emitter_mod.transpile_to_js
        try:
            ts_emitter_mod.transpile_to_js = (
                lambda _east_doc: "const __ts_js_pipeline_marker = 1;\n"
            )
            ts = ts_emitter_mod.transpile_to_typescript(
                {"kind": "Module", "body": [], "meta": {}}
            )
        finally:
            ts_emitter_mod.transpile_to_js = original
        self.assertIn("const __ts_js_pipeline_marker = 1;", ts)

    def test_ts_preview_keeps_isinstance_type_id_lowering(self) -> None:
        src = """class Base:
    def __init__(self):
        pass

def f(x: object) -> bool:
    return isinstance(x, int) or isinstance(x, Base)
"""
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "ts_isinstance_type_id.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            ts = transpile_to_typescript(east)

        self.assertIn("pyIsInstance(x, PY_TYPE_NUMBER)", ts)
        self.assertIn("pyIsInstance(x, Base.PYTRA_TYPE_ID)", ts)
        self.assertIn("static PYTRA_TYPE_ID = pyRegisterClassType([PY_TYPE_OBJECT]);", ts)

    def test_ts_preview_lowers_isinstance_tuple_to_or_checks(self) -> None:
        src = """class Base:
    def __init__(self):
        pass

def f(x: object) -> bool:
    return isinstance(x, (int, Base, dict, object))
"""
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "ts_isinstance_tuple_type_id.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            ts = transpile_to_typescript(east)

        self.assertIn("pyIsInstance(x, PY_TYPE_NUMBER)", ts)
        self.assertIn("pyIsInstance(x, Base.PYTRA_TYPE_ID)", ts)
        self.assertIn("pyIsInstance(x, PY_TYPE_MAP)", ts)
        self.assertIn("pyIsInstance(x, PY_TYPE_OBJECT)", ts)
        self.assertNotIn("isinstance(", ts)

    def test_ts_preview_lowers_isinstance_set_to_type_id_check(self) -> None:
        src = """def f(x: object) -> bool:
    return isinstance(x, set)
"""
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "ts_isinstance_set_type_id.py"
            src_py.write_text(src, encoding="utf-8")
            east = load_east(src_py, parser_backend="self_hosted")
            ts = transpile_to_typescript(east)

        self.assertIn("pyIsInstance(x, PY_TYPE_SET)", ts)
        self.assertNotIn("isinstance(", ts)

    def test_ts_preview_fail_closed_on_unresolved_stdlib_runtime_call(self) -> None:
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
            transpile_to_typescript(east)
        self.assertIn("unresolved stdlib runtime call", str(cm.exception))

    def test_ts_preview_for_core_static_range_inlines_start_when_safe(self) -> None:
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
        ts = transpile_to_typescript(east)
        self.assertIn("for (let i = 0; i < 3; i += 1)", ts)
        self.assertNotIn("const __start_", ts)

    def test_ts_preview_for_core_static_range_keeps_start_tmp_when_start_mentions_target(self) -> None:
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
        ts = transpile_to_typescript(east)
        self.assertIn("const __start_", ts)
        self.assertIn("for (let i = __start_", ts)

    def test_ts_preview_downcount_range_uses_descending_condition(self) -> None:
        fixture = find_fixture_case("range_downcount_len_minus1")
        east = load_east(fixture, parser_backend="self_hosted")
        ts = transpile_to_typescript(east)
        self.assertIn("for (let i = ", ts)
        self.assertIn("i > -1; i += -1)", ts)
        self.assertNotIn("__start_", ts)
        self.assertNotIn("i < -1; i += -1)", ts)

    def test_ts_preview_materializes_ref_container_args_to_value_path(self) -> None:
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
            ts = transpile_to_typescript(east)
        self.assertIn("let a = (Array.isArray(xs) ? xs.slice() : Array.from(xs));", ts)
        self.assertIn("let b = ((ys && typeof ys === \"object\") ? { ...ys } : {});", ts)


if __name__ == "__main__":
    unittest.main()
