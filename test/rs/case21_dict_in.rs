#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{perf_counter, py_in, py_len, py_print, py_slice};

// このファイルは自動生成です（native Rust mode）。

fn has_key_23(k: String) -> bool {
    let mut d: std::collections::HashMap<String, i64> = std::collections::HashMap::from([("a".to_string(), 1), ("b".to_string(), 2)]);
    if py_in(&(d), &(k)) {
        return true;
    } else {
        return false;
    }
}

fn main() {
    py_print(has_key_23("a".to_string()));
}
