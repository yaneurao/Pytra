#ifndef PYTRA_NATIVE_BUILT_IN_BASE_OPS_H
#define PYTRA_NATIVE_BUILT_IN_BASE_OPS_H

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

template <class T>
static inline int64 py_len(const T& v) {
    return static_cast<int64>(v.size());
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
    ::std::ostringstream oss;
    oss << v;
    return oss.str();
}

static inline ::std::string py_to_string(const ::std::string& v) {
    return v;
}

static inline ::std::string py_to_string(const object& v) {
    if (!v) return "";
    if (v.type_id() == PYTRA_TID_STR)
        return static_cast<PyBoxedValue<str>*>(v.get())->value;
    if (v.type_id() == PYTRA_TID_INT)
        return ::std::to_string(static_cast<PyBoxedValue<int64>*>(v.get())->value);
    if (v.type_id() == PYTRA_TID_FLOAT)
        return ::std::to_string(static_cast<PyBoxedValue<float64>*>(v.get())->value);
    if (v.type_id() == PYTRA_TID_BOOL)
        return static_cast<PyBoxedValue<bool>*>(v.get())->value ? "True" : "False";
    return "<object>";
}

static inline ::std::string py_to_string(const ::std::exception& v) {
    return ::std::string(v.what());
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

#endif  // PYTRA_NATIVE_BUILT_IN_BASE_OPS_H
