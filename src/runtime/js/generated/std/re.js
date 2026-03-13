// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/re.py
// generated-by: tools/gen_runtime_from_manifest.py

import { PYTRA_TYPE_ID, PY_TYPE_OBJECT, pyRegisterClassType } from "./pytra/py_runtime.js";

class Match {
    static PYTRA_TYPE_ID = pyRegisterClassType([PY_TYPE_OBJECT]);
    
    constructor(text, groups) {
        this._text = text;
        this._groups = groups;
    this[PYTRA_TYPE_ID] = Match.PYTRA_TYPE_ID;
    }
    
    group(idx) {
        if (idx === 0) {
            return this._text;
        }
        if (idx < 0 || idx > (this._groups).length) {
            throw new Error("group index out of range");
        }
        return this._groups[(((idx - 1) < 0) ? ((this._groups).length + (idx - 1)) : (idx - 1))];
    }
}

function group(m, idx) {
    if (m === null) {
        return "";
    }
    let mm = m;
    return mm.group(idx);
}

function strip_group(m, idx) {
    return group(m, idx).strip();
}

function _is_ident(s) {
    if (s === "") {
        return false;
    }
    let h = s.slice(0, 1);
    let is_head_alpha = "a" <= h && h <= "z" || "A" <= h && h <= "Z";
    if (!(is_head_alpha || h === "_")) {
        return false;
    }
    for (const ch of s.slice(1)) {
        let is_alpha = "a" <= ch && ch <= "z" || "A" <= ch && ch <= "Z";
        let is_digit = "0" <= ch && ch <= "9";
        if (!(is_alpha || is_digit || ch === "_")) {
            return false;
        }
    }
    return true;
}

function _is_dotted_ident(s) {
    if (s === "") {
        return false;
    }
    let part = "";
    for (const ch of s) {
        if (ch === ".") {
            if (!_is_ident(part)) {
                return false;
            }
            part = "";
            continue;
        }
        part += ch;
    }
    if (!_is_ident(part)) {
        return false;
    }
    if (part === "") {
        return false;
    }
    return true;
}

function _strip_suffix_colon(s) {
    let t = s.rstrip();
    if ((t).length === 0) {
        return "";
    }
    if (t.slice(-1) !== ":") {
        return "";
    }
    return t.slice(0, -1);
}

function _is_space_ch(ch) {
    if (ch === " ") {
        return true;
    }
    if (ch === "\t") {
        return true;
    }
    if (ch === "\r") {
        return true;
    }
    if (ch === "\n") {
        return true;
    }
    return false;
}

function _is_alnum_or_underscore(ch) {
    let is_alpha = "a" <= ch && ch <= "z" || "A" <= ch && ch <= "Z";
    let is_digit = "0" <= ch && ch <= "9";
    if (is_alpha || is_digit) {
        return true;
    }
    return ch === "_";
}

function _skip_spaces(t, i) {
    while (i < (t).length) {
        if (!_is_space_ch(t.slice(i, i + 1))) {
            return i;
        }
        i += 1;
    }
    return i;
}

