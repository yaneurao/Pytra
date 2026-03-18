// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/json.py
// generated-by: tools/gen_runtime_from_manifest.py

const { PYTRA_TYPE_ID, PY_TYPE_OBJECT, pyRegisterClassType } = require("../../native/built_in/py_runtime.js");

function _is_plain_json_object(value) {
    if (value === null || typeof value !== "object" || Array.isArray(value)) {
        return false;
    }
    const proto = Object.getPrototypeOf(value);
    return (
        proto === Object.prototype
        || proto === null
        || Object.prototype.hasOwnProperty.call(value, PYTRA_TYPE_ID)
    );
}

function _unwrap_json_value(value) {
    if (value instanceof JsonValue || value instanceof JsonObj || value instanceof JsonArr) {
        return value.raw;
    }
    return value;
}

function _normalize_indent(indent) {
    if (indent === null || indent === undefined) {
        return null;
    }
    const value = Math.trunc(Number(indent));
    return value < 0 ? 0 : value;
}

function _repeat_indent(indent, level) {
    return " ".repeat(indent * level);
}

function _unicode_escape(codePoint) {
    if (codePoint <= 0xFFFF) {
        return "\\u" + codePoint.toString(16).padStart(4, "0");
    }
    const adjusted = codePoint - 0x10000;
    const high = 0xD800 + (adjusted >> 10);
    const low = 0xDC00 + (adjusted & 0x3FF);
    return _unicode_escape(high) + _unicode_escape(low);
}

function _escape_json_string(text, ensure_ascii) {
    const out = ['"'];
    for (const ch of String(text)) {
        const code = ch.codePointAt(0);
        if (ch === '"') {
            out.push('\"');
        } else if (ch === "\\") {
            out.push('\\');
        } else if (ch === "\b") {
            out.push('\b');
        } else if (ch === "\f") {
            out.push('\f');
        } else if (ch === "\n") {
            out.push('\n');
        } else if (ch === "\r") {
            out.push('\r');
        } else if (ch === "\t") {
            out.push('\t');
        } else if (code !== undefined && code < 0x20) {
            out.push(_unicode_escape(code));
        } else if (ensure_ascii && code !== undefined && code > 0x7F) {
            out.push(_unicode_escape(code));
        } else {
            out.push(ch);
        }
    }
    out.push('"');
    return out.join("");
}

class JsonObj {
    static PYTRA_TYPE_ID = pyRegisterClassType([PY_TYPE_OBJECT]);

    constructor(raw) {
        this.raw = _is_plain_json_object(raw) ? raw : {};
        this[PYTRA_TYPE_ID] = JsonObj.PYTRA_TYPE_ID;
    }

    get(key) {
        if (!Object.prototype.hasOwnProperty.call(this.raw, key)) {
            return null;
        }
        return new JsonValue(this.raw[key]);
    }

    get_obj(key) {
        const value = this.get(key);
        return value === null ? null : value.as_obj();
    }

    get_arr(key) {
        const value = this.get(key);
        return value === null ? null : value.as_arr();
    }

    get_str(key) {
        const value = this.get(key);
        return value === null ? null : value.as_str();
    }

    get_int(key) {
        const value = this.get(key);
        return value === null ? null : value.as_int();
    }

    get_float(key) {
        const value = this.get(key);
        return value === null ? null : value.as_float();
    }

    get_bool(key) {
        const value = this.get(key);
        return value === null ? null : value.as_bool();
    }
}

class JsonArr {
    static PYTRA_TYPE_ID = pyRegisterClassType([PY_TYPE_OBJECT]);

    constructor(raw) {
        this.raw = Array.isArray(raw) ? raw : [];
        this[PYTRA_TYPE_ID] = JsonArr.PYTRA_TYPE_ID;
    }

    get(index) {
        if (!Number.isInteger(index) || index < 0 || index >= this.raw.length) {
            return null;
        }
        return new JsonValue(this.raw[index]);
    }

    get_obj(index) {
        const value = this.get(index);
        return value === null ? null : value.as_obj();
    }

    get_arr(index) {
        const value = this.get(index);
        return value === null ? null : value.as_arr();
    }

    get_str(index) {
        const value = this.get(index);
        return value === null ? null : value.as_str();
    }

    get_int(index) {
        const value = this.get(index);
        return value === null ? null : value.as_int();
    }

