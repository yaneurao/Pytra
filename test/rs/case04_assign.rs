#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{perf_counter, py_print};

// このファイルは自動生成です（native Rust mode）。

fn square_plus_one(n: i64) -> i64 {
    let mut result: i64 = ((n) * (n));
    result = result + 1;
    return result;
}

fn main() {
    py_print(square_plus_one(5));
}
