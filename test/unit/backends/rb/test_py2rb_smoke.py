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

from backends.ruby.emitter import load_ruby_profile, transpile_to_ruby, transpile_to_ruby_native
from toolchain.compiler.transpile_cli import load_east3_document
from src.toolchain.compiler.east_parts.core import convert_path
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

    def test_ruby_native_emitter_skeleton_handles_module_function_class(self) -> None:
        fixture = find_fixture_case("inheritance")
        east = load_east(fixture, parser_backend="self_hosted")
        ruby = transpile_to_ruby_native(east)
        self.assertIn("class Animal", ruby)
        self.assertIn("class Dog < Animal", ruby)
        self.assertIn("def _case_main()", ruby)

    def test_module_leading_comments_are_emitted(self) -> None:
        sample = ROOT / "sample" / "py" / "01_mandelbrot.py"
        east = load_east(sample, parser_backend="self_hosted")
        ruby = transpile_to_ruby_native(east)
        assert_no_generated_comments(self, ruby)
        assert_sample01_module_comments(self, ruby, prefix="#")

    def test_py2rb_does_not_import_src_common(self) -> None:
        src = (ROOT / "src" / "py2x.py").read_text(encoding="utf-8")
        self.assertNotIn("src.common", src)
        self.assertNotIn("from common.", src)

    def test_ruby_runtime_source_path_is_migrated(self) -> None:
        runtime_path = ROOT / "src" / "runtime" / "ruby" / "pytra-core" / "built_in" / "py_runtime.rb"
        image_runtime = ROOT / "src" / "runtime" / "ruby" / "pytra-gen" / "utils" / "image_runtime.rb"
        legacy_path = ROOT / "src" / "ruby_module" / "py_runtime.rb"
        self.assertTrue(runtime_path.exists())
        self.assertTrue(image_runtime.exists())
        self.assertFalse(legacy_path.exists())

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
                [sys.executable, "src/py2x.py", "--target", "ruby", str(fixture), "-o", str(out_rb)],
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


if __name__ == "__main__":
    unittest.main()
