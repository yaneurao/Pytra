// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/os.py
// generated-by: tools/gen_runtime_from_manifest.py

mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::pytra::std::extern;
use crate::pytra::std::os_path as path;

fn getcwd() -> String {
    return __os.getcwd();
}

fn mkdir(p: &str) {
    __os.mkdir(p);
}

fn makedirs(p: &str, exist_ok: bool) {
    __os.makedirs(p, exist_ok);
}

fn main() {
    ("pytra.std.os: extern-marked os subset with Python runtime fallback.").to_string();
}
