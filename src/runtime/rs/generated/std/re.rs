// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/re.py
// generated-by: tools/gen_runtime_from_manifest.py

mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

#[derive(Clone, Debug)]
struct Match {
    _text: String,
    _groups: Vec<String>,
}
impl Match {
    fn new(text: String, groups: Vec<String>) -> Self {
        Self {
            _text: text,
            _groups: groups,
        }
    }
    
    fn group(&self, idx: i64) -> String {
        if idx == 0 {
            return self._text;
        }
        if (idx < 0) || (idx > self._groups.len() as i64) {
            panic!("{}", ("group index out of range").to_string());
        }
        return (self._groups[((if ((idx - 1) as i64) < 0 { (self._groups.len() as i64 + ((idx - 1) as i64)) } else { ((idx - 1) as i64) }) as usize)]).clone();
    }
}


fn group(m: Option<Match>, idx: i64) -> String {
    if m == () {
        return ("").to_string();
    }
    let mm: Match = m;
    return mm.group(idx);
}

fn strip_group(m: Option<Match>, idx: i64) -> String {
    return group(m, idx).strip();
}

fn _is_ident(s: &str) -> bool {
    if s == "" {
        return false;
    }
    let h = py_slice_str(&s, Some((0) as i64), Some((1) as i64));
    let is_head_alpha = (((("a").to_string() <= h) && (h <= ("z").to_string())) || ((("A").to_string() <= h) && (h <= ("Z").to_string())));
    if !((is_head_alpha || (h == "_"))) {
        return false;
    }
    for ch in py_slice_str(&s, Some((1) as i64), None).chars() {
        let is_alpha = (((("a").to_string() <= ch) && (ch <= ("z").to_string())) || ((("A").to_string() <= ch) && (ch <= ("Z").to_string())));
        let is_digit = ((("0").to_string() <= ch) && (ch <= ("9").to_string()));
        if !((is_alpha || is_digit || (ch == "_"))) {
            return false;
        }
    }
    return true;
}

fn _is_dotted_ident(s: &str) -> bool {
    if s == "" {
        return false;
    }
    let mut part = ("").to_string();
    for ch in s.chars() {
        if ch == "." {
            if !_is_ident(&(part)) {
                return false;
            }
            part = ("").to_string();
            continue;
        }
        part += ch;
    }
    if !_is_ident(&(part)) {
        return false;
    }
    if part == "" {
        return false;
    }
    return true;
}

fn _strip_suffix_colon(s: &str) -> String {
    let t = s.rstrip();
    if t.len() as i64 == 0 {
        return ("").to_string();
    }
    if py_slice_str(&t, Some((-1) as i64), None) != ":" {
        return ("").to_string();
    }
    return py_slice_str(&t, None, Some((-1) as i64));
}

fn _is_space_ch(ch: &str) -> bool {
    if ch == " " {
        return true;
    }
    if ch == "\t" {
        return true;
    }
    if ch == "\r" {
        return true;
    }
    if ch == "\n" {
        return true;
    }
    return false;
}

fn _is_alnum_or_underscore(ch: &str) -> bool {
    let is_alpha = (((("a").to_string() <= ch) && (ch <= ("z").to_string())) || ((("A").to_string() <= ch) && (ch <= ("Z").to_string())));
    let is_digit = ((("0").to_string() <= ch) && (ch <= ("9").to_string()));
    if is_alpha || is_digit {
        return true;
    }
    return (ch == "_");
}

fn _skip_spaces(t: &str, mut i: i64) -> i64 {
    while i < t.len() as i64 {
        if !_is_space_ch(&(py_slice_str(&t, Some((i) as i64), Some((i + 1) as i64)))) {
            return i;
        }
        i += 1;
    }
    return i;
}

