#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_floor, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_isalpha, py_isdigit, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

// このファイルは自動生成です（native Rust mode）。

#[derive(Clone)]
struct Multiplier {
}

impl Multiplier {
    fn new() -> Self {
        let mut self_obj = Self {
        };
        self_obj
    }

    fn mul(&mut self, mut x: i64, mut y: i64) -> i64 {
        return ((x) * (y));
    }
}

fn main() {
    let mut m: Multiplier = Multiplier::new();
    py_print(m.mul(6, 7));
}
