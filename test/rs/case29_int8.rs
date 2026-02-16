#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{perf_counter, py_in, py_len, py_print, py_slice};

// このファイルは自動生成です（native Rust mode）。

fn main() -> () {
    let mut i: i8 = 1;
    py_print(((i) * (2)));
}
