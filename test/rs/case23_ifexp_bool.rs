#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{perf_counter, py_print};

// このファイルは自動生成です（native Rust mode）。

fn pick_25(a: i64, b: i64, flag: bool) -> i64 {
    let mut c: i64 = (if (flag && ((a) > (b))) { a } else { b });
    return c;
}

fn main() {
    py_print(pick_25(10, 3, true));
}
