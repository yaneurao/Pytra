#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{perf_counter, py_in, py_len, py_print, py_slice};

// このファイルは自動生成です（native Rust mode）。

fn half(x: f64) -> f64 {
    return ((x) / (2.0));
}

fn main() {
    py_print(half(5.0));
}
