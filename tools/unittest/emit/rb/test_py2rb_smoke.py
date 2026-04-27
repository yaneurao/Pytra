"""py2rb (EAST based) smoke tests."""

# Language-specific smoke suite.
# Shared py2x target-parameterized checks live in test_py2x_smoke_common.py.

from __future__ import annotations

import json
import os
import shutil
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

from toolchain.emit.ruby.emitter import load_ruby_profile, transpile_to_ruby, transpile_to_ruby_native
from toolchain.misc.transpile_cli import load_east3_document
from src.toolchain.compile.core_entrypoints import convert_path
from comment_fidelity import assert_no_generated_comments, assert_sample01_module_comments
from relative_import_longtail_smoke_support import (
    transpile_relative_import_longtail_via_module_graph,
    transpile_relative_import_longtail_project,
    transpile_relative_import_longtail_expect_failure,
)

RUBY_RELATIVE_IMPORT_REWRITE_MARKER = "helper_f()"
RUBY_RELATIVE_IMPORT_MODULE_ALIAS_FORBIDDEN = "h.f()"
RUBY_RELATIVE_IMPORT_SYMBOL_ALIAS_FORBIDDEN = "g()"


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
        target_lang="ruby",
    )
    return doc3 if isinstance(doc3, dict) else {}


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


