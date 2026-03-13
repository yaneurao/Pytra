// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/json.py
// generated-by: tools/gen_runtime_from_manifest.py

using System;
using System.Collections.Generic;
using System.Linq;
using Any = System.Object;
using int64 = System.Int64;
using float64 = System.Double;
using str = System.String;
using Pytra.CsModule;

public class JsonObj
{
    public static readonly long PYTRA_TYPE_ID = Pytra.CsModule.py_runtime.py_register_class_type(Pytra.CsModule.py_runtime.PYTRA_TID_OBJECT);
    public System.Collections.Generic.Dictionary<string, object> raw;
    
    public JsonObj(System.Collections.Generic.Dictionary<string, object> raw)
    {
        this.raw = raw;
    }
    
    public JsonValue get(string key)
    {
        if (!((this.raw).ContainsKey(key))) {
            return null;
        }
        var value = _json_obj_require(this.raw, key);
        return new JsonValue(value);
    }
    
    public JsonObj get_obj(string key)
    {
        if (!((this.raw).ContainsKey(key))) {
            return null;
        }
        var value = _json_obj_require(this.raw, key);
        return new JsonValue(value).as_obj();
    }
    
    public JsonArr get_arr(string key)
    {
        if (!((this.raw).ContainsKey(key))) {
            return null;
        }
        var value = _json_obj_require(this.raw, key);
        return new JsonValue(value).as_arr();
    }
    
    public string get_str(string key)
    {
        if (!((this.raw).ContainsKey(key))) {
            return null;
        }
        var value = _json_obj_require(this.raw, key);
        return new JsonValue(value).as_str();
    }
    
    public long? get_int(string key)
    {
        if (!((this.raw).ContainsKey(key))) {
            return null;
        }
        var value = _json_obj_require(this.raw, key);
        return new JsonValue(value).as_int();
    }
    
    public double? get_float(string key)
    {
        if (!((this.raw).ContainsKey(key))) {
            return null;
        }
        var value = _json_obj_require(this.raw, key);
        return new JsonValue(value).as_float();
    }
    
    public bool? get_bool(string key)
    {
        if (!((this.raw).ContainsKey(key))) {
            return null;
        }
        var value = _json_obj_require(this.raw, key);
        return new JsonValue(value).as_bool();
    }
}

public class JsonArr
{
    public static readonly long PYTRA_TYPE_ID = Pytra.CsModule.py_runtime.py_register_class_type(Pytra.CsModule.py_runtime.PYTRA_TID_OBJECT);
    public System.Collections.Generic.List<object> raw;
    
    public JsonArr(System.Collections.Generic.List<object> raw)
    {
        this.raw = raw;
    }
    
    public JsonValue get(long index)
    {
        if (((index) < (0)) || ((index) >= ((_json_array_items(this.raw)).Count))) {
            return null;
        }
        return new JsonValue(Pytra.CsModule.py_runtime.py_get(_json_array_items(this.raw), index));
    }
    
    public JsonObj get_obj(long index)
    {
        if (((index) < (0)) || ((index) >= ((_json_array_items(this.raw)).Count))) {
            return null;
        }
        return new JsonValue(Pytra.CsModule.py_runtime.py_get(_json_array_items(this.raw), index)).as_obj();
    }
    
    public JsonArr get_arr(long index)
    {
        if (((index) < (0)) || ((index) >= ((_json_array_items(this.raw)).Count))) {
            return null;
        }
        return new JsonValue(Pytra.CsModule.py_runtime.py_get(_json_array_items(this.raw), index)).as_arr();
    }
    
    public string get_str(long index)
    {
        if (((index) < (0)) || ((index) >= ((_json_array_items(this.raw)).Count))) {
            return null;
        }
        return new JsonValue(Pytra.CsModule.py_runtime.py_get(_json_array_items(this.raw), index)).as_str();
    }
    
    public long? get_int(long index)
    {
        if (((index) < (0)) || ((index) >= ((_json_array_items(this.raw)).Count))) {
            return null;
        }
        return new JsonValue(Pytra.CsModule.py_runtime.py_get(_json_array_items(this.raw), index)).as_int();
    }
    
