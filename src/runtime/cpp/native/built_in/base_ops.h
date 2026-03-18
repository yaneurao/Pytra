#ifndef PYTRA_NATIVE_BUILT_IN_BASE_OPS_H
#define PYTRA_NATIVE_BUILT_IN_BASE_OPS_H

#include "runtime/cpp/native/core/py_types.h"

// 基本スカラー長さ演算・文字列スライス。
// py_runtime.h から移動（P6-EAST3-LEN-SLICE-NODE-01）。

// py_len: 各コレクション型の長さを int64 で返す。
// object 境界（型不明）の len() フォールバックとして emitter が参照する。
template <class T>
static inline int64 py_len(const rc<list<T>>& v) {
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

#endif  // PYTRA_NATIVE_BUILT_IN_BASE_OPS_H
