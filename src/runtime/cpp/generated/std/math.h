// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/math.py
// generated-by: tools/gen_runtime_from_manifest.py

#ifndef PYTRA_GEN_STD_MATH_H
#define PYTRA_GEN_STD_MATH_H

// forward declarations
float64 sqrt(float64 x);
float64 sin(float64 x);
float64 cos(float64 x);
float64 tan(float64 x);
float64 exp(float64 x);
float64 log(float64 x);
float64 log10(float64 x);
float64 fabs(float64 x);
float64 floor(float64 x);
float64 ceil(float64 x);
float64 pow(float64 x, float64 y);

float64 pi;
float64 e;

/* pytra.std.math: extern-marked math API with Python runtime fallback. */

float64 sqrt(float64 x) {
    return __m.sqrt(x);
}

float64 sin(float64 x) {
    return __m.sin(x);
}

float64 cos(float64 x) {
    return __m.cos(x);
}

float64 tan(float64 x) {
    return __m.tan(x);
}

float64 exp(float64 x) {
    return __m.exp(x);
}

float64 log(float64 x) {
    return __m.log(x);
}

float64 log10(float64 x) {
    return __m.log10(x);
}

float64 fabs(float64 x) {
    return __m.fabs(x);
}

float64 floor(float64 x) {
    return __m.floor(x);
}

float64 ceil(float64 x) {
    return __m.ceil(x);
}

float64 pow(float64 x, float64 y) {
    return __m.pow(x, y);
}

#endif  // PYTRA_GEN_STD_MATH_H
