#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_floor, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_isalpha, py_isdigit, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

// このファイルは自動生成です（native Rust mode）。

fn square_plus_one(mut n: i64) -> i64 {
    let mut result: i64 = ((n) * (n));
    result = result + 1;
    return result;
}

fn main() {
    py_print(square_plus_one(5));
}
