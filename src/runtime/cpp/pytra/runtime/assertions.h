// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/runtime/assertions.py
// generated-by: src/py2cpp.py

#ifndef SRC_RUNTIME_CPP_PYTRA_RUNTIME_ASSERTIONS_H
#define SRC_RUNTIME_CPP_PYTRA_RUNTIME_ASSERTIONS_H

namespace pytra::runtime::assertions {

bool py_assert_true(bool cond, const str& label);
bool py_assert_eq(const object& actual, const object& expected, const str& label);
bool py_assert_all(const list<bool>& results, const str& label);
bool py_assert_stdout(const list<str>& expected_lines, const object& fn);

}  // namespace pytra::runtime::assertions

#endif  // SRC_RUNTIME_CPP_PYTRA_RUNTIME_ASSERTIONS_H
