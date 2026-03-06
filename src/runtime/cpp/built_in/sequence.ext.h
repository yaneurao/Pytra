#ifndef PYTRA_BUILT_IN_SEQUENCE_EXT_H
#define PYTRA_BUILT_IN_SEQUENCE_EXT_H

#include "runtime/cpp/core/py_types.ext.h"

template <class T>
static inline list<T> py_repeat(const list<T>& v, int64 n) {
    list<T> out;
    if (n <= 0) return out;
    out.reserve(v.size() * static_cast<::std::size_t>(n));
    for (int64 i = 0; i < n; ++i) {
        out.insert(out.end(), v.begin(), v.end());
    }
    return out;
}

#endif  // PYTRA_BUILT_IN_SEQUENCE_EXT_H
