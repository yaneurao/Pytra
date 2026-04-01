#ifndef PYTRA_BUILT_IN_PY_TYPES_H
#define PYTRA_BUILT_IN_PY_TYPES_H

#include <algorithm>
#include <any>
#include <cctype>
#include <deque>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <tuple>
#include <type_traits>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <variant>
#include <vector>

#include "core/py_scalar_types.h"
#include "core/io.h"

class str;

class str;
template <class T> class list;
template <class K, class V> class dict;

// Forward declare Object<T> so list/dict constructors can reference it.
template <typename T> struct Object;

namespace pytra::runtime::cpp::detail {

template <class T>
inline void hash_combine(::std::size_t& seed, const T& value) {
    seed ^= ::std::hash<T>{}(value) + 0x9e3779b97f4a7c15ULL + (seed << 6U) + (seed >> 2U);
}

template <class Tuple, ::std::size_t... I>
inline ::std::size_t tuple_hash_impl(const Tuple& value, ::std::index_sequence<I...>) {
    ::std::size_t seed = 0;
    (hash_combine(seed, ::std::get<I>(value)), ...);
    return seed;
}

}  // namespace pytra::runtime::cpp::detail

namespace std {

template <class... Ts>
struct hash<::std::tuple<Ts...>> {
    ::std::size_t operator()(const ::std::tuple<Ts...>& value) const noexcept {
        return ::pytra::runtime::cpp::detail::tuple_hash_impl(value, ::std::index_sequence_for<Ts...>{});
    }
};

}  // namespace std

#include "core/str.h"
#include "core/list.h"
#include "core/dict.h"
#include "core/set.h"

// Object<T> support — include after list/dict/set are complete.
#include "core/object.h"

template <class T>
struct py_is_rc_list_handle : ::std::false_type {};

template <class T>
struct py_is_rc_list_handle<Object<list<T>>> : ::std::true_type {
    using item_type = T;
};

// Object<list<T>> based list helpers (requires Object<T> to be defined).

template <class T>
static inline Object<list<T>> rc_list_new() {
    return make_object<list<T>>(PYTRA_TID_LIST);
}

template <class T>
static inline Object<list<T>> rc_list_from_value(list<T> values) {
    return make_object<list<T>>(PYTRA_TID_LIST, ::std::move(values));
}

template <class T>
static inline list<T>& rc_list_ref(Object<list<T>>& values) {
    return *values;
}

template <class T>
static inline const list<T>& rc_list_ref(const Object<list<T>>& values) {
    return *values;
}

template <class T>
static inline list<T> rc_list_copy_value(const Object<list<T>>& values) {
    if (!values) {
        return list<T>{};
    }
    return *values;
}

template <class K, class V>
static inline Object<dict<K, V>> rc_dict_new() {
    return make_object<dict<K, V>>(PYTRA_TID_DICT);
}

template <class K, class V>
static inline Object<dict<K, V>> rc_dict_from_value(dict<K, V> values) {
    return make_object<dict<K, V>>(PYTRA_TID_DICT, ::std::move(values));
}

// Identity overload: pass-through when already Object<dict<K,V>>.
template <class K, class V>
static inline Object<dict<K, V>> rc_dict_from_value(Object<dict<K, V>> v) {
    return v;
}

template <class K, class V>
static inline dict<K, V>& rc_dict_ref(Object<dict<K, V>>& values) {
    return *values;
}

template <class K, class V>
static inline const dict<K, V>& rc_dict_ref(const Object<dict<K, V>>& values) {
    return *values;
}

template <class K, class V>
static inline dict<K, V> rc_dict_copy_value(const Object<dict<K, V>>& values) {
    if (!values) {
        return dict<K, V>{};
    }
    return *values;
}

template <class T>
static inline Object<set<T>> rc_set_new() {
    return make_object<set<T>>(PYTRA_TID_SET);
}

template <class T>
static inline Object<set<T>> rc_set_from_value(set<T> values) {
    return make_object<set<T>>(PYTRA_TID_SET, ::std::move(values));
}

