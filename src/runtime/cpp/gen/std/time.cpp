// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/time.py
// generated-by: src/py2cpp.py

#include "runtime/cpp/core/built_in/py_runtime.h"

#include "runtime/cpp/gen/std/time.h"

#include "runtime/cpp/core/std/time-impl.h"

namespace pytra::std::time {

    /* pytra.std.time wrapper. */
    
    
    
    float64 perf_counter() {
        return py_to_float64(pytra::std::time_impl::perf_counter());
    }
    
    list<str> __all__ = list<str>{"perf_counter"};
    
}  // namespace pytra::std::time
