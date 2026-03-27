from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from toolchain2.compile.lower import lower_east2_to_east3
from toolchain2.emit.cpp.emitter import emit_cpp_module
from toolchain2.emit.go.emitter import emit_go_module
from toolchain2.parse.py.parser import parse_python_source
from toolchain2.resolve.py.builtin_registry import load_builtin_registry
from toolchain2.resolve.py.resolver import resolve_east1_to_east2


ROOT = Path(__file__).resolve().parents[3]


def _load_registry():
    return load_builtin_registry(
        ROOT / "test" / "include" / "east1" / "py" / "built_in" / "builtins.py.east1",
        ROOT / "test" / "include" / "east1" / "py" / "built_in" / "containers.py.east1",
        ROOT / "test" / "include" / "east1" / "py" / "std",
    )


def _build_east3(source: str, *, target_language: str) -> dict:
    east2 = parse_python_source(source, "<common-renderer-smoke>").to_jv()
    resolve_east1_to_east2(east2, registry=_load_registry())
    east3 = lower_east2_to_east3(east2, target_language=target_language)
    meta = east3.setdefault("meta", {})
    assert isinstance(meta, dict)
    meta["emit_context"] = {"module_id": "app", "is_entry": True}
    return east3


SOURCE = """
def f() -> int:
    x = 1
    if x < 2:
        x = x + 1
    while x < 3:
        x = x + 1
    return x
"""


class CommonRendererCompileSmokeTests(unittest.TestCase):
    def test_go_emitted_common_renderer_shapes_compile(self) -> None:
        east3 = _build_east3(SOURCE, target_language="go")
        go_code = emit_go_module(east3)

        with tempfile.TemporaryDirectory() as tmp:
            go_path = Path(tmp) / "app.go"
            go_path.write_text(go_code, encoding="utf-8")
            proc = subprocess.run(
                ["go", "build", str(go_path)],
                cwd=tmp,
                capture_output=True,
                text=True,
            )

        self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")

    def test_cpp_emitted_common_renderer_shapes_compile(self) -> None:
        east3 = _build_east3(SOURCE, target_language="cpp")
        cpp_code = emit_cpp_module(east3)

        with tempfile.TemporaryDirectory() as tmp:
            cpp_path = Path(tmp) / "app.cpp"
            obj_path = Path(tmp) / "app.o"
            cpp_path.write_text(cpp_code, encoding="utf-8")
            proc = subprocess.run(
                [
                    "g++",
                    "-std=c++20",
                    "-I",
                    str(ROOT / "src" / "runtime" / "cpp"),
                    "-c",
                    str(cpp_path),
                    "-o",
                    str(obj_path),
                ],
                cwd=tmp,
                capture_output=True,
                text=True,
            )

        self.assertEqual(proc.returncode, 0, msg=f"{proc.stdout}\n{proc.stderr}")


if __name__ == "__main__":
    unittest.main()
