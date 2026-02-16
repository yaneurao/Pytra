#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_isalpha, py_isdigit, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

// このファイルは自動生成です（native Rust mode）。

fn main() -> () {
    let mut nums: Vec<i64> = vec![10, 20, 30, 40, 50];
    let mut text: String = "abcdef".to_string();
    let mut mid_nums: Vec<i64> = py_slice(&(nums), Some(1), Some(4));
    let mut mid_text: String = py_slice(&(text), Some(2), Some(5));
    py_print((mid_nums)[0 as usize]);
    py_print((mid_nums)[2 as usize]);
    py_print(mid_text);
}
