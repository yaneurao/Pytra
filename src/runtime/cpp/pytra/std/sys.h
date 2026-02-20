// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/runtime/std/sys.py
// generated-by: src/py2cpp.py

#ifndef SRC_RUNTIME_CPP_PYTRA_STD_SYS_H
#define SRC_RUNTIME_CPP_PYTRA_STD_SYS_H

namespace pytra::std::sys {

extern list<str> argv;
extern list<str> path;
extern int64 stderr;
extern int64 stdout;

void exit(int64 code);
void set_argv(const object& values);
void set_path(const object& values);
void write_stderr(const str& text);
void write_stdout(const str& text);

}  // namespace pytra::std::sys

#endif  // SRC_RUNTIME_CPP_PYTRA_STD_SYS_H
