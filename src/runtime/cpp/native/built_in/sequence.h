#ifndef PYTRA_NATIVE_BUILT_IN_SEQUENCE_H
#define PYTRA_NATIVE_BUILT_IN_SEQUENCE_H

#include "runtime/cpp/core/py_types.ext.h"

template <class T>
static inline list<T> py_repeat_list_copy(const list<T>& v, int64 n) {
    list<T> out;
    if (n <= 0) return out;
    out.reserve(v.size() * static_cast<::std::size_t>(n));
    for (int64 i = 0; i < n; ++i) {
        out.insert(out.end(), v.begin(), v.end());
    }
    return out;
}

template <class T>
static inline list<T> py_repeat(const list<T>& v, int64 n) {
    return py_repeat_list_copy(v, n);
}

template <class T>
static inline list<T> py_repeat(const rc<list<T>>& v, int64 n) {
    return py_repeat_list_copy(rc_list_ref(v), n);
}

#endif  // PYTRA_NATIVE_BUILT_IN_SEQUENCE_H
