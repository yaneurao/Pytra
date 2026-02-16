#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{perf_counter, py_in, py_len, py_print, py_slice};

// このファイルは自動生成です（native Rust mode）。

struct Counter {
    value: i64,
}

impl Counter {
    fn new() -> Self {
        let mut self_obj = Self {
            value: 0,
        };
        self_obj
    }

    fn inc(&mut self) -> i64 {
        self.value = self.value + 1;
        return self.value;
    }
}

fn main() {
    let mut c: Counter = Counter::new();
    py_print(c.inc());
}
