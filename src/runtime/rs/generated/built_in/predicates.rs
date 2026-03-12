// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/predicates.py
// generated-by: tools/gen_runtime_from_manifest.py

mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

fn py_any(values: PyAny) -> bool {
    let mut i = 0;
    let n = (match &values { PyAny::Str(s) => s.len() as i64, PyAny::Dict(d) => d.len() as i64, PyAny::List(xs) => xs.len() as i64, PyAny::Set(xs) => xs.len() as i64, PyAny::None => 0, _ => 0 });
    while i < n {
        if py_any_to_bool(&values[((i) as usize)]) {
            return true;
        }
        i += 1;
    }
    return false;
}

fn py_all(values: PyAny) -> bool {
    let mut i = 0;
    let n = (match &values { PyAny::Str(s) => s.len() as i64, PyAny::Dict(d) => d.len() as i64, PyAny::List(xs) => xs.len() as i64, PyAny::Set(xs) => xs.len() as i64, PyAny::None => 0, _ => 0 });
    while i < n {
        if !(py_any_to_bool(&values[((i) as usize)])) {
            return false;
        }
        i += 1;
    }
    return true;
}

fn main() {
    ("Pure-Python source-of-truth for predicate helpers.").to_string();
}
