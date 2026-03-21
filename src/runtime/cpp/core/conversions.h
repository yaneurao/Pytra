#ifndef PYTRA_CORE_CONVERSIONS_H
#define PYTRA_CORE_CONVERSIONS_H

#include <variant>
#include <type_traits>
#include "core/py_types.h"

template <class T>
static inline T py_to(const T& v);

template <class T>
static inline bool py_to_bool(const Object<list<T>>& v) {
    return v && !v->empty();
}

static inline bool py_to_bool(bool v) {
    return py_to<bool>(v);
}

template <class... Ts>
static inline bool py_variant_to_bool(const ::std::variant<Ts...>& v) {
    return ::std::visit([](const auto& x) -> bool {
        using T = ::std::decay_t<decltype(x)>;
        if constexpr (::std::is_same_v<T, ::std::monostate>) return false;
        else if constexpr (::std::is_same_v<T, bool>) return x;
        else if constexpr (::std::is_same_v<T, str>) return !x.empty();
        else if constexpr (::std::is_arithmetic_v<T>) return x != 0;
        else return true;
    }, v);
}

template <class T>
struct py_is_list_type : ::std::false_type {};

template <class T>
struct py_is_list_type<list<T>> : ::std::true_type {
    using item_type = T;
};

template <class T>
struct py_is_list_type<Object<list<T>>> : ::std::true_type {
    using item_type = T;
};

template <class T>
static inline T py_to(const T& v) {
    return v;
}

// Conversions from object (= Object<void>) to concrete types.
static inline int64 py_to_int64(int64 v) { return v; }
static inline int64 py_to_int64(float64 v) { return static_cast<int64>(v); }
static inline int64 py_to_int64(const object& v) {
    if (!v) return 0;
    return static_cast<PyBoxedValue<int64>*>(v.get())->value;
}

static inline float64 py_to_float64(float64 v) { return v; }
static inline float64 py_to_float64(int64 v) { return static_cast<float64>(v); }
static inline float64 py_to_float64(const object& v) {
    if (!v) return 0.0;
    if (v.type_id() == PYTRA_TID_INT)
        return static_cast<float64>(static_cast<PyBoxedValue<int64>*>(v.get())->value);
    return static_cast<PyBoxedValue<float64>*>(v.get())->value;
}

// py_to_string for object is in base_ops.h (overload below template).

#endif  // PYTRA_CORE_CONVERSIONS_H
