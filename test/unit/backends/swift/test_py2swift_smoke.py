"""py2swift (EAST based) smoke tests."""

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

from backends.swift.emitter import load_swift_profile, transpile_to_swift, transpile_to_swift_native
from toolchain.compiler.transpile_cli import load_east3_document
from src.toolchain.ir.core_entrypoints import convert_path
from comment_fidelity import assert_no_generated_comments, assert_sample01_module_comments
from relative_import_native_path_smoke_support import (
    relative_import_native_path_expected_rewrite,
    relative_import_native_path_scenarios,
    write_relative_import_native_path_project,
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
        target_lang="swift",
    )
    return doc3 if isinstance(doc3, dict) else {}


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


class Py2SwiftSmokeTest(unittest.TestCase):
    def test_load_swift_profile_contains_core_sections(self) -> None:
        profile = load_swift_profile()
        self.assertIn("types", profile)
        self.assertIn("operators", profile)
        self.assertIn("syntax", profile)
        self.assertIn("runtime_calls", profile)

    def test_bitwise_invert_basic_uses_swift_invert_operator(self) -> None:
        fixture = find_fixture_case("bitwise_invert_basic")
        east = load_east(fixture, parser_backend="self_hosted")
        swift = transpile_to_swift_native(east)
        self.assertIn("~y", swift)

    def test_swift_native_emitter_skeleton_handles_module_function_class(self) -> None:
        fixture = find_fixture_case("inheritance")
        east = load_east(fixture, parser_backend="self_hosted")
        swift = transpile_to_swift_native(east)
        self.assertIn("@main", swift)
        self.assertIn("class Animal", swift)
        self.assertIn("class Dog: Animal", swift)
        self.assertIn("func _case_main()", swift)

    def test_bitwise_invert_fixture_uses_swift_bitwise_not(self) -> None:
        fixture = find_fixture_case("bitwise_invert_basic")
        east = load_east(fixture, parser_backend="self_hosted")
        swift = transpile_to_swift_native(east)
        self.assertIn("~y", swift)

    def test_cli_relative_import_native_path_bundle_scenarios_transpile_for_swift(self) -> None:
        for scenario_id in ("parent_module_alias", "parent_symbol_alias"):
            with self.subTest(scenario_id=scenario_id):
                scenario = relative_import_native_path_scenarios()[scenario_id]
                with tempfile.TemporaryDirectory() as td:
                    entry_path = write_relative_import_native_path_project(
                        Path(td),
                        import_form=str(scenario["import_form"]),
                        body_text=(
                            "def call() -> int:\n"
                            f"    return {scenario['representative_expr']}\n"
                        ),
                    )
                    east = load_east(entry_path, parser_backend="self_hosted")
                    swift = transpile_to_swift_native(east)
                positive, forbidden = relative_import_native_path_expected_rewrite(scenario_id)
                self.assertIn(positive, swift)
                self.assertNotIn(forbidden, swift)

    def test_cli_relative_import_native_path_bundle_fail_closed_for_wildcard_on_swift(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            entry_path = write_relative_import_native_path_project(
                Path(td),
                import_form="from ..helper import *",
                body_text="def call() -> int:\n    return f()\n",
            )
            east = load_east(entry_path, parser_backend="self_hosted")
            with self.assertRaises(RuntimeError) as cm:
                transpile_to_swift_native(east)
        self.assertIn("unsupported relative import form: wildcard import", str(cm.exception))
        self.assertIn("swift native emitter", str(cm.exception))

    def test_swift_native_emitter_lowers_override_and_super_method_dispatch(self) -> None:
        fixture = find_fixture_case("inheritance_virtual_dispatch_multilang")
        east = load_east(fixture, parser_backend="self_hosted")
        swift = transpile_to_swift_native(east)
        self.assertIn("override func speak() -> String {", swift)
        self.assertIn('return __pytra_str("loud-" + super.speak())', swift)
        self.assertNotIn("super().speak()", swift)

    def test_secondary_bundle_representative_fixtures_transpile_for_swift(self) -> None:
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
                swift = transpile_to_swift_native(east)
                self.assertTrue(swift.strip())

    def test_tuple_assign_fixture_lowers_swap_via_temp_for_swift(self) -> None:
        fixture = find_fixture_case("tuple_assign")
        east = load_east(fixture, parser_backend="self_hosted")
        swift = transpile_to_swift_native(east)
        self.assertIn("var __swap_", swift)
        self.assertIn("x = y", swift)
        self.assertRegex(swift, r"y = __swap_\d+")

    def test_module_leading_comments_are_emitted(self) -> None:
        sample = ROOT / "sample" / "py" / "01_mandelbrot.py"
        east = load_east(sample, parser_backend="self_hosted")
        swift = transpile_to_swift_native(east)
        assert_no_generated_comments(self, swift)
        assert_sample01_module_comments(self, swift, prefix="//")

    def test_sample_01_quality_fastpaths_reduce_redundant_wrappers(self) -> None:
        sample = ROOT / "sample" / "py" / "01_mandelbrot.py"
        east = load_east(sample, parser_backend="self_hosted")
        swift = transpile_to_swift_native(east)
        self.assertIn("__pytra_write_rgb_png(out_path, width, height, pixels)", swift)
        self.assertNotIn("__pytra_noop(out_path, width, height, pixels)", swift)
        self.assertNotIn("__pytra_float(__pytra_float(", swift)
        self.assertNotIn("__pytra_int(__pytra_int(", swift)
        self.assertIn("while (y < __pytra_int(height)) {", swift)
        self.assertIn("while (x < __pytra_int(width)) {", swift)
        self.assertIn("pixels.append(r)", swift)
        self.assertIn("pixels.append(g)", swift)
        self.assertIn("pixels.append(b)", swift)
        self.assertNotIn("pixels = __pytra_as_list(pixels); pixels.append", swift)

    def test_swift_native_emitter_routes_math_calls_via_runtime_helpers(self) -> None:
        sample = ROOT / "sample" / "py" / "06_julia_parameter_sweep.py"
        east = load_east(sample, parser_backend="self_hosted")
        swift = transpile_to_swift_native(east)
        self.assertIn("pyMathPi()", swift)
        self.assertIn("pyMathCos(__pytra_float(angle))", swift)
        self.assertIn("pyMathSin(__pytra_float(angle))", swift)

    def test_swift_emitter_source_has_no_owner_math_special_case(self) -> None:
        src = (ROOT / "src" / "backends" / "swift" / "emitter" / "swift_native_emitter.py").read_text(encoding="utf-8")
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

    def test_ref_container_args_materialize_value_path_with_copy_expr(self) -> None:
        src = """
def f(xs: list[int], ys: dict[str, int]) -> int:
    a: list[int] = xs
    b: dict[str, int] = ys
    a.append(1)
    b["k"] = 2
    return len(a) + len(b)
"""
        with tempfile.TemporaryDirectory() as td:
            in_py = Path(td) / "case.py"
            in_py.write_text(src, encoding="utf-8")
            east = load_east(in_py, parser_backend="self_hosted")
            swift = transpile_to_swift_native(east)
        self.assertIn("var a: [Any] = Array(__pytra_as_list(xs))", swift)
        self.assertIn(
            "var b: [AnyHashable: Any] = Dictionary(uniqueKeysWithValues: __pytra_as_dict(ys).map { ($0.key, $0.value) })",
            swift,
        )

    def test_swift_native_emitter_maps_json_calls_to_runtime_helpers(self) -> None:
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
            swift = transpile_to_swift_native(east)
        self.assertIn("var obj: Any = pyJsonLoads(s)", swift)
        self.assertIn("return __pytra_str(pyJsonDumps(obj))", swift)
        self.assertNotIn("json.loads(", swift)
        self.assertNotIn("json.dumps(", swift)

    def test_swift_native_emitter_uses_runtime_path_class(self) -> None:
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
            swift = transpile_to_swift_native(east)
        self.assertIn("var p: Path = Path(\"tmp/a.txt\")", swift)
        self.assertIn("p.parent.mkdir(true, true)", swift)
        self.assertIn("return p.exists()", swift)

    def test_swift_native_emitter_backend_only_ir_fixture_resolves_math_and_path(self) -> None:
        fixture = ROOT / "test" / "ir" / "java_math_path_runtime.east3.json"
        east = load_east(fixture, parser_backend="self_hosted")
        swift = transpile_to_swift_native(east)
        self.assertIn("var p: Path = Path(\"tmp/a.txt\")", swift)
        self.assertIn("var q: Path = p.parent", swift)
        self.assertIn("var n: String = __pytra_str(p.name)", swift)
        self.assertIn("var s: String = __pytra_str(p.stem)", swift)
        self.assertIn("var x: Double = pyMathSin(__pytra_float(pyMathPi()))", swift)

    def test_swift_native_emitter_fail_closed_on_unresolved_stdlib_runtime_call(self) -> None:
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
            transpile_to_swift_native(east)
        self.assertIn("unresolved stdlib runtime call", str(cm.exception))

    def test_py2swift_does_not_import_src_common(self) -> None:
        src = (ROOT / "src" / "py2x.py").read_text(encoding="utf-8")
        self.assertNotIn("src.common", src)
        self.assertNotIn("from common.", src)

    def test_swift_runtime_source_path_is_migrated(self) -> None:
        runtime_path = ROOT / "src" / "runtime" / "swift" / "native" / "built_in" / "py_runtime.swift"
        generated_contains = ROOT / "src" / "runtime" / "swift" / "generated" / "built_in" / "contains.swift"
        generated_zip = ROOT / "src" / "runtime" / "swift" / "generated" / "built_in" / "zip_ops.swift"
        image_runtime = ROOT / "src" / "runtime" / "swift" / "generated" / "utils" / "image_runtime.swift"
        legacy_path = ROOT / "src" / "swift_module" / "py_runtime.swift"
        self.assertTrue(runtime_path.exists())
        self.assertTrue(generated_contains.exists())
        self.assertTrue(generated_zip.exists())
        self.assertTrue(image_runtime.exists())
        self.assertFalse(legacy_path.exists())

    def test_swift_generated_built_in_compare_lane_compiles_with_runtime_bundle(self) -> None:
        runtime_path = ROOT / "src" / "runtime" / "swift" / "native" / "built_in" / "py_runtime.swift"
        contains_path = ROOT / "src" / "runtime" / "swift" / "generated" / "built_in" / "contains.swift"
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            (tmp / "py_runtime.swift").write_text(runtime_path.read_text(encoding="utf-8"), encoding="utf-8")
            (tmp / "contains.swift").write_text(contains_path.read_text(encoding="utf-8"), encoding="utf-8")
            (tmp / "Main.swift").write_text(
                "\n".join(
                    [
                        "@main",
                        "struct Main {",
                        "    static func main() {",
                        '        print(py_contains_str_object("abc", "b") ? "swift-built-in-ok" : "swift-built-in-bad")',
                        "    }",
                        "}",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            build_proc = subprocess.run(
                [
                    "swiftc",
                    str(tmp / "py_runtime.swift"),
                    str(tmp / "contains.swift"),
                    str(tmp / "Main.swift"),
                    "-o",
                    str(tmp / "built_in"),
                ],
                cwd=tmp,
                text=True,
                capture_output=True,
            )
            self.assertEqual(build_proc.returncode, 0, build_proc.stderr)
            run_proc = subprocess.run(
                [str(tmp / "built_in")],
                cwd=tmp,
                text=True,
                capture_output=True,
            )
            self.assertEqual(run_proc.returncode, 0, run_proc.stderr)
            self.assertEqual(run_proc.stdout.strip(), "swift-built-in-ok")


if __name__ == "__main__":
    unittest.main()
