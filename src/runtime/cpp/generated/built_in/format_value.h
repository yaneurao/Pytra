// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/format_value.py
// generated-by: tools/gen_runtime_from_manifest.py

#ifndef PYTRA_GEN_BUILT_IN_FORMAT_VALUE_H
#define PYTRA_GEN_BUILT_IN_FORMAT_VALUE_H

// forward declarations
str py_format_value(const object& value, const str& spec);
str py_format_conversion(const object& value, const str& conversion);
str _to_str(const object& value);
str _repr_value(const object& value);
str _int_to_str(int64 value);
str _float_to_str(float64 value);
list<str> _parse_format_spec(const str& spec);
str _spec_fill(const list<str>& p);
str _spec_align(const list<str>& p);
str _spec_sign(const list<str>& p);
str _spec_width(const list<str>& p);
str _spec_grouping(const list<str>& p);
str _spec_precision(const list<str>& p);
str _spec_type(const list<str>& p);
str _format_core(const object& value, const list<str>& parsed);
str _format_int(int64 value, const str& tc, const str& sign, const str& grouping);
str _format_float(float64 value, const str& tc, const str& sign, const str& precision, const str& grouping);
str _int_to_hex(int64 value, bool upper);
str _int_to_oct(int64 value);
str _int_to_bin(int64 value);
str _float_fixed(float64 value, int64 prec);
str _float_exp(float64 value, int64 prec, const str& e_char);
str _float_general(float64 value, int64 prec, const str& tc);
str _apply_sign(const str& raw, bool negative, const str& sign);
str _apply_align(const str& raw, const list<str>& parsed);
int64 _str_to_int(const str& s);
str _insert_grouping(const str& digits, const str& sep, int64 group_size);

/* Pure-Python format spec interpreter for f-string formatting.

Implements a subset of Python's Format Specification Mini-Language:
  [[fill]align][sign][z][#][0][width][grouping_option][.precision][type]

Supported types: d, f, e, E, g, G, x, X, o, b, s, n, %
Supported align: <, >, ^, =
Supported sign: +, -, space
Supported grouping: , (comma) and _ (underscore)

This module is the source-of-truth for all transpilation targets.
Backends with native format support can override with emitter-level optimization.
 */

str py_format_value(const object& value, const str& spec) {
    /* Format *value* according to Python format spec *spec*.

    Equivalent to ``format(value, spec)`` in Python.
     */
    if (spec == "")
        return _to_str(value);
    list<str> parsed = _parse_format_spec(spec);
    str raw = _format_core(value, parsed);
    return _apply_align(raw, parsed);
}

str py_format_conversion(const object& value, const str& conversion) {
    /* Apply f-string conversion flag (!s, !r, !a). */
    if (conversion == "s")
        return _to_str(value);
    if (conversion == "r")
        return _repr_value(value);
    if (conversion == "a")
        return _repr_value(value);
    return _to_str(value);
}

str _to_str(const object& value) {
    str v = "";
    if (py_runtime_value_isinstance(value, PYTRA_TID_STR)) {
        v = py_to_string(value);
    } else if (py_runtime_value_isinstance(value, PYTRA_TID_BOOL)) {
        if (py_to<bool>(value))
            v = "True";
        else
            v = "False";
    } else if (py_runtime_value_isinstance(value, PYTRA_TID_INT)) {
        v = _int_to_str(int64(value));
    } else if (py_runtime_value_isinstance(value, PYTRA_TID_FLOAT)) {
        v = _float_to_str(float64(value));
    } else {
        v = py_to_string(value);
    }
    return v;
}

str _repr_value(const object& value) {
    if (py_runtime_value_isinstance(value, PYTRA_TID_STR))
        return "'" + value + "'";
    return _to_str(value);
}

str _int_to_str(int64 value) {
    if (value < 0)
        return "-" + _int_to_str(-(value));
    if (value == 0)
        return "0";
    list<str> digits = {};
    int64 n = value;
    while (n > 0) {
        int64 d = n % 10;
        if (d == 0) {
            digits.append("0");
        } else if (d == 1) {
            digits.append("1");
        } else if (d == 2) {
            digits.append("2");
        } else if (d == 3) {
            digits.append("3");
        } else if (d == 4) {
            digits.append("4");
        } else if (d == 5) {
            digits.append("5");
        } else if (d == 6) {
            digits.append("6");
        } else if (d == 7) {
            digits.append("7");
        } else if (d == 8) {
            digits.append("8");
        } else {
            digits.append("9");
        }
        n = n / 10;
    }
    str result = "";
    int64 i = digits.size() - 1;
    while (i >= 0) {
        result = result + digits[i];
        i = i - 1;
    }
    return result;
}

