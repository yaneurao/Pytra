#ifndef PYTRA_BUILT_IN_ITER_OPS_EXT_H
#define PYTRA_BUILT_IN_ITER_OPS_EXT_H

#include "runtime/cpp/built_in/iter_ops.gen.h"

static inline list<object> py_reversed(const object& values) {
    return list<object>(py_reversed_object(values));
}

static inline list<object> py_enumerate(const object& values) {
    return list<object>(py_enumerate_object(values, 0));
}

static inline list<object> py_enumerate(const object& values, int64 start) {
    return list<object>(py_enumerate_object(values, start));
}

#endif  // PYTRA_BUILT_IN_ITER_OPS_EXT_H
