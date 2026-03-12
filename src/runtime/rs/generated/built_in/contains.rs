// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/contains.py
// generated-by: tools/gen_runtime_from_manifest.py

mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

fn py_contains_dict_object(values: PyAny, key: PyAny) -> bool {
    let needle = py_any_to_string(&key);
    for cur in values {
        if cur == needle {
            return true;
        }
    }
    return false;
}

fn py_contains_list_object(values: PyAny, key: PyAny) -> bool {
    for cur in values {
        if cur == key {
            return true;
        }
    }
    return false;
}

fn py_contains_set_object(values: PyAny, key: PyAny) -> bool {
    for cur in values {
        if cur == key {
            return true;
        }
    }
    return false;
}

fn py_contains_str_object(values: PyAny, key: PyAny) -> bool {
    let needle = py_any_to_string(&key);
    let haystack = py_any_to_string(&values);
    let n = haystack.len() as i64;
    let m = needle.len() as i64;
    if m == 0 {
        return true;
    }
    let mut i = 0;
    let last = n - m;
    while i <= last {
        let mut j = 0;
        let mut ok = true;
        while j < m {
            if py_str_at_nonneg(&haystack, ((i + j) as usize)) != py_str_at_nonneg(&needle, ((j) as usize)) {
                ok = false;
                break;
            }
            j += 1;
        }
        if ok {
            return true;
        }
        i += 1;
    }
    return false;
}

fn main() {
    ("Pure-Python source-of-truth for containment helpers.").to_string();
}
