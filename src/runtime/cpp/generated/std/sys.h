// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/sys.py
// generated-by: src/backends/cpp/cli.py

#ifndef PYTRA_GENERATED_STD_SYS_H
#define PYTRA_GENERATED_STD_SYS_H

#include "runtime/cpp/native/core/py_types.h"

namespace pytra::std::sys {

extern list<str> argv;
extern list<str> path;
extern object stderr;
extern object stdout;

void exit(int64 code = 0);
void set_argv(const rc<list<str>>& values);
void set_path(const rc<list<str>>& values);
void write_stderr(const str& text);
void write_stdout(const str& text);

}  // namespace pytra::std::sys

#endif  // PYTRA_GENERATED_STD_SYS_H
