#ifndef PYTRA_NATIVE_BUILT_IN_BASE_OPS_H
#define PYTRA_NATIVE_BUILT_IN_BASE_OPS_H

#include <charconv>
#include <algorithm>
#include <cstring>
#include <limits>
#include <sstream>
#include "core/py_types.h"

// 基本スカラー長さ演算・文字列スライス。
// py_runtime.h から移動（P6-EAST3-LEN-SLICE-NODE-01）。

// py_len: 各コレクション型の長さを int64 で返す。
// object 境界（型不明）の len() フォールバックとして emitter が参照する。
template <class T>
static inline int64 py_len(const Object<list<T>>& v) {
    if (!v) return 0;
    return static_cast<int64>(v->size());
}

template <class K, class V>
static inline int64 py_len(const Object<dict<K, V>>& v) {
    if (!v) return 0;
    return static_cast<int64>(v->size());
}

template <class T>
static inline int64 py_len(const Object<set<T>>& v) {
    if (!v) return 0;
    return static_cast<int64>(v->size());
}

template <class T>
static inline int64 py_len(const T& v) {
    if constexpr (requires(const T& x) { x.__len__(); }) {
        return static_cast<int64>(v.__len__());
    } else {
        return static_cast<int64>(v.size());
    }
}

template <class T>
static inline int64 py_len(const ::std::optional<T>& v) {
    if (!v.has_value()) return 0;
    return py_len(*v);
}

template <::std::size_t N>
static inline int64 py_len(const char (&)[N]) {
    return N > 0 ? static_cast<int64>(N - 1) : 0;
}

// py_is_none: None 判定。
// emitter が型不明の場合の fallback として参照する（P6-EAST3-IS-NONE-INLINE-01）。
// optional<T> → !v.has_value()、object → !v、確定型 → 常に false。
template <class T>
static inline bool py_is_none(const ::std::optional<T>& v) { return !v.has_value(); }
static inline bool py_is_none(const object& v) { return !static_cast<bool>(v); }
template <class T>
static inline bool py_is_none(const T&) { return false; }

