"""Runtime-level regression tests for iterable protocol helper APIs."""

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
    "src/runtime/cpp/native/core/gc.cpp",
    "src/runtime/cpp/native/core/io.cpp",
    "src/runtime/cpp/generated/built_in/string_ops.cpp",
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
#include "runtime/cpp/core/py_runtime.h"
#include "pytra/built_in/iter_ops.h"
#include "pytra/built_in/sequence.h"

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

    object mut_list_obj = make_object(list<int64>{10, 20});
    object mut_iter_obj = py_iter_or_raise(mut_list_obj);
    auto m0 = py_next_or_stop(mut_iter_obj);
    assert(m0.has_value() && obj_to_int64(*m0) == 10);
    py_append(mut_list_obj, make_object(int64(30)));
    auto m1 = py_next_or_stop(mut_iter_obj);
    auto m2 = py_next_or_stop(mut_iter_obj);
    auto m3 = py_next_or_stop(mut_iter_obj);
    assert(m1.has_value() && obj_to_int64(*m1) == 20);
    assert(m2.has_value() && obj_to_int64(*m2) == 30);
    assert(!m3.has_value());
    py_extend(mut_list_obj, make_object(list<int64>{40, 50}));
    assert(py_len(mut_list_obj) == 5);
    object p0 = py_pop(mut_list_obj);
    assert(obj_to_int64(p0) == 50);
    object p1 = py_pop(mut_list_obj, 0);
    assert(obj_to_int64(p1) == 10);
    py_reverse(mut_list_obj);
    assert(obj_to_int64(py_at(mut_list_obj, 0)) == 40);
    py_sort(mut_list_obj);
    assert(obj_to_int64(py_at(mut_list_obj, 0)) == 20);
    py_clear(mut_list_obj);
    assert(py_len(mut_list_obj) == 0);

    rc<list<int64>> typed = rc_list_from_value(list<int64>{3, 1, 2});
    assert(py_len(typed) == 3);
    assert(py_to_bool(typed));
    list<int64> typed_head = py_slice(typed, 0, 2);
    assert(typed_head.size() == 2);
    assert(typed_head[0] == 3);
    assert(typed_head[1] == 1);
    py_set_at(typed, 1, int64(9));
    assert(py_at(typed, 1) == 9);
    py_append(typed, int64(4));
    py_extend(typed, list<int64>{5, 6});
    assert(py_len(typed) == 6);
    assert(py_pop(typed) == 6);
    assert(py_pop(typed, 0) == 3);
    py_reverse(typed);
    assert(py_at(typed, 0) == 5);
    py_sort(typed);
    assert(py_at(typed, 0) == 2);
    py_clear(typed);
    assert(py_len(typed) == 0);
    assert(!py_to_bool(typed));

    rc<list<int64>> typed_iter = rc_list_from_value(list<int64>{7, 8, 9});
    assert(py_contains(typed_iter, int64(8)));
    assert(!py_contains(typed_iter, int64(5)));
    list<int64> typed_rev = py_reversed(typed_iter);
    assert(typed_rev.size() == 3);
    assert(typed_rev[0] == 9);
    assert(typed_rev[2] == 7);
    auto typed_enum = py_enumerate(typed_iter, 5);
    assert(typed_enum.size() == 3);
    assert(::std::get<0>(typed_enum[0]) == 5);
    assert(::std::get<1>(typed_enum[0]) == 7);
    assert(::std::get<0>(typed_enum[2]) == 7);
    assert(::std::get<1>(typed_enum[2]) == 9);
    list<int64> typed_repeat = py_repeat(typed_iter, 2);
    assert(typed_repeat.size() == 6);
    assert(typed_repeat[0] == 7);
    assert(typed_repeat[3] == 7);
    assert(typed_repeat[5] == 9);
    object typed_obj = make_object(typed_iter);
    auto typed_from_obj = py_to<rc<list<int64>>>(typed_obj);
    assert(py_len(typed_from_obj) == 3);
    assert(py_at(typed_from_obj, 1) == 8);
    assert(py_is_list(typed_iter));

    object nested_obj = make_object(list<list<int64>>{list<int64>{1, 2}, list<int64>{3, 4}});
    list<list<int64>> nested_plain = py_to<list<list<int64>>>(nested_obj);
    assert(nested_plain.size() == 2);
    assert(nested_plain[0].size() == 2);
    assert(nested_plain[0][1] == 2);
    auto nested_rc = py_to<rc<list<list<int64>>>>(nested_obj);
    assert(py_len(nested_rc) == 2);
    assert(py_at(py_at(nested_rc, 1), 0) == 3);

    list<int64> plain = list<int64>{4, 5, 6};
    list<int64> plain_slice = py_slice(plain, 0, 2);
    assert(plain_slice.size() == 2);
    assert(plain_slice[0] == 4);
    assert(py_at(plain, -1) == 6);
    assert(py_contains(plain, int64(5)));
    auto plain_enum = py_enumerate(plain, 10);
    assert(plain_enum.size() == 3);
    assert(::std::get<0>(plain_enum[0]) == 10);
    assert(::std::get<1>(plain_enum[2]) == 6);
    list<int64> plain_rev = py_reversed(plain);
    assert(plain_rev[0] == 6);
    list<int64> plain_repeat = py_repeat(plain, 2);
    assert(plain_repeat.size() == 6);
    assert(plain_repeat[3] == 4);

    int64 list_sum = 0;
    for (object v : py_dyn_range(list_obj)) {
        list_sum += obj_to_int64(v);
    }
    assert(list_sum == 6);
    assert(sum(list<int64>{1, 2, 3}) == 6);
    assert(py_min(int64(9), int64(3)) == 3);
    assert(py_max(int64(9), int64(3)) == 9);
    assert(py_min(int64(9), int64(3), int64(5)) == 3);
    assert(py_max(int64(9), int64(3), int64(5)) == 9);
    list<::std::tuple<int64, str>> zipped = zip(list<int64>{1, 2, 3}, list<str>{"a", "b"});
    assert(zipped.size() == 2);
    assert(::std::get<0>(zipped[0]) == 1);
    assert(::std::get<1>(zipped[0]) == "a");
    object zipped_lhs = make_object(list<object>{make_object(int64(1)), make_object(int64(2))});
    object zipped_rhs = make_object(list<object>{make_object(str("x")), make_object(str("y")), make_object(str("z"))});
    auto zipped_from_obj = zip(py_to<list<object>>(zipped_lhs), py_to<list<object>>(zipped_rhs));
    assert(zipped_from_obj.size() == 2);
    assert(obj_to_int64(::std::get<0>(zipped_from_obj[1])) == 2);
    assert(obj_to_str(::std::get<1>(zipped_from_obj[0])) == "x");

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

    list<str> split_all = str("a,b,c").split(",", -1);
    assert(split_all.size() == 3);
    assert(split_all[1] == "b");
    list<str> split_once = str("a,b,c").split(",", 1);
    assert(split_once.size() == 2);
    assert(split_once[1] == "b,c");
    list<str> split_lines = str("x\ny\r\n").splitlines();
    assert(split_lines.size() == 3);
    assert(split_lines[2] == "");
    assert(str("banana").count("na") == 2);

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

    def test_runtime_list_overload_inventory(self) -> None:
        forwarder_header = (ROOT / "src/runtime/cpp/core/py_runtime.h").read_text(encoding="utf-8")
        runtime_header = (ROOT / "src/runtime/cpp/native/core/py_runtime.h").read_text(encoding="utf-8")
        iter_ops_header = (ROOT / "src/runtime/cpp/native/built_in/iter_ops.h").read_text(encoding="utf-8")
        sequence_header = (ROOT / "src/runtime/cpp/native/built_in/sequence.h").read_text(encoding="utf-8")
        contains_header = (ROOT / "src/runtime/cpp/native/built_in/contains.h").read_text(encoding="utf-8")
        string_ops_header = (ROOT / "src/runtime/cpp/generated/built_in/string_ops.h").read_text(encoding="utf-8")
        string_ops_cpp = (ROOT / "src/runtime/cpp/generated/built_in/string_ops.cpp").read_text(encoding="utf-8")
        numeric_ops_header = (ROOT / "src/runtime/cpp/generated/built_in/numeric_ops.h").read_text(encoding="utf-8")
        zip_ops_header = (ROOT / "src/runtime/cpp/generated/built_in/zip_ops.h").read_text(encoding="utf-8")

        self.assertIn('#include "runtime/cpp/native/core/py_runtime.h"', forwarder_header)
        self.assertIn('#include "runtime/cpp/generated/built_in/numeric_ops.h"', runtime_header)
        self.assertIn('#include "runtime/cpp/generated/built_in/zip_ops.h"', runtime_header)
        self.assertNotIn('#include "runtime/cpp/generated/built_in/predicates.h"', runtime_header)
        self.assertNotIn('#include "runtime/cpp/native/built_in/sequence.h"', runtime_header)
        self.assertNotIn('#include "runtime/cpp/generated/built_in/sequence.h"', runtime_header)
        self.assertNotIn('#include "runtime/cpp/native/built_in/iter_ops.h"', runtime_header)
        self.assertNotIn("static inline T& py_at(list<T>& v, int64 idx)", runtime_header)
        self.assertNotIn("static inline void py_set_at(list<T>& v, I idx, const U& item)", runtime_header)
        self.assertNotIn("static inline T sum(const list<T>& values)", runtime_header)
        self.assertNotIn("static inline auto py_min(const A& a, const B& b)", runtime_header)
        self.assertNotIn("static inline auto py_max(const A& a, const B& b)", runtime_header)
        self.assertNotIn("static inline list<::std::tuple<A, B>> zip(const list<A>& lhs, const list<B>& rhs)", runtime_header)
        self.assertNotIn("static inline list<str> py_dict_keys(const object& obj)", runtime_header)
        self.assertNotIn("static inline list<object> py_dict_items(const object& obj)", runtime_header)
        self.assertNotIn("static inline list<object> py_dict_values(const object& obj)", runtime_header)
        self.assertNotIn("static inline ::std::any py_dict_get(const ::std::any& obj, const char* key)", runtime_header)
        self.assertNotIn("static inline object py_dict_get_maybe(const ::std::any& obj, const char* key)", runtime_header)
        self.assertNotIn("static inline D py_dict_get_default(const dict<str, ::std::any>& d, const char* key, const D& defval)", runtime_header)
        self.assertNotIn("static inline D py_dict_get_default(const ::std::any& obj, const char* key, const D& defval)", runtime_header)
        self.assertNotIn("static inline str py_dict_get_default(const ::std::any& obj, const char* key, const char* defval)", runtime_header)
        self.assertNotIn("static inline object py_dict_get(const object& obj, const char* key)", runtime_header)
        self.assertNotIn("static inline object py_dict_get_maybe(const object& obj, const char* key)", runtime_header)
        self.assertNotIn("static inline object py_dict_get_maybe(const object& obj, const str& key)", runtime_header)
        self.assertNotIn("static inline object py_dict_get_default(const object& obj, const char* key, const object& defval)", runtime_header)
        self.assertNotIn("static inline object py_dict_get_default(const object& obj, const char* key, const char* defval)", runtime_header)
        self.assertNotIn("static inline object py_dict_get_default(const ::std::optional<dict<str, object>>& d, const char* key, const object& defval)", runtime_header)
        self.assertNotIn("static inline object py_dict_get_default(const ::std::optional<dict<str, object>>& d, const char* key, const char* defval)", runtime_header)
        self.assertNotIn("static inline bool dict_get_bool(const object& obj, const char* key, bool defval)", runtime_header)
        self.assertNotIn("static inline bool dict_get_bool(const ::std::optional<dict<str, object>>& d, const char* key, bool defval)", runtime_header)
        self.assertNotIn("static inline str dict_get_str(const object& obj, const char* key, const str& defval)", runtime_header)
        self.assertNotIn("static inline str dict_get_str(const ::std::optional<dict<str, object>>& d, const char* key, const str& defval)", runtime_header)
        self.assertNotIn("static inline int64 dict_get_int(const object& obj, const char* key, int64 defval)", runtime_header)
        self.assertNotIn("static inline int64 dict_get_int(const ::std::optional<dict<str, object>>& d, const char* key, int64 defval)", runtime_header)
        self.assertNotIn("static inline float64 dict_get_float(const object& obj, const char* key, float64 defval)", runtime_header)
        self.assertNotIn("static inline float64 dict_get_float(const ::std::optional<dict<str, object>>& d, const char* key, float64 defval)", runtime_header)
        self.assertNotIn(
            "static inline list<object> dict_get_list(\n    const object& obj, const char* key, const list<object>& defval = list<object>{})",
            runtime_header,
        )
        self.assertNotIn(
            "static inline list<object> dict_get_list(\n    const ::std::optional<dict<str, object>>& d, const char* key, const list<object>& defval = list<object>{})",
            runtime_header,
        )
        self.assertNotIn("static inline list<::std::tuple<object, object>> zip(const object& lhs, const object& rhs)", runtime_header)
        self.assertNotIn("static inline object sum(const object& values)", runtime_header)
        self.assertNotIn("static inline list<str> py_dict_keys(const ::std::optional<dict<str, object>>& d)", runtime_header)
        self.assertNotIn("static inline list<object> py_dict_items(const ::std::optional<dict<str, object>>& d)", runtime_header)
        self.assertNotIn("static inline list<object> py_dict_values(const ::std::optional<dict<str, object>>& d)", runtime_header)
        self.assertNotIn("static inline object sum(const list<object>& values)", runtime_header)
        self.assertNotIn("static inline object dict_get_node(const object& obj, const char* key, const object& defval = object{})", runtime_header)
        self.assertNotIn(
            "static inline object dict_get_node(\n    const ::std::optional<dict<str, object>>& d, const char* key, const object& defval = object{})",
            runtime_header,
        )
        self.assertNotIn("static inline bool operator<(const ::std::any& lhs, const ::std::any& rhs)", runtime_header)
        self.assertNotIn("static inline bool operator>(const ::std::any& lhs, const ::std::any& rhs)", runtime_header)
        self.assertNotIn("static inline bool operator<=(const ::std::any& lhs, const ::std::any& rhs)", runtime_header)
        self.assertNotIn("static inline bool operator>=(const ::std::any& lhs, const ::std::any& rhs)", runtime_header)
        self.assertNotIn("static inline bool operator>(const ::std::any& lhs, int rhs)", runtime_header)
        self.assertNotIn("static inline bool operator<(int64 lhs, const ::std::any& rhs)", runtime_header)
        self.assertNotIn("static inline str operator+(const char* lhs, const ::std::any& rhs)", runtime_header)
        self.assertNotIn("static inline float64 operator+(const ::std::any& lhs, const ::std::any& rhs)", runtime_header)
        self.assertNotIn("static inline float64 operator-(const ::std::any& lhs, const ::std::any& rhs)", runtime_header)
        self.assertNotIn("static inline float64 operator*(const ::std::any& lhs, const ::std::any& rhs)", runtime_header)
        self.assertNotIn("static inline float64 operator/(const ::std::any& lhs, const ::std::any& rhs)", runtime_header)
        self.assertIn("static inline const T& py_at(const list<T>& v, int64 idx)", runtime_header)
        self.assertIn("static inline void py_append(list<T>& v, const U& item)", runtime_header)
        self.assertIn("static inline list<T> py_slice(const list<T>& v, int64 lo, int64 up)", runtime_header)
        self.assertNotIn("static inline bool operator==(const ::std::any& lhs, const char* rhs)", runtime_header)
        self.assertNotIn("static inline bool operator!=(const ::std::any& lhs, const char* rhs)", runtime_header)
        self.assertNotIn("static inline bool operator<(const ::std::any& lhs, T rhs)", runtime_header)
        self.assertNotIn("static inline bool operator>(const ::std::any& lhs, T rhs)", runtime_header)
        self.assertNotIn("namespace std {", runtime_header)
        self.assertNotIn("static inline list<::std::any>::iterator begin(::std::any& v)", runtime_header)
        self.assertNotIn("static inline list<::std::any>::iterator end(::std::any& v)", runtime_header)
        self.assertNotIn("static inline ::list<::std::any>::iterator begin(::std::any& v)", runtime_header)
        self.assertNotIn("static inline ::list<::std::any>::const_iterator end(const ::std::any& v)", runtime_header)
        self.assertIn("static inline bool py_contains(const list<T>& values, const Q& key)", contains_header)
        self.assertIn("static inline list<T> py_reversed(const list<T>& values)", iter_ops_header)
        self.assertIn("static inline list<::std::tuple<int64, T>> py_enumerate(const list<T>& values)", iter_ops_header)
        self.assertNotIn("static inline list<::std::any> py_reversed(const ::std::any& values)", iter_ops_header)
        self.assertNotIn("static inline list<::std::tuple<int64, ::std::any>> py_enumerate(const ::std::any& values)", iter_ops_header)
        self.assertIn("static inline list<T> py_repeat(const list<T>& v, int64 n)", sequence_header)
        self.assertIn("str py_join(const str& sep, const list<str>& parts);", string_ops_header)
        self.assertIn("list<str> py_split(const str& s, const str& sep, int64 maxsplit);", string_ops_header)
        self.assertIn("list<str> py_splitlines(const str& s);", string_ops_header)
        self.assertIn("int64 py_count(const str& s, const str& needle);", string_ops_header)
        self.assertIn("str py_join(const str& sep, const list<str>& parts) {", string_ops_cpp)
        self.assertIn("list<str> py_split(const str& s, const str& sep, int64 maxsplit) {", string_ops_cpp)
        self.assertIn("list<str> py_splitlines(const str& s) {", string_ops_cpp)
        self.assertIn("int64 py_count(const str& s, const str& needle) {", string_ops_cpp)
        self.assertNotIn("rc<list<str>>", string_ops_header)
        self.assertIn("template <class T>", numeric_ops_header)
        self.assertIn("T sum(const list<T>& values) {", numeric_ops_header)
        self.assertIn("T py_min(const T& a, const T& b) {", numeric_ops_header)
        self.assertIn("T py_max(const T& a, const T& b) {", numeric_ops_header)
        self.assertIn("template <class A, class B>", zip_ops_header)
        self.assertIn("list<::std::tuple<A, B>> zip(const list<A>& lhs, const list<B>& rhs) {", zip_ops_header)
        self.assertFalse((ROOT / "src/runtime/cpp/generated/built_in/numeric_ops.cpp").exists())
        self.assertFalse((ROOT / "src/runtime/cpp/generated/built_in/zip_ops.cpp").exists())


if __name__ == "__main__":
    unittest.main()
