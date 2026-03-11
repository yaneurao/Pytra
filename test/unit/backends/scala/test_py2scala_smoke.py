"""py2scala (EAST based) smoke tests."""

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

from backends.scala.emitter import load_scala_profile, transpile_to_scala, transpile_to_scala_native
from toolchain.compiler.transpile_cli import load_east3_document
from src.toolchain.ir.core_entrypoints import convert_path


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
        target_lang="scala",
    )
    return doc3 if isinstance(doc3, dict) else {}


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


class Py2ScalaSmokeTest(unittest.TestCase):
    def test_load_scala_profile_contains_core_sections(self) -> None:
        profile = load_scala_profile()
        self.assertIn("types", profile)
        self.assertIn("operators", profile)
        self.assertIn("syntax", profile)
        self.assertIn("runtime_calls", profile)

    def test_scala_native_emitter_skeleton_handles_module_function_class(self) -> None:
        fixture = find_fixture_case("inheritance")
        east = load_east(fixture, parser_backend="self_hosted")
        scala = transpile_to_scala_native(east)
        self.assertIn("def main(args: Array[String]): Unit", scala)
        self.assertIn("class Animal()", scala)
        self.assertIn("class Dog() extends Animal()", scala)
        self.assertIn("def _case_main(): Unit =", scala)

    def test_scala_native_emitter_emits_override_and_super_for_dispatch_fixture(self) -> None:
        fixture = find_fixture_case("inheritance_virtual_dispatch_multilang")
        east = load_east(fixture, parser_backend="self_hosted")
        scala = transpile_to_scala_native(east)
        self.assertIn("override def speak(): String = {", scala)
        self.assertIn("super.speak()", scala)

    def test_module_leading_comments_are_emitted(self) -> None:
        sample = ROOT / "sample" / "py" / "01_mandelbrot.py"
        east = load_east(sample, parser_backend="self_hosted")
        scala = transpile_to_scala_native(east)
        self.assertIn("// 01: Sample that outputs the Mandelbrot set as a PNG image.", scala)
        self.assertIn("// Syntax is kept straightforward with future transpilation in mind.", scala)

    def test_png_writer_uses_runtime_helper_instead_of_noop(self) -> None:
        sample = ROOT / "sample" / "py" / "01_mandelbrot.py"
        east = load_east(sample, parser_backend="self_hosted")
        scala = transpile_to_scala_native(east)
        self.assertIn("__pytra_write_rgb_png(out_path, width, height, pixels)", scala)
        self.assertNotIn("__pytra_noop(out_path, width, height, pixels)", scala)
        self.assertNotIn("def __pytra_write_rgb_png(", scala)

    def test_gif_writer_uses_runtime_helper_instead_of_noop(self) -> None:
        sample = ROOT / "sample" / "py" / "06_julia_parameter_sweep.py"
        east = load_east(sample, parser_backend="self_hosted")
        scala = transpile_to_scala_native(east)
        self.assertIn("__pytra_save_gif(out_path, width, height, frames, julia_palette(), 8L, 0L)", scala)
        self.assertNotIn("__pytra_noop(out_path, width, height, frames, julia_palette())", scala)
        self.assertNotIn("def __pytra_save_gif(", scala)

    def test_scala_native_emitter_save_gif_keyword_order_uses_adapter_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "gif_case.py"
            src.write_text(
                "from pytra.utils.gif import save_gif, grayscale_palette\n\n"
                "def main(frames: list[bytes]) -> None:\n"
                "    save_gif('x.gif', 1, 1, frames, grayscale_palette(), loop=0, delay_cs=4)\n",
                encoding="utf-8",
            )
            east = load_east(src, parser_backend="self_hosted")
            scala = transpile_to_scala_native(east)
        self.assertIn("__pytra_save_gif(\"x.gif\", 1L, 1L, frames, __pytra_grayscale_palette(), 4L, 0L)", scala)
        self.assertNotIn("__pytra_save_gif(\"x.gif\", 1L, 1L, frames, __pytra_grayscale_palette(), 0L, 4L)", scala)

    def test_sample_01_quality_fastpaths_reduce_redundant_wrappers(self) -> None:
        sample = ROOT / "sample" / "py" / "01_mandelbrot.py"
        east = load_east(sample, parser_backend="self_hosted")
        scala = transpile_to_scala_native(east)
        self.assertNotIn("__pytra_float(__pytra_float(", scala)
        self.assertNotIn("__pytra_int(__pytra_int(", scala)
        self.assertIn("while (y < height) {", scala)
        self.assertIn("while (x < width) {", scala)
        self.assertIn("pixels.append(r)", scala)
        self.assertNotIn("pixels = __pytra_as_list(pixels); pixels.append(", scala)
        self.assertNotIn("def __pytra_write_rgb_png(", scala)
        self.assertNotIn("def __pytra_save_gif(", scala)

    def test_sample_01_preserves_nested_arithmetic_precedence(self) -> None:
        sample = ROOT / "sample" / "py" / "01_mandelbrot.py"
        east = load_east(sample, parser_backend="self_hosted")
        scala = transpile_to_scala_native(east)
        self.assertIn("__pytra_int(255.0 * (1.0 - t))", scala)
        self.assertNotIn("__pytra_int(255.0 * 1.0 - t)", scala)

    def test_scala_native_emitter_fail_closed_on_unsupported_stmt_kind(self) -> None:
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
                    "body": [{"kind": "UnsupportedStmt"}],
                }
            ],
            "main_guard_body": [],
        }
        with self.assertRaises(RuntimeError) as cm:
            transpile_to_scala_native(east)
        self.assertIn("unsupported stmt kind", str(cm.exception))

    def test_scala_native_emitter_fail_closed_on_unresolved_stdlib_runtime_call(self) -> None:
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
        }
        with self.assertRaises(RuntimeError) as cm:
            transpile_to_scala_native(east)
        self.assertIn("unresolved stdlib runtime call", str(cm.exception))

    def test_sample_18_scala_output_has_no_unsupported_todo_marker(self) -> None:
        sample = ROOT / "sample" / "py" / "18_mini_language_interpreter.py"
        east = load_east(sample, parser_backend="self_hosted")
        scala = transpile_to_scala_native(east)
        self.assertNotIn("TODO: unsupported", scala)
        self.assertIn(
            "__pytra_as_dict(single_char_token_tags).getOrElse(__pytra_str(ch), 0L)",
            scala,
        )

    def test_sample_18_scala_output_preserves_continue_inside_loop(self) -> None:
        sample = ROOT / "sample" / "py" / "18_mini_language_interpreter.py"
        east = load_east(sample, parser_backend="self_hosted")
        scala = transpile_to_scala_native(east)
        self.assertNotIn("pytra continue outside loop", scala)
        self.assertIn("break(())(using __continueLabel_", scala)

    def test_pathlib_fixture_uses_path_runtime_helpers(self) -> None:
        fixture = find_fixture_case("pathlib_extended")
        east = load_east(fixture, parser_backend="self_hosted")
        scala = transpile_to_scala_native(east)
        self.assertIn("__pytra_path_new(", scala)
        self.assertIn("__pytra_path_join(", scala)
        self.assertIn("__pytra_path_exists(", scala)
        self.assertIn("__pytra_path_read_text(", scala)
        self.assertNotIn("var root: Path", scala)

    def test_math_fixture_maps_fabs_to_scala_abs(self) -> None:
        fixture = find_fixture_case("math_extended")
        east = load_east(fixture, parser_backend="self_hosted")
        scala = transpile_to_scala_native(east)
        self.assertIn("scala.math.abs", scala)
        self.assertNotIn("fabs(", scala)

    def test_scala_emitter_source_has_no_source_math_special_case(self) -> None:
        src = (ROOT / "src" / "backends" / "scala" / "emitter" / "scala_native_emitter.py").read_text(encoding="utf-8")
        self.assertNotIn('module_name == "math"', src)
        self.assertNotIn("module_name == 'math'", src)

    def test_for_core_static_range_prefers_normalized_condition_expr(self) -> None:
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
                            "kind": "ForCore",
                            "normalized_expr_version": "east3_expr_v1",
                            "normalized_exprs": {
                                "for_cond_expr": {
                                    "kind": "Compare",
                                    "left": {"kind": "Name", "id": "i", "resolved_type": "int64"},
                                    "ops": ["Gt"],
                                    "comparators": [{"kind": "Constant", "value": 3, "resolved_type": "int64"}],
                                    "resolved_type": "bool",
                                }
                            },
                            "target_plan": {"kind": "NameTarget", "id": "i", "target_type": "int64"},
                            "iter_plan": {
                                "kind": "StaticRangeForPlan",
                                "start": {"kind": "Constant", "value": 0, "resolved_type": "int64"},
                                "stop": {"kind": "Constant", "value": 3, "resolved_type": "int64"},
                                "step": {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                                "range_mode": "ascending",
                            },
                            "body": [{"kind": "Pass"}],
                            "orelse": [],
                        }
                    ],
                }
            ],
            "main_guard_body": [],
            "meta": {},
        }
        scala = transpile_to_scala_native(east)
        self.assertIn("while (i > 3L) {", scala)
        self.assertNotIn("while ((i > 3L)) {", scala)
        self.assertNotIn("while ((i < 3L)) {", scala)

    def test_py2scala_does_not_import_src_common(self) -> None:
        src = (ROOT / "src" / "py2x.py").read_text(encoding="utf-8")
        self.assertNotIn("src.common", src)
        self.assertNotIn("from common.", src)


if __name__ == "__main__":
    unittest.main()
