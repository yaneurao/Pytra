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

from backends.php.emitter import load_php_profile, transpile_to_php, transpile_to_php_native
from toolchain.compiler.transpile_cli import load_east3_document


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

    def test_transpile_for_range_fixture_contains_static_for(self) -> None:
        fixture = find_fixture_case("for_range")
        east = load_east(fixture, parser_backend="self_hosted")
        php = transpile_to_php_native(east)
        self.assertIn("function sum_range_29($n)", php)
        self.assertIn("for ($i = 0; $i < $n; $i += 1)", php)
        self.assertIn("$total += $i;", php)

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
        self.assertIn("__pytra_save_gif($out_path, $width, $height, $frames, grayscale_palette(), 5, 0);", php)

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
        self.assertIn("__pytra_save_gif(\"x.gif\", 1, 1, $frames, grayscale_palette(), 4, 0);", php)
        self.assertNotIn("__pytra_save_gif(\"x.gif\", 1, 1, $frames, grayscale_palette(), 0, 4);", php)

    def test_transpile_sample16_bitwise_ops_are_preserved(self) -> None:
        sample = find_sample_case("16_glass_sculpture_chaos")
        east = load_east(sample, parser_backend="self_hosted")
        php = transpile_to_php_native(east)
        self.assertIn("($i >> 5)", php)
        self.assertIn("($i & 3)", php)
        self.assertIn("(($rr >> 5) << 5)", php)

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
