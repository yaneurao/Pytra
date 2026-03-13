// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/predicates.py
// generated-by: src/backends/cpp/cli.py
#include "runtime/cpp/native/core/py_runtime.h"

#include "runtime/cpp/generated/built_in/predicates.h"
#include "runtime/cpp/native/core/process_runtime.h"
#include "runtime/cpp/native/core/scope_exit.h"


/* Pure-Python source-of-truth for predicate helpers. */

bool py_any(const object& values) {
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

bool py_all(const object& values) {
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
