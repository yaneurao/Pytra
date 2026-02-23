#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/std/math.h"

#include "pytra/std/math-impl.h"

namespace pytra::std::math {

    float64 pi;
    float64 e;
    
    
    
    float64 sqrt(float64 x) {
        return pytra::std::math_impl::sqrt(x);
    }
    
    float64 sin(float64 x) {
        return pytra::std::math_impl::sin(x);
    }
    
    float64 cos(float64 x) {
        return pytra::std::math_impl::cos(x);
    }
    
    float64 tan(float64 x) {
        return pytra::std::math_impl::tan(x);
    }
    
    float64 exp(float64 x) {
        return pytra::std::math_impl::exp(x);
    }
    
    float64 log(float64 x) {
        return pytra::std::math_impl::log(x);
    }
    
    float64 log10(float64 x) {
        return pytra::std::math_impl::log10(x);
    }
    
    float64 fabs(float64 x) {
        return pytra::std::math_impl::fabs(x);
    }
    
    float64 floor(float64 x) {
        return pytra::std::math_impl::floor(x);
    }
    
    float64 ceil(float64 x) {
        return pytra::std::math_impl::ceil(x);
    }
    
    float64 pow(float64 x, float64 y) {
        return pytra::std::math_impl::pow(x, y);
    }
    
    static void __pytra_module_init() {
        static bool __initialized = false;
        if (__initialized) return;
        __initialized = true;
        /* pytra.std.math: thin wrapper over native math_impl module. */
        pi = pytra::std::math_impl::pi;
        e = pytra::std::math_impl::e;
    }
    
}  // namespace pytra::std::math
