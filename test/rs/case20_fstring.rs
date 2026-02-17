#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_floor, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_isalpha, py_isdigit, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

// このファイルは自動生成です（native Rust mode）。

fn make_msg_22(name: &String, mut count: i64) -> String {
    return format!("{}:22:{}", name, count);
}

fn main() {
    py_print(make_msg_22(&("user".to_string()), 7));
}