fn py_match(pattern: &str, text: &str, flags: i64) -> Option<Match> {
    // ^([A-Za-z_][A-Za-z0-9_]*)\[(.*)\]$
    if pattern == "^([A-Za-z_][A-Za-z0-9_]*)\\[(.*)\\]$" {
        if !text.endswith(("]").to_string()) {
            return ();
        }
        let mut i = text.find(("[").to_string());
        if i <= 0 {
            return ();
        }
        let head = py_slice_str(&text, None, Some((i) as i64));
        if !_is_ident(&(head)) {
            return ();
        }
        return Match::new(((text).to_string()), (vec![head, py_slice_str(&text, Some((i + 1) as i64), Some((-1) as i64))]).clone());
    }
    if pattern == "^def\\s+([A-Za-z_][A-Za-z0-9_]*)\\((.*)\\)\\s*(?:->\\s*(.+)\\s*)?:\\s*$" {
        let mut t = _strip_suffix_colon(text);
        if t == "" {
            return ();
        }
        let mut i = 0;
        if !t.startswith(("def").to_string()) {
            return ();
        }
        i = 3;
        if (i >= t.len() as i64) || !_is_space_ch(&(py_slice_str(&t, Some((i) as i64), Some((i + 1) as i64)))) {
            return ();
        }
        i = _skip_spaces(&(t), i);
        let mut j = i;
        while (j < t.len() as i64) && _is_alnum_or_underscore(&(py_slice_str(&t, Some((j) as i64), Some((j + 1) as i64)))) {
            j += 1;
        }
        let mut name: String = ((py_slice_str(&t, Some((i) as i64), Some((j) as i64))).to_string());
        if !_is_ident(&(name)) {
            return ();
        }
        let mut k = j;
        k = _skip_spaces(&(t), k);
        if (k >= t.len() as i64) || (py_slice_str(&t, Some((k) as i64), Some((k + 1) as i64)) != "(") {
            return ();
        }
        let r: i64 = py_any_to_i64(&t.rfind((")").to_string()));
        if r <= k {
            return ();
        }
        let args: String = ((py_slice_str(&t, Some((k + 1) as i64), Some((r) as i64))).to_string());
        let mut tail: String = ((py_slice_str(&t, Some((r + 1) as i64), None).strip()).to_string());
        if tail == "" {
            return Match::new(((text).to_string()), (vec![name, args, ("").to_string()]).clone());
        }
        if !tail.startswith(("->").to_string()) {
            return ();
        }
        let ret: String = ((py_slice_str(&tail, Some((2) as i64), None).strip()).to_string());
        if ret == "" {
            return ();
        }
        return Match::new(((text).to_string()), (vec![name, args, ret]).clone());
    }
    if pattern == "^([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*([^=]+?)(?:\\s*=\\s*(.+))?$" {
        let mut c = text.find((":").to_string());
        if c <= 0 {
            return ();
        }
        let mut name = py_slice_str(&text, None, Some((c) as i64)).strip();
        if !_is_ident(&(name)) {
            return ();
        }
        let mut rhs = py_slice_str(&text, Some((c + 1) as i64), None);
        let mut eq = rhs.find(("=").to_string());
        if eq < 0 {
            let mut ann = rhs.strip();
            if ann == "" {
                return ();
            }
            return Match::new(((text).to_string()), (vec![name, ann, ("").to_string()]).clone());
        }
        let mut ann = py_slice_str(&rhs, None, Some((eq) as i64)).strip();
        let val = py_slice_str(&rhs, Some((eq + 1) as i64), None).strip();
        if (ann == "") || (val == "") {
            return ();
        }
        return Match::new(((text).to_string()), (vec![name, ann, val]).clone());
    }
    if pattern == "^[A-Za-z_][A-Za-z0-9_]*$" {
        if _is_ident(text) {
            return Match::new(((text).to_string()), (vec![]).clone());
        }
        return ();
    }
    if pattern == "^class\\s+([A-Za-z_][A-Za-z0-9_]*)(?:\\(([A-Za-z_][A-Za-z0-9_]*)\\))?\\s*:\\s*$" {
        let mut t = _strip_suffix_colon(text);
        if t == "" {
            return ();
        }
        if !t.startswith(("class").to_string()) {
            return ();
        }
        let mut i = 5;
        if (i >= t.len() as i64) || !_is_space_ch(&(py_slice_str(&t, Some((i) as i64), Some((i + 1) as i64)))) {
            return ();
        }
        i = _skip_spaces(&(t), i);
        let mut j = i;
        while (j < t.len() as i64) && _is_alnum_or_underscore(&(py_slice_str(&t, Some((j) as i64), Some((j + 1) as i64)))) {
            j += 1;
        }
        let mut name: String = ((py_slice_str(&t, Some((i) as i64), Some((j) as i64))).to_string());
        if !_is_ident(&(name)) {
            return ();
        }
        let mut tail: String = ((py_slice_str(&t, Some((j) as i64), None).strip()).to_string());
        if tail == "" {
            return Match::new(((text).to_string()), (vec![name, ("").to_string()]).clone());
        }
        if !((tail.startswith(("(").to_string()) && tail.endswith((")").to_string()))) {
            return ();
        }
        let base: String = ((py_slice_str(&tail, Some((1) as i64), Some((-1) as i64)).strip()).to_string());
        if !_is_ident(&(base)) {
            return ();
        }
        return Match::new(((text).to_string()), (vec![name, base]).clone());
    }
    if pattern == "^(any|all)\\((.+)\\)$" {
        if text.startswith(("any(").to_string()) && text.endswith((")").to_string()) && (text.len() as i64 > 5) {
            return Match::new(((text).to_string()), (vec![("any").to_string(), py_slice_str(&text, Some((4) as i64), Some((-1) as i64))]).clone());
        }
        if text.startswith(("all(").to_string()) && text.endswith((")").to_string()) && (text.len() as i64 > 5) {
            return Match::new(((text).to_string()), (vec![("all").to_string(), py_slice_str(&text, Some((4) as i64), Some((-1) as i64))]).clone());
        }
        return ();
    }
    if pattern == "^\\[\\s*([A-Za-z_][A-Za-z0-9_]*)\\s+for\\s+([A-Za-z_][A-Za-z0-9_]*)\\s+in\\s+(.+)\\]$" {
        if !((text.startswith(("[").to_string()) && text.endswith(("]").to_string()))) {
            return ();
        }
        let inner: String = ((py_slice_str(&text, Some((1) as i64), Some((-1) as i64)).strip()).to_string());
        let m1 = (" for ").to_string();
        let m2 = (" in ").to_string();
        let mut i: i64 = py_any_to_i64(&inner.find(m1));
        if i < 0 {
            return ();
        }
        let mut expr: String = ((py_slice_str(&inner, None, Some((i) as i64)).strip()).to_string());
        let mut rest: String = ((py_slice_str(&inner, Some((i + m1.len() as i64) as i64), None)).to_string());
        let mut j: i64 = py_any_to_i64(&rest.find(m2));
        if j < 0 {
            return ();
        }
        let var: String = ((py_slice_str(&rest, None, Some((j) as i64)).strip()).to_string());
        let it: String = ((py_slice_str(&rest, Some((j + m2.len() as i64) as i64), None).strip()).to_string());
        if !_is_ident(&(expr)) || !_is_ident(&(var)) || (it == "") {
            return ();
        }
        return Match::new(((text).to_string()), (vec![expr, var, it]).clone());
    }
    if pattern == "^for\\s+(.+)\\s+in\\s+(.+):$" {
        let mut t = _strip_suffix_colon(text);
        if (t == "") || !t.startswith(("for").to_string()) {
            return ();
        }
        let mut rest: String = ((py_slice_str(&t, Some((3) as i64), None).strip()).to_string());
        let mut i: i64 = py_any_to_i64(&rest.find((" in ").to_string()));
        if i < 0 {
            return ();
        }
        let mut left: String = ((py_slice_str(&rest, None, Some((i) as i64)).strip()).to_string());
        let mut right: String = ((py_slice_str(&rest, Some((i + 4) as i64), None).strip()).to_string());
        if (left == "") || (right == "") {
            return ();
        }
        return Match::new(((text).to_string()), (vec![left, right]).clone());
    }
    if pattern == "^with\\s+(.+)\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*$" {
        let mut t = _strip_suffix_colon(text);
        if (t == "") || !t.startswith(("with").to_string()) {
            return ();
        }
        let mut rest: String = ((py_slice_str(&t, Some((4) as i64), None).strip()).to_string());
        let mut i: i64 = py_any_to_i64(&rest.rfind((" as ").to_string()));
        if i < 0 {
            return ();
        }
        let mut expr: String = ((py_slice_str(&rest, None, Some((i) as i64)).strip()).to_string());
        let mut name: String = ((py_slice_str(&rest, Some((i + 4) as i64), None).strip()).to_string());
        if (expr == "") || !_is_ident(&(name)) {
            return ();
        }
        return Match::new(((text).to_string()), (vec![expr, name]).clone());
    }
    if pattern == "^except\\s+(.+?)\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*$" {
        let mut t = _strip_suffix_colon(text);
        if (t == "") || !t.startswith(("except").to_string()) {
            return ();
        }
        let mut rest: String = ((py_slice_str(&t, Some((6) as i64), None).strip()).to_string());
        let mut i: i64 = py_any_to_i64(&rest.rfind((" as ").to_string()));
        if i < 0 {
            return ();
        }
        let exc: String = ((py_slice_str(&rest, None, Some((i) as i64)).strip()).to_string());
        let mut name: String = ((py_slice_str(&rest, Some((i + 4) as i64), None).strip()).to_string());
        if (exc == "") || !_is_ident(&(name)) {
            return ();
        }
        return Match::new(((text).to_string()), (vec![exc, name]).clone());
    }
    if pattern == "^except\\s+(.+?)\\s*:\\s*$" {
        let mut t = _strip_suffix_colon(text);
        if (t == "") || !t.startswith(("except").to_string()) {
            return ();
        }
        let mut rest: String = ((py_slice_str(&t, Some((6) as i64), None).strip()).to_string());
        if rest == "" {
            return ();
        }
        return Match::new(((text).to_string()), (vec![rest]).clone());
    }
    if pattern == "^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*:\\s*(.+)$" {
        let mut c = text.find((":").to_string());
        if c <= 0 {
            return ();
        }
        let mut target: String = ((py_slice_str(&text, None, Some((c) as i64)).strip()).to_string());
        let mut ann: String = ((py_slice_str(&text, Some((c + 1) as i64), None).strip()).to_string());
        if (ann == "") || !_is_dotted_ident(&(target)) {
            return ();
        }
        return Match::new(((text).to_string()), (vec![target, ann]).clone());
    }
    if pattern == "^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*:\\s*([^=]+?)\\s*=\\s*(.+)$" {
        let mut c = text.find((":").to_string());
        if c <= 0 {
            return ();
        }
        let mut target: String = ((py_slice_str(&text, None, Some((c) as i64)).strip()).to_string());
        let mut rhs: String = ((py_slice_str(&text, Some((c + 1) as i64), None)).to_string());
        let mut eq: i64 = py_any_to_i64(&rhs.find(("=").to_string()));
        if eq < 0 {
            return ();
        }
        let mut ann: String = ((py_slice_str(&rhs, None, Some((eq) as i64)).strip()).to_string());
        let mut expr: String = ((py_slice_str(&rhs, Some((eq + 1) as i64), None).strip()).to_string());
        if !_is_dotted_ident(&(target)) || (ann == "") || (expr == "") {
            return ();
        }
        return Match::new(((text).to_string()), (vec![target, ann, expr]).clone());
    }
    if pattern == "^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*(\\+=|-=|\\*=|/=|//=|%=|&=|\\|=|\\^=|<<=|>>=)\\s*(.+)$" {
        let ops = vec![("<<=").to_string(), (">>=").to_string(), ("+=").to_string(), ("-=").to_string(), ("*=").to_string(), ("/=").to_string(), ("//=").to_string(), ("%=").to_string(), ("&=").to_string(), ("|=").to_string(), ("^=").to_string()];
        let mut op_pos = -1;
        let mut op_txt = ("").to_string();
        for op in (ops).iter().cloned() {
            let p = text.find(op);
            if (p >= 0) && ((op_pos < 0) || (p < op_pos)) {
                op_pos = py_any_to_i64(&p);
                op_txt = op;
            }
        }
        if op_pos < 0 {
            return ();
        }
        let mut left: String = ((py_slice_str(&text, None, Some((op_pos) as i64)).strip()).to_string());
        let mut right: String = ((py_slice_str(&text, Some((op_pos + op_txt.len() as i64) as i64), None).strip()).to_string());
        if (right == "") || !_is_dotted_ident(&(left)) {
            return ();
        }
        return Match::new(((text).to_string()), (vec![left, op_txt, right]).clone());
    }
    if pattern == "^([A-Za-z_][A-Za-z0-9_]*)\\s*,\\s*([A-Za-z_][A-Za-z0-9_]*)\\s*=\\s*(.+)$" {
        let mut eq: i64 = py_any_to_i64(&text.find(("=").to_string()));
        if eq < 0 {
            return ();
        }
        let mut left: String = ((py_slice_str(&text, None, Some((eq) as i64))).to_string());
        let mut right: String = ((py_slice_str(&text, Some((eq + 1) as i64), None).strip()).to_string());
        if right == "" {
            return ();
        }
        let mut c: i64 = py_any_to_i64(&left.find((",").to_string()));
        if c < 0 {
            return ();
        }
        let a: String = ((py_slice_str(&left, None, Some((c) as i64)).strip()).to_string());
        let b: String = ((py_slice_str(&left, Some((c + 1) as i64), None).strip()).to_string());
        if !_is_ident(&(a)) || !_is_ident(&(b)) {
            return ();
        }
        return Match::new(((text).to_string()), (vec![a, b, right]).clone());
    }
    if pattern == "^if\\s+__name__\\s*==\\s*[\\\"']__main__[\\\"']\\s*:\\s*$" {
        let mut t = _strip_suffix_colon(text);
        if t == "" {
            return ();
        }
        let mut rest: String = ((t.strip()).to_string());
        if !rest.startswith(("if").to_string()) {
            return ();
        }
        rest = py_slice_str(&rest, Some((2) as i64), None).strip();
        if !rest.startswith(("__name__").to_string()) {
            return ();
        }
        rest = py_slice_str(&rest, Some((("__name__").to_string().len() as i64) as i64), None).strip();
        if !rest.startswith(("==").to_string()) {
            return ();
        }
        rest = py_slice_str(&rest, Some((2) as i64), None).strip();
        if (rest == "\"__main__\"") || (rest == "'__main__'") {
            return Match::new(((text).to_string()), (vec![]).clone());
        }
        return ();
    }
    if pattern == "^import\\s+(.+)$" {
        if !text.startswith(("import").to_string()) {
            return ();
        }
        if text.len() as i64 <= 6 {
            return ();
        }
        if !_is_space_ch(&(py_slice_str(&text, Some((6) as i64), Some((7) as i64)))) {
            return ();
        }
        let mut rest: String = ((py_slice_str(&text, Some((7) as i64), None).strip()).to_string());
        if rest == "" {
            return ();
        }
        return Match::new(((text).to_string()), (vec![rest]).clone());
    }
    if pattern == "^([A-Za-z_][A-Za-z0-9_\\.]*)(?:\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*))?$" {
        let mut parts: Vec<String> = text.split((" as ").to_string());
        if parts.len() as i64 == 1 {
            let mut name: String = (((parts[((0) as usize)]).clone().strip()).to_string());
            if !_is_dotted_ident(&(name)) {
                return ();
            }
            return Match::new(((text).to_string()), (vec![name, ("").to_string()]).clone());
        }
        if parts.len() as i64 == 2 {
            let mut name: String = (((parts[((0) as usize)]).clone().strip()).to_string());
            let mut alias: String = (((parts[((1) as usize)]).clone().strip()).to_string());
            if !_is_dotted_ident(&(name)) || !_is_ident(&(alias)) {
                return ();
            }
            return Match::new(((text).to_string()), (vec![name, alias]).clone());
        }
        return ();
    }
    if pattern == "^from\\s+([A-Za-z_][A-Za-z0-9_\\.]*)\\s+import\\s+(.+)$" {
        if !text.startswith(("from ").to_string()) {
            return ();
        }
        let mut rest: String = ((py_slice_str(&text, Some((5) as i64), None)).to_string());
        let mut i: i64 = py_any_to_i64(&rest.find((" import ").to_string()));
        if i < 0 {
            return ();
        }
        let py_mod: String = ((py_slice_str(&rest, None, Some((i) as i64)).strip()).to_string());
        let sym: String = ((py_slice_str(&rest, Some((i + 8) as i64), None).strip()).to_string());
        if !_is_dotted_ident(&(py_mod)) || (sym == "") {
            return ();
        }
        return Match::new(((text).to_string()), (vec![py_mod, sym]).clone());
    }
    if pattern == "^([A-Za-z_][A-Za-z0-9_]*)(?:\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*))?$" {
        let mut parts: Vec<String> = text.split((" as ").to_string());
        if parts.len() as i64 == 1 {
            let mut name: String = (((parts[((0) as usize)]).clone().strip()).to_string());
            if !_is_ident(&(name)) {
                return ();
            }
            return Match::new(((text).to_string()), (vec![name, ("").to_string()]).clone());
        }
        if parts.len() as i64 == 2 {
            let mut name: String = (((parts[((0) as usize)]).clone().strip()).to_string());
            let mut alias: String = (((parts[((1) as usize)]).clone().strip()).to_string());
            if !_is_ident(&(name)) || !_is_ident(&(alias)) {
                return ();
            }
            return Match::new(((text).to_string()), (vec![name, alias]).clone());
        }
        return ();
    }
    if pattern == "^([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*([^=]+?)\\s*=\\s*(.+)$" {
        let mut c = text.find((":").to_string());
        if c <= 0 {
            return ();
        }
        let mut name: String = ((py_slice_str(&text, None, Some((c) as i64)).strip()).to_string());
        let mut rhs: String = ((py_slice_str(&text, Some((c + 1) as i64), None)).to_string());
        let mut eq: i64 = py_any_to_i64(&rhs.find(("=").to_string()));
        if eq < 0 {
            return ();
        }
        let mut ann: String = ((py_slice_str(&rhs, None, Some((eq) as i64)).strip()).to_string());
        let mut expr: String = ((py_slice_str(&rhs, Some((eq + 1) as i64), None).strip()).to_string());
        if !_is_ident(&(name)) || (ann == "") || (expr == "") {
            return ();
        }
        return Match::new(((text).to_string()), (vec![name, ann, expr]).clone());
    }
    if pattern == "^([A-Za-z_][A-Za-z0-9_]*)\\s*=\\s*(.+)$" {
        let mut eq: i64 = py_any_to_i64(&text.find(("=").to_string()));
        if eq < 0 {
            return ();
        }
        let mut name: String = ((py_slice_str(&text, None, Some((eq) as i64)).strip()).to_string());
        let mut expr: String = ((py_slice_str(&text, Some((eq + 1) as i64), None).strip()).to_string());
        if !_is_ident(&(name)) || (expr == "") {
            return ();
        }
        return Match::new(((text).to_string()), (vec![name, expr]).clone());
    }
    panic!("{}", f"unsupported regex pattern in pytra.std.re: {pattern}");
}

