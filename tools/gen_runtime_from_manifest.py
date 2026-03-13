#!/usr/bin/env python3
"""Generate runtime artifacts from a declarative manifest.

Source of truth is canonical Python modules under ``src/pytra``.
Per-target outputs and optional postprocess hooks are defined in
``tools/runtime_generation_manifest.json``.
"""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from toolchain.compiler.backend_registry_static import (
    emit_source,
    get_backend_spec,
    lower_ir,
    optimize_ir,
    resolve_layer_options,
)
from toolchain.frontends.python_frontend import load_east3_document


DEFAULT_MANIFEST = ROOT / "tools" / "runtime_generation_manifest.json"
GENERATED_BY = "tools/gen_runtime_from_manifest.py"

COMMENT_PREFIX: dict[str, str] = {
    "cpp": "//",
    "rs": "//",
    "cs": "//",
    "js": "//",
    "ts": "//",
    "go": "//",
    "java": "//",
    "swift": "//",
    "kotlin": "//",
    "ruby": "#",
    "lua": "--",
    "scala": "//",
    "php": "//",
    "nim": "#",
}


@dataclass(frozen=True)
class GenerationItem:
    item_id: str
    source_rel: str
    target: str
    output_rel: str
    postprocess: str
    helper_name: str


def parse_csv_arg(raw: str) -> list[str]:
    parts = [p.strip() for p in raw.split(",")]
    return [p for p in parts if p != ""]


def _to_str(value: object) -> str:
    return value if isinstance(value, str) else ""


def load_manifest_items(manifest_path: Path) -> list[GenerationItem]:
    doc = json.loads(manifest_path.read_text(encoding="utf-8"))
    items_any = doc.get("items")
    if not isinstance(items_any, list):
        raise RuntimeError("manifest.items must be a list")
    out: list[GenerationItem] = []
    for item_obj in items_any:
        if not isinstance(item_obj, dict):
            continue
        item_id = _to_str(item_obj.get("id"))
        source_rel = _to_str(item_obj.get("source"))
        if item_id == "" or source_rel == "":
            raise RuntimeError("manifest item requires id/source")
        targets_any = item_obj.get("targets")
        if not isinstance(targets_any, list):
            raise RuntimeError("manifest item targets must be a list: " + item_id)
        for target_obj in targets_any:
            if not isinstance(target_obj, dict):
                continue
            target = _to_str(target_obj.get("target"))
            output_rel = _to_str(target_obj.get("output"))
            postprocess = _to_str(target_obj.get("postprocess"))
            helper_name = _to_str(target_obj.get("helper_name"))
            if target == "" or output_rel == "":
                raise RuntimeError("manifest target entry requires target/output: " + item_id)
            out.append(
                GenerationItem(
                    item_id=item_id,
                    source_rel=source_rel,
                    target=target,
                    output_rel=output_rel,
                    postprocess=postprocess,
                    helper_name=helper_name,
                )
            )
    return out


def resolve_targets(raw_targets: str, all_items: list[GenerationItem]) -> list[str]:
    known: list[str] = sorted({item.target for item in all_items})
    if raw_targets.strip() in {"", "all"}:
        return known
    targets = parse_csv_arg(raw_targets)
    unknown = [t for t in targets if t not in known]
    if len(unknown) > 0:
        raise RuntimeError("unknown targets: " + ", ".join(unknown))
    return targets


def resolve_item_ids(raw_items: str, all_items: list[GenerationItem]) -> list[str]:
    known: list[str] = sorted({item.item_id for item in all_items})
    if raw_items.strip() in {"", "all"}:
        return known
    ids = parse_csv_arg(raw_items)
    unknown = [x for x in ids if x not in known]
    if len(unknown) > 0:
        raise RuntimeError("unknown item id(s): " + ", ".join(unknown))
    return ids


def build_generation_plan(
    all_items: list[GenerationItem],
    targets: list[str],
    item_ids: list[str],
) -> list[GenerationItem]:
    target_set = set(targets)
    id_set = set(item_ids)
    out: list[GenerationItem] = []
    for item in all_items:
        if item.target not in target_set:
            continue
        if item.item_id not in id_set:
            continue
        out.append(item)
    return out


def run_py2x(target: str, source_rel: str, output_rel: str) -> str:
    src = ROOT / source_rel
    spec = get_backend_spec(target)
    target_lang = str(spec.get("target_lang", target))
    east_doc = load_east3_document(
        src,
        parser_backend="self_hosted",
        target_lang=target_lang,
    )
    lower_options = resolve_layer_options(spec, "lower", {})
    optimizer_options = resolve_layer_options(spec, "optimizer", {})
    emitter_options = resolve_layer_options(spec, "emitter", {})
    ir = lower_ir(spec, east_doc, lower_options)
    ir = optimize_ir(spec, ir, optimizer_options)
    out_name = Path(output_rel).name
    out_suffix = Path(output_rel).suffix
    if out_name == "":
        out_name = "tmp" + out_suffix
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / out_name
        out_text = emit_source(spec, ir, out, emitter_options)
        if out_text == "":
            if out.exists():
                return out.read_text(encoding="utf-8")
            raise RuntimeError(
                "runtime generation backend emitted no inline text and wrote no file: "
                + target
                + " -> "
                + output_rel
            )
        return out_text


def _skip_cs_main_method(body_lines: list[str]) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(body_lines):
        line = body_lines[i]
        if line.strip().startswith("public static void Main("):
            brace_depth = 0
            while i < len(body_lines):
                cur = body_lines[i]
                brace_depth += cur.count("{")
                brace_depth -= cur.count("}")
                i += 1
                if brace_depth <= 0 and cur.strip() == "}":
                    break
            continue
        out.append(line)
        i += 1
    return out


def rewrite_cs_program_to_helper(cs_src: str, helper_name: str) -> str:
    lines = cs_src.splitlines()
    using_lines: list[str] = []
    class_start = -1
    class_end = -1

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("using ") and line.strip() != "using Pytra.CsModule;":
            using_lines.append(line)
        if line.strip() == "public static class Program":
            class_start = i
            break
        i += 1
    if class_start < 0:
        raise RuntimeError("generated C# does not contain Program class")

    brace_depth = 0
    i = class_start
    seen_open = False
    while i < len(lines):
        cur = lines[i]
        if "{" in cur:
            seen_open = True
        brace_depth += cur.count("{")
        brace_depth -= cur.count("}")
        if seen_open and brace_depth == 0:
            class_end = i
            break
        i += 1
    if class_end < 0:
        raise RuntimeError("failed to locate end of Program class")

    body_lines = lines[class_start + 2 : class_end]
    body_lines = _skip_cs_main_method(body_lines)
    out: list[str] = []
    out.extend(using_lines)
    if len(using_lines) > 0:
        out.append("")
    out.append("namespace Pytra.CsModule")
    out.append("{")
    out.append("    public static class " + helper_name)
    out.append("    {")
    for line in body_lines:
        if line.strip() == "":
            out.append("")
        else:
            out.append("    " + line)
    out.append("    }")
    out.append("}")
    out.append("")
    text = "\n".join(out)
    return text.replace("Program.", helper_name + ".")


def rewrite_cs_std_native_owner_wrapper(cs_src: str, helper_name: str) -> str:
    text = rewrite_cs_program_to_helper(cs_src, helper_name)
    native_owner = helper_name + "_native"
    rewritten = re.sub(
        r"return __[A-Za-z_][A-Za-z0-9_]*\.",
        "return " + native_owner + ".",
        text,
    )
    if rewritten == text:
        raise RuntimeError(
            "generated C# std/" + helper_name + " wrapper is missing extern return delegation"
        )
    return rewritten


def rewrite_cs_std_math_live_wrapper(cs_src: str) -> str:
    text = rewrite_cs_program_to_helper(cs_src, "math")
    text = text.replace(
        "    public static class math\n    {\n",
        "    public static class math\n    {\n"
        "        public static double pi { get { return math_native.pi; } }\n"
        "        public static double e { get { return math_native.e; } }\n\n",
        1,
    )
    replacements = {
        "return __m.sqrt(x);": "return math_native.sqrt(x);",
        "return __m.sin(x);": "return math_native.sin(x);",
        "return __m.cos(x);": "return math_native.cos(x);",
        "return __m.tan(x);": "return math_native.tan(x);",
        "return __m.exp(x);": "return math_native.exp(x);",
        "return __m.log(x);": "return math_native.log(x);",
        "return __m.log10(x);": "return math_native.log10(x);",
        "return __m.fabs(x);": "return math_native.fabs(x);",
        "return __m.floor(x);": "return math_native.floor(x);",
        "return __m.ceil(x);": "return math_native.ceil(x);",
        "return __m.pow(x, y);": "return math_native.pow(x, y);",
    }
    for before, after in replacements.items():
        text = text.replace(before, after)
    if "__m." in text or "py_extern(" in text or "Math." in text:
        raise RuntimeError("generated C# std/math wrapper still contains extern/math runtime residue")
    return text


def rewrite_cs_std_json_live_wrapper(cs_src: str) -> str:
    required_fragments = (
        "public class JsonObj",
        "public class JsonArr",
        "public class JsonValue",
        "public static object loads(string text)",
        "public static JsonObj loads_obj(string text)",
        "public static JsonArr loads_arr(string text)",
        "public static string dumps(",
    )
    for fragment in required_fragments:
        if fragment not in cs_src:
            raise RuntimeError("generated C# std/json wrapper is missing: " + fragment)
    return """
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
                    if (ch != '\\\\')
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
                    else if (esc == '\\\\')
                    {
                        sb.Append('\\\\');
                    }
                    else if (esc == '/')
                    {
                        sb.Append('/');
                    }
                    else if (esc == 'b')
                    {
                        sb.Append('\\b');
                    }
                    else if (esc == 'f')
                    {
                        sb.Append('\\f');
                    }
                    else if (esc == 'n')
                    {
                        sb.Append('\\n');
                    }
                    else if (esc == 'r')
                    {
                        sb.Append('\\r');
                    }
                    else if (esc == 't')
                    {
                        sb.Append('\\t');
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
            return ch == ' ' || ch == '\\t' || ch == '\\r' || ch == '\\n';
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
                    sb.Append("\\\\\\"");
                }
                else if (ch == '\\\\')
                {
                    sb.Append("\\\\\\\\");
                }
                else if (ch == '\\b')
                {
                    sb.Append("\\\\b");
                }
                else if (ch == '\\f')
                {
                    sb.Append("\\\\f");
                }
                else if (ch == '\\n')
                {
                    sb.Append("\\\\n");
                }
                else if (ch == '\\r')
                {
                    sb.Append("\\\\r");
                }
                else if (ch == '\\t')
                {
                    sb.Append("\\\\t");
                }
                else if (ensureAscii && code > 0x7F)
                {
                    sb.Append("\\\\u");
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
            return "[\\n" + string.Join(",\\n", parts.ToArray()) + "\\n" + RepeatIndent(indent.Value, level) + "]";
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
            return "{\\n" + string.Join(",\\n", parts.ToArray()) + "\\n" + RepeatIndent(indent.Value, level) + "}";
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
""".lstrip()