function match(pattern, text, flags) {
    // ^([A-Za-z_][A-Za-z0-9_]*)\[(.*)\]$
    if (pattern === "^([A-Za-z_][A-Za-z0-9_]*)\\[(.*)\\]$") {
        if (!text.endswith("]")) {
            return null;
        }
        let i = text.find("[");
        if (i <= 0) {
            return null;
        }
        let head = text.slice(0, i);
        if (!_is_ident(head)) {
            return null;
        }
        return new Match(text, [head, text.slice(i + 1, -1)]);
    }
    if (pattern === "^def\\s+([A-Za-z_][A-Za-z0-9_]*)\\((.*)\\)\\s*(?:->\\s*(.+)\\s*)?:\\s*$") {
        let t = _strip_suffix_colon(text);
        if (t === "") {
            return null;
        }
        let i = 0;
        if (!t.startswith("def")) {
            return null;
        }
        i = 3;
        if (i >= (t).length || !_is_space_ch(t.slice(i, i + 1))) {
            return null;
        }
        i = _skip_spaces(t, i);
        let j = i;
        while (j < (t).length && _is_alnum_or_underscore(t.slice(j, j + 1))) {
            j += 1;
        }
        let name = t.slice(i, j);
        if (!_is_ident(name)) {
            return null;
        }
        let k = j;
        k = _skip_spaces(t, k);
        if (k >= (t).length || t.slice(k, k + 1) !== "(") {
            return null;
        }
        let r = t.rfind(")");
        if (r <= k) {
            return null;
        }
        let args = t.slice(k + 1, r);
        let tail = t.slice(r + 1).strip();
        if (tail === "") {
            return new Match(text, [name, args, ""]);
        }
        if (!tail.startswith("->")) {
            return null;
        }
        let ret = tail.slice(2).strip();
        if (ret === "") {
            return null;
        }
        return new Match(text, [name, args, ret]);
    }
    if (pattern === "^([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*([^=]+?)(?:\\s*=\\s*(.+))?$") {
        let c = text.find(":");
        if (c <= 0) {
            return null;
        }
        let name = text.slice(0, c).strip();
        if (!_is_ident(name)) {
            return null;
        }
        let rhs = text.slice(c + 1);
        let eq = rhs.find("=");
        if (eq < 0) {
            let ann = rhs.strip();
            if (ann === "") {
                return null;
            }
            return new Match(text, [name, ann, ""]);
        }
        let ann = rhs.slice(0, eq).strip();
        let val = rhs.slice(eq + 1).strip();
        if (ann === "" || val === "") {
            return null;
        }
        return new Match(text, [name, ann, val]);
    }
    if (pattern === "^[A-Za-z_][A-Za-z0-9_]*$") {
        if (_is_ident(text)) {
            return new Match(text, []);
        }
        return null;
    }
    if (pattern === "^class\\s+([A-Za-z_][A-Za-z0-9_]*)(?:\\(([A-Za-z_][A-Za-z0-9_]*)\\))?\\s*:\\s*$") {
        let t = _strip_suffix_colon(text);
        if (t === "") {
            return null;
        }
        if (!t.startswith("class")) {
            return null;
        }
        let i = 5;
        if (i >= (t).length || !_is_space_ch(t.slice(i, i + 1))) {
            return null;
        }
        i = _skip_spaces(t, i);
        let j = i;
        while (j < (t).length && _is_alnum_or_underscore(t.slice(j, j + 1))) {
            j += 1;
        }
        let name = t.slice(i, j);
        if (!_is_ident(name)) {
            return null;
        }
        let tail = t.slice(j).strip();
        if (tail === "") {
            return new Match(text, [name, ""]);
        }
        if (!(tail.startswith("(") && tail.endswith(")"))) {
            return null;
        }
        let base = tail.slice(1, -1).strip();
        if (!_is_ident(base)) {
            return null;
        }
        return new Match(text, [name, base]);
    }
    if (pattern === "^(any|all)\\((.+)\\)$") {
        if (text.startswith("any(") && text.endswith(")") && (text).length > 5) {
            return new Match(text, ["any", text.slice(4, -1)]);
        }
        if (text.startswith("all(") && text.endswith(")") && (text).length > 5) {
            return new Match(text, ["all", text.slice(4, -1)]);
        }
        return null;
    }
    if (pattern === "^\\[\\s*([A-Za-z_][A-Za-z0-9_]*)\\s+for\\s+([A-Za-z_][A-Za-z0-9_]*)\\s+in\\s+(.+)\\]$") {
        if (!(text.startswith("[") && text.endswith("]"))) {
            return null;
        }
        let inner = text.slice(1, -1).strip();
        let m1 = " for ";
        let m2 = " in ";
        let i = inner.find(m1);
        if (i < 0) {
            return null;
        }
        let expr = inner.slice(0, i).strip();
        let rest = inner.slice(i + (m1).length);
        let j = rest.find(m2);
        if (j < 0) {
            return null;
        }
        let py_var = rest.slice(0, j).strip();
        let it = rest.slice(j + (m2).length).strip();
        if (!_is_ident(expr) || !_is_ident(py_var) || it === "") {
            return null;
        }
        return new Match(text, [expr, py_var, it]);
    }
    if (pattern === "^for\\s+(.+)\\s+in\\s+(.+):$") {
        let t = _strip_suffix_colon(text);
        if (t === "" || !t.startswith("for")) {
            return null;
        }
        let rest = t.slice(3).strip();
        let i = rest.find(" in ");
        if (i < 0) {
            return null;
        }
        let left = rest.slice(0, i).strip();
        let right = rest.slice(i + 4).strip();
        if (left === "" || right === "") {
            return null;
        }
        return new Match(text, [left, right]);
    }
    if (pattern === "^with\\s+(.+)\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*$") {
        let t = _strip_suffix_colon(text);
        if (t === "" || !t.startswith("with")) {
            return null;
        }
        let rest = t.slice(4).strip();
        let i = rest.rfind(" as ");
        if (i < 0) {
            return null;
        }
        let expr = rest.slice(0, i).strip();
        let name = rest.slice(i + 4).strip();
        if (expr === "" || !_is_ident(name)) {
            return null;
        }
        return new Match(text, [expr, name]);
    }
    if (pattern === "^except\\s+(.+?)\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*$") {
        let t = _strip_suffix_colon(text);
        if (t === "" || !t.startswith("except")) {
            return null;
        }
        let rest = t.slice(6).strip();
        let i = rest.rfind(" as ");
        if (i < 0) {
            return null;
        }
        let exc = rest.slice(0, i).strip();
        let name = rest.slice(i + 4).strip();
        if (exc === "" || !_is_ident(name)) {
            return null;
        }
        return new Match(text, [exc, name]);
    }
    if (pattern === "^except\\s+(.+?)\\s*:\\s*$") {
        let t = _strip_suffix_colon(text);
        if (t === "" || !t.startswith("except")) {
            return null;
        }
        let rest = t.slice(6).strip();
        if (rest === "") {
            return null;
        }
        return new Match(text, [rest]);
    }
    if (pattern === "^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*:\\s*(.+)$") {
        let c = text.find(":");
        if (c <= 0) {
            return null;
        }
        let target = text.slice(0, c).strip();
        let ann = text.slice(c + 1).strip();
        if (ann === "" || !_is_dotted_ident(target)) {
            return null;
        }
        return new Match(text, [target, ann]);
    }
    if (pattern === "^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*:\\s*([^=]+?)\\s*=\\s*(.+)$") {
        let c = text.find(":");
        if (c <= 0) {
            return null;
        }
        let target = text.slice(0, c).strip();
        let rhs = text.slice(c + 1);
        let eq = rhs.find("=");
        if (eq < 0) {
            return null;
        }
        let ann = rhs.slice(0, eq).strip();
        let expr = rhs.slice(eq + 1).strip();
        if (!_is_dotted_ident(target) || ann === "" || expr === "") {
            return null;
        }
        return new Match(text, [target, ann, expr]);
    }
    if (pattern === "^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*(\\+=|-=|\\*=|/=|//=|%=|&=|\\|=|\\^=|<<=|>>>=)\\s*(.+)$") {
        let ops = ["<<=", ">>>=", "+=", "-=", "*=", "/=", "//=", "%=", "&=", "|=", "^="];
        let op_pos = -1;
        let op_txt = "";
        for (const op of ops) {
            let p = text.find(op);
            if (p >= 0 && op_pos < 0 || p < op_pos) {
                op_pos = p;
                op_txt = op;
            }
        }
        if (op_pos < 0) {
            return null;
        }
        let left = text.slice(0, op_pos).strip();
        let right = text.slice(op_pos + (op_txt).length).strip();
        if (right === "" || !_is_dotted_ident(left)) {
            return null;
        }
        return new Match(text, [left, op_txt, right]);
    }
    if (pattern === "^([A-Za-z_][A-Za-z0-9_]*)\\s*,\\s*([A-Za-z_][A-Za-z0-9_]*)\\s*=\\s*(.+)$") {
        let eq = text.find("=");
        if (eq < 0) {
            return null;
        }
        let left = text.slice(0, eq);
        let right = text.slice(eq + 1).strip();
        if (right === "") {
            return null;
        }
        let c = left.find(",");
        if (c < 0) {
            return null;
        }
        let a = left.slice(0, c).strip();
        let b = left.slice(c + 1).strip();
        if (!_is_ident(a) || !_is_ident(b)) {
            return null;
        }
        return new Match(text, [a, b, right]);
    }
    if (pattern === "^if\\s+__name__\\s*==\\s*[\\\"']__main__[\\\"']\\s*:\\s*$") {
        let t = _strip_suffix_colon(text);
        if (t === "") {
            return null;
        }
        let rest = t.strip();
        if (!rest.startswith("if")) {
            return null;
        }
        rest = rest.slice(2).strip();
        if (!rest.startswith("__name__")) {
            return null;
        }
        rest = rest.slice(("__name__").length).strip();
        if (!rest.startswith("==")) {
            return null;
        }
        rest = rest.slice(2).strip();
        if (rest in {'"__main__"', "'__main__'"}) {
            return new Match(text, []);
        }
        return null;
    }
    if (pattern === "^import\\s+(.+)$") {
        if (!text.startswith("import")) {
            return null;
        }
        if ((text).length <= 6) {
            return null;
        }
        if (!_is_space_ch(text.slice(6, 7))) {
            return null;
        }
        let rest = text.slice(7).strip();
        if (rest === "") {
            return null;
        }
        return new Match(text, [rest]);
    }
    if (pattern === "^([A-Za-z_][A-Za-z0-9_\\.]*)(?:\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*))?$") {
        let parts = text.split(" as ");
        if ((parts).length === 1) {
            let name = parts[(((0) < 0) ? ((parts).length + (0)) : (0))].strip();
            if (!_is_dotted_ident(name)) {
                return null;
            }
            return new Match(text, [name, ""]);
        }
        if ((parts).length === 2) {
            let name = parts[(((0) < 0) ? ((parts).length + (0)) : (0))].strip();
            let alias = parts[(((1) < 0) ? ((parts).length + (1)) : (1))].strip();
            if (!_is_dotted_ident(name) || !_is_ident(alias)) {
                return null;
            }
            return new Match(text, [name, alias]);
        }
        return null;
    }
    if (pattern === "^from\\s+([A-Za-z_][A-Za-z0-9_\\.]*)\\s+import\\s+(.+)$") {
        if (!text.startswith("from ")) {
            return null;
        }
        let rest = text.slice(5);
        let i = rest.find(" import ");
        if (i < 0) {
            return null;
        }
        let mod = rest.slice(0, i).strip();
        let sym = rest.slice(i + 8).strip();
        if (!_is_dotted_ident(mod) || sym === "") {
            return null;
        }
        return new Match(text, [mod, sym]);
    }
    if (pattern === "^([A-Za-z_][A-Za-z0-9_]*)(?:\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*))?$") {
        let parts = text.split(" as ");
        if ((parts).length === 1) {
            let name = parts[(((0) < 0) ? ((parts).length + (0)) : (0))].strip();
            if (!_is_ident(name)) {
                return null;
            }
            return new Match(text, [name, ""]);
        }
        if ((parts).length === 2) {
            let name = parts[(((0) < 0) ? ((parts).length + (0)) : (0))].strip();
            let alias = parts[(((1) < 0) ? ((parts).length + (1)) : (1))].strip();
            if (!_is_ident(name) || !_is_ident(alias)) {
                return null;
            }
            return new Match(text, [name, alias]);
        }
        return null;
    }
    if (pattern === "^([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*([^=]+?)\\s*=\\s*(.+)$") {
        let c = text.find(":");
        if (c <= 0) {
            return null;
        }
        let name = text.slice(0, c).strip();
        let rhs = text.slice(c + 1);
        let eq = rhs.find("=");
        if (eq < 0) {
            return null;
        }
        let ann = rhs.slice(0, eq).strip();
        let expr = rhs.slice(eq + 1).strip();
        if (!_is_ident(name) || ann === "" || expr === "") {
            return null;
        }
        return new Match(text, [name, ann, expr]);
    }
    if (pattern === "^([A-Za-z_][A-Za-z0-9_]*)\\s*=\\s*(.+)$") {
        let eq = text.find("=");
        if (eq < 0) {
            return null;
        }
        let name = text.slice(0, eq).strip();
        let expr = text.slice(eq + 1).strip();
        if (!_is_ident(name) || expr === "") {
            return null;
        }
        return new Match(text, [name, expr]);
    }
    throw new Error(("unsupported regex pattern in pytra.std.re: " + String(pattern)));
}

