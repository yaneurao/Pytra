#ifndef PYTRA_NATIVE_BUILT_IN_LIST_OPS_H
#define PYTRA_NATIVE_BUILT_IN_LIST_OPS_H

#include "core/py_runtime.h"
#include "built_in/scalar_ops.h"

// operator+ for Object<list<T>>: Python list + list concatenation.
template <class T>
static inline Object<list<T>> operator+(const Object<list<T>>& lhs, const Object<list<T>>& rhs) {
    list<T> out;
    if (lhs) out.extend(*lhs);
    if (rhs) out.extend(*rhs);
    return rc_list_from_value(::std::move(out));
}

// rc_list_from_value identity overload: pass-through when already Object<list<T>>.
template <class T>
static inline Object<list<T>> rc_list_from_value(Object<list<T>> v) {
    return v;
}

// py_zip: zip two lists into a list of 2-tuples (shortest-length truncation).
template <class A, class B>
static inline list<::std::tuple<A, B>> py_zip(const list<A>& a, const list<B>& b) {
    list<::std::tuple<A, B>> result;
    const ::std::size_t n = ::std::min(a.size(), b.size());
    result.reserve(n);
    for (::std::size_t i = 0; i < n; ++i) {
        result.push_back({a[i], b[i]});
    }
    return result;
}

template <class A, class B>
static inline list<::std::tuple<A, B>> py_zip(const Object<list<A>>& a, const Object<list<B>>& b) {
    if (!a || !b) return list<::std::tuple<A, B>>{};
    return py_zip(*a, *b);
}

template <class A, class B>
static inline list<::std::tuple<A, B>> py_zip(const Object<list<A>>& a, const list<B>& b) {
    if (!a) return list<::std::tuple<A, B>>{};
    return py_zip(*a, b);
}

template <class A, class B>
static inline list<::std::tuple<A, B>> py_zip(const list<A>& a, const Object<list<B>>& b) {
    if (!b) return list<::std::tuple<A, B>>{};
    return py_zip(a, *b);
}

// py_sum: sum all elements of a list (returns 0 for empty list).
template <class T>
static inline T py_sum(const list<T>& v) {
    T acc = T{};
    for (const auto& x : v) acc += x;
    return acc;
}

template <class T>
static inline T py_sum(const Object<list<T>>& v) {
    if (!v) return T{};
    return py_sum(*v);
}

template <class T, class S>
static inline T py_sum(const list<T>& v, const S& start) {
    T acc = static_cast<T>(start);
    for (const auto& x : v) acc += x;
    return acc;
}

template <class T, class S>
static inline T py_sum(const Object<list<T>>& v, const S& start) {
    if (!v) return static_cast<T>(start);
    return py_sum(*v, start);
}

// リスト境界正規化・スライス・インデックスアクセス。
// py_runtime.h から移動（P6-CPP-LIST-MUT-IR-BYPASS-FIX-01）。

template <class T>
static inline list<T> py_list_slice_copy(const list<T>& values, int64 lo, int64 up) {
    const int64 n = static_cast<int64>(values.size());
    if (lo < 0) lo += n;
    if (up < 0) up += n;
    lo = ::std::max<int64>(0, ::std::min<int64>(lo, n));
    up = ::std::max<int64>(0, ::std::min<int64>(up, n));
    if (up < lo) up = lo;
    return list<T>(values.begin() + lo, values.begin() + up);
}

template <class T>
static inline list<T> py_list_slice_copy(const Object<list<T>>& values, int64 lo, int64 up) {
    if (!values) {
        return list<T>{};
    }
    return py_list_slice_copy(*values, lo, up);
}

template <class T>
static inline int64 py_list_normalize_index_or_raise(const list<T>& values, int64 idx, const char* label) {
    int64 pos = idx;
    const int64 n = static_cast<int64>(values.size());
    if (pos < 0) pos += n;
    if (pos < 0 || pos >= n) {
        throw ::std::out_of_range(label);
    }
    return pos;
}

template <class T>
static inline typename list<T>::reference py_list_at_ref(list<T>& values, int64 idx) {
    const int64 pos = py_list_normalize_index_or_raise(values, idx, "list index out of range");
    return values[static_cast<::std::size_t>(pos)];
}

template <class T>
static inline typename list<T>::const_reference py_list_at_ref(const list<T>& values, int64 idx) {
    const int64 pos = py_list_normalize_index_or_raise(values, idx, "list index out of range");
    return values[static_cast<::std::size_t>(pos)];
}

template <class T>
static inline typename list<T>::reference py_list_at_ref(Object<list<T>>& values, int64 idx) {
    return py_list_at_ref(*values, idx);
}

template <class T>
static inline typename list<T>::const_reference py_list_at_ref(const Object<list<T>>& values, int64 idx) {
    return py_list_at_ref(*values, idx);
}

