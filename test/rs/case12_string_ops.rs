#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_floor, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_isalpha, py_isdigit, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

// このファイルは自動生成です（native Rust mode）。

fn decorate(name: &String) -> String {
    let mut prefix: String = "[USER] ".to_string();
    let mut message: String = format!("{}{}", prefix, name);
    return format!("{}{}", message, "!".to_string());
}

fn main() {
    py_print(decorate(&("Alice".to_string())));
}
