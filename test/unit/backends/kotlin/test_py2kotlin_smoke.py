"""py2kotlin (EAST based) smoke tests."""

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

from backends.kotlin.emitter import load_kotlin_profile, transpile_to_kotlin, transpile_to_kotlin_native
from toolchain.compiler.transpile_cli import load_east3_document
from src.toolchain.ir.core_entrypoints import convert_path
from comment_fidelity import assert_no_generated_comments, assert_sample01_module_comments
from relative_import_jvm_package_smoke_support import (
    relative_import_jvm_package_expected_needles,
    transpile_relative_import_jvm_package_expect_failure,
    transpile_relative_import_jvm_package_project,
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
        target_lang="kotlin",
    )
    return doc3 if isinstance(doc3, dict) else {}


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


class Py2KotlinSmokeTest(unittest.TestCase):
    def test_load_kotlin_profile_contains_core_sections(self) -> None:
        profile = load_kotlin_profile()
        self.assertIn("types", profile)
        self.assertIn("operators", profile)
        self.assertIn("syntax", profile)
        self.assertIn("runtime_calls", profile)

    def test_bitwise_invert_basic_uses_kotlin_inv(self) -> None:
        fixture = find_fixture_case("bitwise_invert_basic")
        east = load_east(fixture, parser_backend="self_hosted")
        kotlin = transpile_to_kotlin_native(east)
        self.assertIn(".inv()", kotlin)

    def test_kotlin_native_emitter_skeleton_handles_module_function_class(self) -> None:
        fixture = find_fixture_case("inheritance")
        east = load_east(fixture, parser_backend="self_hosted")
        kotlin = transpile_to_kotlin_native(east)
        self.assertIn("fun main(args: Array<String>)", kotlin)
        self.assertIn("open class Animal", kotlin)
        self.assertIn("open class Dog() : Animal()", kotlin)
        self.assertIn("fun _case_main()", kotlin)

    def test_bitwise_invert_fixture_uses_kotlin_inv(self) -> None:
        fixture = find_fixture_case("bitwise_invert_basic")
        east = load_east(fixture, parser_backend="self_hosted")
        kotlin = transpile_to_kotlin_native(east)
        self.assertIn(".inv()", kotlin)

    def test_cli_relative_import_jvm_package_bundle_scenarios_transpile_for_kotlin(self) -> None:
        for scenario_id in ("parent_module_alias", "parent_symbol_alias"):
            with self.subTest(scenario_id=scenario_id):
                kotlin = transpile_relative_import_jvm_package_project(scenario_id, "kotlin")
                positive, forbidden = relative_import_jvm_package_expected_needles("kotlin", scenario_id)
                self.assertIn(positive, kotlin)
                self.assertNotIn(forbidden, kotlin)

    def test_cli_relative_import_jvm_package_bundle_fail_closed_for_wildcard_on_kotlin(self) -> None:
        err = transpile_relative_import_jvm_package_expect_failure(
            "kotlin",
            "from ..helper import *",
            "f()",
        )
        self.assertIn("unsupported relative import form: wildcard import", err)
        self.assertIn("kotlin native emitter", err)

    def test_kotlin_native_emitter_lowers_override_and_super_method_dispatch(self) -> None:
        fixture = find_fixture_case("inheritance_virtual_dispatch_multilang")
        east = load_east(fixture, parser_backend="self_hosted")
        kotlin = transpile_to_kotlin_native(east)
        self.assertIn("open fun speak()", kotlin)
        self.assertIn("override fun speak()", kotlin)
        self.assertIn('return __pytra_str("loud-" + super.speak())', kotlin)
        self.assertNotIn("super().speak()", kotlin)

    def test_secondary_bundle_representative_fixtures_transpile_for_kotlin(self) -> None:
        for stem in (
            "tuple_assign",
            "lambda_basic",
            "comprehension",
            "for_range",
            "try_raise",
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
                kotlin = transpile_to_kotlin_native(east)
                self.assertTrue(kotlin.strip())

    def test_tuple_assign_fixture_lowers_swap_via_temp_for_kotlin(self) -> None:
        fixture = find_fixture_case("tuple_assign")
        east = load_east(fixture, parser_backend="self_hosted")
        kotlin = transpile_to_kotlin_native(east)
        self.assertRegex(kotlin, r"var __swap_\d+: Long = x")
        self.assertIn("x = y", kotlin)
        self.assertRegex(kotlin, r"y = __swap_\d+")

    def test_module_leading_comments_are_emitted(self) -> None:
        sample = ROOT / "sample" / "py" / "01_mandelbrot.py"
        east = load_east(sample, parser_backend="self_hosted")
        kotlin = transpile_to_kotlin_native(east)
        assert_no_generated_comments(self, kotlin)
        assert_sample01_module_comments(self, kotlin, prefix="//")

    def test_sample_01_quality_fastpaths_reduce_redundant_wrappers(self) -> None:
        sample = ROOT / "sample" / "py" / "01_mandelbrot.py"
        east = load_east(sample, parser_backend="self_hosted")
        kotlin = transpile_to_kotlin_native(east)
        self.assertIn("__pytra_write_rgb_png(out_path, width, height, pixels)", kotlin)
        self.assertNotIn("__pytra_noop(out_path, width, height, pixels)", kotlin)
        self.assertNotIn("__pytra_float(__pytra_float(", kotlin)
        self.assertNotIn("__pytra_int(__pytra_int(", kotlin)
        self.assertIn("while (y < __pytra_int(height))", kotlin)
        self.assertIn("while (x < __pytra_int(width))", kotlin)
        self.assertIn("pixels.add(r)", kotlin)
        self.assertIn("pixels.add(g)", kotlin)
        self.assertIn("pixels.add(b)", kotlin)
        self.assertNotIn("pixels = __pytra_as_list(pixels); pixels.add", kotlin)

    def test_kotlin_native_emitter_routes_math_calls_via_runtime_helpers(self) -> None:
        sample = ROOT / "sample" / "py" / "06_julia_parameter_sweep.py"
        east = load_east(sample, parser_backend="self_hosted")
        kotlin = transpile_to_kotlin_native(east)
        self.assertIn("pyMathPi()", kotlin)
        self.assertIn("pyMathCos(__pytra_float(angle))", kotlin)
        self.assertIn("pyMathSin(__pytra_float(angle))", kotlin)

    def test_dict_get_with_default_uses_kotlin_elvis(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "dict_get_default.py"
            src.write_text(
                "def f(d, k):\n"
                "    return d.get(k, 0)\n",
                encoding="utf-8",
            )
            east = load_east(src, parser_backend="self_hosted")
            kotlin = transpile_to_kotlin_native(east)
        self.assertIn("?: 0L", kotlin)
        self.assertNotIn(".get(k, 0L)", kotlin)

    def test_kotlin_native_emitter_maps_json_calls_to_runtime_helpers(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "json_case.py"
            src.write_text(
                "import json\n"
                "def f(s: str) -> str:\n"
                "    obj = json.loads(s)\n"
                "    return json.dumps(obj)\n",
                encoding="utf-8",
            )
            east = load_east(src, parser_backend="self_hosted")
            kotlin = transpile_to_kotlin_native(east)
        self.assertIn("var obj: Any? = pyJsonLoads(s)", kotlin)
        self.assertIn("return __pytra_str(pyJsonDumps(obj))", kotlin)
        self.assertNotIn("json.loads(", kotlin)
        self.assertNotIn("json.dumps(", kotlin)

    def test_kotlin_emitter_source_has_no_owner_math_special_case(self) -> None:
        src = (ROOT / "src" / "backends" / "kotlin" / "emitter" / "kotlin_native_emitter.py").read_text(encoding="utf-8")
        self.assertNotIn('owner == "math"', src)
        self.assertNotIn("owner == 'math'", src)
        self.assertNotIn('runtime_symbol.startswith("pyMath")', src)
        self.assertNotIn("runtime_symbol.startswith('pyMath')", src)
        self.assertNotIn('runtime_symbol == "pyMathPi"', src)
        self.assertNotIn('runtime_symbol == "pyMathE"', src)
        self.assertNotIn('resolved_runtime.endswith(".pi")', src)
        self.assertNotIn('resolved_runtime.endswith(".e")', src)
        banned_runtime_literals = [
            "write_rgb_png",
            "save_gif",
            "grayscale_palette",
            "perf_counter",
            "json.loads",
            "json.dumps",
            "Path",
        ]
        for symbol in banned_runtime_literals:
            self.assertNotIn(f'runtime_call == "{symbol}"', src)
            self.assertNotIn(f"runtime_call == '{symbol}'", src)

    def test_kotlin_native_emitter_uses_runtime_path_class(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "path_case.py"
            src.write_text(
                "from pathlib import Path\n"
                "def f() -> bool:\n"
                "    p = Path('tmp/a.txt')\n"
                "    p.parent.mkdir(parents=True, exist_ok=True)\n"
                "    return p.exists()\n",
                encoding="utf-8",
            )
            east = load_east(src, parser_backend="self_hosted")
            kotlin = transpile_to_kotlin_native(east)
        self.assertIn("var p: Path = Path(\"tmp/a.txt\")", kotlin)
        self.assertIn("p.parent.mkdir(true, true)", kotlin)
        self.assertIn("return p.exists()", kotlin)

    def test_kotlin_native_emitter_backend_only_ir_fixture_resolves_math_and_path(self) -> None:
        fixture = ROOT / "test" / "ir" / "java_math_path_runtime.east3.json"
        east = load_east(fixture, parser_backend="self_hosted")
        kotlin = transpile_to_kotlin_native(east)
        self.assertIn("var p: Path = Path(\"tmp/a.txt\")", kotlin)
        self.assertIn("var q: Path = p.parent", kotlin)
        self.assertIn("var n: String = __pytra_str(p.name)", kotlin)
        self.assertIn("var s: String = __pytra_str(p.stem)", kotlin)
        self.assertIn("var x: Double = pyMathSin(__pytra_float(pyMathPi()))", kotlin)

    def test_kotlin_native_emitter_fail_closed_on_unresolved_stdlib_runtime_call(self) -> None:
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
            transpile_to_kotlin_native(east)
        self.assertIn("unresolved stdlib runtime", str(cm.exception))

    def test_kotlin_native_emitter_fail_closed_on_unresolved_resolved_runtime_call(self) -> None:
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
            transpile_to_kotlin_native(east)
        self.assertIn("unresolved stdlib runtime", str(cm.exception))

    def test_dict_literal_entries_are_materialized(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "dict_literal_entries.py"
            src.write_text(
                "def f():\n"
                "    d = {'=': 7}\n"
                "    return d.get('=', 0)\n",
                encoding="utf-8",
            )
            east = load_east(src, parser_backend="self_hosted")
            kotlin = transpile_to_kotlin_native(east)
        self.assertIn('Pair("=", 7L)', kotlin)
        self.assertIn('(d.get("=") ?: 0L)', kotlin)

    def test_ref_container_args_materialize_value_path_with_mutable_copy(self) -> None:
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
            kotlin = transpile_to_kotlin_native(east)
        self.assertIn("var a: MutableList<Any?> = __pytra_as_list(xs).toMutableList()", kotlin)
        self.assertIn("var b: MutableMap<Any, Any?> = __pytra_as_dict(ys).toMutableMap()", kotlin)
        self.assertNotIn("var a: MutableList<Any?> = xs", kotlin)
        self.assertNotIn("var b: MutableMap<Any, Any?> = ys", kotlin)
        self.assertIn("a.add(1L)", kotlin)

    def test_py2kotlin_does_not_import_src_common(self) -> None:
        src = (ROOT / "src" / "py2x.py").read_text(encoding="utf-8")
        self.assertNotIn("src.common", src)
        self.assertNotIn("from common.", src)

    def test_kotlin_runtime_source_path_is_migrated(self) -> None:
        runtime_path = ROOT / "src" / "runtime" / "kotlin" / "native" / "built_in" / "py_runtime.kt"
        generated_root = ROOT / "src" / "runtime" / "kotlin" / "generated"
        legacy_path = ROOT / "src" / "kotlin_module" / "py_runtime.kt"
        self.assertTrue(runtime_path.exists())
        for rel_path in (
            "built_in/contains.kt",
            "built_in/io_ops.kt",
            "built_in/iter_ops.kt",
            "built_in/numeric_ops.kt",
            "built_in/predicates.kt",
            "built_in/scalar_ops.kt",
            "built_in/sequence.kt",
            "built_in/string_ops.kt",
            "built_in/type_id.kt",
            "built_in/zip_ops.kt",
            "std/argparse.kt",
            "std/glob.kt",
            "std/json.kt",
            "std/math.kt",
            "std/os.kt",
            "std/os_path.kt",
            "std/pathlib.kt",
            "std/random.kt",
            "std/re.kt",
            "std/sys.kt",
            "std/time.kt",
            "std/timeit.kt",
            "utils/assertions.kt",
            "utils/gif.kt",
            "utils/image_runtime.kt",
            "utils/png.kt",
        ):
            self.assertTrue((generated_root / rel_path).exists(), msg=rel_path)
        self.assertFalse(legacy_path.exists())

    def test_kotlin_generated_built_in_compare_lane_compiles_with_runtime_bundle(self) -> None:
        runtime_path = ROOT / "src" / "runtime" / "kotlin" / "native" / "built_in" / "py_runtime.kt"
        contains_path = ROOT / "src" / "runtime" / "kotlin" / "generated" / "built_in" / "contains.kt"
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            (tmp / "py_runtime.kt").write_text(runtime_path.read_text(encoding="utf-8"), encoding="utf-8")
            (tmp / "contains.kt").write_text(contains_path.read_text(encoding="utf-8"), encoding="utf-8")
            (tmp / "Main.kt").write_text(
                "\n".join(
                    [
                        "fun main() {",
                        '    println(if (py_contains_str_object("abc", "b")) "kotlin-built-in-ok" else "kotlin-built-in-bad")',
                        "}",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            compile_proc = subprocess.run(
                [
                    "kotlinc",
                    str(tmp / "py_runtime.kt"),
                    str(tmp / "contains.kt"),
                    str(tmp / "Main.kt"),
                    "-include-runtime",
                    "-d",
                    str(tmp / "built_in.jar"),
                ],
                cwd=tmp,
                text=True,
                capture_output=True,
            )
            self.assertEqual(compile_proc.returncode, 0, compile_proc.stderr)
            run_proc = subprocess.run(
                ["java", "-jar", str(tmp / "built_in.jar")],
                cwd=tmp,
                text=True,
                capture_output=True,
            )
            self.assertEqual(run_proc.returncode, 0, run_proc.stderr)
            self.assertEqual(run_proc.stdout.strip(), "kotlin-built-in-ok")

    def test_representative_property_method_call_fixture_transpiles(self) -> None:
        try:
            from test.unit.backends.representative_contract_support import (
                assert_no_representative_escape,
            )
        except ModuleNotFoundError:
            from representative_contract_support import assert_no_representative_escape

        fixture = find_fixture_case("property_method_call")
        east = load_east(fixture, parser_backend="self_hosted")
        kotlin = transpile_to_kotlin_native(east)
        assert_no_representative_escape(self, kotlin, backend="kotlin", fixture="property_method_call")

    def test_representative_list_bool_index_fixture_transpiles(self) -> None:
        try:
            from test.unit.backends.representative_contract_support import (
                assert_no_representative_escape,
            )
        except ModuleNotFoundError:
            from representative_contract_support import assert_no_representative_escape

        fixture = find_fixture_case("list_bool_index")
        east = load_east(fixture, parser_backend="self_hosted")
        kotlin = transpile_to_kotlin_native(east)
        assert_no_representative_escape(self, kotlin, backend="kotlin", fixture="list_bool_index")


if __name__ == "__main__":
    unittest.main()
