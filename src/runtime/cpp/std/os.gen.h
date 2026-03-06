// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/os.py
// generated-by: src/backends/cpp/cli.py

#ifndef PYTRA_STD_OS_GEN_H
#define PYTRA_STD_OS_GEN_H

#include "runtime/cpp/core/py_types.ext.h"

namespace pytra::std::os {

str getcwd();
void mkdir(const str& p);
void makedirs(const str& p, bool exist_ok = false);

}  // namespace pytra::std::os

#endif  // PYTRA_STD_OS_GEN_H
