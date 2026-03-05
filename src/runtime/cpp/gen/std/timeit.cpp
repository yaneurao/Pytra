// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/timeit.py
// generated-by: src/py2cpp.py

#include "runtime/cpp/core/built_in/py_runtime.h"

#include "runtime/cpp/gen/std/timeit.h"

#include "runtime/cpp/gen/std/time.h"

namespace pytra::std::timeit {

    /* pytra.std.timeit compatibility shim. */
    
    
    
    float64 default_timer() {
        /* `timeit.default_timer` compatible entrypoint. */
        return pytra::std::time::perf_counter();
    }
    
    list<str> __all__ = list<str>{"default_timer"};
    
}  // namespace pytra::std::timeit
