// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/json.py
// generated-by: tools/gen_runtime_from_manifest.py

mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::pytra::std::abi;

fn py_register_generated_type_info() {
    static INIT: ::std::sync::Once = ::std::sync::Once::new();
    INIT.call_once(|| {
        py_register_type_info(0, 0, 0, 0);
        py_register_type_info(1, 3, 3, 3);
        py_register_type_info(2, 2, 2, 3);
        py_register_type_info(3, 4, 4, 4);
        py_register_type_info(4, 5, 5, 5);
        py_register_type_info(5, 6, 6, 6);
        py_register_type_info(6, 7, 7, 7);
        py_register_type_info(7, 8, 8, 8);
        py_register_type_info(8, 1, 1, 12);
        py_register_type_info(1000, 9, 9, 9);
        py_register_type_info(1001, 10, 10, 10);
        py_register_type_info(1002, 11, 11, 11);
        py_register_type_info(1003, 12, 12, 12);
    });
}

fn _is_ws(ch: &str) -> bool {
    return ((ch == " ") || (ch == "\t") || (ch == "\r") || (ch == "\n"));
}

fn _is_digit(ch: &str) -> bool {
    return ((ch >= ("0").to_string()) && (ch <= ("9").to_string()));
}

fn _hex_value(ch: &str) -> i64 {
    if (ch >= ("0").to_string()) && (ch <= ("9").to_string()) {
        return ((ch).parse::<i64>().unwrap_or(0));
    }
    if (ch == "a") || (ch == "A") {
        return 10;
    }
    if (ch == "b") || (ch == "B") {
        return 11;
    }
    if (ch == "c") || (ch == "C") {
        return 12;
    }
    if (ch == "d") || (ch == "D") {
        return 13;
    }
    if (ch == "e") || (ch == "E") {
        return 14;
    }
    if (ch == "f") || (ch == "F") {
        return 15;
    }
    panic!("{}", ("invalid json unicode escape").to_string());
}

fn _int_from_hex4(hx: &str) -> i64 {
    if hx.len() as i64 != 4 {
        panic!("{}", ("invalid json unicode escape").to_string());
    }
    let v0 = _hex_value(&(py_slice_str(&hx, Some((0) as i64), Some((1) as i64))));
    let v1 = _hex_value(&(py_slice_str(&hx, Some((1) as i64), Some((2) as i64))));
    let v2 = _hex_value(&(py_slice_str(&hx, Some((2) as i64), Some((3) as i64))));
    let v3 = _hex_value(&(py_slice_str(&hx, Some((3) as i64), Some((4) as i64))));
    return v0 * 4096 + v1 * 256 + v2 * 16 + v3;
}

fn _hex4(code: i64) -> String {
    let mut v = code % 65536;
    let d3 = v % 16;
    v = v / 16;
    let d2 = v % 16;
    v = v / 16;
    let d1 = v % 16;
    v = v / 16;
    let d0 = v % 16;
    let p0: String = ((py_any_to_string(&_HEX_DIGITS[d0..d0 + 1])).to_string());
    let p1: String = ((py_any_to_string(&_HEX_DIGITS[d1..d1 + 1])).to_string());
    let p2: String = ((py_any_to_string(&_HEX_DIGITS[d2..d2 + 1])).to_string());
    let p3: String = ((py_any_to_string(&_HEX_DIGITS[d3..d3 + 1])).to_string());
    return format!("{}{}{}{}", p0, p1, p2, p3);
}

fn _json_array_items(raw: PyAny) -> Vec<PyAny> {
    return list(raw);
}

fn _json_new_array() -> Vec<PyAny> {
    return list();
}

fn _json_obj_require(raw: &::std::collections::BTreeMap<String, PyAny>, key: &str) -> PyAny {
    for (k, value) in (raw).clone().into_iter() {
        if k == key {
            return value;
        }
    }
    panic!("{}", format!("{}{}", ("json object key not found: ").to_string(), key));
}

fn _json_indent_value(indent: Option<i64>) -> i64 {
    if indent == () {
        panic!("{}", ("json indent is required").to_string());
    }
    let indent_i: i64 = indent;
    return indent_i;
}

