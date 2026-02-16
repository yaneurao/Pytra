#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{perf_counter, py_in, py_len, py_print, py_slice};

// このファイルは自動生成です（native Rust mode）。

fn sum_range_29(n: i64) -> i64 {
    let mut total: i64 = 0;
    for i in (0)..(n) {
        total = total + i;
    }
    return total;
}

fn main() {
    py_print(sum_range_29(5));
}
