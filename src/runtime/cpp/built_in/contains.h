#ifndef PYTRA_NATIVE_BUILT_IN_CONTAINS_H
#define PYTRA_NATIVE_BUILT_IN_CONTAINS_H

#include "built_in/contains.h"

template <class T, class Q>
static inline bool py_list_contains_ref(const list<T>& values, const Q& key) {
    return ::std::find(values.begin(), values.end(), key) != values.end();
}

template <class K, class V, class Q>
static inline bool py_contains(const dict<K, V>& d, const Q& key) {
    if constexpr (::std::is_same_v<K, Q>) {
        return d.find(key) != d.end();
    } else if constexpr (::std::is_convertible_v<Q, K>) {
        return d.find(static_cast<K>(key)) != d.end();
    } else {
        return d.find(K(key)) != d.end();
    }
}

template <class V, class Q>
static inline bool py_contains(const dict<str, V>& d, const Q& key) {
    return d.find(str(py_to_string(key))) != d.end();
}

template <class T, class Q>
static inline bool py_contains(const list<T>& values, const Q& key) {
    return py_list_contains_ref(values, key);
}

template <class T, class Q>
static inline bool py_contains(const rc<list<T>>& values, const Q& key) {
    return py_list_contains_ref(rc_list_ref(values), key);
}

template <class T, class Q>
static inline bool py_contains(const Object<list<T>>& values, const Q& key) {
    return py_list_contains_ref(*values, key);
}

template <class T, class Q>
static inline bool py_contains(const set<T>& values, const Q& key) {
    return values.find(static_cast<T>(key)) != values.end();
}

template <class Q>
static inline bool py_contains(const str& values, const Q& key) {
    const str key_str = str(py_to_string(key));
    return values.find(key_str) != str::npos;
}

template <class Tup, class V>
static inline bool py_tuple_contains(const Tup& tup, const V& value) {
    bool found = false;
    ::std::apply(
        [&](const auto&... elems) {
            ((found = found || (elems == value)), ...);
        },
        tup);
    return found;
}

template <class... Ts, class V>
static inline bool py_contains(const ::std::tuple<Ts...>& values, const V& key) {
    return py_tuple_contains(values, key);
}

#endif  // PYTRA_NATIVE_BUILT_IN_CONTAINS_H
