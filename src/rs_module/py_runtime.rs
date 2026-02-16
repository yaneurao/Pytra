// Rust 変換先で共通利用するランタイム補助。
// - Python 互換の print 表示（bool は True/False）
// - time.perf_counter 相当
// - embed モード向けの Python 実行ヘルパ

use std::env;
use std::hash::Hash;
use std::fs;
use std::io::Write;
use std::process::Command;
use std::time::{SystemTime, UNIX_EPOCH};
use std::{collections::HashMap, collections::HashSet};

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

pub trait PyBool {
    fn py_bool(&self) -> bool;
}

impl PyBool for bool {
    fn py_bool(&self) -> bool {
        *self
    }
}
impl PyBool for i64 {
    fn py_bool(&self) -> bool {
        *self != 0
    }
}
impl PyBool for i32 {
    fn py_bool(&self) -> bool {
        *self != 0
    }
}
impl PyBool for i16 {
    fn py_bool(&self) -> bool {
        *self != 0
    }
}
impl PyBool for i8 {
    fn py_bool(&self) -> bool {
        *self != 0
    }
}
impl PyBool for u64 {
    fn py_bool(&self) -> bool {
        *self != 0
    }
}
impl PyBool for u32 {
    fn py_bool(&self) -> bool {
        *self != 0
    }
}
impl PyBool for u16 {
    fn py_bool(&self) -> bool {
        *self != 0
    }
}
impl PyBool for u8 {
    fn py_bool(&self) -> bool {
        *self != 0
    }
}
impl PyBool for f64 {
    fn py_bool(&self) -> bool {
        *self != 0.0
    }
}
impl PyBool for f32 {
    fn py_bool(&self) -> bool {
        *self != 0.0
    }
}
impl PyBool for String {
    fn py_bool(&self) -> bool {
        !self.is_empty()
    }
}
impl<T> PyBool for Vec<T> {
    fn py_bool(&self) -> bool {
        !self.is_empty()
    }
}
impl<K, V> PyBool for HashMap<K, V> {
    fn py_bool(&self) -> bool {
        !self.is_empty()
    }
}
impl<T> PyBool for HashSet<T> {
    fn py_bool(&self) -> bool {
        !self.is_empty()
    }
}

pub fn py_bool<T: PyBool>(v: &T) -> bool {
    v.py_bool()
}

pub fn py_isdigit(v: &str) -> bool {
    if v.is_empty() {
        return false;
    }
    v.chars().all(|c| c.is_ascii_digit())
}

pub fn py_isalpha(v: &str) -> bool {
    if v.is_empty() {
        return false;
    }
    v.chars().all(|c| c.is_ascii_alphabetic())
}

pub fn py_print<T: PyStringify>(v: T) {
    println!("{}", v.py_stringify());
}

pub trait PyContains<K> {
    fn py_contains(&self, key: &K) -> bool;
}

impl<T: PartialEq> PyContains<T> for Vec<T> {
    fn py_contains(&self, key: &T) -> bool {
        self.contains(key)
    }
}

impl<T: Eq + Hash> PyContains<T> for HashSet<T> {
    fn py_contains(&self, key: &T) -> bool {
        self.contains(key)
    }
}

impl<K: Eq + Hash, V> PyContains<K> for HashMap<K, V> {
    fn py_contains(&self, key: &K) -> bool {
        self.contains_key(key)
    }
}

pub fn py_in<C, K>(container: &C, key: &K) -> bool
where
    C: PyContains<K>,
{
    container.py_contains(key)
}

pub trait PyLen {
    fn py_len(&self) -> usize;
}

impl<T> PyLen for Vec<T> {
    fn py_len(&self) -> usize {
        self.len()
    }
}

impl<K, V> PyLen for HashMap<K, V> {
    fn py_len(&self) -> usize {
        self.len()
    }
}

impl<T> PyLen for HashSet<T> {
    fn py_len(&self) -> usize {
        self.len()
    }
}

impl PyLen for String {
    fn py_len(&self) -> usize {
        self.chars().count()
    }
}

pub fn py_len<T: PyLen>(value: &T) -> usize {
    value.py_len()
}

pub trait PySlice {
    type Output;
    fn py_slice(&self, start: Option<i64>, end: Option<i64>) -> Self::Output;
}

fn normalize_slice_range(len: i64, start: Option<i64>, end: Option<i64>) -> (usize, usize) {
    let mut s = start.unwrap_or(0);
    let mut e = end.unwrap_or(len);
    if s < 0 {
        s += len;
    }
    if e < 0 {
        e += len;
    }
    if s < 0 {
        s = 0;
    }
    if e < 0 {
        e = 0;
    }
    if s > len {
        s = len;
    }
    if e > len {
        e = len;
    }
    if e < s {
        e = s;
    }
    (s as usize, e as usize)
}

impl<T: Clone> PySlice for Vec<T> {
    type Output = Vec<T>;
    fn py_slice(&self, start: Option<i64>, end: Option<i64>) -> Self::Output {
        let (s, e) = normalize_slice_range(self.len() as i64, start, end);
        self[s..e].to_vec()
    }
}

impl PySlice for String {
    type Output = String;
    fn py_slice(&self, start: Option<i64>, end: Option<i64>) -> Self::Output {
        let chars: Vec<char> = self.chars().collect();
        let (s, e) = normalize_slice_range(chars.len() as i64, start, end);
        chars[s..e].iter().collect()
    }
}

pub fn py_slice<T: PySlice>(value: &T, start: Option<i64>, end: Option<i64>) -> T::Output {
    value.py_slice(start, end)
}

