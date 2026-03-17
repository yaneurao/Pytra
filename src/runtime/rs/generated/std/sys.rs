// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/sys.py
// generated-by: tools/gen_runtime_from_manifest.py

mod py_runtime;
pub use crate::py_runtime::{pytra};
use crate::py_runtime::*;

use crate::pytra::std::extern;

fn exit(code: i64) {
    __s.exit(code);
}

fn set_argv(values: &[String]) {
    argv.clear();
    for v in (values).iter() {
        argv.append(v);
    }
}

fn set_path(values: &[String]) {
    path.clear();
    for v in (values).iter() {
        path.append(v);
    }
}

fn write_stderr(text: &str) {
    __s.stderr.write(text);
}

fn write_stdout(text: &str) {
    __s.stdout.write(text);
}

fn main() {
    ("pytra.std.sys: extern-marked sys API with Python runtime fallback.").to_string();
    let argv: Vec<String> = py_extern(__s.argv);
    let path: Vec<String> = py_extern(__s.path);
    let stderr = py_extern(__s.stderr);
    let stdout = py_extern(__s.stdout);
}
