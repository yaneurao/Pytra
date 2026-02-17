#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_floor, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_isalpha, py_isdigit, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

// このファイルは自動生成です（native Rust mode）。

fn comp_like_24(mut x: i64) -> i64 {
    let mut values: Vec<i64> = { let mut __pytra_listcomp_1 = Vec::new(); for i in (vec![1, 2, 3, 4]).clone() {     __pytra_listcomp_1.push(i); } __pytra_listcomp_1 };
    return ((x) + (1));
}

fn main() {
    py_print(comp_like_24(5));
}
