// Rust 変換先で共通利用するランタイム補助。
// - Python 互換の print 表示（bool は True/False）
// - time.perf_counter 相当
// - embed モード向けの Python 実行ヘルパ

use std::env;
use std::process::Command;
use std::time::{SystemTime, UNIX_EPOCH};

pub trait PyStringify {
    fn py_stringify(&self) -> String;
}

impl PyStringify for bool {
    fn py_stringify(&self) -> String {
        if *self {
            "True".to_string()
        } else {
            "False".to_string()
        }
    }
}

impl PyStringify for i64 {
    fn py_stringify(&self) -> String {
        format!("{}", self)
    }
}
impl PyStringify for i32 {
    fn py_stringify(&self) -> String {
        format!("{}", self)
    }
}
impl PyStringify for i16 {
    fn py_stringify(&self) -> String {
        format!("{}", self)
    }
}
impl PyStringify for i8 {
    fn py_stringify(&self) -> String {
        format!("{}", self)
    }
}
impl PyStringify for u64 {
    fn py_stringify(&self) -> String {
        format!("{}", self)
    }
}
impl PyStringify for u32 {
    fn py_stringify(&self) -> String {
        format!("{}", self)
    }
}
impl PyStringify for u16 {
    fn py_stringify(&self) -> String {
        format!("{}", self)
    }
}
impl PyStringify for u8 {
    fn py_stringify(&self) -> String {
        format!("{}", self)
    }
}
impl PyStringify for f64 {
    fn py_stringify(&self) -> String {
        format!("{}", self)
    }
}
impl PyStringify for f32 {
    fn py_stringify(&self) -> String {
        format!("{}", self)
    }
}
impl PyStringify for String {
    fn py_stringify(&self) -> String {
        self.clone()
    }
}
impl PyStringify for &str {
    fn py_stringify(&self) -> String {
        (*self).to_string()
    }
}

pub fn py_print<T: PyStringify>(v: T) {
    println!("{}", v.py_stringify());
}

pub fn perf_counter() -> f64 {
    let d = SystemTime::now().duration_since(UNIX_EPOCH).unwrap();
    d.as_secs_f64()
}

fn run_with(interpreter: &str, source: &str) -> Option<i32> {
    let mut cmd = Command::new(interpreter);
    cmd.arg("-c").arg(source);

    // sample/py が `from py_module ...` を使うため `PYTHONPATH=src` を付与する。
    let py_path = match env::var("PYTHONPATH") {
        Ok(v) if !v.is_empty() => format!("src:{}", v),
        _ => "src".to_string(),
    };
    cmd.env("PYTHONPATH", py_path);

    let status = cmd.status().ok()?;
    Some(status.code().unwrap_or(1))
}

pub fn run_embedded_python(source: &str) -> i32 {
    // python3 を優先し、無ければ python を試す。
    if let Some(code) = run_with("python3", source) {
        return code;
    }
    if let Some(code) = run_with("python", source) {
        return code;
    }
    eprintln!("error: python interpreter not found (python3/python)");
    1
}

