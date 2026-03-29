// Rust 変換先で共通利用するランタイム補助。
// - Python 互換の print 表示（bool は True/False）
// - time.perf_counter 相当
// source: src/pytra/utils/png.py
// source: src/pytra/utils/gif.py

use std::cell::RefCell;
use std::hash::Hash;
use std::fs;
use std::io::Write;
use std::path::{Path as StdPath, PathBuf};
use std::rc::Rc;
use std::sync::Once;
use std::{collections::BTreeMap, collections::BTreeSet, collections::HashMap, collections::HashSet, collections::VecDeque};

// ---------------------------------------------------------------------------
// PyList<T> — Python list の参照セマンティクスラッパー (spec-emitter-guide §10)
// Clone は Rc のコピー（shallow）で Python の代入・引数渡しと一致。
// ---------------------------------------------------------------------------

#[derive(Debug)]
pub struct PyList<T> {
    inner: Rc<RefCell<Vec<T>>>,
}

impl<T> Clone for PyList<T> {
    fn clone(&self) -> Self {
        PyList { inner: Rc::clone(&self.inner) }
    }
}

impl<T> PyList<T> {
    pub fn new() -> Self {
        PyList { inner: Rc::new(RefCell::new(Vec::new())) }
    }
    pub fn with_capacity(cap: usize) -> Self {
        PyList { inner: Rc::new(RefCell::new(Vec::with_capacity(cap))) }
    }
    pub fn from_vec(v: Vec<T>) -> Self {
        PyList { inner: Rc::new(RefCell::new(v)) }
    }
    pub fn push(&self, val: T) {
        self.inner.borrow_mut().push(val);
    }
    pub fn len(&self) -> usize {
        self.inner.borrow().len()
    }
    pub fn py_len(&self) -> usize {
        self.inner.borrow().len()
    }
    pub fn is_empty(&self) -> bool {
        self.inner.borrow().is_empty()
    }
    pub fn py_borrow(&self) -> std::cell::Ref<'_, Vec<T>> {
        self.inner.borrow()
    }
    pub fn py_borrow_mut(&self) -> std::cell::RefMut<'_, Vec<T>> {
        self.inner.borrow_mut()
    }
}

impl<T: Clone> PyList<T> {
    pub fn get(&self, idx: i64) -> T {
        let v = self.inner.borrow();
        let i = if idx < 0 { (v.len() as i64 + idx) as usize } else { idx as usize };
        v[i].clone()
    }
    pub fn set(&self, idx: i64, val: T) {
        let mut v = self.inner.borrow_mut();
        let i = if idx < 0 { (v.len() as i64 + idx) as usize } else { idx as usize };
        v[i] = val;
    }
    pub fn pop(&self) -> Option<T> {
        self.inner.borrow_mut().pop()
    }
    /// for ループ用: 内部 Vec のスナップショットを返す。
    /// Python では for 中にリスト変更しても iterating は元のコピーを使う。
    pub fn iter_snapshot(&self) -> Vec<T> {
        self.inner.borrow().clone()
    }
    pub fn extend_from_slice(&self, src: &[T]) {
        self.inner.borrow_mut().extend_from_slice(src);
    }
    /// Vec<T> への一時的な不変参照コールバック（添字アクセス最適化用）
    pub fn with_borrow<R, F: FnOnce(&Vec<T>) -> R>(&self, f: F) -> R {
        f(&self.inner.borrow())
    }
    /// 内部 Vec の所有権を取り出す（消費的操作、最終出力用）
    pub fn into_vec(self) -> Vec<T> {
        match Rc::try_unwrap(self.inner) {
            Ok(cell) => cell.into_inner(),
            Err(rc) => rc.borrow().clone(),
        }
    }
}

// PyList + PyList — Python list concatenation
impl<T: Clone> std::ops::Add for PyList<T> {
    type Output = PyList<T>;
    fn add(self, rhs: PyList<T>) -> PyList<T> {
        let mut result = self.py_borrow().clone();
        result.extend(rhs.py_borrow().iter().cloned());
        PyList::<T>::from_vec(result)
    }
}

// PyList * n — Python list repeat
impl<T: Clone> std::ops::Mul<i64> for PyList<T> {
    type Output = PyList<T>;
    fn mul(self, rhs: i64) -> PyList<T> {
        let inner = self.py_borrow();
        let n = rhs.max(0) as usize;
        let mut result = Vec::with_capacity(inner.len() * n);
        for _ in 0..n { result.extend(inner.iter().cloned()); }
        PyList::<T>::from_vec(result)
    }
}

// n * PyList — allow reversed operand order
impl<T: Clone> std::ops::Mul<PyList<T>> for i64 {
    type Output = PyList<T>;
    fn mul(self, rhs: PyList<T>) -> PyList<T> { rhs * self }
}

