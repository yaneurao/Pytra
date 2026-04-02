#ifndef PYTRA_BUILT_IN_DICT_OPS_H
#define PYTRA_BUILT_IN_DICT_OPS_H

#include <stdexcept>
#include "core/py_types.h"

template <class K, class V, class Q>
static inline V& py_at(dict<K, V>& d, const Q& key) {
    const K k = [&]() -> K {
        if constexpr (py_is_cstr_like<Q>::value) {
            return py_coerce_cstr_typed_value<K>(key);
        } else if constexpr (::std::is_same_v<K, Q>) {
            return key;
        } else if constexpr (::std::is_convertible_v<Q, K>) {
            return static_cast<K>(key);
        } else {
            return K(key);
        }
    }();
    auto it = d.find(k);
    if (it == d.end()) {
        throw ::std::out_of_range("dict key not found");
    }
    return it->second;
}

template <class K, class V, class Q>
static inline const V& py_at(const dict<K, V>& d, const Q& key) {
    const K k = [&]() -> K {
        if constexpr (py_is_cstr_like<Q>::value) {
            return py_coerce_cstr_typed_value<K>(key);
        } else if constexpr (::std::is_same_v<K, Q>) {
            return key;
        } else if constexpr (::std::is_convertible_v<Q, K>) {
            return static_cast<K>(key);
        } else {
            return K(key);
        }
    }();
    auto it = d.find(k);
    if (it == d.end()) {
        throw ::std::out_of_range("dict key not found");
    }
    return it->second;
}

template <class K, class V, class Q>
static inline V& py_at(Object<dict<K, V>>& d, const Q& key) {
    return py_at(*d, key);
}

template <class K, class V, class Q>
static inline const V& py_at(const Object<dict<K, V>>& d, const Q& key) {
    return py_at(*d, key);
}

template <class K, class V, class Q>
static inline V py_dict_get(const dict<K, V>& d, const Q& key) {
    const K k = [&]() -> K {
        if constexpr (py_is_cstr_like<Q>::value) {
            return py_coerce_cstr_typed_value<K>(key);
        } else if constexpr (::std::is_same_v<K, Q>) {
            return key;
        } else if constexpr (::std::is_convertible_v<Q, K>) {
            return static_cast<K>(key);
        } else {
            return K(key);
        }
    }();
    return d.get(k);
}

template <class K, class V, class Q>
static inline V py_dict_get(const Object<dict<K, V>>& d, const Q& key) {
    return py_dict_get(*d, key);
}

// py_dict_get_opt: dict.get(key) with no default → returns None (empty optional) if key absent.
template <class K, class V, class Q>
static inline ::std::optional<V> py_dict_get_opt(const dict<K, V>& d, const Q& key) {
    const K k = [&]() -> K {
        if constexpr (py_is_cstr_like<Q>::value) {
            return py_coerce_cstr_typed_value<K>(key);
        } else if constexpr (::std::is_same_v<K, Q>) {
            return key;
        } else if constexpr (::std::is_convertible_v<Q, K>) {
            return static_cast<K>(key);
        } else {
            return K(key);
        }
    }();
    auto it = d.find(k);
    if (it == d.end()) return ::std::nullopt;
    return it->second;
}

template <class K, class V, class Q>
static inline ::std::optional<V> py_dict_get_opt(const Object<dict<K, V>>& d, const Q& key) {
    return py_dict_get_opt(*d, key);
}

template <class K, class V, class Q, class D>
static inline V py_dict_get(const dict<K, V>& d, const Q& key, const D& default_value) {
    const K k = [&]() -> K {
        if constexpr (py_is_cstr_like<Q>::value) {
            return py_coerce_cstr_typed_value<K>(key);
        } else if constexpr (::std::is_same_v<K, Q>) {
            return key;
        } else if constexpr (::std::is_convertible_v<Q, K>) {
            return static_cast<K>(key);
        } else {
            return K(key);
        }
    }();
    auto it = d.find(k);
    if (it != d.end()) {
        return it->second;
    }
    if constexpr (::std::is_same_v<V, D>) {
        return default_value;
    } else if constexpr (::std::is_convertible_v<D, V>) {
        return static_cast<V>(default_value);
    } else {
        return V(default_value);
    }
}

template <class K, class V, class Q, class D>
static inline V py_dict_get(const Object<dict<K, V>>& d, const Q& key, const D& default_value) {
    return py_dict_get(*d, key, default_value);
}

template <class K, class V>
static inline void py_dict_clear_mut(dict<K, V>& d) {
    d.clear();
}

template <class K, class V>
static inline void py_dict_clear_mut(Object<dict<K, V>>& d) {
    py_dict_clear_mut(*d);
}

template <class K, class V, class Q>
static inline V py_dict_pop_mut(dict<K, V>& d, const Q& key) {
    const K k = [&]() -> K {
        if constexpr (py_is_cstr_like<Q>::value) {
            return py_coerce_cstr_typed_value<K>(key);
        } else if constexpr (::std::is_same_v<K, Q>) {
            return key;
        } else if constexpr (::std::is_convertible_v<Q, K>) {
            return static_cast<K>(key);
        } else {
            return K(key);
        }
    }();
    return d.pop(k);
}

