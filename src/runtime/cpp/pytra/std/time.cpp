#include "runtime/cpp/py_runtime.h"

#include "pytra/std/time.h"

namespace pytra::std::time {

    
    
    float64 perf_counter() {
        return py_to_float64(pytra::std::time::perf_counter());
    }
    
}  // namespace pytra::std::time
