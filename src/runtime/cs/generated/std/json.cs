// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/json.py
// generated-by: tools/gen_runtime_from_manifest.py

using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace Pytra.CsModule
{
    public class JsonObj
    {
        public static readonly long PYTRA_TYPE_ID = Pytra.CsModule.py_runtime.py_register_class_type(Pytra.CsModule.py_runtime.PYTRA_TID_OBJECT);
        public Dictionary<string, object> raw;

        public JsonObj(Dictionary<string, object> raw)
        {
            this.raw = raw ?? new Dictionary<string, object>();
        }

        public JsonValue get(string key)
        {
            object value;
            if (!this.raw.TryGetValue(key, out value))
            {
                return null;
            }
            return new JsonValue(value);
        }

        public JsonObj get_obj(string key)
        {
            JsonValue value = this.get(key);
            return value == null ? null : value.as_obj();
        }

        public JsonArr get_arr(string key)
        {
            JsonValue value = this.get(key);
            return value == null ? null : value.as_arr();
        }

        public string get_str(string key)
        {
            JsonValue value = this.get(key);
            return value == null ? null : value.as_str();
        }

        public long? get_int(string key)
        {
            JsonValue value = this.get(key);
            return value == null ? null : value.as_int();
        }

        public double? get_float(string key)
        {
            JsonValue value = this.get(key);
            return value == null ? null : value.as_float();
        }

        public bool? get_bool(string key)
        {
            JsonValue value = this.get(key);
            return value == null ? null : value.as_bool();
        }
    }

    public class JsonArr
    {
        public static readonly long PYTRA_TYPE_ID = Pytra.CsModule.py_runtime.py_register_class_type(Pytra.CsModule.py_runtime.PYTRA_TID_OBJECT);
        public List<object> raw;

        public JsonArr(List<object> raw)
        {
            this.raw = raw ?? new List<object>();
        }

        public JsonValue get(long index)
        {
            if (index < 0 || index >= this.raw.Count)
            {
                return null;
            }
            return new JsonValue(this.raw[(int)index]);
        }

        public JsonObj get_obj(long index)
        {
            JsonValue value = this.get(index);
            return value == null ? null : value.as_obj();
        }

        public JsonArr get_arr(long index)
        {
            JsonValue value = this.get(index);
            return value == null ? null : value.as_arr();
        }

        public string get_str(long index)
        {
            JsonValue value = this.get(index);
            return value == null ? null : value.as_str();
        }

        public long? get_int(long index)
        {
            JsonValue value = this.get(index);
            return value == null ? null : value.as_int();
        }

        public double? get_float(long index)
        {
            JsonValue value = this.get(index);
            return value == null ? null : value.as_float();
        }

        public bool? get_bool(long index)
        {
            JsonValue value = this.get(index);
            return value == null ? null : value.as_bool();
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
            return json.IsObjectValue(this.raw) ? new JsonObj(json.DictStringObjectFromAny(this.raw)) : null;
        }

        public JsonArr as_arr()
        {
            return json.IsArrayValue(this.raw) ? new JsonArr(json.ListObjectFromAny(this.raw)) : null;
        }

        public string as_str()
        {
            return this.raw as string;
        }

        public long? as_int()
        {
            if (this.raw is bool)
            {
                return null;
            }
            if (this.raw is int)
            {
                return Convert.ToInt64((int)this.raw, CultureInfo.InvariantCulture);
            }
            if (this.raw is long)
            {
                return (long)this.raw;
            }
            return null;
        }

        public double? as_float()
        {
            if (this.raw is float)
            {
                return Convert.ToDouble((float)this.raw, CultureInfo.InvariantCulture);
            }
            if (this.raw is double)
            {
                return (double)this.raw;
            }
            return null;
        }

        public bool? as_bool()
        {
            if (this.raw is bool)
            {
                return (bool)this.raw;
            }
            return null;
        }
    }

    public static class json
    {
        private sealed class JsonParser
        {
            private readonly string _text;
            private readonly int _n;
            private int _i;

            public JsonParser(string text)
            {
                _text = text ?? string.Empty;
                _n = _text.Length;
                _i = 0;
            }

            public object Parse()
            {
                SkipWs();
                object value = ParseValue();
                SkipWs();
                if (_i != _n)
                {
                    throw new Exception("invalid json: trailing characters");
                }
                return value;
            }

            private void SkipWs()
            {
                while (_i < _n && IsWs(_text[_i]))
                {
                    _i += 1;
                }
            }

            private bool Peek(char ch)
            {
                return _i < _n && _text[_i] == ch;
            }

            private void Expect(char ch)
            {
                if (!Peek(ch))
                {
                    throw new Exception("invalid json: expected '" + ch + "'");
                }
                _i += 1;
            }

            private bool MatchLiteral(string lit)
            {
                if (_i + lit.Length > _n)
                {
                    return false;
                }
                if (string.CompareOrdinal(_text, _i, lit, 0, lit.Length) != 0)
                {
                    return false;
                }
                _i += lit.Length;
                return true;
            }

            private object ParseValue()
            {
                if (_i >= _n)
                {
                    throw new Exception("invalid json: unexpected end");
                }
                char ch = _text[_i];
                if (ch == '{')
                {
                    return ParseObject();
                }
                if (ch == '[')
                {
                    return ParseArray();
                }
                if (ch == '"')
                {
                    return ParseString();
                }
                if (MatchLiteral("true"))
                {
                    return true;
                }
                if (MatchLiteral("false"))
                {
                    return false;
                }
                if (MatchLiteral("null"))
                {
                    return null;
                }
                return ParseNumber();
            }

            private Dictionary<string, object> ParseObject()
            {
                var outv = new Dictionary<string, object>();
                Expect('{');
                SkipWs();
                if (Peek('}'))
                {
                    _i += 1;
                    return outv;
                }
                while (true)
                {
                    SkipWs();
                    if (!Peek('"'))
                    {
                        throw new Exception("invalid json object key");
                    }
                    string key = ParseString();
                    SkipWs();
                    Expect(':');
                    SkipWs();
                    outv[key] = ParseValue();
                    SkipWs();
                    if (Peek('}'))
                    {
                        _i += 1;
                        return outv;
                    }
                    Expect(',');
                }
            }

            private List<object> ParseArray()
            {
                var outv = new List<object>();
                Expect('[');
                SkipWs();
                if (Peek(']'))
                {
                    _i += 1;
                    return outv;
                }
                while (true)
                {
                    SkipWs();
                    outv.Add(ParseValue());
                    SkipWs();
                    if (Peek(']'))
                    {
                        _i += 1;
                        return outv;
                    }
                    Expect(',');
                }
            }

            private string ParseString()
            {
                Expect('"');
                var sb = new StringBuilder();
                while (_i < _n)
                {
                    char ch = _text[_i++];
                    if (ch == '"')
                    {
                        return sb.ToString();
                    }
                    if (ch != '\\')
                    {
                        sb.Append(ch);
                        continue;
                    }
                    if (_i >= _n)
                    {
                        throw new Exception("invalid json string escape");
                    }
                    char esc = _text[_i++];
                    if (esc == '"')
                    {
                        sb.Append('"');
                    }
                    else if (esc == '\\')
                    {
                        sb.Append('\\');
                    }
                    else if (esc == '/')
                    {
                        sb.Append('/');
                    }
                    else if (esc == 'b')
                    {
                        sb.Append('\b');
                    }
                    else if (esc == 'f')
                    {
                        sb.Append('\f');
                    }
                    else if (esc == 'n')
                    {
                        sb.Append('\n');
                    }
                    else if (esc == 'r')
                    {
                        sb.Append('\r');
                    }
                    else if (esc == 't')
                    {
                        sb.Append('\t');
                    }
                    else if (esc == 'u')
                    {
                        if (_i + 4 > _n)
                        {
                            throw new Exception("invalid json unicode escape");
                        }
                        string hx = _text.Substring(_i, 4);
                        _i += 4;
                        sb.Append((char)IntFromHex4(hx));
                    }
                    else
                    {
                        throw new Exception("invalid json escape");
                    }
                }
                throw new Exception("invalid json string: unexpected end");
            }

            private object ParseNumber()
            {
                int start = _i;
                if (Peek('-'))
                {
                    _i += 1;
                }
                if (_i >= _n)
                {
                    throw new Exception("invalid json number");
                }
                if (Peek('0'))
                {
                    _i += 1;
                }
                else
                {
                    if (!IsDigit(_text[_i]))
                    {
                        throw new Exception("invalid json number");
                    }
                    while (_i < _n && IsDigit(_text[_i]))
                    {
                        _i += 1;
                    }
                }
                bool isFloat = false;
                if (_i < _n && _text[_i] == '.')
                {
                    isFloat = true;
                    _i += 1;
                    if (_i >= _n || !IsDigit(_text[_i]))
                    {
                        throw new Exception("invalid json fraction");
                    }
                    while (_i < _n && IsDigit(_text[_i]))
                    {
                        _i += 1;
                    }
                }
                if (_i < _n && (_text[_i] == 'e' || _text[_i] == 'E'))
                {
                    isFloat = true;
                    _i += 1;
                    if (_i < _n && (_text[_i] == '+' || _text[_i] == '-'))
                    {
                        _i += 1;
                    }
                    if (_i >= _n || !IsDigit(_text[_i]))
                    {
                        throw new Exception("invalid json exponent");
                    }
                    while (_i < _n && IsDigit(_text[_i]))
                    {
                        _i += 1;
                    }
                }
                string token = _text.Substring(start, _i - start);
                if (isFloat)
                {
                    return Convert.ToDouble(token, CultureInfo.InvariantCulture);
                }
                return Convert.ToInt64(token, CultureInfo.InvariantCulture);
            }
        }

        private static bool IsWs(char ch)
        {
            return ch == ' ' || ch == '\t' || ch == '\r' || ch == '\n';
        }

        private static bool IsDigit(char ch)
        {
            return ch >= '0' && ch <= '9';
        }

        private static int HexValue(char ch)
        {
            if (ch >= '0' && ch <= '9')
            {
                return ch - '0';
            }
            if (ch >= 'a' && ch <= 'f')
            {
                return 10 + (ch - 'a');
            }
            if (ch >= 'A' && ch <= 'F')
            {
                return 10 + (ch - 'A');
            }
            throw new Exception("invalid json unicode escape");
        }

        private static int IntFromHex4(string hx)
        {
            if (hx == null || hx.Length != 4)
            {
                throw new Exception("invalid json unicode escape");
            }
            int v0 = HexValue(hx[0]);
            int v1 = HexValue(hx[1]);
            int v2 = HexValue(hx[2]);
            int v3 = HexValue(hx[3]);
            return (v0 * 4096) + (v1 * 256) + (v2 * 16) + v3;
        }

        public static bool IsObjectValue(object value)
        {
            return value is IDictionary && !(value is IList);
        }

        public static bool IsArrayValue(object value)
        {
            return value is IList && !(value is string) && !(value is IDictionary);
        }

        public static Dictionary<string, object> DictStringObjectFromAny(object source)
        {
            if (source is Dictionary<string, object>)
            {
                return new Dictionary<string, object>((Dictionary<string, object>)source);
            }
            var outv = new Dictionary<string, object>();
            var dictRaw = source as IDictionary;
            if (dictRaw == null)
            {
                return outv;
            }
            foreach (DictionaryEntry ent in dictRaw)
            {
                string key = Convert.ToString(ent.Key, CultureInfo.InvariantCulture);
                if (key == null)
                {
                    continue;
                }
                outv[key] = ent.Value;
            }
            return outv;
        }

        public static List<object> ListObjectFromAny(object source)
        {
            if (source is List<object>)
            {
                return new List<object>((List<object>)source);
            }
            var outv = new List<object>();
            if (source == null || source is string)
            {
                return outv;
            }
            var seq = source as IEnumerable;
            if (seq == null)
            {
                return outv;
            }
            foreach (object item in seq)
            {
                outv.Add(item);
            }
            return outv;
        }

        private static object Unwrap(object value)
        {
            if (value is JsonValue)
            {
                return ((JsonValue)value).raw;
            }
            if (value is JsonObj)
            {
                return ((JsonObj)value).raw;
            }
            if (value is JsonArr)
            {
                return ((JsonArr)value).raw;
            }
            return value;
        }

        public static object loads(string text)
        {
            return new JsonParser(text).Parse();
        }

        public static JsonObj loads_obj(string text)
        {
            object value = loads(text);
            return IsObjectValue(value) ? new JsonObj(DictStringObjectFromAny(value)) : null;
        }

        public static JsonArr loads_arr(string text)
        {
            object value = loads(text);
            return IsArrayValue(value) ? new JsonArr(ListObjectFromAny(value)) : null;
        }

        private static string EscapeString(string text, bool ensureAscii)
        {
            string src = text ?? string.Empty;
            var sb = new StringBuilder();
            sb.Append('"');
            int i = 0;
            while (i < src.Length)
            {
                char ch = src[i];
                int code = ch;
                if (ch == '"')
                {
                    sb.Append("\\\"");
                }
                else if (ch == '\\')
                {
                    sb.Append("\\\\");
                }
                else if (ch == '\b')
                {
                    sb.Append("\\b");
                }
                else if (ch == '\f')
                {
                    sb.Append("\\f");
                }
                else if (ch == '\n')
                {
                    sb.Append("\\n");
                }
                else if (ch == '\r')
                {
                    sb.Append("\\r");
                }
                else if (ch == '\t')
                {
                    sb.Append("\\t");
                }
                else if (ensureAscii && code > 0x7F)
                {
                    sb.Append("\\u");
                    sb.Append(code.ToString("x4", CultureInfo.InvariantCulture));
                }
                else
                {
                    sb.Append(ch);
                }
                i += 1;
            }
            sb.Append('"');
            return sb.ToString();
        }

        private static int? NormalizeIndent(long? indent)
        {
            if (!indent.HasValue)
            {
                return null;
            }
            long value = indent.Value;
            if (value < 0)
            {
                value = 0;
            }
            return (int)value;
        }

        private static string RepeatIndent(int indent, int level)
        {
            return new string(' ', indent * level);
        }

        private static string DumpList(List<object> values, bool ensureAscii, int? indent, string itemSep, string keySep, int level)
        {
            if (values.Count == 0)
            {
                return "[]";
            }
            var parts = new List<string>();
            foreach (object item in values)
            {
                string dumped = DumpValue(item, ensureAscii, indent, itemSep, keySep, indent.HasValue ? level + 1 : level);
                if (!indent.HasValue)
                {
                    parts.Add(dumped);
                }
                else
                {
                    parts.Add(RepeatIndent(indent.Value, level + 1) + dumped);
                }
            }
            if (!indent.HasValue)
            {
                return "[" + string.Join(itemSep, parts.ToArray()) + "]";
            }
            return "[\n" + string.Join(",\n", parts.ToArray()) + "\n" + RepeatIndent(indent.Value, level) + "]";
        }

        private static string DumpDict(Dictionary<string, object> values, bool ensureAscii, int? indent, string itemSep, string keySep, int level)
        {
            if (values.Count == 0)
            {
                return "{}";
            }
            var parts = new List<string>();
            foreach (KeyValuePair<string, object> kv in values)
            {
                string item = EscapeString(kv.Key ?? string.Empty, ensureAscii)
                    + keySep
                    + DumpValue(kv.Value, ensureAscii, indent, itemSep, keySep, indent.HasValue ? level + 1 : level);
                if (!indent.HasValue)
                {
                    parts.Add(item);
                }
                else
                {
                    parts.Add(RepeatIndent(indent.Value, level + 1) + item);
                }
            }
            if (!indent.HasValue)
            {
                return "{" + string.Join(itemSep, parts.ToArray()) + "}";
            }
            return "{\n" + string.Join(",\n", parts.ToArray()) + "\n" + RepeatIndent(indent.Value, level) + "}";
        }

        private static string DumpValue(object value, bool ensureAscii, int? indent, string itemSep, string keySep, int level)
        {
            value = Unwrap(value);
            if (value == null)
            {
                return "null";
            }
            if (value is bool)
            {
                return ((bool)value) ? "true" : "false";
            }
            if (value is int || value is long)
            {
                return Convert.ToString(value, CultureInfo.InvariantCulture);
            }
            if (value is float || value is double)
            {
                return Convert.ToString(value, CultureInfo.InvariantCulture);
            }
            if (value is string)
            {
                return EscapeString((string)value, ensureAscii);
            }
            if (IsArrayValue(value))
            {
                return DumpList(ListObjectFromAny(value), ensureAscii, indent, itemSep, keySep, level);
            }
            if (IsObjectValue(value))
            {
                return DumpDict(DictStringObjectFromAny(value), ensureAscii, indent, itemSep, keySep, level);
            }
            throw new Exception("json.dumps unsupported type");
        }

        private static string DumpsImpl(object obj, bool ensureAscii, long? indent, bool hasSeparators, string itemSep, string keySep)
        {
            int? indentValue = NormalizeIndent(indent);
            string actualItemSep = hasSeparators ? itemSep : ",";
            string actualKeySep = hasSeparators ? keySep : (indentValue.HasValue ? ": " : ":");
            return DumpValue(obj, ensureAscii, indentValue, actualItemSep, actualKeySep, 0);
        }

        public static string dumps(object obj)
        {
            return DumpsImpl(obj, true, null, false, ",", ":");
        }

        public static string dumps(object obj, bool ensure_ascii)
        {
            return DumpsImpl(obj, ensure_ascii, null, false, ",", ":");
        }

        public static string dumps(object obj, bool ensure_ascii, long? indent)
        {
            return DumpsImpl(obj, ensure_ascii, indent, false, ",", ":");
        }

        public static string dumps(object obj, bool ensure_ascii, (string, string) separators)
        {
            return DumpsImpl(obj, ensure_ascii, null, true, separators.Item1, separators.Item2);
        }

        public static string dumps(object obj, bool ensure_ascii, long? indent, (string, string) separators)
        {
            return DumpsImpl(obj, ensure_ascii, indent, true, separators.Item1, separators.Item2);
        }

        public static string dumps(object obj, bool ensure_ascii, (string, string) separators, long? indent)
        {
            return DumpsImpl(obj, ensure_ascii, indent, true, separators.Item1, separators.Item2);
        }
    }
}
