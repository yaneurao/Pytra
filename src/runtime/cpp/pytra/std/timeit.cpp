#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/std/timeit.h"

#include "pytra/std/time.h"

namespace pytra::std::timeit {

    /* pytra.std.timeit compatibility shim. */
    
    
    
    float64 default_timer() {
        /* `timeit.default_timer` compatible entrypoint. */
        return pytra::std::time::perf_counter();
    }
    
    list<str> __all__ = list<str>{"default_timer"};
    
}  // namespace pytra::std::timeit
