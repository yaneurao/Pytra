"""py2dart (EAST based) smoke tests."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
if str(ROOT / "test" / "unit") not in sys.path:
    sys.path.insert(0, str(ROOT / "test" / "unit"))
if str(ROOT / "test" / "unit" / "backends") not in sys.path:
    sys.path.insert(0, str(ROOT / "test" / "unit" / "backends"))

from toolchain.emit.dart.emitter import load_dart_profile, transpile_to_dart, transpile_to_dart_native
from toolchain.misc.transpile_cli import load_east3_document


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
        target_lang="dart",
    )
    return doc3 if isinstance(doc3, dict) else {}


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


class Py2DartSmokeTest(unittest.TestCase):
    def test_load_dart_profile_contains_core_sections(self) -> None:
        profile = load_dart_profile()
        self.assertIn("types", profile)
        self.assertIn("operators", profile)
        self.assertIn("syntax", profile)
        self.assertIn("runtime_calls", profile)

    def test_dart_runtime_exists(self) -> None:
        runtime_path = ROOT / "src" / "runtime" / "dart" / "built_in" / "py_runtime.dart"
        self.assertTrue(runtime_path.exists())

    def test_transpile_add(self) -> None:
        east = load_east(find_fixture_case("add"))
        source = transpile_to_dart_native(east)
        self.assertIn("int add(", source)
        self.assertIn("+", source)

    def test_transpile_if_else(self) -> None:
        east = load_east(find_fixture_case("if_else"))
        source = transpile_to_dart_native(east)
        self.assertIn("if (", source)
        self.assertIn("} else {", source)

    def test_transpile_for_range(self) -> None:
        east = load_east(find_fixture_case("for_range"))
        source = transpile_to_dart_native(east)
        self.assertIn("for (var", source)

    def test_transpile_api_compat(self) -> None:
        east = load_east(find_fixture_case("add"))
        source = transpile_to_dart(east)
        self.assertIn("+", source)

    def test_transpile_inheritance(self) -> None:
        east = load_east(find_fixture_case("inheritance"))
        source = transpile_to_dart_native(east)
        self.assertIn("class ", source)
        self.assertIn("extends", source)


if __name__ == "__main__":
    unittest.main()
