#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{perf_counter, py_in, py_len, py_print, py_slice};

// このファイルは自動生成です（native Rust mode）。

fn decorate(name: String) -> String {
    let mut prefix: String = "[USER] ".to_string();
    let mut message: String = format!("{}{}", prefix, name);
    return format!("{}{}", message, "!".to_string());
}

fn main() {
    py_print(decorate("Alice".to_string()));
}