def rewrite_cs_std_pathlib_live_wrapper(cs_src: str) -> str:
    required_fragments = (
        "public class Path",
        "public Path __truediv__(string rhs)",
        "public Path parent()",
        "public string name()",
        "public string stem()",
        "public Path resolve()",
        "public bool exists()",
        'public string read_text(string encoding = "utf-8")',
        'public long write_text(string text, string encoding = "utf-8")',
        "public System.Collections.Generic.List<Path> glob(string pattern)",
        "public static Path cwd()",
    )
    for fragment in required_fragments:
        if fragment not in cs_src:
            raise RuntimeError("generated C# std/pathlib wrapper is missing: " + fragment)
    return """
using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace Pytra.CsModule
{
    public class py_path
    {
        public static readonly long PYTRA_TYPE_ID = py_runtime.py_register_class_type(py_runtime.PYTRA_TID_OBJECT);
        private readonly string _value;

        public py_path(string value)
        {
            _value = value ?? string.Empty;
        }

        private static string NormalizeParentText(string value)
        {
            return string.IsNullOrEmpty(value) ? "." : value;
        }

        private static Encoding ResolveEncoding(string encoding)
        {
            if (string.IsNullOrEmpty(encoding) || encoding == "utf-8")
            {
                return new UTF8Encoding(false);
            }
            return Encoding.GetEncoding(encoding);
        }

        public string __str__()
        {
            return _value;
        }

        public string __repr__()
        {
            return "Path(" + _value + ")";
        }

        public string __fspath__()
        {
            return _value;
        }

        public static py_path operator /(py_path lhs, string rhs)
        {
            string basePath = lhs == null ? string.Empty : lhs._value;
            return new py_path(Path.Combine(basePath, rhs ?? string.Empty));
        }

        public py_path __truediv__(string rhs)
        {
            return this / rhs;
        }

        public py_path parent()
        {
            return new py_path(NormalizeParentText(Path.GetDirectoryName(_value)));
        }

        public List<py_path> parents()
        {
            List<py_path> py_out = new List<py_path>();
            string current = NormalizeParentText(Path.GetDirectoryName(_value));
            while (true)
            {
                py_out.Add(new py_path(current));
                string nextCurrent = NormalizeParentText(Path.GetDirectoryName(current));
                if (nextCurrent == current)
                {
                    break;
                }
                current = nextCurrent;
            }
            return py_out;
        }

        public string name()
        {
            return Path.GetFileName(_value) ?? string.Empty;
        }

        public string suffix()
        {
            return Path.GetExtension(name()) ?? string.Empty;
        }

        public string stem()
        {
            return Path.GetFileNameWithoutExtension(name()) ?? string.Empty;
        }

        public py_path resolve()
        {
            string target = string.IsNullOrEmpty(_value) ? "." : _value;
            return new py_path(Path.GetFullPath(target));
        }

        public bool exists()
        {
            return File.Exists(_value) || Directory.Exists(_value);
        }

        public void mkdir(bool parents = false, bool exist_ok = false)
        {
            try
            {
                Directory.CreateDirectory(_value);
            }
            catch
            {
                if (!exist_ok)
                {
                    throw;
                }
            }
        }

        public string read_text(string encoding = "utf-8")
        {
            return File.ReadAllText(_value, ResolveEncoding(encoding));
        }

        public long write_text(string text, string encoding = "utf-8")
        {
            string body = text ?? string.Empty;
            File.WriteAllText(_value, body, ResolveEncoding(encoding));
            return Convert.ToInt64(body.Length);
        }

        public List<py_path> glob(string pattern)
        {
            List<py_path> py_out = new List<py_path>();
            string baseDir = string.IsNullOrEmpty(_value) ? "." : _value;
            if (!Directory.Exists(baseDir))
            {
                return py_out;
            }
            string searchPattern = string.IsNullOrEmpty(pattern) ? "*" : pattern;
            foreach (string item in Directory.GetFileSystemEntries(baseDir, searchPattern))
            {
                py_out.Add(new py_path(item));
            }
            return py_out;
        }

        public static py_path cwd()
        {
            return new py_path(Directory.GetCurrentDirectory());
        }

        public override string ToString()
        {
            return _value;
        }
    }
}
"""


def rewrite_rs_std_time_live_wrapper(rs_src: str) -> str:
    del rs_src
    return """pub fn perf_counter() -> f64 {
    crate::py_runtime::perf_counter()
}
"""


def rewrite_rs_std_math_live_wrapper(rs_src: str) -> str:
    del rs_src
    return """pub const pi: f64 = ::std::f64::consts::PI;
pub const e: f64 = ::std::f64::consts::E;

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
"""


def rewrite_java_std_time_live_wrapper(java_src: str) -> str:
    return java_src.replace(
        "return __t.perf_counter();",
        "return (double) System.nanoTime() / 1_000_000_000.0;",
    )


def rewrite_java_std_math_live_wrapper(java_src: str) -> str:
    text = java_src
    text = text.replace("public static double pi = extern(math.pi);", "public static double pi = Math.PI;")
    text = text.replace("public static double e = extern(math.e);", "public static double e = Math.E;")
    replacements = {
        "return math.sqrt(x);": "return Math.sqrt(x);",
        "return math.sin(x);": "return Math.sin(x);",
        "return math.cos(x);": "return Math.cos(x);",
        "return math.tan(x);": "return Math.tan(x);",
        "return math.exp(x);": "return Math.exp(x);",
        "return math.log(x);": "return Math.log(x);",
        "return math.log10(x);": "return Math.log10(x);",
        "return math.fabs(x);": "return Math.abs(x);",
        "return math.floor(x);": "return Math.floor(x);",
        "return math.ceil(x);": "return Math.ceil(x);",
        "return math.pow(x, y);": "return Math.pow(x, y);",
    }
    for before, after in replacements.items():
        text = text.replace(before, after)
    return text


def rewrite_js_std_math_live_wrapper(js_src: str) -> str:
    text = _strip_trailing_string_literal_expr(js_src)
    text = text.replace('import { extern } from "./pytra/std.js";\n\n', "")
    text = text.replace('"pytra.std.math: extern-marked math API with Python runtime fallback.";\n', "")
    text = text.replace("let pi = extern(__m.pi);", "const pi = Math.PI;")
    text = text.replace("let e = extern(__m.e);", "const e = Math.E;")
    replacements = {
        "return __m.sqrt(x);": "return Math.sqrt(x);",
        "return __m.sin(x);": "return Math.sin(x);",
        "return __m.cos(x);": "return Math.cos(x);",
        "return __m.tan(x);": "return Math.tan(x);",
        "return __m.exp(x);": "return Math.exp(x);",
        "return __m.log(x);": "return Math.log(x);",
        "return __m.log10(x);": "return Math.log10(x);",
        "return __m.fabs(x);": "return Math.abs(x);",
        "return __m.floor(x);": "return Math.floor(x);",
        "return __m.ceil(x);": "return Math.ceil(x);",
        "return __m.pow(x, y);": "return Math.pow(x, y);",
    }
    for before, after in replacements.items():
        text = text.replace(before, after)
    if "extern(" in text or "__m." in text:
        raise RuntimeError("generated JS std/math wrapper still contains extern/math runtime residue")
    return text.rstrip() + "\n\nmodule.exports = { pi, e, sin, cos, tan, sqrt, exp, log, log10, fabs, floor, ceil, pow };\n"


def _strip_trailing_string_literal_expr(text: str) -> str:
    lines = text.splitlines()
    if len(lines) == 0:
        return text
    literal_re = re.compile(r"""^\s*(["']).*\1;\s*$""")
    while len(lines) > 0 and literal_re.match(lines[-1]):
        lines.pop()
    if len(lines) == 0:
        return ""
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def _remove_block_by_signature(lines: list[str], signature_re: re.Pattern[str]) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if signature_re.match(line.strip()):
            brace_depth = 0
            seen_open = False
            while i < len(lines):
                cur = lines[i]
                if "{" in cur:
                    seen_open = True
                brace_depth += cur.count("{")
                brace_depth -= cur.count("}")
                i += 1
                if seen_open and brace_depth <= 0:
                    break
            continue
        out.append(line)
        i += 1
    return out


def rewrite_js_program_to_cjs_module(js_src: str) -> str:
    js_src = _strip_trailing_string_literal_expr(js_src)
    js_src = re.sub(
        r"\b([A-Za-z_][A-Za-z0-9_]*)\.extend\(([^;\n]+)\);",
        r"\1 = \1.concat(\2);",
        js_src,
    )
    js_src = re.sub(r"(?<!>)>>(?!>)", ">>>", js_src)

    if "module.exports" in js_src:
        return js_src
    names: list[str] = []
    for m in re.finditer(r"(?m)^function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", js_src):
        name = m.group(1)
        if name not in names:
            names.append(name)
    public_names = [name for name in names if not name.startswith("_")]
    if len(public_names) == 0:
        return js_src
    body = js_src.rstrip("\n")
    if "open(" in body and "function open(" not in body:
        prelude = (
            "const fs = require('node:fs');\n"
            "const path = require('node:path');\n"
            "function open(pathLike, mode) {\n"
            "    const filePath = String(pathLike);\n"
            "    const writeMode = String(mode || 'wb');\n"
            "    return {\n"
            "        write(data) {\n"
            "            const bytes = Array.isArray(data) ? data : Array.from(data || []);\n"
            "            fs.mkdirSync(path.dirname(filePath), { recursive: true });\n"
            "            const flag = (writeMode === 'ab' || writeMode === 'a') ? 'a' : 'w';\n"
            "            fs.writeFileSync(filePath, Buffer.from(bytes), { flag });\n"
            "        },\n"
            "        close() {},\n"
            "    };\n"
            "}\n\n"
        )
        body = prelude + body
    exports = "module.exports = {" + ", ".join(public_names) + "};\n"
    return body + "\n\n" + exports


def rewrite_js_ts_built_in_cjs_module(js_src: str) -> str:
    text = _strip_trailing_string_literal_expr(js_src)
    text = re.sub(
        r'^import\s+\{([^}]+)\}\s+from\s+"\.\/(?:pytra|runtime\/js\/native\/built_in)\/py_runtime\.js";$',
        lambda m: 'const {' + m.group(1).strip() + '} = require("../../native/built_in/py_runtime.js");',
        text,
        flags=re.MULTILINE,
    )
    if "./pytra/py_runtime.js" in text or "./runtime/js/native/built_in/py_runtime.js" in text:
        raise RuntimeError("generated JS/TS built_in module still points at staged runtime path")
    return rewrite_js_program_to_cjs_module(text)


