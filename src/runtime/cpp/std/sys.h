#ifndef PYTRA_STD_SYS_H
#define PYTRA_STD_SYS_H

#include "core/py_runtime.h"

extern Object<list<str>> argv;
extern Object<list<str>> path;

void exit(int64 code = 0);
void set_argv(const Object<list<str>>& values);
void set_path(const Object<list<str>>& values);
void write_stderr(const str& text);
void write_stdout(const str& text);

#endif  // PYTRA_STD_SYS_H
