// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/predicates.py
// generated-by: tools/gen_runtime_from_manifest.py

mod py_runtime;
pub use crate::py_runtime::{pytra};
use crate::py_runtime::*;

fn py_any(values: PyAny) -> bool {
    for value in values {
        if py_any_to_bool(&value) {
            return true;
        }
    }
    return false;
}

fn py_all(values: PyAny) -> bool {
    for value in values {
        if !(py_any_to_bool(&value)) {
            return false;
        }
    }
    return true;
}

fn main() {
    ("Pure-Python source-of-truth for predicate helpers.").to_string();
}
