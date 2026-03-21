#include "core/py_runtime.h"
#include "core/process_runtime.h"
#include "std/time.h"

/* pytra.std.timeit compatibility shim. */

float64 default_timer() {
    /* `timeit.default_timer` compatible entrypoint. */
    return pytra::std::time::perf_counter();
}