template <class Exact>
static inline bool py_runtime_object_exact_is(const object& value) {
    if (!value) {
        return false;
    }
    if constexpr (::std::is_same_v<Exact, bool>) return value.type_id() == ::pytra::runtime::cpp::detail::kTypeIdBool;
    else if constexpr (::std::is_same_v<Exact, int64>) return value.type_id() == ::pytra::runtime::cpp::detail::kTypeIdInt;
    else if constexpr (::std::is_same_v<Exact, float64>) return value.type_id() == ::pytra::runtime::cpp::detail::kTypeIdFloat;
    else if constexpr (::std::is_same_v<Exact, str>) return value.type_id() == ::pytra::runtime::cpp::detail::kTypeIdStr;
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

static inline bool py_is_bool(const object& v) {
    return static_cast<bool>(v) && v.type_id() == ::pytra::runtime::cpp::detail::kTypeIdBool;
}

template <class T>
static inline bool py_is_bool(const T&) {
    return ::std::is_same_v<::std::decay_t<T>, bool>;
}

static inline bool py_is_int(const object& v) {
    return static_cast<bool>(v) && v.type_id() == ::pytra::runtime::cpp::detail::kTypeIdInt;
}

template <class T>
static inline bool py_is_int(const T&) {
    using Decayed = ::std::decay_t<T>;
    return ::std::is_same_v<Decayed, int> || ::std::is_same_v<Decayed, int64>;
}

static inline bool py_is_float(const object& v) {
    return static_cast<bool>(v) && v.type_id() == ::pytra::runtime::cpp::detail::kTypeIdFloat;
}

template <class T>
static inline bool py_is_float(const T&) {
    using Decayed = ::std::decay_t<T>;
    return ::std::is_same_v<Decayed, float> || ::std::is_same_v<Decayed, float64>;
}

static inline bool py_is_str(const object& v) {
    return static_cast<bool>(v) && v.type_id() == ::pytra::runtime::cpp::detail::kTypeIdStr;
}

template <class T>
static inline bool py_is_str(const T&) {
    return ::std::is_same_v<::std::decay_t<T>, str>;
}

template <class T>
static inline bool py_is_list(const list<T>&) { return true; }

template <class T>
static inline bool py_is_list(const Object<list<T>>&) { return true; }

static inline bool py_is_list(const object& v) {
    return static_cast<bool>(v) && v.type_id() == ::pytra::runtime::cpp::detail::kTypeIdList;
}

template <class T>
static inline bool py_is_list(const T&) { return false; }

template <class K, class V>
static inline bool py_is_dict(const dict<K, V>&) { return true; }

template <class K, class V>
static inline bool py_is_dict(const Object<dict<K, V>>&) { return true; }

static inline bool py_is_dict(const object& v) {
    return static_cast<bool>(v) && v.type_id() == ::pytra::runtime::cpp::detail::kTypeIdDict;
}

template <class T>
static inline bool py_is_dict(const T&) { return false; }

template <class T>
static inline bool py_is_set(const set<T>&) { return true; }

template <class T>
static inline bool py_is_set(const Object<set<T>>&) { return true; }

static inline bool py_is_set(const object& v) {
    return static_cast<bool>(v) && v.type_id() == ::pytra::runtime::cpp::detail::kTypeIdSet;
}

template <class T>
static inline bool py_is_set(const T&) { return false; }

static inline bool py_is_object(const object&) { return true; }

template <class T>
static inline bool py_is_object(const T&) { return true; }

template <class... Ts>
static inline bool py_is_bool(const ::std::variant<Ts...>& v) {
    return ::std::visit([](const auto& item) -> bool { return py_is_bool(item); }, v);
}

template <class... Ts>
static inline bool py_is_int(const ::std::variant<Ts...>& v) {
    return ::std::visit([](const auto& item) -> bool { return py_is_int(item); }, v);
}

template <class... Ts>
static inline bool py_is_float(const ::std::variant<Ts...>& v) {
    return ::std::visit([](const auto& item) -> bool { return py_is_float(item); }, v);
}

template <class... Ts>
static inline bool py_is_str(const ::std::variant<Ts...>& v) {
    return ::std::visit([](const auto& item) -> bool { return py_is_str(item); }, v);
}

template <class... Ts>
static inline bool py_is_list(const ::std::variant<Ts...>& v) {
    return ::std::visit([](const auto& item) -> bool { return py_is_list(item); }, v);
}

template <class... Ts>
static inline bool py_is_dict(const ::std::variant<Ts...>& v) {
    return ::std::visit([](const auto& item) -> bool { return py_is_dict(item); }, v);
}

template <class... Ts>
static inline bool py_is_set(const ::std::variant<Ts...>& v) {
    return ::std::visit([](const auto& item) -> bool { return py_is_set(item); }, v);
}

template <class... Ts>
static inline bool py_is_object(const ::std::variant<Ts...>& v) {
    return ::std::visit([](const auto& item) -> bool { return py_is_object(item); }, v);
}

// py_str_slice: str のスライス（境界クランプ付き）。
// 旧 py_slice(const str&, ...) を改名。emitter は str スライス時にこちらを使用する。
static inline str py_str_slice(const str& v, int64 lo, int64 up) {
    const int64 n = static_cast<int64>(v.size());
    if (lo < 0) lo += n;
    if (up < 0) up += n;
    lo = ::std::max<int64>(0, ::std::min<int64>(lo, n));
    up = ::std::max<int64>(0, ::std::min<int64>(up, n));
    if (up < lo) up = lo;
    return v.substr(static_cast<::std::size_t>(lo), static_cast<::std::size_t>(up - lo));
}

// py_to_string: 文字列化。
// py_runtime.h から移動（P6-EAST3-PY-TO-STRING-INLINE-01）。
// emitter は型確定ケースで ::std::to_string 等にインライン化済み。
// object 境界の fallback として残す。
template <class T, ::std::enable_if_t<
    !::std::is_same_v<::std::decay_t<T>, object> &&
    !::std::is_same_v<::std::decay_t<T>, ::std::string>, int> = 0>
static inline ::std::string py_to_string(const T& v) {
    if constexpr (requires(const T& x) { x.__str__(); }) {
        return str(v.__str__()).std();
    } else {
        ::std::ostringstream oss;
        oss << v;
        return oss.str();
    }
}

static inline ::std::string py_to_string(const ::std::string& v) {
    return v;
}

static inline ::std::string py_to_string(bool v) {
    return v ? "True" : "False";
}

// Python-like float formatting: shortest round-trip representation.
// Matches Python's str(float) output (e.g. 1.2246467991473532e-16, not 1.22465e-16).
static inline ::std::string py_to_string(double v) {
    char buf[32];
    // Shortest round-trip representation (matches Python str(float) behaviour).
    auto [ptr, ec] = ::std::to_chars(buf, buf + sizeof(buf), v);
    if (ec != ::std::errc{}) {
        // Fallback for special values (inf, nan, etc.)
        ::std::ostringstream oss;
        oss << v;
        return oss.str();
    }
    ::std::string s(buf, ptr);
    if (s.find('.') == ::std::string::npos &&
        s.find('e') == ::std::string::npos &&
        s.find('n') == ::std::string::npos &&
        s.find('i') == ::std::string::npos) {
        s += ".0";
    }
    return s;
}

static inline ::std::string py_to_string(float v) {
    return py_to_string(static_cast<double>(v));
}

static inline ::std::string py_to_string(const object& v) {
    if (!v) return "";
    if (v.type_id() == ::pytra::runtime::cpp::detail::kTypeIdStr)
        return static_cast<PyBoxedValue<str>*>(v.get())->value;
    if (v.type_id() == ::pytra::runtime::cpp::detail::kTypeIdInt)
        return ::std::to_string(static_cast<PyBoxedValue<int64>*>(v.get())->value);
    if (v.type_id() == ::pytra::runtime::cpp::detail::kTypeIdFloat)
        return py_to_string(static_cast<PyBoxedValue<float64>*>(v.get())->value);
    if (v.type_id() == ::pytra::runtime::cpp::detail::kTypeIdBool)
        return static_cast<PyBoxedValue<bool>*>(v.get())->value ? "True" : "False";
    return "<object>";
}

static inline ::std::string py_to_string(uint8 v) {
    return ::std::to_string(static_cast<int>(v));
}

static inline ::std::string py_to_string(int8 v) {
    return ::std::to_string(static_cast<int>(v));
}

static inline ::std::string py_to_string(const char* v) {
    return ::std::string(v);
}

template <class T>
static inline ::std::string py_to_string(const ::std::optional<T>& v) {
    if (!v.has_value()) return "None";
    return py_to_string(*v);
}

static inline ::std::string py_repr(const str& v);
static inline ::std::string py_repr(bool v);
template <class T>
static inline ::std::string py_repr(const T& v);

template <class... Ts>
static inline ::std::string py_to_string(const ::std::variant<Ts...>& v) {
    return ::std::visit(
        [](const auto& item) -> ::std::string {
            return py_to_string(item);
        },
        v
    );
}

// optional<variant> stringification: nullopt → "None"
template <class... Ts>
static inline ::std::string py_to_string(const ::std::optional<::std::variant<Ts...>>& v) {
    if (!v.has_value()) return "None";
    return py_to_string(*v);
}

template <class... Ts>
static inline ::std::string py_to_string(const ::std::tuple<Ts...>& v) {
    ::std::string result = "(";
    bool first = true;
    ::std::apply(
        [&](const auto&... items) {
            ((result += (first ? "" : ", "), result += py_repr(items), first = false), ...);
        },
        v
    );
    if constexpr (sizeof...(Ts) == 1) {
        result += ",";
    }
    result += ")";
    return result;
}

// py_repr: Python repr()-like formatting for collection elements.
// Used by py_to_string for containers.
static inline ::std::string py_repr(const str& v) {
    return "'" + v.std() + "'";
}
static inline ::std::string py_repr(bool v) {
    return v ? "True" : "False";
}
template <class T>
static inline ::std::string py_repr(const T& v) {
    using DT = ::std::decay_t<T>;
    if constexpr (!::std::is_same_v<DT, bool> && !::std::is_arithmetic_v<DT> && ::std::is_convertible_v<T, bool>) {
        return py_repr(static_cast<bool>(v));
    }
    return py_to_string(v);
}

// py_to_string for Object<list<T>>: Python-like "[a, b, c]" format.
template <class T>
static inline ::std::string py_to_string(const Object<list<T>>& v) {
    if (!v) return "[]";
    ::std::string result = "[";
    bool first = true;
    for (const auto& elem : *v) {
        if (!first) result += ", ";
        result += py_repr(elem);
        first = false;
    }
    result += "]";
    return result;
}

// py_to_string for Object<set<T>>: Python-like "{a, b, c}" format.
template <class T>
static inline ::std::string py_to_string(const Object<set<T>>& v) {
    if (!v || v->empty()) return "set()";
    ::std::string result = "{";
    bool first = true;
    for (const auto& elem : *v) {
        if (!first) result += ", ";
        result += py_repr(elem);
        first = false;
    }
    result += "}";
    return result;
}

// py_to_string for Object<dict<K,V>>: Python-like "{k: v, ...}" format.
template <class K, class V>
static inline ::std::string py_to_string(const Object<dict<K, V>>& d) {
    if (!d) return "{}";
    ::std::vector<::std::string> entries;
    for (const auto& kv : *d) {
        entries.push_back(py_repr(kv.first) + ": " + py_repr(kv.second));
    }
    ::std::sort(entries.begin(), entries.end());
    ::std::string result = "{";
    bool first = true;
    for (const auto& entry : entries) {
        if (!first) result += ", ";
        result += entry;
        first = false;
    }
    result += "}";
    return result;
}

#endif  // PYTRA_NATIVE_BUILT_IN_BASE_OPS_H