def rewrite_js_std_module_runtime_imports(js_src: str, *, module_name: str) -> str:
    text = _strip_trailing_string_literal_expr(js_src)
    replacements = {
        'import { PYTRA_TYPE_ID, PY_TYPE_MAP, PY_TYPE_OBJECT, pyRegisterClassType, pyBool, pyLen } from "./pytra/py_runtime.js";':
            'const { PYTRA_TYPE_ID, PY_TYPE_MAP, PY_TYPE_OBJECT, pyRegisterClassType, pyBool, pyLen } = require("../../native/built_in/py_runtime.js");',
        'import { PYTRA_TYPE_ID, PY_TYPE_MAP, PY_TYPE_OBJECT, pyRegisterClassType, pyBool, pyLen } from "./runtime/js/native/built_in/py_runtime.js";':
            'const { PYTRA_TYPE_ID, PY_TYPE_MAP, PY_TYPE_OBJECT, pyRegisterClassType, pyBool, pyLen } = require("../../native/built_in/py_runtime.js");',
        'import { PYTRA_TYPE_ID, PY_TYPE_OBJECT, pyRegisterClassType } from "./pytra/py_runtime.js";':
            'const { PYTRA_TYPE_ID, PY_TYPE_OBJECT, pyRegisterClassType } = require("../../native/built_in/py_runtime.js");',
        'import { PYTRA_TYPE_ID, PY_TYPE_OBJECT, pyRegisterClassType } from "./runtime/js/native/built_in/py_runtime.js";':
            'const { PYTRA_TYPE_ID, PY_TYPE_OBJECT, pyRegisterClassType } = require("../../native/built_in/py_runtime.js");',
        'import * as sys from "./pytra/std/sys.js";':
            'const sys = require("./sys.js");',
        'import * as sys from "./runtime/js/generated/std/sys.js";':
            'const sys = require("./sys.js");',
        'import * as _math from "./pytra/std/math.js";':
            'const _math = require("./math.js");',
        'import * as _math from "./runtime/js/generated/std/math.js";':
            'const _math = require("./math.js");',
        'import { perf_counter } from "./pytra/std/time.js";':
            'const { perf_counter } = require("./time.js");',
        'import { perf_counter } from "./runtime/js/generated/std/time.js";':
            'const { perf_counter } = require("./time.js");',
    }
    for before, after in replacements.items():
        text = text.replace(before, after)
    if "./pytra/" in text or "./runtime/js/" in text:
        raise RuntimeError("generated JS std/" + module_name + " wrapper still points at staged runtime paths")
    return rewrite_js_program_to_cjs_module(text)


def rewrite_js_std_time_live_wrapper(js_src: str) -> str:
    text = _strip_trailing_string_literal_expr(js_src)
    text = text.replace(
        "return __t.perf_counter();",
        "return Number(process.hrtime.bigint()) / 1_000_000_000;",
    ).rstrip()
    if "function perf_counter(" not in text:
        raise RuntimeError("generated JS std/time wrapper is missing perf_counter()")
    return text + "\n\nconst perfCounter = perf_counter;\nmodule.exports = {perf_counter, perfCounter};\n"


def rewrite_js_std_sys_live_wrapper(js_src: str) -> str:
    required_fragments = (
        "function exit(code) {",
        "function set_argv(values) {",
        "function set_path(values) {",
        "function write_stderr(text) {",
        "function write_stdout(text) {",
    )
    for fragment in required_fragments:
        if fragment not in js_src:
            raise RuntimeError("generated JS std/sys wrapper is missing: " + fragment)
    return """
const sys = {
    argv: Array.from(process.argv),
    path: [],
    stderr: process.stderr,
    stdout: process.stdout,
    exit(code = 0) {
        process.exit(Number(code) || 0);
    },
};

function exit(code) {
    sys.exit(code);
}

function set_argv(values) {
    sys.argv = Array.isArray(values) ? Array.from(values, (value) => String(value)) : [];
}

function set_path(values) {
    sys.path = Array.isArray(values) ? Array.from(values, (value) => String(value)) : [];
}

function write_stderr(text) {
    process.stderr.write(String(text));
}

function write_stdout(text) {
    process.stdout.write(String(text));
}

sys.set_argv = set_argv;
sys.set_path = set_path;
sys.write_stderr = write_stderr;
sys.write_stdout = write_stdout;

module.exports = { sys, argv: sys.argv, path: sys.path, stderr: sys.stderr, stdout: sys.stdout, exit, set_argv, set_path, write_stderr, write_stdout };
""".lstrip()


def rewrite_js_std_pathlib_live_wrapper(js_src: str) -> str:
    required_fragments = (
        "class Path {",
        "__truediv__(rhs)",
        "parent()",
        "parents()",
        "name()",
        "suffix()",
        "stem()",
        "resolve()",
        "exists()",
        "mkdir(parents, exist_ok)",
        "read_text(encoding)",
        "write_text(text, encoding)",
        "glob(pattern)",
        "cwd()",
    )
    for fragment in required_fragments:
        if fragment not in js_src:
            raise RuntimeError("generated JS std/pathlib wrapper is missing: " + fragment)
    return (
        'const fs = require("fs");\n'
        'const nodepath = require("path");\n\n'
        "function _coercePathText(value) {\n"
        "    if (value && typeof value.__fspath__ === \"function\") {\n"
        "        return String(value.__fspath__());\n"
        "    }\n"
        "    if (value && typeof value.toString === \"function\" && value.toString !== Object.prototype.toString) {\n"
        "        return String(value.toString());\n"
        "    }\n"
        "    return String(value ?? \"\");\n"
        "}\n\n"
        "function _globSegmentToRegExp(segment) {\n"
        "    const escaped = String(segment).replace(/[|\\\\{}()[\\]^$+?.]/g, \"\\\\$&\");\n"
        "    return new RegExp(\"^\" + escaped.replace(/\\*/g, \".*\") + \"$\");\n"
        "}\n\n"
        "function _globPaths(pattern) {\n"
        "    const text = _coercePathText(pattern);\n"
        "    if (text.indexOf(\"*\") === -1) {\n"
        "        return fs.existsSync(text) ? [text] : [];\n"
        "    }\n"
        "    const normalized = text.replace(/\\\\/g, \"/\");\n"
        "    const lastSlash = normalized.lastIndexOf(\"/\");\n"
        "    const baseDir = lastSlash >= 0 ? normalized.slice(0, lastSlash) : \".\";\n"
        "    const leafPattern = lastSlash >= 0 ? normalized.slice(lastSlash + 1) : normalized;\n"
        "    const dirPath = baseDir === \"\" ? \".\" : baseDir;\n"
        "    if (!fs.existsSync(dirPath) || !fs.statSync(dirPath).isDirectory()) {\n"
        "        return [];\n"
        "    }\n"
        "    const leafRe = _globSegmentToRegExp(leafPattern);\n"
        "    const out = [];\n"
        "    for (const entry of fs.readdirSync(dirPath, { withFileTypes: true })) {\n"
        "        if (!leafRe.test(entry.name)) {\n"
        "            continue;\n"
        "        }\n"
        "        out.push(nodepath.join(dirPath, entry.name));\n"
        "    }\n"
        "    return out;\n"
        "}\n\n"
        "class PathValue {\n"
        "    constructor(value) {\n"
        "        this._value = _coercePathText(value);\n"
        "    }\n\n"
        "    __str__() {\n"
        "        return this._value;\n"
        "    }\n\n"
        "    __repr__() {\n"
        "        return \"Path(\" + this._value + \")\";\n"
        "    }\n\n"
        "    __fspath__() {\n"
        "        return this._value;\n"
        "    }\n\n"
        "    __truediv__(rhs) {\n"
        "        return new PathValue(nodepath.join(this._value, _coercePathText(rhs)));\n"
        "    }\n\n"
        "    parent() {\n"
        "        let parentTxt = nodepath.dirname(this._value);\n"
        "        if (parentTxt === \"\") {\n"
        "            parentTxt = \".\";\n"
        "        }\n"
        "        return new PathValue(parentTxt);\n"
        "    }\n\n"
        "    parents() {\n"
        "        const out = [];\n"
        "        let current = nodepath.dirname(this._value);\n"
        "        while (true) {\n"
        "            if (current === \"\") {\n"
        "                current = \".\";\n"
        "            }\n"
        "            out.push(new PathValue(current));\n"
        "            let nextCurrent = nodepath.dirname(current);\n"
        "            if (nextCurrent === \"\") {\n"
        "                nextCurrent = \".\";\n"
        "            }\n"
        "            if (nextCurrent === current) {\n"
        "                break;\n"
        "            }\n"
        "            current = nextCurrent;\n"
        "        }\n"
        "        return out;\n"
        "    }\n\n"
        "    name() {\n"
        "        return nodepath.basename(this._value);\n"
        "    }\n\n"
        "    suffix() {\n"
        "        return nodepath.extname(this._value);\n"
        "    }\n\n"
        "    stem() {\n"
        "        return nodepath.parse(this._value).name;\n"
        "    }\n\n"
        "    resolve() {\n"
        "        return new PathValue(nodepath.resolve(this._value));\n"
        "    }\n\n"
        "    exists() {\n"
        "        return fs.existsSync(this._value);\n"
        "    }\n\n"
        "    mkdir(parents = false, exist_ok = false) {\n"
        "        if (parents) {\n"
        "            fs.mkdirSync(this._value, { recursive: true });\n"
        "            return;\n"
        "        }\n"
        "        try {\n"
        "            fs.mkdirSync(this._value);\n"
        "        } catch (err) {\n"
        "            if (!(exist_ok && err && err.code === \"EEXIST\")) {\n"
        "                throw err;\n"
        "            }\n"
        "        }\n"
        "    }\n\n"
        "    read_text(_encoding = \"utf-8\") {\n"
        "        return fs.readFileSync(this._value, \"utf8\");\n"
        "    }\n\n"
        "    write_text(text, _encoding = \"utf-8\") {\n"
        "        const rendered = String(text);\n"
        "        fs.writeFileSync(this._value, rendered, \"utf8\");\n"
        "        return rendered.length;\n"
        "    }\n\n"
        "    glob(pattern) {\n"
        "        const matches = _globPaths(nodepath.join(this._value, _coercePathText(pattern)));\n"
        "        return matches.map((item) => new PathValue(item));\n"
        "    }\n\n"
        "    toString() {\n"
        "        return this._value;\n"
        "    }\n\n"
        "    static cwd() {\n"
        "        return new PathValue(process.cwd());\n"
        "    }\n"
        "}\n\n"
        "function _wrap_path_obj(obj) {\n"
        "    if (!(obj instanceof PathValue)) {\n"
        "        return obj;\n"
        "    }\n"
        "    if (!Object.prototype.hasOwnProperty.call(obj, \"parent\")) {\n"
        "        Object.defineProperty(obj, \"parent\", { get: function() { return _wrap_path_obj(PathValue.prototype.parent.call(this)); }, configurable: true });\n"
        "    }\n"
        "    if (!Object.prototype.hasOwnProperty.call(obj, \"parents\")) {\n"
        "        Object.defineProperty(obj, \"parents\", { get: function() { return PathValue.prototype.parents.call(this).map(_wrap_path_obj); }, configurable: true });\n"
        "    }\n"
        "    if (!Object.prototype.hasOwnProperty.call(obj, \"name\")) {\n"
        "        Object.defineProperty(obj, \"name\", { get: function() { return PathValue.prototype.name.call(this); }, configurable: true });\n"
        "    }\n"
        "    if (!Object.prototype.hasOwnProperty.call(obj, \"suffix\")) {\n"
        "        Object.defineProperty(obj, \"suffix\", { get: function() { return PathValue.prototype.suffix.call(this); }, configurable: true });\n"
        "    }\n"
        "    if (!Object.prototype.hasOwnProperty.call(obj, \"stem\")) {\n"
        "        Object.defineProperty(obj, \"stem\", { get: function() { return PathValue.prototype.stem.call(this); }, configurable: true });\n"
        "    }\n"
        "    return obj;\n"
        "}\n\n"
        "function Path(value = \"\") {\n"
        "    return _wrap_path_obj(new PathValue(value));\n"
        "}\n\n"
        "Path.cwd = function() {\n"
        "    return _wrap_path_obj(PathValue.cwd());\n"
        "};\n\n"
        "function pathJoin(base, child) {\n"
        "    return _wrap_path_obj(new PathValue(nodepath.join(_coercePathText(base), _coercePathText(child))));\n"
        "}\n\n"
        "module.exports = { Path, pathJoin };\n"
    )


