#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/std/time.h"

#include "pytra/std/time-impl.h"

namespace pytra::std::time {

    /* pytra.std.time wrapper. */
    
    
    
    float64 perf_counter() {
        return py_to_float64(pytra::std::time_impl::perf_counter());
    }
    
    list<str> __all__ = list<str>{"perf_counter"};
    
}  // namespace pytra::std::time
