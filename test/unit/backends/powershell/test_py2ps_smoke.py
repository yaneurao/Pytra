"""py2powershell (EAST based) smoke tests."""

# Language-specific smoke suite.
# Shared py2x target-parameterized checks live in test_py2x_smoke_common.py.

from __future__ import annotations

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

from toolchain.emit.powershell.emitter import load_powershell_profile, transpile_to_powershell
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
        target_lang="js",
    )
    return doc3 if isinstance(doc3, dict) else {}


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


class Py2PowerShellSmokeTest(unittest.TestCase):
    def test_load_powershell_profile_contains_core_sections(self) -> None:
        profile = load_powershell_profile()
        self.assertIn("types", profile)
        self.assertIn("operators", profile)
        self.assertIn("syntax", profile)
        self.assertIn("runtime_calls", profile)

    def test_bitwise_invert_basic_transpiles(self) -> None:
        fixture = find_fixture_case("bitwise_invert_basic")
        east = load_east(fixture, parser_backend="self_hosted")
        ps = transpile_to_powershell(east)
        self.assertTrue(ps.strip())
        self.assertIn("#Requires -Version 5.1", ps)

    def test_output_contains_powershell_header(self) -> None:
        fixture = find_fixture_case("bitwise_invert_basic")
        east = load_east(fixture, parser_backend="self_hosted")
        ps = transpile_to_powershell(east)
        self.assertIn("Set-StrictMode -Version Latest", ps)
        self.assertIn("$ErrorActionPreference", ps)
        self.assertIn("py_runtime.ps1", ps)

    def test_secondary_bundle_representative_fixtures_transpile_for_powershell(self) -> None:
        for stem in (
            "tuple_assign",
            "lambda_basic",
            "comprehension",
            "for_range",
            "try_raise",
            "enumerate_basic",
            "is_instance",
        ):
            with self.subTest(stem=stem):
                fixture = find_fixture_case(stem)
                east = load_east(fixture, parser_backend="self_hosted")
                ps = transpile_to_powershell(east)
                self.assertTrue(ps.strip())

    def test_function_emits_powershell_function_keyword(self) -> None:
        fixture = find_fixture_case("lambda_basic")
        east = load_east(fixture, parser_backend="self_hosted")
        ps = transpile_to_powershell(east)
        self.assertIn("function ", ps)

    def test_for_loop_emits_powershell_for_or_foreach(self) -> None:
        fixture = find_fixture_case("for_range")
        east = load_east(fixture, parser_backend="self_hosted")
        ps = transpile_to_powershell(east)
        has_for = "for (" in ps or "foreach (" in ps
        self.assertTrue(has_for, "Expected 'for (' or 'foreach (' in PowerShell output")

    def test_if_emits_powershell_if_block(self) -> None:
        fixture = find_fixture_case("is_instance")
        east = load_east(fixture, parser_backend="self_hosted")
        ps = transpile_to_powershell(east)
        self.assertIn("if (", ps)

    def test_cli_transpile_powershell_via_py2x(self) -> None:
        fixture = find_fixture_case("class_body_pass")
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "test.ps1"
            env = dict(os.environ)
            py_path = str(ROOT / "src")
            old = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
            cmd = [
                sys.executable, str(ROOT / "src" / "py2x.py"),
                "--target", "powershell",
                str(fixture),
                "-o", str(out),
            ]
            proc = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)
            self.assertEqual(proc.returncode, 0, msg=f"stdout={proc.stdout}\nstderr={proc.stderr}")
            text = out.read_text(encoding="utf-8")
            self.assertIn("#Requires -Version 5.1", text)


if __name__ == "__main__":
    unittest.main()
