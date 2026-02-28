// Rust 変換先で共通利用するランタイム補助。
// - Python 互換の print 表示（bool は True/False）
// - time.perf_counter 相当

use std::hash::Hash;
use std::fs;
use std::io::Write;
use std::path::{Path as StdPath, PathBuf};
use std::sync::Once;
use std::time::Instant;
use std::{collections::BTreeMap, collections::BTreeSet, collections::HashMap, collections::HashSet};

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

pub fn py_runtime_type_id<T: PyRuntimeTypeId>(value: &T) -> i64 {
    value.py_runtime_type_id()
}

pub fn py_is_subtype(actual_type_id: i64, expected_type_id: i64) -> bool {
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

pub fn py_issubclass(actual_type_id: i64, expected_type_id: i64) -> bool {
    py_is_subtype(actual_type_id, expected_type_id)
}

pub fn py_isinstance<T: PyRuntimeTypeId>(value: &T, expected_type_id: i64) -> bool {
    py_is_subtype(py_runtime_type_id(value), expected_type_id)
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
    frames: &[Vec<u8>],
    palette: &[u8],
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

fn png_crc32(data: &[u8]) -> u32 {
    let mut crc: u32 = 0xFFFF_FFFF;
    for &b in data {
        crc ^= b as u32;
        for _ in 0..8 {
            if (crc & 1) != 0 {
                crc = (crc >> 1) ^ 0xEDB8_8320;
            } else {
                crc >>= 1;
            }
        }
    }
    !crc
}

fn png_adler32(data: &[u8]) -> u32 {
    const MOD: u32 = 65521;
    let mut s1: u32 = 1;
    let mut s2: u32 = 0;
    for &b in data {
        s1 = (s1 + b as u32) % MOD;
        s2 = (s2 + s1) % MOD;
    }
    (s2 << 16) | s1
}

fn png_chunk(kind: &[u8; 4], data: &[u8]) -> Vec<u8> {
    let mut out = Vec::<u8>::with_capacity(12 + data.len());
    out.extend_from_slice(&(data.len() as u32).to_be_bytes());
    out.extend_from_slice(kind);
    out.extend_from_slice(data);
    let mut crc_input = Vec::<u8>::with_capacity(4 + data.len());
    crc_input.extend_from_slice(kind);
    crc_input.extend_from_slice(data);
    out.extend_from_slice(&png_crc32(&crc_input).to_be_bytes());
    out
}

fn zlib_store_compress(raw: &[u8]) -> Vec<u8> {
    // zlib header: CMF=0x78 (deflate/32KB), FLG=0x01 (fastest, checksum OK)
    let mut out = Vec::<u8>::with_capacity(raw.len() + 64);
    out.push(0x78);
    out.push(0x01);

    let mut pos: usize = 0;
    while pos < raw.len() {
        let remain = raw.len() - pos;
        let block_len = if remain > 65_535 { 65_535 } else { remain };
        let final_block = pos + block_len >= raw.len();
        out.push(if final_block { 0x01 } else { 0x00 }); // BFINAL + BTYPE=00
        let len = block_len as u16;
        let nlen = !len;
        out.extend_from_slice(&len.to_le_bytes());
        out.extend_from_slice(&nlen.to_le_bytes());
        out.extend_from_slice(&raw[pos..(pos + block_len)]);
        pos += block_len;
    }

    out.extend_from_slice(&png_adler32(raw).to_be_bytes());
    out
}

pub fn py_write_rgb_png(path: &str, width: i64, height: i64, pixels: &[u8]) {
    if width <= 0 || height <= 0 {
        panic!("invalid image size");
    }
    let w = width as usize;
    let h = height as usize;
    let expected = w * h * 3;
    if pixels.len() != expected {
        panic!("pixels length mismatch: got={} expected={}", pixels.len(), expected);
    }

    let row_bytes = w * 3;
    let mut scanlines = Vec::<u8>::with_capacity(h * (row_bytes + 1));
    for y in 0..h {
        scanlines.push(0); // filter type 0
        let start = y * row_bytes;
        scanlines.extend_from_slice(&pixels[start..(start + row_bytes)]);
    }

    let mut ihdr = Vec::<u8>::with_capacity(13);
    ihdr.extend_from_slice(&(width as u32).to_be_bytes());
    ihdr.extend_from_slice(&(height as u32).to_be_bytes());
    ihdr.push(8); // bit depth
    ihdr.push(2); // color type: RGB
    ihdr.push(0); // compression
    ihdr.push(0); // filter
    ihdr.push(0); // interlace

    let idat = zlib_store_compress(&scanlines);
    let mut png = Vec::<u8>::new();
    png.extend_from_slice(&[0x89, b'P', b'N', b'G', 0x0D, 0x0A, 0x1A, 0x0A]);
    png.extend_from_slice(&png_chunk(b"IHDR", &ihdr));
    png.extend_from_slice(&png_chunk(b"IDAT", &idat));
    png.extend_from_slice(&png_chunk(b"IEND", &[]));

    let parent = std::path::Path::new(path).parent();
    if let Some(dir) = parent {
        let _ = fs::create_dir_all(dir);
    }
    let mut f = fs::File::create(path).expect("create png file failed");
    f.write_all(&png).expect("write png file failed");
}

pub fn perf_counter() -> f64 {
    static INIT: Once = Once::new();
    static mut START: Option<Instant> = None;
    INIT.call_once(|| unsafe {
        START = Some(Instant::now());
    });
    unsafe { START.as_ref().expect("perf counter start must be initialized").elapsed().as_secs_f64() }
}

pub mod time {
    pub fn perf_counter() -> f64 {
        super::perf_counter()
    }
}

pub mod math {
    pub const pi: f64 = ::std::f64::consts::PI;

    pub trait ToF64 {
        fn to_f64(self) -> f64;
    }
    impl ToF64 for f64 {
        fn to_f64(self) -> f64 {
            self
        }
    }
    impl ToF64 for f32 {
        fn to_f64(self) -> f64 {
            self as f64
        }
    }
    impl ToF64 for i64 {
        fn to_f64(self) -> f64 {
            self as f64
        }
    }
    impl ToF64 for i32 {
        fn to_f64(self) -> f64 {
            self as f64
        }
    }
    impl ToF64 for i16 {
        fn to_f64(self) -> f64 {
            self as f64
        }
    }
    impl ToF64 for i8 {
        fn to_f64(self) -> f64 {
            self as f64
        }
    }
    impl ToF64 for u64 {
        fn to_f64(self) -> f64 {
            self as f64
        }
    }
    impl ToF64 for u32 {
        fn to_f64(self) -> f64 {
            self as f64
        }
    }
    impl ToF64 for u16 {
        fn to_f64(self) -> f64 {
            self as f64
        }
    }
    impl ToF64 for u8 {
        fn to_f64(self) -> f64 {
            self as f64
        }
    }
    impl ToF64 for usize {
        fn to_f64(self) -> f64 {
            self as f64
        }
    }
    impl ToF64 for isize {
        fn to_f64(self) -> f64 {
            self as f64
        }
    }

    pub fn sin<T: ToF64>(v: T) -> f64 {
        v.to_f64().sin()
    }
    pub fn cos<T: ToF64>(v: T) -> f64 {
        v.to_f64().cos()
    }
    pub fn tan<T: ToF64>(v: T) -> f64 {
        v.to_f64().tan()
    }
    pub fn sqrt<T: ToF64>(v: T) -> f64 {
        v.to_f64().sqrt()
    }
    pub fn exp<T: ToF64>(v: T) -> f64 {
        v.to_f64().exp()
    }
    pub fn log<T: ToF64>(v: T) -> f64 {
        v.to_f64().ln()
    }
    pub fn log10<T: ToF64>(v: T) -> f64 {
        v.to_f64().log10()
    }
    pub fn fabs<T: ToF64>(v: T) -> f64 {
        v.to_f64().abs()
    }
    pub fn floor<T: ToF64>(v: T) -> f64 {
        v.to_f64().floor()
    }
    pub fn ceil<T: ToF64>(v: T) -> f64 {
        v.to_f64().ceil()
    }
    pub fn pow(a: f64, b: f64) -> f64 {
        a.powf(b)
    }
}

pub mod pytra {
    pub mod runtime {
        pub mod png {
            pub fn write_rgb_png(path: impl AsRef<str>, width: i64, height: i64, pixels: &[u8]) {
                super::super::super::py_write_rgb_png(path.as_ref(), width, height, pixels);
            }
        }

        pub mod gif {
            pub fn grayscale_palette() -> Vec<u8> {
                super::super::super::py_grayscale_palette()
            }

            pub fn save_gif(
                path: impl AsRef<str>,
                width: i64,
                height: i64,
                frames: &[Vec<u8>],
                palette: &[u8],
                delay_cs: i64,
                loop_count: i64,
            ) {
                super::super::super::py_save_gif(
                    path.as_ref(),
                    width,
                    height,
                    frames,
                    palette,
                    delay_cs,
                    loop_count,
                );
            }
        }
    }

    pub mod utils {
        pub use super::runtime::gif;
        pub use super::runtime::png;
    }
}
