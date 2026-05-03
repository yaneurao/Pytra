from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from toolchain.compile.lower import lower_east2_to_east3
from toolchain.emit.dart.emitter import emit_dart_module
from toolchain.parse.py.parser import parse_python_source
from toolchain.resolve.py.builtin_registry import load_builtin_registry
from toolchain.resolve.py.resolver import resolve_east1_to_east2


ROOT = Path(__file__).resolve().parents[3]


def _load_registry():
    return load_builtin_registry(
        ROOT / "test" / "include" / "east1" / "py" / "built_in" / "builtins.py.east1",
        ROOT / "test" / "include" / "east1" / "py" / "built_in" / "containers.py.east1",
        ROOT / "test" / "include" / "east1" / "py" / "std",
    )


def _build_east3(source: str) -> dict:
    east2 = parse_python_source(source, "<dart-smoke>").to_jv()
    resolve_east1_to_east2(east2, registry=_load_registry())
    east3 = lower_east2_to_east3(east2, target_language="dart")
    meta = east3.setdefault("meta", {})
    assert isinstance(meta, dict)
    meta["emit_context"] = {"module_id": "app", "root_rel_prefix": "./", "is_entry": True}
    return east3


def _assert_dart_runs(source: str) -> str:
    if shutil.which("dart") is None:
        raise unittest.SkipTest("dart is not installed")
    east3 = _build_east3(source)
    dart_code = emit_dart_module(east3)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        app_path = tmp_path / "app.dart"
        runtime_root = ROOT / "src" / "runtime" / "dart"
        built_in_dir = tmp_path / "built_in"
        std_dir = tmp_path / "std"
        built_in_dir.mkdir(parents=True, exist_ok=True)
        std_dir.mkdir(parents=True, exist_ok=True)
        for src in runtime_root.joinpath("built_in").glob("*.dart"):
            shutil.copy2(src, built_in_dir / src.name)
        for src in runtime_root.joinpath("std").glob("*.dart"):
            shutil.copy2(src, std_dir / src.name)
        app_path.write_text(dart_code, encoding="utf-8")
        run = subprocess.run(
            ["dart", "run", str(app_path)],
            cwd=tmp,
            capture_output=True,
            text=True,
        )
    if run.returncode != 0:
        raise AssertionError(f"{run.stdout}\n{run.stderr}")
    return run.stdout


class DartEmitterSmokeTest(unittest.TestCase):
    def test_dart_emitter_does_not_import_swift_emitter(self) -> None:
        emitter_source = (ROOT / "src" / "toolchain" / "emit" / "dart" / "emitter.py").read_text(encoding="utf-8")
        self.assertNotIn("toolchain.emit.swift.emitter", emitter_source)

    def test_emit_add_function(self) -> None:
        source = """
def add(a: int, b: int) -> int:
    return a + b
"""
        east3 = _build_east3(source)
        code = emit_dart_module(east3)
        self.assertIn("int add(", code)
        self.assertIn("return pytraInt((a + b));", code)

    def test_emit_if_else(self) -> None:
        source = """
def f(x: int) -> int:
    if x < 1:
        return 10
    return 20
"""
        east3 = _build_east3(source)
        code = emit_dart_module(east3)
        self.assertIn("if (((x < 1)))", code)
        self.assertIn("return 10;", code)

    def test_emit_and_run_print(self) -> None:
        out = _assert_dart_runs(
            """
def f() -> int:
    return 3

if __name__ == "__main__":
    print(f())
"""
        )
        self.assertEqual(out.strip(), "3")
