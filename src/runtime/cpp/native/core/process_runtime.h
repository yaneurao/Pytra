#pragma once

#include <cstdlib>
#include <iostream>

#include "py_types.h"

inline list<str> py_runtime_argv_storage_v{};

static inline void py_runtime_set_argv(const list<str>& values);

static inline void pytra_configure_from_argv(int argc, char** argv) {
    list<str> args{};
    args.reserve(static_cast<::std::size_t>(argc));
    for (int i = 0; i < argc; ++i) {
        args.append(str(argv[i]));
    }
    py_runtime_set_argv(args);
}

static inline list<str> py_runtime_argv() {
    return py_runtime_argv_storage_v;
}

static inline void py_runtime_set_argv(const list<str>& values) {
    py_runtime_argv_storage_v = values;
}

static inline void py_runtime_write_stderr(const str& text) {
    ::std::cerr << text;
}

static inline void py_runtime_write_stdout(const str& text) {
    ::std::cout << text;
}

[[noreturn]] static inline void py_runtime_exit(int64 code = 0) {
    ::std::exit(static_cast<int>(code));
}