function sub(pattern, repl, text, flags) {
    if (pattern === "\\s+") {
        let out = [];
        let in_ws = false;
        for (const ch of text) {
            if (ch.isspace()) {
                if (!in_ws) {
                    out.push(repl);
                    in_ws = true;
                }
            } else {
                out.push(ch);
                in_ws = false;
            }
        }
        return "".join(out);
    }
    if (pattern === "\\s+#.*$") {
        let i = 0;
        while (i < (text).length) {
            if (text[(((i) < 0) ? ((text).length + (i)) : (i))].isspace()) {
                let j = i + 1;
                while (j < (text).length && text[(((j) < 0) ? ((text).length + (j)) : (j))].isspace()) {
                    j += 1;
                }
                if (j < (text).length && text[(((j) < 0) ? ((text).length + (j)) : (j))] === "#") {
                    return text.slice(0, i) + repl;
                }
            }
            i += 1;
        }
        return text;
    }
    if (pattern === "[^0-9A-Za-z_]") {
        let out = [];
        for (const ch of text) {
            if (ch.isalnum() || ch === "_") {
                out.push(ch);
            } else {
                out.push(repl);
            }
        }
        return "".join(out);
    }
    throw new Error(("unsupported regex sub pattern in pytra.std.re: " + String(pattern)));
}

"Minimal pure-Python regex subset used by Pytra selfhost path.";
let S = 1;

module.exports = {group, strip_group, match, sub};
