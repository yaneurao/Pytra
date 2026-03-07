// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/iter_ops.py
// generated-by: src/backends/cpp/cli.py
#include "runtime/cpp/core/py_runtime.h"

#include "runtime/cpp/generated/built_in/iter_ops.h"


/* Pure-Python source-of-truth for object-based iterator helpers. */

object py_reversed_object(const object& values) {
    object out = make_object(list<object>{});
    int64 i = py_len(values) - 1;
    while (i >= 0) {
        py_append(out, make_object(py_at(values, py_to<int64>(i))));
        i--;
    }
    return make_object(out);
}

object py_enumerate_object(const object& values, int64 start = 0) {
    object out = make_object(list<object>{});
    int64 i = 0;
    int64 n = py_len(values);
    while (i < n) {
        py_append(out, make_object(list<object>{make_object(start + i), make_object(py_at(values, py_to<int64>(i)))}));
        i++;
    }
    return make_object(out);
}
