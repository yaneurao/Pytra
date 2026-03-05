// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/timeit.py
// generated-by: src/backends/cpp/cli.py
#include "runtime/cpp/core/built_in/py_runtime.h"

#include "runtime/cpp/gen/std/timeit.h"

#include "runtime/cpp/gen/std/time.h"

namespace pytra::std::timeit {

    list<str> __all__;
    
    float64 default_timer() {
        /* `timeit.default_timer` compatible entrypoint. */
        return pytra::std::time::perf_counter();
    }
    
    static void __pytra_module_init() {
        static bool __initialized = false;
        if (__initialized) return;
        __initialized = true;
        /* pytra.std.timeit compatibility shim. */
        __all__ = list<str>{"default_timer"};
    }
    
    namespace {
        struct __pytra_module_initializer {
            __pytra_module_initializer() { __pytra_module_init(); }
        };
        static const __pytra_module_initializer __pytra_module_initializer_instance{};
    }  // namespace
    
}  // namespace pytra::std::timeit
