#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{perf_counter, py_in, py_len, py_print, py_slice};

// このファイルは自動生成です（native Rust mode）。

fn invert(flag: bool) -> bool {
    if (!flag) {
        return true;
    } else {
        return false;
    }
}

fn main() {
    py_print(invert(false));
}
