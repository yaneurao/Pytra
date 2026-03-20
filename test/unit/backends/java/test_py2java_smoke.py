"""py2java (EAST based) smoke tests."""

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

from toolchain.emit.java.emitter import load_java_profile, transpile_to_java
from toolchain.compiler.transpile_cli import load_east3_document
from toolchain.emit.java.emitter.java_native_emitter import (
    _java_string_literal,
    _render_expr,
    transpile_to_java_native,
)
from src.toolchain.compile.core_entrypoints import convert_path
from comment_fidelity import assert_no_generated_comments, assert_sample01_module_comments
from relative_import_jvm_package_smoke_support import (
    relative_import_jvm_package_expected_needles,
    transpile_relative_import_jvm_package_expect_failure,
    transpile_relative_import_jvm_package_project,
    transpile_relative_import_jvm_package_via_module_graph,
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
        target_lang="java",
    )
    return doc3 if isinstance(doc3, dict) else {}


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


class Py2JavaSmokeTest(unittest.TestCase):
    def test_load_java_profile_contains_core_sections(self) -> None:
        profile = load_java_profile()
        self.assertIn("types", profile)
        self.assertIn("operators", profile)
        self.assertIn("syntax", profile)
        self.assertIn("runtime_calls", profile)

    def test_bitwise_invert_basic_uses_java_invert_operator(self) -> None:
        fixture = find_fixture_case("bitwise_invert_basic")
        east = load_east(fixture, parser_backend="self_hosted")
        java = transpile_to_java_native(east, class_name="Main")
        self.assertIn("~(y)", java)

    def test_java_native_emitter_skeleton_handles_module_function_class(self) -> None:
        fixture = find_fixture_case("inheritance")
        east = load_east(fixture, parser_backend="self_hosted")
        java = transpile_to_java_native(east, class_name="Main")
        self.assertIn("public final class Main", java)
        self.assertIn("public static class Animal", java)
        self.assertIn("public static class Dog extends Animal", java)
        self.assertIn('return this.sound() + "-bark";', java)
        self.assertIn("public static void _case_main()", java)
        self.assertIn("Dog d = new Dog();", java)
        self.assertIn('System.out.println("True");', java)

    def test_bitwise_invert_fixture_uses_java_bitwise_not(self) -> None:
        fixture = find_fixture_case("bitwise_invert_basic")
        east = load_east(fixture, parser_backend="self_hosted")
        java = transpile_to_java_native(east, class_name="Main")
        self.assertIn("~(y)", java)

    def test_cli_relative_import_jvm_package_bundle_scenarios_transpile_for_java(self) -> None:
        for scenario_id in ("parent_module_alias", "parent_symbol_alias"):
            with self.subTest(scenario_id=scenario_id):
                java = transpile_relative_import_jvm_package_project(scenario_id, "java")
                positive, forbidden = relative_import_jvm_package_expected_needles("java", scenario_id)
                self.assertIn(positive, java)
                self.assertNotIn(forbidden, java)

    def test_cli_relative_import_jvm_package_bundle_wildcard_via_module_graph_for_java(self) -> None:
        java = transpile_relative_import_jvm_package_via_module_graph(
            target="java",
            import_form="from ..helper import *",
            body_text="def call() -> int:\n    return f()\n",
        )
        positive, forbidden = relative_import_jvm_package_expected_needles(
            "java",
            "parent_symbol_wildcard",
        )
        self.assertIn(positive, java)
        self.assertNotIn(forbidden, java)

    def test_cli_relative_import_jvm_package_bundle_direct_fail_closed_for_wildcard_on_java(self) -> None:
        err = transpile_relative_import_jvm_package_expect_failure(
            "java",
            "from ..helper import *",
            "f()",
        )
        self.assertIn("unsupported relative import form: wildcard import", err)
        self.assertIn("java native emitter", err)

    def test_java_native_emitter_lowers_super_method_call_without_super_constructor_syntax(self) -> None:
        fixture = find_fixture_case("inheritance_virtual_dispatch_multilang")
        east = load_east(fixture, parser_backend="self_hosted")
        java = transpile_to_java_native(east, class_name="Main")
        self.assertIn('return "loud-" + super.speak();', java)
        self.assertNotIn("super().speak()", java)

    def test_secondary_bundle_representative_fixtures_transpile_for_java(self) -> None:
        for stem in (
            "tuple_assign",
            "lambda_basic",
            "comprehension",
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
                java = transpile_to_java_native(east, class_name="Main")
                self.assertTrue(java.strip())

    def test_tuple_assign_fixture_lowers_swap_via_temp_for_java(self) -> None:
        fixture = find_fixture_case("tuple_assign")
        east = load_east(fixture, parser_backend="self_hosted")
        java = transpile_to_java_native(east, class_name="Main")
        self.assertRegex(java, r"long __swap_\d+ = x;")
        self.assertIn("x = y;", java)
        self.assertRegex(java, r"y = __swap_\d+;")

    def test_java_string_literal_escapes_control_characters(self) -> None:
        rendered = _java_string_literal("\\\"\r\n\t\b\f")
        self.assertEqual(rendered, '"\\\\\\\"\\r\\n\\t\\b\\f"')

    def test_java_native_emitter_skeleton_maps_simple_int_signature(self) -> None:
        fixture = find_fixture_case("add")
        east = load_east(fixture, parser_backend="self_hosted")
        java = transpile_to_java_native(east, class_name="Main")
        self.assertIn("public static long add(long a, long b)", java)
        self.assertIn("return a + b;", java)
        self.assertIn('System.out.println("True");', java)

    def test_module_leading_comments_are_emitted(self) -> None:
        sample = ROOT / "sample" / "py" / "01_mandelbrot.py"
        east = load_east(sample, parser_backend="self_hosted")
        java = transpile_to_java_native(east, class_name="Main")
        assert_no_generated_comments(self, java)
        assert_sample01_module_comments(self, java, prefix="//")

    def test_java_native_emitter_lowers_if_and_forcore(self) -> None:
        if_fixture = find_fixture_case("if_else")
        if_east = load_east(if_fixture, parser_backend="self_hosted")
        if_java = transpile_to_java_native(if_east, class_name="Main")
        self.assertIn("public static long abs_like(long n) {", if_java)
        self.assertIn("if (((n) < (0L))) {", if_java)
        self.assertIn("return (-(n));", if_java)
        self.assertIn("return n;", if_java)

        for_fixture = find_fixture_case("for_range")
        for_east = load_east(for_fixture, parser_backend="self_hosted")
        for_java = transpile_to_java_native(for_east, class_name="Main")
        self.assertIn("for (long i = 0L;", for_java)
        self.assertIn("total += i;", for_java)

    def test_java_native_emitter_omits_step_tmp_for_constant_range_steps(self) -> None:
        for_fixture = find_fixture_case("for_range")
        for_east = load_east(for_fixture, parser_backend="self_hosted")
        for_java = transpile_to_java_native(for_east, class_name="Main")
        self.assertNotIn("__step_", for_java)
        self.assertIn("for (long i = 0L; i < n; i += 1L)", for_java)

        down_fixture = find_fixture_case("range_downcount_len_minus1")
        down_east = load_east(down_fixture, parser_backend="self_hosted")
        down_java = transpile_to_java_native(down_east, class_name="Main")
        self.assertNotIn("__step_", down_java)
        self.assertIn("for (long i = ((long)(xs.size())) - 1L; i > (-(1L)); i -= 1L)", down_java)

    def test_java_native_emitter_uses_main_guard_body_for_sample_entry(self) -> None:
        sample = ROOT / "sample" / "py" / "17_monte_carlo_pi.py"
        east = load_east(sample, parser_backend="self_hosted")
        java = transpile_to_java_native(east, class_name="Main")
        self.assertIn("run_integer_benchmark();", java)

    def test_java_native_emitter_handles_bytearray_cast_and_runtime_noop(self) -> None:
        sample = ROOT / "sample" / "py" / "03_julia_set.py"
        east = load_east(sample, parser_backend="self_hosted")
        java = transpile_to_java_native(east, class_name="Main")
        self.assertIn("java.util.ArrayList<Long> pixels = new java.util.ArrayList<Long>();", java)
        self.assertIn("pixels.add(r);", java)
        self.assertIn("r = PyRuntime.__pytra_int(", java)
        self.assertIn("png.write_rgb_png(out_path, width, height, pixels);", java)
        self.assertNotIn("PyRuntime.write_rgb_png(", java)

    def test_java_native_emitter_allocates_sized_bytearray_for_subscript_set(self) -> None:
        sample = ROOT / "sample" / "py" / "05_mandelbrot_zoom.py"
        east = load_east(sample, parser_backend="self_hosted")
        java = transpile_to_java_native(east, class_name="Main")
        self.assertIn("PyRuntime.__pytra_bytearray(width * height)", java)
        self.assertIn("frame.set((int)(", java)

    def test_java_native_emitter_routes_math_calls_without_java_emitter_special_case(self) -> None:
        sample = ROOT / "sample" / "py" / "06_julia_parameter_sweep.py"
        east = load_east(sample, parser_backend="self_hosted")
        java = transpile_to_java_native(east, class_name="Main")
        self.assertIn("double angle = 2.0 * math.pi * t;", java)
        self.assertIn("math.cos(angle)", java)
        self.assertIn("math.sin(angle)", java)

    def test_java_native_emitter_maps_json_calls_to_runtime_helpers(self) -> None:
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
            java = transpile_to_java_native(east, class_name="Main")
        self.assertIn("Object obj = json.loads(s);", java)
        self.assertIn("return json.dumps(obj);", java)
        self.assertNotIn("PyRuntime.pyJsonLoads(", java)
        self.assertNotIn("PyRuntime.pyJsonDumps(", java)

    def test_java_native_emitter_uses_runtime_path_class(self) -> None:
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
            java = transpile_to_java_native(east, class_name="Main")
        self.assertIn("pathlib.Path p = new pathlib.Path(\"tmp/a.txt\");", java)
        self.assertIn("p.parent().mkdir(true, true);", java)
        self.assertIn("return p.exists();", java)

    def test_java_native_emitter_renders_path_properties_from_ir_runtime_attr(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "path_props.py"
            src.write_text(
                "from pathlib import Path\n"
                "def f() -> None:\n"
                "    p = Path('tmp/a.txt')\n"
                "    n = p.name\n"
                "    s = p.stem\n"
                "    q = p.parent\n"
                "    print(n, s, q)\n",
                encoding="utf-8",
            )
            east = load_east(src, parser_backend="self_hosted")
            java = transpile_to_java_native(east, class_name="Main")
        self.assertIn("p.name()", java)
        self.assertIn("p.stem()", java)
        self.assertIn("p.parent()", java)

    def test_java_native_emitter_backend_only_ir_fixture_resolves_math_and_path(self) -> None:
        fixture = ROOT / "test" / "ir" / "java_math_path_runtime.east3.json"
        east = load_east(fixture, parser_backend="self_hosted")
        java = transpile_to_java_native(east, class_name="Main")
        self.assertIn("pathlib.Path p = new pathlib.Path(\"tmp/a.txt\");", java)
        self.assertIn("pathlib.Path q = p.parent();", java)
        self.assertIn("String n = p.name();", java)
        self.assertIn("String s = p.stem();", java)
        self.assertIn("double x = math.sin(math.pi);", java)
        self.assertNotIn("_m.sin(", java)
        self.assertNotIn("_m.pi", java)

    def test_java_native_emitter_routes_perf_counter_via_runtime_helper(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "perf_case.py"
            src.write_text(
                "from time import perf_counter\n"
                "def f() -> float:\n"
                "    return perf_counter()\n",
                encoding="utf-8",
            )
            east = load_east(src, parser_backend="self_hosted")
            java = transpile_to_java_native(east, class_name="Main")
        self.assertIn("return _impl.perf_counter();", java)
        self.assertNotIn("System.nanoTime()", java)

    def test_java_binop_minimal_parentheses_and_rhs_grouping(self) -> None:
        simple_expr = {
            "kind": "BinOp",
            "op": "Mult",
            "left": {"kind": "Name", "id": "x"},
            "right": {"kind": "Name", "id": "y"},
        }
        self.assertEqual(_render_expr(simple_expr), "x * y")

        grouped_rhs = {
            "kind": "BinOp",
            "op": "Sub",
            "left": {"kind": "Name", "id": "a"},
            "right": {
                "kind": "BinOp",
                "op": "Sub",
                "left": {"kind": "Name", "id": "b"},
                "right": {"kind": "Name", "id": "c"},
            },
        }
        self.assertEqual(_render_expr(grouped_rhs), "a - (b - c)")

    def test_java_native_emitter_lowers_listcomp_and_repeat_list_init(self) -> None:
        sample = ROOT / "sample" / "py" / "07_game_of_life_loop.py"
        east = load_east(sample, parser_backend="self_hosted")
        java = transpile_to_java_native(east, class_name="Main")
        self.assertIn("grid = new java.util.ArrayList<", java)
        self.assertIn("grid.add(PyRuntime.__pytra_list_repeat(0L, w));", java)

    def test_java_native_emitter_maps_min_max_and_list_truthy(self) -> None:
        sample = ROOT / "sample" / "py" / "14_raymarching_light_cycle.py"
        east = load_east(sample, parser_backend="self_hosted")
        java = transpile_to_java_native(east, class_name="Main")
        self.assertIn("Math.max(", java)
        self.assertIn("Math.min(", java)

        sample2 = ROOT / "sample" / "py" / "13_maze_generation_steps.py"
        east2 = load_east(sample2, parser_backend="self_hosted")
        java2 = transpile_to_java_native(east2, class_name="Main")
        self.assertIn("while (((stack) != null && !(stack).isEmpty()))", java2)

    def test_java_native_emitter_lowers_tuple_subscript_swap_assignment(self) -> None:
        sample = ROOT / "sample" / "py" / "12_sort_visualizer.py"
        east = load_east(sample, parser_backend="self_hosted")
        java = transpile_to_java_native(east, class_name="Main")
        self.assertGreaterEqual(java.count("values.set((int)("), 2)
        self.assertIn("__tuple_", java)

    def test_java_native_emitter_lowers_len_and_subscript_set(self) -> None:
        sample = ROOT / "sample" / "py" / "07_game_of_life_loop.py"
        east = load_east(sample, parser_backend="self_hosted")
        java = transpile_to_java_native(east, class_name="Main")
        self.assertIn(".size()", java)
        self.assertIn(".set((int)(", java)

    def test_java_native_emitter_rejects_non_module_root(self) -> None:
        with self.assertRaises(RuntimeError):
            transpile_to_java_native({"kind": "FunctionDef"}, class_name="Main")

    def test_py2java_does_not_import_src_common(self) -> None:
        src = (ROOT / "src" / "py2x.py").read_text(encoding="utf-8")
        self.assertNotIn("src.common", src)
        self.assertNotIn("from common.", src)

    def test_java_runtime_source_path_is_migrated(self) -> None:
        delete_target_runtime = ROOT / "src" / "runtime" / "java" / "pytra" / "built_in" / "PyRuntime.java"
        runtime_path = ROOT / "src" / "runtime" / "java" / "native" / "built_in" / "PyRuntime.java"
        native_math_path = ROOT / "src" / "runtime" / "java" / "native" / "std" / "math_native.java"
        native_time_path = ROOT / "src" / "runtime" / "java" / "native" / "std" / "time_native.java"
        generated_root = ROOT / "src" / "runtime" / "java" / "generated"
        legacy_path = ROOT / "src" / "java_module" / "PyRuntime.java"
        self.assertFalse(delete_target_runtime.exists())
        self.assertTrue(runtime_path.exists())
        self.assertTrue(native_math_path.exists())
        self.assertTrue(native_time_path.exists())
        for rel_path in (
            "built_in/contains.java",
            "built_in/predicates.java",
            "built_in/sequence.java",
            "built_in/string_ops.java",
            "built_in/type_id.java",
            "built_in/zip_ops.java",
            "std/argparse.java",
            "std/glob.java",
            "std/json.java",
            "std/math.java",
            "std/os.java",
            "std/os_path.java",
            "std/pathlib.java",
            "std/random.java",
            "std/re.java",
            "std/sys.java",
            "std/time.java",
            "std/timeit.java",
            "utils/assertions.java",
            "utils/gif.java",
            "utils/png.java",
        ):
            self.assertTrue((generated_root / rel_path).exists(), msg=rel_path)
        self.assertFalse(legacy_path.exists())
        generated_time = (generated_root / "std" / "time.java").read_text(encoding="utf-8")
        native_time = native_time_path.read_text(encoding="utf-8")
        self.assertIn("return time_native.perf_counter();", generated_time)
        self.assertNotIn("System.nanoTime()", generated_time)
        self.assertIn("System.nanoTime()", native_time)

    def test_java_generated_math_runtime_owner_is_live_wrapper_shaped(self) -> None:
        generated_root = ROOT / "src" / "runtime" / "java" / "generated"
        native_path = ROOT / "src" / "runtime" / "java" / "native" / "std" / "math_native.java"
        generated = (generated_root / "std" / "math.java").read_text(encoding="utf-8")
        native = native_path.read_text(encoding="utf-8")
        self.assertIn("public static double pi = math_native.pi;", generated)
        self.assertIn("public static double e = math_native.e;", generated)
        self.assertIn("return math_native.sqrt(x);", generated)
        self.assertIn("return math_native.pow(x, y);", generated)
        self.assertNotIn("Math.PI", generated)
        self.assertNotIn("Math.sqrt", generated)
        self.assertIn("public static double pi = Math.PI;", native)
        self.assertIn("public static double e = Math.E;", native)
        self.assertIn("return Math.sqrt(x);", native)
        self.assertIn("return Math.pow(x, y);", native)

    def test_java_generated_built_in_compare_lane_compiles_with_runtime_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            files = (
                ROOT / "src" / "runtime" / "java" / "native" / "built_in" / "PyRuntime.java",
                ROOT / "src" / "runtime" / "java" / "generated" / "built_in" / "contains.java",
            )
            for src in files:
                (tmp / src.name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            main_java = tmp / "Main.java"
            main_java.write_text(
                "\n".join(
                    [
                        "public final class Main {",
                        "    public static void main(String[] args) {",
                        '        if (!contains.py_contains_str_object("abc", "b")) {',
                        '            throw new RuntimeException("contains");',
                        "        }",
                        '        System.out.println("java-built-in-ok");',
                        "    }",
                        "}",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            proc = subprocess.run(
                ["bash", "-lc", "javac PyRuntime.java contains.java Main.java && java Main"],
                cwd=tmp,
                capture_output=True,
                text=True,
            )
        self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
        self.assertIn("java-built-in-ok", proc.stdout)

    def test_java_native_emitter_has_no_direct_runtime_call_branches_for_json_png_gif(self) -> None:
        src_path = ROOT / "src" / "backends" / "java" / "emitter" / "java_native_emitter.py"
        src = src_path.read_text(encoding="utf-8")
        forbidden = [
            'runtime_call == "perf_counter"',
            'runtime_call == "json.loads"',
            'runtime_call == "json.dumps"',
            'runtime_call == "write_rgb_png"',
            'runtime_call == "save_gif"',
            'runtime_call == "grayscale_palette"',
            'runtime_call.startswith("py_assert_")',
            'callee_name.startswith("py_assert_")',
            'owner_type == "Path"',
            "owner_type == 'Path'",
            'owner == "math"',
            "owner == 'math'",
            "_java_math_runtime_call(",
            'binding_module.startswith("pytra.utils.")',
            "binding_module.startswith('pytra.utils.')",
            'attr in {"parent", "name", "stem"}',
            "attr in {'parent', 'name', 'stem'}",
            "_render_call_via_runtime_call(expr,",
            "_render_resolved_runtime_call(expr,",
            "_call_name(expr).strip()",
        ]
        for marker in forbidden:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, src)
        self.assertNotIn("py_assert_", src)
        self.assertNotIn('"perf_counter"', src)
        self.assertNotIn("_RESOLVED_RUNTIME_HELPERS", src)

    def test_representative_property_method_call_fixture_transpiles(self) -> None:
        try:
            from test.unit.backends.representative_contract_support import (
                assert_no_representative_escape,
            )
        except ModuleNotFoundError:
            from representative_contract_support import assert_no_representative_escape

        fixture = find_fixture_case("property_method_call")
        east = load_east(fixture, parser_backend="self_hosted")
        java = transpile_to_java_native(east, class_name="Main")
        assert_no_representative_escape(self, java, backend="java", fixture="property_method_call")

    def test_representative_list_bool_index_fixture_transpiles(self) -> None:
        try:
            from test.unit.backends.representative_contract_support import (
                assert_no_representative_escape,
            )
        except ModuleNotFoundError:
            from representative_contract_support import assert_no_representative_escape

        fixture = find_fixture_case("list_bool_index")
        east = load_east(fixture, parser_backend="self_hosted")
        java = transpile_to_java_native(east, class_name="Main")
        assert_no_representative_escape(self, java, backend="java", fixture="list_bool_index")


if __name__ == "__main__":
    unittest.main()
