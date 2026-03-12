// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/os_path.py
// generated-by: tools/gen_runtime_from_manifest.py

mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::pytra::std::extern;

fn join(a: &str, b: &str) -> String {
    return __path.join(a, b);
}

fn dirname(p: &str) -> String {
    return __path.dirname(p);
}

fn basename(p: &str) -> String {
    return __path.basename(p);
}

fn splitext(p: &str) -> (String, String) {
    return __path.splitext(p);
}

fn abspath(p: &str) -> String {
    return __path.abspath(p);
}

fn exists(p: &str) -> bool {
    return __path.exists(p);
}

fn main() {
    ("pytra.std.os_path: extern-marked os.path subset with Python runtime fallback.").to_string();
}
