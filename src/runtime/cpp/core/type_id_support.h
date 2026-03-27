#ifndef PYTRA_CORE_TYPE_ID_SUPPORT_H
#define PYTRA_CORE_TYPE_ID_SUPPORT_H

#include <type_traits>
#include "core/py_types.h"

// Forward declarations for generated type_id functions (defined in runtime/east/built_in/type_id.east).
// toolchain2 emits runtime symbols at global scope, so this header mirrors that surface.
bool py_tid_is_subtype(int64 actual_type_id, int64 expected_type_id);
bool py_tid_issubclass(int64 actual_type_id, int64 expected_type_id);
bool py_tid_isinstance(const object& value, int64 expected_type_id);
int64 py_tid_register_class_type(int64 base_type_id);
int64 py_tid_register_known_class_type(int64 type_id, int64 base_type_id);

static inline bool py_runtime_type_id_is_subtype(pytra_type_id actual_type_id, pytra_type_id expected_type_id) {
    return py_tid_is_subtype(static_cast<int64>(actual_type_id), static_cast<int64>(expected_type_id));
}

static inline bool py_runtime_type_id_issubclass(pytra_type_id actual_type_id, pytra_type_id expected_type_id) {
    return py_tid_issubclass(static_cast<int64>(actual_type_id), static_cast<int64>(expected_type_id));
}

static inline pytra_type_id py_runtime_object_type_id(const object& v) {
    if (!v) {
        return PYTRA_TID_NONE;
    }
    pytra_type_id out = v.type_id();
    if (out == 0) {
        return PYTRA_TID_OBJECT;
    }
    return out;
}

static inline bool py_runtime_object_isinstance(const object& value, pytra_type_id expected_type_id) {
    if (!value) {
        return expected_type_id == PYTRA_TID_NONE;
    }
    return py_tid_isinstance(value, static_cast<int64>(expected_type_id));
}

template <class Exact>
static inline bool py_runtime_object_exact_is(const object& value) {
    if (!value) {
        return false;
    }
    if constexpr (::std::is_same_v<Exact, bool>) return value.type_id() == PYTRA_TID_BOOL;
    else if constexpr (::std::is_same_v<Exact, int64>) return value.type_id() == PYTRA_TID_INT;
    else if constexpr (::std::is_same_v<Exact, float64>) return value.type_id() == PYTRA_TID_FLOAT;
    else if constexpr (::std::is_same_v<Exact, str>) return value.type_id() == PYTRA_TID_STR;
    else return false;
}

template <class Exact, class T>
static inline bool py_runtime_value_exact_is(const T&) {
    return ::std::is_same_v<::std::decay_t<T>, Exact>;
}

template <class Exact>
static inline bool py_runtime_value_exact_is(const object& value) {
    return py_runtime_object_exact_is<Exact>(value);
}

template <class T>
static inline pytra_type_id _py_static_type_id_for() {
    if constexpr (::std::is_same_v<T, bool>) return PYTRA_TID_BOOL;
    else if constexpr (::std::is_integral_v<T>) return PYTRA_TID_INT;
    else if constexpr (::std::is_floating_point_v<T>) return PYTRA_TID_FLOAT;
    else if constexpr (::std::is_same_v<T, str>) return PYTRA_TID_STR;
    else return PYTRA_TID_OBJECT;
}

template <class T>
static inline pytra_type_id py_runtime_value_type_id(const T& value) {
    (void)value;
    return _py_static_type_id_for<T>();
}

template <class K, class V>
static inline pytra_type_id py_runtime_value_type_id(const dict<K, V>&) { return PYTRA_TID_DICT; }

template <class T>
static inline pytra_type_id py_runtime_value_type_id(const list<T>&) { return PYTRA_TID_LIST; }

template <class T>
static inline pytra_type_id py_runtime_value_type_id(const set<T>&) { return PYTRA_TID_SET; }

// Object<T> isinstance is provided by Object<T>::isinstance(TypeInfo*) in object.h.
// Legacy rc<T>/RcObject specializations removed (Object<T> migration complete).

template <class T>
static inline bool py_runtime_value_isinstance(const T& value, pytra_type_id expected_type_id) {
    return py_runtime_type_id_is_subtype(py_runtime_value_type_id(value), expected_type_id);
}

#endif  // PYTRA_CORE_TYPE_ID_SUPPORT_H