#[derive(Clone, Debug)]
struct JsonObj {
    raw: ::std::collections::BTreeMap<String, PyAny>,
}
impl JsonObj {
    const PYTRA_TYPE_ID: i64 = 1001;
    
    fn new(raw: ::std::collections::BTreeMap<String, PyAny>) -> Self {
        Self {
            raw: raw,
        }
    }
    
    fn get(&self, key: &str) -> Option<JsonValue> {
        if !(self.raw.contains_key(&key)) {
            return ();
        }
        let value = _json_obj_require(&(self.raw), key);
        return JsonValue::new(value);
    }
    
    fn get_obj(&self, key: &str) -> Option<JsonObj> {
        if !(self.raw.contains_key(&key)) {
            return ();
        }
        let value = _json_obj_require(&(self.raw), key);
        return JsonValue::new(value).as_obj();
    }
    
    fn get_arr(&self, key: &str) -> Option<JsonArr> {
        if !(self.raw.contains_key(&key)) {
            return ();
        }
        let value = _json_obj_require(&(self.raw), key);
        return JsonValue::new(value).as_arr();
    }
    
    fn get_str(&self, key: &str) -> Option<String> {
        if !(self.raw.contains_key(&key)) {
            return ();
        }
        let value = _json_obj_require(&(self.raw), key);
        return JsonValue::new(value).as_str();
    }
    
    fn get_int(&self, key: &str) -> Option<i64> {
        if !(self.raw.contains_key(&key)) {
            return ();
        }
        let value = _json_obj_require(&(self.raw), key);
        return JsonValue::new(value).as_int();
    }
    
    fn get_float(&self, key: &str) -> Option<f64> {
        if !(self.raw.contains_key(&key)) {
            return ();
        }
        let value = _json_obj_require(&(self.raw), key);
        return JsonValue::new(value).as_float();
    }
    
    fn get_bool(&self, key: &str) -> Option<bool> {
        if !(self.raw.contains_key(&key)) {
            return ();
        }
        let value = _json_obj_require(&(self.raw), key);
        return JsonValue::new(value).as_bool();
    }
}

impl PyRuntimeTypeId for JsonObj {
    fn py_runtime_type_id(&self) -> i64 {
        JsonObj::PYTRA_TYPE_ID
    }
}

#[derive(Clone, Debug)]
struct JsonArr {
    raw: Vec<PyAny>,
}
impl JsonArr {
    const PYTRA_TYPE_ID: i64 = 1000;
    
    fn new(raw: Vec<PyAny>) -> Self {
        Self {
            raw: raw,
        }
    }
    
    fn get(&self, index: i64) -> Option<JsonValue> {
        if (index < 0) || (index >= _json_array_items((self.raw).clone()).len() as i64) {
            return ();
        }
        return JsonValue::new((_json_array_items((self.raw).clone())[((if ((index) as i64) < 0 { (_json_array_items((self.raw).clone()).len() as i64 + ((index) as i64)) } else { ((index) as i64) }) as usize)]).clone());
    }
    
    fn get_obj(&self, index: i64) -> Option<JsonObj> {
        if (index < 0) || (index >= _json_array_items((self.raw).clone()).len() as i64) {
            return ();
        }
        return JsonValue::new((_json_array_items((self.raw).clone())[((if ((index) as i64) < 0 { (_json_array_items((self.raw).clone()).len() as i64 + ((index) as i64)) } else { ((index) as i64) }) as usize)]).clone()).as_obj();
    }
    
    fn get_arr(&self, index: i64) -> Option<JsonArr> {
        if (index < 0) || (index >= _json_array_items((self.raw).clone()).len() as i64) {
            return ();
        }
        return JsonValue::new((_json_array_items((self.raw).clone())[((if ((index) as i64) < 0 { (_json_array_items((self.raw).clone()).len() as i64 + ((index) as i64)) } else { ((index) as i64) }) as usize)]).clone()).as_arr();
    }
    
