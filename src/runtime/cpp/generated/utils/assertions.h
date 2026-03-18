// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/assertions.py
// generated-by: src/backends/cpp/cli.py

#ifndef PYTRA_GENERATED_UTILS_ASSERTIONS_H
#define PYTRA_GENERATED_UTILS_ASSERTIONS_H

#include "runtime/cpp/native/core/py_types.h"

namespace pytra::utils::assertions {

bool _eq_any(const ::std::variant<str, int64, float64, bool, ::std::monostate>& actual, const ::std::variant<str, int64, float64, bool, ::std::monostate>& expected);
bool py_assert_true(bool cond, const str& label = "");
bool py_assert_eq(const ::std::variant<str, int64, float64, bool, ::std::monostate>& actual, const ::std::variant<str, int64, float64, bool, ::std::monostate>& expected, const str& label = "");
bool py_assert_all(const list<bool>& results, const str& label = "");
bool py_assert_stdout(const list<str>& expected_lines, const object& fn);

}  // namespace pytra::utils::assertions

#endif  // PYTRA_GENERATED_UTILS_ASSERTIONS_H