    public double? get_float(long index)
    {
        if (((index) < (0)) || ((index) >= ((_json_array_items(this.raw)).Count))) {
            return null;
        }
        return new JsonValue(Pytra.CsModule.py_runtime.py_get(_json_array_items(this.raw), index)).as_float();
    }
    
    public bool? get_bool(long index)
    {
        if (((index) < (0)) || ((index) >= ((_json_array_items(this.raw)).Count))) {
            return null;
        }
        return new JsonValue(Pytra.CsModule.py_runtime.py_get(_json_array_items(this.raw), index)).as_bool();
    }
}

public class JsonValue
{
    public static readonly long PYTRA_TYPE_ID = Pytra.CsModule.py_runtime.py_register_class_type(Pytra.CsModule.py_runtime.PYTRA_TID_OBJECT);
    public object raw;
    
    public JsonValue(object raw)
    {
        this.raw = raw;
    }
    
    public JsonObj as_obj()
    {
        var raw = this.raw;
        if (Pytra.CsModule.py_runtime.py_runtime_value_isinstance(raw, Pytra.CsModule.py_runtime.PYTRA_TID_DICT)) {
            System.Collections.Generic.Dictionary<string, object> raw_obj = Program.PytraDictStringObjectFromAny(raw);
            return new JsonObj(raw_obj);
        }
        return null;
    }
    
    public JsonArr as_arr()
    {
        var raw = this.raw;
        if (Pytra.CsModule.py_runtime.py_runtime_value_isinstance(raw, Pytra.CsModule.py_runtime.PYTRA_TID_LIST)) {
            System.Collections.Generic.List<object> raw_arr = new System.Collections.Generic.List<object>(raw);
            return new JsonArr(raw_arr);
        }
        return null;
    }
    
    public string as_str()
    {
        var raw = this.raw;
        if (Pytra.CsModule.py_runtime.py_runtime_value_isinstance(raw, Pytra.CsModule.py_runtime.PYTRA_TID_STR)) {
            return raw;
        }
        return null;
    }
    
    public long? as_int()
    {
        var raw = this.raw;
        if (Pytra.CsModule.py_runtime.py_runtime_value_isinstance(raw, Pytra.CsModule.py_runtime.PYTRA_TID_BOOL)) {
            return null;
        }
        if (Pytra.CsModule.py_runtime.py_runtime_value_isinstance(raw, Pytra.CsModule.py_runtime.PYTRA_TID_INT)) {
            long raw_i = Pytra.CsModule.py_runtime.py_int(raw);
            return raw_i;
        }
        return null;
    }
    
    public double? as_float()
    {
        var raw = this.raw;
        if (Pytra.CsModule.py_runtime.py_runtime_value_isinstance(raw, Pytra.CsModule.py_runtime.PYTRA_TID_FLOAT)) {
            double raw_f = System.Convert.ToDouble(raw);
            return raw_f;
        }
        return null;
    }
    
    public bool? as_bool()
    {
        var raw = this.raw;
        if (Pytra.CsModule.py_runtime.py_runtime_value_isinstance(raw, Pytra.CsModule.py_runtime.PYTRA_TID_BOOL)) {
            bool raw_b = Pytra.CsModule.py_runtime.py_bool(raw);
            return raw_b;
        }
        return null;
    }
}

public class _JsonParser
{
    public static readonly long PYTRA_TYPE_ID = Pytra.CsModule.py_runtime.py_register_class_type(Pytra.CsModule.py_runtime.PYTRA_TID_OBJECT);
    public string text;
    public long n;
    public long i;
    
    public _JsonParser(string text)
    {
        this.text = text;
        this.n = (text).Length;
        this.i = 0;
    }
    
    public object parse()
    {
        this._skip_ws();
        var py_out = this._parse_value();
        this._skip_ws();
        if ((this.i) != (this.n)) {
            throw new System.Exception("invalid json: trailing characters");
        }
        return py_out;
    }
    
    public void _skip_ws()
    {
        while (((this.i) < (this.n)) && (_is_ws(Pytra.CsModule.py_runtime.py_get(this.text, this.i)))) {
            this.i += 1;
        }
    }
    
