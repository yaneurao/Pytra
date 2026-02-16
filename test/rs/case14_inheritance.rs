#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{perf_counter, py_in, py_len, py_print, py_slice};

// このファイルは自動生成です（native Rust mode）。

struct Animal {
}

impl Animal {
    fn new() -> Self {
        let mut self_obj = Self {
        };
        self_obj
    }

    fn sound(&self) -> String {
        return "generic".to_string();
    }
}

struct Dog {
}

impl Dog {
    fn new() -> Self {
        let mut self_obj = Self {
        };
        self_obj
    }

    fn bark(&self) -> String {
        return format!("{}{}", self.sound(), "-bark".to_string());
    }

    fn sound(&self) -> String {
        return "generic".to_string();
    }
}

fn main() {
    let mut d: Dog = Dog::new();
    py_print(d.bark());
}
