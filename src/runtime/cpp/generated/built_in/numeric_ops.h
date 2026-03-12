// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/numeric_ops.py
// generated-by: src/backends/cpp/cli.py

#ifndef PYTRA_GENERATED_BUILT_IN_NUMERIC_OPS_H
#define PYTRA_GENERATED_BUILT_IN_NUMERIC_OPS_H

#include "runtime/cpp/native/core/py_runtime.h"
#include "runtime/cpp/native/core/process_runtime.h"
#include "runtime/cpp/native/core/scope_exit.h"


/* Pure-Python source-of-truth for numeric helper built-ins. */

template <class T>
T sum(const list<T>& values) {
    if (values.empty())
        return 0;
    auto acc = values[0] - values[0];
    int64 i = 0;
    int64 n = py_len(values);
    while (i < n) {
        acc += values[i];
        i++;
    }
    return acc;
}

template <class T>
T py_min(const T& a, const T& b) {
    if (a < b)
        return a;
    return b;
}

template <class T>
T py_max(const T& a, const T& b) {
    if (a > b)
        return a;
    return b;
}

#endif  // PYTRA_GENERATED_BUILT_IN_NUMERIC_OPS_H