    public object _parse_value()
    {
        if ((this.i) >= (this.n)) {
            throw new System.Exception("invalid json: unexpected end");
        }
        string ch = Pytra.CsModule.py_runtime.py_get(this.text, this.i);
        if ((ch) == ("{")) {
            return this._parse_object();
        }
        if ((ch) == ("[")) {
            return this._parse_array();
        }
        if ((ch) == ("\"")) {
            return this._parse_string();
        }
        if (((ch) == ("t")) && ((Pytra.CsModule.py_runtime.py_slice(this.text, System.Convert.ToInt64(this.i), System.Convert.ToInt64(this.i + 4))) == ("true"))) {
            this.i += 4;
            return true;
        }
        if (((ch) == ("f")) && ((Pytra.CsModule.py_runtime.py_slice(this.text, System.Convert.ToInt64(this.i), System.Convert.ToInt64(this.i + 5))) == ("false"))) {
            this.i += 5;
            return false;
        }
        if (((ch) == ("n")) && ((Pytra.CsModule.py_runtime.py_slice(this.text, System.Convert.ToInt64(this.i), System.Convert.ToInt64(this.i + 4))) == ("null"))) {
            this.i += 4;
            return null;
        }
        return this._parse_number();
    }
    
    public System.Collections.Generic.Dictionary<string, object> _parse_object()
    {
        System.Collections.Generic.Dictionary<string, object> py_out = new System.Collections.Generic.Dictionary<string, object>();
        this.i += 1;
        this._skip_ws();
        if (((this.i) < (this.n)) && ((Pytra.CsModule.py_runtime.py_get(this.text, this.i)) == ("}"))) {
            this.i += 1;
            return py_out;
        }
        while (true) {
            this._skip_ws();
            if (((this.i) >= (this.n)) || ((Pytra.CsModule.py_runtime.py_get(this.text, this.i)) != ("\""))) {
                throw new System.Exception("invalid json object key");
            }
            string key = this._parse_string();
            this._skip_ws();
            if (((this.i) >= (this.n)) || ((Pytra.CsModule.py_runtime.py_get(this.text, this.i)) != (":"))) {
                throw new System.Exception("invalid json object: missing ':'");
            }
            this.i += 1;
            this._skip_ws();
            py_out[key] = this._parse_value();
            this._skip_ws();
            if ((this.i) >= (this.n)) {
                throw new System.Exception("invalid json object: unexpected end");
            }
            string ch = Pytra.CsModule.py_runtime.py_get(this.text, this.i);
            this.i += 1;
            if ((ch) == ("}")) {
                return py_out;
            }
            if ((ch) != (",")) {
                throw new System.Exception("invalid json object separator");
            }
        }
    return default(System.Collections.Generic.Dictionary<string, object>);
    }
    
    public System.Collections.Generic.List<object> _parse_array()
    {
        System.Collections.Generic.List<object> py_out = _json_new_array();
        this.i += 1;
        this._skip_ws();
        if (((this.i) < (this.n)) && ((Pytra.CsModule.py_runtime.py_get(this.text, this.i)) == ("]"))) {
            this.i += 1;
            return py_out;
        }
        while (true) {
            this._skip_ws();
            py_out.Add(this._parse_value());
            this._skip_ws();
            if ((this.i) >= (this.n)) {
                throw new System.Exception("invalid json array: unexpected end");
            }
            string ch = Pytra.CsModule.py_runtime.py_get(this.text, this.i);
            this.i += 1;
            if ((ch) == ("]")) {
                return py_out;
            }
            if ((ch) != (",")) {
                throw new System.Exception("invalid json array separator");
            }
        }
    return default(System.Collections.Generic.List<object>);
    }
    