def find_sample_case(stem: str) -> Path:
    matches = sorted((ROOT / "sample" / "py").glob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing sample: {stem}")
    return matches[0]


class Py2RbSmokeTest(unittest.TestCase):
    def test_load_ruby_profile_contains_core_sections(self) -> None:
        profile = load_ruby_profile()
        self.assertIn("types", profile)
        self.assertIn("operators", profile)
        self.assertIn("syntax", profile)
        self.assertIn("runtime_calls", profile)

    def test_tuple_assign_fixture_lowers_swap_via_temp_for_ruby(self) -> None:
        fixture = find_fixture_case("tuple_assign")
        east = load_east(fixture, parser_backend="self_hosted")
        ruby = transpile_to_ruby_native(east)
        self.assertIn("__swap_", ruby)
        self.assertIn("x = y", ruby)
        self.assertRegex(ruby, r"y = __swap_\d+")

    def test_longtail_bundle_representative_fixtures_transpile_for_ruby(self) -> None:
        for stem in (
            "tuple_assign",
            "lambda_basic",
            "comprehension",
            "for_range",
            "try_raise",
            "enumerate_basic",
            "ok_generator_tuple_target",
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
                ruby = transpile_to_ruby_native(east)
                self.assertTrue(ruby.strip())

    def test_representative_property_method_call_fixture_transpiles(self) -> None:
        try:
            from test.unit.backends.representative_contract_support import (
                assert_no_representative_escape,
            )
        except ModuleNotFoundError:
            from representative_contract_support import assert_no_representative_escape

        fixture = find_fixture_case("property_method_call")
        east = load_east(fixture, parser_backend="self_hosted")
        ruby = transpile_to_ruby_native(east)
        assert_no_representative_escape(self, ruby, backend="ruby", fixture="property_method_call")

    def test_representative_list_bool_index_fixture_transpiles(self) -> None:
        try:
            from test.unit.backends.representative_contract_support import (
                assert_no_representative_escape,
            )
        except ModuleNotFoundError:
            from representative_contract_support import assert_no_representative_escape

        fixture = find_fixture_case("list_bool_index")
        east = load_east(fixture, parser_backend="self_hosted")
        ruby = transpile_to_ruby_native(east)
        assert_no_representative_escape(self, ruby, backend="ruby", fixture="list_bool_index")

    def test_cli_relative_import_support_rollout_scenarios_transpile_for_ruby(self) -> None:
        for scenario_id in ("parent_module_alias", "parent_symbol_alias"):
            with self.subTest(scenario_id=scenario_id):
                ruby = transpile_relative_import_longtail_project("ruby", scenario_id)
                self.assertIn(RUBY_RELATIVE_IMPORT_REWRITE_MARKER, ruby)
                if scenario_id == "parent_module_alias":
                    self.assertNotIn(RUBY_RELATIVE_IMPORT_MODULE_ALIAS_FORBIDDEN, ruby)
                else:
                    self.assertNotIn(RUBY_RELATIVE_IMPORT_SYMBOL_ALIAS_FORBIDDEN, ruby)

    def test_cli_relative_import_support_rollout_fail_closed_for_wildcard_on_ruby(self) -> None:
        err = transpile_relative_import_longtail_expect_failure(
            "ruby",
            "from ..helper import *",
            "f()",
        )
        self.assertIn("unsupported relative import form: wildcard import", err)
        self.assertIn("ruby native emitter", err)

    def test_cli_relative_import_support_rollout_module_graph_wildcard_for_ruby(self) -> None:
        ruby = transpile_relative_import_longtail_via_module_graph(
            target="ruby",
            import_form="from ..helper import *",
            body_text="def call() -> int:\n    return f()\n",
        )
        self.assertIn("helper_f()", ruby)
        self.assertNotIn("unsupported relative import form: wildcard import", ruby)

    def test_module_leading_comments_are_emitted(self) -> None:
        sample = ROOT / "sample" / "py" / "01_mandelbrot.py"
        east = load_east(sample, parser_backend="self_hosted")
        ruby = transpile_to_ruby_native(east)
        assert_no_generated_comments(self, ruby)
        assert_sample01_module_comments(self, ruby, prefix="#")

    def test_py2rb_does_not_import_src_common(self) -> None:
        src = (ROOT / "src" / "pytra-cli.py").read_text(encoding="utf-8")
        self.assertNotIn("src.common", src)
        self.assertNotIn("from common.", src)

    def test_ruby_runtime_source_path_is_migrated(self) -> None:
        runtime_path = ROOT / "src" / "runtime" / "ruby" / "native" / "built_in" / "py_runtime.rb"
        image_runtime = ROOT / "src" / "runtime" / "ruby" / "generated" / "utils" / "image_runtime.rb"
        delete_target_path = ROOT / "src" / "runtime" / "ruby" / "pytra"
        legacy_path = ROOT / "src" / "ruby_module" / "py_runtime.rb"
        self.assertTrue(runtime_path.exists())
        self.assertTrue(image_runtime.exists())
        self.assertFalse(delete_target_path.exists())
        self.assertFalse(legacy_path.exists())

    def test_ruby_generated_std_baseline_source_guard_materializes_new_compare_modules(self) -> None:
        runtime_root = ROOT / "src" / "runtime" / "ruby" / "generated"
        guarded_targets = {
            runtime_root / "built_in" / "type_id.rb": ("def py_tid_runtime_type_id(",),
            runtime_root / "std" / "argparse.rb": ("class ArgSpec", "class ArgumentParser"),
            runtime_root / "std" / "json.rb": ("class JsonObj", "class JsonParser"),
            runtime_root / "std" / "time.rb": ("def perf_counter(",),
            runtime_root / "utils" / "assertions.rb": ("def py_assert_true(",),
            runtime_root / "utils" / "gif.rb": ("def save_gif(",),
            runtime_root / "utils" / "png.rb": ("def write_rgb_png(",),
        }
        for path, needles in guarded_targets.items():
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                text = path.read_text(encoding="utf-8")
                self.assertIn("AUTO-GENERATED FILE. DO NOT EDIT.", text)
                for needle in needles:
                    self.assertIn(needle, text)
        self.assertFalse((runtime_root / "utils" / "gif_helper.rb").exists())
        self.assertFalse((runtime_root / "utils" / "png_helper.rb").exists())
        for lint_path in (
            runtime_root / "built_in" / "type_id.rb",
            runtime_root / "std" / "argparse.rb",
            runtime_root / "std" / "json.rb",
            runtime_root / "utils" / "assertions.rb",
        ):
            with self.subTest(lint_path=lint_path.relative_to(ROOT).as_posix()):
                proc = subprocess.run(
                    ["ruby", "-c", str(lint_path)],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_ruby_cli_staged_runtime_lane_resolves_runtime_helpers(self) -> None:
        fixture = find_fixture_case("add")
        with tempfile.TemporaryDirectory() as td:
            out_rb = Path(td) / "add.rb"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/pytra-cli.py", "--target", "ruby", str(fixture), "-o", str(out_rb)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            staged_runtime = (Path(td) / "py_runtime.rb").resolve()
            self.assertTrue(staged_runtime.exists())
            code = "\n".join(
                [
                    f"load {staged_runtime.as_posix()!r}",
                    "puts(__pytra_truthy([1]) ? 'ruby-ok' : 'ruby-missing')",
                ]
            )
            proc = subprocess.run(
                ["ruby", "-e", code],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(proc.stdout, "ruby-ok\n")

    def test_generated_add_fixture_executes_when_ruby_available(self) -> None:
        if shutil.which("ruby") is None:
            self.skipTest("ruby toolchain is not installed in this environment")
        fixture = find_fixture_case("add")
        with tempfile.TemporaryDirectory() as td:
            out_rb = Path(td) / "add.rb"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/pytra-cli.py", "--target", "ruby", str(fixture), "-o", str(out_rb)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            run = subprocess.run(["ruby", str(out_rb)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, msg=f"{run.stdout}\n{run.stderr}")

    def test_sample07_listcomp_and_bytearray_are_lowered(self) -> None:
        sample = find_sample_case("07_game_of_life_loop")
        east = load_east(sample, parser_backend="self_hosted")
        ruby = transpile_to_ruby_native(east)
        self.assertIn("grid = __pytra_list_comp_range(", ruby)
        self.assertIn("frame = __pytra_bytearray(", ruby)
        self.assertNotIn("grid = nil", ruby)

    def test_sample01_static_range_loops_use_canonical_while_fastpath(self) -> None:
        sample = find_sample_case("01_mandelbrot")
        east = load_east(sample, parser_backend="self_hosted")
        ruby = transpile_to_ruby_native(east)
        self.assertIn("while y < height", ruby)
        self.assertIn("while x < width", ruby)
        self.assertIn("while i < max_iter", ruby)
        self.assertIn("y += 1", ruby)
        self.assertIn("x += 1", ruby)
        self.assertIn("i += 1", ruby)
        self.assertNotIn("__step_", ruby)
        self.assertIn("y = 0", ruby)
        self.assertIn("x = 0", ruby)
        self.assertIn("i = 0", ruby)
        self.assertIn("if x2 + y2 > 4.0", ruby)
        self.assertIn("if it >= max_iter", ruby)
        self.assertNotIn("if ((x2 + y2) > 4.0)", ruby)
        self.assertNotIn("if (it >= max_iter)", ruby)
        self.assertNotIn("if __pytra_truthy(((x2 + y2) > 4.0))", ruby)
        self.assertNotIn("if __pytra_truthy((it >= max_iter))", ruby)
        self.assertNotIn("r = nil", ruby)
        self.assertNotIn("g = nil", ruby)
        self.assertNotIn("b = nil", ruby)

    def test_sample03_reduces_redundant_parentheses_in_binop_and_conditions(self) -> None:
        sample = find_sample_case("03_julia_set")
        east = load_east(sample, parser_backend="self_hosted")
        ruby = transpile_to_ruby_native(east)
        self.assertIn("zx2 = zx * zx", ruby)
        self.assertIn("zy2 = zy * zy", ruby)
        self.assertIn("if zx2 + zy2 > 4.0", ruby)
        self.assertNotIn("zx2 = (zx * zx)", ruby)
        self.assertNotIn("zy2 = (zy * zy)", ruby)
        self.assertNotIn("if ((zx2 + zy2) > 4.0)", ruby)
        self.assertIn("pixels.concat([r, g, b])", ruby)
        self.assertNotIn("pixels.append(r)", ruby)
        self.assertNotIn("pixels.append(g)", ruby)
        self.assertNotIn("pixels.append(b)", ruby)
        self.assertNotIn("r = 0\n      g = 0\n      b = 0\n      if i >= max_iter", ruby)

    def test_sample18_enumerate_and_slice_are_lowered(self) -> None:
        sample = find_sample_case("18_mini_language_interpreter")
        east = load_east(sample, parser_backend="self_hosted")
        ruby = transpile_to_ruby_native(east)
        self.assertIn("__pytra_enumerate(lines)", ruby)
        self.assertIn("__pytra_slice(source, start, i)", ruby)
        self.assertIn("__pytra_contains(env, stmt.name)", ruby)
        self.assertIn("__pytra_contains(env, node.name)", ruby)
        self.assertIn("__pytra_as_dict(single_char_token_tags).fetch(ch, 0)", ruby)
        self.assertNotIn("single_char_token_tags.get(", ruby)
        self.assertNotIn("stmt.name == env", ruby)
        self.assertNotIn("node.name == env", ruby)
        self.assertIn("__pytra_main()", ruby)

    def test_fixture_dict_literal_entries_are_emitted(self) -> None:
        fixture = find_fixture_case("dict_literal_entries")
        east = load_east(fixture, parser_backend="self_hosted")
        ruby = transpile_to_ruby_native(east)
        self.assertIn('token_tags = { "+" => 1, "=" => 7 }', ruby)
        self.assertNotIn("token_tags = {}", ruby)
        self.assertIn('__pytra_as_dict(token_tags).fetch("=", 0)', ruby)

    def test_sample18_dataclass_ctor_and_self_receiver_are_lowered(self) -> None:
        sample = find_sample_case("18_mini_language_interpreter")
        east = load_east(sample, parser_backend="self_hosted")
        ruby = transpile_to_ruby_native(east)
        self.assertIn("attr_accessor :kind, :text, :pos", ruby)
        self.assertIn("def initialize(kind, text, pos, number_value)", ruby)
        self.assertIn("def initialize(tokens)", ruby)
        self.assertNotIn("def initialize(self_, tokens)", ruby)
        self.assertIn("self.tokens = tokens", ruby)

    def test_png_module_call_uses_runtime_writer(self) -> None:
        sample = find_sample_case("01_mandelbrot")
        east = load_east(sample, parser_backend="self_hosted")
        ruby = transpile_to_ruby_native(east)
        self.assertIn("write_rgb_png(out_path, width, height, pixels)", ruby)
        self.assertNotIn("png.write_rgb_png(", ruby)
        self.assertNotIn("__pytra_noop(out_path, width, height, pixels)", ruby)

    def test_gif_calls_use_runtime_writer_and_keywords(self) -> None:
        sample06 = find_sample_case("06_julia_parameter_sweep")
        east06 = load_east(sample06, parser_backend="self_hosted")
        ruby06 = transpile_to_ruby_native(east06)
        self.assertIn("save_gif(out_path, width, height, frames, julia_palette(), 8, 0)", ruby06)
        self.assertNotIn("__pytra_noop(out_path, width, height, frames, julia_palette())", ruby06)

        sample05 = find_sample_case("05_mandelbrot_zoom")
        east05 = load_east(sample05, parser_backend="self_hosted")
        ruby05 = transpile_to_ruby_native(east05)
        self.assertIn("grayscale_palette()", ruby05)
        self.assertIn("save_gif(out_path, width, height, frames, grayscale_palette(), 5, 0)", ruby05)
        self.assertNotIn("__pytra_noop(out_path, width, height, frames, [])", ruby05)

    def test_ruby_native_emitter_backend_only_ir_fixture_resolves_math_and_path(self) -> None:
        fixture = ROOT / "test" / "ir" / "java_math_path_runtime.east3.json"
        east = json.loads(fixture.read_text(encoding="utf-8"))
        ruby = transpile_to_ruby_native(east)
        self.assertIn('p = Path.new("tmp/a.txt")', ruby)
        self.assertIn("q = p.parent", ruby)
        self.assertIn("n = p.name", ruby)
        self.assertIn("s = p.stem", ruby)
        self.assertIn("x = pyMathSin(pyMathPi())", ruby)

    def test_ruby_emitter_source_has_no_pymath_special_case(self) -> None:
        src = (ROOT / "src" / "backends" / "ruby" / "emitter" / "ruby_native_emitter.py").read_text(encoding="utf-8")
        self.assertNotIn("pyMathPi", src)
        self.assertNotIn("pyMathE", src)
        self.assertNotIn('if _runtime_module_id(expr) != "pytra.std.math":', src)

    def test_fixture_is_instance_uses_ruby_is_a_checks(self) -> None:
        fixture = find_fixture_case("is_instance")
        east = load_east(fixture, parser_backend="self_hosted")
        ruby = transpile_to_ruby_native(east)
        self.assertIn("cat.is_a?(Dog)", ruby)
        self.assertIn("cat.is_a?(Animal)", ruby)

    def test_inheritance_virtual_dispatch_lowers_super_method_without_super_keyword_rename(self) -> None:
        fixture = find_fixture_case("inheritance_virtual_dispatch_multilang")
        east = load_east(fixture, parser_backend="self_hosted")
        ruby = transpile_to_ruby_native(east)
        self.assertIn("self.class.superclass.instance_method(:speak).bind(self).call()", ruby)
        self.assertNotIn("super_()", ruby)

    def test_true_division_binop_uses_pytra_div_helper(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "true_div.py"
            src_py.write_text(
                "def main() -> None:\n"
                "    denom: int = 2\n"
                "    x: float = 1 / denom\n"
                "    print(x)\n",
                encoding="utf-8",
            )
            east = load_east(src_py, parser_backend="self_hosted")
            ruby = transpile_to_ruby_native(east)
        self.assertIn("__pytra_div(1, denom)", ruby)

    def test_true_division_with_nonzero_constant_rhs_uses_direct_slash_fastpath(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "true_div_const_rhs.py"
            src_py.write_text(
                "def main(a: int) -> float:\n"
                "    return a / 2\n",
                encoding="utf-8",
            )
            east = load_east(src_py, parser_backend="self_hosted")
            ruby = transpile_to_ruby_native(east)
        self.assertIn("__pytra_float(a) / 2.0", ruby)
        self.assertNotIn("__pytra_div(a, 2)", ruby)

    def test_ref_container_args_materialize_value_path_with_dup_copy(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "ref_materialize.py"
            src_py.write_text(
                "def f(xs: list[int], ys: dict[str, int]) -> int:\n"
                "    a: list[int] = xs\n"
                "    b: dict[str, int] = ys\n"
                "    a.append(1)\n"
                "    b['k'] = 2\n"
                "    return len(a) + len(b)\n",
                encoding="utf-8",
            )
            east = load_east(src_py, parser_backend="self_hosted")
            ruby = transpile_to_ruby_native(east)
        self.assertIn("a = __pytra_as_list(xs).dup", ruby)
        self.assertIn("b = __pytra_as_dict(ys).dup", ruby)

    def test_sample06_uses_true_division_helper(self) -> None:
        sample = find_sample_case("06_julia_parameter_sweep")
        east = load_east(sample, parser_backend="self_hosted")
        ruby = transpile_to_ruby_native(east)
        self.assertIn("__pytra_div(", ruby)
        self.assertNotIn("(y / (height - 1))", ruby)

    def test_ruby_native_emitter_fail_closed_on_unresolved_stdlib_runtime_call(self) -> None:
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
            transpile_to_ruby_native(east)
        self.assertIn("unresolved stdlib runtime call", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
