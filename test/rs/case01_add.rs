#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{perf_counter, py_print};

// このファイルは自動生成です（native Rust mode）。

fn add(a: i64, b: i64) -> i64 {
    return ((a) + (b));
}

fn main() {
    py_print(add(3, 4));
}
