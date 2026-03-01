using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace Pytra.CsModule
{
    // Minimal JSON runtime for selfhost/transpiler paths.
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

        public static object loads(string text)
        {
            return new JsonParser(text).Parse();
        }

        private static bool IsNumericType(object obj)
        {
            if (obj == null)
            {
                return false;
            }
            TypeCode tc = Type.GetTypeCode(obj.GetType());
            return tc == TypeCode.Byte
                || tc == TypeCode.SByte
                || tc == TypeCode.Int16
                || tc == TypeCode.UInt16
                || tc == TypeCode.Int32
                || tc == TypeCode.UInt32
                || tc == TypeCode.Int64
                || tc == TypeCode.UInt64
                || tc == TypeCode.Single
                || tc == TypeCode.Double
                || tc == TypeCode.Decimal;
        }

        private static string EscapeString(string text)
        {
            string src = text ?? string.Empty;
            var sb = new StringBuilder();
            int i = 0;
            while (i < src.Length)
            {
                char ch = src[i];
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
                else if (ch < ' ')
                {
                    sb.Append("\\u");
                    sb.Append(((int)ch).ToString("X4", CultureInfo.InvariantCulture));
                }
                else
                {
                    sb.Append(ch);
                }
                i += 1;
            }
            return sb.ToString();
        }

        private static string SerializeValue(object obj)
        {
            if (obj == null)
            {
                return "null";
            }
            if (obj is bool)
            {
                return ((bool)obj) ? "true" : "false";
            }
            if (obj is string)
            {
                return "\"" + EscapeString((string)obj) + "\"";
            }
            if (obj is char)
            {
                return "\"" + EscapeString(new string((char)obj, 1)) + "\"";
            }
            if (IsNumericType(obj))
            {
                IFormattable fmtn = obj as IFormattable;
                if (fmtn != null)
                {
                    return fmtn.ToString(null, CultureInfo.InvariantCulture);
                }
                return Convert.ToString(obj, CultureInfo.InvariantCulture);
            }

            var dict = obj as Dictionary<string, object>;
            if (dict != null)
            {
                var sbObj = new StringBuilder();
                sbObj.Append('{');
                bool firstObj = true;
                foreach (KeyValuePair<string, object> kv in dict)
                {
                    if (!firstObj)
                    {
                        sbObj.Append(',');
                    }
                    firstObj = false;
                    sbObj.Append('"');
                    sbObj.Append(EscapeString(kv.Key ?? string.Empty));
                    sbObj.Append('"');
                    sbObj.Append(':');
                    sbObj.Append(SerializeValue(kv.Value));
                }
                sbObj.Append('}');
                return sbObj.ToString();
            }

            IDictionary idict = obj as IDictionary;
            if (idict != null)
            {
                var sbMap = new StringBuilder();
                sbMap.Append('{');
                bool firstMap = true;
                foreach (DictionaryEntry de in idict)
                {
                    if (!firstMap)
                    {
                        sbMap.Append(',');
                    }
                    firstMap = false;
                    string k = Convert.ToString(de.Key, CultureInfo.InvariantCulture) ?? string.Empty;
                    sbMap.Append('"');
                    sbMap.Append(EscapeString(k));
                    sbMap.Append('"');
                    sbMap.Append(':');
                    sbMap.Append(SerializeValue(de.Value));
                }
                sbMap.Append('}');
                return sbMap.ToString();
            }

            IEnumerable seq = obj as IEnumerable;
            if (seq != null)
            {
                var sbArr = new StringBuilder();
                sbArr.Append('[');
                bool firstArr = true;
                foreach (object item in seq)
                {
                    if (!firstArr)
                    {
                        sbArr.Append(',');
                    }
                    firstArr = false;
                    sbArr.Append(SerializeValue(item));
                }
                sbArr.Append(']');
                return sbArr.ToString();
            }

            string fallback = Convert.ToString(obj, CultureInfo.InvariantCulture) ?? string.Empty;
            return "\"" + EscapeString(fallback) + "\"";
        }

        public static string dumps(object obj)
        {
            return SerializeValue(obj);
        }
    }
}
