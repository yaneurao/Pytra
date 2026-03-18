// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/math.py
// generated-by: tools/gen_runtime_from_manifest.py

pub use super::math_native::{e, pi, ToF64};

pub fn sin<T: ToF64>(v: T) -> f64 {
    super::math_native::sin(v)
}

pub fn cos<T: ToF64>(v: T) -> f64 {
    super::math_native::cos(v)
}

pub fn tan<T: ToF64>(v: T) -> f64 {
    super::math_native::tan(v)
}

pub fn sqrt<T: ToF64>(v: T) -> f64 {
    super::math_native::sqrt(v)
}

pub fn exp<T: ToF64>(v: T) -> f64 {
    super::math_native::exp(v)
}

pub fn log<T: ToF64>(v: T) -> f64 {
    super::math_native::log(v)
}

pub fn log10<T: ToF64>(v: T) -> f64 {
    super::math_native::log10(v)
}

pub fn fabs<T: ToF64>(v: T) -> f64 {
    super::math_native::fabs(v)
}

pub fn floor<T: ToF64>(v: T) -> f64 {
    super::math_native::floor(v)
}

pub fn ceil<T: ToF64>(v: T) -> f64 {
    super::math_native::ceil(v)
}

pub fn pow(a: f64, b: f64) -> f64 {
    super::math_native::pow(a, b)
}
