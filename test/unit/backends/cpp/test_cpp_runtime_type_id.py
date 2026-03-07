"""Runtime-level regression tests for type_id subtype/isinstance APIs."""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
PYTRA_TEST_COMPILE_TIMEOUT_SEC = float(os.environ.get("PYTRA_TEST_COMPILE_TIMEOUT_SEC", "120"))
PYTRA_TEST_RUN_TIMEOUT_SEC = float(os.environ.get("PYTRA_TEST_RUN_TIMEOUT_SEC", "2"))

CPP_RUNTIME_SRCS = [
    "src/runtime/cpp/native/core/gc.ext.cpp",
    "src/runtime/cpp/native/core/io.ext.cpp",
    "src/runtime/cpp/generated/built_in/type_id.cpp",
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
#include "runtime/cpp/core/py_runtime.h"

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

    uint32 base_tid = py_register_class_type(PYTRA_TID_OBJECT);
    uint32 child_tid = py_register_class_type(base_tid);

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

    def test_rc_handle_upcast_from_derived_compiles(self) -> None:
        cpp_src = r'''
#include "runtime/cpp/core/gc.h"

#include <cassert>
#include <iostream>
#include <utility>

class BaseObj : public pytra::gc::PyObj {
public:
    BaseObj() : pytra::gc::PyObj(1000) {}
};

class ChildObj : public BaseObj {
public:
    ChildObj() : BaseObj() {}
};

int main() {
    using pytra::gc::RcHandle;

    RcHandle<ChildObj> child = RcHandle<ChildObj>::adopt(pytra::gc::rc_new<ChildObj>());
    RcHandle<BaseObj> base_copy = child;
    assert(base_copy.get() != nullptr);

    RcHandle<BaseObj> base_move = RcHandle<ChildObj>::adopt(pytra::gc::rc_new<ChildObj>());
    assert(base_move.get() != nullptr);

    RcHandle<BaseObj> assigned;
    assigned = child;
    assert(assigned.get() != nullptr);

    RcHandle<ChildObj> tmp = RcHandle<ChildObj>::adopt(pytra::gc::rc_new<ChildObj>());
    assigned = std::move(tmp);
    assert(assigned.get() != nullptr);
    assert(!tmp);

    std::cout << "rc upcast ok" << std::endl;
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as tmpdir:
            work = Path(tmpdir)
            src = work / "rc_upcast.cpp"
            exe = work / "rc_upcast.out"
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
                    "src/runtime/cpp/native/core/gc.ext.cpp",
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                timeout_sec=PYTRA_TEST_COMPILE_TIMEOUT_SEC,
                label="compile rc upcast smoke",
            )
            self.assertEqual(comp.returncode, 0, msg=comp.stderr)

            run = self._run(
                [str(exe)],
                cwd=work,
                timeout_sec=PYTRA_TEST_RUN_TIMEOUT_SEC,
                label="run rc upcast smoke",
            )
            self.assertEqual(run.returncode, 0, msg=run.stderr)
            self.assertIn("rc upcast ok", run.stdout)


if __name__ == "__main__":
    unittest.main()