    fn get_str(&self, index: i64) -> Option<String> {
        if (index < 0) || (index >= _json_array_items((self.raw).clone()).len() as i64) {
            return ();
        }
        return JsonValue::new((_json_array_items((self.raw).clone())[((if ((index) as i64) < 0 { (_json_array_items((self.raw).clone()).len() as i64 + ((index) as i64)) } else { ((index) as i64) }) as usize)]).clone()).as_str();
    }
    
    fn get_int(&self, index: i64) -> Option<i64> {
        if (index < 0) || (index >= _json_array_items((self.raw).clone()).len() as i64) {
            return ();
        }
        return JsonValue::new((_json_array_items((self.raw).clone())[((if ((index) as i64) < 0 { (_json_array_items((self.raw).clone()).len() as i64 + ((index) as i64)) } else { ((index) as i64) }) as usize)]).clone()).as_int();
    }
    
    fn get_float(&self, index: i64) -> Option<f64> {
        if (index < 0) || (index >= _json_array_items((self.raw).clone()).len() as i64) {
            return ();
        }
        return JsonValue::new((_json_array_items((self.raw).clone())[((if ((index) as i64) < 0 { (_json_array_items((self.raw).clone()).len() as i64 + ((index) as i64)) } else { ((index) as i64) }) as usize)]).clone()).as_float();
    }
    
    fn get_bool(&self, index: i64) -> Option<bool> {
        if (index < 0) || (index >= _json_array_items((self.raw).clone()).len() as i64) {
            return ();
        }
        return JsonValue::new((_json_array_items((self.raw).clone())[((if ((index) as i64) < 0 { (_json_array_items((self.raw).clone()).len() as i64 + ((index) as i64)) } else { ((index) as i64) }) as usize)]).clone()).as_bool();
    }
}

impl PyRuntimeTypeId for JsonArr {
    fn py_runtime_type_id(&self) -> i64 {
        JsonArr::PYTRA_TYPE_ID
    }
}

#[derive(Clone, Debug)]
struct JsonValue {
    raw: PyAny,
}
impl JsonValue {
    const PYTRA_TYPE_ID: i64 = 1002;
    
    fn new(raw: PyAny) -> Self {
        Self {
            raw: raw,
        }
    }
    
    fn as_obj(&self) -> Option<JsonObj> {
        let raw = self.raw;
        if { py_register_generated_type_info(); py_runtime_value_isinstance(&raw, PYTRA_TID_DICT) } {
            let raw_obj: ::std::collections::BTreeMap<String, PyAny> = dict(raw);
            return JsonObj::new((raw_obj).clone());
        }
        return ();
    }
    
    fn as_arr(&self) -> Option<JsonArr> {
        let raw = self.raw;
        if { py_register_generated_type_info(); py_runtime_value_isinstance(&raw, PYTRA_TID_LIST) } {
            let raw_arr: Vec<PyAny> = list(raw);
            return JsonArr::new((raw_arr).clone());
        }
        return ();
    }
    
    fn as_str(&self) -> Option<String> {
        let raw = self.raw;
        if { py_register_generated_type_info(); py_runtime_value_isinstance(&raw, PYTRA_TID_STR) } {
            return raw;
        }
        return ();
    }
    
    fn as_int(&self) -> Option<i64> {
        let raw = self.raw;
        if { py_register_generated_type_info(); py_runtime_value_isinstance(&raw, PYTRA_TID_BOOL) } {
            return ();
        }
        if { py_register_generated_type_info(); py_runtime_value_isinstance(&raw, PYTRA_TID_INT) } {
            let raw_i: i64 = py_any_to_i64(&raw);
            return raw_i;
        }
        return ();
    }
    
    fn as_float(&self) -> Option<f64> {
        let raw = self.raw;
        if { py_register_generated_type_info(); py_runtime_value_isinstance(&raw, PYTRA_TID_FLOAT) } {
            let raw_f: f64 = py_any_to_f64(&(raw));
            return raw_f;
        }
        return ();
    }
    