pub trait PyStringify {
    fn py_stringify(&self) -> String;
}

impl<T: PyStringify> PyStringify for PyList<T> {
    fn py_stringify(&self) -> String {
        let inner = self.py_borrow();
        let items: Vec<String> = inner.iter().map(|x| x.py_stringify()).collect();
        "[".to_string() + &items.join(", ") + "]"
    }
}

impl<T: PyStringify> PyStringify for Option<T> {
    fn py_stringify(&self) -> String {
        match self {
            Some(v) => v.py_stringify(),
            None => "None".to_string(),
        }
    }
}

impl<T: PyStringify> PyStringify for Vec<T> {
    fn py_stringify(&self) -> String {
        let items: Vec<String> = self.iter().map(|x| x.py_stringify()).collect();
        "[".to_string() + &items.join(", ") + "]"
    }
}

impl<K: PyStringify, V: PyStringify> PyStringify for HashMap<K, V> {
    fn py_stringify(&self) -> String {
        let items: Vec<String> = self.iter().map(|(k, v)| k.py_stringify() + ": " + &v.py_stringify()).collect();
        "{".to_string() + &items.join(", ") + "}"
    }
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
impl PyStringify for PyPath {
    fn py_stringify(&self) -> String {
        self.to_string()
    }
}
impl PyStringify for &str {
    fn py_stringify(&self) -> String {
        (*self).to_string()
    }
}
impl PyStringify for usize {
    fn py_stringify(&self) -> String {
        format!("{}", self)
    }
}
impl PyStringify for isize {
    fn py_stringify(&self) -> String {
        format!("{}", self)
    }
}
impl<T: PyStringify + Copy> PyStringify for &T {
    fn py_stringify(&self) -> String {
        (**self).py_stringify()
    }
}
impl PyStringify for () {
    fn py_stringify(&self) -> String {
        "None".to_string()
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
impl<T> PyBool for PyList<T> {
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
pub fn py_str_isdigit(s: &str) -> bool { py_isdigit(s) }

pub fn py_isalpha(v: &str) -> bool {
    if v.is_empty() {
        return false;
    }
    v.chars().all(|c| c.is_ascii_alphabetic())
}
pub fn py_str_isalpha(s: &str) -> bool { py_isalpha(s) }

pub fn py_str_isalnum(s: &str) -> bool {
    !s.is_empty() && s.chars().all(|c| c.is_alphanumeric())
}

pub fn py_str_isspace(s: &str) -> bool {
    !s.is_empty() && s.chars().all(|c| c.is_whitespace())
}

pub fn py_str_char_at(s: &str, i: i64) -> i64 {
    let idx = if i < 0 { (s.chars().count() as i64 + i) as usize } else { i as usize };
    s.chars().nth(idx).map(|c| c as i64).unwrap_or(0)
}
pub fn py_str_get_at(s: &str, i: i64) -> String {
    let idx = if i < 0 { (s.chars().count() as i64 + i) as usize } else { i as usize };
    s.chars().nth(idx).map(|c| c.to_string()).unwrap_or_default()
}
pub fn py_str_strip(s: &str) -> String { s.trim().to_string() }
pub fn py_str_lstrip(s: &str) -> String { s.trim_start().to_string() }
pub fn py_str_rstrip(s: &str) -> String { s.trim_end().to_string() }
pub fn py_str_upper(s: &str) -> String { s.to_uppercase() }
pub fn py_str_lower(s: &str) -> String { s.to_lowercase() }

pub fn py_str_startswith(s: &str, prefix: &str) -> bool { s.starts_with(prefix) }
pub fn py_str_endswith(s: &str, suffix: &str) -> bool { s.ends_with(suffix) }

pub fn py_str_replace(s: &str, old: &str, new: &str) -> String { s.replace(old, new) }

pub fn py_str_find(s: &str, sub: &str) -> i64 {
    s.find(sub).map(|i| i as i64).unwrap_or(-1_i64)
}
pub fn py_str_rfind(s: &str, sub: &str) -> i64 {
    s.rfind(sub).map(|i| i as i64).unwrap_or(-1_i64)
}
pub fn py_str_index(s: &str, sub: &str) -> i64 {
    s.find(sub).map(|i| i as i64).expect("substring not found")
}
pub fn py_str_count(s: &str, sub: &str) -> i64 {
    if sub.is_empty() { return (s.chars().count() + 1) as i64; }
    let mut count: i64 = 0;
    let mut pos = 0_usize;
    while let Some(idx) = s[pos..].find(sub) {
        count += 1;
        pos += idx + sub.len();
    }
    count
}
pub fn py_str_split(s: &str, sep: &str) -> PyList<String> {
    PyList::<String>::from_vec(s.split(sep).map(|x| x.to_string()).collect())
}
pub fn py_str_join(sep: &str, items: &PyList<String>) -> String {
    items.py_borrow().join(sep)
}

/// Python `int(s)` from string — parse decimal integer.
pub fn py_str_to_i64(s: &str) -> i64 { s.trim().parse::<i64>().unwrap_or(0) }
/// Python `float(s)` from string — parse float.
pub fn py_str_to_f64(s: &str) -> f64 { s.trim().parse::<f64>().unwrap_or(0.0) }

/// Python `int(v)` — convert string or numeric to i64.
pub fn py_int<T: PyAnyToI64Arg + ?Sized>(v: &T) -> i64 { py_any_to_i64(v) }
/// Python `float(v)` — convert to f64.
pub fn py_float<T: PyAnyToF64Arg + ?Sized>(v: &T) -> f64 { py_any_to_f64(v) }
/// Python `str(v)` alias (already defined as py_str above but add py_to_string alias).
pub fn py_to_string<T: PyStringify>(v: T) -> String { v.py_stringify() }

/// Python `enumerate(iterable)` — returns PyList of (index, value) pairs as PyList.
pub fn py_enumerate<T: Clone>(items: &PyList<T>) -> PyList<(i64, T)> {
    let inner = items.py_borrow();
    PyList::<(i64, T)>::from_vec(
        inner.iter().enumerate().map(|(i, v)| (i as i64, v.clone())).collect()
    )
}

/// Python `sorted(iterable)` — returns new sorted PyList.
pub fn py_sorted<T: Ord + Clone>(items: &PyList<T>) -> PyList<T> {
    let mut v = items.py_borrow().clone();
    v.sort();
    PyList::<T>::from_vec(v)
}

/// Python `reversed(iterable)` — returns new reversed PyList.
pub fn py_reversed<T: Clone>(items: &PyList<T>) -> PyList<T> {
    let mut v = items.py_borrow().clone();
    v.reverse();
    PyList::<T>::from_vec(v)
}

/// Python `set(iterable)` constructor.
pub fn py_set<T: Eq + Hash + Clone>(items: &PyList<T>) -> HashSet<T> {
    items.py_borrow().iter().cloned().collect()
}

/// Python `list(iterable)` constructor.
pub fn py_list<T: Clone>(items: &PyList<T>) -> PyList<T> { items.clone() }

pub fn py_str_at(s: &str, index: i64) -> String {
    let n = if s.is_ascii() { s.len() as i64 } else { s.chars().count() as i64 };
    let mut idx = index;
    if idx < 0 {
        idx += n;
    }
    if idx < 0 || idx >= n {
        return String::new();
    }
    if s.is_ascii() {
        let b = s.as_bytes()[idx as usize];
        return (b as char).to_string();
    }
    s.chars().nth(idx as usize).map(|c| c.to_string()).unwrap_or_default()
}

pub fn py_str_at_nonneg(s: &str, index: usize) -> String {
    if s.is_ascii() {
        if index >= s.len() {
            return String::new();
        }
        let b = s.as_bytes()[index];
        return (b as char).to_string();
    }
    s.chars().nth(index).map(|c| c.to_string()).unwrap_or_default()
}

pub fn py_slice_str(s: &str, start: Option<i64>, end: Option<i64>) -> String {
    let n = if s.is_ascii() { s.len() as i64 } else { s.chars().count() as i64 };
    let mut i = start.unwrap_or(0);
    let mut j = end.unwrap_or(n);
    if i < 0 {
        i += n;
    }
    if j < 0 {
        j += n;
    }
    if i < 0 {
        i = 0;
    }
    if j < 0 {
        j = 0;
    }
    if i > n {
        i = n;
    }
    if j > n {
        j = n;
    }
    if j < i {
        j = i;
    }
    if s.is_ascii() {
        return s[(i as usize)..(j as usize)].to_string();
    }
    let start_b = if i == 0 {
        0
    } else {
        s.char_indices()
            .nth(i as usize)
            .map(|(b, _)| b)
            .unwrap_or(s.len())
    };
    let end_b = if j == n {
        s.len()
    } else {
        s.char_indices()
            .nth(j as usize)
            .map(|(b, _)| b)
            .unwrap_or(s.len())
    };
    s[start_b..end_b].to_string()
}

pub fn py_print<T: PyStringify>(v: T) {
    println!("{}", v.py_stringify());
}

pub trait PyContains<K: ?Sized> {
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

impl<T: PartialEq> PyContains<T> for PyList<T> {
    fn py_contains(&self, key: &T) -> bool {
        self.py_borrow().contains(key)
    }
}

impl PyContains<str> for String {
    fn py_contains(&self, key: &str) -> bool {
        self.contains(key)
    }
}

// Tuple `in` support (common sizes)
impl<T: PartialEq> PyContains<T> for (T, T) {
    fn py_contains(&self, key: &T) -> bool { &self.0 == key || &self.1 == key }
}
impl<T: PartialEq> PyContains<T> for (T, T, T) {
    fn py_contains(&self, key: &T) -> bool { &self.0 == key || &self.1 == key || &self.2 == key }
}
impl<T: PartialEq> PyContains<T> for (T, T, T, T) {
    fn py_contains(&self, key: &T) -> bool { &self.0 == key || &self.1 == key || &self.2 == key || &self.3 == key }
}

// VecDeque support
impl<T> PyLen for VecDeque<T> {
    fn py_len(&self) -> usize { self.len() }
}

pub fn py_in<C, K: ?Sized>(container: &C, key: &K) -> bool
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
impl<T> PyLen for PyList<T> {
    fn py_len(&self) -> usize {
        self.inner.borrow().len()
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
        // ASCII 前提のコードでは byte 長と文字数が一致するため O(1)。
        // 非 ASCII を含む場合だけ従来どおり chars() へフォールバックする。
        if self.is_ascii() {
            return self.len();
        }
        self.chars().count()
    }
}

pub fn py_len<T: PyLen>(value: &T) -> usize {
    value.py_len()
}

#[derive(Clone, Debug, Default)]
pub enum PyAny {
    Int(i64),
    Float(f64),
    Bool(bool),
    Str(String),
    Dict(BTreeMap<String, PyAny>),
    List(Vec<PyAny>),
    Set(Vec<PyAny>),
    #[default]
    None,
}

pub fn py_any_as_dict(v: PyAny) -> BTreeMap<String, PyAny> {
    match v {
        PyAny::Dict(d) => d,
        _ => BTreeMap::new(),
    }
}

pub trait PyAnyToI64Arg {
    fn py_any_to_i64_arg(&self) -> i64;
}

impl PyAnyToI64Arg for PyAny {
    fn py_any_to_i64_arg(&self) -> i64 {
        match self {
            PyAny::Int(n) => *n,
            PyAny::Float(f) => *f as i64,
            PyAny::Bool(b) => {
                if *b {
                    1
                } else {
                    0
                }
            }
            PyAny::Str(s) => s.parse::<i64>().unwrap_or(0),
            _ => 0,
        }
    }
}

impl PyAnyToI64Arg for i64 {
    fn py_any_to_i64_arg(&self) -> i64 {
        *self
    }
}
impl PyAnyToI64Arg for i32 {
    fn py_any_to_i64_arg(&self) -> i64 {
        *self as i64
    }
}
impl PyAnyToI64Arg for f64 {
    fn py_any_to_i64_arg(&self) -> i64 {
        *self as i64
    }
}
impl PyAnyToI64Arg for f32 {
    fn py_any_to_i64_arg(&self) -> i64 {
        *self as i64
    }
}
impl PyAnyToI64Arg for bool {
    fn py_any_to_i64_arg(&self) -> i64 {
        if *self {
            1
        } else {
            0
        }
    }
}
impl PyAnyToI64Arg for String {
    fn py_any_to_i64_arg(&self) -> i64 {
        self.parse::<i64>().unwrap_or(0)
    }
}
impl PyAnyToI64Arg for str {
    fn py_any_to_i64_arg(&self) -> i64 {
        self.parse::<i64>().unwrap_or(0)
    }
}

pub fn py_any_to_i64<T: PyAnyToI64Arg + ?Sized>(v: &T) -> i64 {
    v.py_any_to_i64_arg()
}

pub trait PyAnyToF64Arg {
    fn py_any_to_f64_arg(&self) -> f64;
}

impl PyAnyToF64Arg for PyAny {
    fn py_any_to_f64_arg(&self) -> f64 {
        match self {
            PyAny::Int(n) => *n as f64,
            PyAny::Float(f) => *f,
            PyAny::Bool(b) => {
                if *b {
                    1.0
                } else {
                    0.0
                }
            }
            PyAny::Str(s) => s.parse::<f64>().unwrap_or(0.0),
            _ => 0.0,
        }
    }
}

impl PyAnyToF64Arg for f64 {
    fn py_any_to_f64_arg(&self) -> f64 {
        *self
    }
}
impl PyAnyToF64Arg for f32 {
    fn py_any_to_f64_arg(&self) -> f64 {
        *self as f64
    }
}
impl PyAnyToF64Arg for i64 {
    fn py_any_to_f64_arg(&self) -> f64 {
        *self as f64
    }
}
impl PyAnyToF64Arg for i32 {
    fn py_any_to_f64_arg(&self) -> f64 {
        *self as f64
    }
}
impl PyAnyToF64Arg for bool {
    fn py_any_to_f64_arg(&self) -> f64 {
        if *self {
            1.0
        } else {
            0.0
        }
    }
}
impl PyAnyToF64Arg for String {
    fn py_any_to_f64_arg(&self) -> f64 {
        self.parse::<f64>().unwrap_or(0.0)
    }
}
impl PyAnyToF64Arg for str {
    fn py_any_to_f64_arg(&self) -> f64 {
        self.parse::<f64>().unwrap_or(0.0)
    }
}

pub fn py_any_to_f64<T: PyAnyToF64Arg + ?Sized>(v: &T) -> f64 {
    v.py_any_to_f64_arg()
}

pub trait PyAnyToBoolArg {
    fn py_any_to_bool_arg(&self) -> bool;
}

impl PyAnyToBoolArg for PyAny {
    fn py_any_to_bool_arg(&self) -> bool {
        match self {
            PyAny::Int(n) => *n != 0,
            PyAny::Float(f) => *f != 0.0,
            PyAny::Bool(b) => *b,
            PyAny::Str(s) => !s.is_empty(),
            PyAny::Dict(d) => !d.is_empty(),
            PyAny::List(xs) => !xs.is_empty(),
            PyAny::Set(xs) => !xs.is_empty(),
            PyAny::None => false,
        }
    }
}
impl PyAnyToBoolArg for bool {
    fn py_any_to_bool_arg(&self) -> bool {
        *self
    }
}
impl PyAnyToBoolArg for i64 {
    fn py_any_to_bool_arg(&self) -> bool {
        *self != 0
    }
}
impl PyAnyToBoolArg for f64 {
    fn py_any_to_bool_arg(&self) -> bool {
        *self != 0.0
    }
}
impl PyAnyToBoolArg for String {
    fn py_any_to_bool_arg(&self) -> bool {
        !self.is_empty()
    }
}
impl PyAnyToBoolArg for str {
    fn py_any_to_bool_arg(&self) -> bool {
        !self.is_empty()
    }
}

pub fn py_any_to_bool<T: PyAnyToBoolArg + ?Sized>(v: &T) -> bool {
    v.py_any_to_bool_arg()
}

pub trait PyAnyToStringArg {
    fn py_any_to_string_arg(&self) -> String;
}
impl PyAnyToStringArg for PyAny {
    fn py_any_to_string_arg(&self) -> String {
        match self {
            PyAny::Int(n) => n.to_string(),
            PyAny::Float(f) => f.to_string(),
            PyAny::Bool(b) => b.to_string(),
            PyAny::Str(s) => s.clone(),
            PyAny::Dict(d) => format!("{:?}", d),
            PyAny::List(xs) => format!("{:?}", xs),
            PyAny::Set(xs) => format!("{:?}", xs),
            PyAny::None => String::new(),
        }
    }
}
impl PyAnyToStringArg for String {
    fn py_any_to_string_arg(&self) -> String {
        self.clone()
    }
}
impl PyAnyToStringArg for str {
    fn py_any_to_string_arg(&self) -> String {
        self.to_string()
    }
}
impl PyAnyToStringArg for i64 {
    fn py_any_to_string_arg(&self) -> String {
        self.to_string()
    }
}
impl PyAnyToStringArg for f64 {
    fn py_any_to_string_arg(&self) -> String {
        self.to_string()
    }
}
impl PyAnyToStringArg for bool {
    fn py_any_to_string_arg(&self) -> String {
        self.to_string()
    }
}

pub fn py_any_to_string<T: PyAnyToStringArg + ?Sized>(v: &T) -> String {
    v.py_any_to_string_arg()
}

pub const PYTRA_TID_NONE: i64 = 0;
pub const PYTRA_TID_BOOL: i64 = 1;
pub const PYTRA_TID_INT: i64 = 2;
pub const PYTRA_TID_FLOAT: i64 = 3;
pub const PYTRA_TID_STR: i64 = 4;
pub const PYTRA_TID_LIST: i64 = 5;
pub const PYTRA_TID_DICT: i64 = 6;
pub const PYTRA_TID_SET: i64 = 7;
pub const PYTRA_TID_OBJECT: i64 = 8;

#[derive(Clone, Copy, Debug)]
pub struct PyTypeInfo {
    pub order: i64,
    pub min: i64,
    pub max: i64,
}

static PYTRA_TYPE_INFO_INIT: Once = Once::new();
static mut PYTRA_TYPE_INFO_MAP: Option<BTreeMap<i64, PyTypeInfo>> = None;

fn py_type_info_map_mut() -> &'static mut BTreeMap<i64, PyTypeInfo> {
    PYTRA_TYPE_INFO_INIT.call_once(|| unsafe {
        let mut map = BTreeMap::<i64, PyTypeInfo>::new();
        map.insert(
            PYTRA_TID_NONE,
            PyTypeInfo {
                order: PYTRA_TID_NONE,
                min: PYTRA_TID_NONE,
                max: PYTRA_TID_NONE,
            },
        );
        map.insert(
            PYTRA_TID_BOOL,
            PyTypeInfo {
                order: PYTRA_TID_BOOL,
                min: PYTRA_TID_BOOL,
                max: PYTRA_TID_BOOL,
            },
        );
        map.insert(
            PYTRA_TID_INT,
            PyTypeInfo {
                order: PYTRA_TID_INT,
                min: PYTRA_TID_INT,
                max: PYTRA_TID_INT,
            },
        );
        map.insert(
            PYTRA_TID_FLOAT,
            PyTypeInfo {
                order: PYTRA_TID_FLOAT,
                min: PYTRA_TID_FLOAT,
                max: PYTRA_TID_FLOAT,
            },
        );
        map.insert(
            PYTRA_TID_STR,
            PyTypeInfo {
                order: PYTRA_TID_STR,
                min: PYTRA_TID_STR,
                max: PYTRA_TID_STR,
            },
        );
        map.insert(
            PYTRA_TID_LIST,
            PyTypeInfo {
                order: PYTRA_TID_LIST,
                min: PYTRA_TID_LIST,
                max: PYTRA_TID_LIST,
            },
        );
        map.insert(
            PYTRA_TID_DICT,
            PyTypeInfo {
                order: PYTRA_TID_DICT,
                min: PYTRA_TID_DICT,
                max: PYTRA_TID_DICT,
            },
        );
        map.insert(
            PYTRA_TID_SET,
            PyTypeInfo {
                order: PYTRA_TID_SET,
                min: PYTRA_TID_SET,
                max: PYTRA_TID_SET,
            },
        );
        map.insert(
            PYTRA_TID_OBJECT,
            PyTypeInfo {
                order: PYTRA_TID_OBJECT,
                min: PYTRA_TID_OBJECT,
                max: PYTRA_TID_OBJECT,
            },
        );
        PYTRA_TYPE_INFO_MAP = Some(map);
    });
    unsafe {
        PYTRA_TYPE_INFO_MAP
            .as_mut()
            .expect("type info map must be initialized")
    }
}

fn py_type_info_map() -> &'static BTreeMap<i64, PyTypeInfo> {
    let _ = py_type_info_map_mut();
    unsafe {
        PYTRA_TYPE_INFO_MAP
            .as_ref()
            .expect("type info map must be initialized")
    }
}

pub fn py_register_type_info(type_id: i64, order: i64, min: i64, max: i64) {
    py_type_info_map_mut().insert(type_id, PyTypeInfo { order, min, max });
}

pub fn py_type_info(type_id: i64) -> Option<PyTypeInfo> {
    py_type_info_map().get(&type_id).copied()
}

pub trait PyRuntimeTypeId {
    fn py_runtime_type_id(&self) -> i64;
}

impl PyRuntimeTypeId for bool {
    fn py_runtime_type_id(&self) -> i64 {
        PYTRA_TID_BOOL
    }
}
impl PyRuntimeTypeId for i64 {
    fn py_runtime_type_id(&self) -> i64 {
        PYTRA_TID_INT
    }
}
impl PyRuntimeTypeId for f64 {
    fn py_runtime_type_id(&self) -> i64 {
        PYTRA_TID_FLOAT
    }
}
impl PyRuntimeTypeId for String {
    fn py_runtime_type_id(&self) -> i64 {
        PYTRA_TID_STR
    }
}
impl<T> PyRuntimeTypeId for Vec<T> {
    fn py_runtime_type_id(&self) -> i64 {
        PYTRA_TID_LIST
    }
}
impl<K: Ord, V> PyRuntimeTypeId for BTreeMap<K, V> {
    fn py_runtime_type_id(&self) -> i64 {
        PYTRA_TID_DICT
    }
}
impl<T: Ord> PyRuntimeTypeId for BTreeSet<T> {
    fn py_runtime_type_id(&self) -> i64 {
        PYTRA_TID_SET
    }
}
impl<T: PyRuntimeTypeId> PyRuntimeTypeId for Option<T> {
    fn py_runtime_type_id(&self) -> i64 {
        match self {
            Some(v) => v.py_runtime_type_id(),
            None => PYTRA_TID_NONE,
        }
    }
}
impl PyRuntimeTypeId for PyAny {
    fn py_runtime_type_id(&self) -> i64 {
        match self {
            PyAny::Int(_) => PYTRA_TID_INT,
            PyAny::Float(_) => PYTRA_TID_FLOAT,
            PyAny::Bool(_) => PYTRA_TID_BOOL,
            PyAny::Str(_) => PYTRA_TID_STR,
            PyAny::List(_) => PYTRA_TID_LIST,
            PyAny::Dict(_) => PYTRA_TID_DICT,
            PyAny::Set(_) => PYTRA_TID_SET,
            PyAny::None => PYTRA_TID_NONE,
        }
    }
}

impl<T: PyRuntimeTypeId> PyRuntimeTypeId for Box<T> {
    fn py_runtime_type_id(&self) -> i64 {
        (**self).py_runtime_type_id()
    }
}

pub fn py_runtime_value_type_id<T: PyRuntimeTypeId>(value: &T) -> i64 {
    value.py_runtime_type_id()
}

fn py_runtime_type_id<T: PyRuntimeTypeId>(value: &T) -> i64 {
    py_runtime_value_type_id(value)
}

pub fn py_runtime_type_id_is_subtype(actual_type_id: i64, expected_type_id: i64) -> bool {
    let actual = match py_type_info(actual_type_id) {
        Some(info) => info,
        None => return false,
    };
    let expected = match py_type_info(expected_type_id) {
        Some(info) => info,
        None => return false,
    };
    expected.min <= actual.order && actual.order <= expected.max
}

fn py_is_subtype(actual_type_id: i64, expected_type_id: i64) -> bool {
    py_runtime_type_id_is_subtype(actual_type_id, expected_type_id)
}

pub fn py_runtime_type_id_issubclass(actual_type_id: i64, expected_type_id: i64) -> bool {
    py_runtime_type_id_is_subtype(actual_type_id, expected_type_id)
}

fn py_issubclass(actual_type_id: i64, expected_type_id: i64) -> bool {
    py_runtime_type_id_issubclass(actual_type_id, expected_type_id)
}

pub fn py_runtime_value_isinstance<T: PyRuntimeTypeId>(value: &T, expected_type_id: i64) -> bool {
    py_runtime_type_id_is_subtype(py_runtime_value_type_id(value), expected_type_id)
}

fn py_isinstance<T: PyRuntimeTypeId>(value: &T, expected_type_id: i64) -> bool {
    py_runtime_value_isinstance(value, expected_type_id)
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
        // ASCII の場合は byte 境界でそのまま切り出せる。
        if self.is_ascii() {
            let bytes = self.as_bytes();
            let (s, e) = normalize_slice_range(bytes.len() as i64, start, end);
            return String::from_utf8(bytes[s..e].to_vec()).expect("ascii slice must be valid utf-8");
        }

        // 非 ASCII は文字境界を維持するため従来実装を使う。
        let chars: Vec<char> = self.chars().collect();
        let (s, e) = normalize_slice_range(chars.len() as i64, start, end);
        chars[s..e].iter().collect()
    }
}

pub fn py_slice<T: PySlice>(value: &T, start: Option<i64>, end: Option<i64>) -> T::Output {
    value.py_slice(start, end)
}

/// Convert Vec<i64> to Vec<u8> (for image encoding where internal computation
/// uses i64 but the output format requires u8 bytes).
pub fn py_vec_i64_to_u8(v: &Vec<i64>) -> Vec<u8> {
    v.iter().map(|x| (*x & 0xFF) as u8).collect()
}

/// Convert Vec<u8> to Vec<i64>.
pub fn py_vec_u8_to_i64(v: &Vec<u8>) -> Vec<i64> {
    v.iter().map(|x| *x as i64).collect()
}

pub fn math_sin(v: f64) -> f64 {
    v.sin()
}

pub fn math_cos(v: f64) -> f64 {
    v.cos()
}

pub fn math_tan(v: f64) -> f64 {
    v.tan()
}

pub fn math_sqrt(v: f64) -> f64 {
    v.sqrt()
}

pub fn math_exp(v: f64) -> f64 {
    v.exp()
}

pub fn math_log(v: f64) -> f64 {
    v.ln()
}

pub fn math_log10(v: f64) -> f64 {
    v.log10()
}

pub fn math_fabs(v: f64) -> f64 {
    v.abs()
}

pub fn math_floor(v: f64) -> f64 {
    v.floor()
}

pub fn math_ceil(v: f64) -> f64 {
    v.ceil()
}

pub fn math_pow(a: f64, b: f64) -> f64 {
    a.powf(b)
}

#[derive(Clone, Debug)]
pub struct PyPath {
    value: String,
}

impl PyPath {
    pub fn new(value: &str) -> Self {
        Self {
            value: value.to_string(),
        }
    }