pub fn math_sin(v: f64) -> f64 {
    v.sin()
}

pub fn math_cos(v: f64) -> f64 {
    v.cos()
}

pub fn math_sqrt(v: f64) -> f64 {
    v.sqrt()
}

pub fn math_exp(v: f64) -> f64 {
    v.exp()
}

pub fn py_grayscale_palette() -> Vec<u8> {
    let mut p = Vec::<u8>::with_capacity(256 * 3);
    let mut i: u16 = 0;
    while i < 256 {
        let v = i as u8;
        p.push(v);
        p.push(v);
        p.push(v);
        i += 1;
    }
    p
}

fn gif_lzw_encode(data: &[u8], min_code_size: u8) -> Vec<u8> {
    if data.is_empty() {
        return Vec::new();
    }
    let clear_code: u16 = 1u16 << min_code_size;
    let end_code: u16 = clear_code + 1;
    let code_size: u8 = min_code_size + 1;
    let mut out = Vec::<u8>::new();
    let mut bit_buffer: u32 = 0;
    let mut bit_count: u8 = 0;

    let emit = |code: u16, out: &mut Vec<u8>, bit_buffer: &mut u32, bit_count: &mut u8| {
        *bit_buffer |= (code as u32) << (*bit_count as u32);
        *bit_count += code_size;
        while *bit_count >= 8 {
            out.push((*bit_buffer & 0xFF) as u8);
            *bit_buffer >>= 8;
            *bit_count -= 8;
        }
    };

    emit(clear_code, &mut out, &mut bit_buffer, &mut bit_count);
    for &v in data {
        emit(v as u16, &mut out, &mut bit_buffer, &mut bit_count);
        emit(clear_code, &mut out, &mut bit_buffer, &mut bit_count);
    }
    emit(end_code, &mut out, &mut bit_buffer, &mut bit_count);

    if bit_count > 0 {
        out.push((bit_buffer & 0xFF) as u8);
    }
    out
}

pub fn py_save_gif(
    path: &str,
    width: i64,
    height: i64,
    frames: &Vec<Vec<u8>>,
    palette: &Vec<u8>,
    delay_cs: i64,
    loop_count: i64,
) {
    if palette.len() != 256 * 3 {
        panic!("palette must be 256*3 bytes");
    }
    let w = width as usize;
    let h = height as usize;
    for fr in frames.iter() {
        if fr.len() != w * h {
            panic!("frame size mismatch");
        }
    }

    let mut out = Vec::<u8>::new();
    out.extend_from_slice(b"GIF89a");
    out.extend_from_slice(&(width as u16).to_le_bytes());
    out.extend_from_slice(&(height as u16).to_le_bytes());
    out.push(0xF7);
    out.push(0);
    out.push(0);
    out.extend_from_slice(palette);

    out.extend_from_slice(b"\x21\xFF\x0BNETSCAPE2.0\x03\x01");
    out.extend_from_slice(&(loop_count as u16).to_le_bytes());
    out.push(0);

    for fr in frames.iter() {
        out.extend_from_slice(b"\x21\xF9\x04\x00");
        out.extend_from_slice(&(delay_cs as u16).to_le_bytes());
        out.extend_from_slice(b"\x00\x00");

        out.push(0x2C);
        out.extend_from_slice(&(0u16).to_le_bytes());
        out.extend_from_slice(&(0u16).to_le_bytes());
        out.extend_from_slice(&(width as u16).to_le_bytes());
        out.extend_from_slice(&(height as u16).to_le_bytes());
        out.push(0);

        out.push(8);
        let compressed = gif_lzw_encode(fr, 8);
        let mut pos = 0usize;
        while pos < compressed.len() {
            let remain = compressed.len() - pos;
            let chunk_len = if remain > 255 { 255 } else { remain };
            out.push(chunk_len as u8);
            out.extend_from_slice(&compressed[pos..(pos + chunk_len)]);
            pos += chunk_len;
        }
        out.push(0);
    }

    out.push(0x3B);
    let parent = std::path::Path::new(path).parent();
    if let Some(dir) = parent {
        let _ = fs::create_dir_all(dir);
    }
    let mut f = fs::File::create(path).expect("create gif file failed");
    f.write_all(&out).expect("write gif file failed");
}

pub fn py_write_rgb_png(path: &str, width: i64, height: i64, pixels: &[u8]) {
    // PNG は Rust 標準ライブラリだけでの実装コストが高いため、既存 Python helper を利用する。
    let tmp = env::temp_dir().join(format!(
        "pytra_png_pixels_{}_{}.bin",
        std::process::id(),
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    fs::write(&tmp, pixels).expect("write temp png pixels failed");

    let script = r#"
import os, sys
from py_module import png_helper
p = sys.argv[1]
out_path = sys.argv[2]
w = int(sys.argv[3]); h = int(sys.argv[4])
with open(p, "rb") as f:
    raw = f.read()
png_helper.write_rgb_png(out_path, w, h, raw)
"#;

    let py_path = match env::var("PYTHONPATH") {
        Ok(v) if !v.is_empty() => format!("src:{}", v),
        _ => "src".to_string(),
    };
    let status = Command::new("python3")
        .arg("-c")
        .arg(script)
        .arg(tmp.to_string_lossy().to_string())
        .arg(path)
        .arg(width.to_string())
        .arg(height.to_string())
        .env("PYTHONPATH", py_path)
        .status()
        .expect("python3 execution failed");
    let _ = fs::remove_file(&tmp);
    if !status.success() {
        panic!("py_write_rgb_png failed");
    }
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
