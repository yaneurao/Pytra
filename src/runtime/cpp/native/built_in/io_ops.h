#ifndef PYTRA_NATIVE_BUILT_IN_IO_OPS_H
#define PYTRA_NATIVE_BUILT_IN_IO_OPS_H

#include <iostream>

#include "runtime/cpp/generated/built_in/io_ops.h"
#include "runtime/cpp/core/py_runtime.h"

inline void py_print(const object& v) {
    ::std::cout << py_to_string(v) << ::std::endl;
}

inline void py_print(bool v) {
    ::std::cout << (v ? "True" : "False") << ::std::endl;
}

template <class T, ::std::enable_if_t<!::std::is_same_v<T, object> && !::std::is_same_v<T, bool>, int> = 0>
inline void py_print(const T& v) {
    ::std::cout << v << ::std::endl;
}

template <class T, class... Rest>
inline void py_print(const T& first, const Rest&... rest) {
    ::std::cout << py_to_string(first);
    ((::std::cout << " " << py_to_string(rest)), ...);
    ::std::cout << ::std::endl;
}

#endif  // PYTRA_NATIVE_BUILT_IN_IO_OPS_H
