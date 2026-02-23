"""Runtime-level regression tests for type_id subtype/isinstance APIs."""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PYTRA_TEST_COMPILE_TIMEOUT_SEC = float(os.environ.get("PYTRA_TEST_COMPILE_TIMEOUT_SEC", "120"))
PYTRA_TEST_RUN_TIMEOUT_SEC = float(os.environ.get("PYTRA_TEST_RUN_TIMEOUT_SEC", "2"))

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
    "src/runtime/cpp/pytra/built_in/bytes_util.cpp",
    "src/runtime/cpp/pytra/utils/png.cpp",
    "src/runtime/cpp/pytra/utils/gif.cpp",
    "src/runtime/cpp/pytra/utils/assertions.cpp",
]


class CppRuntimeTypeIdTest(unittest.TestCase):
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

    def test_runtime_type_id_subtype_and_isinstance_contract(self) -> None:
        cpp_src = r'''
#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include <cassert>
#include <iostream>

class BaseObj : public PyObj {
public:
    explicit BaseObj(uint32 type_id) : PyObj(type_id) {}
};

class ChildObj : public BaseObj {
public:
    explicit ChildObj(uint32 type_id) : BaseObj(type_id) {}
};

int main() {
    assert(py_is_subtype(PYTRA_TID_BOOL, PYTRA_TID_INT));
    assert(py_is_subtype(PYTRA_TID_BOOL, PYTRA_TID_OBJECT));
    assert(py_isinstance(true, PYTRA_TID_INT));
    assert(py_isinstance(true, PYTRA_TID_OBJECT));
    assert(py_isinstance(int64(3), PYTRA_TID_INT));
    assert(py_isinstance(str("x"), PYTRA_TID_STR));

    uint32 base_tid = py_register_class_type(list<uint32>{PYTRA_TID_OBJECT});
    uint32 child_tid = py_register_class_type(list<uint32>{base_tid});

    assert(py_is_subtype(child_tid, base_tid));
    assert(py_issubclass(child_tid, base_tid));

    object base_obj = object_new<BaseObj>(base_tid);
    object child_obj = object_new<ChildObj>(child_tid);
    assert(py_isinstance(base_obj, base_tid));
    assert(py_isinstance(child_obj, child_tid));
    assert(py_isinstance(child_obj, base_tid));
    assert(py_isinstance(child_obj, PYTRA_TID_OBJECT));
    assert(!py_isinstance(base_obj, child_tid));

    set<str> names = set<str>{"a", "b"};
    assert(py_isinstance(names, PYTRA_TID_SET));
    object names_obj = make_object(names);
    assert(py_isinstance(names_obj, PYTRA_TID_SET));

    std::cout << "runtime type_id ok" << std::endl;
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as tmpdir:
            work = Path(tmpdir)
            src = work / "runtime_type_id.cpp"
            exe = work / "runtime_type_id.out"
            src.write_text(cpp_src, encoding="utf-8")

            comp = self._run(
                [
                    "g++",
                    "-std=c++20",
                    "-O2",
                    "-I",
                    "src",
                    "-I",
                    "src/runtime/cpp",
                    str(src),
                    *CPP_RUNTIME_SRCS,
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                timeout_sec=PYTRA_TEST_COMPILE_TIMEOUT_SEC,
                label="compile runtime type_id smoke",
            )
            self.assertEqual(comp.returncode, 0, msg=comp.stderr)

            run = self._run(
                [str(exe)],
                cwd=work,
                timeout_sec=PYTRA_TEST_RUN_TIMEOUT_SEC,
                label="run runtime type_id smoke",
            )
            self.assertEqual(run.returncode, 0, msg=run.stderr)
            self.assertIn("runtime type_id ok", run.stdout)


if __name__ == "__main__":
    unittest.main()
