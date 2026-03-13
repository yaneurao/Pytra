"""py2nim (EAST based) smoke tests."""

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

from backends.nim.emitter import load_nim_profile, transpile_to_nim, transpile_to_nim_native
from toolchain.compiler.transpile_cli import load_east3_document
from relative_import_native_path_smoke_support import (
    relative_import_native_path_expected_rewrite,
    relative_import_native_path_scenarios,
    transpile_relative_import_native_path_via_module_graph,
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
        target_lang="nim",
    )
    return doc3 if isinstance(doc3, dict) else {}


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


class Py2NimSmokeTest(unittest.TestCase):
    def test_load_nim_profile_contains_core_sections(self) -> None:
        profile = load_nim_profile()
        self.assertIn("types", profile)
        self.assertIn("operators", profile)
        self.assertIn("syntax", profile)
        self.assertIn("runtime_calls", profile)

    def test_bitwise_invert_basic_uses_nim_not(self) -> None:
        fixture = find_fixture_case("bitwise_invert_basic")
        east = load_east(fixture, parser_backend="self_hosted")
        nim = transpile_to_nim_native(east)
        self.assertIn("not y", nim)

    def test_transpile_for_range_fixture_contains_static_for(self) -> None:
        fixture = find_fixture_case("for_range")
        east = load_east(fixture, parser_backend="self_hosted")
        nim = transpile_to_nim_native(east)
        self.assertIn("proc sum_range_29", nim)
        self.assertIn("for i in 0 ..< n", nim)

    def test_bitwise_invert_fixture_uses_nim_not(self) -> None:
        fixture = find_fixture_case("bitwise_invert_basic")
        east = load_east(fixture, parser_backend="self_hosted")
        nim = transpile_to_nim_native(east)
        self.assertIn("not y", nim)

    def test_cli_relative_import_native_path_bundle_scenarios_transpile_for_nim(self) -> None:
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
                    nim = transpile_to_nim_native(east)
                positive, forbidden = relative_import_native_path_expected_rewrite(scenario_id)
                self.assertIn(positive, nim)
                self.assertNotIn(forbidden, nim)

    def test_cli_relative_import_native_path_bundle_supports_wildcard_on_nim(self) -> None:
        nim = transpile_relative_import_native_path_via_module_graph(
            target="nim",
            import_form="from ..helper import *",
            body_text="def call() -> int:\n    return f() + X\n",
        )
        self.assertIn("helper.f()", nim)
        self.assertIn("helper.X", nim)

    def test_direct_relative_import_native_path_bundle_stays_fail_closed_for_wildcard_on_nim(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            entry_path = write_relative_import_native_path_project(
                Path(td),
                import_form="from ..helper import *",
                body_text="def call() -> int:\n    return f()\n",
            )
            east = load_east(entry_path, parser_backend="self_hosted")
            with self.assertRaises(RuntimeError) as cm:
                transpile_to_nim_native(east)
        self.assertIn("unsupported relative import form: wildcard import", str(cm.exception))
        self.assertIn("nim native emitter", str(cm.exception))

    def test_nim_native_emitter_backend_only_ir_fixture_resolves_math_and_path(self) -> None:
        fixture = ROOT / "test" / "ir" / "java_math_path_runtime.east3.json"
        east = json.loads(fixture.read_text(encoding="utf-8"))
        nim = transpile_to_nim_native(east)
        self.assertIn('var p = Path("tmp/a.txt")', nim)
        self.assertIn("var q = p.parent", nim)
        self.assertIn("n = p.name", nim)
        self.assertIn("s = p.stem", nim)
        self.assertIn("x = math.sin(PI)", nim)

    def test_secondary_bundle_representative_fixtures_transpile_for_nim(self) -> None:
        for stem in (
            "tuple_assign",
            "lambda_basic",
            "comprehension",
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
                nim = transpile_to_nim_native(east)
                self.assertTrue(nim.strip())

    def test_tuple_assign_fixture_lowers_swap_via_temp_for_nim(self) -> None:
        fixture = find_fixture_case("tuple_assign")
        east = load_east(fixture, parser_backend="self_hosted")
        nim = transpile_to_nim_native(east)
        self.assertIn("var __swap_", nim)
        self.assertIn("x = y", nim)
        self.assertRegex(nim, r"y = __swap_\d+")

    def test_nim_emitter_source_has_no_owner_math_special_case(self) -> None:
        src = (ROOT / "src" / "backends" / "nim" / "emitter" / "nim_native_emitter.py").read_text(encoding="utf-8")
        self.assertNotIn('owner == "math"', src)
        self.assertNotIn("owner == 'math'", src)
        self.assertNotIn('"pytra.std.math"', src)
        self.assertNotIn("'pytra.std.math'", src)

    def test_nim_native_emitter_routes_math_symbols_via_runtime_metadata(self) -> None:
        fixture = find_fixture_case("pytra_std_import_math")
        east = load_east(fixture, parser_backend="self_hosted")
        nim = transpile_to_nim_native(east)
        self.assertIn("math.sqrt(float(81.0))", nim)
        self.assertIn("floor(3.9)", nim)

    def test_nim_native_emitter_fail_closed_on_unresolved_stdlib_runtime_call(self) -> None:
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
            transpile_to_nim_native(east)
        self.assertIn("unresolved stdlib runtime", str(cm.exception))

    def test_nim_native_emitter_fail_closed_on_unresolved_resolved_runtime_call(self) -> None:
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
            transpile_to_nim_native(east)
        self.assertIn("unresolved stdlib runtime", str(cm.exception))

    def test_nim_runtime_source_path_is_migrated(self) -> None:
        delete_target_runtime = ROOT / "src" / "runtime" / "nim" / "pytra" / "built_in" / "py_runtime.nim"
        native_runtime = ROOT / "src" / "runtime" / "nim" / "native" / "built_in" / "py_runtime.nim"
        generated_root = ROOT / "src" / "runtime" / "nim" / "generated"
        legacy_path = ROOT / "src" / "nim_module" / "py_runtime.nim"
        self.assertFalse(delete_target_runtime.exists())
        self.assertTrue(native_runtime.exists())
        for rel_path in (
            "built_in/contains.nim",
            "built_in/io_ops.nim",
            "built_in/iter_ops.nim",
            "built_in/numeric_ops.nim",
            "built_in/predicates.nim",
            "built_in/scalar_ops.nim",
            "built_in/sequence.nim",
            "built_in/string_ops.nim",
            "built_in/type_id.nim",
            "built_in/zip_ops.nim",
            "std/argparse.nim",
            "std/glob.nim",
            "std/json.nim",
            "std/math.nim",
            "std/os.nim",
            "std/os_path.nim",
            "std/pathlib.nim",
            "std/random.nim",
            "std/re.nim",
            "std/sys.nim",
            "std/time.nim",
            "std/timeit.nim",
            "utils/assertions.nim",
            "utils/gif.nim",
            "utils/image_runtime.nim",
            "utils/png.nim",
        ):
            self.assertTrue((generated_root / rel_path).exists(), msg=rel_path)
        self.assertFalse(legacy_path.exists())

    def test_nim_generated_built_in_compare_lane_compiles_with_runtime_bundle(self) -> None:
        runtime_path = ROOT / "src" / "runtime" / "nim" / "native" / "built_in" / "py_runtime.nim"
        image_runtime = ROOT / "src" / "runtime" / "nim" / "generated" / "utils" / "image_runtime.nim"
        contains_path = ROOT / "src" / "runtime" / "nim" / "generated" / "built_in" / "contains.nim"
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            (tmp / "py_runtime.nim").write_text(runtime_path.read_text(encoding="utf-8"), encoding="utf-8")
            (tmp / "image_runtime.nim").write_text(image_runtime.read_text(encoding="utf-8"), encoding="utf-8")
            (tmp / "contains.nim").write_text(contains_path.read_text(encoding="utf-8"), encoding="utf-8")
            (tmp / "main.nim").write_text(
                "\n".join(
                    [
                        'include "contains.nim"',
                        "",
                        "when isMainModule:",
                        '  if py_contains_str_object("abc", "b"):',
                        '    echo "nim-built-in-ok"',
                        "  else:",
                        '    echo "nim-built-in-bad"',
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            run_proc = subprocess.run(
                [
                    "nim",
                    "c",
                    "-r",
                    "--nimcache:" + str(tmp / "nimcache"),
                    str(tmp / "main.nim"),
                ],
                cwd=tmp,
                text=True,
                capture_output=True,
            )
            self.assertEqual(run_proc.returncode, 0, run_proc.stderr)
            self.assertIn("nim-built-in-ok", run_proc.stdout)

    def test_representative_property_method_call_fixture_transpiles(self) -> None:
        try:
            from test.unit.backends.representative_contract_support import (
                assert_no_representative_escape,
            )
        except ModuleNotFoundError:
            from representative_contract_support import assert_no_representative_escape

        fixture = find_fixture_case("property_method_call")
        east = load_east(fixture, parser_backend="self_hosted")
        nim = transpile_to_nim_native(east)
        assert_no_representative_escape(self, nim, backend="nim", fixture="property_method_call")

    def test_representative_list_bool_index_fixture_transpiles(self) -> None:
        try:
            from test.unit.backends.representative_contract_support import (
                assert_no_representative_escape,
            )
        except ModuleNotFoundError:
            from representative_contract_support import assert_no_representative_escape

        fixture = find_fixture_case("list_bool_index")
        east = load_east(fixture, parser_backend="self_hosted")
        nim = transpile_to_nim_native(east)
        assert_no_representative_escape(self, nim, backend="nim", fixture="list_bool_index")

if __name__ == "__main__":
    unittest.main()