    public string _parse_string()
    {
        if ((Pytra.CsModule.py_runtime.py_get(this.text, this.i)) != ("\"")) {
            throw new System.Exception("invalid json string");
        }
        this.i += 1;
        System.Collections.Generic.List<string> out_chars = new System.Collections.Generic.List<string>();
        while ((this.i) < (this.n)) {
            string ch = Pytra.CsModule.py_runtime.py_get(this.text, this.i);
            this.i += 1;
            if ((ch) == ("\"")) {
                return _join_strs(out_chars, _EMPTY);
            }
            if ((ch) == ("\\")) {
                if ((this.i) >= (this.n)) {
                    throw new System.Exception("invalid json string escape");
                }
                string esc = Pytra.CsModule.py_runtime.py_get(this.text, this.i);
                this.i += 1;
                if ((esc) == ("\"")) {
                    out_chars.Add("\"");
                } else {
                    if ((esc) == ("\\")) {
                        out_chars.Add("\\");
                    } else {
                        if ((esc) == ("/")) {
                            out_chars.Add("/");
                        } else {
                            if ((esc) == ("b")) {
                                out_chars.Add("\b");
                            } else {
                                if ((esc) == ("f")) {
                                    out_chars.Add("\f");
                                } else {
                                    if ((esc) == ("n")) {
                                        out_chars.Add("\n");
                                    } else {
                                        if ((esc) == ("r")) {
                                            out_chars.Add("\r");
                                        } else {
                                            if ((esc) == ("t")) {
                                                out_chars.Add("\t");
                                            } else {
                                                if ((esc) == ("u")) {
                                                    if ((this.i + 4) > (this.n)) {
                                                        throw new System.Exception("invalid json unicode escape");
                                                    }
                                                    string hx = Pytra.CsModule.py_runtime.py_slice(this.text, System.Convert.ToInt64(this.i), System.Convert.ToInt64(this.i + 4));
                                                    this.i += 4;
                                                    out_chars.Add(System.Convert.ToString(System.Convert.ToChar(System.Convert.ToInt32(_int_from_hex4(hx)))));
                                                } else {
                                                    throw new System.Exception("invalid json escape");
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            } else {
                out_chars.Add(ch);
            }
        }
        throw new System.Exception("unterminated json string");
    return default(string);
    }
    
    public object _parse_number()
    {
        long start = this.i;
        if ((Pytra.CsModule.py_runtime.py_get(this.text, this.i)) == ("-")) {
            this.i += 1;
        }
        if ((this.i) >= (this.n)) {
            throw new System.Exception("invalid json number");
        }
        if ((Pytra.CsModule.py_runtime.py_get(this.text, this.i)) == ("0")) {
            this.i += 1;
        } else {
            if (!_is_digit(Pytra.CsModule.py_runtime.py_get(this.text, this.i))) {
                throw new System.Exception("invalid json number");
            }
            while (((this.i) < (this.n)) && (_is_digit(Pytra.CsModule.py_runtime.py_get(this.text, this.i)))) {
                this.i += 1;
            }
        }
        bool is_float = false;
        if (((this.i) < (this.n)) && ((Pytra.CsModule.py_runtime.py_get(this.text, this.i)) == ("."))) {
            is_float = true;
            this.i += 1;
            if (((this.i) >= (this.n)) || (!_is_digit(Pytra.CsModule.py_runtime.py_get(this.text, this.i)))) {
                throw new System.Exception("invalid json number");
            }
            while (((this.i) < (this.n)) && (_is_digit(Pytra.CsModule.py_runtime.py_get(this.text, this.i)))) {
                this.i += 1;
            }
        }
        if ((this.i) < (this.n)) {
            string exp_ch = Pytra.CsModule.py_runtime.py_get(this.text, this.i);
            if (((exp_ch) == ("e")) || ((exp_ch) == ("E"))) {
                is_float = true;
                this.i += 1;
                if ((this.i) < (this.n)) {
                    string sign = Pytra.CsModule.py_runtime.py_get(this.text, this.i);
                    if (((sign) == ("+")) || ((sign) == ("-"))) {
                        this.i += 1;
                    }
                }
                if (((this.i) >= (this.n)) || (!_is_digit(Pytra.CsModule.py_runtime.py_get(this.text, this.i)))) {
                    throw new System.Exception("invalid json exponent");
                }
                while (((this.i) < (this.n)) && (_is_digit(Pytra.CsModule.py_runtime.py_get(this.text, this.i)))) {
                    this.i += 1;
                }
            }
        }
        string token = Pytra.CsModule.py_runtime.py_slice(this.text, System.Convert.ToInt64(start), System.Convert.ToInt64(this.i));
        if (is_float) {
            double num_f = System.Convert.ToDouble(token);
            return num_f;
        }
        long num_i = Pytra.CsModule.py_runtime.py_int(token);
        return num_i;
    }
}

public static class Program
{
    public static bool _is_ws(string ch)
    {
        return (((ch) == (" ")) || ((ch) == ("\t")) || ((ch) == ("\r")) || ((ch) == ("\n")));
    }
    
    public static bool _is_digit(string ch)
    {
        return (((ch) >= ("0")) && ((ch) <= ("9")));
    }
    
    public static long _hex_value(string ch)
    {
        if (((ch) >= ("0")) && ((ch) <= ("9"))) {
            return Pytra.CsModule.py_runtime.py_int(ch);
        }
        if (((ch) == ("a")) || ((ch) == ("A"))) {
            return 10;
        }
        if (((ch) == ("b")) || ((ch) == ("B"))) {
            return 11;
        }
        if (((ch) == ("c")) || ((ch) == ("C"))) {
            return 12;
        }
        if (((ch) == ("d")) || ((ch) == ("D"))) {
            return 13;
        }
        if (((ch) == ("e")) || ((ch) == ("E"))) {
            return 14;
        }
        if (((ch) == ("f")) || ((ch) == ("F"))) {
            return 15;
        }
        throw new System.Exception("invalid json unicode escape");
    return default(long);
    }
    
    public static long _int_from_hex4(string hx)
    {
        if (((hx).Length) != (4)) {
            throw new System.Exception("invalid json unicode escape");
        }
        long v0 = _hex_value(Pytra.CsModule.py_runtime.py_slice(hx, System.Convert.ToInt64(0), System.Convert.ToInt64(1)));
        long v1 = _hex_value(Pytra.CsModule.py_runtime.py_slice(hx, System.Convert.ToInt64(1), System.Convert.ToInt64(2)));
        long v2 = _hex_value(Pytra.CsModule.py_runtime.py_slice(hx, System.Convert.ToInt64(2), System.Convert.ToInt64(3)));
        long v3 = _hex_value(Pytra.CsModule.py_runtime.py_slice(hx, System.Convert.ToInt64(3), System.Convert.ToInt64(4)));
        return v0 * 4096 + v1 * 256 + v2 * 16 + v3;
    }
    
    public static string _hex4(long code)
    {
        long v = code % 65536;
        long d3 = v % 16;
        v = System.Convert.ToInt64(System.Math.Floor(System.Convert.ToDouble(v) / System.Convert.ToDouble(16)));
        long d2 = v % 16;
        v = System.Convert.ToInt64(System.Math.Floor(System.Convert.ToDouble(v) / System.Convert.ToDouble(16)));
        long d1 = v % 16;
        v = System.Convert.ToInt64(System.Math.Floor(System.Convert.ToDouble(v) / System.Convert.ToDouble(16)));
        long d0 = v % 16;
        string p0 = System.Convert.ToString(_HEX_DIGITS[System.Convert.ToInt32(null)]);
        string p1 = System.Convert.ToString(_HEX_DIGITS[System.Convert.ToInt32(null)]);
        string p2 = System.Convert.ToString(_HEX_DIGITS[System.Convert.ToInt32(null)]);
        string p3 = System.Convert.ToString(_HEX_DIGITS[System.Convert.ToInt32(null)]);
        return p0 + p1 + p2 + p3;
    }
    
    public static System.Collections.Generic.List<object> _json_array_items(object raw)
    {
        return new System.Collections.Generic.List<object>(raw);
    }
    
    public static System.Collections.Generic.List<object> _json_new_array()
    {
        return new System.Collections.Generic.List<object>();
    }
    
    public static object _json_obj_require(System.Collections.Generic.Dictionary<string, object> raw, string key)
    {
        foreach (var __it_1 in raw) {
        var k = __it_1.Key;
        var value = __it_1.Value;
            if ((k) == (key)) {
                return value;
            }
        }
        throw new System.Exception("json object key not found: " + key);
    return default(object);
    }
    
    public static long _json_indent_value(long? indent)
    {
        if ((indent) == (null)) {
            throw new System.Exception("json indent is required");
        }
        long indent_i = indent;
        return indent_i;
    }
    
    public static object loads(string text)
    {
        return new _JsonParser(text).parse();
    }
    
    public static JsonObj loads_obj(string text)
    {
        var value = new _JsonParser(text).parse();
        if (Pytra.CsModule.py_runtime.py_runtime_value_isinstance(value, Pytra.CsModule.py_runtime.PYTRA_TID_DICT)) {
            System.Collections.Generic.Dictionary<string, object> raw_obj = Program.PytraDictStringObjectFromAny(value);
            return new JsonObj(raw_obj);
        }
        return null;
    }
    
    public static JsonArr loads_arr(string text)
    {
        var value = new _JsonParser(text).parse();
        if (Pytra.CsModule.py_runtime.py_runtime_value_isinstance(value, Pytra.CsModule.py_runtime.PYTRA_TID_LIST)) {
            System.Collections.Generic.List<object> raw_arr = new System.Collections.Generic.List<object>(value);
            return new JsonArr(raw_arr);
        }
        return null;
    }
    
    public static string _join_strs(System.Collections.Generic.List<string> parts, string sep)
    {
        if (((parts).Count) == (0)) {
            return "";
        }
        string py_out = Pytra.CsModule.py_runtime.py_get(parts, 0);
        long i = 1;
        while ((i) < ((parts).Count)) {
            py_out = py_out + sep + Pytra.CsModule.py_runtime.py_get(parts, i);
            i += 1;
        }
        return py_out;
    }
    
    public static string _escape_str(string s, bool ensure_ascii)
    {
        System.Collections.Generic.List<string> py_out = new System.Collections.Generic.List<string> { "\"" };
        foreach (var ch in (s).Select(__ch => __ch.ToString())) {
            long code = System.Convert.ToInt64(Pytra.CsModule.py_runtime.py_ord(ch));
            if ((ch) == ("\"")) {
                py_out.Add("\\\"");
            } else {
                if ((ch) == ("\\")) {
                    py_out.Add("\\\\");
                } else {
                    if ((ch) == ("\b")) {
                        py_out.Add("\\b");
                    } else {
                        if ((ch) == ("\f")) {
                            py_out.Add("\\f");
                        } else {
                            if ((ch) == ("\n")) {
                                py_out.Add("\\n");
                            } else {
                                if ((ch) == ("\r")) {
                                    py_out.Add("\\r");
                                } else {
                                    if ((ch) == ("\t")) {
                                        py_out.Add("\\t");
                                    } else {
                                        if ((ensure_ascii) && ((code) > (0x7F))) {
                                            py_out.Add("\\u" + _hex4(code));
                                        } else {
                                            py_out.Add(ch);
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        py_out.Add("\"");
        return _join_strs(py_out, _EMPTY);
    }
    
    public static string _dump_json_list(System.Collections.Generic.List<object> values, bool ensure_ascii, long? indent, string item_sep, string key_sep, long level)
    {
        if (((values).Count) == (0)) {
            return "[]";
        }
        if ((indent) == (null)) {
            System.Collections.Generic.List<string> dumped = new System.Collections.Generic.List<string>();
            foreach (var x in values) {
                string dumped_txt = System.Convert.ToString(_dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level));
                dumped.Add(dumped_txt);
            }
            return "[" + _join_strs(dumped, item_sep) + "]";
        }
        long indent_i = _json_indent_value(indent);
        System.Collections.Generic.List<string> inner = new System.Collections.Generic.List<string>();
        foreach (var x in values) {
            string prefix = System.Convert.ToString(string.Concat(System.Linq.Enumerable.Repeat(" ", System.Convert.ToInt32(indent_i * (level + 1)))));
            string value_txt = System.Convert.ToString(_dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level + 1));
            inner.Add(prefix + value_txt);
        }
        return "[\n" + _join_strs(inner, _COMMA_NL) + "\n" + string.Concat(System.Linq.Enumerable.Repeat(" ", System.Convert.ToInt32(indent_i * level))) + "]";
    }
    
    public static string _dump_json_dict(System.Collections.Generic.Dictionary<string, object> values, bool ensure_ascii, long? indent, string item_sep, string key_sep, long level)
    {
        if (((values).Count) == (0)) {
            return "{}";
        }
        if ((indent) == (null)) {
            System.Collections.Generic.List<string> parts = new System.Collections.Generic.List<string>();
            foreach (var __it_2 in values) {
            var k = __it_2.Key;
            var x = __it_2.Value;
                string k_txt = _escape_str(System.Convert.ToString(k), ensure_ascii);
                string v_txt = System.Convert.ToString(_dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level));
                parts.Add(k_txt + key_sep + v_txt);
            }
            return "{" + _join_strs(parts, item_sep) + "}";
        }
        long indent_i = _json_indent_value(indent);
        System.Collections.Generic.List<string> inner = new System.Collections.Generic.List<string>();
        foreach (var __it_3 in values) {
        var k = __it_3.Key;
        var x = __it_3.Value;
            string prefix = System.Convert.ToString(string.Concat(System.Linq.Enumerable.Repeat(" ", System.Convert.ToInt32(indent_i * (level + 1)))));
            string k_txt = _escape_str(System.Convert.ToString(k), ensure_ascii);
            string v_txt = System.Convert.ToString(_dump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level + 1));
            inner.Add(prefix + k_txt + key_sep + v_txt);
        }
        return "{\n" + _join_strs(inner, _COMMA_NL) + "\n" + string.Concat(System.Linq.Enumerable.Repeat(" ", System.Convert.ToInt32(indent_i * level))) + "}";
    }
    
    public static string _dump_json_value(object v, bool ensure_ascii, long? indent, string item_sep, string key_sep, long level)
    {
        if ((v) == (null)) {
            return "null";
        }
        if (Pytra.CsModule.py_runtime.py_runtime_value_isinstance(v, Pytra.CsModule.py_runtime.PYTRA_TID_BOOL)) {
            bool raw_b = Pytra.CsModule.py_runtime.py_bool(v);
            return (raw_b ? "true" : "false");
        }
        if (Pytra.CsModule.py_runtime.py_runtime_value_isinstance(v, Pytra.CsModule.py_runtime.PYTRA_TID_INT)) {
            return System.Convert.ToString(v);
        }
        if (Pytra.CsModule.py_runtime.py_runtime_value_isinstance(v, Pytra.CsModule.py_runtime.PYTRA_TID_FLOAT)) {
            return System.Convert.ToString(v);
        }
        if (Pytra.CsModule.py_runtime.py_runtime_value_isinstance(v, Pytra.CsModule.py_runtime.PYTRA_TID_STR)) {
            return _escape_str(v, ensure_ascii);
        }
        if (Pytra.CsModule.py_runtime.py_runtime_value_isinstance(v, Pytra.CsModule.py_runtime.PYTRA_TID_LIST)) {
            System.Collections.Generic.List<object> as_list = new System.Collections.Generic.List<object>(v);
            return _dump_json_list(as_list, ensure_ascii, indent, item_sep, key_sep, level);
        }
        if (Pytra.CsModule.py_runtime.py_runtime_value_isinstance(v, Pytra.CsModule.py_runtime.PYTRA_TID_DICT)) {
            System.Collections.Generic.Dictionary<string, object> as_dict = Program.PytraDictStringObjectFromAny(v);
            return _dump_json_dict(as_dict, ensure_ascii, indent, item_sep, key_sep, level);
        }
        throw new System.Exception("json.dumps unsupported type");
    return default(string);
    }
    
    public static string dumps(object obj, bool ensure_ascii = true, long? indent = null, (string, string) separators = null)
    {
        string item_sep = ",";
        string key_sep = ((indent) == (null) ? ":" : ": ");
        if ((separators) != (null)) {
            var __tmp_4 = separators;
            item_sep = __tmp_4.Item1;
            key_sep = __tmp_4.Item2;
        }
        return _dump_json_value(obj, ensure_ascii, indent, item_sep, key_sep, 0);
    }
    
    public static void Main(string[] args)
    {
            string _EMPTY = "";
            string _COMMA_NL = ",\n";
            string _HEX_DIGITS = "0123456789abcdef";
    }
    
    public static System.Collections.Generic.Dictionary<string, object> PytraDictStringObjectFromAny(object source)
    {
        if (source is System.Collections.Generic.Dictionary<string, object> typed)
        {
            return new System.Collections.Generic.Dictionary<string, object>(typed);
        }
        var outv = new System.Collections.Generic.Dictionary<string, object>();
        var dictRaw = source as System.Collections.IDictionary;
        if (dictRaw == null)
        {
            return outv;
        }
        foreach (System.Collections.DictionaryEntry ent in dictRaw)
        {
            string key = System.Convert.ToString(ent.Key);
            if (key == null || key == "")
            {
                continue;
            }
            outv[key] = ent.Value;
        }
        return outv;
    }
}
