// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/predicates.py
// generated-by: tools/gen_runtime_from_manifest.py

#ifndef PYTRA_GEN_BUILT_IN_PREDICATES_H
#define PYTRA_GEN_BUILT_IN_PREDICATES_H

// forward declarations
bool py_any(const T& values);
bool py_all(const T& values);

/* Pure-Python source-of-truth for predicate helpers. */

template <class T>
bool py_any(const T& values) {
    {
        object __iter_obj_1 = ([&]() -> object { object __obj = values; if (!__obj) throw TypeError("NoneType is not iterable"); return __obj->py_iter_or_raise(); }());
        while (true) {
            ::std::optional<object> __next_2 = ([&]() -> ::std::optional<object> { object __iter = __iter_obj_1; if (!__iter) throw TypeError("NoneType is not an iterator"); return __iter->py_next_or_stop(); }());
            if (!__next_2.has_value()) break;
            object value = *__next_2;
            if (py_to<bool>(value))
                return true;
        }
    }
    return false;
}

template <class T>
bool py_all(const T& values) {
    {
        object __iter_obj_3 = ([&]() -> object { object __obj = values; if (!__obj) throw TypeError("NoneType is not iterable"); return __obj->py_iter_or_raise(); }());
        while (true) {
            ::std::optional<object> __next_4 = ([&]() -> ::std::optional<object> { object __iter = __iter_obj_3; if (!__iter) throw TypeError("NoneType is not an iterator"); return __iter->py_next_or_stop(); }());
            if (!__next_4.has_value()) break;
            object value = *__next_4;
            if (!(py_to<bool>(value)))
                return false;
        }
    }
    return true;
}

#endif  // PYTRA_GEN_BUILT_IN_PREDICATES_H
