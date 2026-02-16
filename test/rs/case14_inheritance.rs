#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_isalpha, py_isdigit, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

// このファイルは自動生成です（native Rust mode）。

#[derive(Clone)]
struct Animal {
}

impl Animal {
    fn new() -> Self {
        let mut self_obj = Self {
        };
        self_obj
    }

    fn sound(&mut self) -> String {
        return "generic".to_string();
    }
}

#[derive(Clone)]
struct Dog {
}

impl Dog {
    fn new() -> Self {
        let mut self_obj = Self {
        };
        self_obj
    }

    fn bark(&mut self) -> String {
        return format!("{}{}", self.sound(), "-bark".to_string());
    }

    fn sound(&mut self) -> String {
        return "generic".to_string();
    }
}

fn main() {
    let mut d: Dog = Dog::new();
    py_print(d.bark());
}