def rewrite_js_std_json_live_wrapper(js_src: str) -> str:
    required_fragments = (
        "class JsonObj {",
        "class JsonArr {",
        "class JsonValue {",
        "function loads(",
        "function loads_obj(",
        "function loads_arr(",
        "function dumps(",
    )
    for fragment in required_fragments:
        if fragment not in js_src:
            raise RuntimeError("generated JS std/json wrapper is missing: " + fragment)
    return """
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
        return "\\\\u" + codePoint.toString(16).padStart(4, "0");
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
            out.push('\\"');
        } else if (ch === "\\\\") {
            out.push('\\\\');
        } else if (ch === "\\b") {
            out.push('\\b');
        } else if (ch === "\\f") {
            out.push('\\f');
        } else if (ch === "\\n") {
            out.push('\\n');
        } else if (ch === "\\r") {
            out.push('\\r');
        } else if (ch === "\\t") {
            out.push('\\t');
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
    return "[\\n" + inner.join(",\\n") + "\\n" + _repeat_indent(indent, level) + "]";
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
    return "{\\n" + inner.join(",\\n") + "\\n" + _repeat_indent(indent, level) + "}";
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
""".lstrip()


def rewrite_ts_std_math_live_wrapper(ts_src: str) -> str:
    text = _strip_trailing_string_literal_expr(ts_src)
    text = text.replace('import { extern } from "./pytra/std.js";\n\n', "")
    text = text.replace('"pytra.std.math: extern-marked math API with Python runtime fallback.";\n', "")
    text = text.replace("let pi = extern(__m.pi);", "export const pi: number = Math.PI;")
    text = text.replace("let e = extern(__m.e);", "export const e: number = Math.E;")
    signature_replacements = {
        "function sqrt(x) {": "export function sqrt(x: number): number {",
        "function sin(x) {": "export function sin(x: number): number {",
        "function cos(x) {": "export function cos(x: number): number {",
        "function tan(x) {": "export function tan(x: number): number {",
        "function exp(x) {": "export function exp(x: number): number {",
        "function log(x) {": "export function log(x: number): number {",
        "function log10(x) {": "export function log10(x: number): number {",
        "function fabs(x) {": "export function fabs(x: number): number {",
        "function floor(x) {": "export function floor(x: number): number {",
        "function ceil(x) {": "export function ceil(x: number): number {",
        "function pow(x, y) {": "export function pow(x: number, y: number): number {",
    }
    for before, after in signature_replacements.items():
        text = text.replace(before, after)
    replacements = {
        "return __m.sqrt(x);": "return Math.sqrt(x);",
        "return __m.sin(x);": "return Math.sin(x);",
        "return __m.cos(x);": "return Math.cos(x);",
        "return __m.tan(x);": "return Math.tan(x);",
        "return __m.exp(x);": "return Math.exp(x);",
        "return __m.log(x);": "return Math.log(x);",
        "return __m.log10(x);": "return Math.log10(x);",
        "return __m.fabs(x);": "return Math.abs(x);",
        "return __m.floor(x);": "return Math.floor(x);",
        "return __m.ceil(x);": "return Math.ceil(x);",
        "return __m.pow(x, y);": "return Math.pow(x, y);",
    }
    for before, after in replacements.items():
        text = text.replace(before, after)
    if "extern(" in text or "__m." in text:
        raise RuntimeError("generated TS std/math wrapper still contains extern/math runtime residue")
    return text.rstrip() + "\n"


def rewrite_ts_std_time_live_wrapper(ts_src: str) -> str:
    text = _strip_trailing_string_literal_expr(ts_src)
    text = text.replace(
        "function perf_counter() {",
        "export function perf_counter(): number {",
        1,
    )
    text = text.replace(
        "return __t.perf_counter();",
        "return Number(process.hrtime.bigint()) / 1_000_000_000;",
    ).rstrip()
    if "export function perf_counter(): number {" not in text:
        raise RuntimeError("generated TS std/time wrapper is missing perf_counter()")
    return text + "\n\nexport const perfCounter = perf_counter;\n"


def rewrite_ts_std_sys_live_wrapper(ts_src: str) -> str:
    required_fragments = (
        "function exit(code) {",
        "function set_argv(values) {",
        "function set_path(values) {",
        "function write_stderr(text) {",
        "function write_stdout(text) {",
    )
    for fragment in required_fragments:
        if fragment not in ts_src:
            raise RuntimeError("generated TS std/sys wrapper is missing: " + fragment)
    return """
type SysApi = {
    argv: string[];
    path: string[];
    stderr: NodeJS.WriteStream;
    stdout: NodeJS.WriteStream;
    exit: (code?: number) => never;
    set_argv: (values: unknown) => void;
    set_path: (values: unknown) => void;
    write_stderr: (text: unknown) => void;
    write_stdout: (text: unknown) => void;
};

export const sys: SysApi = {
    argv: Array.from(process.argv),
    path: [],
    stderr: process.stderr,
    stdout: process.stdout,
    exit(code: number = 0): never {
        process.exit(Number(code) || 0);
    },
    set_argv(values: unknown): void {
        sys.argv = Array.isArray(values) ? Array.from(values, (value) => String(value)) : [];
    },
    set_path(values: unknown): void {
        sys.path = Array.isArray(values) ? Array.from(values, (value) => String(value)) : [];
    },
    write_stderr(text: unknown): void {
        process.stderr.write(String(text));
    },
    write_stdout(text: unknown): void {
        process.stdout.write(String(text));
    },
};

export const argv = sys.argv;
export const path = sys.path;
export const stderr = sys.stderr;
export const stdout = sys.stdout;

export function exit(code: number = 0): never {
    return sys.exit(code);
}

export function set_argv(values: unknown): void {
    sys.set_argv(values);
}

export function set_path(values: unknown): void {
    sys.set_path(values);
}

export function write_stderr(text: unknown): void {
    sys.write_stderr(text);
}

export function write_stdout(text: unknown): void {
    sys.write_stdout(text);
}
""".lstrip()


def rewrite_ts_std_module_runtime_imports(ts_src: str, *, module_name: str) -> str:
    text = _strip_trailing_string_literal_expr(ts_src)
    replacements = {
        'import { PYTRA_TYPE_ID, PY_TYPE_MAP, PY_TYPE_OBJECT, pyRegisterClassType, pyBool, pyLen } from "./pytra/py_runtime.js";':
            'const { PYTRA_TYPE_ID, PY_TYPE_MAP, PY_TYPE_OBJECT, pyRegisterClassType, pyBool, pyLen } = require("../../native/built_in/py_runtime.js");',
        'import { PYTRA_TYPE_ID, PY_TYPE_MAP, PY_TYPE_OBJECT, pyRegisterClassType, pyBool, pyLen } from "./runtime/js/native/built_in/py_runtime.js";':
            'const { PYTRA_TYPE_ID, PY_TYPE_MAP, PY_TYPE_OBJECT, pyRegisterClassType, pyBool, pyLen } = require("../../native/built_in/py_runtime.js");',
        'import { PYTRA_TYPE_ID, PY_TYPE_OBJECT, pyRegisterClassType } from "./pytra/py_runtime.js";':
            'const { PYTRA_TYPE_ID, PY_TYPE_OBJECT, pyRegisterClassType } = require("../../native/built_in/py_runtime.js");',
        'import { PYTRA_TYPE_ID, PY_TYPE_OBJECT, pyRegisterClassType } from "./runtime/js/native/built_in/py_runtime.js";':
            'const { PYTRA_TYPE_ID, PY_TYPE_OBJECT, pyRegisterClassType } = require("../../native/built_in/py_runtime.js");',
        'import * as sys from "./pytra/std/sys.js";':
            'const sys = require("./sys.js");',
        'import * as sys from "./runtime/js/generated/std/sys.js";':
            'const sys = require("./sys.js");',
        'import * as _math from "./pytra/std/math.js";':
            'const _math = require("./math.js");',
        'import * as _math from "./runtime/js/generated/std/math.js";':
            'const _math = require("./math.js");',
        'import { perf_counter } from "./pytra/std/time.js";':
            'const { perf_counter } = require("./time.js");',
        'import { perf_counter } from "./runtime/js/generated/std/time.js";':
            'const { perf_counter } = require("./time.js");',
    }
    for before, after in replacements.items():
        text = text.replace(before, after)
    if "./pytra/" in text or "./runtime/js/" in text:
        raise RuntimeError("generated TS std/" + module_name + " wrapper still points at staged runtime paths")
    return rewrite_js_program_to_cjs_module(text)


