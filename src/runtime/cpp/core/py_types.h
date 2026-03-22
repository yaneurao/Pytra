#ifndef PYTRA_BUILT_IN_PY_TYPES_H
#define PYTRA_BUILT_IN_PY_TYPES_H

#include <algorithm>
#include <any>
#include <cctype>
#include <deque>
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
#include "core/gc.h"
#include "core/io.h"

// Legacy aliases — kept for backward compatibility with generated runtime .cpp
// TODO: remove once all generated code is regenerated without rc<T>/RcObject
using RcObject = pytra::gc::RcObject;
template <class T>
using rc = pytra::gc::RcHandle<T>;
template <class T, class... Args>
static inline rc<T> rc_new(Args&&... args) {
    return rc<T>::adopt(pytra::gc::rc_new<T>(::std::forward<Args>(args)...));
}

class str;

class str;
template <class T> class list;
template <class K, class V> class dict;

// Forward declare Object<T> so list/dict constructors can reference it.
template <typename T> struct Object;

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

// POD boxing for Object<void> (= object)
// These create a heap-allocated boxed value wrapped in ControlBlock.
template<typename T>
struct PyBoxedValue {
    T value;
    PyBoxedValue(T v) : value(::std::move(v)) {}
};

// Object<void>::unbox — deferred definition (PyBoxedValue must be complete)
template<typename T, uint32_t TID>
inline const T& Object<void>::unbox() const {
    return static_cast<PyBoxedValue<T>*>(cb->base_ptr)->value;
}

inline Object<void>::Object(int64 v) : cb(nullptr) {
    auto* boxed = new PyBoxedValue<int64>(v);
    cb = new ControlBlock{0, PYTRA_TID_INT, boxed};
    retain();
}

inline Object<void>::Object(int v) : Object(static_cast<int64>(v)) {}

inline Object<void>::Object(const char* v) : cb(nullptr) {
    auto* boxed = new PyBoxedValue<str>(str(v));
    cb = new ControlBlock{0, PYTRA_TID_STR, boxed};
    retain();
}

inline Object<void>::Object(float64 v) : cb(nullptr) {
    auto* boxed = new PyBoxedValue<float64>(v);
    cb = new ControlBlock{0, PYTRA_TID_FLOAT, boxed};
    retain();
}

inline Object<void>::Object(bool v) : cb(nullptr) {
    auto* boxed = new PyBoxedValue<bool>(v);
    cb = new ControlBlock{0, PYTRA_TID_BOOL, boxed};
    retain();
}

inline Object<void>::Object(const str& v) : cb(nullptr) {
    auto* boxed = new PyBoxedValue<str>(v);
    cb = new ControlBlock{0, PYTRA_TID_STR, boxed};
    retain();
}

inline Object<void>::Object(::std::size_t v) : Object(static_cast<int64>(v)) {}

#endif  // PYTRA_BUILT_IN_PY_TYPES_H
