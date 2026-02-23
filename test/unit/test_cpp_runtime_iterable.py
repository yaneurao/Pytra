"""Runtime-level regression tests for iterable protocol helper APIs."""

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


class CppRuntimeIterableTest(unittest.TestCase):
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

    def test_runtime_iterable_protocol_helpers(self) -> None:
        cpp_src = r'''
#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include <cassert>
#include <iostream>

int main() {
    object list_obj = make_object(list<int64>{1, 2, 3});
    object iter_obj = py_iter_or_raise(list_obj);
    auto n0 = py_next_or_stop(iter_obj);
    auto n1 = py_next_or_stop(iter_obj);
    auto n2 = py_next_or_stop(iter_obj);
    auto n3 = py_next_or_stop(iter_obj);
    assert(n0.has_value() && obj_to_int64(*n0) == 1);
    assert(n1.has_value() && obj_to_int64(*n1) == 2);
    assert(n2.has_value() && obj_to_int64(*n2) == 3);
    assert(!n3.has_value());

    int64 sum = 0;
    for (object v : py_dyn_range(list_obj)) {
        sum += obj_to_int64(v);
    }
    assert(sum == 6);

    dict<str, object> d{};
    d["a"] = make_object(1);
    d["b"] = make_object(2);
    bool has_a = false;
    bool has_b = false;
    for (object key_obj : py_dyn_range(make_object(d))) {
        str key = obj_to_str(key_obj);
        if (key == "a") has_a = true;
        if (key == "b") has_b = true;
    }
    assert(has_a && has_b);

    str joined = "";
    for (object ch : py_dyn_range(make_object(str("ab")))) {
        joined += obj_to_str(ch);
    }
    assert(joined == "ab");

    object set_obj = make_object(set<int64>{1, 2, 3});
    int64 set_sum = 0;
    for (object v : py_dyn_range(set_obj)) {
        set_sum += obj_to_int64(v);
    }
    assert(set_sum == 6);

    bool thrown = false;
    try {
        for (object _ : py_dyn_range(make_object(int64(9)))) {
            (void)_;
        }
    } catch (const ::std::runtime_error&) {
        thrown = true;
    }
    assert(thrown);

    std::cout << "runtime iterable ok" << std::endl;
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as tmpdir:
            work = Path(tmpdir)
            src = work / "runtime_iterable.cpp"
            exe = work / "runtime_iterable.out"
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
                label="compile runtime iterable smoke",
            )
            self.assertEqual(comp.returncode, 0, msg=comp.stderr)

            run = self._run(
                [str(exe)],
                cwd=work,
                timeout_sec=PYTRA_TEST_RUN_TIMEOUT_SEC,
                label="run runtime iterable smoke",
            )
            self.assertEqual(run.returncode, 0, msg=run.stderr)
            self.assertIn("runtime iterable ok", run.stdout)


if __name__ == "__main__":
    unittest.main()
