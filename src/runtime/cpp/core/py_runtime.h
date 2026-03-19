#ifndef PYTRA_BUILT_IN_PY_RUNTIME_H
#define PYTRA_BUILT_IN_PY_RUNTIME_H

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <optional>
#include <sstream>
#include <variant>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <tuple>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

#include "py_types.h"
#include "exceptions.h"
#include "io.h"

// base_ops.h provides py_str_slice / py_find_window used by generated string_ops.h.
#include "runtime/cpp/built_in/base_ops.h"

// Generated string helpers (py_split, py_join, py_count, etc.).
#include "runtime/cpp/generated/built_in/string_ops.h"

// PYTRA_TID_* 定数は py_scalar_types.h へ移動済み（P2-COMPILE-LINK-PIPELINE-01）。

inline list<str> str::split(const str& sep, int64 maxsplit) const {
    return py_split(*this, sep, maxsplit);
}

inline list<str> str::split(const str& sep) const {
    return split(sep, -1);
}

inline list<str> str::splitlines() const {
    return py_splitlines(*this);
}

inline int64 str::count(const str& needle) const {
    return py_count(*this, needle);
}

inline str str::join(const list<str>& parts) const {
    return py_join(*this, parts);
}

// py_to_string は base_ops.h へ移動済み（P6-EAST3-PY-TO-STRING-INLINE-01）。

template <class T>
static inline T py_to(const T& v);

template <class T>
static inline bool py_to_bool(const rc<list<T>>& v) {
    return v && !v->empty();
}

static inline bool py_to_bool(bool v) {
    return py_to<bool>(v);
}

// py_variant_to_bool: std::variant を Python の bool() 相当に変換する。
// emitter が bool(variant_val) を生成する際に使用する。
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

// リスト操作（at / append_mut 等）は native/built_in/list_ops.h へ移動済み。
// py_slice（list/rc 版）は emitter が py_list_slice_copy を直接 emit するため除去。
#include "runtime/cpp/built_in/list_ops.h"

// list/rc<list> 版の py_at は除去済み（P6-EAST3-PY-AT-INLINE-01）。
// emitter は py_list_at_ref を直接 emit する。

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

template <class T>
static inline int64 py_index(const list<T>& v, const T& item) {
    return v.index(item);
}

template <class Seq>
static inline decltype(auto) py_at_bounds(Seq& v, int64 idx) {
    const int64 n = py_len(v);
    if (idx < 0 || idx >= n) throw ::std::out_of_range("index out of range");
    return v[static_cast<::std::size_t>(idx)];
}

template <class Seq>
static inline decltype(auto) py_at_bounds(const Seq& v, int64 idx) {
    const int64 n = py_len(v);
    if (idx < 0 || idx >= n) throw ::std::out_of_range("index out of range");
    return v[static_cast<::std::size_t>(idx)];
}

template <class Seq>
static inline decltype(auto) py_at_bounds_debug(Seq& v, int64 idx) {
#ifndef NDEBUG
    return py_at_bounds(v, idx);
#else
    return v[static_cast<::std::size_t>(idx)];
#endif
}

template <class Seq>
static inline decltype(auto) py_at_bounds_debug(const Seq& v, int64 idx) {
#ifndef NDEBUG
    return py_at_bounds(v, idx);
#else
    return v[static_cast<::std::size_t>(idx)];
#endif
}

// py_is_none は native/built_in/base_ops.h へ移動済み（P6-EAST3-IS-NONE-INLINE-01）。

// P0-contract-shrink label: shared_type_id_contract seam.
// type_id 判定ロジックは generated built_in 層（py_tid_*）を正本とする。
#include "runtime/cpp/generated/built_in/type_id.h"

// Runtime type_id registration machinery removed (P2-COMPILE-LINK-PIPELINE-01).
// Type IDs are now assigned by the linker at compile time.
// py_tid_register_known_class_type() is called from generated __pytra_init_type_ids() in main().

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
    pytra_type_id out = v->py_type_id();
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

template <class T>
static inline pytra_type_id py_runtime_value_type_id(const rc<T>& value) {
    if (!value) return PYTRA_TID_NONE;
    pytra_type_id out = value->py_type_id();
    return out == 0 ? PYTRA_TID_OBJECT : out;
}

template <class T>
static inline bool py_runtime_value_isinstance(const T& value, pytra_type_id expected_type_id) {
    return py_runtime_type_id_is_subtype(py_runtime_value_type_id(value), expected_type_id);
}

// Specialization for user-defined ref classes that inherit RcObject.
// Uses the virtual py_type_id() on the RcObject base.
template <class T, ::std::enable_if_t<::std::is_base_of_v<RcObject, T>, int> = 0>
static inline bool py_runtime_value_isinstance(const rc<T>& value, pytra_type_id expected_type_id) {
    if (!value) return expected_type_id == PYTRA_TID_NONE;
    return py_runtime_type_id_is_subtype(value->py_type_id(), expected_type_id);
}

template <class T, ::std::enable_if_t<::std::is_arithmetic_v<T>, int> = 0>
static inline auto operator-(const rc<T>& v) -> decltype(v->__neg__()) {
    return v->__neg__();
}

// py_div / py_floordiv / py_mod は native/built_in/scalar_ops.h へ移動済み。

#endif  // PYTRA_BUILT_IN_PY_RUNTIME_H