def rewrite_ts_std_pathlib_live_wrapper(ts_src: str) -> str:
    required_fragments = (
        "class Path {",
        "__truediv__(rhs)",
        "parent()",
        "parents()",
        "name()",
        "suffix()",
        "stem()",
        "resolve()",
        "exists()",
        "mkdir(parents, exist_ok)",
        "read_text(encoding)",
        "write_text(text, encoding)",
        "glob(pattern)",
        "cwd()",
    )
    for fragment in required_fragments:
        if fragment not in ts_src:
            raise RuntimeError("generated TS std/pathlib wrapper is missing: " + fragment)
    return (
        'import * as fs from "fs";\n'
        'import * as nodepath from "path";\n\n'
        "function _coercePathText(value: unknown): string {\n"
        "    const maybePath = value as { __fspath__?: () => unknown; toString?: () => string } | null | undefined;\n"
        "    if (maybePath && typeof maybePath.__fspath__ === \"function\") {\n"
        "        return String(maybePath.__fspath__());\n"
        "    }\n"
        "    if (maybePath && typeof maybePath.toString === \"function\" && maybePath.toString !== Object.prototype.toString) {\n"
        "        return String(maybePath.toString());\n"
        "    }\n"
        "    return String(value ?? \"\");\n"
        "}\n\n"
        "function _globSegmentToRegExp(segment: string): RegExp {\n"
        "    const escaped = String(segment).replace(/[|\\\\{}()[\\]^$+?.]/g, \"\\\\$&\");\n"
        "    return new RegExp(\"^\" + escaped.replace(/\\*/g, \".*\") + \"$\");\n"
        "}\n\n"
        "function _globPaths(pattern: string): string[] {\n"
        "    const text = _coercePathText(pattern);\n"
        "    if (text.indexOf(\"*\") === -1) {\n"
        "        return fs.existsSync(text) ? [text] : [];\n"
        "    }\n"
        "    const normalized = text.replace(/\\\\/g, \"/\");\n"
        "    const lastSlash = normalized.lastIndexOf(\"/\");\n"
        "    const baseDir = lastSlash >= 0 ? normalized.slice(0, lastSlash) : \".\";\n"
        "    const leafPattern = lastSlash >= 0 ? normalized.slice(lastSlash + 1) : normalized;\n"
        "    const dirPath = baseDir === \"\" ? \".\" : baseDir;\n"
        "    if (!fs.existsSync(dirPath) || !fs.statSync(dirPath).isDirectory()) {\n"
        "        return [];\n"
        "    }\n"
        "    const leafRe = _globSegmentToRegExp(leafPattern);\n"
        "    const out: string[] = [];\n"
        "    for (const entry of fs.readdirSync(dirPath, { withFileTypes: true })) {\n"
        "        if (!leafRe.test(entry.name)) {\n"
        "            continue;\n"
        "        }\n"
        "        out.push(nodepath.join(dirPath, entry.name));\n"
        "    }\n"
        "    return out;\n"
        "}\n\n"
        "export class PathValue {\n"
        "    _value: string;\n\n"
        "    constructor(value: unknown) {\n"
        "        this._value = _coercePathText(value);\n"
        "    }\n\n"
        "    __str__(): string {\n"
        "        return this._value;\n"
        "    }\n\n"
        "    __repr__(): string {\n"
        "        return \"Path(\" + this._value + \")\";\n"
        "    }\n\n"
        "    __fspath__(): string {\n"
        "        return this._value;\n"
        "    }\n\n"
        "    __truediv__(rhs: unknown): PathValue {\n"
        "        return new PathValue(nodepath.join(this._value, _coercePathText(rhs)));\n"
        "    }\n\n"
        "    parent(): PathValue {\n"
        "        let parentTxt = nodepath.dirname(this._value);\n"
        "        if (parentTxt === \"\") {\n"
        "            parentTxt = \".\";\n"
        "        }\n"
        "        return new PathValue(parentTxt);\n"
        "    }\n\n"
        "    parents(): PathValue[] {\n"
        "        const out: PathValue[] = [];\n"
        "        let current = nodepath.dirname(this._value);\n"
        "        while (true) {\n"
        "            if (current === \"\") {\n"
        "                current = \".\";\n"
        "            }\n"
        "            out.push(new PathValue(current));\n"
        "            let nextCurrent = nodepath.dirname(current);\n"
        "            if (nextCurrent === \"\") {\n"
        "                nextCurrent = \".\";\n"
        "            }\n"
        "            if (nextCurrent === current) {\n"
        "                break;\n"
        "            }\n"
        "            current = nextCurrent;\n"
        "        }\n"
        "        return out;\n"
        "    }\n\n"
        "    name(): string {\n"
        "        return nodepath.basename(this._value);\n"
        "    }\n\n"
        "    suffix(): string {\n"
        "        return nodepath.extname(this._value);\n"
        "    }\n\n"
        "    stem(): string {\n"
        "        return nodepath.parse(this._value).name;\n"
        "    }\n\n"
        "    resolve(): PathValue {\n"
        "        return new PathValue(nodepath.resolve(this._value));\n"
        "    }\n\n"
        "    exists(): boolean {\n"
        "        return fs.existsSync(this._value);\n"
        "    }\n\n"
        "    mkdir(parents: boolean = false, exist_ok: boolean = false): void {\n"
        "        if (parents) {\n"
        "            fs.mkdirSync(this._value, { recursive: true });\n"
        "            return;\n"
        "        }\n"
        "        try {\n"
        "            fs.mkdirSync(this._value);\n"
        "        } catch (err: unknown) {\n"
        "            const e = err as { code?: string };\n"
        "            if (!(exist_ok && e.code === \"EEXIST\")) {\n"
        "                throw err;\n"
        "            }\n"
        "        }\n"
        "    }\n\n"
        "    read_text(_encoding: string = \"utf-8\"): string {\n"
        "        return fs.readFileSync(this._value, \"utf8\");\n"
        "    }\n\n"
        "    write_text(text: unknown, _encoding: string = \"utf-8\"): number {\n"
        "        const rendered = String(text);\n"
        "        fs.writeFileSync(this._value, rendered, \"utf8\");\n"
        "        return rendered.length;\n"
        "    }\n\n"
        "    glob(pattern: string): PathValue[] {\n"
        "        const matches = _globPaths(nodepath.join(this._value, _coercePathText(pattern)));\n"
        "        return matches.map((item) => new PathValue(item));\n"
        "    }\n\n"
        "    toString(): string {\n"
        "        return this._value;\n"
        "    }\n\n"
        "    static cwd(): PathValue {\n"
        "        return new PathValue(process.cwd());\n"
        "    }\n"
        "}\n\n"
        "function _wrap_path_obj(obj: PathValue): PathValue {\n"
        "    if (!Object.prototype.hasOwnProperty.call(obj, \"parent\")) {\n"
        "        Object.defineProperty(obj, \"parent\", { get: function(this: PathValue) { return _wrap_path_obj(PathValue.prototype.parent.call(this)); }, configurable: true });\n"
        "    }\n"
        "    if (!Object.prototype.hasOwnProperty.call(obj, \"parents\")) {\n"
        "        Object.defineProperty(obj, \"parents\", { get: function(this: PathValue) { return PathValue.prototype.parents.call(this).map(_wrap_path_obj); }, configurable: true });\n"
        "    }\n"
        "    if (!Object.prototype.hasOwnProperty.call(obj, \"name\")) {\n"
        "        Object.defineProperty(obj, \"name\", { get: function(this: PathValue) { return PathValue.prototype.name.call(this); }, configurable: true });\n"
        "    }\n"
        "    if (!Object.prototype.hasOwnProperty.call(obj, \"suffix\")) {\n"
        "        Object.defineProperty(obj, \"suffix\", { get: function(this: PathValue) { return PathValue.prototype.suffix.call(this); }, configurable: true });\n"
        "    }\n"
        "    if (!Object.prototype.hasOwnProperty.call(obj, \"stem\")) {\n"
        "        Object.defineProperty(obj, \"stem\", { get: function(this: PathValue) { return PathValue.prototype.stem.call(this); }, configurable: true });\n"
        "    }\n"
        "    return obj;\n"
        "}\n\n"
        "export const Path: ((value?: unknown) => PathValue) & { cwd(): PathValue } = Object.assign(\n"
        "    function Path(value: unknown = \"\"): PathValue {\n"
        "        return _wrap_path_obj(new PathValue(value));\n"
        "    },\n"
        "    {\n"
        "        cwd(): PathValue {\n"
        "            return _wrap_path_obj(PathValue.cwd());\n"
        "        },\n"
        "    },\n"
        ");\n\n"
        "export function pathJoin(base: unknown, child: unknown): PathValue {\n"
        "    return _wrap_path_obj(new PathValue(nodepath.join(_coercePathText(base), _coercePathText(child))));\n"
        "}\n"
    )


def rewrite_ts_std_json_live_wrapper(ts_src: str) -> str:
    required_fragments = (
        "class JsonObj {",
        "class JsonArr {",
        "class JsonValue {",
        "function loads(",
        "function loads_obj(",
        "function loads_arr(",
        "function dumps(",
    )
    for fragment in required_fragments:
        if fragment not in ts_src:
            raise RuntimeError("generated TS std/json wrapper is missing: " + fragment)
    return """
import { PYTRA_TYPE_ID, PY_TYPE_OBJECT, pyRegisterClassType } from "../../native/built_in/py_runtime";

type JsonPlainObject = Record<string, unknown>;

function _is_plain_json_object(value: unknown): value is JsonPlainObject {
    if (value === null || typeof value !== "object" || Array.isArray(value)) {
        return false;
    }
    const proto = Object.getPrototypeOf(value);
    return (
        proto === Object.prototype
        || proto === null
        || Object.prototype.hasOwnProperty.call(value as object, PYTRA_TYPE_ID)
    );
}

function _unwrap_json_value(value: unknown): unknown {
    if (value instanceof JsonValue || value instanceof JsonObj || value instanceof JsonArr) {
        return value.raw;
    }
    return value;
}

function _normalize_indent(indent: number | null | undefined): number | null {
    if (indent === null || indent === undefined) {
        return null;
    }
    const value = Math.trunc(Number(indent));
    return value < 0 ? 0 : value;
}

function _repeat_indent(indent: number, level: number): string {
    return " ".repeat(indent * level);
}

function _unicode_escape(codePoint: number): string {
    if (codePoint <= 0xFFFF) {
        return "\\\\u" + codePoint.toString(16).padStart(4, "0");
    }
    const adjusted = codePoint - 0x10000;
    const high = 0xD800 + (adjusted >> 10);
    const low = 0xDC00 + (adjusted & 0x3FF);
    return _unicode_escape(high) + _unicode_escape(low);
}

function _escape_json_string(text: string, ensure_ascii: boolean): string {
    const out: string[] = ['"'];
    for (const ch of String(text)) {
        const code = ch.codePointAt(0);
        if (ch === '"') {
            out.push('\\"');
        } else if (ch === "\\\\") {
            out.push('\\\\');
        } else if (ch === "\\b") {
            out.push('\\b');
        } else if (ch === "\\f") {
            out.push('\\f');
        } else if (ch === "\\n") {
            out.push('\\n');
        } else if (ch === "\\r") {
            out.push('\\r');
        } else if (ch === "\\t") {
            out.push('\\t');
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

export class JsonObj {
    static PYTRA_TYPE_ID = pyRegisterClassType([PY_TYPE_OBJECT]);
    raw: JsonPlainObject;

    constructor(raw: JsonPlainObject) {
        this.raw = _is_plain_json_object(raw) ? raw : {};
        (this as any)[PYTRA_TYPE_ID] = JsonObj.PYTRA_TYPE_ID;
    }

    get(key: string): JsonValue | null {
        if (!Object.prototype.hasOwnProperty.call(this.raw, key)) {
            return null;
        }
        return new JsonValue(this.raw[key]);
    }

    get_obj(key: string): JsonObj | null {
        const value = this.get(key);
        return value === null ? null : value.as_obj();
    }

    get_arr(key: string): JsonArr | null {
        const value = this.get(key);
        return value === null ? null : value.as_arr();
    }

    get_str(key: string): string | null {
        const value = this.get(key);
        return value === null ? null : value.as_str();
    }

    get_int(key: string): number | null {
        const value = this.get(key);
        return value === null ? null : value.as_int();
    }

    get_float(key: string): number | null {
        const value = this.get(key);
        return value === null ? null : value.as_float();
    }

    get_bool(key: string): boolean | null {
        const value = this.get(key);
        return value === null ? null : value.as_bool();
    }
}

export class JsonArr {
    static PYTRA_TYPE_ID = pyRegisterClassType([PY_TYPE_OBJECT]);
    raw: unknown[];

    constructor(raw: unknown[]) {
        this.raw = Array.isArray(raw) ? raw : [];
        (this as any)[PYTRA_TYPE_ID] = JsonArr.PYTRA_TYPE_ID;
    }

    get(index: number): JsonValue | null {
        if (!Number.isInteger(index) || index < 0 || index >= this.raw.length) {
            return null;
        }
        return new JsonValue(this.raw[index]);
    }

    get_obj(index: number): JsonObj | null {
        const value = this.get(index);
        return value === null ? null : value.as_obj();
    }

    get_arr(index: number): JsonArr | null {
        const value = this.get(index);
        return value === null ? null : value.as_arr();
    }

    get_str(index: number): string | null {
        const value = this.get(index);
        return value === null ? null : value.as_str();
    }

    get_int(index: number): number | null {
        const value = this.get(index);
        return value === null ? null : value.as_int();
    }

    get_float(index: number): number | null {
        const value = this.get(index);
        return value === null ? null : value.as_float();
    }

    get_bool(index: number): boolean | null {
        const value = this.get(index);
        return value === null ? null : value.as_bool();
    }
}

export class JsonValue {
    static PYTRA_TYPE_ID = pyRegisterClassType([PY_TYPE_OBJECT]);
    raw: unknown;

    constructor(raw: unknown) {
        this.raw = raw;
        (this as any)[PYTRA_TYPE_ID] = JsonValue.PYTRA_TYPE_ID;
    }

    as_obj(): JsonObj | null {
        return _is_plain_json_object(this.raw) ? new JsonObj(this.raw) : null;
    }

    as_arr(): JsonArr | null {
        return Array.isArray(this.raw) ? new JsonArr(this.raw) : null;
    }

    as_str(): string | null {
        return typeof this.raw === "string" ? this.raw : null;
    }

    as_int(): number | null {
        if (typeof this.raw === "boolean") {
            return null;
        }
        return typeof this.raw === "number" ? Math.trunc(this.raw) : null;
    }

    as_float(): number | null {
        return typeof this.raw === "number" ? this.raw : null;
    }

    as_bool(): boolean | null {
        return typeof this.raw === "boolean" ? this.raw : null;
    }
}

function _parse_json_text(text: string): unknown {
    return JSON.parse(String(text));
}

export function loads(text: string): unknown {
    return _parse_json_text(text);
}

export function loads_obj(text: string): JsonObj | null {
    const value = _parse_json_text(text);
    return _is_plain_json_object(value) ? new JsonObj(value) : null;
}

export function loads_arr(text: string): JsonArr | null {
    const value = _parse_json_text(text);
    return Array.isArray(value) ? new JsonArr(value) : null;
}

function _dump_json_list(
    values: unknown[],
    ensure_ascii: boolean,
    indent: number | null,
    item_sep: string,
    key_sep: string,
    level: number,
): string {
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
    return "[\\n" + inner.join(",\\n") + "\\n" + _repeat_indent(indent, level) + "]";
}

function _dump_json_dict(
    values: JsonPlainObject,
    ensure_ascii: boolean,
    indent: number | null,
    item_sep: string,
    key_sep: string,
    level: number,
): string {
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
    return "{\\n" + inner.join(",\\n") + "\\n" + _repeat_indent(indent, level) + "}";
}

function _dump_json_value(
    value: unknown,
    ensure_ascii: boolean,
    indent: number | null,
    item_sep: string,
    key_sep: string,
    level: number,
): string {
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

export function dumps(
    obj: unknown,
    ensure_ascii: boolean = true,
    indent: number | null = null,
    separators: [string, string] | null = null,
): string {
    let item_sep = ",";
    let key_sep = indent === null || indent === undefined ? ":" : ": ";
    if (Array.isArray(separators) && separators.length >= 2) {
        item_sep = String(separators[0]);
        key_sep = String(separators[1]);
    }
    return _dump_json_value(obj, ensure_ascii !== false, _normalize_indent(indent), item_sep, key_sep, 0);
}
""".lstrip()