str _float_to_str(float64 value) {
    // Delegate to runtime str() for basic float rendering.
    return ::std::to_string(value);
}

list<str> _parse_format_spec(const str& spec) {
    /* Parse format spec into [fill, align, sign, width, grouping, precision, type_char].

    Returns a list of 7 strings for selfhost compatibility (no dataclass).
     */
    str fill = "";
    str align = "";
    str sign = "";
    str width = "";
    str grouping = "";
    str precision = "";
    str type_char = "";
    
    int64 pos = 0;
    int64 n = spec.size();
    
    // Detect fill + align.
    if ((n >= 2) && ((spec[1] == "<") || (spec[1] == ">") || (spec[1] == "^") || (spec[1] == "="))) {
        fill = spec[0];
        align = spec[1];
        pos = 2;
    } else if ((n >= 1) && ((spec[0] == "<") || (spec[0] == ">") || (spec[0] == "^") || (spec[0] == "="))) {
        align = spec[0];
        pos = 1;
    }
    if ((pos < n) && ((spec[pos] == "+") || (spec[pos] == "-") || (spec[pos] == " "))) {
        sign = spec[pos];
        pos = pos + 1;
    }
    if ((pos < n) && (spec[pos] == "z"))
        pos = pos + 1;
    if ((pos < n) && (spec[pos] == "#"))
        pos = pos + 1;
    if ((pos < n) && (spec[pos] == "0")) {
        if ((fill == "") && (align == "")) {
            fill = "0";
            align = "=";
        }
        pos = pos + 1;
    }
    int64 width_start = pos;
    while ((pos < n) && (spec[pos] >= "0") && (spec[pos] <= "9")) {
        pos = pos + 1;
    }
    if (pos > width_start)
        width = py_str_slice(spec, width_start, pos);
    if ((pos < n) && ((spec[pos] == ",") || (spec[pos] == "_"))) {
        grouping = spec[pos];
        pos = pos + 1;
    }
    if ((pos < n) && (spec[pos] == ".")) {
        pos = pos + 1;
        int64 prec_start = pos;
        while ((pos < n) && (spec[pos] >= "0") && (spec[pos] <= "9")) {
            pos = pos + 1;
        }
        precision = py_str_slice(spec, prec_start, pos);
    }
    if (pos < n)
        type_char = spec[pos];
    return list<str>{fill, align, sign, width, grouping, precision, type_char};
}

str _spec_fill(const list<str>& p) {
    return p[0];
}

str _spec_align(const list<str>& p) {
    return p[1];
}

str _spec_sign(const list<str>& p) {
    return p[2];
}

str _spec_width(const list<str>& p) {
    return p[3];
}

str _spec_grouping(const list<str>& p) {
    return p[4];
}

str _spec_precision(const list<str>& p) {
    return p[5];
}

str _spec_type(const list<str>& p) {
    return p[6];
}

str _format_core(const object& value, const list<str>& parsed) {
    str tc = _spec_type(parsed);
    str sign = _spec_sign(parsed);
    str precision = _spec_precision(parsed);
    str grouping = _spec_grouping(parsed);
    
    if ((tc == "s") || ((tc == "") && (py_runtime_value_isinstance(value, PYTRA_TID_STR)))) {
        str s = _to_str(value);
        if (precision != "") {
            int64 max_len = _str_to_int(precision);
            if (s.size() > max_len)
                s = py_str_slice(s, 0, max_len);
        }
        return s;
    }
    if ((py_runtime_value_isinstance(value, PYTRA_TID_INT)) && (!(py_runtime_value_isinstance(value, PYTRA_TID_BOOL))))
        return _format_int(int64(value), tc, sign, grouping);
    if (py_runtime_value_isinstance(value, PYTRA_TID_FLOAT))
        return _format_float(float64(value), tc, sign, precision, grouping);
    return _to_str(value);
}

str _format_int(int64 value, const str& tc, const str& sign, const str& grouping) {
    bool negative = value < 0;
    int64 abs_val = (negative ? -(value) : value);
    
    str raw = "";
    if ((tc == "d") || (tc == "") || (tc == "n")) {
        raw = _int_to_str(abs_val);
    } else if (tc == "x") {
        raw = _int_to_hex(abs_val, false);
    } else if (tc == "X") {
        raw = _int_to_hex(abs_val, true);
    } else if (tc == "o") {
        raw = _int_to_oct(abs_val);
    } else if (tc == "b") {
        raw = _int_to_bin(abs_val);
    } else if ((tc == "f") || (tc == "e") || (tc == "E") || (tc == "g") || (tc == "G")) {
        // int with float format spec: convert to float.
        return _format_float(float64(value), tc, sign, "", grouping);
    } else {
        raw = _int_to_str(abs_val);
    }
    if (grouping == ",") {
        raw = _insert_grouping(raw, ",", 3);
    } else if (grouping == "_") {
        if ((tc == "x") || (tc == "X")) {
            raw = _insert_grouping(raw, "_", 4);
        } else if (tc == "b") {
            raw = _insert_grouping(raw, "_", 4);
        } else if (tc == "o") {
            raw = _insert_grouping(raw, "_", 4);
        } else {
            raw = _insert_grouping(raw, "_", 3);
        }
    }
    return _apply_sign(raw, negative, sign);
}

