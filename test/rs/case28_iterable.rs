#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{perf_counter, py_in, py_len, py_print, py_slice};

// このファイルは自動生成です（native Rust mode）。

fn main() -> () {
    let mut l: Vec<i64> = vec![1, 2, 3];
    let mut sum = 0;
    for v in (l).clone() {
        sum = sum + v;
    }
    py_print(sum);
}
