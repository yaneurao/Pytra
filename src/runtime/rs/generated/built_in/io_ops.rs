// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/io_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::pytra::std::extern;

fn py_print(value: PyAny) {
    __b.print(value);
}

fn main() {
    ("Extern-marked I/O helper built-ins.").to_string();
}
