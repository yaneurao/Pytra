#ifndef PYTRA_CORE_CONVERSIONS_H
#define PYTRA_CORE_CONVERSIONS_H

#include <variant>
#include <type_traits>
#include "core/py_types.h"

template <class T>
static inline T py_to(const T& v);

template <class T>
static inline bool py_to_bool(const rc<list<T>>& v) {
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
struct py_is_list_type<rc<list<T>>> : ::std::true_type {
    using item_type = T;
};

template <class T>
static inline T py_to(const T& v) {
    return v;
}

#endif  // PYTRA_CORE_CONVERSIONS_H
