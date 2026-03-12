// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/scalar_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::pytra::std::extern;

fn py_to_int64_base(v: &str, base: i64) -> i64 {
    return __b.int(v, base);
}

fn py_ord(ch: &str) -> i64 {
    return __b.ord(ch);
}

fn py_chr(codepoint: i64) -> String {
    return __b.chr(codepoint);
}

fn main() {
    ("Extern-marked scalar helper built-ins.").to_string();
}