template <class T>
struct py_is_cstr_like : ::std::bool_constant<
    ::std::is_pointer_v<::std::decay_t<T>>
    && ::std::is_same_v<
        ::std::remove_cv_t<::std::remove_pointer_t<::std::decay_t<T>>>,
        char>> {};

template <class T>
static inline T py_coerce_cstr_typed_value(const char* value) {
    if constexpr (::std::is_same_v<T, str>) {
        return str(value);
    } else if constexpr (::std::is_same_v<T, bool>) {
        return str(value).size() != 0;
    } else if constexpr (::std::is_integral_v<T> && !::std::is_same_v<T, bool>) {
        return static_cast<T>(py_to_int64(str(value)));
    } else if constexpr (::std::is_floating_point_v<T>) {
        return static_cast<T>(py_to_float64(str(value)));
    } else if constexpr (::std::is_convertible_v<const char*, T>) {
        return static_cast<T>(value);
    } else if constexpr (::std::is_constructible_v<T, const char*>) {
        return T(value);
    } else if constexpr (::std::is_convertible_v<str, T>) {
        return static_cast<T>(str(value));
    } else if constexpr (::std::is_constructible_v<T, str>) {
        return T(str(value));
    } else {
        static_assert(!::std::is_same_v<T, T>, "py_coerce_cstr_typed_value<T>: unsupported target type");
    }
}

// ミューテーション操作（pyobj list model 向けに emitter が emit する）。
template <class T, class U>
static inline void py_list_append_mut(list<T>& values, const U& item) {
    if constexpr (py_is_cstr_like<U>::value) {
        values.append(py_coerce_cstr_typed_value<T>(item));
    } else if constexpr (::std::is_same_v<T, U>) {
        values.append(item);
    } else if constexpr (::std::is_convertible_v<U, T>) {
        values.append(static_cast<T>(item));
    } else {
        values.append(T(item));
    }
}

template <class T, class U>
static inline void py_list_append_mut(Object<list<T>>& values, const U& item) {
    py_list_append_mut(*values, item);
}

template <class T, class I, class U>
static inline void py_list_set_at_mut(list<T>& values, I idx, const U& item) {
    int64 pos = py_to<int64>(idx);
    pos = py_list_normalize_index_or_raise(values, pos, "list index out of range");
    if constexpr (py_is_cstr_like<U>::value) {
        values[static_cast<::std::size_t>(pos)] = py_coerce_cstr_typed_value<T>(item);
    } else if constexpr (::std::is_same_v<T, U>) {
        values[static_cast<::std::size_t>(pos)] = item;
    } else if constexpr (::std::is_convertible_v<U, T>) {
        values[static_cast<::std::size_t>(pos)] = static_cast<T>(item);
    } else {
        values[static_cast<::std::size_t>(pos)] = T(item);
    }
}

template <class T, class I, class U>
static inline void py_list_set_at_mut(Object<list<T>>& values, I idx, const U& item) {
    py_list_set_at_mut(*values, idx, item);
}

template <class T, class U>
static inline void py_list_extend_mut(list<T>& values, const U& items) {
    values.extend(items);
}

template <class T, class U>
static inline void py_list_extend_mut(Object<list<T>>& values, const U& items) {
    py_list_extend_mut(*values, items);
}

template <class T>
static inline T py_list_pop_mut(list<T>& values) {
    return values.pop();
}

template <class T>
static inline T py_list_pop_mut(Object<list<T>>& values) {
    return py_list_pop_mut(*values);
}

template <class T>
static inline T py_list_pop_mut(list<T>& values, int64 idx) {
    return values.pop(idx);
}

template <class T>
static inline T py_list_pop_mut(Object<list<T>>& values, int64 idx) {
    return py_list_pop_mut(*values, idx);
}

template <class T>
static inline void py_list_clear_mut(list<T>& values) {
    values.clear();
}

template <class T>
static inline void py_list_clear_mut(Object<list<T>>& values) {
    py_list_clear_mut(*values);
}

template <class T>
static inline void py_list_reverse_mut(list<T>& values) {
    ::std::reverse(values.begin(), values.end());
}

template <class T>
static inline void py_list_reverse_mut(Object<list<T>>& values) {
    py_list_reverse_mut(*values);
}

template <class T>
static inline void py_list_sort_mut(list<T>& values) {
    ::std::sort(values.begin(), values.end());
}

template <class T>
static inline void py_list_sort_mut(Object<list<T>>& values) {
    py_list_sort_mut(*values);
}

// py_list_at_ref for object (= Object<void>): downcast to list<object> and index.
static inline object py_list_at_ref(const object& values, int64 idx) {
    auto typed = values.as<list<object>>();
    if (!typed) throw ::std::runtime_error("py_list_at_ref: object is not a list");
    return py_list_at_ref(*typed, idx);
}

#endif  // PYTRA_NATIVE_BUILT_IN_LIST_OPS_H
