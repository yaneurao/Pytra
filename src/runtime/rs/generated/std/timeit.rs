// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/timeit.py
// generated-by: tools/gen_runtime_from_manifest.py

mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::pytra::std::time::perf_counter;

fn default_timer() -> f64 {
    return perf_counter();
}

fn main() {
    ("pytra.std.timeit compatibility shim.").to_string();
}
