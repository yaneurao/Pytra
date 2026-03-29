#ifndef PYTRA_BUILT_IN_ZIP_OPS_H
#define PYTRA_BUILT_IN_ZIP_OPS_H

#include <tuple>
#include "core/py_types.h"

// py_zip: zip two lists into a list of 2-tuples (shortest-length truncation).
template <class A, class B>
static inline list<::std::tuple<A, B>> py_zip(const list<A>& a, const list<B>& b) {
    list<::std::tuple<A, B>> result;
    const ::std::size_t n = ::std::min(a.size(), b.size());
    result.reserve(n);
    for (::std::size_t i = 0; i < n; ++i) {
        result.push_back({a[i], b[i]});
    }
    return result;
}

template <class A, class B>
static inline list<::std::tuple<A, B>> py_zip(const Object<list<A>>& a, const Object<list<B>>& b) {
    if (!a || !b) return list<::std::tuple<A, B>>{};
    return py_zip(*a, *b);
}

template <class A, class B>
static inline list<::std::tuple<A, B>> py_zip(const Object<list<A>>& a, const list<B>& b) {
    if (!a) return list<::std::tuple<A, B>>{};
    return py_zip(*a, b);
}

template <class A, class B>
static inline list<::std::tuple<A, B>> py_zip(const list<A>& a, const Object<list<B>>& b) {
    if (!b) return list<::std::tuple<A, B>>{};
    return py_zip(a, *b);
}

// py_sum: sum all elements of a list (returns 0 for empty list).
template <class T>
static inline T py_sum(const list<T>& v) {
    T acc = T{};
    for (const auto& x : v) acc += x;
    return acc;
}

template <class T>
static inline T py_sum(const Object<list<T>>& v) {
    if (!v) return T{};
    return py_sum(*v);
}

template <class T, class S>
static inline T py_sum(const list<T>& v, const S& start) {
    T acc = static_cast<T>(start);
    for (const auto& x : v) acc += x;
    return acc;
}

template <class T, class S>
static inline T py_sum(const Object<list<T>>& v, const S& start) {
    if (!v) return static_cast<T>(start);
    return py_sum(*v, start);
}

#endif  // PYTRA_BUILT_IN_ZIP_OPS_H