    fn as_bool(&self) -> Option<bool> {
        let raw = self.raw;
        if { py_register_generated_type_info(); py_runtime_value_isinstance(&raw, PYTRA_TID_BOOL) } {
            let raw_b: bool = py_any_to_bool(&raw);
            return raw_b;
        }
        return ();
    }
}

impl PyRuntimeTypeId for JsonValue {
    fn py_runtime_type_id(&self) -> i64 {
        JsonValue::PYTRA_TYPE_ID
    }
}

#[derive(Clone, Debug)]
struct _JsonParser {
    text: String,
    n: i64,
    i: i64,
}
impl _JsonParser {
    const PYTRA_TYPE_ID: i64 = 1003;
    
    fn new(text: String) -> Self {
        Self {
            text: text,
            n: text.len() as i64,
            i: 0,
        }
    }
    
    fn parse(&mut self) -> PyAny {
        self._skip_ws();
        let out = self._parse_value();
        self._skip_ws();
        if self.i != self.n {
            panic!("{}", ("invalid json: trailing characters").to_string());
        }
        return out;
    }
    
    fn _skip_ws(&mut self) {
        while (self.i < self.n) && _is_ws(&(py_str_at(&self.text, ((self.i) as i64)))) {
            self.i += 1;
        }
    }
    
    fn _parse_value(&mut self) -> PyAny {
        if self.i >= self.n {
            panic!("{}", ("invalid json: unexpected end").to_string());
        }
        let ch = py_str_at(&self.text, ((self.i) as i64));
        if ch == "{" {
            return self._parse_object();
        }
        if ch == "[" {
            return self._parse_array();
        }
        if ch == "\"" {
            return self._parse_string();
        }
        if (ch == "t") && (py_slice_str(&self.text, Some((self.i) as i64), Some((self.i + 4) as i64)) == "true") {
            self.i += 4;
            return true;
        }
        if (ch == "f") && (py_slice_str(&self.text, Some((self.i) as i64), Some((self.i + 5) as i64)) == "false") {
            self.i += 5;
            return false;
        }
        if (ch == "n") && (py_slice_str(&self.text, Some((self.i) as i64), Some((self.i + 4) as i64)) == "null") {
            self.i += 4;
            return ();
        }
        return self._parse_number();
    }
    
    fn _parse_object(&mut self) -> ::std::collections::BTreeMap<String, PyAny> {
        let mut out: ::std::collections::HashMap<String, PyAny> = ::std::collections::HashMap::from([]);
        self.i += 1;
        self._skip_ws();
        if (self.i < self.n) && (py_str_at(&self.text, ((self.i) as i64)) == "}") {
            self.i += 1;
            return out;
        }
        while true {
            self._skip_ws();
            if (self.i >= self.n) || (py_str_at(&self.text, ((self.i) as i64)) != "\"") {
                panic!("{}", ("invalid json object key").to_string());
            }
            let key = self._parse_string();
            self._skip_ws();
            if (self.i >= self.n) || (py_str_at(&self.text, ((self.i) as i64)) != ":") {
                panic!("{}", ("invalid json object: missing ':'").to_string());
            }
            self.i += 1;
            self._skip_ws();
            out.insert(((key).to_string()), self._parse_value());
            self._skip_ws();
            if self.i >= self.n {
                panic!("{}", ("invalid json object: unexpected end").to_string());
            }
            let ch = py_str_at(&self.text, ((self.i) as i64));
            self.i += 1;
            if ch == "}" {
                return out;
            }
            if ch != "," {
                panic!("{}", ("invalid json object separator").to_string());
            }
        }
    }
    
    fn _parse_array(&mut self) -> Vec<PyAny> {
        let mut out = _json_new_array();
        self.i += 1;
        self._skip_ws();
        if (self.i < self.n) && (py_str_at(&self.text, ((self.i) as i64)) == "]") {
            self.i += 1;
            return out;
        }
        while true {
            self._skip_ws();
            out.push(self._parse_value());
            self._skip_ws();
            if self.i >= self.n {
                panic!("{}", ("invalid json array: unexpected end").to_string());
            }
            let ch = py_str_at(&self.text, ((self.i) as i64));
            self.i += 1;
            if ch == "]" {
                return out;
            }
            if ch != "," {
                panic!("{}", ("invalid json array separator").to_string());
            }
        }
    }
    
