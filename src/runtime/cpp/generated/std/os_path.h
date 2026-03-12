// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/os_path.py
// generated-by: src/backends/cpp/cli.py

#ifndef PYTRA_GENERATED_STD_OS_PATH_H
#define PYTRA_GENERATED_STD_OS_PATH_H

#include "runtime/cpp/native/core/py_types.h"

#include <tuple>

namespace pytra::std::os_path {

str join(const str& a, const str& b);
str dirname(const str& p);
str basename(const str& p);
::std::tuple<str, str> splitext(const str& p);
str abspath(const str& p);
bool exists(const str& p);

}  // namespace pytra::std::os_path

#endif  // PYTRA_GENERATED_STD_OS_PATH_H