def rewrite_go_program_to_library(go_src: str) -> str:
    lines = _strip_trailing_string_literal_expr(go_src).splitlines()
    lines = _remove_block_by_signature(lines, re.compile(r"^func\s+main\s*\("))
    text = "\n".join(lines)
    text = re.sub(
        r"(?m)^(\s*)_(?:[A-Za-z0-9]+_)?append_list\((\w+),\s*(.+)\)$",
        r"\1\2 = append(\2, \3...)",
        text,
    )
    text = re.sub(
        r"(?m)^(\s*)_ = open\(",
        r"\1f := open(",
        text,
    )
    return text.rstrip() + "\n"


def rewrite_kotlin_program_to_library(kotlin_src: str) -> str:
    lines = _strip_trailing_string_literal_expr(kotlin_src).splitlines()
    lines = _remove_block_by_signature(lines, re.compile(r"^fun\s+main\s*\("))
    return "\n".join(lines).rstrip() + "\n"


def rewrite_scala_program_to_library(scala_src: str) -> str:
    lines = _strip_trailing_string_literal_expr(scala_src).splitlines()
    lines = _remove_block_by_signature(lines, re.compile(r"^def\s+main\s*\("))
    return "\n".join(lines).rstrip() + "\n"


def rewrite_swift_program_to_library(swift_src: str) -> str:
    lines = _strip_trailing_string_literal_expr(swift_src).splitlines()
    lines = _remove_block_by_signature(lines, re.compile(r"^@main$"))
    return "\n".join(lines).rstrip() + "\n"


def _php_generated_runtime_require_block() -> str:
    return "\n".join(
        [
            "$__pytra_runtime_candidates = [",
            "    dirname(__DIR__) . '/py_runtime.php',",
            "    dirname(__DIR__, 2) . '/native/built_in/py_runtime.php',",
            "];",
            "foreach ($__pytra_runtime_candidates as $__pytra_runtime_path) {",
            "    if (is_file($__pytra_runtime_path)) {",
            "        require_once $__pytra_runtime_path;",
            "        break;",
            "    }",
            "}",
            "if (!function_exists('__pytra_len')) {",
            "    throw new RuntimeException('py_runtime.php not found for generated PHP runtime lane');",
            "}",
        ]
    ) + "\n"


def rewrite_php_program_to_library(php_src: str) -> str:
    lines = _strip_trailing_string_literal_expr(php_src).splitlines()
    lines = _remove_block_by_signature(lines, re.compile(r"^function\s+__pytra_main\s*\("))
    runtime_require = _php_generated_runtime_require_block().rstrip()
    out: list[str] = []
    for line in lines:
        line = line.replace(
            "require_once __DIR__ . '/pytra/py_runtime.php';",
            runtime_require,
        )
        if line.strip() == "__pytra_main();":
            continue
        out.append(line)
    text = "\n".join(out)
    # PHP 配列は値渡しが既定のため、生成 helper の append_list は参照渡し化する。
    text = re.sub(
        r"(?m)^function\s+(_[A-Za-z0-9]+_append_list)\(\$([A-Za-z_][A-Za-z0-9_]*),\s*(\$[A-Za-z_][A-Za-z0-9_]*)\)\s*\{",
        r"function \1(&$\2, \3) {",
        text,
    )
    return text.rstrip() + "\n"


def rewrite_php_std_time_live_wrapper(php_src: str) -> str:
    lines = _strip_trailing_string_literal_expr(php_src).splitlines()
    lines = _remove_block_by_signature(lines, re.compile(r"^function\s+__pytra_main\s*\("))
    out: list[str] = []
    for line in lines:
        if line.strip() == "require_once __DIR__ . '/pytra/py_runtime.php';":
            continue
        if line.strip() == "__pytra_main();":
            continue
        out.append(line)
    text = "\n".join(out)
    text = text.replace("function perf_counter() {", "function perf_counter(): float {")
    text = text.replace("return $__t->perf_counter();", "return microtime(true);")
    if "function perf_counter(): float {" not in text:
        raise RuntimeError("generated PHP std/time wrapper is missing perf_counter()")
    return text.rstrip() + "\n"


def rewrite_php_std_math_live_wrapper(php_src: str) -> str:
    text = rewrite_php_program_to_library(php_src)
    runtime_require = _php_generated_runtime_require_block().rstrip()
    text = text.replace(
        runtime_require,
        runtime_require + "\n\n$pi = pyMathPi();\n$e = pyMathE();",
        1,
    )
    signature_replacements = {
        "function sqrt($x) {": "function sqrt($x): float {",
        "function sin($x) {": "function sin($x): float {",
        "function cos($x) {": "function cos($x): float {",
        "function tan($x) {": "function tan($x): float {",
        "function exp($x) {": "function exp($x): float {",
        "function log($x) {": "function log($x): float {",
        "function log10($x) {": "function log10($x): float {",
        "function fabs($x) {": "function fabs($x): float {",
        "function floor($x) {": "function floor($x): float {",
        "function ceil($x) {": "function ceil($x): float {",
        "function pow($x, $y) {": "function pow($x, $y): float {",
    }
    for before, after in signature_replacements.items():
        text = text.replace(before, after)
    if "pyMathPi()" not in text or "pyMathE()" not in text:
        raise RuntimeError("generated PHP std/math wrapper is missing pi/e helpers")
    if "__pytra_main" in text:
        raise RuntimeError("generated PHP std/math wrapper still contains main stub")
    return text.rstrip() + "\n"


def rewrite_php_std_pathlib_live_wrapper(php_src: str) -> str:
    required_fragments = (
        "class Path {",
        "__truediv__",
        "parent()",
        "name()",
        "stem()",
        "resolve()",
        "exists()",
        "mkdir(",
        "read_text(",
        "write_text(",
        "glob(",
        "cwd()",
    )
    for fragment in required_fragments:
        if fragment not in php_src:
            raise RuntimeError("generated PHP std/pathlib wrapper is missing: " + fragment)
    runtime_require = _php_generated_runtime_require_block().rstrip()
    return "\n".join(
        [
            "<?php",
            "declare(strict_types=1);",
            "",
            runtime_require,
            "",
            "if (!class_exists('Path', false)) {",
            "    class Path {",
            "        public string $path;",
            "        public string $name;",
            "        public string $stem;",
            "        public string $suffix;",
            "        public $parent;",
            "",
            "        public function __construct($value) {",
            "            $this->path = (string)$value;",
            "            $this->name = basename($this->path);",
            "            $dot = strrpos($this->name, '.');",
            "            $this->stem = ($dot === false || $dot === 0) ? $this->name : substr($this->name, 0, $dot);",
            "            $this->suffix = ($dot === false || $dot === 0) ? '' : substr($this->name, $dot);",
            "            $parentTxt = dirname($this->path);",
            "            if ($parentTxt === '' || $parentTxt === $this->path) {",
            "                $this->parent = null;",
            "            } else {",
            "                $this->parent = new Path($parentTxt);",
            "            }",
            "        }",
            "",
            "        public function __toString(): string {",
            "            return $this->path;",
            "        }",
            "",
            "        public function __fspath__(): string {",
            "            return $this->path;",
            "        }",
            "",
            "        public function __truediv__($rhs): Path {",
            "            $rhsText = (string)$rhs;",
            "            if ($this->path === '') {",
            "                return new Path($rhsText);",
            "            }",
            "            return new Path(rtrim($this->path, DIRECTORY_SEPARATOR) . DIRECTORY_SEPARATOR . ltrim($rhsText, DIRECTORY_SEPARATOR));",
            "        }",
            "",
            "        public function resolve(): Path {",
            "            $resolved = realpath($this->path);",
            "            if ($resolved === false) {",
            "                $resolved = $this->path;",
            "            }",
            "            return new Path($resolved);",
            "        }",
            "",
            "        public function exists(): bool {",
            "            return file_exists($this->path);",
            "        }",
            "",
            "        public function mkdir($parents = false, $exist_ok = false): void {",
            "            if ($exist_ok && file_exists($this->path)) {",
            "                return;",
            "            }",
            "            if ((bool)$parents) {",
            "                if (@mkdir($this->path, 0777, true)) {",
            "                    return;",
            "                }",
            "                if ((bool)$exist_ok && is_dir($this->path)) {",
            "                    return;",
            "                }",
            "                throw new RuntimeException('mkdir failed: ' . $this->path);",
            "            }",
            "            if (@mkdir($this->path)) {",
            "                return;",
            "            }",
            "            if ((bool)$exist_ok && is_dir($this->path)) {",
            "                return;",
            "            }",
            "            throw new RuntimeException('mkdir failed: ' . $this->path);",
            "        }",
            "",
            "        public function write_text($text, $encoding = 'utf-8'): int {",
            "            $bytes = file_put_contents($this->path, (string)$text);",
            "            if ($bytes === false) {",
            "                throw new RuntimeException('write_text failed: ' . $this->path);",
            "            }",
            "            return $bytes;",
            "        }",
            "",
            "        public function read_text($encoding = 'utf-8'): string {",
            "            $data = file_get_contents($this->path);",
            "            if ($data === false) {",
            "                throw new RuntimeException('read_text failed: ' . $this->path);",
            "            }",
            "            return $data;",
            "        }",
            "",
            "        public function glob($pattern): array {",
            "            $prefix = rtrim($this->path, DIRECTORY_SEPARATOR);",
            "            $items = glob($prefix . DIRECTORY_SEPARATOR . (string)$pattern);",
            "            if (!is_array($items)) {",
            "                return [];",
            "            }",
            "            return array_map(fn($item) => new Path($item), $items);",
            "        }",
            "",
            "        public static function cwd(): Path {",
            "            return new Path(getcwd());",
            "        }",
            "    }",
            "}",
            "",
        ]
    )