    fn _parse_string(&mut self) -> String {
        if py_str_at(&self.text, ((self.i) as i64)) != "\"" {
            panic!("{}", ("invalid json string").to_string());
        }
        self.i += 1;
        let mut out_chars: Vec<String> = vec![];
        while self.i < self.n {
            let ch = py_str_at(&self.text, ((self.i) as i64));
            self.i += 1;
            if ch == "\"" {
                return _join_strs(&(out_chars), &(_EMPTY));
            }
            if ch == "\\" {
                if self.i >= self.n {
                    panic!("{}", ("invalid json string escape").to_string());
                }
                let esc = py_str_at(&self.text, ((self.i) as i64));
                self.i += 1;
                if esc == "\"" {
                    out_chars.push(("\"").to_string());
                } else if esc == "\\" {
                    out_chars.push(("\\").to_string());
                } else if esc == "/" {
                    out_chars.push(("/").to_string());
                } else if esc == "b" {
                    out_chars.push(("\b").to_string());
                } else if esc == "f" {
                    out_chars.push(("\f").to_string());
                } else if esc == "n" {
                    out_chars.push(("\n").to_string());
                } else if esc == "r" {
                    out_chars.push(("\r").to_string());
                } else if esc == "t" {
                    out_chars.push(("\t").to_string());
                } else if esc == "u" {
                    if self.i + 4 > self.n {
                        panic!("{}", ("invalid json unicode escape").to_string());
                    }
                    let hx = py_slice_str(&self.text, Some((self.i) as i64), Some((self.i + 4) as i64));
                    self.i += 4;
                    out_chars.push(chr(_int_from_hex4(&(hx))));
                } else {
                    panic!("{}", ("invalid json escape").to_string());
                }
            } else {
                out_chars.push(ch);
            }
        }
        panic!("{}", ("unterminated json string").to_string());
    }
    
    fn _parse_number(&mut self) -> PyAny {
        let start = self.i;
        if py_str_at(&self.text, ((self.i) as i64)) == "-" {
            self.i += 1;
        }
        if self.i >= self.n {
            panic!("{}", ("invalid json number").to_string());
        }
        if py_str_at(&self.text, ((self.i) as i64)) == "0" {
            self.i += 1;
        } else {
            if !_is_digit(&(py_str_at(&self.text, ((self.i) as i64)))) {
                panic!("{}", ("invalid json number").to_string());
            }
            while (self.i < self.n) && _is_digit(&(py_str_at(&self.text, ((self.i) as i64)))) {
                self.i += 1;
            }
        }
        let mut is_float = false;
        if (self.i < self.n) && (py_str_at(&self.text, ((self.i) as i64)) == ".") {
            is_float = true;
            self.i += 1;
            if (self.i >= self.n) || !_is_digit(&(py_str_at(&self.text, ((self.i) as i64)))) {
                panic!("{}", ("invalid json number").to_string());
            }
            while (self.i < self.n) && _is_digit(&(py_str_at(&self.text, ((self.i) as i64)))) {
                self.i += 1;
            }
        }
        if self.i < self.n {
            let exp_ch = py_str_at(&self.text, ((self.i) as i64));
            if (exp_ch == "e") || (exp_ch == "E") {
                is_float = true;
                self.i += 1;
                if self.i < self.n {
                    let sign = py_str_at(&self.text, ((self.i) as i64));
                    if (sign == "+") || (sign == "-") {
                        self.i += 1;
                    }
                }
                if (self.i >= self.n) || !_is_digit(&(py_str_at(&self.text, ((self.i) as i64)))) {
                    panic!("{}", ("invalid json exponent").to_string());
                }
                while (self.i < self.n) && _is_digit(&(py_str_at(&self.text, ((self.i) as i64)))) {
                    self.i += 1;
                }
            }
        }
        let token = py_slice_str(&self.text, Some((start) as i64), Some((self.i) as i64));
        if is_float {
            let num_f: f64 = ((token) as f64);
            return num_f;
        }
        let num_i: i64 = ((token).parse::<i64>().unwrap_or(0));
        return num_i;
    }
}

