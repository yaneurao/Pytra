// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/predicates.py
// generated-by: src/backends/cpp/cli.py
#include "runtime/cpp/core/py_runtime.h"

#include "runtime/cpp/generated/built_in/predicates.h"


/* Pure-Python source-of-truth for predicate helpers. */

bool py_any(const object& values) {
    int64 i = 0;
    int64 n = py_len(values);
    while (i < n) {
        if (py_to<bool>(py_at(values, py_to<int64>(i))))
            return true;
        i++;
    }
    return false;
}

bool py_all(const object& values) {
    int64 i = 0;
    int64 n = py_len(values);
    while (i < n) {
        if (!(py_to<bool>(py_at(values, py_to<int64>(i)))))
            return false;
        i++;
    }
    return true;
}
