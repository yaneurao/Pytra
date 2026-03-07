#ifndef PYTRA_NATIVE_BUILT_IN_CONTAINS_H
#define PYTRA_NATIVE_BUILT_IN_CONTAINS_H

#include "runtime/cpp/generated/built_in/contains.h"

template <class T, class Q>
static inline bool py_list_contains_ref(const list<T>& values, const Q& key) {
    return ::std::find(values.begin(), values.end(), key) != values.end();
}

template <class K, class V, class Q>
static inline bool py_contains(const dict<K, V>& d, const Q& key) {
    return d.find(py_dict_key_cast<K>(key)) != d.end();
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
static inline bool py_contains(const set<T>& values, const Q& key) {
    return values.find(static_cast<T>(key)) != values.end();
}

template <class Q>
static inline bool py_contains(const str& values, const Q& key) {
    return py_contains_str_object(make_object(values), make_object(key));
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

template <class Q>
static inline bool py_contains(const object& values, const Q& key) {
    if (const auto* d = obj_to_dict_ptr(values)) {
        return py_contains_dict_object(values, make_object(key));
    }
    if (const auto* lst = obj_to_list_ptr(values)) {
        return py_contains_list_object(values, make_object(key));
    }
    if (const auto* st = obj_to_set_ptr(values)) {
        return py_contains_set_object(values, make_object(key));
    }
    if (const auto* s = py_obj_cast<PyStrObj>(values)) {
        return py_contains_str_object(values, make_object(key));
    }
    return false;
}

#endif  // PYTRA_NATIVE_BUILT_IN_CONTAINS_H
