#include "runtime/cpp/native/core/py_runtime.h"
#include "runtime/cpp/native/core/process_runtime.h"

#include "runtime/cpp/generated/std/sys.h"

namespace pytra::std::sys {

list<str> argv = py_runtime_argv();
list<str> path = {};
object stderr = make_object(::std::nullopt);
object stdout = make_object(::std::nullopt);

void exit(int64 code) {
    py_runtime_exit(code);
}

void set_argv(const list<str>& values) {
    argv = values;
    py_runtime_set_argv(values);
}

void set_path(const list<str>& values) {
    path = values;
}

void write_stderr(const str& text) {
    py_runtime_write_stderr(text);
}

void write_stdout(const str& text) {
    py_runtime_write_stdout(text);
}

}  // namespace pytra::std::sys
