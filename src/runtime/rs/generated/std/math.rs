// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/math.py
// generated-by: tools/gen_runtime_from_manifest.py

mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::pytra::std::extern;

fn sqrt(x: f64) -> f64 {
    return __m.sqrt(x);
}

fn sin(x: f64) -> f64 {
    return __m.sin(x);
}

fn cos(x: f64) -> f64 {
    return __m.cos(x);
}

fn tan(x: f64) -> f64 {
    return __m.tan(x);
}

fn exp(x: f64) -> f64 {
    return __m.exp(x);
}

fn log(x: f64) -> f64 {
    return __m.log(x);
}

fn log10(x: f64) -> f64 {
    return __m.log10(x);
}

fn fabs(x: f64) -> f64 {
    return __m.fabs(x);
}

fn floor(x: f64) -> f64 {
    return __m.floor(x);
}

fn ceil(x: f64) -> f64 {
    return __m.ceil(x);
}

fn pow(x: f64, y: f64) -> f64 {
    return __m.pow(x, y);
}

fn main() {
    ("pytra.std.math: extern-marked math API with Python runtime fallback.").to_string();
    let pi: f64 = py_any_to_f64(&(py_extern(__m.pi)));
    let e: f64 = py_any_to_f64(&(py_extern(__m.e)));
}
