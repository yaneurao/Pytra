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

from backends.nim.emitter import load_nim_profile, transpile_to_nim, transpile_to_nim_native
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

    def test_nim_native_emitter_backend_only_ir_fixture_resolves_math_and_path(self) -> None:
        fixture = ROOT / "test" / "ir" / "java_math_path_runtime.east3.json"
        east = json.loads(fixture.read_text(encoding="utf-8"))
        nim = transpile_to_nim_native(east)
        self.assertIn('var p = Path("tmp/a.txt")', nim)
        self.assertIn("var q = p.parent", nim)
        self.assertIn("n = p.name", nim)
        self.assertIn("s = p.stem", nim)
        self.assertIn("x = math.sin(PI)", nim)

    def test_nim_emitter_source_has_no_owner_math_special_case(self) -> None:
        src = (ROOT / "src" / "backends" / "nim" / "emitter" / "nim_native_emitter.py").read_text(encoding="utf-8")
        self.assertNotIn('owner == "math"', src)
        self.assertNotIn("owner == 'math'", src)

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

if __name__ == "__main__":
    unittest.main()
