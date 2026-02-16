#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_isalpha, py_isdigit, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

// このファイルは自動生成です（native Rust mode）。

#[derive(Clone)]
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

    fn add(&mut self, mut x: i64) -> i64 {
        self.total = self.total + x;
        return self.total;
    }
}

fn main() {
    let mut c: Counter26 = Counter26::new();
    py_print(c.add(5));
}
