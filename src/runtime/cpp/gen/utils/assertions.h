// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/assertions.py
// generated-by: src/py2cpp.py

#ifndef PYTRA_UTILS_ASSERTIONS_H
#define PYTRA_UTILS_ASSERTIONS_H

namespace pytra::utils::assertions {

bool _eq_any(const object& actual, const object& expected);
bool py_assert_true(bool cond, const str& label);
bool py_assert_eq(const object& actual, const object& expected, const str& label);
bool py_assert_all(const list<bool>& results, const str& label);
bool py_assert_stdout(const list<str>& expected_lines, const object& fn);

}  // namespace pytra::utils::assertions

#endif  // PYTRA_UTILS_ASSERTIONS_H
