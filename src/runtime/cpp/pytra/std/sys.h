// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/sys.py
// generated-by: src/py2cpp.py

#ifndef PYTRA_STD_SYS_H
#define PYTRA_STD_SYS_H

namespace pytra::std::sys {

extern list<str> argv;
extern list<str> path;
extern object stderr;
extern object stdout;

void exit(int64 code = 0);
list<str> _to_str_list_fallback(const object& values);
void set_argv(const object& values);
void set_path(const object& values);
void write_stderr_impl(const str& text);
void write_stdout_impl(const str& text);
void write_stderr(const str& text);
void write_stdout(const str& text);

}  // namespace pytra::std::sys

#endif  // PYTRA_STD_SYS_H
