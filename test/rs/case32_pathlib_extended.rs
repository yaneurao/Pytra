#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{py_print};

// このファイルは自動生成です（native Rust mode）。

fn main() -> () {
    let mut root = py_runtime::PyPath::new(&(format!("{}", "test/obj/pathlib_case32".to_string())));
    root.mkdir(true, true);
    let mut child = ((root) / ("values.txt".to_string()));
    child.write_text(&(format!("{}", "42".to_string())));
    py_print(child.exists());
    py_print(child.name());
    py_print(child.stem());
    py_print(((child.parent()) / ("values.txt".to_string())).exists());
    py_print(child.read_text());
}