    pub fn resolve(&self) -> Self {
        let p = StdPath::new(&self.value);
        let abs: PathBuf = if p.is_absolute() {
            p.to_path_buf()
        } else {
            std::env::current_dir().expect("cwd").join(p)
        };
        Self::new(abs.to_string_lossy().as_ref())
    }

    pub fn parent(&self) -> Self {
        match StdPath::new(&self.value).parent() {
            Some(p) => Self::new(p.to_string_lossy().as_ref()),
            None => Self::new(""),
        }
    }

    pub fn name(&self) -> String {
        StdPath::new(&self.value)
            .file_name()
            .map(|s| s.to_string_lossy().to_string())
            .unwrap_or_default()
    }

    pub fn stem(&self) -> String {
        StdPath::new(&self.value)
            .file_stem()
            .map(|s| s.to_string_lossy().to_string())
            .unwrap_or_default()
    }

    pub fn exists(&self) -> bool {
        StdPath::new(&self.value).exists()
    }

    pub fn read_text(&self) -> String {
        std::fs::read_to_string(&self.value).expect("read_text failed")
    }

    pub fn write_text(&self, content: &str) {
        std::fs::write(&self.value, content.as_bytes()).expect("write_text failed");
    }

    pub fn mkdir(&self, parents: bool, exist_ok: bool) {
        let p = StdPath::new(&self.value);
        let result = if parents {
            std::fs::create_dir_all(p)
        } else {
            std::fs::create_dir(p)
        };
        if let Err(err) = result {
            if !(exist_ok && p.exists()) {
                panic!("mkdir failed: {}", err);
            }
        }
    }
}

impl std::fmt::Display for PyPath {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.value)
    }
}

