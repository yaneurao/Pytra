"""Common smoke tests shared across py2x backend targets.

Per-language smoke suites should keep only language-specific assertions.
Shared CLI/load_east/add-fixture checks belong to this file.
"""

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

from toolchain.compiler.backend_registry import get_backend_spec
from toolchain.compiler.transpile_cli import load_east3_document

TARGET_EXT: dict[str, str] = {
    "cpp": ".cpp",
    "rs": ".rs",
    "cs": ".cs",
    "js": ".js",
    "ts": ".ts",
    "go": ".go",
    "java": ".java",
    "swift": ".swift",
    "kotlin": ".kt",
    "ruby": ".rb",
    "lua": ".lua",
    "scala": ".scala",
    "php": ".php",
    "nim": ".nim",
}

ALL_TARGETS: tuple[str, ...] = tuple(TARGET_EXT.keys())
NON_CPP_TARGETS: tuple[str, ...] = tuple(t for t in ALL_TARGETS if t != "cpp")
STAGE2_REMOVED = "--east-stage 2 is no longer supported; use EAST3 (default)."


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


def run_py2x(target: str, fixture: Path, output_path: Path, *extra_args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    py_path = str(ROOT / "src")
    old = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = py_path if old == "" else py_path + os.pathsep + old
    cmd = [sys.executable, "src/py2x.py", "--target", target, str(fixture), "-o", str(output_path), *extra_args]
    return subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True)


def load_east_for_target(input_path: Path, target: str) -> dict[str, object]:
    doc3 = load_east3_document(
        input_path,
        parser_backend="self_hosted",
        object_dispatch_mode="native",
        east3_opt_level="1",
        east3_opt_pass="",
        dump_east3_before_opt="",
        dump_east3_after_opt="",
        dump_east3_opt_trace="",
        target_lang=target,
    )
    return doc3 if isinstance(doc3, dict) else {}


class Py2XCommonSmokeTest(unittest.TestCase):
    def test_backend_specs_expose_core_hooks_for_non_cpp_targets(self) -> None:
        for target in NON_CPP_TARGETS:
            with self.subTest(target=target):
                spec = get_backend_spec(target)
                self.assertIsInstance(spec, dict)
                self.assertEqual(spec.get("target_lang"), target)
                self.assertEqual(spec.get("extension"), TARGET_EXT[target])
                self.assertTrue(callable(spec.get("lower")))
                self.assertTrue(callable(spec.get("optimizer")))
                self.assertTrue(callable(spec.get("emit")))
                self.assertTrue(callable(spec.get("emit_module")))
                self.assertTrue(callable(spec.get("program_writer")))
                self.assertTrue(callable(spec.get("runtime_hook")))

    def test_cli_smoke_generates_output_for_all_targets(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            for target in ALL_TARGETS:
                with self.subTest(target=target):
                    out = base / f"if_else_{target}{TARGET_EXT[target]}"
                    proc = run_py2x(target, fixture, out)
                    self.assertEqual(proc.returncode, 0, msg=f"{target}\n{proc.stdout}\n{proc.stderr}")
                    self.assertTrue(out.exists(), msg=target)
                    self.assertGreater(len(out.read_text(encoding="utf-8")), 0, msg=target)

    def test_cli_rejects_stage2_mode_for_all_targets(self) -> None:
        fixture = find_fixture_case("if_else")
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            for target in ALL_TARGETS:
                with self.subTest(target=target):
                    out = base / f"if_else_{target}{TARGET_EXT[target]}"
                    proc = run_py2x(target, fixture, out, "--east-stage", "2")
                    self.assertNotEqual(proc.returncode, 0, msg=f"{target}\n{proc.stdout}\n{proc.stderr}")
                    self.assertTrue(
                        STAGE2_REMOVED in proc.stderr
                        or "--east-stage 2 is removed; py2cpp supports only --east-stage 3." in proc.stderr,
                        msg=f"{target}\n{proc.stderr}",
                    )

    def test_load_east_defaults_to_stage3_for_non_cpp_targets(self) -> None:
        fixture = find_fixture_case("for_range")
        for target in NON_CPP_TARGETS:
            with self.subTest(target=target):
                loaded = load_east_for_target(fixture, target)
                self.assertIsInstance(loaded, dict)
                self.assertEqual(loaded.get("kind"), "Module")
                self.assertEqual(loaded.get("east_stage"), 3)

    def test_load_east_from_json_roundtrip_for_non_cpp_targets(self) -> None:
        fixture = find_fixture_case("add")
        for target in NON_CPP_TARGETS:
            with self.subTest(target=target):
                east = load_east_for_target(fixture, target)
                with tempfile.TemporaryDirectory() as td:
                    east_json = Path(td) / f"{target}.east.json"
                    east_json.write_text(json.dumps(east), encoding="utf-8")
                    loaded = load_east_for_target(east_json, target)
                self.assertIsInstance(loaded, dict)
                self.assertEqual(loaded.get("kind"), "Module")
                self.assertEqual(loaded.get("east_stage"), 3)

    def test_add_fixture_transpile_via_py2x_for_non_cpp_targets(self) -> None:
        fixture = find_fixture_case("add")
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            for target in NON_CPP_TARGETS:
                with self.subTest(target=target):
                    out = base / f"add_{target}{TARGET_EXT[target]}"
                    proc = run_py2x(target, fixture, out)
                    self.assertEqual(proc.returncode, 0, msg=f"{target}\n{proc.stdout}\n{proc.stderr}")
                    txt = out.read_text(encoding="utf-8")
                    self.assertIn("add", txt, msg=target)


if __name__ == "__main__":
    unittest.main()
