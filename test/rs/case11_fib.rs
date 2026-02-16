#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{perf_counter, py_print};

// このファイルは自動生成です（native Rust mode）。

fn fib(n: i64) -> i64 {
    if ((n) <= (1)) {
        return n;
    }
    return ((fib(((n) - (1)))) + (fib(((n) - (2)))));
}

fn main() {
    py_print(fib(10));
}
