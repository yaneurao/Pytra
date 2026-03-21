#include "core/py_runtime.h"
#include "core/process_runtime.h"

float64 pi;
float64 e;

/* pytra.std.math: extern-marked math API with Python runtime fallback. */

float64 sqrt(float64 x) {
    return math.sqrt(x);
}

float64 sin(float64 x) {
    return math.sin(x);
}

float64 cos(float64 x) {
    return math.cos(x);
}

float64 tan(float64 x) {
    return math.tan(x);
}

float64 exp(float64 x) {
    return math.exp(x);
}

float64 log(float64 x) {
    return math.log(x);
}

float64 log10(float64 x) {
    return math.log10(x);
}

float64 fabs(float64 x) {
    return math.fabs(x);
}

float64 floor(float64 x) {
    return math.floor(x);
}

float64 ceil(float64 x) {
    return math.ceil(x);
}

float64 pow(float64 x, float64 y) {
    return math.pow(x, y);
}

static void __pytra_module_init() {
    static bool __initialized = false;
    if (__initialized) return;
    __initialized = true;
    pi = float64(pytra::std::extern(math.pi));
    e = float64(pytra::std::extern(math.e));
}
