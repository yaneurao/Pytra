// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/numeric_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::pytra::std::abi;
use crate::pytra::std::template;

fn sum(values: &[T]) -> T {
    if values.len() as i64 == 0 {
        return 0;
    }
    let mut acc = (values[((0) as usize)]).clone() - (values[((0) as usize)]).clone();
    let mut i = 0;
    let n = values.len() as i64;
    while i < n {
        acc += (values[((i) as usize)]).clone();
        i += 1;
    }
    return acc;
}

fn py_min(a: T, b: T) -> T {
    if a < b {
        return a;
    }
    return b;
}

fn py_max(a: T, b: T) -> T {
    if a > b {
        return a;
    }
    return b;
}

fn main() {
    ("Pure-Python source-of-truth for numeric helper built-ins.").to_string();
}
