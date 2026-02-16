#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{perf_counter, py_in, py_len, py_print, py_slice};

// このファイルは自動生成です（native Rust mode）。

fn make_msg_22(name: String, count: i64) -> String {
    return format!("{}:22:{}", name, count);
}

fn main() {
    py_print(make_msg_22("user".to_string(), 7));
}
