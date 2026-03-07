// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/timeit.py
// generated-by: src/backends/cpp/cli.py
#include "runtime/cpp/core/py_runtime.h"

#include "runtime/cpp/generated/std/timeit.h"

#include "pytra/std/time.h"

namespace pytra::std::timeit {

    /* pytra.std.timeit compatibility shim. */
    
    float64 default_timer() {
        /* `timeit.default_timer` compatible entrypoint. */
        return pytra::std::time::perf_counter();
    }
    
}  // namespace pytra::std::timeit
