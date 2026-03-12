// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/iter_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

fn py_reversed_object(values: PyAny) -> PyAny {
    let mut out: Vec<PyAny> = vec![];
    let mut i = (match &values { PyAny::Str(s) => s.len() as i64, PyAny::Dict(d) => d.len() as i64, PyAny::List(xs) => xs.len() as i64, PyAny::Set(xs) => xs.len() as i64, PyAny::None => 0, _ => 0 }) - 1;
    while i >= 0 {
        out.push(values[((if ((i) as i64) < 0 { (values.len() as i64 + ((i) as i64)) } else { ((i) as i64) }) as usize)]);
        i -= 1;
    }
    return out;
}

fn py_enumerate_object(values: PyAny, start: i64) -> PyAny {
    let mut out: Vec<PyAny> = vec![];
    let mut i = 0;
    let n = (match &values { PyAny::Str(s) => s.len() as i64, PyAny::Dict(d) => d.len() as i64, PyAny::List(xs) => xs.len() as i64, PyAny::Set(xs) => xs.len() as i64, PyAny::None => 0, _ => 0 });
    while i < n {
        out.push(vec![start + i, values[((i) as usize)]]);
        i += 1;
    }
    return out;
}

fn main() {
    ("Pure-Python source-of-truth for object-based iterator helpers.").to_string();
}
