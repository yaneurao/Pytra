#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_isalpha, py_isdigit, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

// このファイルは自動生成です（native Rust mode）。

fn calc_17(mut values: Vec<i64>) -> i64 {
    let mut total: i64 = 0;
    for v in (values).clone() {
        if py_bool(&(((((v) % (2))) == (0)))) {
            total = total + v;
        } else {
            total = total + ((v) * (2));
        }
    }
    return total;
}

fn main() {
    py_print(calc_17(vec![1, 2, 3, 4]));
}
