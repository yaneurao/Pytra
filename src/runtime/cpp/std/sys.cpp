#include "core/py_runtime.h"
#include "core/process_runtime.h"

#include "sys.h"

Object<list<str>> argv = rc_list_from_value(py_runtime_argv());
Object<list<str>> path = rc_list_new<str>();

void exit(int64 code) {
    py_runtime_exit(code);
}

void set_argv(const Object<list<str>>& values) {
    argv = values;
    if (values) py_runtime_set_argv(*values);
}

void set_path(const Object<list<str>>& values) {
    path = values;
}

void write_stderr(const str& text) {
    py_runtime_write_stderr(text);
}

void write_stdout(const str& text) {
    py_runtime_write_stdout(text);
}