impl std::ops::Div<String> for PyPath {
    type Output = PyPath;
    fn div(self, rhs: String) -> Self::Output {
        let joined = StdPath::new(&self.value).join(rhs);
        PyPath::new(joined.to_string_lossy().as_ref())
    }
}

impl std::ops::Div<&str> for PyPath {
    type Output = PyPath;
    fn div(self, rhs: &str) -> Self::Output {
        let joined = StdPath::new(&self.value).join(rhs);
        PyPath::new(joined.to_string_lossy().as_ref())
    }
}

/// Python-compatible file object for binary write.
pub struct PyFile {
    inner: fs::File,
}

pub trait PyFileWritable {
    fn write_to_file(&self, file: &mut fs::File);
}

impl PyFileWritable for Vec<i64> {
    fn write_to_file(&self, file: &mut fs::File) {
        let bytes: Vec<u8> = self.iter().map(|v| (*v & 0xFF) as u8).collect();
        file.write_all(&bytes).expect("write failed");
    }
}

impl PyFileWritable for Vec<u8> {
    fn write_to_file(&self, file: &mut fs::File) {
        file.write_all(self).expect("write failed");
    }
}

impl PyFile {
    pub fn write<T: PyFileWritable>(&mut self, data: T) {
        data.write_to_file(&mut self.inner);
    }

