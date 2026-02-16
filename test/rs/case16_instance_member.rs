#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_isalpha, py_isdigit, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

// このファイルは自動生成です（native Rust mode）。

#[derive(Clone)]
struct Point {
    x: i64,
    y: i64,
}

impl Point {
    fn new(x: i64, y: i64) -> Self {
        let mut self_obj = Self {
            x: 0,
            y: 0,
        };
        self_obj.x = x;
        self_obj.y = y;
        self_obj
    }

    fn total(&mut self) -> i64 {
        return ((self.x) + (self.y));
    }
}

fn main() {
    let mut p: Point = Point::new(2, 5);
    py_print(p.total());
}
