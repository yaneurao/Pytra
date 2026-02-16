#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{perf_counter, py_in, py_len, py_print, py_slice};

// このファイルは自動生成です（native Rust mode）。

fn calc_17(values: Vec<i64>) -> i64 {
    let mut total: i64 = 0;
    for v in (values).clone() {
        if ((((v) % (2))) == (0)) {
            total = total + v;
        } else {
            total = total + ((v) * (2));
        }
    }
    return total;
}

fn main() {
    py_print(calc_17(vec![1, 2, 3, 4]));
}
