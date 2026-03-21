"""py2julia (EAST based) smoke tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from toolchain.emit.julia.emitter import transpile_to_julia, transpile_to_julia_native
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
        target_lang="julia",
    )
    return doc3 if isinstance(doc3, dict) else {}


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


class Py2JuliaSmokeTest(unittest.TestCase):
    def test_julia_runtime_exists(self) -> None:
        runtime_path = ROOT / "src" / "runtime" / "julia" / "built_in" / "py_runtime.jl"
        self.assertTrue(runtime_path.exists())

    def test_transpile_simple_add(self) -> None:
        east_doc = load_east(find_fixture_case("add"))
        source = transpile_to_julia_native(east_doc)
        self.assertIsInstance(source, str)
        self.assertIn("function", source)
        self.assertIn("end", source)

    def test_transpile_fib(self) -> None:
        east_doc = load_east(find_fixture_case("fib"))
        source = transpile_to_julia_native(east_doc)
        self.assertIn("function", source)
        self.assertIn("if", source)

    def test_transpile_if_else(self) -> None:
        east_doc = load_east(find_fixture_case("if_else"))
        source = transpile_to_julia_native(east_doc)
        self.assertIn("if", source)
        self.assertIn("end", source)

    def test_transpile_for_loop(self) -> None:
        east_doc = load_east(find_fixture_case("for_range"))
        source = transpile_to_julia_native(east_doc)
        self.assertIn("for", source)
        self.assertIn("end", source)

    def test_transpile_loop(self) -> None:
        east_doc = load_east(find_fixture_case("loop"))
        source = transpile_to_julia_native(east_doc)
        self.assertIn("for", source)
        self.assertIn("end", source)

    def test_transpile_compare(self) -> None:
        east_doc = load_east(find_fixture_case("compare"))
        source = transpile_to_julia_native(east_doc)
        self.assertIsInstance(source, str)

    def test_transpile_dict_literal_entries(self) -> None:
        east_doc = load_east(find_fixture_case("dict_literal_entries"))
        source = transpile_to_julia_native(east_doc)
        self.assertIn("Dict", source)

    def test_transpile_class(self) -> None:
        east_doc = load_east(find_fixture_case("class_body_pass"))
        source = transpile_to_julia_native(east_doc)
        self.assertIn("mutable struct", source)
        self.assertIn("end", source)

    def test_transpile_assign(self) -> None:
        east_doc = load_east(find_fixture_case("assign"))
        source = transpile_to_julia_native(east_doc)
        self.assertIn("=", source)

    def test_transpile_to_julia_api_compat(self) -> None:
        """transpile_to_julia is an alias for transpile_to_julia_native."""
        east_doc = load_east(find_fixture_case("add"))
        source = transpile_to_julia(east_doc)
        self.assertIsInstance(source, str)
        self.assertIn("function", source)


if __name__ == "__main__":
    unittest.main()
