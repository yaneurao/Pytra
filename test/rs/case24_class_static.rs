#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{perf_counter, py_in, py_len, py_print, py_slice};

// このファイルは自動生成です（native Rust mode）。

struct Counter26 {
    total: i64,
}

impl Counter26 {
    fn new() -> Self {
        let mut self_obj = Self {
            total: 0,
        };
        self_obj
    }

    fn add(&mut self, x: i64) -> i64 {
        self.total = self.total + x;
        return self.total;
    }
}

fn main() {
    let mut c: Counter26 = Counter26::new();
    py_print(c.add(5));
}
