// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/os.py
// generated-by: src/backends/cpp/cli.py

#ifndef PYTRA_GENERATED_STD_OS_H
#define PYTRA_GENERATED_STD_OS_H

#include "runtime/cpp/core/py_types.h"

namespace pytra::std::os {

str getcwd();
void mkdir(const str& p);
void makedirs(const str& p, bool exist_ok = false);

}  // namespace pytra::std::os

#endif  // PYTRA_GENERATED_STD_OS_H
