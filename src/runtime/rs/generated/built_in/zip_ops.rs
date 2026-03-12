// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/zip_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::pytra::std::abi;
use crate::pytra::std::template;

fn zip(lhs: &[A], rhs: &[B]) -> Vec<(A, B)> {
    let mut out: Vec<(A, B)> = vec![];
    let mut i = 0;
    let mut n = lhs.len() as i64;
    if rhs.len() as i64 < n {
        n = rhs.len() as i64;
    }
    while i < n {
        out.push(((lhs[((i) as usize)]).clone(), (rhs[((i) as usize)]).clone()));
        i += 1;
    }
    return out;
}

fn main() {
    ("Pure-Python source-of-truth for generic zip helpers.").to_string();
}