impl PyRuntimeTypeId for _JsonParser {
    fn py_runtime_type_id(&self) -> i64 {
        _JsonParser::PYTRA_TYPE_ID
    }
}

fn loads(text: &str) -> PyAny {
    return _JsonParser::new(text).parse();
}

fn loads_obj(text: &str) -> Option<JsonObj> {
    let value = _JsonParser::new(text).parse();
    if { py_register_generated_type_info(); py_runtime_value_isinstance(&value, PYTRA_TID_DICT) } {
        let raw_obj: ::std::collections::BTreeMap<String, PyAny> = dict(value);
        return JsonObj::new((raw_obj).clone());
    }
    return ();
}

fn loads_arr(text: &str) -> Option<JsonArr> {
    let value = _JsonParser::new(text).parse();
    if { py_register_generated_type_info(); py_runtime_value_isinstance(&value, PYTRA_TID_LIST) } {
        let raw_arr: Vec<PyAny> = list(value);
        return JsonArr::new((raw_arr).clone());
    }
    return ();
}

fn _join_strs(parts: &[String], sep: &str) -> String {
    if parts.len() as i64 == 0 {
        return ("").to_string();
    }
    let mut out: String = (((parts[((0) as usize)]).clone()).to_string());
    let mut i = 1;
    while i < parts.len() as i64 {
        out = format!("{}{}{}", out, sep, (parts[((i) as usize)]).clone());
        i += 1;
    }
    return out;
}

fn _escape_str(s: &str, ensure_ascii: bool) -> String {
    let mut out: Vec<String> = vec![("\"").to_string()];
    for ch in s.chars() {
        let code: i64 = py_any_to_i64(&ord(ch));
        if ch == "\"" {
            out.push(("\\\"").to_string());
        } else if ch == "\\" {
            out.push(("\\\\").to_string());
        } else if ch == "\b" {
            out.push(("\\b").to_string());
        } else if ch == "\f" {
            out.push(("\\f").to_string());
        } else if ch == "\n" {
            out.push(("\\n").to_string());
        } else if ch == "\r" {
            out.push(("\\r").to_string());
        } else if ch == "\t" {
            out.push(("\\t").to_string());
        } else if ensure_ascii && (code > 0x7F) {
            out.push(format!("{}{}", ("\\u").to_string(), _hex4(code)));
        } else {
            out.push(ch);
        }
    }
    out.push(("\"").to_string());
    return _join_strs(&(out), &(_EMPTY));
}

fn _dump_json_list(values: &[PyAny], ensure_ascii: bool, indent: Option<i64>, item_sep: &str, key_sep: &str, level: i64) -> String {
    if values.len() as i64 == 0 {
        return ("[]").to_string();
    }
    if indent == () {
        let mut dumped: Vec<String> = vec![];
        for x in (values).iter().cloned() {
            let dumped_txt: String = ((py_any_to_string(&_dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level))).to_string());
            dumped.push(dumped_txt);
        }
        return format!("{}{}{}", ("[").to_string(), _join_strs(&(dumped), item_sep), ("]").to_string());
    }
    let indent_i: i64 = _json_indent_value(indent);
    let mut inner: Vec<String> = vec![];
    for x in (values).iter().cloned() {
        let prefix: String = ((py_any_to_string(&(" ").to_string() * indent_i * (level + 1))).to_string());
        let value_txt: String = ((py_any_to_string(&_dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level + 1))).to_string());
        inner.push(format!("{}{}", prefix, value_txt));
    }
    return format!("{}{}{}{}{}", ("[\n").to_string(), _join_strs(&(inner), &(_COMMA_NL)), ("\n").to_string(), (" ").to_string() * indent_i * level, ("]").to_string());
}

