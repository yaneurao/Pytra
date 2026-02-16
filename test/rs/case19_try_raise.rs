#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{perf_counter, py_in, py_len, py_print, py_slice};

// このファイルは自動生成です（native Rust mode）。

fn maybe_fail_19(flag: bool) -> i64 {
    if flag {
        return 20;
    } else {
        return 10;
    }
}

fn main() {
    py_print(maybe_fail_19(true));
}
