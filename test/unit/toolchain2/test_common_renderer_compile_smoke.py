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


def _fixture_case_source(rel_path: str) -> str:
    source = (ROOT / rel_path).read_text(encoding="utf-8")
    lines = source.splitlines()
    out: list[str] = []
    in_main_guard = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("from pytra.utils.assertions import py_assert_stdout"):
            continue
        if stripped == 'if __name__ == "__main__":':
            in_main_guard = True
            out.append(line)
            out.append("    _case_main()")
            continue
        if in_main_guard:
            continue
        out.append(line)
    return "\n".join(out) + "\n"


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

PRINT_SOURCE = """
def f() -> int:
    x = 1
    if x < 2:
        x = x + 2
    return x

if __name__ == "__main__":
    print(f())
"""

FIXTURE_ADD_SOURCE = _fixture_case_source("test/fixture/source/py/core/add.py")
FIXTURE_NOT_SOURCE = _fixture_case_source("test/fixture/source/py/control/not.py")


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


def _run_go(source: str) -> str:
    east3 = _build_east3(source, target_language="go")
    go_code = emit_go_module(east3)

    with tempfile.TemporaryDirectory() as tmp:
        go_path = Path(tmp) / "app.go"
        runtime_path = ROOT / "src" / "runtime" / "go" / "built_in" / "py_runtime.go"
        bundled_runtime = Path(tmp) / "py_runtime.go"
        out_path = Path(tmp) / "app"
        go_path.write_text(go_code, encoding="utf-8")
        bundled_runtime.write_text(runtime_path.read_text(encoding="utf-8"), encoding="utf-8")
        build = subprocess.run(
            ["go", "build", "-o", str(out_path), str(bundled_runtime), str(go_path)],
            cwd=tmp,
            capture_output=True,
            text=True,
        )
        if build.returncode != 0:
            raise AssertionError(f"{build.stdout}\n{build.stderr}")
        run = subprocess.run([str(out_path)], cwd=tmp, capture_output=True, text=True)

    if run.returncode != 0:
        raise AssertionError(f"{run.stdout}\n{run.stderr}")
    return run.stdout


def _run_cpp(source: str) -> str:
    east3 = _build_east3(source, target_language="cpp")
    cpp_code = emit_cpp_module(east3)

    with tempfile.TemporaryDirectory() as tmp:
        cpp_path = Path(tmp) / "app.cpp"
        out_path = Path(tmp) / "app.out"
        cpp_path.write_text(cpp_code, encoding="utf-8")
        build = subprocess.run(
            [
                "g++",
                "-std=c++20",
                "-I",
                str(ROOT / "src" / "runtime" / "cpp"),
                str(cpp_path),
                "-o",
                str(out_path),
            ],
            cwd=tmp,
            capture_output=True,
            text=True,
        )
        if build.returncode != 0:
            raise AssertionError(f"{build.stdout}\n{build.stderr}")
        run = subprocess.run([str(out_path)], cwd=tmp, capture_output=True, text=True)

    if run.returncode != 0:
        raise AssertionError(f"{run.stdout}\n{run.stderr}")
    return run.stdout


def _assert_go_runs_empty(source: str) -> None:
    stdout = _run_go(source)
    if stdout != "":
        raise AssertionError(stdout)


def _assert_cpp_runs_empty(source: str) -> None:
    stdout = _run_cpp(source)
    if stdout != "":
        raise AssertionError(stdout)


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

    def test_go_emitted_common_renderer_shapes_run(self) -> None:
        _assert_go_runs_empty(SOURCE)

    def test_cpp_emitted_common_renderer_shapes_run(self) -> None:
        _assert_cpp_runs_empty(SOURCE)

    def test_common_renderer_empty_stdout_parity_between_go_and_cpp(self) -> None:
        go_stdout = _run_go(SOURCE)
        cpp_stdout = _run_cpp(SOURCE)

        self.assertEqual(go_stdout, "")
        self.assertEqual(cpp_stdout, "")
        self.assertEqual(go_stdout, cpp_stdout)

    def test_common_renderer_print_stdout_parity_between_go_and_cpp(self) -> None:
        go_stdout = _run_go(PRINT_SOURCE)
        cpp_stdout = _run_cpp(PRINT_SOURCE)

        self.assertEqual(go_stdout, "3\n")
        self.assertEqual(cpp_stdout, "3\n")
        self.assertEqual(go_stdout, cpp_stdout)

    def test_common_renderer_fixture_add_stdout_parity_between_go_and_cpp(self) -> None:
        go_stdout = _run_go(FIXTURE_ADD_SOURCE)
        cpp_stdout = _run_cpp(FIXTURE_ADD_SOURCE)

        self.assertEqual(go_stdout, "7\n")
        self.assertEqual(cpp_stdout, "7\n")
        self.assertEqual(go_stdout, cpp_stdout)

    def test_common_renderer_fixture_not_stdout_parity_between_go_and_cpp(self) -> None:
        go_stdout = _run_go(FIXTURE_NOT_SOURCE)
        cpp_stdout = _run_cpp(FIXTURE_NOT_SOURCE)

        self.assertEqual(go_stdout, "True\n")
        self.assertEqual(cpp_stdout, "True\n")
        self.assertEqual(go_stdout, cpp_stdout)


if __name__ == "__main__":
    unittest.main()
