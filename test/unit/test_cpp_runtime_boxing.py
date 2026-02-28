"""Runtime-level regression tests for boxing/unboxing helper APIs."""

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


class CppRuntimeBoxingTest(unittest.TestCase):
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

    def test_runtime_boxing_helpers_behave_as_expected(self) -> None:
        cpp_src = r'''
#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include <cassert>
#include <iostream>

class CustomLenObj : public PyObj {
public:
    CustomLenObj() : PyObj(9001) {}
    bool py_truthy() const override { return false; }
    ::std::optional<int64> py_try_len() const override { return int64(7); }
    ::std::string py_str() const override { return "custom"; }
};

int main() {
    object as_int = make_object(int64(42));
    assert(obj_to_int64(as_int) == 42);
    assert(obj_to_int64_or_raise(as_int, "int-cast") == 42);
    assert(py_to<int64>(as_int) == 42);
    assert(py_to<float64>(as_int) == 42.0);
    assert(py_to<bool>(as_int));

    object as_str_num = make_object(str("12"));
    assert(obj_to_int64_or_raise(as_str_num, "str-int") == 12);
    assert(py_to_int64(as_str_num) == 12);
    assert(py_to<int64>(as_str_num) == 12);

    object as_str_bad = make_object(str("oops"));
    assert(py_to_int64(as_str_bad) == 0);
    assert(py_to<int64>(as_str_bad) == 0);

    object as_list = make_object(list<int64>{1, 2});
    auto as_list_rc = obj_to_list_obj(as_list);
    assert(static_cast<bool>(as_list_rc));
    assert(as_list_rc->value.size() == 2);
    list<int64> legacy_list = list<int64>(as_list);
    assert(legacy_list.size() == 2);
    legacy_list.append(99);
    assert(legacy_list.size() == 3);
    assert(as_list_rc->value.size() == 2);

    object as_bytes_obj = make_object(bytes{uint8(1), uint8(2), uint8(255)});
    bytes as_bytes = bytes(as_bytes_obj);
    assert(as_bytes.size() == 3);
    assert(as_bytes[0] == static_cast<uint8>(1));
    assert(as_bytes[2] == static_cast<uint8>(255));

    object as_frames_obj = make_object(list<object>{make_object(bytes{uint8(3), uint8(4), uint8(5)})});
    list<bytes> as_frames = list<bytes>(as_frames_obj);
    assert(as_frames.size() == 1);
    assert(as_frames[0].size() == 3);
    assert(as_frames[0][1] == static_cast<uint8>(4));

    object tuple_list_obj = make_object(list<::std::tuple<int64, int64>>{::std::make_tuple(7, 8)});
    assert(py_len(tuple_list_obj) == 1);
    object tuple_elem_obj = py_at(tuple_list_obj, int64(-1));
    assert(py_is_list(tuple_elem_obj));
    assert(py_len(tuple_elem_obj) == 2);
    assert(py_to<int64>(py_at(tuple_elem_obj, int64(0))) == 7);
    assert(py_to<int64>(py_at(tuple_elem_obj, int64(1))) == 8);

    ::std::any any_num = str("21");
    assert(py_to_int64(any_num) == 21);
    assert(py_to<int64>(any_num) == 21);

    ::std::any any_bad = str("oops");
    assert(py_to_int64(any_bad) == 0);
    assert(py_to<int64>(any_bad) == 0);

    ::std::any any_obj = as_str_num;
    assert(py_to_int64(any_obj) == 0);
    assert(py_to<int64>(any_obj) == 0);
    assert(py_to_int64_base(any_obj, 10) == 12);

    assert(py_to_int64_base(str("10"), 16) == 16);
    assert(py_to_int64_base(any_num, 10) == 21);

    bool thrown = false;
    try {
        (void)obj_to_int64_or_raise(make_object(str("oops")), "bad-int");
    } catch (const ::std::runtime_error&) {
        thrown = true;
    }
    assert(thrown);

    auto custom = rc_new<CustomLenObj>();
    object custom_obj = make_object(custom);
    assert(!obj_to_bool(custom_obj));
    assert(py_len(custom_obj) == 7);
    assert(obj_to_str(custom_obj) == "custom");

    auto cast_ok = obj_to_rc<CustomLenObj>(custom_obj);
    assert(static_cast<bool>(cast_ok));
    assert(cast_ok->type_id() == 9001);

    thrown = false;
    try {
        (void)obj_to_rc_or_raise<PyListObj>(custom_obj, "rc-cast");
    } catch (const ::std::runtime_error&) {
        thrown = true;
    }
    assert(thrown);

    std::cout << "runtime boxing ok" << std::endl;
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as tmpdir:
            work = Path(tmpdir)
            src = work / "runtime_boxing.cpp"
            exe = work / "runtime_boxing.out"
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
                label="compile runtime boxing smoke",
            )
            self.assertEqual(comp.returncode, 0, msg=comp.stderr)

            run = self._run(
                [str(exe)],
                cwd=work,
                timeout_sec=PYTRA_TEST_RUN_TIMEOUT_SEC,
                label="run runtime boxing smoke",
            )
            self.assertEqual(run.returncode, 0, msg=run.stderr)
            self.assertIn("runtime boxing ok", run.stdout)


if __name__ == "__main__":
    unittest.main()
