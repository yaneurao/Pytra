// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/glob.py
// generated-by: tools/gen_runtime_from_manifest.py

mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::pytra::std::extern;

fn glob(pattern: &str) -> Vec<String> {
    return __glob.glob(pattern);
}

fn main() {
    ("pytra.std.glob: extern-marked glob subset with Python runtime fallback.").to_string();
}
