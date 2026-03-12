// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/time.py
// generated-by: tools/gen_runtime_from_manifest.py

mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::pytra::std::extern;

fn perf_counter() -> f64 {
    return __t.perf_counter();
}

fn main() {
    ("pytra.std.time: extern-marked time API with Python runtime fallback.").to_string();
}
