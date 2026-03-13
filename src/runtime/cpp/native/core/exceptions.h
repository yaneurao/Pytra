#ifndef PYTRA_BUILT_IN_EXCEPTIONS_H
#define PYTRA_BUILT_IN_EXCEPTIONS_H

#include <stdexcept>
#include <string>

using ValueError = ::std::runtime_error;
using RuntimeError = ::std::runtime_error;
using NotImplementedError = ::std::runtime_error;
using TypeError = ::std::runtime_error;
using IndexError = ::std::runtime_error;
using KeyError = ::std::runtime_error;

struct SystemExit : public ::std::runtime_error {
    int code;

    explicit SystemExit(int exit_code)
        : ::std::runtime_error("SystemExit"), code(exit_code) {}
};

#endif  // PYTRA_BUILT_IN_EXCEPTIONS_H
