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

_GEN_DIR = os.environ.get("PYTRA_GENERATED_CPP_DIR", "work/out/_test_generated_cpp")
CPP_RUNTIME_SRCS = [
    "src/runtime/cpp/core/io.cpp",
    os.path.join(_GEN_DIR, "built_in", "type_id.cpp"),
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

struct Base {
    virtual ~Base() {}
};
struct Child : Base {};

enum { TID_BASE = 100, TID_CHILD = 101 };
TypeInfo ti_base   = {TID_BASE,  100, 102, &deleter_impl<Base>};
TypeInfo ti_child  = {TID_CHILD, 101, 102, &deleter_impl<Child>};

int main() {
    g_type_table[TID_BASE]  = &ti_base;
    g_type_table[TID_CHILD] = &ti_child;

    // Object<T> isinstance via TypeInfo interval check
    Object<Child> child_obj = make_object<Child>(TID_CHILD);
    Object<Base>  base_obj  = make_object<Base>(TID_BASE);

    assert(child_obj.isinstance(&ti_base));
    assert(child_obj.isinstance(&ti_child));
    assert(base_obj.isinstance(&ti_base));
    assert(!base_obj.isinstance(&ti_child));

    // Upcast preserves type_id
    Object<Base> upcasted = child_obj;
    assert(upcasted.type_id() == TID_CHILD);
    assert(upcasted.isinstance(&ti_base));

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
                    "-I",
                    "src/runtime/east",
                    "-I",
                    _GEN_DIR,
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

    def test_generated_type_id_registry_accepts_preallocated_user_ids(self) -> None:
        cpp_src = r'''
#include "runtime/cpp/core/py_runtime.h"

#include <cassert>
#include <iostream>

struct BaseObj {
    int64 val;
    inline static constexpr uint32_t TYPE_ID = 1400;
    BaseObj() : val(0) {}
};

struct ChildObj : public BaseObj {
    inline static constexpr uint32_t TYPE_ID = 1401;
    ChildObj() : BaseObj() {}
};

int main() {
    g_type_table[1400] = new TypeInfo{1400, 1400, 1402, &deleter_impl<BaseObj>};
    g_type_table[1401] = new TypeInfo{1401, 1401, 1402, &deleter_impl<ChildObj>};

    assert(is_subtype(1401, g_type_table[1400]));

    Object<ChildObj> child_obj = make_object<ChildObj>(ChildObj::TYPE_ID);
    assert(child_obj.type_id() == 1401);

    Object<BaseObj> base_view = child_obj;
    assert(base_view.type_id() == 1401);
    assert(is_subtype(base_view.type_id(), g_type_table[1400]));

    std::cout << "generated type_id ok" << std::endl;
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as tmpdir:
            work = Path(tmpdir)
            src = work / "generated_type_id.cpp"
            exe = work / "generated_type_id.out"
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
                    "-I",
                    "src/runtime/east",
                    "-I",
                    _GEN_DIR,
                    str(src),
                    *CPP_RUNTIME_SRCS,
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                timeout_sec=PYTRA_TEST_COMPILE_TIMEOUT_SEC,
                label="compile generated type_id smoke",
            )
            self.assertEqual(comp.returncode, 0, msg=comp.stderr)

            run = self._run(
                [str(exe)],
                cwd=work,
                timeout_sec=PYTRA_TEST_RUN_TIMEOUT_SEC,
                label="run generated type_id smoke",
            )
            self.assertEqual(run.returncode, 0, msg=run.stderr)
            self.assertIn("generated type_id ok", run.stdout)

    def test_object_t_upcast_from_derived_compiles(self) -> None:
        cpp_src = r'''
#include "runtime/cpp/core/py_runtime.h"

#include <cassert>
#include <iostream>

struct BaseObj {
    inline static constexpr uint32_t TYPE_ID = 1500;
    BaseObj() {}
};

struct ChildObj : public BaseObj {
    inline static constexpr uint32_t TYPE_ID = 1501;
    ChildObj() : BaseObj() {}
};

int main() {
    g_type_table[1500] = new TypeInfo{1500, 1500, 1502, &deleter_impl<BaseObj>};
    g_type_table[1501] = new TypeInfo{1501, 1501, 1502, &deleter_impl<ChildObj>};

    Object<ChildObj> child = make_object<ChildObj>(ChildObj::TYPE_ID);
    Object<BaseObj> base_copy = child;
    assert(base_copy);

    Object<BaseObj> base_move = make_object<ChildObj>(ChildObj::TYPE_ID);
    assert(base_move);

    Object<BaseObj> assigned;
    assigned = child;
    assert(assigned);

    Object<ChildObj> tmp = make_object<ChildObj>(ChildObj::TYPE_ID);
    assigned = tmp;
    assert(assigned);

    std::cout << "object_t upcast ok" << std::endl;
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as tmpdir:
            work = Path(tmpdir)
            src = work / "object_t_upcast.cpp"
            exe = work / "object_t_upcast.out"
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
                    "-I",
                    "src/runtime/east",
                    "-I",
                    _GEN_DIR,
                    str(src),
                    *CPP_RUNTIME_SRCS,
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                timeout_sec=PYTRA_TEST_COMPILE_TIMEOUT_SEC,
                label="compile object_t upcast smoke",
            )
            self.assertEqual(comp.returncode, 0, msg=comp.stderr)

            run = self._run(
                [str(exe)],
                cwd=work,
                timeout_sec=PYTRA_TEST_RUN_TIMEOUT_SEC,
                label="run rc upcast smoke",
            )
            self.assertEqual(run.returncode, 0, msg=run.stderr)
            self.assertIn("object_t upcast ok", run.stdout)


if __name__ == "__main__":
    unittest.main()
