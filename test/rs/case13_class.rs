#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{perf_counter, py_in, py_len, py_print, py_slice};

// このファイルは自動生成です（native Rust mode）。

struct Multiplier {
}

impl Multiplier {
    fn new() -> Self {
        let mut self_obj = Self {
        };
        self_obj
    }

    fn mul(&self, x: i64, y: i64) -> i64 {
        return ((x) * (y));
    }
}

fn main() {
    let mut m: Multiplier = Multiplier::new();
    py_print(m.mul(6, 7));
}