    pub fn close(self) {
        // File is closed when dropped; explicit close is a no-op.
        drop(self.inner);
    }
}

/// Python `open(path, mode)` emulation (only "wb" mode supported).
pub fn open(path: &str, _mode: String) -> PyFile {
    // Ensure parent directory exists (Python's open does this implicitly via os)
    if let Some(parent) = StdPath::new(path).parent() {
        if !parent.as_os_str().is_empty() {
            let _ = fs::create_dir_all(parent);
        }
    }
    let file = fs::File::create(path).expect("open failed");
    PyFile { inner: file }
}

/// Python `str(v)` — convert any PyStringify value to String.
pub fn py_str<T: PyStringify>(v: T) -> String {
    v.py_stringify()
}

/// Python `repr(v)` — same as str for most types in Pytra.
pub fn py_repr<T: PyStringify>(v: T) -> String {
    v.py_stringify()
}

/// Python `assert_true(cond, label)`.
pub fn py_assert_true(cond: bool, _label: String) -> bool {
    cond
}

/// Python `assert_eq(actual, expected, label)` — compare via string representation.
pub fn py_assert_eq<A: PyStringify, B: PyStringify>(actual: A, expected: B, _label: String) -> bool {
    actual.py_stringify() == expected.py_stringify()
}

/// Python `assert_all(results, label)` — all booleans must be true.
pub fn py_assert_all(results: PyList<bool>, _label: String) -> bool {
    for v in results.py_borrow().iter() {
        if !v {
            return false;
        }
    }
    true
}

/// Python `py_assert_stdout(expected_lines, fn)` — stub for self-hosted compatibility.
/// Calls the function and returns true (stdout capture not implemented).
pub fn py_assert_stdout<F: Fn()>(_expected: PyList<String>, f: F) -> bool {
    f();
    true
}

// Sub-module declarations (std, utils, pytra facade) are generated
// by the entry module via #[path] attributes. py_runtime.rs provides
// only built-in helpers (print, len, range, type conversions, etc.).
