"""py2php (EAST based) smoke tests."""

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

from backends.php.emitter import load_php_profile, transpile_to_php, transpile_to_php_native
from toolchain.compiler.transpile_cli import load_east3_document
from relative_import_longtail_smoke_support import (
    transpile_relative_import_longtail_project,
    transpile_relative_import_longtail_expect_failure,
)

PHP_RELATIVE_IMPORT_REWRITE_MARKER = "helper_f()"
PHP_RELATIVE_IMPORT_MODULE_ALIAS_FORBIDDEN = "$h->f()"
PHP_RELATIVE_IMPORT_SYMBOL_ALIAS_FORBIDDEN = "g()"


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
        target_lang="php",
    )
    return doc3 if isinstance(doc3, dict) else {}


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


def find_sample_case(stem: str) -> Path:
    p = ROOT / "sample" / "py" / f"{stem}.py"
    if not p.exists():
        raise FileNotFoundError(f"missing sample: {stem}")
    return p


class Py2PhpSmokeTest(unittest.TestCase):
    def test_load_php_profile_contains_core_sections(self) -> None:
        profile = load_php_profile()
        self.assertIn("types", profile)
        self.assertIn("operators", profile)
        self.assertIn("syntax", profile)
        self.assertIn("runtime_calls", profile)

    def test_tuple_assign_fixture_lowers_swap_via_temp_for_php(self) -> None:
        fixture = find_fixture_case("tuple_assign")
        east = load_east(fixture, parser_backend="self_hosted")
        php = transpile_to_php_native(east)
        self.assertIn("$__pytra_swap_", php)
        self.assertIn("$x = $y;", php)
        self.assertRegex(php, r"\$y = \$__pytra_swap_\d+;")

    def test_longtail_bundle_representative_fixtures_transpile_for_php(self) -> None:
        for stem in (
            "tuple_assign",
            "lambda_basic",
            "comprehension",
            "try_raise",
            "enumerate_basic",
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
                php = transpile_to_php_native(east)
                self.assertTrue(php.strip())

    def test_php_runtime_source_path_is_migrated(self) -> None:
        runtime_path = ROOT / "src" / "runtime" / "php" / "native" / "built_in" / "py_runtime.php"
        generated_contains_path = ROOT / "src" / "runtime" / "php" / "generated" / "built_in" / "contains.php"
        generated_sequence_path = ROOT / "src" / "runtime" / "php" / "generated" / "built_in" / "sequence.php"
        generated_json_path = ROOT / "src" / "runtime" / "php" / "generated" / "std" / "json.php"
        generated_math_path = ROOT / "src" / "runtime" / "php" / "generated" / "std" / "math.php"
        generated_pathlib_path = ROOT / "src" / "runtime" / "php" / "generated" / "std" / "pathlib.php"
        time_path = ROOT / "src" / "runtime" / "php" / "native" / "std" / "time.php"
        generated_time_path = ROOT / "src" / "runtime" / "php" / "generated" / "std" / "time.php"
        png_path = ROOT / "src" / "runtime" / "php" / "generated" / "utils" / "png.php"
        gif_path = ROOT / "src" / "runtime" / "php" / "generated" / "utils" / "gif.php"
        compat_time_path = ROOT / "src" / "runtime" / "php" / "pytra" / "std" / "time.php"
        legacy_path = ROOT / "src" / "runtime" / "php" / "pytra-core"
        self.assertTrue(runtime_path.exists())
        self.assertTrue(generated_contains_path.exists())
        self.assertTrue(generated_sequence_path.exists())
        self.assertTrue(generated_json_path.exists())
        self.assertTrue(generated_math_path.exists())
        self.assertTrue(generated_pathlib_path.exists())
        self.assertTrue(time_path.exists())
        self.assertTrue(generated_time_path.exists())
        self.assertTrue(png_path.exists())
        self.assertTrue(gif_path.exists())
        self.assertTrue(compat_time_path.exists())
        self.assertFalse((ROOT / "src" / "runtime" / "php" / "pytra" / "std" / "math.php").exists())
        self.assertFalse((ROOT / "src" / "runtime" / "php" / "pytra" / "std" / "pathlib.php").exists())
        self.assertFalse(legacy_path.exists())

    def test_php_repo_generated_and_compat_lanes_resolve_native_substrate(self) -> None:
        generated_json_path = ROOT / "src" / "runtime" / "php" / "generated" / "std" / "json.php"
        generated_pathlib_path = ROOT / "src" / "runtime" / "php" / "generated" / "std" / "pathlib.php"
        generated_png_path = ROOT / "src" / "runtime" / "php" / "generated" / "utils" / "png.php"
        code = "\n".join(
            [
                f"require {generated_json_path.as_posix()!r};",
                f"require {generated_pathlib_path.as_posix()!r};",
                f"require {generated_png_path.as_posix()!r};",
                "$doc = loads_obj('{\"name\":\"a.txt\",\"items\":[1,2],\"empty\":{}}');",
                "echo ($doc instanceof JsonObj ? $doc->get_str('name') : 'json-missing'), PHP_EOL;",
                "$items = $doc instanceof JsonObj ? $doc->get_arr('items') : null;",
                "echo ($items instanceof JsonArr && $items->get_int(1) === 2 ? 'json-ok' : 'json-missing'), PHP_EOL;",
                "$empty = $doc instanceof JsonObj ? $doc->get_obj('empty') : null;",
                "echo ($empty instanceof JsonObj ? 'json-obj-ok' : 'json-obj-missing'), PHP_EOL;",
                "echo dumps(['x' => 1]), PHP_EOL;",
                "echo (new Path('tmp/a.txt'))->name, PHP_EOL;",
                "echo function_exists('write_rgb_png') ? 'png-ok' : 'png-missing', PHP_EOL;",
            ]
        )
        proc = subprocess.run(
            ["php", "-r", code],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, "a.txt\njson-ok\njson-obj-ok\n{\"x\":1}\na.txt\npng-ok\n")

    def test_php_generated_built_in_compare_lane_resolves_native_runtime(self) -> None:
        generated_contains_path = ROOT / "src" / "runtime" / "php" / "generated" / "built_in" / "contains.php"
        generated_predicates_path = ROOT / "src" / "runtime" / "php" / "generated" / "built_in" / "predicates.php"
        generated_sequence_path = ROOT / "src" / "runtime" / "php" / "generated" / "built_in" / "sequence.php"
        code = "\n".join(
            [
                f"require {generated_contains_path.as_posix()!r};",
                f"require {generated_predicates_path.as_posix()!r};",
                f"require {generated_sequence_path.as_posix()!r};",
                "echo py_contains_str_object('abc', 'b') ? 'contains-ok' : 'contains-missing', PHP_EOL;",
                "echo py_any([0, 1]) ? 'predicates-ok' : 'predicates-missing', PHP_EOL;",
                "$xs = py_range(1, 4, 1);",
                "echo ($xs[0] === 1 && $xs[2] === 3 ? 'sequence-ok' : 'sequence-missing'), PHP_EOL;",
            ]
        )
        proc = subprocess.run(
            ["php", "-r", code],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, "contains-ok\npredicates-ok\nsequence-ok\n")

    def test_php_repo_public_compat_lane_resolves_remaining_shims(self) -> None:
        compat_runtime_path = ROOT / "src" / "runtime" / "php" / "pytra" / "py_runtime.php"
        compat_time_path = ROOT / "src" / "runtime" / "php" / "pytra" / "std" / "time.php"
        compat_png_path = ROOT / "src" / "runtime" / "php" / "pytra" / "utils" / "png.php"
        compat_gif_path = ROOT / "src" / "runtime" / "php" / "pytra" / "utils" / "gif.php"
        code = "\n".join(
            [
                f"require_once {compat_runtime_path.as_posix()!r};",
                f"require_once {compat_time_path.as_posix()!r};",
                f"require_once {compat_png_path.as_posix()!r};",
                f"require_once {compat_gif_path.as_posix()!r};",
                "echo __pytra_truthy([1]) ? 'truthy-ok' : 'truthy-missing', PHP_EOL;",
                "echo (perf_counter() > 0.0) ? 'time-ok' : 'time-missing', PHP_EOL;",
                "echo function_exists('__pytra_write_rgb_png') ? 'png-ok' : 'png-missing', PHP_EOL;",
                "echo function_exists('__pytra_save_gif') ? 'gif-ok' : 'gif-missing', PHP_EOL;",
            ]
        )
        proc = subprocess.run(
            ["php", "-r", code],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, "truthy-ok\ntime-ok\npng-ok\ngif-ok\n")

    def test_transpile_dict_items_fixture_uses_foreach_key_value(self) -> None:
        fixture = find_fixture_case("dict_get_items")
        east = load_east(fixture, parser_backend="self_hosted")
        php = transpile_to_php_native(east)
        self.assertIn('foreach (($table["a"] ?? []) as $__pytra_iter_key_', php)
        self.assertIn('foreach (($table["missing"] ?? []) as $__pytra_iter_key_', php)
        self.assertIn('$_k = ($__pytra_iter_item_', php)
        self.assertIn('$v = ($__pytra_iter_item_', php)

    def test_bitwise_invert_basic_uses_php_invert_operator(self) -> None:
        fixture = find_fixture_case("bitwise_invert_basic")
        east = load_east(fixture, parser_backend="self_hosted")
        php = transpile_to_php_native(east)
        self.assertIn("~$y", php)

    def test_transpile_for_range_fixture_contains_static_for(self) -> None:
        fixture = find_fixture_case("for_range")
        east = load_east(fixture, parser_backend="self_hosted")
        php = transpile_to_php_native(east)
        self.assertIn("function sum_range_29($n)", php)
        self.assertIn("for ($i = 0; $i < $n; $i += 1)", php)
        self.assertIn("$total += $i;", php)

    def test_bitwise_invert_fixture_uses_php_bitwise_not(self) -> None:
        fixture = find_fixture_case("bitwise_invert_basic")
        east = load_east(fixture, parser_backend="self_hosted")
        php = transpile_to_php_native(east)
        self.assertIn("~$y", php)

    def test_cli_relative_import_support_rollout_scenarios_transpile_for_php(self) -> None:
        for scenario_id in ("parent_module_alias", "parent_symbol_alias"):
            with self.subTest(scenario_id=scenario_id):
                php = transpile_relative_import_longtail_project("php", scenario_id)
                self.assertIn(PHP_RELATIVE_IMPORT_REWRITE_MARKER, php)
                if scenario_id == "parent_module_alias":
                    self.assertNotIn(PHP_RELATIVE_IMPORT_MODULE_ALIAS_FORBIDDEN, php)
                else:
                    self.assertNotIn(PHP_RELATIVE_IMPORT_SYMBOL_ALIAS_FORBIDDEN, php)

    def test_cli_relative_import_support_rollout_fail_closed_for_wildcard_on_php(self) -> None:
        err = transpile_relative_import_longtail_expect_failure(
            "php",
            "from ..helper import *",
            "f()",
        )
        self.assertIn("unsupported relative import form: wildcard import", err)
        self.assertIn("php native emitter", err)

    def test_transpile_downcount_range_fixture_uses_descending_condition(self) -> None:
        fixture = find_fixture_case("range_downcount_len_minus1")
        east = load_east(fixture, parser_backend="self_hosted")
        php = transpile_to_php_native(east)
        self.assertIn("for ($i = (__pytra_len($xs) - 1); $i > (-1); $i -= 1)", php)

    def test_transpile_inheritance_fixture_contains_extends(self) -> None:
        fixture = find_fixture_case("inheritance")
        east = load_east(fixture, parser_backend="self_hosted")
        php = transpile_to_php_native(east)
        self.assertIn("class Animal", php)
        self.assertIn("class Dog extends Animal", php)
        self.assertIn("$this->sound()", php)

    def test_transpile_virtual_dispatch_fixture_lowers_parent_method_call(self) -> None:
        fixture = find_fixture_case("inheritance_virtual_dispatch_multilang")
        east = load_east(fixture, parser_backend="self_hosted")
        php = transpile_to_php_native(east)
        self.assertIn("class LoudDog extends Dog", php)
        self.assertIn("parent::speak()", php)

    def test_transpile_is_instance_fixture_uses_instanceof(self) -> None:
        fixture = find_fixture_case("is_instance")
        east = load_east(fixture, parser_backend="self_hosted")
        php = transpile_to_php_native(east)
        self.assertIn("($cat instanceof Dog)", php)
        self.assertIn("($dog instanceof Animal)", php)

    def test_transpile_sample05_save_gif_emits_delay_and_loop(self) -> None:
        sample = find_sample_case("05_mandelbrot_zoom")
        east = load_east(sample, parser_backend="self_hosted")
        php = transpile_to_php_native(east)
        self.assertIn("save_gif($out_path, $width, $height, $frames, grayscale_palette(), 5, 0);", php)

    def test_transpile_save_gif_keyword_order_is_respected(self) -> None:
        src = (
            "from pytra.utils.gif import save_gif, grayscale_palette\n\n"
            "def main() -> None:\n"
            "    frames: list[bytes] = [bytes([0])]\n"
            "    save_gif('x.gif', 1, 1, frames, grayscale_palette(), loop=0, delay_cs=4)\n"
        )
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "case.py"
            p.write_text(src, encoding="utf-8")
            east = load_east(p, parser_backend="self_hosted")
            php = transpile_to_php_native(east)
        self.assertIn("save_gif(\"x.gif\", 1, 1, $frames, grayscale_palette(), 4, 0);", php)
        self.assertNotIn("save_gif(\"x.gif\", 1, 1, $frames, grayscale_palette(), 0, 4);", php)

    def test_transpile_sample16_bitwise_ops_are_preserved(self) -> None:
        sample = find_sample_case("16_glass_sculpture_chaos")
        east = load_east(sample, parser_backend="self_hosted")
        php = transpile_to_php_native(east)
        self.assertIn("($i >> 5)", php)
        self.assertIn("($i & 3)", php)
        self.assertIn("(($rr >> 5) << 5)", php)

    def test_php_native_emitter_backend_only_ir_fixture_resolves_math_and_path(self) -> None:
        fixture = ROOT / "test" / "ir" / "java_math_path_runtime.east3.json"
        east = json.loads(fixture.read_text(encoding="utf-8"))
        php = transpile_to_php_native(east)
        self.assertIn('$p = new Path("tmp/a.txt");', php)
        self.assertIn("$q = $p->parent;", php)
        self.assertIn("$n = $p->name;", php)
        self.assertIn("$s = $p->stem;", php)
        self.assertIn("$x = pyMathSin(pyMathPi());", php)

    def test_php_emitter_source_has_no_pymath_special_case(self) -> None:
        src = (ROOT / "src" / "backends" / "php" / "emitter" / "php_native_emitter.py").read_text(encoding="utf-8")
        self.assertNotIn('runtime_symbol == "pyMathPi"', src)
        self.assertNotIn('runtime_symbol == "pyMathE"', src)
        self.assertNotIn("runtime_symbol == 'pyMathPi'", src)
        self.assertNotIn("runtime_symbol == 'pyMathE'", src)

    def test_php_native_emitter_fail_closed_on_unresolved_stdlib_runtime_call(self) -> None:
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
            transpile_to_php_native(east)
        self.assertIn("unresolved stdlib runtime", str(cm.exception))

    def test_php_native_emitter_fail_closed_on_unresolved_resolved_runtime_call(self) -> None:
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
            transpile_to_php_native(east)
        self.assertIn("unresolved stdlib runtime", str(cm.exception))

if __name__ == "__main__":
    unittest.main()