// Identity overload: pass-through when already Object<set<T>>.
template <class T>
static inline Object<set<T>> rc_set_from_value(Object<set<T>> v) {
    return v;
}

template <class T>
static inline set<T>& rc_set_ref(Object<set<T>>& values) {
    return *values;
}

template <class T>
static inline const set<T>& rc_set_ref(const Object<set<T>>& values) {
    return *values;
}

template <class T>
static inline set<T> rc_set_copy_value(const Object<set<T>>& values) {
    if (!values) {
        return set<T>{};
    }
    return *values;
}

// rc_from_value: 汎用コンテナ RC ラッパー (P3-CR-CPP-S7)。
// emitter は型に関わらず rc_from_value(...) のみを使い、型ごとの分岐を持たない。
template <class T>
static inline Object<list<T>> rc_from_value(list<T> values) {
    return make_object<list<T>>(PYTRA_TID_LIST, ::std::move(values));
}
template <class T>
static inline Object<list<T>> rc_from_value(Object<list<T>> v) {
    return v;
}
template <class K, class V>
static inline Object<dict<K, V>> rc_from_value(dict<K, V> values) {
    return make_object<dict<K, V>>(PYTRA_TID_DICT, ::std::move(values));
}
template <class K, class V>
static inline Object<dict<K, V>> rc_from_value(Object<dict<K, V>> v) {
    return v;
}
template <class T>
static inline Object<set<T>> rc_from_value(set<T> values) {
    return make_object<set<T>>(PYTRA_TID_SET, ::std::move(values));
}
template <class T>
static inline Object<set<T>> rc_from_value(Object<set<T>> v) {
    return v;
}

// POD boxing for Object<void> (= object)
// These create a heap-allocated boxed value wrapped in ControlBlock.
template<typename T>
struct PyBoxedValue {
    T value;
    PyBoxedValue(T v) : value(::std::move(v)) {}
};

// Object<void>::unbox — deferred definition (PyBoxedValue must be complete)
template<typename T>
inline const T& Object<void>::unbox() const {
    return static_cast<PyBoxedValue<T>*>(cb->base_ptr)->value;
}

inline Object<void>::Object(int64 v) : cb(nullptr) {
    auto boxed = std::make_unique<PyBoxedValue<int64>>(v);
    cb = new ControlBlock{0, PYTRA_TID_INT, boxed.get(), &deleter_impl<PyBoxedValue<int64>>};
    boxed.release();
    retain();
}

inline Object<void>::Object(int v) : Object(static_cast<int64>(v)) {}

inline Object<void>::Object(const char* v) : cb(nullptr) {
    auto boxed = std::make_unique<PyBoxedValue<str>>(str(v));
    cb = new ControlBlock{0, PYTRA_TID_STR, boxed.get(), &deleter_impl<PyBoxedValue<str>>};
    boxed.release();
    retain();
}

inline Object<void>::Object(float64 v) : cb(nullptr) {
    auto boxed = std::make_unique<PyBoxedValue<float64>>(v);
    cb = new ControlBlock{0, PYTRA_TID_FLOAT, boxed.get(), &deleter_impl<PyBoxedValue<float64>>};
    boxed.release();
    retain();
}

inline Object<void>::Object(bool v) : cb(nullptr) {
    auto boxed = std::make_unique<PyBoxedValue<bool>>(v);
    cb = new ControlBlock{0, PYTRA_TID_BOOL, boxed.get(), &deleter_impl<PyBoxedValue<bool>>};
    boxed.release();
    retain();
}

inline Object<void>::Object(const str& v) : cb(nullptr) {
    auto boxed = std::make_unique<PyBoxedValue<str>>(v);
    cb = new ControlBlock{0, PYTRA_TID_STR, boxed.get(), &deleter_impl<PyBoxedValue<str>>};
    boxed.release();
    retain();
}

inline Object<void>::Object(::std::size_t v) : Object(static_cast<int64>(v)) {}

#endif  // PYTRA_BUILT_IN_PY_TYPES_H
