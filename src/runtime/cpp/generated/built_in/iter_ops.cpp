// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/iter_ops.py
// generated-by: src/backends/cpp/cli.py
#include "runtime/cpp/native/core/py_runtime.h"

#include "runtime/cpp/generated/built_in/iter_ops.h"
#include "runtime/cpp/native/core/process_runtime.h"
#include "runtime/cpp/native/core/scope_exit.h"


/* Pure-Python source-of-truth for object-based iterator helpers. */

list<object> py_reversed_object(const object& values) {
    list<object> out = list<object>{};
    int64 i = py_len(values) - 1;
    while (i >= 0) {
        out.append(make_object(py_at(values, py_to<int64>(i))));
        i--;
    }
    return out;
}

list<object> py_enumerate_object(const object& values, int64 start) {
    list<object> out = list<object>{};
    int64 i = 0;
    int64 n = py_len(values);
    while (i < n) {
        out.append(make_object(list<object>{make_object(start + i), make_object(py_at(values, py_to<int64>(i)))}));
        i++;
    }
    return out;
}