str _format_float(float64 value, const str& tc, const str& sign, const str& precision, const str& grouping) {
    int64 prec = 6;
    if (precision != "")
        prec = _str_to_int(precision);
    bool negative = value < 0.0;
    float64 abs_val = (negative ? -(value) : value);
    
    str raw = "";
    if ((tc == "f") || (tc == "F") || (tc == "")) {
        raw = _float_fixed(abs_val, prec);
    } else if (tc == "e") {
        raw = _float_exp(abs_val, prec, "e");
    } else if (tc == "E") {
        raw = _float_exp(abs_val, prec, "E");
    } else if ((tc == "g") || (tc == "G")) {
        raw = _float_general(abs_val, prec, tc);
    } else if (tc == "%") {
        raw = _float_fixed(abs_val * 100.0, prec) + "%";
    } else if ((tc == "") && (precision != "")) {
        raw = _float_fixed(abs_val, prec);
    } else {
        raw = _float_fixed(abs_val, prec);
    }
    if (grouping != "") {
        // Apply grouping to integer part only.
        int64 dot_pos = int64(py_find(raw, "."));
        if (dot_pos >= 0) {
            str int_part = py_str_slice(raw, 0, dot_pos);
            str frac_part = py_str_slice(raw, dot_pos, int64(raw.size()));
            raw = _insert_grouping(int_part, grouping, 3) + frac_part;
        } else {
            int64 pct_pos = int64(py_find(raw, "%"));
            if (pct_pos >= 0)
                raw = _insert_grouping(py_str_slice(raw, 0, pct_pos), grouping, 3) + "%";
            else
                raw = _insert_grouping(raw, grouping, 3);
        }
    }
    return _apply_sign(raw, negative, sign);
}

str _int_to_hex(int64 value, bool upper) {
    if (value == 0)
        return "0";
    str hex_lower = "0123456789abcdef";
    str hex_upper = "0123456789ABCDEF";
    str table = (upper ? hex_upper : hex_lower);
    list<str> digits = {};
    int64 n = value;
    while (n > 0) {
        digits.append(table[n % 16]);
        n = n / 16;
    }
    str result = "";
    int64 i = digits.size() - 1;
    while (i >= 0) {
        result = result + digits[i];
        i = i - 1;
    }
    return result;
}

str _int_to_oct(int64 value) {
    if (value == 0)
        return "0";
    list<str> digits = {};
    int64 n = value;
    while (n > 0) {
        digits.append(_int_to_str(n % 8));
        n = n / 8;
    }
    str result = "";
    int64 i = digits.size() - 1;
    while (i >= 0) {
        result = result + digits[i];
        i = i - 1;
    }
    return result;
}

str _int_to_bin(int64 value) {
    if (value == 0)
        return "0";
    list<str> digits = {};
    int64 n = value;
    while (n > 0) {
        if (n % 2 == 0)
            digits.append("0");
        else
            digits.append("1");
        n = n / 2;
    }
    str result = "";
    int64 i = digits.size() - 1;
    while (i >= 0) {
        result = result + digits[i];
        i = i - 1;
    }
    return result;
}

str _float_fixed(float64 value, int64 prec) {
    /* Format float as fixed-point with *prec* decimal places. */
    if (prec == 0) {
        int64 rounded = int64(value + 0.5);
        return _int_to_str(rounded);
    }
    float64 factor = 1.0;
    int64 i = 0;
    while (i < prec) {
        factor = factor * 10.0;
        i = i + 1;
    }
    int64 rounded_val = int64(value * factor + 0.5);
    int64 int_part = rounded_val / int64(factor);
    int64 frac_part = rounded_val % int64(factor);
    
    str frac_str = _int_to_str(frac_part);
    // Zero-pad fraction to prec digits.
    while (frac_str.size() < prec) {
        frac_str = "0" + frac_str;
    }
    return _int_to_str(int_part) + "." + frac_str;
}