def rewrite_php_std_json_live_wrapper(php_src: str) -> str:
    required_fragments = (
        "class JsonObj {",
        "class JsonArr {",
        "class JsonValue {",
        "function loads(",
        "function loads_obj(",
        "function loads_arr(",
        "function dumps(",
    )
    for fragment in required_fragments:
        if fragment not in php_src:
            raise RuntimeError("generated PHP std/json wrapper is missing: " + fragment)
    runtime_require = _php_generated_runtime_require_block().rstrip()
    return "\n".join(
        [
            "<?php",
            "declare(strict_types=1);",
            "",
            runtime_require,
            "",
            "function _pytra_json_is_object_value($value): bool {",
            "    if (is_object($value)) {",
            "        return true;",
            "    }",
            "    return is_array($value) && !__pytra_array_is_list_like($value);",
            "}",
            "",
            "function _pytra_json_is_array_value($value): bool {",
            "    return is_array($value) && __pytra_array_is_list_like($value);",
            "}",
            "",
            "function _pytra_json_object_raw($value): object {",
            "    if (is_object($value)) {",
            "        return $value;",
            "    }",
            "    if (is_array($value) && !__pytra_array_is_list_like($value)) {",
            "        return (object)$value;",
            "    }",
            "    return (object)[];",
            "}",
            "",
            "function _pytra_json_object_props($value): array {",
            "    $props = get_object_vars(_pytra_json_object_raw($value));",
            "    return is_array($props) ? $props : [];",
            "}",
            "",
            "function _pytra_json_array_raw($value): array {",
            "    if (is_array($value) && __pytra_array_is_list_like($value)) {",
            "        return array_values($value);",
            "    }",
            "    return [];",
            "}",
            "",
            "function _pytra_json_unwrap($value) {",
            "    if ($value instanceof JsonValue || $value instanceof JsonObj || $value instanceof JsonArr) {",
            "        return $value->raw;",
            "    }",
            "    return $value;",
            "}",
            "",
            "function _pytra_json_normalize_indent($indent): ?int {",
            "    if ($indent === null) {",
            "        return null;",
            "    }",
            "    $value = (int)$indent;",
            "    return $value < 0 ? 0 : $value;",
            "}",
            "",
            "function _pytra_json_repeat_indent(int $indent, int $level): string {",
            "    return str_repeat(\" \", $indent * $level);",
            "}",
            "",
            "function _pytra_json_escape_string(string $text, bool $ensure_ascii): string {",
            "    $flags = JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR;",
            "    if (!$ensure_ascii) {",
            "        $flags |= JSON_UNESCAPED_UNICODE;",
            "    }",
            "    $encoded = json_encode($text, $flags);",
            "    if (!is_string($encoded)) {",
            "        throw new RuntimeException('json string encoding failed');",
            "    }",
            "    return $encoded;",
            "}",
            "",
            "function _pytra_json_number_text($value): string {",
            "    if (is_int($value)) {",
            "        return (string)$value;",
            "    }",
            "    $encoded = json_encode($value, JSON_PRESERVE_ZERO_FRACTION | JSON_THROW_ON_ERROR);",
            "    if (!is_string($encoded)) {",
            "        throw new RuntimeException('json number encoding failed');",
            "    }",
            "    return $encoded;",
            "}",
            "",
            "class JsonObj {",
            "    public object $raw;",
            "",
            "    public function __construct($raw) {",
            "        $this->raw = _pytra_json_object_raw($raw);",
            "    }",
            "",
            "    public function get(string $key): ?JsonValue {",
            "        $props = _pytra_json_object_props($this->raw);",
            "        if (!array_key_exists($key, $props)) {",
            "            return null;",
            "        }",
            "        return new JsonValue($props[$key]);",
            "    }",
            "",
            "    public function get_obj(string $key): ?JsonObj {",
            "        $value = $this->get($key);",
            "        return $value === null ? null : $value->as_obj();",
            "    }",
            "",
            "    public function get_arr(string $key): ?JsonArr {",
            "        $value = $this->get($key);",
            "        return $value === null ? null : $value->as_arr();",
            "    }",
            "",
            "    public function get_str(string $key): ?string {",
            "        $value = $this->get($key);",
            "        return $value === null ? null : $value->as_str();",
            "    }",
            "",
            "    public function get_int(string $key): ?int {",
            "        $value = $this->get($key);",
            "        return $value === null ? null : $value->as_int();",
            "    }",
            "",
            "    public function get_float(string $key): ?float {",
            "        $value = $this->get($key);",
            "        return $value === null ? null : $value->as_float();",
            "    }",
            "",
            "    public function get_bool(string $key): ?bool {",
            "        $value = $this->get($key);",
            "        return $value === null ? null : $value->as_bool();",
            "    }",
            "}",
            "",
            "class JsonArr {",
            "    public array $raw;",
            "",
            "    public function __construct($raw) {",
            "        $this->raw = _pytra_json_array_raw($raw);",
            "    }",
            "",
            "    public function get(int $index): ?JsonValue {",
            "        if ($index < 0 || !array_key_exists($index, $this->raw)) {",
            "            return null;",
            "        }",
            "        return new JsonValue($this->raw[$index]);",
            "    }",
            "",
            "    public function get_obj(int $index): ?JsonObj {",
            "        $value = $this->get($index);",
            "        return $value === null ? null : $value->as_obj();",
            "    }",
            "",
            "    public function get_arr(int $index): ?JsonArr {",
            "        $value = $this->get($index);",
            "        return $value === null ? null : $value->as_arr();",
            "    }",
            "",
            "    public function get_str(int $index): ?string {",
            "        $value = $this->get($index);",
            "        return $value === null ? null : $value->as_str();",
            "    }",
            "",
            "    public function get_int(int $index): ?int {",
            "        $value = $this->get($index);",
            "        return $value === null ? null : $value->as_int();",
            "    }",
            "",
            "    public function get_float(int $index): ?float {",
            "        $value = $this->get($index);",
            "        return $value === null ? null : $value->as_float();",
            "    }",
            "",
            "    public function get_bool(int $index): ?bool {",
            "        $value = $this->get($index);",
            "        return $value === null ? null : $value->as_bool();",
            "    }",
            "}",
            "",
            "class JsonValue {",
            "    public $raw;",
            "",
            "    public function __construct($raw) {",
            "        $this->raw = $raw;",
            "    }",
            "",
            "    public function as_obj(): ?JsonObj {",
            "        return _pytra_json_is_object_value($this->raw) ? new JsonObj($this->raw) : null;",
            "    }",
            "",
            "    public function as_arr(): ?JsonArr {",
            "        return _pytra_json_is_array_value($this->raw) ? new JsonArr($this->raw) : null;",
            "    }",
            "",
            "    public function as_str(): ?string {",
            "        return is_string($this->raw) ? $this->raw : null;",
            "    }",
            "",
            "    public function as_int(): ?int {",
            "        if (is_bool($this->raw)) {",
            "            return null;",
            "        }",
            "        return is_int($this->raw) ? $this->raw : null;",
            "    }",
            "",
            "    public function as_float(): ?float {",
            "        return is_float($this->raw) ? $this->raw : null;",
            "    }",
            "",
            "    public function as_bool(): ?bool {",
            "        return is_bool($this->raw) ? $this->raw : null;",
            "    }",
            "}",
            "",
            "function loads(string $text) {",
            "    return json_decode((string)$text, false, 512, JSON_THROW_ON_ERROR);",
            "}",
            "",
            "function loads_obj(string $text): ?JsonObj {",
            "    $value = loads($text);",
            "    return _pytra_json_is_object_value($value) ? new JsonObj($value) : null;",
            "}",
            "",
            "function loads_arr(string $text): ?JsonArr {",
            "    $value = loads($text);",
            "    return _pytra_json_is_array_value($value) ? new JsonArr($value) : null;",
            "}",
            "",
            "function _pytra_json_dump_list(array $values, bool $ensure_ascii, ?int $indent, string $item_sep, string $key_sep, int $level): string {",
            "    if (count($values) === 0) {",
            "        return '[]';",
            "    }",
            "    if ($indent === null) {",
            "        $parts = [];",
            "        foreach ($values as $item) {",
            "            $parts[] = _pytra_json_dump_value($item, $ensure_ascii, $indent, $item_sep, $key_sep, $level);",
            "        }",
            "        return '[' . implode($item_sep, $parts) . ']';",
            "    }",
            "    $indent_i = _pytra_json_normalize_indent($indent);",
            "    $parts = [];",
            "    foreach ($values as $item) {",
            "        $parts[] = _pytra_json_repeat_indent($indent_i, $level + 1) . _pytra_json_dump_value($item, $ensure_ascii, $indent_i, $item_sep, $key_sep, $level + 1);",
            "    }",
            "    return \"[\\n\" . implode(\",\\n\", $parts) . \"\\n\" . _pytra_json_repeat_indent($indent_i, $level) . ']';",
            "}",
            "",
            "function _pytra_json_dump_dict($values, bool $ensure_ascii, ?int $indent, string $item_sep, string $key_sep, int $level): string {",
            "    $props = _pytra_json_object_props($values);",
            "    if (count($props) === 0) {",
            "        return '{}';",
            "    }",
            "    if ($indent === null) {",
            "        $parts = [];",
            "        foreach ($props as $key => $item) {",
            "            $parts[] = _pytra_json_escape_string((string)$key, $ensure_ascii) . $key_sep . _pytra_json_dump_value($item, $ensure_ascii, $indent, $item_sep, $key_sep, $level);",
            "        }",
            "        return '{' . implode($item_sep, $parts) . '}';",
            "    }",
            "    $indent_i = _pytra_json_normalize_indent($indent);",
            "    $parts = [];",
            "    foreach ($props as $key => $item) {",
            "        $parts[] = _pytra_json_repeat_indent($indent_i, $level + 1) . _pytra_json_escape_string((string)$key, $ensure_ascii) . $key_sep . _pytra_json_dump_value($item, $ensure_ascii, $indent_i, $item_sep, $key_sep, $level + 1);",
            "    }",
            "    return \"{\\n\" . implode(\",\\n\", $parts) . \"\\n\" . _pytra_json_repeat_indent($indent_i, $level) . '}';",
            "}",
            "",
            "function _pytra_json_dump_value($value, bool $ensure_ascii, ?int $indent, string $item_sep, string $key_sep, int $level): string {",
            "    $value = _pytra_json_unwrap($value);",
            "    if ($value === null) {",
            "        return 'null';",
            "    }",
            "    if (is_bool($value)) {",
            "        return $value ? 'true' : 'false';",
            "    }",
            "    if (is_int($value) || is_float($value)) {",
            "        return _pytra_json_number_text($value);",
            "    }",
            "    if (is_string($value)) {",
            "        return _pytra_json_escape_string($value, $ensure_ascii);",
            "    }",
            "    if (_pytra_json_is_array_value($value)) {",
            "        return _pytra_json_dump_list(_pytra_json_array_raw($value), $ensure_ascii, $indent, $item_sep, $key_sep, $level);",
            "    }",
            "    if (_pytra_json_is_object_value($value)) {",
            "        return _pytra_json_dump_dict($value, $ensure_ascii, $indent, $item_sep, $key_sep, $level);",
            "    }",
            "    throw new TypeError('json.dumps unsupported type');",
            "}",
            "",
            "function dumps($obj, bool $ensure_ascii = true, $indent = null, $separators = null): string {",
            "    $indent_value = _pytra_json_normalize_indent($indent);",
            "    $item_sep = ',';",
            "    $key_sep = $indent_value === null ? ':' : ': ';",
            "    if (is_array($separators) && count($separators) >= 2) {",
            "        $item_sep = (string)$separators[0];",
            "        $key_sep = (string)$separators[1];",
            "    }",
            "    return _pytra_json_dump_value($obj, $ensure_ascii, $indent_value, $item_sep, $key_sep, 0);",
            "}",
            "",
        ]
    )