fn _dump_json_dict(values: &::std::collections::BTreeMap<String, PyAny>, ensure_ascii: bool, indent: Option<i64>, item_sep: &str, key_sep: &str, level: i64) -> String {
    if values.len() as i64 == 0 {
        return ("{}").to_string();
    }
    if indent == () {
        let mut parts: Vec<String> = vec![];
        for (k, x) in (values).clone().into_iter() {
            let mut k_txt: String = ((_escape_str(&(py_any_to_string(&k)), ensure_ascii)).to_string());
            let mut v_txt: String = ((py_any_to_string(&_dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level))).to_string());
            parts.push(format!("{}{}{}", k_txt, key_sep, v_txt));
        }
        return format!("{}{}{}", ("{").to_string(), _join_strs(&(parts), item_sep), ("}").to_string());
    }
    let indent_i: i64 = _json_indent_value(indent);
    let mut inner: Vec<String> = vec![];
    for (k, x) in (values).clone().into_iter() {
        let prefix: String = ((py_any_to_string(&(" ").to_string() * indent_i * (level + 1))).to_string());
        let mut k_txt: String = ((_escape_str(&(py_any_to_string(&k)), ensure_ascii)).to_string());
        let mut v_txt: String = ((py_any_to_string(&_dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level + 1))).to_string());
        inner.push(format!("{}{}{}{}", prefix, k_txt, key_sep, v_txt));
    }
    return format!("{}{}{}{}{}", ("{\n").to_string(), _join_strs(&(inner), &(_COMMA_NL)), ("\n").to_string(), (" ").to_string() * indent_i * level, ("}").to_string());
}

fn _dump_json_value(v: PyAny, ensure_ascii: bool, indent: Option<i64>, item_sep: &str, key_sep: &str, level: i64) -> String {
    if v == () {
        return ("null").to_string();
    }
    if { py_register_generated_type_info(); py_runtime_value_isinstance(&v, PYTRA_TID_BOOL) } {
        let raw_b: bool = py_any_to_bool(&v);
        return (if raw_b { ("true").to_string() } else { ("false").to_string() });
    }
    if { py_register_generated_type_info(); py_runtime_value_isinstance(&v, PYTRA_TID_INT) } {
        return py_any_to_string(&v);
    }
    if { py_register_generated_type_info(); py_runtime_value_isinstance(&v, PYTRA_TID_FLOAT) } {
        return py_any_to_string(&v);
    }
    if { py_register_generated_type_info(); py_runtime_value_isinstance(&v, PYTRA_TID_STR) } {
        return _escape_str(&(v), ensure_ascii);
    }
    if { py_register_generated_type_info(); py_runtime_value_isinstance(&v, PYTRA_TID_LIST) } {
        let as_list: Vec<PyAny> = list(v);
        return _dump_json_list(&(as_list), ensure_ascii, indent, item_sep, key_sep, level);
    }
    if { py_register_generated_type_info(); py_runtime_value_isinstance(&v, PYTRA_TID_DICT) } {
        let as_dict: ::std::collections::HashMap<String, PyAny> = dict(v);
        return _dump_json_dict(&(as_dict), ensure_ascii, indent, item_sep, key_sep, level);
    }
    panic!("{}", ("json.dumps unsupported type").to_string());
}

fn dumps(obj: PyAny, ensure_ascii: bool, indent: Option<i64>, separators: &Option<(String, String)>) -> String {
    let mut item_sep = (",").to_string();
    let mut key_sep = (if indent == () { (":").to_string() } else { (": ").to_string() });
    if separators != () {
        let __tmp_1 = separators;
        item_sep = __tmp_1.0;
        key_sep = __tmp_1.1;
    }
    return _dump_json_value(obj, ensure_ascii, indent, &(item_sep), &(key_sep), 0);
}

fn main() {
    py_register_generated_type_info();
    ("Pure Python JSON utilities for selfhost-friendly transpilation.").to_string();
    let _EMPTY: String = ("").to_string();
    let _COMMA_NL: String = (",\n").to_string();
    let _HEX_DIGITS: String = ("0123456789abcdef").to_string();
}
