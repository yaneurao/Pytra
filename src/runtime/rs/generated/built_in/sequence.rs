// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/sequence.py
// generated-by: tools/gen_runtime_from_manifest.py

mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::pytra::std::abi;

fn py_range(start: i64, stop: i64, step: i64) -> Vec<i64> {
    let mut out: Vec<i64> = vec![];
    if step == 0 {
        return out;
    }
    if step > 0 {
        let mut i = start;
        while i < stop {
            out.push(i);
            i += step;
        }
    } else {
        let mut i = start;
        while i > stop {
            out.push(i);
            i += step;
        }
    }
    return out;
}

fn py_repeat(v: &str, n: i64) -> String {
    if n <= 0 {
        return ("").to_string();
    }
    let mut out = ("").to_string();
    let mut i = 0;
    while i < n {
        out += v;
        i += 1;
    }
    return out;
}

fn main() {
    ("Pure-Python source-of-truth for sequence helpers used by runtime built-ins.").to_string();
}