str _float_exp(float64 value, int64 prec, const str& e_char) {
    /* Format float in scientific notation. */
    if (value == 0.0) {
        str frac = "";
        if (prec > 0)
            frac = py_to_string("." + py_repeat("0", prec));
        return "0" + frac + e_char + "+00";
    }
    int64 exp = 0;
    float64 v = value;
    if (v >= 10.0) {
        while (v >= 10.0) {
            v = v / 10.0;
            exp = exp + 1;
        }
    } else if (v < 1.0) {
        while (v < 1.0) {
            v = v * 10.0;
            exp = exp - 1;
        }
    }
    str mantissa = _float_fixed(v, prec);
    str exp_sign = (exp >= 0 ? "+" : "-");
    int64 abs_exp = (exp >= 0 ? exp : -(exp));
    str exp_str = _int_to_str(abs_exp);
    if (exp_str.size() < 2)
        exp_str = "0" + exp_str;
    return mantissa + e_char + exp_sign + exp_str;
}

str _float_general(float64 value, int64 prec, const str& tc) {
    /* Format float in general format (g/G). */
    if (prec == 0)
        prec = 1;
    if (value == 0.0)
        return (prec > 1 ? _float_fixed(value, prec - 1) : "0");
    float64 abs_val = (value >= 0.0 ? value : -(value));
    int64 exp = 0;
    float64 v = abs_val;
    if (v >= 10.0) {
        while (v >= 10.0) {
            v = v / 10.0;
            exp = exp + 1;
        }
    } else if ((v < 1.0) && (v > 0.0)) {
        while (v < 1.0) {
            v = v * 10.0;
            exp = exp - 1;
        }
    }
    str e_char = (tc == "g" ? "e" : "E");
    if ((exp >= -(4)) && (exp < prec)) {
        int64 fixed_prec = prec - 1 - exp;
        if (fixed_prec < 0)
            fixed_prec = 0;
        str result = _float_fixed(value, fixed_prec);
        // Strip trailing zeros after decimal.
        if (py_contains(result, ".")) {
            while (py_endswith(result, "0")) {
                result = py_str_slice(result, 0, -(1));
            }
            if (py_endswith(result, "."))
                result = py_str_slice(result, 0, -(1));
        }
        return result;
    }
    return _float_exp(value, prec - 1, e_char);
}

str _apply_sign(const str& raw, bool negative, const str& sign) {
    if (negative)
        return "-" + raw;
    if (sign == "+")
        return "+" + raw;
    if (sign == " ")
        return " " + raw;
    return raw;
}

str _apply_align(const str& raw, const list<str>& parsed) {
    str width_str = _spec_width(parsed);
    if (width_str == "")
        return raw;
    int64 width = _str_to_int(width_str);
    if (raw.size() >= width)
        return raw;
    str fill = _spec_fill(parsed);
    if (fill == "")
        fill = " ";
    str align = _spec_align(parsed);
    int64 pad_count = width - raw.size();
    str padding = py_repeat(fill, pad_count);
    
    if (align == "<")
        return raw + padding;
    if (align == "^") {
        int64 left = pad_count / 2;
        int64 right = pad_count - left;
        return py_repeat(fill, left) + raw + py_repeat(fill, right);
    }
    if (align == "=") {
        // Pad after sign.
        if ((raw.size() > 0) && ((raw[0] == "-") || (raw[0] == "+") || (raw[0] == " ")))
            return raw[0] + padding + py_str_slice(raw, 1, int64(raw.size()));
        return padding + raw;
    }
    str tc = _spec_type(parsed);
    if (tc == "s")
        return raw + padding;
    return padding + raw;
}

int64 _str_to_int(const str& s) {
    int64 result = 0;
    int64 i = 0;
    while (i < s.size()) {
        str c = s[i];
        int64 d = 0;
        if (c == "1") {
            d = 1;
        } else if (c == "2") {
            d = 2;
        } else if (c == "3") {
            d = 3;
        } else if (c == "4") {
            d = 4;
        } else if (c == "5") {
            d = 5;
        } else if (c == "6") {
            d = 6;
        } else if (c == "7") {
            d = 7;
        } else if (c == "8") {
            d = 8;
        } else if (c == "9") {
            d = 9;
        }
        result = result * 10 + d;
        i = i + 1;
    }
    return result;
}

str _insert_grouping(const str& digits, const str& sep, int64 group_size) {
    /* Insert *sep* every *group_size* digits from the right. */
    int64 n = digits.size();
    if (n <= group_size)
        return digits;
    list<str> parts = {};
    int64 pos = n;
    while (pos > 0) {
        int64 start = pos - group_size;
        if (start < 0)
            start = 0;
        parts.append(py_str_slice(digits, start, pos));
        pos = start;
    }
    // Reverse parts.
    str result = "";
    int64 i = parts.size() - 1;
    while (i >= 0) {
        if (result != "")
            result = result + sep;
        result = result + parts[i];
        i = i - 1;
    }
    return result;
}

#endif  // PYTRA_GEN_BUILT_IN_FORMAT_VALUE_H
