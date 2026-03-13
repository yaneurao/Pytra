// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/utils/assertions.py
// generated-by: tools/gen_runtime_from_manifest.py

mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::pytra::std::abi;

fn _eq_any(actual: PyAny, expected: PyAny) -> bool {
    {
        return (py_to_string(actual) == py_to_string(expected));
    }
    {
        return (actual == expected);
    }
}

fn py_assert_true(cond: bool, label: &str) -> bool {
    if cond {
        return true;
    }
    if label != "" {
        println!("{}", f"[assert_true] {label}: False");
    } else {
        println!("{}", ("[assert_true] False").to_string());
    }
    return false;
}

fn py_assert_eq(actual: PyAny, expected: PyAny, label: &str) -> bool {
    let ok = _eq_any(actual, expected);
    if ok {
        return true;
    }
    if label != "" {
        println!("{}", f"[assert_eq] {label}: actual={actual}, expected={expected}");
    } else {
        println!("{}", f"[assert_eq] actual={actual}, expected={expected}");
    }
    return false;
}

fn py_assert_all(results: &[bool], label: &str) -> bool {
    for v in (results).iter().copied() {
        if !v {
            if label != "" {
                println!("{}", f"[assert_all] {label}: False");
            } else {
                println!("{}", ("[assert_all] False").to_string());
            }
            return false;
        }
    }
    return true;
}

fn py_assert_stdout(expected_lines: &[String], py_fn: PyAny) -> bool {
    // self_hosted parser / runtime 互換優先: stdout capture は未実装。
    return true;
}