def rewrite_cpp_program_to_namespace(cpp_src: str, namespace_name: str) -> str:
    lines = _strip_trailing_string_literal_expr(cpp_src).splitlines()
    lines = _remove_block_by_signature(lines, re.compile(r"^static\s+void\s+__pytra_module_init\s*\("))
    lines = _remove_block_by_signature(lines, re.compile(r"^int\s+main\s*\("))

    include_lines: list[str] = []
    body_lines: list[str] = []
    in_body = False
    for line in lines:
        if not in_body and (line.startswith("#") or line.strip() == ""):
            include_lines.append(line)
            continue
        in_body = True
        body_lines.append(line)

    out: list[str] = []
    out.extend(include_lines)
    if len(out) > 0 and out[-1].strip() != "":
        out.append("")
    out.append("namespace " + namespace_name + " {")
    out.append("")
    out.extend(body_lines)
    if len(out) > 0 and out[-1].strip() != "":
        out.append("")
    out.append("}  // namespace " + namespace_name)
    out.append("")
    return "\n".join(out)


def inject_generated_header(text: str, target: str, source_rel: str) -> str:
    prefix = COMMENT_PREFIX.get(target)
    if prefix is None:
        raise RuntimeError("missing comment prefix for target: " + target)

    header_lines = [
        prefix + " AUTO-GENERATED FILE. DO NOT EDIT.",
        prefix + " source: " + source_rel,
        prefix + " generated-by: " + GENERATED_BY,
    ]
    header_blob = "\n".join(header_lines)

    if target == "php" and text.startswith("<?php"):
        parts = text.splitlines()
        first = parts[0]
        rest = parts[1:]
        return first + "\n" + header_blob + "\n\n" + "\n".join(rest) + ("\n" if text.endswith("\n") else "")

    suffix = "\n" if text.endswith("\n") else ""
    body = text.rstrip("\n")
    return header_blob + "\n\n" + body + suffix


def render_item(item: GenerationItem) -> str:
    generated = run_py2x(item.target, item.source_rel, item.output_rel)
    if item.postprocess == "cs_program_to_helper":
        if item.helper_name == "":
            raise RuntimeError("missing helper_name for cs_program_to_helper: " + item.item_id)
        generated = rewrite_cs_program_to_helper(generated, item.helper_name)
    elif item.postprocess == "cs_std_native_owner_wrapper":
        if item.helper_name == "":
            raise RuntimeError("missing helper_name for cs_std_native_owner_wrapper: " + item.item_id)
        generated = rewrite_cs_std_native_owner_wrapper(generated, item.helper_name)
    elif item.postprocess == "cs_std_math_live_wrapper":
        generated = rewrite_cs_std_math_live_wrapper(generated)
    elif item.postprocess == "cs_std_json_live_wrapper":
        generated = rewrite_cs_std_json_live_wrapper(generated)
    elif item.postprocess == "cs_std_pathlib_live_wrapper":
        generated = rewrite_cs_std_pathlib_live_wrapper(generated)
    elif item.postprocess == "rs_std_time_live_wrapper":
        generated = rewrite_rs_std_time_live_wrapper(generated)
    elif item.postprocess == "rs_std_math_live_wrapper":
        generated = rewrite_rs_std_math_live_wrapper(generated)
    elif item.postprocess == "java_std_time_live_wrapper":
        generated = rewrite_java_std_time_live_wrapper(generated)
    elif item.postprocess == "java_std_math_live_wrapper":
        generated = rewrite_java_std_math_live_wrapper(generated)
    elif item.postprocess == "js_std_math_live_wrapper":
        generated = rewrite_js_std_math_live_wrapper(generated)
    elif item.postprocess == "js_std_time_live_wrapper":
        generated = rewrite_js_std_time_live_wrapper(generated)
    elif item.postprocess == "js_std_sys_live_wrapper":
        generated = rewrite_js_std_sys_live_wrapper(generated)
    elif item.postprocess == "js_std_pathlib_live_wrapper":
        generated = rewrite_js_std_pathlib_live_wrapper(generated)
    elif item.postprocess == "js_std_json_live_wrapper":
        generated = rewrite_js_std_json_live_wrapper(generated)
    elif item.postprocess == "js_std_argparse_runtime_imports":
        generated = rewrite_js_std_module_runtime_imports(generated, module_name="argparse")
    elif item.postprocess == "js_std_random_runtime_imports":
        generated = rewrite_js_std_module_runtime_imports(generated, module_name="random")
    elif item.postprocess == "js_std_re_runtime_imports":
        generated = rewrite_js_std_module_runtime_imports(generated, module_name="re")
    elif item.postprocess == "js_std_timeit_runtime_imports":
        generated = rewrite_js_std_module_runtime_imports(generated, module_name="timeit")
    elif item.postprocess == "ts_std_math_live_wrapper":
        generated = rewrite_ts_std_math_live_wrapper(generated)
    elif item.postprocess == "ts_std_time_live_wrapper":
        generated = rewrite_ts_std_time_live_wrapper(generated)
    elif item.postprocess == "ts_std_sys_live_wrapper":
        generated = rewrite_ts_std_sys_live_wrapper(generated)
    elif item.postprocess == "ts_std_pathlib_live_wrapper":
        generated = rewrite_ts_std_pathlib_live_wrapper(generated)
    elif item.postprocess == "ts_std_json_live_wrapper":
        generated = rewrite_ts_std_json_live_wrapper(generated)
    elif item.postprocess == "ts_std_argparse_runtime_imports":
        generated = rewrite_ts_std_module_runtime_imports(generated, module_name="argparse")
    elif item.postprocess == "ts_std_random_runtime_imports":
        generated = rewrite_ts_std_module_runtime_imports(generated, module_name="random")
    elif item.postprocess == "ts_std_re_runtime_imports":
        generated = rewrite_ts_std_module_runtime_imports(generated, module_name="re")
    elif item.postprocess == "ts_std_timeit_runtime_imports":
        generated = rewrite_ts_std_module_runtime_imports(generated, module_name="timeit")
    elif item.postprocess == "js_program_to_cjs_module":
        generated = rewrite_js_program_to_cjs_module(generated)
    elif item.postprocess == "js_ts_built_in_cjs_module":
        generated = rewrite_js_ts_built_in_cjs_module(generated)
    elif item.postprocess == "go_program_to_library":
        generated = rewrite_go_program_to_library(generated)
    elif item.postprocess == "kotlin_program_to_library":
        generated = rewrite_kotlin_program_to_library(generated)
    elif item.postprocess == "scala_program_to_library":
        generated = rewrite_scala_program_to_library(generated)
    elif item.postprocess == "swift_program_to_library":
        generated = rewrite_swift_program_to_library(generated)
    elif item.postprocess == "php_std_time_live_wrapper":
        generated = rewrite_php_std_time_live_wrapper(generated)
    elif item.postprocess == "php_std_math_live_wrapper":
        generated = rewrite_php_std_math_live_wrapper(generated)
    elif item.postprocess == "php_std_pathlib_live_wrapper":
        generated = rewrite_php_std_pathlib_live_wrapper(generated)
    elif item.postprocess == "php_std_json_live_wrapper":
        generated = rewrite_php_std_json_live_wrapper(generated)
    elif item.postprocess == "php_program_to_library":
        generated = rewrite_php_program_to_library(generated)
    elif item.postprocess == "cpp_program_to_namespace":
        if item.helper_name == "":
            raise RuntimeError("missing helper_name(namespace) for cpp_program_to_namespace: " + item.item_id)
        generated = rewrite_cpp_program_to_namespace(generated, item.helper_name)
    elif item.postprocess != "":
        raise RuntimeError("unknown postprocess: " + item.postprocess)
    return inject_generated_header(generated, item.target, item.source_rel)


def generate(plan: list[GenerationItem], *, check: bool, dry_run: bool) -> tuple[int, int]:
    updated = 0
    checked = 0
    for item in plan:
        out_path = ROOT / item.output_rel
        rendered = render_item(item)
        if out_path.exists():
            with out_path.open("r", encoding="utf-8", newline="") as handle:
                current = handle.read()
        else:
            current = None
        changed = (current != rendered)
        checked += 1
        if dry_run:
            print(item.target + ":" + item.item_id + " -> " + item.output_rel + (" [changed]" if changed else " [same]"))
            continue
        if check:
            if changed:
                raise RuntimeError("stale generated runtime: " + item.output_rel)
            continue
        if changed:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(rendered, encoding="utf-8")
            updated += 1
            print("updated: " + item.output_rel)
        else:
            print("unchanged: " + item.output_rel)
    return checked, updated


def main() -> int:
    parser = argparse.ArgumentParser(description="generate runtime artifacts from declarative manifest")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="runtime manifest path")
    parser.add_argument("--targets", default="all", help="comma separated targets (default: all)")
    parser.add_argument("--items", default="all", help="comma separated item ids (default: all)")
    parser.add_argument("--check", action="store_true", help="fail when generated output differs")
    parser.add_argument("--dry-run", action="store_true", help="show plan and diff status without writing")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    all_items = load_manifest_items(manifest_path)
    targets = resolve_targets(args.targets, all_items)
    item_ids = resolve_item_ids(args.items, all_items)
    plan = build_generation_plan(all_items, targets, item_ids)
    checked, updated = generate(plan, check=bool(args.check), dry_run=bool(args.dry_run))
    print("summary: checked=" + str(checked) + " updated=" + str(updated))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
