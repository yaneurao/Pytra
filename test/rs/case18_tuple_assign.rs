#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_floor, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_isalpha, py_isdigit, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

// このファイルは自動生成です（native Rust mode）。

fn swap_sum_18(mut a: i64, mut b: i64) -> i64 {
    let mut x: i64 = a;
    let mut y: i64 = b;
    let __pytra_tuple_0_1 = y;
    let __pytra_tuple_1_2 = x;
    x = __pytra_tuple_0_1;
    y = __pytra_tuple_1_2;
    return ((x) + (y));
}

fn main() {
    py_print(swap_sum_18(10, 20));
}
