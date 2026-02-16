#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{perf_counter, py_in, py_len, py_print, py_slice};

// このファイルは自動生成です（native Rust mode）。

fn mul3(n: i64) -> i64 {
    return ((n) * (3));
}

fn main() {
    let mut value: i64 = 7;
    py_print(mul3(value));
}
