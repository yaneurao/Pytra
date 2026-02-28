"""Regression tests for C++ pyobj list model runtime parity."""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from src.py2cpp import CppEmitter, load_east

ROOT = Path(__file__).resolve().parents[2]
PYTRA_TEST_COMPILE_TIMEOUT_SEC = float(os.environ.get("PYTRA_TEST_COMPILE_TIMEOUT_SEC", "120"))
PYTRA_TEST_RUN_TIMEOUT_SEC = float(os.environ.get("PYTRA_TEST_RUN_TIMEOUT_SEC", "15"))

CPP_RUNTIME_SRCS = [
    "src/runtime/cpp/pytra/built_in/gc.cpp",
    "src/runtime/cpp/pytra/std/pathlib.cpp",
    "src/runtime/cpp/pytra/std/time.cpp",
    "src/runtime/cpp/pytra/std/time-impl.cpp",
    "src/runtime/cpp/pytra/std/math.cpp",
    "src/runtime/cpp/pytra/std/math-impl.cpp",
    "src/runtime/cpp/pytra/std/random.cpp",
    "src/runtime/cpp/pytra/std/dataclasses.cpp",
    "src/runtime/cpp/pytra/std/glob.cpp",
    "src/runtime/cpp/pytra/std/json.cpp",
    "src/runtime/cpp/pytra/std/re.cpp",
    "src/runtime/cpp/pytra/std/sys.cpp",
    "src/runtime/cpp/pytra/std/timeit.cpp",
    "src/runtime/cpp/pytra/std/traceback.cpp",
    "src/runtime/cpp/pytra/std/typing.cpp",
    "src/runtime/cpp/pytra/built_in/io.cpp",
    "src/runtime/cpp/pytra/built_in/type_id.cpp",
    "src/runtime/cpp/pytra/built_in/bytes_util.cpp",
    "src/runtime/cpp/pytra/utils/png.cpp",
    "src/runtime/cpp/pytra/utils/gif.cpp",
    "src/runtime/cpp/pytra/utils/assertions.cpp",
]


class Py2CppListPyobjModelTest(unittest.TestCase):
    def _run(self, args: list[str], *, cwd: Path, timeout_sec: float, label: str) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout_sec)
        except subprocess.TimeoutExpired as ex:
            out_obj = ex.stdout
            err_obj = ex.stderr
            out_txt = out_obj if isinstance(out_obj, str) else ""
            err_txt = err_obj if isinstance(err_obj, str) else ""
            self.fail(
                f"{label} timed out after {timeout_sec:.1f}s: {' '.join(args)}\n"
                f"stdout:\n{out_txt}\n"
                f"stderr:\n{err_txt}"
            )
            raise AssertionError("unreachable")

    def _transpile_cpp_pyobj(self, src_py: Path, out_cpp: Path) -> None:
        east = load_east(src_py)
        emitter = CppEmitter(east, {})
        emitter.cpp_list_model = "pyobj"
        out_cpp.write_text(emitter.transpile(), encoding="utf-8")

    def _run_python(self, src_py: Path, *, cwd: Path) -> str:
        proc = self._run(
            ["python3", str(src_py)],
            cwd=cwd,
            timeout_sec=PYTRA_TEST_RUN_TIMEOUT_SEC,
            label=f"run python {src_py.name}",
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        return proc.stdout.replace("\r\n", "\n")

    def _compile_and_run_cpp_pyobj(self, src_py: Path, *, cwd: Path) -> str:
        out_cpp = cwd / (src_py.stem + ".cpp")
        out_exe = cwd / (src_py.stem + ".out")
        self._transpile_cpp_pyobj(src_py, out_cpp)
        comp = self._run(
            [
                "g++",
                "-std=c++20",
                "-O2",
                "-I",
                "src",
                "-I",
                "src/runtime/cpp",
                str(out_cpp),
                *CPP_RUNTIME_SRCS,
                "-o",
                str(out_exe),
            ],
            cwd=ROOT,
            timeout_sec=PYTRA_TEST_COMPILE_TIMEOUT_SEC,
            label=f"compile cpp pyobj {src_py.name}",
        )
        self.assertEqual(comp.returncode, 0, msg=comp.stderr)
        run = self._run(
            [str(out_exe)],
            cwd=cwd,
            timeout_sec=PYTRA_TEST_RUN_TIMEOUT_SEC,
            label=f"run cpp pyobj {src_py.name}",
        )
        self.assertEqual(run.returncode, 0, msg=run.stderr)
        return run.stdout.replace("\r\n", "\n")

    def test_sample18_pyobj_model_matches_python_stdout_except_elapsed(self) -> None:
        src_py = ROOT / "sample" / "py" / "18_mini_language_interpreter.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            work = Path(tmpdir)
            py_out = self._run_python(src_py, cwd=work)
            cpp_out = self._compile_and_run_cpp_pyobj(src_py, cwd=work)
        py_lines = [line for line in py_out.splitlines() if not line.startswith("elapsed_sec:")]
        cpp_lines = [line for line in cpp_out.splitlines() if not line.startswith("elapsed_sec:")]
        self.assertEqual(py_lines, cpp_lines)

    def test_list_alias_fixture_pyobj_model_matches_python_stdout(self) -> None:
        src_py = ROOT / "test" / "fixtures" / "collections" / "list_alias_shared_mutation.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            work = Path(tmpdir)
            py_out = self._run_python(src_py, cwd=work)
            cpp_out = self._compile_and_run_cpp_pyobj(src_py, cwd=work)
        self.assertEqual(py_out.strip(), cpp_out.strip())


if __name__ == "__main__":
    unittest.main()