template <class K, class V, class Q>
static inline V py_dict_pop_mut(Object<dict<K, V>>& d, const Q& key) {
    return py_dict_pop_mut(*d, key);
}

template <class K, class V, class Q, class D>
static inline V py_dict_pop_mut(dict<K, V>& d, const Q& key, const D& default_value) {
    const K k = [&]() -> K {
        if constexpr (py_is_cstr_like<Q>::value) {
            return py_coerce_cstr_typed_value<K>(key);
        } else if constexpr (::std::is_same_v<K, Q>) {
            return key;
        } else if constexpr (::std::is_convertible_v<Q, K>) {
            return static_cast<K>(key);
        } else {
            return K(key);
        }
    }();
    if constexpr (::std::is_same_v<V, D>) {
        return d.pop(k, default_value);
    } else if constexpr (::std::is_convertible_v<D, V>) {
        return d.pop(k, static_cast<V>(default_value));
    } else {
        return d.pop(k, V(default_value));
    }
}

template <class K, class V, class Q, class D>
static inline V py_dict_pop_mut(Object<dict<K, V>>& d, const Q& key, const D& default_value) {
    return py_dict_pop_mut(*d, key, default_value);
}

template <class K, class V, class Q>
static inline V py_dict_setdefault_mut(dict<K, V>& d, const Q& key) {
    const K k = [&]() -> K {
        if constexpr (py_is_cstr_like<Q>::value) {
            return py_coerce_cstr_typed_value<K>(key);
        } else if constexpr (::std::is_same_v<K, Q>) {
            return key;
        } else if constexpr (::std::is_convertible_v<Q, K>) {
            return static_cast<K>(key);
        } else {
            return K(key);
        }
    }();
    return d.setdefault(k);
}

template <class K, class V, class Q>
static inline V py_dict_setdefault_mut(Object<dict<K, V>>& d, const Q& key) {
    return py_dict_setdefault_mut(*d, key);
}

template <class K, class V, class Q, class D>
static inline V py_dict_setdefault_mut(dict<K, V>& d, const Q& key, const D& default_value) {
    const K k = [&]() -> K {
        if constexpr (py_is_cstr_like<Q>::value) {
            return py_coerce_cstr_typed_value<K>(key);
        } else if constexpr (::std::is_same_v<K, Q>) {
            return key;
        } else if constexpr (::std::is_convertible_v<Q, K>) {
            return static_cast<K>(key);
        } else {
            return K(key);
        }
    }();
    if constexpr (::std::is_same_v<V, D>) {
        return d.setdefault(k, default_value);
    } else if constexpr (::std::is_convertible_v<D, V>) {
        return d.setdefault(k, static_cast<V>(default_value));
    } else {
        return d.setdefault(k, V(default_value));
    }
}

template <class K, class V, class Q, class D>
static inline V py_dict_setdefault_mut(Object<dict<K, V>>& d, const Q& key, const D& default_value) {
    return py_dict_setdefault_mut(*d, key, default_value);
}

template <class K, class V>
static inline list<::std::tuple<K, V>> py_dict_items(const dict<K, V>& d) {
    return d.items();
}

template <class K, class V>
static inline list<::std::tuple<K, V>> py_dict_items(const Object<dict<K, V>>& d) {
    return py_dict_items(*d);
}

template <class K, class V>
static inline list<K> py_dict_keys(const dict<K, V>& d) {
    return d.keys();
}

template <class K, class V>
static inline list<K> py_dict_keys(const Object<dict<K, V>>& d) {
    return py_dict_keys(*d);
}

template <class K, class V>
static inline list<V> py_dict_values(const dict<K, V>& d) {
    return d.values();
}

template <class K, class V>
static inline list<V> py_dict_values(const Object<dict<K, V>>& d) {
    return py_dict_values(*d);
}

template <class T>
static inline int64 py_index(const list<T>& v, const T& item) {
    return v.index(item);
}

template <class T>
static inline int64 py_index(const Object<list<T>>& v, const T& item) {
    return py_index(*v, item);
}

// py_index for str list with char (string iteration over str yields char in C++)
static inline int64 py_index(const list<str>& v, char ch) {
    return v.index(str(1, (unsigned char)ch));
}
static inline int64 py_index(const Object<list<str>>& v, char ch) {
    return py_index(*v, ch);
}

// py_at for tuple (runtime index → object conversion)
template <class... Ts>
static inline object py_at(const ::std::tuple<Ts...>& t, int64 idx) {
    object result;
    int64 cur = 0;
    ::std::apply([&](const auto&... args) {
        ((cur++ == idx ? (result = object(args), true) : false) || ...);
    }, t);
    return result;
}

template <class... Ts>
static inline object py_at(const ::std::tuple<Ts...>& t, int idx) {
    return py_at(t, static_cast<int64>(idx));
}

#endif  // PYTRA_BUILT_IN_DICT_OPS_H
