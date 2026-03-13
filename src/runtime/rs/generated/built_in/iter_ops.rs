// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/iter_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

mod py_runtime;
pub use crate::py_runtime::{pytra};
use crate::py_runtime::*;

fn py_reversed_object(values: PyAny) -> Vec<PyAny> {
    let mut out: Vec<PyAny> = vec![];
    for value in values {
        out.push(value);
    }
    return reversed((out).clone());
}

fn py_enumerate_object(values: PyAny, start: i64) -> Vec<PyAny> {
    let mut out: Vec<PyAny> = vec![];
    let mut i = start;
    for value in values {
        out.push(vec![i, value]);
        i += 1;
    }
    return out;
}

fn main() {
    ("Pure-Python source-of-truth for object-based iterator helpers.").to_string();
}
