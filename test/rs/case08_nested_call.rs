#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{perf_counter, py_print};

// このファイルは自動生成です（native Rust mode）。

fn inc(x: i64) -> i64 {
    return ((x) + (1));
}

fn twice(x: i64) -> i64 {
    return inc(inc(x));
}

fn main() {
    py_print(twice(10));
}
