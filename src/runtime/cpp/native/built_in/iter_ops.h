#ifndef PYTRA_NATIVE_BUILT_IN_ITER_OPS_H
#define PYTRA_NATIVE_BUILT_IN_ITER_OPS_H

#include "runtime/cpp/generated/built_in/iter_ops.h"

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

static inline list<object> py_reversed(const object& values) {
    return list<object>(py_reversed_object(values));
}

static inline list<::std::any> py_reversed(const ::std::any& values) {
    if (const auto* p = ::std::any_cast<list<::std::any>>(&values)) return py_reversed(*p);
    return {};
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

static inline list<object> py_enumerate(const object& values) {
    return list<object>(py_enumerate_object(values, 0));
}

static inline list<object> py_enumerate(const object& values, int64 start) {
    return list<object>(py_enumerate_object(values, start));
}

template <class T>
static inline list<::std::tuple<int64, T>> py_enumerate_list_as(const object& values, int64 start) {
    list<::std::tuple<int64, T>> out;
    if (const auto* p = obj_to_list_ptr(values)) {
        out.reserve(p->size());
        for (::std::size_t i = 0; i < p->size(); ++i) {
            out.append(::std::make_tuple(start + static_cast<int64>(i), py_to<T>((*p)[i])));
        }
    }
    return out;
}

template <class T>
static inline list<::std::tuple<int64, T>> py_enumerate_list_as(const object& values) {
    return py_enumerate_list_as<T>(values, 0);
}

static inline list<::std::tuple<int64, ::std::any>> py_enumerate(const ::std::any& values) {
    if (const auto* p = ::std::any_cast<list<::std::any>>(&values)) return py_enumerate(*p);
    if (const auto* p = ::std::any_cast<str>(&values)) return py_enumerate(*p);
    return {};
}

static inline list<::std::tuple<int64, ::std::any>> py_enumerate(const ::std::any& values, int64 start) {
    if (const auto* p = ::std::any_cast<list<::std::any>>(&values)) return py_enumerate(*p, start);
    if (const auto* p = ::std::any_cast<str>(&values)) return py_enumerate(*p, start);
    return {};
}

#endif  // PYTRA_NATIVE_BUILT_IN_ITER_OPS_H
