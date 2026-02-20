// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/runtime/std/sys.py
// generated-by: src/py2cpp.py

#ifndef SRC_RUNTIME_CPP_PYTRA_STD_SYS_H
#define SRC_RUNTIME_CPP_PYTRA_STD_SYS_H

#include <cstdint>
#include <string>
#include <vector>

namespace pytra::std::sys {

void exit(::std::int64_t code);
void set_argv(::std::vector<::std::string> values);
void set_path(::std::vector<::std::string> values);
void write_stderr(::std::string text);
void write_stdout(::std::string text);

}  // namespace pytra::std::sys

#endif  // SRC_RUNTIME_CPP_PYTRA_STD_SYS_H
