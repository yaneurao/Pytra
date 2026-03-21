#include "core/py_runtime.h"
#include "core/process_runtime.h"
#include "built_in/iter_ops.h"

/* Pure-Python source-of-truth for object-based iterator helpers. */

list<object> py_reversed_object(const object& values) {
    list<object> out = list<object>{};
    {
        object __iter_obj_1 = ([&]() -> object { object __obj = values; if (!__obj) throw TypeError("NoneType is not iterable"); return __obj->py_iter_or_raise(); }());
        while (true) {
            ::std::optional<object> __next_2 = ([&]() -> ::std::optional<object> { object __iter = __iter_obj_1; if (!__iter) throw TypeError("NoneType is not an iterator"); return __iter->py_next_or_stop(); }());
            if (!__next_2.has_value()) break;
            object value = *__next_2;
            out.append(value);
        }
    }
    return py_reversed(out);
}

list<object> py_enumerate_object(const object& values, int64 start = 0) {
    list<object> out = list<object>{};
    int64 i = start;
    {
        object __iter_obj_3 = ([&]() -> object { object __obj = values; if (!__obj) throw TypeError("NoneType is not iterable"); return __obj->py_iter_or_raise(); }());
        while (true) {
            ::std::optional<object> __next_4 = ([&]() -> ::std::optional<object> { object __iter = __iter_obj_3; if (!__iter) throw TypeError("NoneType is not an iterator"); return __iter->py_next_or_stop(); }());
            if (!__next_4.has_value()) break;
            object value = *__next_4;
            out.append(object(::std::make_tuple(i, value)));
            i++;
        }
    }
    return out;
}
