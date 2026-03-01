"""py2rb (EAST based) smoke tests."""

from __future__ import annotations

import json
import os
import shutil
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

from src.py2rb import load_east, load_ruby_profile, transpile_to_ruby, transpile_to_ruby_native
from src.pytra.compiler.east_parts.core import convert_path
from comment_fidelity import assert_no_generated_comments, assert_sample01_module_comments


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

    def test_transpile_add_fixture_uses_native_output(self) -> None:
        fixture = find_fixture_case("add")
        east = load_east(fixture, parser_backend="self_hosted")
        ruby = transpile_to_ruby(east)
        assert_no_generated_comments(self, ruby)
        self.assertIn('require_relative "py_runtime"', ruby)
        self.assertIn("def add(a, b)", ruby)
        self.assertNotIn("def __pytra_truthy(v)", ruby)
        self.assertNotIn('exec.Command("node"', ruby)

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

    def test_load_east_from_json(self) -> None:
        fixture = find_fixture_case("add")
        east = convert_path(fixture)
        with tempfile.TemporaryDirectory() as td:
            east_json = Path(td) / "case.east.json"
            east_json.write_text(json.dumps(east), encoding="utf-8")
            loaded = load_east(east_json)
            ruby = transpile_to_ruby_native(loaded)
        self.assertIn("def add(a, b)", ruby)

    def test_load_east_defaults_to_stage3_entry_and_returns_east3_shape(self) -> None:
        fixture = find_fixture_case("for_range")
        loaded = load_east(fixture, parser_backend="self_hosted")
        self.assertIsInstance(loaded, dict)
        self.assertEqual(loaded.get("kind"), "Module")
        self.assertEqual(loaded.get("east_stage"), 3)

    def test_cli_smoke_defaults_to_native_without_sidecar(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_rb = Path(td) / "if_else.rb"
            out_js = Path(td) / "if_else.js"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2rb.py", str(fixture), "-o", str(out_rb)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertTrue(out_rb.exists())
            self.assertFalse(out_js.exists())
            txt = out_rb.read_text(encoding="utf-8")
            self.assertNotIn("Auto-generated Pytra Ruby native source from EAST3.", txt)
            self.assertIn('require_relative "py_runtime"', txt)
            self.assertNotIn("def __pytra_truthy(v)", txt)
            runtime_rb = Path(td) / "py_runtime.rb"
            self.assertTrue(runtime_rb.exists())
            runtime_txt = runtime_rb.read_text(encoding="utf-8")
            self.assertIn("def __pytra_truthy(v)", runtime_txt)

    def test_cli_rejects_stage2_compat_mode(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            out_rb = Path(td) / "if_else.rb"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            proc = subprocess.run(
                [sys.executable, "src/py2rb.py", str(fixture), "-o", str(out_rb), "--east-stage", "2"],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")
            self.assertIn("--east-stage 2 is no longer supported; use EAST3 (default).", proc.stderr)

    def test_py2rb_does_not_import_src_common(self) -> None:
        src = (ROOT / "src" / "py2rb.py").read_text(encoding="utf-8")
        self.assertNotIn("src.common", src)
        self.assertNotIn("from common.", src)

    def test_ruby_runtime_source_path_is_migrated(self) -> None:
        runtime_path = ROOT / "src" / "runtime" / "ruby" / "pytra" / "py_runtime.rb"
        legacy_path = ROOT / "src" / "ruby_module" / "py_runtime.rb"
        self.assertTrue(runtime_path.exists())
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
                [sys.executable, "src/py2rb.py", str(fixture), "-o", str(out_rb)],
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

    def test_sample18_enumerate_and_slice_are_lowered(self) -> None:
        sample = find_sample_case("18_mini_language_interpreter")
        east = load_east(sample, parser_backend="self_hosted")
        ruby = transpile_to_ruby_native(east)
        self.assertIn("__pytra_enumerate(lines)", ruby)
        self.assertIn("__pytra_slice(source, start, i)", ruby)
        self.assertIn("__pytra_contains(env, stmt.name)", ruby)
        self.assertIn("__pytra_contains(env, node.name)", ruby)
        self.assertNotIn("stmt.name == env", ruby)
        self.assertNotIn("node.name == env", ruby)
        self.assertIn("__pytra_main()", ruby)

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
                "    x: float = 1 / 2\n"
                "    print(x)\n",
                encoding="utf-8",
            )
            east = load_east(src_py, parser_backend="self_hosted")
            ruby = transpile_to_ruby_native(east)
        self.assertIn("__pytra_div(1, 2)", ruby)
        self.assertNotIn("(1 / 2)", ruby)

    def test_sample06_uses_true_division_helper(self) -> None:
        sample = find_sample_case("06_julia_parameter_sweep")
        east = load_east(sample, parser_backend="self_hosted")
        ruby = transpile_to_ruby_native(east)
        self.assertIn("__pytra_div(", ruby)
        self.assertNotIn("(y / (height - 1))", ruby)


if __name__ == "__main__":
    unittest.main()