    get_float(index) {
        const value = this.get(index);
        return value === null ? null : value.as_float();
    }

    get_bool(index) {
        const value = this.get(index);
        return value === null ? null : value.as_bool();
    }
}

class JsonValue {
    static PYTRA_TYPE_ID = pyRegisterClassType([PY_TYPE_OBJECT]);

    constructor(raw) {
        this.raw = raw;
        this[PYTRA_TYPE_ID] = JsonValue.PYTRA_TYPE_ID;
    }

    as_obj() {
        return _is_plain_json_object(this.raw) ? new JsonObj(this.raw) : null;
    }

    as_arr() {
        return Array.isArray(this.raw) ? new JsonArr(this.raw) : null;
    }

    as_str() {
        return typeof this.raw === "string" ? this.raw : null;
    }

    as_int() {
        if (typeof this.raw === "boolean") {
            return null;
        }
        return typeof this.raw === "number" ? Math.trunc(this.raw) : null;
    }

    as_float() {
        return typeof this.raw === "number" ? this.raw : null;
    }

    as_bool() {
        return typeof this.raw === "boolean" ? this.raw : null;
    }
}

function _parse_json_text(text) {
    return JSON.parse(String(text));
}

function loads(text) {
    return _parse_json_text(text);
}

function loads_obj(text) {
    const value = _parse_json_text(text);
    return _is_plain_json_object(value) ? new JsonObj(value) : null;
}

function loads_arr(text) {
    const value = _parse_json_text(text);
    return Array.isArray(value) ? new JsonArr(value) : null;
}

function _dump_json_list(values, ensure_ascii, indent, item_sep, key_sep, level) {
    if (values.length === 0) {
        return "[]";
    }
    if (indent === null) {
        return "[" + values.map((item) => _dump_json_value(item, ensure_ascii, indent, item_sep, key_sep, level)).join(item_sep) + "]";
    }
    const inner = values.map(
        (item) =>
            _repeat_indent(indent, level + 1)
            + _dump_json_value(item, ensure_ascii, indent, item_sep, key_sep, level + 1),
    );
    return "[\n" + inner.join(",\n") + "\n" + _repeat_indent(indent, level) + "]";
}

function _dump_json_dict(values, ensure_ascii, indent, item_sep, key_sep, level) {
    const keys = Object.keys(values);
    if (keys.length === 0) {
        return "{}";
    }
    if (indent === null) {
        return "{" + keys.map(
            (key) =>
                _escape_json_string(key, ensure_ascii)
                + key_sep
                + _dump_json_value(values[key], ensure_ascii, indent, item_sep, key_sep, level),
        ).join(item_sep) + "}";
    }
    const inner = keys.map(
        (key) =>
            _repeat_indent(indent, level + 1)
            + _escape_json_string(key, ensure_ascii)
            + key_sep
            + _dump_json_value(values[key], ensure_ascii, indent, item_sep, key_sep, level + 1),
    );
    return "{\n" + inner.join(",\n") + "\n" + _repeat_indent(indent, level) + "}";
}

function _dump_json_value(value, ensure_ascii, indent, item_sep, key_sep, level) {
    const raw = _unwrap_json_value(value);
    if (raw === null || raw === undefined) {
        return "null";
    }
    if (typeof raw === "boolean") {
        return raw ? "true" : "false";
    }
    if (typeof raw === "number") {
        return String(raw);
    }
    if (typeof raw === "string") {
        return _escape_json_string(raw, ensure_ascii);
    }
    if (Array.isArray(raw)) {
        return _dump_json_list(raw, ensure_ascii, indent, item_sep, key_sep, level);
    }
    if (_is_plain_json_object(raw)) {
        return _dump_json_dict(raw, ensure_ascii, indent, item_sep, key_sep, level);
    }
    throw new Error("json.dumps unsupported type");
}

function dumps(obj, ensure_ascii = true, indent = null, separators = null) {
    let item_sep = ",";
    let key_sep = indent === null || indent === undefined ? ":" : ": ";
    if (Array.isArray(separators) && separators.length >= 2) {
        item_sep = String(separators[0]);
        key_sep = String(separators[1]);
    }
    return _dump_json_value(obj, ensure_ascii !== false, _normalize_indent(indent), item_sep, key_sep, 0);
}

module.exports = { JsonObj, JsonArr, JsonValue, loads, loads_obj, loads_arr, dumps };
