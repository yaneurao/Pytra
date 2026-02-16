#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{perf_counter, py_print};

// このファイルは自動生成です（native Rust mode）。

fn calc(x: i64, y: i64) -> i64 {
    return ((((x) - (y))) * (2));
}

fn main() {
    py_print(calc(9, 4));
}
