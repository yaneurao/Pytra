// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/runtime/assertions.py
// generated-by: src/py2cpp.py

#ifndef SRC_RUNTIME_CPP_PYTRA_RUNTIME_ASSERTIONS_H
#define SRC_RUNTIME_CPP_PYTRA_RUNTIME_ASSERTIONS_H

#include <any>
#include <string>
#include <vector>

namespace pytra::runtime::assertions {

bool py_assert_true(bool cond, ::std::string label);
bool py_assert_eq(::std::any actual, ::std::any expected, ::std::string label);
bool py_assert_all(::std::vector<bool> results, ::std::string label);
bool py_assert_stdout(::std::vector<::std::string> expected_lines, ::std::any fn);

}  // namespace pytra::runtime::assertions

#endif  // SRC_RUNTIME_CPP_PYTRA_RUNTIME_ASSERTIONS_H
