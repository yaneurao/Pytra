#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{perf_counter, py_print};

// このファイルは自動生成です（native Rust mode）。

fn abs_like(n: i64) -> i64 {
    if ((n) < (0)) {
        return (-n);
    } else {
        return n;
    }
}

fn main() {
    py_print(abs_like((-12)));
}
