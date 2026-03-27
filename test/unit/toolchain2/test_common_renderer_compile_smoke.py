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


def _emit_context_meta() -> dict[str, object]:
    return {"emit_context": {"module_id": "app", "is_entry": True}}


SOURCE = """
def f() -> int:
    x = 1
    if x < 2:
        x = x + 1
    while x < 3:
        x = x + 1
    return x
"""

BOOL_SOURCE = """
def f(a: bool, b: bool) -> int:
    x = 0
    if not a and b:
        x = 1
    else:
        pass
    return x
"""

COMPARE_SOURCE = """
def f(x: int, y: int) -> int:
    z = x + y
    if z > 3 and x != y:
        return z - 1
    return z
"""

DOCSTRING_SOURCE = '''
def f() -> int:
    "common renderer docstring"
    x = 1
    if x == 1:
        x = x + 2
    return x
'''


def _assert_go_compiles(source: str) -> None:
    east3 = _build_east3(source, target_language="go")
    go_code = emit_go_module(east3)

    with tempfile.TemporaryDirectory() as tmp:
        go_path = Path(tmp) / "app.go"
        runtime_path = ROOT / "src" / "runtime" / "go" / "built_in" / "py_runtime.go"
        bundled_runtime = Path(tmp) / "py_runtime.go"
        go_path.write_text(go_code, encoding="utf-8")
        bundled_runtime.write_text(runtime_path.read_text(encoding="utf-8"), encoding="utf-8")
        proc = subprocess.run(
            ["go", "build", str(bundled_runtime), str(go_path)],
            cwd=tmp,
            capture_output=True,
            text=True,
        )

    if proc.returncode != 0:
        raise AssertionError(f"{proc.stdout}\n{proc.stderr}")


def _assert_cpp_compiles(source: str) -> None:
    east3 = _build_east3(source, target_language="cpp")
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

    if proc.returncode != 0:
        raise AssertionError(f"{proc.stdout}\n{proc.stderr}")


def _assert_go_doc_compiles(doc: dict) -> None:
    go_code = emit_go_module(doc)

    with tempfile.TemporaryDirectory() as tmp:
        go_path = Path(tmp) / "app.go"
        runtime_path = ROOT / "src" / "runtime" / "go" / "built_in" / "py_runtime.go"
        bundled_runtime = Path(tmp) / "py_runtime.go"
        go_path.write_text(go_code, encoding="utf-8")
        bundled_runtime.write_text(runtime_path.read_text(encoding="utf-8"), encoding="utf-8")
        proc = subprocess.run(
            ["go", "build", str(bundled_runtime), str(go_path)],
            cwd=tmp,
            capture_output=True,
            text=True,
        )

    if proc.returncode != 0:
        raise AssertionError(f"{proc.stdout}\n{proc.stderr}")


def _assert_cpp_doc_compiles(doc: dict) -> None:
    cpp_code = emit_cpp_module(doc)

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

    if proc.returncode != 0:
        raise AssertionError(f"{proc.stdout}\n{proc.stderr}")


class CommonRendererCompileSmokeTests(unittest.TestCase):
    def test_go_emitted_common_renderer_shapes_compile(self) -> None:
        _assert_go_compiles(SOURCE)

    def test_cpp_emitted_common_renderer_shapes_compile(self) -> None:
        _assert_cpp_compiles(SOURCE)

    def test_go_emitted_bool_common_renderer_shapes_compile(self) -> None:
        _assert_go_compiles(BOOL_SOURCE)

    def test_cpp_emitted_bool_common_renderer_shapes_compile(self) -> None:
        _assert_cpp_compiles(BOOL_SOURCE)

    def test_go_emitted_compare_common_renderer_shapes_compile(self) -> None:
        _assert_go_compiles(COMPARE_SOURCE)

    def test_cpp_emitted_compare_common_renderer_shapes_compile(self) -> None:
        _assert_cpp_compiles(COMPARE_SOURCE)

    def test_go_emitted_docstring_common_renderer_shapes_compile(self) -> None:
        _assert_go_compiles(DOCSTRING_SOURCE)

    def test_cpp_emitted_docstring_common_renderer_shapes_compile(self) -> None:
        _assert_cpp_compiles(DOCSTRING_SOURCE)

    def test_go_emitted_comment_blank_nodes_compile(self) -> None:
        _assert_go_doc_compiles(
            {
                "kind": "Module",
                "meta": _emit_context_meta(),
                "body": [
                    {"kind": "comment", "text": "note"},
                    {"kind": "blank"},
                    {
                        "kind": "FunctionDef",
                        "name": "f",
                        "arg_types": {},
                        "arg_order": [],
                        "arg_defaults": {},
                        "arg_index": {},
                        "arg_usage": {},
                        "renamed_symbols": {},
                        "return_type": "int64",
                        "body": [
                            {"kind": "Pass"},
                            {"kind": "Return", "value": {"kind": "Constant", "value": 1, "resolved_type": "int64"}},
                        ],
                    },
                ],
            }
        )

    def test_cpp_emitted_comment_blank_nodes_compile(self) -> None:
        _assert_cpp_doc_compiles(
            {
                "kind": "Module",
                "meta": _emit_context_meta(),
                "body": [
                    {"kind": "comment", "text": "note"},
                    {"kind": "blank"},
                    {
                        "kind": "FunctionDef",
                        "name": "f",
                        "arg_types": {},
                        "arg_order": [],
                        "arg_defaults": {},
                        "arg_index": {},
                        "arg_usage": {},
                        "renamed_symbols": {},
                        "return_type": "int64",
                        "body": [
                            {"kind": "Pass"},
                            {"kind": "Return", "value": {"kind": "Constant", "value": 1, "resolved_type": "int64"}},
                        ],
                    },
                ],
            }
        )


if __name__ == "__main__":
    unittest.main()