fn sub(pattern: &str, repl: &str, text: &str, flags: i64) -> String {
    if pattern == "\\s+" {
        let mut out: Vec<String> = vec![];
        let mut in_ws = false;
        for ch in text.chars() {
            if ch.isspace() {
                if !in_ws {
                    out.push(repl);
                    in_ws = true;
                }
            } else {
                out.push(ch);
                in_ws = false;
            }
        }
        return ("").to_string().join(out);
    }
    if pattern == "\\s+#.*$" {
        let mut i = 0;
        while i < text.len() as i64 {
            if py_str_at_nonneg(&text, ((i) as usize)).isspace() {
                let mut j = i + 1;
                while (j < text.len() as i64) && py_str_at_nonneg(&text, ((j) as usize)).isspace() {
                    j += 1;
                }
                if (j < text.len() as i64) && (py_str_at(&text, ((j) as i64)) == "#") {
                    return format!("{}{}", py_slice_str(&text, None, Some((i) as i64)), repl);
                }
            }
            i += 1;
        }
        return text;
    }
    if pattern == "[^0-9A-Za-z_]" {
        let mut out: Vec<String> = vec![];
        for ch in text.chars() {
            if ch.isalnum() || (ch == "_") {
                out.push(ch);
            } else {
                out.push(repl);
            }
        }
        return ("").to_string().join(out);
    }
    panic!("{}", f"unsupported regex sub pattern in pytra.std.re: {pattern}");
}

fn main() {
    ("Minimal pure-Python regex subset used by Pytra selfhost path.").to_string();
    let S = 1;
}
