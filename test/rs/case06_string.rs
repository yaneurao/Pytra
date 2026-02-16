#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{perf_counter, py_in, py_len, py_print, py_slice};

// このファイルは自動生成です（native Rust mode）。

fn greet(name: String) -> String {
    return format!("{}{}", "Hello, ".to_string(), name);
}

fn main() {
    py_print(greet("Codex".to_string()));
}
