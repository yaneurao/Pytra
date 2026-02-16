#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_isalpha, py_isdigit, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

// このファイルは自動生成です（native Rust mode）。

#[derive(Clone)]
struct Box100 {
    seed: i64,
}

impl Box100 {
    fn new(seed: i64) -> Self {
        let mut self_obj = Self {
            seed: 0,
        };
        self_obj.seed = seed;
        self_obj
    }

    fn next(&mut self) -> i64 {
        self.seed = self.seed + 1;
        return self.seed;
    }
}

fn main() {
    let mut b: Box100 = Box100::new(3);
    py_print(b.next());
}
