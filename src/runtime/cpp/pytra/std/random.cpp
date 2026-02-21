#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/std/random.h"


namespace pytra::std::random {

    /* pytra.std.random: minimal deterministic random helpers.

This module is intentionally self-contained and avoids Python stdlib imports,
so it can be transpiled to target runtimes.
 */
    
    
    list<int64> _state_box = list<int64>{2463534242};
    
    void seed(int64 value) {
        /* Set generator seed (32-bit). */
        int64 v = int64(value) & 2147483647;
        if (v == 0)
            v = 1;
        _state_box[0] = v;
    }
    
    int64 _next_u31() {
        /* Advance internal LCG and return a 31-bit value. */
        auto s = py_at(_state_box, py_to_int64(0));
        s = 1103515245 * s + 12345 & 2147483647;
        _state_box[0] = s;
        return s;
    }
    
    float64 random() {
        /* Return pseudo-random float in [0.0, 1.0). */
        return py_to_float64(_next_u31()) / 2147483648.0;
    }
    
    int64 randint(int64 a, int64 b) {
        /* Return pseudo-random integer in [a, b]. */
        int64 lo = int64(a);
        int64 hi = int64(b);
        if (hi < lo)
            ::std::swap(lo, hi);
        int64 span = hi - lo + 1;
        return lo + int64(random() * py_to_float64(span));
    }
    
    list<str> __all__ = list<str>{"seed", "random", "randint"};
    
}  // namespace pytra::std::random
