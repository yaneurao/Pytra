"""py2go (EAST based) smoke tests."""

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

from backends.go.emitter import load_go_profile, transpile_to_go, transpile_to_go_native
from toolchain.compiler.transpile_cli import load_east3_document
from src.toolchain.ir.core import convert_path
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
        target_lang="go",
    )
    return doc3 if isinstance(doc3, dict) else {}


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


class Py2GoSmokeTest(unittest.TestCase):
    def test_load_go_profile_contains_core_sections(self) -> None:
        profile = load_go_profile()
        self.assertIn("types", profile)
        self.assertIn("operators", profile)
        self.assertIn("syntax", profile)
        self.assertIn("runtime_calls", profile)

    def test_go_native_emitter_skeleton_handles_module_function_class(self) -> None:
        fixture = find_fixture_case("inheritance")
        east = load_east(fixture, parser_backend="self_hosted")
        go = transpile_to_go_native(east)
        self.assertIn("package main", go)
        self.assertIn("type Animal struct {", go)
        self.assertIn("type Dog struct {", go)
        self.assertIn("func _case_main()", go)
        self.assertNotIn('    "math"', go)
        self.assertNotIn("var _ = math.Pi", go)

    def test_inheritance_virtual_dispatch_fixture_uses_interface_typed_base_dispatch(self) -> None:
        fixture = find_fixture_case("inheritance_virtual_dispatch_multilang")
        east = load_east(fixture, parser_backend="self_hosted")
        go = transpile_to_go_native(east)
        self.assertIn("type AnimalLike interface {", go)
        self.assertIn("func call_via_animal(a AnimalLike) string {", go)
        self.assertIn("var a AnimalLike = NewLoudDog()", go)
        self.assertIn('return __pytra_str(("loud-" + self.Dog.speak()))', go)

    def test_go_native_emitter_routes_math_calls_via_runtime_helpers(self) -> None:
        sample = ROOT / "sample" / "py" / "06_julia_parameter_sweep.py"
        east = load_east(sample, parser_backend="self_hosted")
        go = transpile_to_go_native(east)
        self.assertIn("pyMathPi()", go)
        self.assertIn("pyMathCos(__pytra_float(angle))", go)
        self.assertIn("pyMathSin(__pytra_float(angle))", go)
        self.assertNotIn("math.", go)
        self.assertNotIn("var _ = math.Pi", go)

    def test_go_emitter_source_has_no_owner_math_special_case(self) -> None:
        src = (ROOT / "src" / "backends" / "go" / "emitter" / "go_native_emitter.py").read_text(encoding="utf-8")
        self.assertNotIn('owner == "math"', src)
        self.assertNotIn("owner == 'math'", src)
        self.assertNotIn('runtime_symbol.startswith("pyMath")', src)
        self.assertNotIn("runtime_symbol.startswith('pyMath')", src)
        self.assertNotIn('runtime_symbol == "pyMathPi"', src)
        self.assertNotIn('runtime_symbol == "pyMathE"', src)
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

    def test_go_native_emitter_maps_json_module_calls_to_runtime_helpers(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "json_calls.py"
            src.write_text(
                "import json\n"
                "def roundtrip(v: dict[str, int]) -> dict[str, int]:\n"
                "    s = json.dumps(v)\n"
                "    return json.loads(s)\n",
                encoding="utf-8",
            )
            east = load_east(src, parser_backend="self_hosted")
            go = transpile_to_go_native(east)
        self.assertIn("pyJsonDumps(v)", go)
        self.assertIn("pyJsonLoads(s)", go)

    def test_go_native_emitter_save_gif_keyword_order_uses_adapter_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "gif_case.py"
            src.write_text(
                "from pytra.utils.gif import save_gif, grayscale_palette\n\n"
                "def main(frames: list[bytes]) -> None:\n"
                "    save_gif('x.gif', 1, 1, frames, grayscale_palette(), loop=0, delay_cs=4)\n",
                encoding="utf-8",
            )
            east = load_east(src, parser_backend="self_hosted")
            go = transpile_to_go_native(east)
        self.assertIn(
            "pySaveGIF(\"x.gif\", int64(1), int64(1), frames, pyGrayscalePalette(), int64(4), int64(0))",
            go,
        )
        self.assertNotIn(
            "pySaveGIF(\"x.gif\", int64(1), int64(1), frames, pyGrayscalePalette(), int64(0), int64(4))",
            go,
        )

    def test_go_native_emitter_uses_runtime_path_wrapper(self) -> None:
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
            go = transpile_to_go_native(east)
        self.assertIn("var p *Path = __pytra_as_Path(NewPath(\"tmp/a.txt\"))", go)
        self.assertIn("p.parent.mkdir(true, true)", go)
        self.assertIn("return __pytra_truthy(p.exists())", go)

    def test_go_native_emitter_backend_only_ir_fixture_resolves_math_and_path(self) -> None:
        fixture = ROOT / "test" / "ir" / "java_math_path_runtime.east3.json"
        east = load_east(fixture, parser_backend="self_hosted")
        go = transpile_to_go_native(east)
        self.assertIn("var p *Path = __pytra_as_Path(NewPath(\"tmp/a.txt\"))", go)
        self.assertIn("var q *Path = __pytra_as_Path(p.parent)", go)
        self.assertIn("var n string = __pytra_str(p.name)", go)
        self.assertIn("var s string = __pytra_str(p.stem)", go)
        self.assertIn("var x float64 = pyMathSin(__pytra_float(pyMathPi()))", go)

    def test_go_native_emitter_fail_closed_on_unresolved_stdlib_runtime_call(self) -> None:
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
            transpile_to_go_native(east)
        self.assertIn("unresolved stdlib runtime", str(cm.exception))

    def test_go_native_emitter_fail_closed_on_unresolved_resolved_runtime_call(self) -> None:
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
            transpile_to_go_native(east)
        self.assertIn("unresolved stdlib runtime", str(cm.exception))

    def test_module_leading_comments_are_emitted(self) -> None:
        sample = ROOT / "sample" / "py" / "01_mandelbrot.py"
        east = load_east(sample, parser_backend="self_hosted")
        go = transpile_to_go_native(east)
        assert_no_generated_comments(self, go)
        assert_sample01_module_comments(self, go, prefix="//")

    def test_sample01_reduces_redundant_numeric_cast_chains(self) -> None:
        sample = ROOT / "sample" / "py" / "01_mandelbrot.py"
        east = load_east(sample, parser_backend="self_hosted")
        go = transpile_to_go_native(east)
        self.assertNotIn("__pytra_float(__pytra_float(", go)
        self.assertNotIn("__pytra_int(__pytra_int(", go)

    def test_sample01_prefers_canonical_range_loops_for_step_one(self) -> None:
        sample = ROOT / "sample" / "py" / "01_mandelbrot.py"
        east = load_east(sample, parser_backend="self_hosted")
        go = transpile_to_go_native(east)
        self.assertIn("for i := int64(0); i < max_iter; i += 1 {", go)
        self.assertNotIn(">= 0 && i <", go)

    def test_image_writers_use_native_runtime_hooks_not_noop(self) -> None:
        sample_png = ROOT / "sample" / "py" / "01_mandelbrot.py"
        east_png = load_east(sample_png, parser_backend="self_hosted")
        go_png = transpile_to_go_native(east_png)
        self.assertIn("pyWriteRGBPNG(out_path, width, height, pixels)", go_png)
        self.assertNotIn("__pytra_noop(out_path, width, height, pixels)", go_png)
        self.assertIn("pixels = append(pixels, r)", go_png)
        self.assertNotIn("append(__pytra_as_list(pixels), r)", go_png)

        sample_gif = ROOT / "sample" / "py" / "05_mandelbrot_zoom.py"
        east_gif = load_east(sample_gif, parser_backend="self_hosted")
        go_gif = transpile_to_go_native(east_gif)
        self.assertIn("pyGrayscalePalette()", go_gif)
        self.assertIn("pySaveGIF(", go_gif)
        self.assertNotIn("__pytra_noop(out_path, width, height, frames", go_gif)

    def test_ref_container_args_materialize_value_path_with_copy_expr(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "ref_container_args.py"
            src.write_text(
                "def f(xs: list[int], ys: dict[str, int]) -> int:\n"
                "    a: list[int] = xs\n"
                "    b: dict[str, int] = ys\n"
                "    a.append(1)\n"
                "    return len(a) + len(b)\n",
                encoding="utf-8",
            )
            east = load_east(src, parser_backend="self_hosted")
            go = transpile_to_go_native(east)
        self.assertIn("var a []any = __pytra_as_list(append([]any(nil), xs...))", go)
        self.assertIn("var b map[any]any = __pytra_as_dict((func() map[any]any {", go)
        self.assertNotIn("var a []any = __pytra_as_list(xs)", go)
        self.assertNotIn("var b map[any]any = __pytra_as_dict(ys)", go)

    def test_py2go_does_not_import_src_common(self) -> None:
        src = (ROOT / "src" / "py2x.py").read_text(encoding="utf-8")
        self.assertNotIn("src.common", src)
        self.assertNotIn("from common.", src)

    def test_go_runtime_source_path_is_migrated(self) -> None:
        runtime_path = ROOT / "src" / "runtime" / "go" / "pytra" / "py_runtime.go"
        legacy_path = ROOT / "src" / "go_module" / "py_runtime.go"
        self.assertTrue(runtime_path.exists())
        self.assertFalse(legacy_path.exists())


if __name__ == "__main__":
    unittest.main()
