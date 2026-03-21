#ifndef PYTRA_NATIVE_BUILT_IN_ITER_OPS_H
#define PYTRA_NATIVE_BUILT_IN_ITER_OPS_H

#include "built_in/iter_ops.h"

template <class T>
static inline list<T> py_reversed_list_copy(const list<T>& values) {
    list<T> out(values.begin(), values.end());
    ::std::reverse(out.begin(), out.end());
    return out;
}

template <class T>
static inline list<T> py_reversed(const list<T>& values) {
    return py_reversed_list_copy(values);
}

template <class T>
static inline list<T> py_reversed(const rc<list<T>>& values) {
    return py_reversed_list_copy(rc_list_ref(values));
}

template <class T>
static inline list<::std::tuple<int64, T>> py_enumerate_list_copy(const list<T>& values, int64 start) {
    list<::std::tuple<int64, T>> out;
    out.reserve(values.size());
    for (::std::size_t i = 0; i < values.size(); i++) {
        out.append(::std::make_tuple(start + static_cast<int64>(i), values[i]));
    }
    return out;
}

template <class T>
static inline list<::std::tuple<int64, T>> py_enumerate(const list<T>& values) {
    return py_enumerate_list_copy(values, 0);
}

template <class T>
static inline list<::std::tuple<int64, T>> py_enumerate(const rc<list<T>>& values) {
    return py_enumerate_list_copy(rc_list_ref(values), 0);
}

template <class T>
static inline list<::std::tuple<int64, T>> py_enumerate(const list<T>& values, int64 start) {
    return py_enumerate_list_copy(values, start);
}

template <class T>
static inline list<::std::tuple<int64, T>> py_enumerate(const rc<list<T>>& values, int64 start) {
    return py_enumerate_list_copy(rc_list_ref(values), start);
}

template <class T>
static inline list<::std::tuple<int64, T>> py_enumerate(const Object<list<T>>& values) {
    return py_enumerate_list_copy(*values, 0);
}

template <class T>
static inline list<::std::tuple<int64, T>> py_enumerate(const Object<list<T>>& values, int64 start) {
    return py_enumerate_list_copy(*values, start);
}

static inline list<::std::tuple<int64, str>> py_enumerate(const str& values) {
    list<::std::tuple<int64, str>> out;
    out.reserve(values.size());
    for (::std::size_t i = 0; i < values.size(); i++) {
        out.append(::std::make_tuple(static_cast<int64>(i), values[i]));
    }
    return out;
}

static inline list<::std::tuple<int64, str>> py_enumerate(const str& values, int64 start) {
    list<::std::tuple<int64, str>> out;
    out.reserve(values.size());
    for (::std::size_t i = 0; i < values.size(); i++) {
        out.append(::std::make_tuple(start + static_cast<int64>(i), values[i]));
    }
    return out;
}

#endif  // PYTRA_NATIVE_BUILT_IN_ITER_OPS_H
