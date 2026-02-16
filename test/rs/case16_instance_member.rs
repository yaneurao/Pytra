#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{perf_counter, py_in, py_len, py_print, py_slice};

// このファイルは自動生成です（native Rust mode）。

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

    fn total(&self) -> i64 {
        return ((self.x) + (self.y));
    }
}

fn main() {
    let mut p: Point = Point::new(2, 5);
    py_print(p.total());
}
