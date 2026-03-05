// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/time.py
// generated-by: src/backends/cpp/cli.py
#include "runtime/cpp/core/built_in/py_runtime.h"

#include "runtime/cpp/gen/std/time.h"

#include "runtime/cpp/core/std/time-impl.h"

namespace pytra::std::time {

    list<str> __all__;
    
    float64 perf_counter() {
        return pytra::std::time_impl::perf_counter();
    }
    
    static void __pytra_module_init() {
        static bool __initialized = false;
        if (__initialized) return;
        __initialized = true;
        /* pytra.std.time wrapper. */
        __all__ = list<str>{"perf_counter"};
    }
    
}  // namespace pytra::std::time
