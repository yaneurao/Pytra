#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/compiler/east_parts/core.h"

#include "pytra/std/dataclasses.h"
#include "pytra/std/json.h"
#include "pytra/std/pathlib.h"
#include "pytra/std/re.h"
#include "pytra/std/sys.h"
#include "pytra/std/typing.h"

namespace pytra::compiler::east_parts::core {

    /* EAST parser core (self-hosted). */
    
    
    
    
    
    
    
    
    
    set<str> INT_TYPES = set<str>{"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"};
    
    set<str> FLOAT_TYPES = set<str>{"float32", "float64"};
    
    set<str> _SH_STR_PREFIX_CHARS = set<str>{"r", "R", "b", "B", "u", "U", "f", "F"};
    
    dict<str, str> _SH_FN_RETURNS = dict<str, str>{};
    
    dict<str, dict<str, str>> _SH_CLASS_METHOD_RETURNS = dict<str, dict<str, str>>{};
    
    dict<str, ::std::optional<str>> _SH_CLASS_BASE = dict<str, ::std::optional<str>>{};
    
    dict<str, object> _SH_EMPTY_SPAN = dict<str, object>{};
    
    // !/usr/bin/env python3
    void _sh_set_parse_context(const dict<str, str>& fn_returns, const dict<str, dict<str, str>>& class_method_returns, const dict<str, ::std::optional<str>>& class_base) {
        /* 式解析で使う関数戻り値/クラス情報のコンテキストを更新する。 */
        _SH_FN_RETURNS.clear();
        _SH_FN_RETURNS.update(fn_returns);
        _SH_CLASS_METHOD_RETURNS.clear();
        _SH_CLASS_METHOD_RETURNS.update(class_method_returns);
        _SH_CLASS_BASE.clear();
        _SH_CLASS_BASE.update(class_base);
    }
    
    struct EastBuildError : public PyObj {
        str kind;
        str message;
        dict<str, object> source_span;
        str hint;
        
        EastBuildError(const str& kind, const str& message, const dict<str, object>& source_span, const str& hint) {
            this->kind = kind;
            this->message = message;
            this->source_span = source_span;
            this->hint = hint;
        }
        dict<str, object> to_payload() {
            /* 例外情報を EAST エラー応答用 dict に整形する。 */
            dict<str, object> out = dict<str, object>{};
            out[py_to_string("kind")] = make_object(this->kind);
            out[py_to_string("message")] = make_object(this->message);
            out[py_to_string("source_span")] = make_object(this->source_span);
            out[py_to_string("hint")] = make_object(this->hint);
            return out;
        }
    };
    
    RuntimeError _make_east_build_error(const str& kind, const str& message, const dict<str, object>& source_span, const str& hint) {
        /* self-hosted 生成で投げる例外を std::exception 互換（RuntimeError）に統一する。 */
        int64 src_line = py_to_int64(dict_get_node(source_span, "lineno", 0));
        int64 src_col = py_to_int64(dict_get_node(source_span, "col", 0));
        return ::std::runtime_error(kind + ": " + message + " at " + ::std::to_string(src_line) + ":" + ::std::to_string(src_col) + " hint=" + hint);
    }
    
    dict<str, object> convert_source_to_east(const str& source, const str& filename) {
        /* 後方互換用の入口。self-hosted パーサで EAST を生成する。 */
        return convert_source_to_east_self_hosted(source, filename);
    }
    
    dict<str, int64> _sh_span(int64 line, int64 col, int64 end_col) {
        /* self-hosted parser 用の source_span を生成する。 */
        return dict<str, int64>{{"lineno", line}, {"col", col}, {"end_lineno", line}, {"end_col", end_col}};
    }
    
    str _sh_ann_to_type(const str& ann) {
        /* 型注釈文字列を EAST 正規型へ変換する。 */
        dict<str, str> mapping = dict<str, str>{{"int", "int64"}, {"float", "float64"}, {"byte", "uint8"}, {"bool", "bool"}, {"str", "str"}, {"None", "None"}, {"bytes", "bytes"}, {"bytearray", "bytearray"}};
        str txt = py_strip(ann);
        if ((py_len(txt) >= 2) && (((txt.at(0) == '\'') && (py_at(txt, -1) == "'")) || ((txt.at(0) == '"') && (py_at(txt, -1) == "\""))))
            txt = py_strip(py_slice(txt, 1, -1));
        if (py_contains(mapping, txt))
            return py_dict_get(mapping, py_to_string(txt));
        ::std::optional<rc<pytra::std::re::Match>> m = pytra::std::re::match("^([A-Za-z_][A-Za-z0-9_]*)\\[(.*)\\]$", txt);
        if (py_is_none(m))
            return txt;
        str head = pytra::std::re::group(m, 1);
        str inner = pytra::std::re::strip_group(m, 2);
        list<str> parts = list<str>{};
        int64 depth = 0;
        int64 start = 0;
        for (auto __it_1 : py_enumerate(inner)) {
            auto i = ::std::get<0>(__it_1);
            auto ch = ::std::get<1>(__it_1);
            if (ch == "[") {
                depth++;
            } else {
                if (ch == "]") {
                    depth--;
                } else {
                    if ((ch == ",") && (depth == 0)) {
                        parts.append(str(py_strip(py_slice(inner, start, i))));
                        start = i + 1;
                    }
                }
            }
        }
        auto tail = py_strip(py_slice(inner, start, py_len(inner)));
        if (tail != "")
            parts.append(str(tail));
        list<str> norm = [&]() -> list<str> {     list<str> __out;     for (auto p : parts) {         __out.append(_sh_ann_to_type(p));     }     return __out; }();
        return head + "[" + py_to_string(str(", ").join(norm)) + "]";
    }
    
    list<::std::tuple<str, int64>> _sh_split_args_with_offsets(const str& arg_text) {
        /* 引数文字列をトップレベルのカンマで分割し、相対オフセットも返す。 */
        list<::std::tuple<str, int64>> out = list<::std::tuple<str, int64>>{};
        int64 depth = 0;
        ::std::optional<str> in_str = ::std::nullopt;
        bool esc = false;
        int64 start = 0;
        int64 i = 0;
        while (i < py_len(arg_text)) {
            str ch = arg_text[i];
            if (!py_is_none(in_str)) {
                if (esc) {
                    esc = false;
                } else {
                    if (ch == "\\") {
                        esc = true;
                    } else {
                        if (ch == in_str)
                            in_str = ::std::nullopt;
                    }
                }
                i++;
                continue;
            }
            if (py_contains(set<str>{"'", "\""}, ch)) {
                in_str = ch;
                i++;
                continue;
            }
            if (py_contains(set<str>{"(", "[", "{"}, ch)) {
                depth++;
            } else {
                if (py_contains(set<str>{")", "]", "}"}, ch)) {
                    depth--;
                } else {
                    if ((ch == ",") && (depth == 0)) {
                        str part = py_slice(arg_text, start, i);
                        out.append(::std::tuple<str, int64>(::std::make_tuple(py_strip(part), start + py_len(part) - py_len(py_lstrip(part)))));
                        start = i + 1;
                    }
                }
            }
            i++;
        }
        str tail = py_slice(arg_text, start, py_len(arg_text));
        if (py_strip(tail) != "")
            out.append(::std::tuple<str, int64>(::std::make_tuple(py_strip(tail), start + py_len(tail) - py_len(py_lstrip(tail)))));
        return out;
    }
    
    ::std::optional<::std::tuple<str, str, str>> _sh_parse_typed_binding(const str& text, bool allow_dotted_name = false) {
        /* `name: Type` / `name: Type = expr` を手書きパースし、(name, type, default) を返す。 */
        auto raw = py_strip(text);
        if (raw == "")
            return ::std::nullopt;
        auto colon = raw.find(":");
        if (colon <= 0)
            return ::std::nullopt;
        auto name_txt = py_strip(py_slice(raw, 0, colon));
        auto ann_txt = py_strip(py_slice(raw, colon + 1, py_len(raw)));
        if (ann_txt == "")
            return ::std::nullopt;
        if (allow_dotted_name) {
            auto name_parts = name_txt.split(".");
            if (py_len(name_parts) == 0)
                return ::std::nullopt;
            for (::std::any seg : name_parts) {
                if (py_is_none(pytra::std::re::match("^[A-Za-z_][A-Za-z0-9_]*$", seg)))
                    return ::std::nullopt;
            }
        } else {
            if (py_is_none(pytra::std::re::match("^[A-Za-z_][A-Za-z0-9_]*$", name_txt)))
                return ::std::nullopt;
        }
        str default_txt = "";
        ::std::optional<::std::tuple<str, str>> split_ann = _sh_split_top_level_assign(ann_txt);
        if (!py_is_none(split_ann)) {
            auto __tuple_3 = *(split_ann);
            str ann_lhs = ::std::get<0>(__tuple_3);
            str ann_rhs = ::std::get<1>(__tuple_3);
            ann_txt = py_strip(ann_lhs);
            default_txt = py_strip(ann_rhs);
        }
        if (ann_txt == "")
            return ::std::nullopt;
        return ::std::make_tuple(name_txt, ann_txt, default_txt);
    }
    
    bool _sh_is_identifier(const str& text) {
        /* ASCII 識別子（先頭英字/`_`）かを返す。 */
        if (text == "")
            return false;
        str c0 = py_slice(text, 0, 1);
        bool is_head = ("A" <= c0 && c0 <= "Z") || ("a" <= c0 && c0 <= "z") || (c0 == "_");
        if (!(is_head))
            return false;
        int64 i = 1;
        while (i < py_len(text)) {
            str ch = py_slice(text, i, i + 1);
            bool is_body = ("A" <= ch && ch <= "Z") || ("a" <= ch && ch <= "z") || ("0" <= ch && ch <= "9") || (ch == "_");
            if (!(is_body))
                return false;
            i++;
        }
        return true;
    }
    
    bool _sh_is_dotted_identifier(const str& text) {
        /* `a.b.c` 形式の識別子列かを返す。 */
        if (py_strip(text) == "")
            return false;
        auto parts = text.split(".");
        if (py_len(parts) == 0)
            return false;
        for (::std::any seg : parts) {
            if (!(_sh_is_identifier(py_to_string(seg))))
                return false;
        }
        return true;
    }
    
    ::std::optional<::std::tuple<str, str>> _sh_parse_import_alias(const str& text, bool allow_dotted_name) {
        /* `name` / `name as alias` を手書きパースして (name, alias_or_empty) を返す。 */
        auto raw = py_strip(text);
        if (raw == "")
            return ::std::nullopt;
        auto name_txt = raw;
        str alias_txt = "";
        ::std::optional<::std::tuple<str, str>> as_split = _sh_split_top_level_as(raw);
        if (!py_is_none(as_split)) {
            auto __tuple_4 = *(as_split);
            name_txt = ::std::get<0>(__tuple_4);
            alias_txt = ::std::get<1>(__tuple_4);
            name_txt = py_strip(name_txt);
            alias_txt = py_strip(alias_txt);
        }
        if (name_txt == "")
            return ::std::nullopt;
        if (allow_dotted_name) {
            if (!(_sh_is_dotted_identifier(name_txt)))
                return ::std::nullopt;
        } else {
            if (!(_sh_is_identifier(name_txt)))
                return ::std::nullopt;
        }
        if ((alias_txt != "") && (!(_sh_is_identifier(alias_txt))))
            return ::std::nullopt;
        return ::std::make_tuple(name_txt, alias_txt);
    }
    
    ::std::optional<::std::tuple<str, str, str>> _sh_parse_augassign(const str& text) {
        /* `target <op>= expr` をトップレベルで分解して返す。 */
        auto raw = py_strip(text);
        if (raw == "")
            return ::std::nullopt;
        list<str> ops = list<str>{"<<=", ">>=", "//=", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^="};
        int64 depth = 0;
        ::std::optional<str> in_str = ::std::nullopt;
        bool esc = false;
        int64 i = 0;
        while (i < py_len(raw)) {
            auto ch = py_at(raw, py_to_int64(i));
            if (!py_is_none(in_str)) {
                if (esc) {
                    esc = false;
                } else {
                    if (ch == "\\") {
                        esc = true;
                    } else {
                        if (ch == in_str)
                            in_str = ::std::nullopt;
                    }
                }
                i++;
                continue;
            }
            if (py_contains(set<str>{"'", "\""}, ch)) {
                in_str = ch;
                i++;
                continue;
            }
            if (py_contains(set<str>{"(", "[", "{"}, ch)) {
                depth++;
                i++;
                continue;
            }
            if (py_contains(set<str>{")", "]", "}"}, ch)) {
                depth--;
                i++;
                continue;
            }
            if (depth == 0) {
                for (str op : ops) {
                    if (py_slice(raw, i, i + py_len(op)) == op) {
                        auto left = py_strip(py_slice(raw, 0, i));
                        auto right = py_strip(py_slice(raw, i + py_len(op), py_len(raw)));
                        if ((left == "") || (right == ""))
                            return ::std::nullopt;
                        if (!(_sh_is_dotted_identifier(left)))
                            return ::std::nullopt;
                        return ::std::make_tuple(left, op, right);
                    }
                }
            }
            i++;
        }
        return ::std::nullopt;
    }
    
    int64 _sh_scan_string_token(const str& text, int64 start, int64 quote_pos, int64 line_no, int64 col_base) {
        /* 文字列リテラルの終端位置を走査して返す。 */
        if ((quote_pos + 2 < py_len(text)) && (py_contains(set<str>{"'''", "\"\"\""}, py_slice(text, quote_pos, quote_pos + 3)))) {
            str q3 = py_slice(text, quote_pos, quote_pos + 3);
            int64 j = quote_pos + 3;
            while (j + 2 < py_len(text)) {
                if (py_slice(text, j, j + 3) == q3)
                    return j + 3;
                j++;
            }
            throw _make_east_build_error("unsupported_syntax", "unterminated triple-quoted string literal in self_hosted parser", _sh_span(line_no, col_base + start, col_base + py_len(text)), "Close triple-quoted string with matching quote.");
        }
        str q = text[quote_pos];
        int64 j = quote_pos + 1;
        while (j < py_len(text)) {
            if (text.at(j) == '\\') {
                j += 2;
                continue;
            }
            if (text[j] == q)
                return j + 1;
            j++;
        }
        throw _make_east_build_error("unsupported_syntax", "unterminated string literal in self_hosted parser", _sh_span(line_no, col_base + start, col_base + py_len(text)), "Close string literal with matching quote.");
    }
    
    str _sh_decode_py_string_body(const str& text, bool raw_mode) {
        /* Python 文字列リテラル本体（引用符除去後）を簡易復号する。 */
        if (raw_mode)
            return text;
        str out = "";
        int64 i = 0;
        while (i < py_len(text)) {
            str ch = py_slice(text, i, i + 1);
            if (ch != "\\") {
                out += ch;
                i++;
                continue;
            }
            i++;
            if (i >= py_len(text)) {
                out += "\\";
                break;
            }
            str esc = py_slice(text, i, i + 1);
            i++;
            if (esc == "n") {
                out += "\n";
            } else {
                if (esc == "r") {
                    out += "\r";
                } else {
                    if (esc == "t") {
                        out += "\t";
                    } else {
                        if (esc == "b") {
                            out += "";
                        } else {
                            if (esc == "f") {
                                out += "";
                            } else {
                                if (esc == "v") {
                                    out += "";
                                } else {
                                    if (esc == "a") {
                                        out += "";
                                    } else {
                                        if (py_contains(set<str>{"\"", "'", "\\"}, esc)) {
                                            out += esc;
                                        } else {
                                            if ((esc == "x") && (i + 1 < py_len(text))) {
                                                str hex2 = py_slice(text, i, i + 2);
                                                try {
                                                    out += py_chr(py_to_int64_base(hex2, py_to_int64(16)));
                                                    i += 2;
                                                }
                                                catch (const ::std::exception& ex) {
                                                    out += "x";
                                                }
                                            } else {
                                                if ((esc == "u") && (i + 3 < py_len(text))) {
                                                    str hex4 = py_slice(text, i, i + 4);
                                                    try {
                                                        out += py_chr(py_to_int64_base(hex4, py_to_int64(16)));
                                                        i += 4;
                                                    }
                                                    catch (const ::std::exception& ex) {
                                                        out += "u";
                                                    }
                                                } else {
                                                    out += esc;
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        return out;
    }
    
    void _sh_append_fstring_literal(list<dict<str, object>>& values, const str& segment, const dict<str, int64>& span, bool raw_mode = false) {
        /* f-string の生文字列片を Constant(str) ノードとして values に追加する。 */
        auto lit = py_replace(py_replace(segment, "{{", "{"), "}}", "}");
        lit = _sh_decode_py_string_body(lit, raw_mode);
        if (lit == "")
            return;
        dict<str, object> node = dict<str, object>{};
        node[py_to_string("kind")] = make_object("Constant");
        node[py_to_string("source_span")] = make_object(span);
        node[py_to_string("resolved_type")] = make_object("str");
        node[py_to_string("borrow_kind")] = make_object("value");
        node[py_to_string("casts")] = make_object(list<object>{});
        node[py_to_string("repr")] = make_object(pytra::std::json::dumps(make_object(lit)));
        node[py_to_string("value")] = make_object(lit);
        values.append(dict<str, object>(node));
    }
    
    ::std::optional<dict<str, object>> _sh_parse_def_sig(int64 ln_no, const str& ln, const str& in_class = "") {
        /* `def ...` 行から関数名・引数型・戻り型を抽出する。 */
        str ln_norm = pytra::std::re::sub("\\s+", " ", py_strip(ln));
        if ((!(py_startswith(ln_norm, "def "))) || (!(py_endswith(ln_norm, ":"))))
            return ::std::nullopt;
        auto head = py_strip(py_slice(ln_norm, 4, -1));
        auto lp = head.find("(");
        auto rp = head.rfind(")");
        if ((lp <= 0) || (rp < lp))
            return ::std::nullopt;
        str fn_name = "";
        str args_raw = "";
        str ret_group = "";
        fn_name = py_strip(py_slice(head, 0, lp));
        if (py_is_none(pytra::std::re::match("^[A-Za-z_][A-Za-z0-9_]*$", fn_name)))
            return ::std::nullopt;
        args_raw = py_slice(head, lp + 1, rp);
        auto tail = py_strip(py_slice(head, rp + 1, py_len(head)));
        if (tail == "") {
            ret_group = "";
        } else {
            if (py_startswith(tail, "->")) {
                ret_group = py_strip(py_slice(tail, 2, py_len(tail)));
                if (ret_group == "")
                    throw _make_east_build_error("unsupported_syntax", "self_hosted parser cannot parse return annotation in function signature", _sh_span(ln_no, 0, py_len(ln_norm)), "Use `def name(args) -> Type:` style signature.");
            } else {
                return ::std::nullopt;
            }
        }
        dict<str, str> arg_types = dict<str, str>{};
        list<str> arg_order = list<str>{};
        dict<str, str> arg_defaults = dict<str, str>{};
        if (py_strip(args_raw) != "") {
            // Supported:
            // - name: Type
            // - name: Type = default
            // - "*" keyword-only marker
            // Not supported:
            // - "/" positional-only marker
            for (auto __it_5 : _sh_split_args_with_offsets(args_raw)) {
                auto p_txt = ::std::get<0>(__it_5);
                auto _off = ::std::get<1>(__it_5);
                str p = py_strip(p_txt);
                if (p == "")
                    continue;
                if (p == "*")
                    continue;
                if (p == "/")
                    throw _make_east_build_error("unsupported_syntax", "self_hosted parser cannot parse positional-only marker '/' in parameter list", _sh_span(ln_no, 0, py_len(ln_norm)), "Remove '/' from signature for now.");
                if (py_startswith(p, "**"))
                    throw _make_east_build_error("unsupported_syntax", "self_hosted parser cannot parse variadic kwargs parameter: " + py_to_string(p_txt), _sh_span(ln_no, 0, py_len(ln_norm)), "Use explicit parameters instead of **kwargs.");
                if (py_startswith(p, "*"))
                    throw _make_east_build_error("unsupported_syntax", "self_hosted parser cannot parse variadic args parameter: " + py_to_string(p_txt), _sh_span(ln_no, 0, py_len(ln_norm)), "Use explicit parameters instead of *args.");
                if ((in_class != "") && (p == "self")) {
                    arg_types[py_to_string("self")] = in_class;
                    arg_order.append(str("self"));
                    continue;
                }
                ::std::optional<::std::tuple<str, str, str>> parsed_param = _sh_parse_typed_binding(p, false);
                if (py_is_none(parsed_param))
                    throw _make_east_build_error("unsupported_syntax", "self_hosted parser cannot parse parameter: " + py_to_string(p_txt), _sh_span(ln_no, 0, py_len(ln_norm)), "Use `name: Type` style parameters.");
                auto __tuple_6 = *(parsed_param);
                str pn = ::std::get<0>(__tuple_6);
                str pt = ::std::get<1>(__tuple_6);
                str pdef = ::std::get<2>(__tuple_6);
                if (!(pytra::std::re::match("^[A-Za-z_][A-Za-z0-9_]*$", pn)))
                    throw _make_east_build_error("unsupported_syntax", "self_hosted parser cannot parse parameter name: " + pn, _sh_span(ln_no, 0, py_len(ln_norm)), "Use valid identifier for parameter name.");
                if (pt == "")
                    throw _make_east_build_error("unsupported_syntax", "self_hosted parser cannot parse parameter type: " + py_to_string(p_txt), _sh_span(ln_no, 0, py_len(ln_norm)), "Use `name: Type` style parameters.");
                arg_types[py_to_string(pn)] = _sh_ann_to_type(pt);
                arg_order.append(str(pn));
                if (pdef != "") {
                    auto default_txt = py_strip(pdef);
                    if (default_txt != "")
                        arg_defaults[py_to_string(pn)] = default_txt;
                }
            }
        }
        dict<str, object> out_sig = dict<str, object>{};
        out_sig[py_to_string("name")] = make_object(fn_name);
        out_sig[py_to_string("ret")] = make_object((ret_group != "" ? _sh_ann_to_type(py_strip(ret_group)) : "None"));
        out_sig[py_to_string("arg_types")] = make_object(arg_types);
        out_sig[py_to_string("arg_order")] = make_object(arg_order);
        out_sig[py_to_string("arg_defaults")] = make_object(arg_defaults);
        return out_sig;
    }
    
    ::std::tuple<int64, str> _sh_scan_logical_line_state(const str& txt, int64 depth, const str& mode) {
        /* 論理行マージ用に括弧深度と文字列モードを更新する。 */
        int64 i = 0;
        str mode_cur = mode;
        while (i < py_len(txt)) {
            if (py_contains(set<str>{"'''", "\"\"\""}, mode_cur)) {
                auto close = txt.find(mode_cur, i);
                if (close < 0) {
                    i = py_len(txt);
                    continue;
                }
                i = close + 3;
                mode_cur = "";
                continue;
            }
            str ch = txt[i];
            if (py_contains(set<str>{"'", "\""}, mode_cur)) {
                if (ch == "\\") {
                    i += 2;
                    continue;
                }
                if (ch == mode_cur)
                    mode_cur = "";
                i++;
                continue;
            }
            if ((i + 2 < py_len(txt)) && (py_contains(set<str>{"'''", "\"\"\""}, py_slice(txt, i, i + 3)))) {
                mode_cur = py_slice(txt, i, i + 3);
                i += 3;
                continue;
            }
            if (py_contains(set<str>{"'", "\""}, ch)) {
                mode_cur = ch;
                i++;
                continue;
            }
            if (ch == "#")
                break;
            if (py_contains(set<str>{"(", "[", "{"}, ch)) {
                depth++;
            } else {
                if (py_contains(set<str>{")", "]", "}"}, ch))
                    depth--;
            }
            i++;
        }
        return ::std::make_tuple(depth, mode_cur);
    }
    
    ::std::tuple<list<::std::tuple<int64, str>>, dict<int64, ::std::tuple<int64, int64>>> _sh_merge_logical_lines(const list<::std::tuple<int64, str>>& raw_lines) {
        /* 物理行を論理行へマージし、開始行ごとの終了行情報も返す。 */
        list<::std::tuple<int64, str>> merged = list<::std::tuple<int64, str>>{};
        dict<int64, ::std::tuple<int64, int64>> merged_line_end = dict<int64, ::std::tuple<int64, int64>>{};
        int64 idx = 0;
        while (idx < py_len(raw_lines)) {
            auto __tuple_7 = raw_lines[idx];
            int64 start_no = ::std::get<0>(__tuple_7);
            str start_txt = ::std::get<1>(__tuple_7);
            str acc = start_txt;
            int64 depth = 0;
            str mode = "";
            auto __tuple_8 = _sh_scan_logical_line_state(start_txt, depth, mode);
            depth = ::std::get<0>(__tuple_8);
            mode = ::std::get<1>(__tuple_8);
            int64 end_no = start_no;
            str end_txt = start_txt;
            while (((depth > 0) || (py_contains(set<str>{"'''", "\"\"\""}, mode))) && (idx + 1 < py_len(raw_lines))) {
                idx++;
                auto __tuple_9 = raw_lines[idx];
                int64 next_no = ::std::get<0>(__tuple_9);
                str next_txt = ::std::get<1>(__tuple_9);
                if (py_contains(set<str>{"'''", "\"\"\""}, mode))
                    acc += "\n" + next_txt;
                else
                    acc += " " + py_strip(next_txt);
                auto __tuple_10 = _sh_scan_logical_line_state(next_txt, depth, mode);
                depth = ::std::get<0>(__tuple_10);
                mode = ::std::get<1>(__tuple_10);
                end_no = next_no;
                end_txt = next_txt;
            }
            merged.append(::std::tuple<int64, str>(::std::make_tuple(start_no, acc)));
            merged_line_end[int64(py_to_int64(start_no))] = ::std::make_tuple(end_no, py_len(end_txt));
            idx++;
        }
        return ::std::make_tuple(merged, merged_line_end);
    }
    
    list<str> _sh_split_top_commas(const str& txt) {
        /* 文字列/括弧深度を考慮してトップレベルのカンマ分割を行う。 */
        list<str> out = list<str>{};
        int64 depth = 0;
        ::std::optional<str> in_str = ::std::nullopt;
        bool esc = false;
        int64 start = 0;
        for (auto __it_11 : py_enumerate(txt)) {
            auto i = ::std::get<0>(__it_11);
            auto ch = ::std::get<1>(__it_11);
            if (!py_is_none(in_str)) {
                if (esc) {
                    esc = false;
                    continue;
                }
                if (ch == "\\") {
                    esc = true;
                    continue;
                }
                if (ch == in_str)
                    in_str = ::std::nullopt;
                continue;
            }
            if (py_contains(set<str>{"'", "\""}, ch)) {
                in_str = ch;
                continue;
            }
            if (py_contains(set<str>{"(", "[", "{"}, ch)) {
                depth++;
                continue;
            }
            if (py_contains(set<str>{")", "]", "}"}, ch)) {
                depth--;
                continue;
            }
            if ((ch == ",") && (depth == 0)) {
                out.append(str(py_strip(py_slice(txt, start, i))));
                start = i + 1;
            }
        }
        auto tail = py_strip(py_slice(txt, start, py_len(txt)));
        if (tail != "")
            out.append(str(tail));
        return out;
    }
    
    int64 _sh_split_top_keyword(const str& text, const str& kw) {
        /* トップレベルでキーワード出現位置を探す（未検出なら -1）。 */
        int64 depth = 0;
        ::std::optional<str> in_str = ::std::nullopt;
        bool esc = false;
        int64 i = 0;
        while (i < py_len(text)) {
            str ch = text[i];
            if (!py_is_none(in_str)) {
                if (esc) {
                    esc = false;
                    i++;
                    continue;
                }
                if (ch == "\\") {
                    esc = true;
                    i++;
                    continue;
                }
                if (ch == in_str)
                    in_str = ::std::nullopt;
                i++;
                continue;
            }
            if (py_contains(set<str>{"'", "\""}, ch)) {
                in_str = ch;
                i++;
                continue;
            }
            if (py_contains(set<str>{"(", "[", "{"}, ch)) {
                depth++;
                i++;
                continue;
            }
            if (py_contains(set<str>{")", "]", "}"}, ch)) {
                depth--;
                i++;
                continue;
            }
            if ((depth == 0) && (py_startswith(py_slice(text, i, py_len(text)), kw))) {
                bool prev_ok = (i == 0) || (text[i - 1].isspace());
                bool next_ok = (i + py_len(kw) >= py_len(text)) || (text[i + py_len(kw)].isspace());
                if ((prev_ok) && (next_ok))
                    return i;
            }
            i++;
        }
        return -1;
    }
    
    list<str> _sh_split_top_plus(const str& text) {
        /* トップレベルの `+` で式を分割する。 */
        list<str> out = list<str>{};
        int64 depth = 0;
        ::std::optional<str> in_str = ::std::nullopt;
        bool esc = false;
        int64 start = 0;
        for (auto __it_12 : py_enumerate(text)) {
            auto i = ::std::get<0>(__it_12);
            auto ch = ::std::get<1>(__it_12);
            if (!py_is_none(in_str)) {
                if (esc) {
                    esc = false;
                    continue;
                }
                if (ch == "\\") {
                    esc = true;
                    continue;
                }
                if (ch == in_str)
                    in_str = ::std::nullopt;
                continue;
            }
            if (py_contains(set<str>{"'", "\""}, ch)) {
                in_str = ch;
                continue;
            }
            if (py_contains(set<str>{"(", "[", "{"}, ch)) {
                depth++;
                continue;
            }
            if (py_contains(set<str>{")", "]", "}"}, ch)) {
                depth--;
                continue;
            }
            if ((ch == "+") && (depth == 0)) {
                out.append(str(py_strip(py_slice(text, start, i))));
                start = i + 1;
            }
        }
        auto tail = py_strip(py_slice(text, start, py_len(text)));
        if (tail != "")
            out.append(str(tail));
        return out;
    }
    
    str _sh_infer_item_type(const dict<str, object>& node) {
        /* dict/list/set/range 由来の反復要素型を簡易推論する。 */
        str t = py_to_string(dict_get_node(node, "resolved_type", "unknown"));
        if (t == "range")
            return "int64";
        if ((py_startswith(t, "list[")) && (py_endswith(t, "]"))) {
            auto inner = py_strip(py_slice(t, 5, -1));
            if (inner != "")
                return inner;
            return "unknown";
        }
        if ((py_startswith(t, "set[")) && (py_endswith(t, "]"))) {
            auto inner = py_strip(py_slice(t, 4, -1));
            if (inner != "")
                return inner;
            return "unknown";
        }
        if (py_contains(set<str>{"bytes", "bytearray"}, t))
            return "uint8";
        if (t == "str")
            return "str";
        return "unknown";
    }
    
    dict<str, str> _sh_bind_comp_target_types(const dict<str, str>& base_types, const dict<str, object>& target_node, const dict<str, object>& iter_node) {
        /* 内包表記 target へ反復要素型を束縛した name_types を返す。 */
        dict<str, str> out = base_types;
        str item_t = _sh_infer_item_type(iter_node);
        if (py_dict_get_maybe(target_node, "kind") == "Name") {
            str nm = py_to_string(dict_get_node(target_node, "id", ""));
            if (nm != "")
                out[py_to_string(nm)] = item_t;
            return out;
        }
        if (py_dict_get_maybe(target_node, "kind") != "Tuple")
            return out;
        auto elem_nodes = dict_get_node(target_node, "elements", list<object>{});
        list<str> elem_types = list<str>{};
        if ((py_startswith(item_t, "tuple[")) && (py_endswith(item_t, "]"))) {
            auto inner = py_strip(py_slice(item_t, 6, -1));
            if (inner != "")
                elem_types = _sh_split_top_commas(inner);
        }
        int64 i = 0;
        while (i < py_len(elem_nodes)) {
            auto e = py_at(elem_nodes, py_to_int64(i));
            if ((py_is_dict(e)) && (py_dict_get_maybe(e, "kind") == "Name")) {
                str nm = py_to_string(py_dict_get_default(e, "id", ""));
                if (nm != "") {
                    if (i < py_len(elem_types)) {
                        auto et = py_strip(elem_types[i]);
                        if (et == "")
                            et = "unknown";
                        out[py_to_string(nm)] = et;
                    } else {
                        out[py_to_string(nm)] = "unknown";
                    }
                }
            }
            i++;
        }
        return out;
    }
    
    dict<str, int64> _sh_block_end_span(const list<::std::tuple<int64, str>>& body_lines, int64 start_ln, int64 start_col, int64 fallback_end_col, int64 end_idx_exclusive) {
        /* 複数行文の終端まで含む source_span を生成する。 */
        if ((end_idx_exclusive > 0) && (end_idx_exclusive - 1 < py_len(body_lines))) {
            auto __tuple_13 = body_lines[end_idx_exclusive - 1];
            int64 end_ln = ::std::get<0>(__tuple_13);
            str end_txt = ::std::get<1>(__tuple_13);
            return dict<str, int64>{{"lineno", start_ln}, {"col", start_col}, {"end_lineno", end_ln}, {"end_col", py_len(end_txt)}};
        }
        return _sh_span(start_ln, start_col, fallback_end_col);
    }
    
    dict<str, int64> _sh_stmt_span(const dict<int64, ::std::tuple<int64, int64>>& merged_line_end, int64 start_ln, int64 start_col, int64 fallback_end_col) {
        /* 単文の source_span を論理行終端まで含めて生成する。 */
        ::std::tuple<int64, int64> end_pair = py_dict_get_default(merged_line_end, int64(py_to_int64(start_ln)), ::std::make_tuple(start_ln, fallback_end_col));
        int64 end_ln = py_to_int64(::std::get<0>(end_pair));
        int64 end_col = py_to_int64(::std::get<1>(end_pair));
        return dict<str, int64>{{"lineno", start_ln}, {"col", start_col}, {"end_lineno", end_ln}, {"end_col", end_col}};
    }
    
    int64 _sh_push_stmt_with_trivia(list<dict<str, object>>& stmts, list<dict<str, object>>& pending_leading_trivia, int64 pending_blank_count, const dict<str, object>& stmt) {
        /* 保留中 trivia を付与して文リストへ追加し、更新後 blank 数を返す。 */
        dict<str, object> stmt_copy = stmt;
        if (pending_blank_count > 0) {
            dict<str, object> blank_item = dict<str, object>{};
            blank_item[py_to_string("kind")] = make_object("blank");
            blank_item[py_to_string("count")] = make_object(pending_blank_count);
            pending_leading_trivia.append(dict<str, object>(blank_item));
            pending_blank_count = 0;
        }
        if (py_len(pending_leading_trivia) > 0) {
            stmt_copy[py_to_string("leading_trivia")] = make_object(pending_leading_trivia);
            list<object> comments = [&]() -> list<object> {     list<object> __out;     for (auto x : pending_leading_trivia) {         if ((py_dict_get_maybe(x, "kind") == "comment") && (py_is_str(py_dict_get_maybe(x, "text")))) __out.append(py_dict_get_maybe(x, "text"));     }     return __out; }();
            if (py_len(comments) > 0)
                stmt_copy[py_to_string("leading_comments")] = make_object(comments);
            pending_leading_trivia.clear();
        }
        stmts.append(dict<str, object>(stmt_copy));
        return pending_blank_count;
    }
    
    ::std::tuple<list<::std::tuple<int64, str>>, int64> _sh_collect_indented_block(const list<::std::tuple<int64, str>>& body_lines, int64 start, int64 parent_indent) {
        /* 指定インデント配下のブロック行を収集する。 */
        list<::std::tuple<int64, str>> out = list<::std::tuple<int64, str>>{};
        int64 j = start;
        while (j < py_len(body_lines)) {
            auto __tuple_15 = body_lines[j];
            int64 n_no = ::std::get<0>(__tuple_15);
            str n_ln = ::std::get<1>(__tuple_15);
            if (py_strip(n_ln) == "") {
                int64 t = j + 1;
                while ((t < py_len(body_lines)) && (py_strip(::std::get<1>(body_lines[t])) == "")) {
                    t++;
                }
                if (t >= py_len(body_lines))
                    break;
                auto t_ln = ::std::get<1>(body_lines[t]);
                int64 t_indent = py_len(t_ln) - py_len(py_lstrip(t_ln, " "));
                if (t_indent <= parent_indent)
                    break;
                out.append(::std::tuple<int64, str>(::std::make_tuple(n_no, n_ln)));
                j++;
                continue;
            }
            int64 n_indent = py_len(n_ln) - py_len(py_lstrip(n_ln, " "));
            if (n_indent <= parent_indent)
                break;
            out.append(::std::tuple<int64, str>(::std::make_tuple(n_no, n_ln)));
            j++;
        }
        return ::std::make_tuple(out, j);
    }
    
    ::std::optional<::std::tuple<str, str>> _sh_split_top_level_assign(const str& text) {
        /* トップレベルの `=` を 1 つだけ持つ代入式を分割する。 */
        int64 depth = 0;
        ::std::optional<str> in_str = ::std::nullopt;
        bool esc = false;
        int64 i = 0;
        while (i < py_len(text)) {
            str ch = text[i];
            if (!py_is_none(in_str)) {
                if (esc) {
                    esc = false;
                } else {
                    if (ch == "\\") {
                        esc = true;
                    } else {
                        if (ch == in_str) {
                            if ((i + 2 < py_len(text)) && (py_slice(text, i, i + 3) == in_str * 3))
                                i += 2;
                            else
                                in_str = ::std::nullopt;
                        }
                    }
                }
                i++;
                continue;
            }
            if ((i + 2 < py_len(text)) && (py_contains(set<str>{"'''", "\"\"\""}, py_slice(text, i, i + 3)))) {
                in_str = text[i];
                i += 3;
                continue;
            }
            if (py_contains(set<str>{"'", "\""}, ch)) {
                in_str = ch;
                i++;
                continue;
            }
            if (ch == "#")
                break;
            if (py_contains(set<str>{"(", "[", "{"}, ch)) {
                depth++;
                i++;
                continue;
            }
            if (py_contains(set<str>{")", "]", "}"}, ch)) {
                depth--;
                i++;
                continue;
            }
            if ((ch == "=") && (depth == 0)) {
                str prev = (i - 1 >= 0 ? text[i - 1] : "");
                str nxt = (i + 1 < py_len(text) ? text[i + 1] : "");
                if ((py_contains(set<str>{"!", "<", ">", "="}, prev)) || (nxt == "=")) {
                    i++;
                    continue;
                }
                auto lhs = py_strip(py_slice(text, 0, i));
                auto rhs = py_strip(py_slice(text, i + 1, py_len(text)));
                if ((lhs != "") && (rhs != ""))
                    return ::std::make_tuple(lhs, rhs);
                return ::std::nullopt;
            }
            i++;
        }
        return ::std::nullopt;
    }
    
    str _sh_strip_inline_comment(const str& text) {
        /* 文字列リテラル外の末尾コメントを除去する。 */
        ::std::optional<str> in_str = ::std::nullopt;
        bool esc = false;
        for (auto __it_16 : py_enumerate(text)) {
            auto i = ::std::get<0>(__it_16);
            auto ch = ::std::get<1>(__it_16);
            if (!py_is_none(in_str)) {
                if (esc) {
                    esc = false;
                } else {
                    if (ch == "\\") {
                        esc = true;
                    } else {
                        if (ch == in_str)
                            in_str = ::std::nullopt;
                    }
                }
                continue;
            }
            if (py_contains(set<str>{"'", "\""}, ch)) {
                in_str = ch;
                continue;
            }
            if (ch == "#")
                return py_rstrip(py_slice(text, 0, i));
        }
        return text;
    }
    
    ::std::optional<::std::tuple<str, str>> _sh_split_top_level_from(const str& text) {
        /* トップレベルの `for ... in ...` を target/iter に分解する。 */
        int64 depth = 0;
        ::std::optional<str> in_str = ::std::nullopt;
        bool esc = false;
        int64 i = 0;
        while (i < py_len(text)) {
            str ch = text[i];
            if (!py_is_none(in_str)) {
                if (esc) {
                    esc = false;
                } else {
                    if (ch == "\\") {
                        esc = true;
                    } else {
                        if (ch == in_str)
                            in_str = ::std::nullopt;
                    }
                }
                i++;
                continue;
            }
            if (py_contains(set<str>{"'", "\""}, ch)) {
                in_str = ch;
                i++;
                continue;
            }
            if (py_contains(set<str>{"(", "[", "{"}, ch)) {
                depth++;
                i++;
                continue;
            }
            if (py_contains(set<str>{")", "]", "}"}, ch)) {
                depth--;
                i++;
                continue;
            }
            if ((depth == 0) && (py_startswith(py_slice(text, i, py_len(text)), " from "))) {
                auto lhs = py_strip(py_slice(text, 0, i));
                auto rhs = py_strip(py_slice(text, i + 6, py_len(text)));
                if ((lhs != "") && (rhs != ""))
                    return ::std::make_tuple(lhs, rhs);
                return ::std::nullopt;
            }
            i++;
        }
        return ::std::nullopt;
    }
    
    ::std::optional<::std::tuple<str, str>> _sh_split_top_level_in(const str& text) {
        /* トップレベルの `target in iter` を target/iter に分割する。 */
        int64 depth = 0;
        ::std::optional<str> in_str = ::std::nullopt;
        bool esc = false;
        int64 i = 0;
        while (i < py_len(text)) {
            str ch = text[i];
            if (!py_is_none(in_str)) {
                if (esc) {
                    esc = false;
                } else {
                    if (ch == "\\") {
                        esc = true;
                    } else {
                        if (ch == in_str)
                            in_str = ::std::nullopt;
                    }
                }
                i++;
                continue;
            }
            if (py_contains(set<str>{"'", "\""}, ch)) {
                in_str = ch;
                i++;
                continue;
            }
            if (py_contains(set<str>{"(", "[", "{"}, ch)) {
                depth++;
                i++;
                continue;
            }
            if (py_contains(set<str>{")", "]", "}"}, ch)) {
                depth--;
                i++;
                continue;
            }
            if ((depth == 0) && (py_startswith(py_slice(text, i, py_len(text)), " in "))) {
                auto lhs = py_strip(py_slice(text, 0, i));
                auto rhs = py_strip(py_slice(text, i + 4, py_len(text)));
                if ((lhs != "") && (rhs != ""))
                    return ::std::make_tuple(lhs, rhs);
                return ::std::nullopt;
            }
            i++;
        }
        return ::std::nullopt;
    }
    
    ::std::optional<::std::tuple<str, str>> _sh_split_top_level_as(const str& text) {
        /* トップレベルの `lhs as rhs` を分割する。 */
        int64 pos = _sh_split_top_keyword(text, "as");
        if (pos < 0)
            return ::std::nullopt;
        auto lhs = py_strip(py_slice(text, 0, pos));
        auto rhs = py_strip(py_slice(text, pos + 2, py_len(text)));
        if ((lhs == "") || (rhs == ""))
            return ::std::nullopt;
        return ::std::make_tuple(lhs, rhs);
    }
    
    ::std::optional<::std::tuple<str, ::std::optional<str>>> _sh_parse_except_clause(const str& header_text) {
        /* `except <Type> [as <name>]:` を手書きパースする。 */
        auto raw = py_strip(header_text);
        if ((!(py_startswith(raw, "except"))) || (!(py_endswith(raw, ":"))))
            return ::std::nullopt;
        auto inner = py_strip(py_slice(raw, py_len("except"), -1));
        if (inner == "")
            return ::std::make_tuple("Exception", ::std::nullopt);
        ::std::optional<::std::tuple<str, str>> as_split = _sh_split_top_level_as(inner);
        if (py_is_none(as_split))
            return ::std::make_tuple(inner, ::std::nullopt);
        auto __tuple_17 = *(as_split);
        str ex_type_txt = ::std::get<0>(__tuple_17);
        str ex_name_txt = ::std::get<1>(__tuple_17);
        if (py_strip(ex_type_txt) == "")
            return ::std::nullopt;
        if (!(_sh_is_identifier(py_strip(ex_name_txt))))
            return ::std::nullopt;
        return ::std::make_tuple(py_strip(ex_type_txt), py_strip(ex_name_txt));
    }
    
    ::std::optional<::std::tuple<str, str>> _sh_parse_class_header(const str& ln) {
        /* `class Name:` / `class Name(Base):` を簡易解析する。 */
        auto s = py_strip(ln);
        if ((!(py_startswith(s, "class "))) || (!(py_endswith(s, ":"))))
            return ::std::nullopt;
        auto head = py_strip(py_slice(s, py_len("class "), -1));
        if (head == "")
            return ::std::nullopt;
        auto lp = head.find("(");
        if (lp < 0) {
            if (!(_sh_is_identifier(head)))
                return ::std::nullopt;
            return ::std::make_tuple(head, "");
        }
        auto rp = head.rfind(")");
        if ((rp < 0) || (rp < lp))
            return ::std::nullopt;
        if (py_strip(py_slice(head, rp + 1, py_len(head))) != "")
            return ::std::nullopt;
        auto cls_name = py_strip(py_slice(head, 0, lp));
        auto base_name = py_strip(py_slice(head, lp + 1, rp));
        if (!(_sh_is_identifier(cls_name)))
            return ::std::nullopt;
        if (!(_sh_is_identifier(base_name)))
            return ::std::nullopt;
        return ::std::make_tuple(cls_name, base_name);
    }
    
    ::std::tuple<list<dict<str, object>>, int64> _sh_parse_if_tail(int64 start_idx, int64 parent_indent, const list<::std::tuple<int64, str>>& body_lines, const dict<str, str>& name_types, const str& scope_label) {
        /* if/elif/else 連鎖の後続ブロックを再帰的に解析する。 */
        if (start_idx >= py_len(body_lines))
            return ::std::make_tuple(list<object>{}, start_idx);
        auto __tuple_18 = body_lines[start_idx];
        int64 t_no = ::std::get<0>(__tuple_18);
        str t_ln = ::std::get<1>(__tuple_18);
        int64 t_indent = py_len(t_ln) - py_len(py_lstrip(t_ln, " "));
        auto t_s = py_strip(t_ln);
        if (t_indent != parent_indent)
            return ::std::make_tuple(list<object>{}, start_idx);
        if (t_s == "else:") {
            auto __tuple_19 = _sh_collect_indented_block(body_lines, start_idx + 1, parent_indent);
            list<::std::tuple<int64, str>> else_block = ::std::get<0>(__tuple_19);
            int64 k2 = ::std::get<1>(__tuple_19);
            if (py_len(else_block) == 0)
                throw _make_east_build_error("unsupported_syntax", "else body is missing in '" + scope_label + "'", _sh_span(t_no, 0, py_len(t_ln)), "Add indented else-body.");
            return ::std::make_tuple(_sh_parse_stmt_block(else_block, name_types, scope_label), k2);
        }
        if ((py_startswith(t_s, "elif ")) && (py_endswith(t_s, ":"))) {
            auto cond_txt2 = py_strip(py_slice(t_s, py_len("elif "), -1));
            auto cond_col2 = t_ln.find(cond_txt2);
            dict<str, object> cond_expr2 = _sh_parse_expr_lowered(cond_txt2, t_no, cond_col2, name_types);
            auto __tuple_20 = _sh_collect_indented_block(body_lines, start_idx + 1, parent_indent);
            list<::std::tuple<int64, str>> elif_block = ::std::get<0>(__tuple_20);
            int64 k2 = ::std::get<1>(__tuple_20);
            if (py_len(elif_block) == 0)
                throw _make_east_build_error("unsupported_syntax", "elif body is missing in '" + scope_label + "'", _sh_span(t_no, 0, py_len(t_ln)), "Add indented elif-body.");
            auto __tuple_21 = _sh_parse_if_tail(k2, parent_indent, body_lines, name_types, scope_label);
            list<dict<str, object>> nested_orelse = ::std::get<0>(__tuple_21);
            int64 k3 = ::std::get<1>(__tuple_21);
            list<dict<str, object>> elif_items = list<dict<str, object>>{};
            dict<str, object> elif_item = dict<str, object>{{"kind", make_object("If")}, {"source_span", make_object(_sh_block_end_span(body_lines, t_no, t_ln.find("elif "), py_len(t_ln), k3))}, {"test", make_object(cond_expr2)}, {"body", make_object(_sh_parse_stmt_block(elif_block, name_types, scope_label))}, {"orelse", make_object(nested_orelse)}};
            elif_items.append(dict<str, object>(elif_item));
            return ::std::make_tuple(elif_items, k3);
        }
        return ::std::make_tuple(list<object>{}, start_idx);
    }
    
    ::std::tuple<::std::optional<str>, list<dict<str, object>>> _sh_extract_leading_docstring(const list<dict<str, object>>& stmts) {
        /* 先頭文が docstring の場合に抽出し、残り文リストを返す。 */
        if (py_len(stmts) == 0)
            return ::std::make_tuple(::std::nullopt, stmts);
        dict<str, object> first = stmts[0];
        if ((!(py_is_dict(first))) || (py_dict_get_maybe(first, "kind") != "Expr"))
            return ::std::make_tuple(::std::nullopt, stmts);
        auto val = py_dict_get_maybe(first, "value");
        if ((!(py_is_dict(val))) || (py_dict_get_maybe(val, "kind") != "Constant"))
            return ::std::make_tuple(::std::nullopt, stmts);
        auto s = py_dict_get_maybe(val, "value");
        if (!(py_is_str(s)))
            return ::std::make_tuple(::std::nullopt, stmts);
        return ::std::make_tuple(s, py_slice(stmts, 1, py_len(stmts)));
    }
    
    void _sh_append_import_binding(list<dict<str, object>>& import_bindings, set<str>& import_binding_names, const str& module_id, const str& export_name, const str& local_name, const str& binding_kind, const str& source_file, int64 source_line) {
        /* import 情報の正本 `ImportBinding` を追加する。 */
        if (py_contains(import_binding_names, local_name))
            throw _make_east_build_error("unsupported_syntax", "duplicate import binding: " + local_name, _sh_span(source_line, 0, 0), "Rename alias to avoid duplicate imported names.");
        import_binding_names.insert(local_name);
        import_bindings.append(dict<str, object>(dict<str, object>{{"module_id", make_object(module_id)}, {"export_name", make_object(export_name)}, {"local_name", make_object(local_name)}, {"binding_kind", make_object(binding_kind)}, {"source_file", make_object(source_file)}, {"source_line", make_object(source_line)}}));
    }
    
    struct _ShExprParser {
        str src;
        int64 line_no;
        int64 col_base;
        dict<str, str> name_types;
        dict<str, str> fn_return_types;
        dict<str, dict<str, str>> class_method_return_types;
        dict<str, ::std::optional<str>> class_base;
        list<dict<str, object>> tokens;
        int64 pos;
        
        _ShExprParser(const str& text, int64 line_no, int64 col_base, const dict<str, str>& name_types, const dict<str, str>& fn_return_types, const dict<str, dict<str, str>>& class_method_return_types, const dict<str, ::std::optional<str>>& class_base) {
            /* 式パースに必要な入力と型環境を初期化する。 */
            this->src = text;
            this->line_no = line_no;
            this->col_base = col_base;
            this->name_types = name_types;
            this->fn_return_types = fn_return_types;
            this->class_method_return_types = class_method_return_types;
            this->class_base = class_base;
            this->tokens = this->_tokenize(text);
            this->pos = 0;
        }
        list<dict<str, object>> _tokenize(const str& text) {
            /* 式テキストを self-hosted 用トークン列へ変換する。 */
            list<dict<str, object>> out = list<dict<str, object>>{};
            int64 i = 0;
            while (i < py_len(text)) {
                str ch = text[i];
                if (ch.isspace()) {
                    i++;
                    continue;
                }
                // string literal prefixes: r"...", f"...", b"...", u"...", rf"...", fr"...", ...
                int64 pref_len = 0;
                if (i + 1 < py_len(text)) {
                    str p1 = text[i];
                    if ((py_contains(_SH_STR_PREFIX_CHARS, p1)) && (py_contains(set<str>{"'", "\""}, text[i + 1]))) {
                        pref_len = 1;
                    } else {
                        if (i + 2 < py_len(text)) {
                            str p2 = py_slice(text, i, i + 2);
                            if ((py_all([&]() -> list<bool> {     list<bool> __out;     for (auto c : p2) {         __out.append(py_contains(_SH_STR_PREFIX_CHARS, c));     }     return __out; }())) && (py_contains(set<str>{"'", "\""}, text[i + 2])))
                                pref_len = 2;
                        }
                    }
                }
                if (pref_len > 0) {
                    int64 end = _sh_scan_string_token(text, i, i + pref_len, this->line_no, this->col_base);
                    out.append(dict<str, object>(dict<str, object>{{"k", make_object("STR")}, {"v", make_object(py_slice(text, i, end))}, {"s", make_object(i)}, {"e", make_object(end)}}));
                    i = end;
                    continue;
                }
                if (ch.isdigit()) {
                    if ((ch == "0") && (i + 2 < py_len(text)) && (py_contains(set<str>{"x", "X"}, text[i + 1]))) {
                        int64 j = i + 2;
                        while ((j < py_len(text)) && ((text[j].isdigit()) || (py_contains(set<str>{"a", "b", "c", "d", "e", "f"}, text[j].lower())))) {
                            j++;
                        }
                        if (j > i + 2) {
                            out.append(dict<str, object>(dict<str, object>{{"k", make_object("INT")}, {"v", make_object(py_slice(text, i, j))}, {"s", make_object(i)}, {"e", make_object(j)}}));
                            i = j;
                            continue;
                        }
                    }
                    int64 j = i + 1;
                    while ((j < py_len(text)) && (text[j].isdigit())) {
                        j++;
                    }
                    bool has_float = false;
                    if ((j < py_len(text)) && (text.at(j) == '.')) {
                        int64 k = j + 1;
                        while ((k < py_len(text)) && (text[k].isdigit())) {
                            k++;
                        }
                        if (k > j + 1) {
                            j = k;
                            has_float = true;
                        }
                    }
                    if ((j < py_len(text)) && (py_contains(set<str>{"e", "E"}, text[j]))) {
                        int64 k = j + 1;
                        if ((k < py_len(text)) && (py_contains(set<str>{"+", "-"}, text[k])))
                            k++;
                        int64 d0 = k;
                        while ((k < py_len(text)) && (text[k].isdigit())) {
                            k++;
                        }
                        if (k > d0) {
                            j = k;
                            has_float = true;
                        }
                    }
                    if (has_float) {
                        out.append(dict<str, object>(dict<str, object>{{"k", make_object("FLOAT")}, {"v", make_object(py_slice(text, i, j))}, {"s", make_object(i)}, {"e", make_object(j)}}));
                        i = j;
                        continue;
                    }
                    out.append(dict<str, object>(dict<str, object>{{"k", make_object("INT")}, {"v", make_object(py_slice(text, i, j))}, {"s", make_object(i)}, {"e", make_object(j)}}));
                    i = j;
                    continue;
                }
                if ((ch.isalpha()) || (ch == "_")) {
                    int64 j = i + 1;
                    while ((j < py_len(text)) && ((text[j].isalnum()) || (text.at(j) == '_'))) {
                        j++;
                    }
                    out.append(dict<str, object>(dict<str, object>{{"k", make_object("NAME")}, {"v", make_object(py_slice(text, i, j))}, {"s", make_object(i)}, {"e", make_object(j)}}));
                    i = j;
                    continue;
                }
                if ((i + 2 < py_len(text)) && (py_contains(set<str>{"'''", "\"\"\""}, py_slice(text, i, i + 3)))) {
                    int64 end = _sh_scan_string_token(text, i, i, this->line_no, this->col_base);
                    out.append(dict<str, object>(dict<str, object>{{"k", make_object("STR")}, {"v", make_object(py_slice(text, i, end))}, {"s", make_object(i)}, {"e", make_object(end)}}));
                    i = end;
                    continue;
                }
                if (py_contains(set<str>{"'", "\""}, ch)) {
                    int64 end = _sh_scan_string_token(text, i, i, this->line_no, this->col_base);
                    out.append(dict<str, object>(dict<str, object>{{"k", make_object("STR")}, {"v", make_object(py_slice(text, i, end))}, {"s", make_object(i)}, {"e", make_object(end)}}));
                    i = end;
                    continue;
                }
                if ((i + 1 < py_len(text)) && (py_contains(set<str>{"<=", ">=", "==", "!=", "//", "<<", ">>"}, py_slice(text, i, i + 2)))) {
                    out.append(dict<str, object>(dict<str, object>{{"k", make_object(py_slice(text, i, i + 2))}, {"v", make_object(py_slice(text, i, i + 2))}, {"s", make_object(i)}, {"e", make_object(i + 2)}}));
                    i += 2;
                    continue;
                }
                if (py_contains(set<str>{"<", ">"}, ch)) {
                    out.append(dict<str, object>(dict<str, object>{{"k", make_object(ch)}, {"v", make_object(ch)}, {"s", make_object(i)}, {"e", make_object(i + 1)}}));
                    i++;
                    continue;
                }
                if (py_contains(set<str>{"+", "-", "*", "/", "%", "&", "|", "^", "(", ")", ",", ".", "[", "]", ":", "=", "{", "}"}, ch)) {
                    out.append(dict<str, object>(dict<str, object>{{"k", make_object(ch)}, {"v", make_object(ch)}, {"s", make_object(i)}, {"e", make_object(i + 1)}}));
                    i++;
                    continue;
                }
                throw _make_east_build_error("unsupported_syntax", "unsupported token '" + ch + "' in self_hosted parser", _sh_span(this->line_no, this->col_base + i, this->col_base + i + 1), "Extend tokenizer for this syntax.");
            }
            out.append(dict<str, object>(dict<str, object>{{"k", make_object("EOF")}, {"v", make_object("")}, {"s", make_object(py_len(text))}, {"e", make_object(py_len(text))}}));
            return out;
        }
        dict<str, object> _cur() {
            /* 現在トークンを返す。 */
            return this->tokens[this->pos];
        }
        dict<str, object> _eat(const ::std::optional<str>& kind = ::std::nullopt) {
            /* 現在トークンを消費して返す。kind 指定時は一致を検証する。 */
            dict<str, object> tok = this->_cur();
            if ((!py_is_none(kind)) && (py_dict_get(tok, py_to_string("k")) != kind))
                throw _make_east_build_error("unsupported_syntax", "expected token " + py_to_string(kind) + ", got " + py_to_string(py_dict_get(tok, py_to_string("k"))), _sh_span(this->line_no, this->col_base + py_dict_get(tok, py_to_string("s")), this->col_base + py_dict_get(tok, py_to_string("e"))), "Fix expression syntax for self_hosted parser.");
            this->pos++;
            return tok;
        }
        dict<str, int64> _node_span(int64 s, int64 e) {
            /* 式内相対位置をファイル基準の source_span へ変換する。 */
            return _sh_span(this->line_no, this->col_base + s, this->col_base + e);
        }
        str _src_slice(int64 s, int64 e) {
            /* 元ソースから該当区間の repr 用文字列を取り出す。 */
            return py_strip(py_slice(this->src, s, e));
        }
        dict<str, object> parse() {
            /* 式を最後まで解析し、EAST 式ノードを返す。 */
            dict<str, object> node = this->_parse_ifexp();
            this->_eat("EOF");
            return node;
        }
        dict<str, object> _parse_lambda() {
            /* lambda 式を解析する。lambda でなければ次順位へ委譲する。 */
            dict<str, object> tok = this->_cur();
            if (!((py_dict_get(tok, py_to_string("k")) == "NAME") && (py_dict_get(tok, py_to_string("v")) == "lambda")))
                return this->_parse_or();
            dict<str, object> lam_tok = this->_eat("NAME");
            list<str> arg_names = list<str>{};
            while (py_dict_get(this->_cur(), py_to_string("k")) != ":") {
                if (py_dict_get(this->_cur(), py_to_string("k")) == ",") {
                    this->_eat(",");
                    continue;
                }
                if (py_dict_get(this->_cur(), py_to_string("k")) == "NAME") {
                    arg_names.append(str(py_to_string(py_dict_get(this->_eat("NAME"), py_to_string("v")))));
                    continue;
                }
                dict<str, object> cur = this->_cur();
                throw _make_east_build_error("unsupported_syntax", "unsupported lambda parameter token: " + py_to_string(py_dict_get(cur, py_to_string("k"))), this->_node_span(int64(py_to_int64(py_dict_get(cur, py_to_string("s")))), int64(py_to_int64(py_dict_get(cur, py_to_string("e"))))), "Use `lambda x, y: expr` form without annotations/defaults.");
            }
            this->_eat(":");
            dict<str, str> bak = dict<str, str>{};
            for (str nm : arg_names) {
                bak[py_to_string(nm)] = py_dict_get_default(this->name_types, py_to_string(nm), "");
                this->name_types[py_to_string(nm)] = "unknown";
            }
            dict<str, object> body = this->_parse_ifexp();
            for (str nm : arg_names) {
                auto old = py_dict_get_default(bak, py_to_string(nm), "");
                if (old == "")
                    (this->name_types.contains(py_to_string(nm)) ? this->name_types.pop(py_to_string(nm)) : str());
                else
                    this->name_types[py_to_string(nm)] = old;
            }
            object s = make_object(py_dict_get(lam_tok, py_to_string("s")));
            int64 e = py_to_int64(py_dict_get(py_dict_get(body, py_to_string("source_span")), "end_col")) - this->col_base;
            str body_t = py_to_string(dict_get_node(body, "resolved_type", "unknown"));
            str ret_t = (body_t != "" ? body_t : "unknown");
            auto params = str(",").join([&]() -> list<str> {     list<str> __out;     for (auto _ : arg_names) {         __out.append("unknown");     }     return __out; }());
            str callable_t = "callable[" + py_to_string(params) + "->" + ret_t + "]";
            return dict<str, object>{{"kind", make_object("Lambda")}, {"source_span", make_object(this->_node_span(int64(py_to_int64(s)), e))}, {"resolved_type", make_object(callable_t)}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(this->_src_slice(int64(py_to_int64(s)), e))}, {"args", make_object([&]() -> list<dict<str, object>> {     list<dict<str, object>> __out;     for (auto nm : arg_names) {         __out.append(dict<str, object>{{"kind", make_object("arg")}, {"arg", make_object(nm)}, {"annotation", make_object(::std::nullopt)}, {"resolved_type", make_object("unknown")}});     }     return __out; }())}, {"body", make_object(body)}, {"return_type", make_object(ret_t)}};
        }
        str _callable_return_type(const str& t) {
            /* `callable[...]` 型文字列から戻り型だけを抽出する。 */
            if (!((py_startswith(t, "callable[")) && (py_endswith(t, "]"))))
                return "unknown";
            str core = py_slice(t, py_len("callable["), -1);
            auto p = core.rfind("->");
            if (p < 0)
                return "unknown";
            auto out = py_strip(py_slice(core, p + 2, py_len(core)));
            return (out != "" ? out : "unknown");
        }
        dict<str, object> _parse_ifexp() {
            /* 条件式 `a if cond else b` を解析する。 */
            dict<str, object> body = this->_parse_lambda();
            if ((py_dict_get(this->_cur(), py_to_string("k")) == "NAME") && (py_dict_get(this->_cur(), py_to_string("v")) == "if")) {
                this->_eat("NAME");
                dict<str, object> test = this->_parse_lambda();
                dict<str, object> else_tok = this->_eat("NAME");
                if (py_dict_get(else_tok, py_to_string("v")) != "else")
                    throw _make_east_build_error("unsupported_syntax", "expected 'else' in conditional expression", this->_node_span(int64(py_to_int64(py_dict_get(else_tok, py_to_string("s")))), int64(py_to_int64(py_dict_get(else_tok, py_to_string("e"))))), "Use `a if cond else b` syntax.");
                dict<str, object> orelse = this->_parse_ifexp();
                int64 s = py_to_int64(py_dict_get(py_dict_get(body, py_to_string("source_span")), "col")) - this->col_base;
                int64 e = py_to_int64(py_dict_get(py_dict_get(orelse, py_to_string("source_span")), "end_col")) - this->col_base;
                str rt = py_to_string(dict_get_node(body, "resolved_type", "unknown"));
                if (rt != py_to_string(dict_get_node(orelse, "resolved_type", "unknown")))
                    rt = "unknown";
                return dict<str, object>{{"kind", make_object("IfExp")}, {"source_span", make_object(this->_node_span(s, e))}, {"resolved_type", make_object(rt)}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(this->_src_slice(s, e))}, {"test", make_object(test)}, {"body", make_object(body)}, {"orelse", make_object(orelse)}};
            }
            return body;
        }
        dict<str, object> _parse_or() {
            /* 論理和（or）式を解析する。 */
            dict<str, object> node = this->_parse_and();
            list<dict<str, object>> values = list<dict<str, object>>{node};
            while ((py_dict_get(this->_cur(), py_to_string("k")) == "NAME") && (py_dict_get(this->_cur(), py_to_string("v")) == "or")) {
                this->_eat("NAME");
                values.append(dict<str, object>(this->_parse_and()));
            }
            if (py_len(values) == 1)
                return node;
            int64 s = py_to_int64(py_dict_get(py_dict_get(values[0], py_to_string("source_span")), "col")) - this->col_base;
            int64 e = py_to_int64(py_dict_get(py_dict_get(py_at(values, -1), py_to_string("source_span")), "end_col")) - this->col_base;
            return dict<str, object>{{"kind", make_object("BoolOp")}, {"source_span", make_object(this->_node_span(s, e))}, {"resolved_type", make_object("bool")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(this->_src_slice(s, e))}, {"op", make_object("Or")}, {"values", make_object(values)}};
        }
        dict<str, object> _parse_and() {
            /* 論理積（and）式を解析する。 */
            dict<str, object> node = this->_parse_not();
            list<dict<str, object>> values = list<dict<str, object>>{node};
            while ((py_dict_get(this->_cur(), py_to_string("k")) == "NAME") && (py_dict_get(this->_cur(), py_to_string("v")) == "and")) {
                this->_eat("NAME");
                values.append(dict<str, object>(this->_parse_not()));
            }
            if (py_len(values) == 1)
                return node;
            int64 s = py_to_int64(py_dict_get(py_dict_get(values[0], py_to_string("source_span")), "col")) - this->col_base;
            int64 e = py_to_int64(py_dict_get(py_dict_get(py_at(values, -1), py_to_string("source_span")), "end_col")) - this->col_base;
            return dict<str, object>{{"kind", make_object("BoolOp")}, {"source_span", make_object(this->_node_span(s, e))}, {"resolved_type", make_object("bool")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(this->_src_slice(s, e))}, {"op", make_object("And")}, {"values", make_object(values)}};
        }
        dict<str, object> _parse_not() {
            /* 単項 not を解析する。 */
            dict<str, object> tok = this->_cur();
            if ((py_dict_get(tok, py_to_string("k")) == "NAME") && (py_dict_get(tok, py_to_string("v")) == "not")) {
                this->_eat("NAME");
                dict<str, object> operand = this->_parse_not();
                object s = make_object(py_dict_get(tok, py_to_string("s")));
                int64 e = py_to_int64(py_dict_get(py_dict_get(operand, py_to_string("source_span")), "end_col")) - this->col_base;
                return dict<str, object>{{"kind", make_object("UnaryOp")}, {"source_span", make_object(this->_node_span(int64(py_to_int64(s)), e))}, {"resolved_type", make_object("bool")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(this->_src_slice(int64(py_to_int64(s)), e))}, {"op", make_object("Not")}, {"operand", make_object(operand)}};
            }
            return this->_parse_compare();
        }
        dict<str, object> _parse_compare() {
            /* 比較演算（連鎖比較含む）を解析する。 */
            dict<str, object> node = this->_parse_bitor();
            dict<str, str> cmp_map = dict<str, str>{{"<", "Lt"}, {"<=", "LtE"}, {">", "Gt"}, {">=", "GtE"}, {"==", "Eq"}, {"!=", "NotEq"}};
            list<str> ops = list<str>{};
            list<dict<str, object>> comparators = list<dict<str, object>>{};
            while (true) {
                if (py_contains(cmp_map, py_dict_get(this->_cur(), py_to_string("k")))) {
                    dict<str, object> tok = this->_eat();
                    ops.append(str(py_dict_get(cmp_map, py_to_string(py_dict_get(tok, py_to_string("k"))))));
                    comparators.append(dict<str, object>(this->_parse_bitor()));
                    continue;
                }
                if ((py_dict_get(this->_cur(), py_to_string("k")) == "NAME") && (py_dict_get(this->_cur(), py_to_string("v")) == "in")) {
                    this->_eat("NAME");
                    ops.append(str("In"));
                    comparators.append(dict<str, object>(this->_parse_bitor()));
                    continue;
                }
                if ((py_dict_get(this->_cur(), py_to_string("k")) == "NAME") && (py_dict_get(this->_cur(), py_to_string("v")) == "is")) {
                    this->_eat("NAME");
                    if ((py_dict_get(this->_cur(), py_to_string("k")) == "NAME") && (py_dict_get(this->_cur(), py_to_string("v")) == "not")) {
                        this->_eat("NAME");
                        ops.append(str("IsNot"));
                        comparators.append(dict<str, object>(this->_parse_bitor()));
                    } else {
                        ops.append(str("Is"));
                        comparators.append(dict<str, object>(this->_parse_bitor()));
                    }
                    continue;
                }
                if ((py_dict_get(this->_cur(), py_to_string("k")) == "NAME") && (py_dict_get(this->_cur(), py_to_string("v")) == "not")) {
                    int64 pos = this->pos;
                    this->_eat("NAME");
                    if ((py_dict_get(this->_cur(), py_to_string("k")) == "NAME") && (py_dict_get(this->_cur(), py_to_string("v")) == "in")) {
                        this->_eat("NAME");
                        ops.append(str("NotIn"));
                        comparators.append(dict<str, object>(this->_parse_bitor()));
                        continue;
                    }
                    this->pos = pos;
                }
                break;
            }
            if (py_len(ops) == 0)
                return node;
            int64 start_col = py_to_int64(py_dict_get(py_dict_get(node, py_to_string("source_span")), "col")) - this->col_base;
            int64 end_col = py_to_int64(py_dict_get(py_dict_get(py_at(comparators, -1), py_to_string("source_span")), "end_col")) - this->col_base;
            return dict<str, object>{{"kind", make_object("Compare")}, {"source_span", make_object(this->_node_span(start_col, end_col))}, {"resolved_type", make_object("bool")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(this->_src_slice(start_col, end_col))}, {"left", make_object(node)}, {"ops", make_object(ops)}, {"comparators", make_object(comparators)}};
        }
        dict<str, object> _parse_bitor() {
            /* ビット OR を解析する。 */
            dict<str, object> node = this->_parse_bitxor();
            while (py_dict_get(this->_cur(), py_to_string("k")) == "|") {
                dict<str, object> op_tok = this->_eat();
                dict<str, object> right = this->_parse_bitxor();
                node = this->_make_bin(node, py_to_string(py_dict_get(op_tok, py_to_string("k"))), right);
            }
            return node;
        }
        dict<str, object> _parse_bitxor() {
            /* ビット XOR を解析する。 */
            dict<str, object> node = this->_parse_bitand();
            while (py_dict_get(this->_cur(), py_to_string("k")) == "^") {
                dict<str, object> op_tok = this->_eat();
                dict<str, object> right = this->_parse_bitand();
                node = this->_make_bin(node, py_to_string(py_dict_get(op_tok, py_to_string("k"))), right);
            }
            return node;
        }
        dict<str, object> _parse_bitand() {
            /* ビット AND を解析する。 */
            dict<str, object> node = this->_parse_shift();
            while (py_dict_get(this->_cur(), py_to_string("k")) == "&") {
                dict<str, object> op_tok = this->_eat();
                dict<str, object> right = this->_parse_shift();
                node = this->_make_bin(node, py_to_string(py_dict_get(op_tok, py_to_string("k"))), right);
            }
            return node;
        }
        dict<str, object> _parse_shift() {
            /* シフト演算を解析する。 */
            dict<str, object> node = this->_parse_addsub();
            while (py_contains(set<str>{"<<", ">>"}, py_dict_get(this->_cur(), py_to_string("k")))) {
                dict<str, object> op_tok = this->_eat();
                dict<str, object> right = this->_parse_addsub();
                node = this->_make_bin(node, py_to_string(py_dict_get(op_tok, py_to_string("k"))), right);
            }
            return node;
        }
        dict<str, object> _parse_addsub() {
            /* 加減算を解析する。 */
            dict<str, object> node = this->_parse_muldiv();
            while (py_contains(set<str>{"+", "-"}, py_dict_get(this->_cur(), py_to_string("k")))) {
                dict<str, object> op_tok = this->_eat();
                dict<str, object> right = this->_parse_muldiv();
                node = this->_make_bin(node, py_to_string(py_dict_get(op_tok, py_to_string("k"))), right);
            }
            return node;
        }
        dict<str, object> _parse_muldiv() {
            /* 乗除算（`* / // %`）を解析する。 */
            dict<str, object> node = this->_parse_unary();
            while (py_contains(set<str>{"*", "/", "//", "%"}, py_dict_get(this->_cur(), py_to_string("k")))) {
                dict<str, object> op_tok = this->_eat();
                dict<str, object> right = this->_parse_unary();
                node = this->_make_bin(node, py_to_string(py_dict_get(op_tok, py_to_string("k"))), right);
            }
            return node;
        }
        dict<str, object> _parse_unary() {
            /* 単項演算（`+` / `-`）を解析する。 */
            if (py_contains(set<str>{"+", "-"}, py_dict_get(this->_cur(), py_to_string("k")))) {
                dict<str, object> tok = this->_eat();
                dict<str, object> operand = this->_parse_unary();
                object s = make_object(py_dict_get(tok, py_to_string("s")));
                int64 e = py_to_int64(py_dict_get(py_dict_get(operand, py_to_string("source_span")), "end_col")) - this->col_base;
                str out_t = py_to_string(dict_get_node(operand, "resolved_type", "unknown"));
                return dict<str, object>{{"kind", make_object("UnaryOp")}, {"source_span", make_object(this->_node_span(int64(py_to_int64(s)), e))}, {"resolved_type", make_object((py_contains(set<str>{"int64", "float64"}, out_t) ? out_t : "unknown"))}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(this->_src_slice(int64(py_to_int64(s)), e))}, {"op", make_object((py_dict_get(tok, py_to_string("k")) == "-" ? "USub" : "UAdd"))}, {"operand", make_object(operand)}};
            }
            return this->_parse_postfix();
        }
        str _lookup_method_return(const str& cls_name, const str& method) {
            /* クラス継承を辿ってメソッド戻り型を解決する。 */
            str cur = cls_name;
            while (true) {
                dict<str, str> methods = dict<str, str>{};
                if (py_contains(this->class_method_return_types, cur))
                    methods = py_dict_get(this->class_method_return_types, py_to_string(cur));
                if (py_contains(methods, method)) {
                    object value_obj = make_object(py_dict_get(methods, py_to_string(method)));
                    if (py_is_str(value_obj))
                        return py_to_string(value_obj);
                    return py_to_string(value_obj);
                }
                object next_cur_obj = object{};
                if (py_contains(this->class_base, cur))
                    next_cur_obj = make_object(py_dict_get(this->class_base, py_to_string(cur)));
                if (!(py_is_str(next_cur_obj)))
                    break;
                cur = py_to_string(next_cur_obj);
            }
            return "unknown";
        }
        list<str> _split_generic_types(const str& s) {
            /* ジェネリック型引数をトップレベルカンマで分割する。 */
            list<str> out = list<str>{};
            int64 depth = 0;
            int64 start = 0;
            for (auto __it_25 : py_enumerate(s)) {
                auto i = ::std::get<0>(__it_25);
                auto ch = ::std::get<1>(__it_25);
                if (ch == "[") {
                    depth++;
                } else {
                    if (ch == "]") {
                        depth--;
                    } else {
                        if ((ch == ",") && (depth == 0)) {
                            out.append(str(py_strip(py_slice(s, start, i))));
                            start = i + 1;
                        }
                    }
                }
            }
            out.append(str(py_strip(py_slice(s, start, py_len(s)))));
            return out;
        }
        list<str> _split_union_types(const str& s) {
            /* Union 型引数をトップレベル `|` で分割する。 */
            list<str> out = list<str>{};
            int64 depth = 0;
            int64 start = 0;
            for (auto __it_26 : py_enumerate(s)) {
                auto i = ::std::get<0>(__it_26);
                auto ch = ::std::get<1>(__it_26);
                if (ch == "[") {
                    depth++;
                } else {
                    if (ch == "]") {
                        depth--;
                    } else {
                        if ((ch == "|") && (depth == 0)) {
                            out.append(str(py_strip(py_slice(s, start, i))));
                            start = i + 1;
                        }
                    }
                }
            }
            out.append(str(py_strip(py_slice(s, start, py_len(s)))));
            return out;
        }
        bool _is_forbidden_object_receiver_type(const str& t) {
            /* object レシーバ禁止ルールに該当する型か判定する。 */
            auto s = py_strip(t);
            if (py_contains(set<str>{"object", "Any", "any"}, s))
                return true;
            if (py_contains(s, "|")) {
                list<str> parts = this->_split_union_types(s);
                return py_any([&]() -> list<bool> {     list<bool> __out;     for (auto p : parts) {         if (p != "None") __out.append(py_contains(set<str>{"object", "Any", "any"}, p));     }     return __out; }());
            }
            return false;
        }
        str _subscript_result_type(const str& container_type) {
            /* 添字アクセスの結果型をコンテナ型から推論する。 */
            if ((py_startswith(container_type, "list[")) && (py_endswith(container_type, "]"))) {
                auto inner = py_strip(py_slice(container_type, 5, -1));
                return (inner != "" ? inner : "unknown");
            }
            if ((py_startswith(container_type, "dict[")) && (py_endswith(container_type, "]"))) {
                list<str> inner = this->_split_generic_types(py_strip(py_slice(container_type, 5, -1)));
                if ((py_len(inner) == 2) && (inner[1] != ""))
                    return inner[1];
                return "unknown";
            }
            if (container_type == "str")
                return "str";
            if (py_contains(set<str>{"bytes", "bytearray"}, container_type))
                return "uint8";
            return "unknown";
        }
        str _iter_item_type(const ::std::optional<dict<str, object>>& iter_expr) {
            /* for 反復対象の要素型を推論する。 */
            if (!(py_is_dict(iter_expr)))
                return "unknown";
            str t = py_to_string(py_dict_get_default(iter_expr, "resolved_type", "unknown"));
            if (t == "range")
                return "int64";
            if ((py_startswith(t, "list[")) && (py_endswith(t, "]"))) {
                auto inner = py_strip(py_slice(t, 5, -1));
                return (inner != "" ? inner : "unknown");
            }
            if ((py_startswith(t, "set[")) && (py_endswith(t, "]"))) {
                auto inner = py_strip(py_slice(t, 4, -1));
                return (inner != "" ? inner : "unknown");
            }
            if ((t == "bytearray") || (t == "bytes"))
                return "uint8";
            if (t == "str")
                return "str";
            return "unknown";
        }
        dict<str, object> _parse_postfix() {
            /* 属性参照・呼び出し・添字・スライスなど後置構文を解析する。 */
            dict<str, object> node = this->_parse_primary();
            while (true) {
                dict<str, object> tok = this->_cur();
                if (py_dict_get(tok, py_to_string("k")) == ".") {
                    this->_eat(".");
                    dict<str, object> name_tok = this->_eat("NAME");
                    int64 s = py_to_int64(py_dict_get(py_dict_get(node, py_to_string("source_span")), "col")) - this->col_base;
                    object e = make_object(py_dict_get(name_tok, py_to_string("e")));
                    str attr_name = py_to_string(py_dict_get(name_tok, py_to_string("v")));
                    str owner_t = py_to_string(dict_get_node(node, "resolved_type", "unknown"));
                    if (this->_is_forbidden_object_receiver_type(owner_t))
                        throw _make_east_build_error("unsupported_syntax", "object receiver attribute/method access is forbidden by language constraints", this->_node_span(s, int64(py_to_int64(e))), "Cast or assign to a concrete type before attribute/method access.");
                    str attr_t = "unknown";
                    if ((py_is_dict(node)) && (py_dict_get_maybe(node, "kind") == "Name") && (py_dict_get_maybe(node, "id") == "self")) {
                        // In method scope, class fields are injected into name_types.
                        auto maybe_field_t = py_dict_get_maybe(this->name_types, py_to_string(attr_name));
                        if ((py_is_str(maybe_field_t)) && (maybe_field_t != ""))
                            attr_t = maybe_field_t;
                    }
                    if (owner_t == "Path") {
                        if (py_contains(set<str>{"name", "stem"}, attr_name)) {
                            attr_t = "str";
                        } else {
                            if (attr_name == "parent")
                                attr_t = "Path";
                        }
                    }
                    node = dict<str, object>{{"kind", make_object("Attribute")}, {"source_span", make_object(this->_node_span(s, int64(py_to_int64(e))))}, {"resolved_type", make_object(attr_t)}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(this->_src_slice(s, int64(py_to_int64(e))))}, {"value", make_object(node)}, {"attr", make_object(attr_name)}};
                    continue;
                }
                if (py_dict_get(tok, py_to_string("k")) == "(") {
                    dict<str, object> ltok = this->_eat("(");
                    list<dict<str, object>> args = list<dict<str, object>>{};
                    list<dict<str, object>> keywords = list<dict<str, object>>{};
                    if (py_dict_get(this->_cur(), py_to_string("k")) != ")") {
                        while (true) {
                            if (py_dict_get(this->_cur(), py_to_string("k")) == "NAME") {
                                int64 save_pos = this->pos;
                                dict<str, object> name_tok = this->_eat("NAME");
                                if (py_dict_get(this->_cur(), py_to_string("k")) == "=") {
                                    this->_eat("=");
                                    dict<str, object> kw_val = this->_parse_ifexp();
                                    keywords.append(dict<str, object>(dict<str, object>{{"arg", make_object(py_to_string(py_dict_get(name_tok, py_to_string("v"))))}, {"value", make_object(kw_val)}}));
                                } else {
                                    this->pos = save_pos;
                                    args.append(dict<str, object>(this->_parse_call_arg_expr()));
                                }
                            } else {
                                args.append(dict<str, object>(this->_parse_call_arg_expr()));
                            }
                            if (py_dict_get(this->_cur(), py_to_string("k")) == ",") {
                                this->_eat(",");
                                if (py_dict_get(this->_cur(), py_to_string("k")) == ")")
                                    break;
                                continue;
                            }
                            break;
                        }
                    }
                    dict<str, object> rtok = this->_eat(")");
                    int64 s = py_to_int64(py_dict_get(py_dict_get(node, py_to_string("source_span")), "col")) - this->col_base;
                    object e = make_object(py_dict_get(rtok, py_to_string("e")));
                    str call_ret = "unknown";
                    str fn_name = "";
                    if ((py_is_dict(node)) && (py_dict_get_maybe(node, "kind") == "Name")) {
                        fn_name = py_to_string(dict_get_node(node, "id", ""));
                        if (fn_name == "print") {
                            call_ret = "None";
                        } else {
                            if (fn_name == "Path") {
                                call_ret = "Path";
                            } else {
                                if (fn_name == "open") {
                                    call_ret = "PyFile";
                                } else {
                                    if (fn_name == "int") {
                                        call_ret = "int64";
                                    } else {
                                        if (fn_name == "float") {
                                            call_ret = "float64";
                                        } else {
                                            if (fn_name == "bool") {
                                                call_ret = "bool";
                                            } else {
                                                if (fn_name == "str") {
                                                    call_ret = "str";
                                                } else {
                                                    if (fn_name == "len") {
                                                        call_ret = "int64";
                                                    } else {
                                                        if (fn_name == "range") {
                                                            call_ret = "range";
                                                        } else {
                                                            if (fn_name == "list") {
                                                                call_ret = "list[unknown]";
                                                            } else {
                                                                if (fn_name == "set") {
                                                                    call_ret = "set[unknown]";
                                                                } else {
                                                                    if (fn_name == "dict") {
                                                                        call_ret = "dict[unknown,unknown]";
                                                                    } else {
                                                                        if (fn_name == "bytes") {
                                                                            call_ret = "bytes";
                                                                        } else {
                                                                            if (fn_name == "bytearray") {
                                                                                call_ret = "bytearray";
                                                                            } else {
                                                                                if (py_contains(set<str>{"Exception", "RuntimeError"}, fn_name)) {
                                                                                    call_ret = "Exception";
                                                                                } else {
                                                                                    if (py_contains(this->fn_return_types, fn_name)) {
                                                                                        call_ret = py_dict_get(this->fn_return_types, py_to_string(fn_name));
                                                                                    } else {
                                                                                        if (py_contains(this->class_method_return_types, fn_name))
                                                                                            call_ret = fn_name;
                                                                                        else
                                                                                            call_ret = this->_callable_return_type(py_to_string(py_dict_get_default(this->name_types, py_to_string(fn_name), "unknown")));
                                                                                    }
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
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
                        if ((py_is_dict(node)) && (py_dict_get_maybe(node, "kind") == "Attribute")) {
                            auto owner = py_dict_get_maybe(node, "value");
                            str attr = py_to_string(dict_get_node(node, "attr", ""));
                            if ((py_is_dict(owner)) && (py_dict_get_maybe(owner, "kind") == "Name")) {
                                str owner_t = py_dict_get_default(this->name_types, py_to_string(py_to_string(py_dict_get_default(owner, "id", ""))), "unknown");
                                if (owner_t != "unknown")
                                    call_ret = this->_lookup_method_return(owner_t, attr);
                                if (owner_t == "Path") {
                                    if (py_contains(set<str>{"read_text", "name", "stem"}, attr)) {
                                        call_ret = "str";
                                    } else {
                                        if (py_contains(set<str>{"exists"}, attr)) {
                                            call_ret = "bool";
                                        } else {
                                            if (py_contains(set<str>{"mkdir", "write_text"}, attr))
                                                call_ret = "None";
                                        }
                                    }
                                } else {
                                    if (owner_t == "PyFile") {
                                        if (py_contains(set<str>{"close", "write"}, attr))
                                            call_ret = "None";
                                    }
                                }
                            }
                        } else {
                            if ((py_is_dict(node)) && (py_dict_get_maybe(node, "kind") == "Lambda"))
                                call_ret = py_to_string(dict_get_node(node, "return_type", "unknown"));
                        }
                    }
                    dict<str, object> payload = dict<str, object>{{"kind", make_object("Call")}, {"source_span", make_object(this->_node_span(s, int64(py_to_int64(e))))}, {"resolved_type", make_object(call_ret)}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(this->_src_slice(s, int64(py_to_int64(e))))}, {"func", make_object(node)}, {"args", make_object(args)}, {"keywords", make_object(keywords)}};
                    if (fn_name == "print") {
                        payload[py_to_string("lowered_kind")] = make_object("BuiltinCall");
                        payload[py_to_string("builtin_name")] = make_object("print");
                        payload[py_to_string("runtime_call")] = make_object("py_print");
                    } else {
                        if (fn_name == "len") {
                            payload[py_to_string("lowered_kind")] = make_object("BuiltinCall");
                            payload[py_to_string("builtin_name")] = make_object("len");
                            payload[py_to_string("runtime_call")] = make_object("py_len");
                        } else {
                            if (fn_name == "str") {
                                payload[py_to_string("lowered_kind")] = make_object("BuiltinCall");
                                payload[py_to_string("builtin_name")] = make_object("str");
                                payload[py_to_string("runtime_call")] = make_object("py_to_string");
                            } else {
                                if (py_contains(set<str>{"int", "float", "bool"}, fn_name)) {
                                    payload[py_to_string("lowered_kind")] = make_object("BuiltinCall");
                                    payload[py_to_string("builtin_name")] = make_object(fn_name);
                                    payload[py_to_string("runtime_call")] = make_object("static_cast");
                                } else {
                                    if (py_contains(set<str>{"min", "max"}, fn_name)) {
                                        payload[py_to_string("lowered_kind")] = make_object("BuiltinCall");
                                        payload[py_to_string("builtin_name")] = make_object(fn_name);
                                        payload[py_to_string("runtime_call")] = make_object((fn_name == "min" ? "py_min" : "py_max"));
                                    } else {
                                        if (fn_name == "perf_counter") {
                                            payload[py_to_string("lowered_kind")] = make_object("BuiltinCall");
                                            payload[py_to_string("builtin_name")] = make_object("perf_counter");
                                            payload[py_to_string("runtime_call")] = make_object("perf_counter");
                                        } else {
                                            if (py_contains(set<str>{"Exception", "RuntimeError"}, fn_name)) {
                                                payload[py_to_string("lowered_kind")] = make_object("BuiltinCall");
                                                payload[py_to_string("builtin_name")] = make_object(fn_name);
                                                payload[py_to_string("runtime_call")] = make_object("std::runtime_error");
                                            } else {
                                                if (fn_name == "Path") {
                                                    payload[py_to_string("lowered_kind")] = make_object("BuiltinCall");
                                                    payload[py_to_string("builtin_name")] = make_object("Path");
                                                    payload[py_to_string("runtime_call")] = make_object("Path");
                                                } else {
                                                    if (fn_name == "open") {
                                                        payload[py_to_string("lowered_kind")] = make_object("BuiltinCall");
                                                        payload[py_to_string("builtin_name")] = make_object("open");
                                                        payload[py_to_string("runtime_call")] = make_object("open");
                                                    } else {
                                                        if (py_contains(set<str>{"bytes", "bytearray"}, fn_name)) {
                                                            payload[py_to_string("lowered_kind")] = make_object("BuiltinCall");
                                                            payload[py_to_string("builtin_name")] = make_object(fn_name);
                                                        } else {
                                                            if ((py_is_dict(node)) && (py_dict_get_maybe(node, "kind") == "Attribute")) {
                                                                str attr = py_to_string(dict_get_node(node, "attr", ""));
                                                                auto owner = py_dict_get_maybe(node, "value");
                                                                str owner_t = (py_is_dict(owner) ? py_to_string(py_dict_get_default(owner, "resolved_type", "unknown")) : "unknown");
                                                                str rc;
                                                                if (owner_t == "str") {
                                                                    dict<str, str> str_map = dict<str, str>{{"strip", "py_strip"}, {"rstrip", "py_rstrip"}, {"startswith", "py_startswith"}, {"endswith", "py_endswith"}, {"replace", "py_replace"}, {"join", "py_join"}, {"isdigit", "py_isdigit"}, {"isalpha", "py_isalpha"}};
                                                                    if (py_contains(str_map, attr)) {
                                                                        rc = py_dict_get(str_map, py_to_string(attr));
                                                                        payload[py_to_string("lowered_kind")] = make_object("BuiltinCall");
                                                                        payload[py_to_string("builtin_name")] = make_object(attr);
                                                                        payload[py_to_string("runtime_call")] = make_object(rc);
                                                                    }
                                                                } else {
                                                                    if (owner_t == "Path") {
                                                                        dict<str, str> path_map = dict<str, str>{{"mkdir", "std::filesystem::create_directories"}, {"exists", "std::filesystem::exists"}, {"write_text", "py_write_text"}, {"read_text", "py_read_text"}, {"parent", "path_parent"}, {"name", "path_name"}, {"stem", "path_stem"}};
                                                                        if (py_contains(path_map, attr)) {
                                                                            rc = py_dict_get(path_map, py_to_string(attr));
                                                                            payload[py_to_string("lowered_kind")] = make_object("BuiltinCall");
                                                                            payload[py_to_string("builtin_name")] = make_object(attr);
                                                                            payload[py_to_string("runtime_call")] = make_object(rc);
                                                                        }
                                                                    } else {
                                                                        if ((py_contains(INT_TYPES, owner_t)) || (owner_t == "int")) {
                                                                            dict<str, str> int_map = dict<str, str>{{"to_bytes", "py_int_to_bytes"}};
                                                                            if (py_contains(int_map, attr)) {
                                                                                rc = py_dict_get(int_map, py_to_string(attr));
                                                                                payload[py_to_string("lowered_kind")] = make_object("BuiltinCall");
                                                                                payload[py_to_string("builtin_name")] = make_object(attr);
                                                                                payload[py_to_string("runtime_call")] = make_object(rc);
                                                                            }
                                                                        } else {
                                                                            if (py_startswith(owner_t, "list[")) {
                                                                                dict<str, str> list_map = dict<str, str>{{"append", "list.append"}, {"extend", "list.extend"}, {"pop", "list.pop"}, {"clear", "list.clear"}, {"reverse", "list.reverse"}, {"sort", "list.sort"}};
                                                                                if (py_contains(list_map, attr)) {
                                                                                    rc = py_dict_get(list_map, py_to_string(attr));
                                                                                    payload[py_to_string("lowered_kind")] = make_object("BuiltinCall");
                                                                                    payload[py_to_string("builtin_name")] = make_object(attr);
                                                                                    payload[py_to_string("runtime_call")] = make_object(rc);
                                                                                }
                                                                            } else {
                                                                                if (py_startswith(owner_t, "set[")) {
                                                                                    dict<str, str> set_map = dict<str, str>{{"add", "set.add"}, {"discard", "set.discard"}, {"remove", "set.remove"}, {"clear", "set.clear"}};
                                                                                    if (py_contains(set_map, attr)) {
                                                                                        rc = py_dict_get(set_map, py_to_string(attr));
                                                                                        payload[py_to_string("lowered_kind")] = make_object("BuiltinCall");
                                                                                        payload[py_to_string("builtin_name")] = make_object(attr);
                                                                                        payload[py_to_string("runtime_call")] = make_object(rc);
                                                                                    }
                                                                                } else {
                                                                                    if (py_startswith(owner_t, "dict[")) {
                                                                                        dict<str, str> dict_map = dict<str, str>{{"get", "dict.get"}, {"pop", "dict.pop"}, {"items", "dict.items"}, {"keys", "dict.keys"}, {"values", "dict.values"}};
                                                                                        if (py_contains(dict_map, attr)) {
                                                                                            rc = py_dict_get(dict_map, py_to_string(attr));
                                                                                            payload[py_to_string("lowered_kind")] = make_object("BuiltinCall");
                                                                                            payload[py_to_string("builtin_name")] = make_object(attr);
                                                                                            payload[py_to_string("runtime_call")] = make_object(rc);
                                                                                        }
                                                                                    } else {
                                                                                        if (owner_t == "unknown") {
                                                                                            dict<str, str> unknown_map = dict<str, str>{{"append", "list.append"}, {"extend", "list.extend"}, {"pop", "list.pop"}, {"get", "dict.get"}, {"items", "dict.items"}, {"keys", "dict.keys"}, {"values", "dict.values"}, {"isdigit", "py_isdigit"}, {"isalpha", "py_isalpha"}};
                                                                                            if (py_contains(unknown_map, attr)) {
                                                                                                rc = py_dict_get(unknown_map, py_to_string(attr));
                                                                                                payload[py_to_string("lowered_kind")] = make_object("BuiltinCall");
                                                                                                payload[py_to_string("builtin_name")] = make_object(attr);
                                                                                                payload[py_to_string("runtime_call")] = make_object(rc);
                                                                                            }
                                                                                        }
                                                                                    }
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    node = payload;
                    continue;
                }
                if (py_dict_get(tok, py_to_string("k")) == "[") {
                    dict<str, object> ltok = this->_eat("[");
                    if (py_dict_get(this->_cur(), py_to_string("k")) == ":") {
                        this->_eat(":");
                        object up = object{};
                        if (py_dict_get(this->_cur(), py_to_string("k")) != "]")
                            up = make_object(this->_parse_addsub());
                        dict<str, object> rtok = this->_eat("]");
                        int64 s = py_to_int64(py_dict_get(py_dict_get(node, py_to_string("source_span")), "col")) - this->col_base;
                        object e = make_object(py_dict_get(rtok, py_to_string("e")));
                        node = dict<str, object>{{"kind", make_object("Subscript")}, {"source_span", make_object(this->_node_span(s, int64(py_to_int64(e))))}, {"resolved_type", make_object(dict_get_node(node, "resolved_type", "unknown"))}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(this->_src_slice(s, int64(py_to_int64(e))))}, {"value", make_object(node)}, {"slice", make_object(dict<str, object>{{"kind", make_object("Slice")}, {"lower", make_object(::std::nullopt)}, {"upper", make_object(up)}, {"step", make_object(::std::nullopt)}})}, {"lowered_kind", make_object("SliceExpr")}, {"lower", make_object(::std::nullopt)}, {"upper", make_object(up)}};
                        continue;
                    }
                    dict<str, object> first = this->_parse_addsub();
                    if (py_dict_get(this->_cur(), py_to_string("k")) == ":") {
                        this->_eat(":");
                        object up = object{};
                        if (py_dict_get(this->_cur(), py_to_string("k")) != "]")
                            up = make_object(this->_parse_addsub());
                        dict<str, object> rtok = this->_eat("]");
                        int64 s = py_to_int64(py_dict_get(py_dict_get(node, py_to_string("source_span")), "col")) - this->col_base;
                        object e = make_object(py_dict_get(rtok, py_to_string("e")));
                        node = dict<str, object>{{"kind", make_object("Subscript")}, {"source_span", make_object(this->_node_span(s, int64(py_to_int64(e))))}, {"resolved_type", make_object(dict_get_node(node, "resolved_type", "unknown"))}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(this->_src_slice(s, int64(py_to_int64(e))))}, {"value", make_object(node)}, {"slice", make_object(dict<str, object>{{"kind", make_object("Slice")}, {"lower", make_object(first)}, {"upper", make_object(up)}, {"step", make_object(::std::nullopt)}})}, {"lowered_kind", make_object("SliceExpr")}, {"lower", make_object(first)}, {"upper", make_object(up)}};
                        continue;
                    }
                    dict<str, object> rtok = this->_eat("]");
                    int64 s = py_to_int64(py_dict_get(py_dict_get(node, py_to_string("source_span")), "col")) - this->col_base;
                    object e = make_object(py_dict_get(rtok, py_to_string("e")));
                    str out_t = this->_subscript_result_type(py_to_string(dict_get_node(node, "resolved_type", "unknown")));
                    node = dict<str, object>{{"kind", make_object("Subscript")}, {"source_span", make_object(this->_node_span(s, int64(py_to_int64(e))))}, {"resolved_type", make_object(out_t)}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(this->_src_slice(s, int64(py_to_int64(e))))}, {"value", make_object(node)}, {"slice", make_object(first)}};
                    continue;
                }
                return node;
            }
        }
        dict<str, object> _parse_comp_target() {
            /* 内包表現のターゲット（name / tuple）を解析する。 */
            if (py_dict_get(this->_cur(), py_to_string("k")) == "NAME") {
                dict<str, object> nm = this->_eat("NAME");
                auto t = py_dict_get_default(this->name_types, py_to_string(py_to_string(py_dict_get(nm, py_to_string("v")))), "unknown");
                return dict<str, object>{{"kind", make_object("Name")}, {"source_span", make_object(this->_node_span(int64(py_to_int64(py_dict_get(nm, py_to_string("s")))), int64(py_to_int64(py_dict_get(nm, py_to_string("e"))))))}, {"resolved_type", make_object(t)}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(py_to_string(py_dict_get(nm, py_to_string("v"))))}, {"id", make_object(py_to_string(py_dict_get(nm, py_to_string("v"))))}};
            }
            if (py_dict_get(this->_cur(), py_to_string("k")) == "(") {
                dict<str, object> l = this->_eat("(");
                list<dict<str, object>> elems = list<dict<str, object>>{};
                elems.append(dict<str, object>(this->_parse_comp_target()));
                while (py_dict_get(this->_cur(), py_to_string("k")) == ",") {
                    this->_eat(",");
                    if (py_dict_get(this->_cur(), py_to_string("k")) == ")")
                        break;
                    elems.append(dict<str, object>(this->_parse_comp_target()));
                }
                dict<str, object> r = this->_eat(")");
                return dict<str, object>{{"kind", make_object("Tuple")}, {"source_span", make_object(this->_node_span(int64(py_to_int64(py_dict_get(l, py_to_string("s")))), int64(py_to_int64(py_dict_get(r, py_to_string("e"))))))}, {"resolved_type", make_object("tuple[unknown]")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(this->_src_slice(int64(py_to_int64(py_dict_get(l, py_to_string("s")))), int64(py_to_int64(py_dict_get(r, py_to_string("e"))))))}, {"elements", make_object(elems)}};
            }
            dict<str, object> tok = this->_cur();
            throw _make_east_build_error("unsupported_syntax", "invalid comprehension target in call argument", this->_node_span(int64(py_to_int64(py_dict_get(tok, py_to_string("s")))), int64(py_to_int64(py_dict_get(tok, py_to_string("e"))))), "Use name or tuple target in generator expression.");
        }
        dict<str, object> _parse_call_arg_expr() {
            /* 呼び出し引数式を解析し、必要なら generator 引数へ lower する。 */
            dict<str, object> first = this->_parse_ifexp();
            if (!((py_dict_get(this->_cur(), py_to_string("k")) == "NAME") && (py_dict_get(this->_cur(), py_to_string("v")) == "for")))
                return first;
            this->_eat("NAME");
            dict<str, object> target = this->_parse_comp_target();
            dict<str, object> in_tok = this->_eat("NAME");
            if (py_dict_get(in_tok, py_to_string("v")) != "in")
                throw _make_east_build_error("unsupported_syntax", "expected 'in' in generator expression", this->_node_span(int64(py_to_int64(py_dict_get(in_tok, py_to_string("s")))), int64(py_to_int64(py_dict_get(in_tok, py_to_string("e"))))), "Use `for x in iterable` form.");
            dict<str, object> iter_expr = this->_parse_ifexp();
            list<dict<str, object>> ifs = list<dict<str, object>>{};
            while ((py_dict_get(this->_cur(), py_to_string("k")) == "NAME") && (py_dict_get(this->_cur(), py_to_string("v")) == "if")) {
                this->_eat("NAME");
                ifs.append(dict<str, object>(this->_parse_ifexp()));
            }
            int64 s = py_to_int64(py_dict_get(py_dict_get(first, py_to_string("source_span")), "col")) - this->col_base;
            dict<str, object> end_node = (py_len(ifs) > 0 ? py_at(ifs, -1) : iter_expr);
            int64 e = py_to_int64(py_dict_get(py_dict_get(end_node, py_to_string("source_span")), "end_col")) - this->col_base;
            return dict<str, object>{{"kind", make_object("ListComp")}, {"source_span", make_object(this->_node_span(s, e))}, {"resolved_type", make_object("list[" + py_to_string(dict_get_node(first, "resolved_type", "unknown")) + "]")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(this->_src_slice(s, e))}, {"elt", make_object(first)}, {"generators", make_object(list<dict<str, object>>{dict<str, object>{{"target", make_object(target)}, {"iter", make_object(iter_expr)}, {"ifs", make_object(ifs)}, {"is_async", make_object(false)}}})}, {"lowered_kind", make_object("GeneratorArg")}};
        }
        dict<str, object> _make_bin(const dict<str, object>& left, const str& op_sym, const dict<str, object>& right) {
            /* 二項演算ノードを構築し、数値昇格 cast も付与する。 */
            dict<str, str> op_map = dict<str, str>{{"+", "Add"}, {"-", "Sub"}, {"*", "Mult"}, {"/", "Div"}, {"//", "FloorDiv"}, {"%", "Mod"}, {"&", "BitAnd"}, {"|", "BitOr"}, {"^", "BitXor"}, {"<<", "LShift"}, {">>", "RShift"}};
            str lt = py_to_string(dict_get_node(left, "resolved_type", "unknown"));
            str rt = py_to_string(dict_get_node(right, "resolved_type", "unknown"));
            list<dict<str, object>> casts = list<dict<str, object>>{};
            str out_t;
            if (op_sym == "/") {
                if ((lt == "Path") && (py_contains(set<str>{"str", "Path"}, rt))) {
                    out_t = "Path";
                } else {
                    out_t = "float64";
                    if (lt == "int64")
                        casts.append(dict<str, object>(dict<str, str>{{"on", "left"}, {"from", "int64"}, {"to", "float64"}, {"reason", "numeric_promotion"}}));
                    if (rt == "int64")
                        casts.append(dict<str, object>(dict<str, str>{{"on", "right"}, {"from", "int64"}, {"to", "float64"}, {"reason", "numeric_promotion"}}));
                }
            } else {
                if (op_sym == "//") {
                    out_t = ((py_contains(set<str>{"int64", "unknown"}, lt)) && (py_contains(set<str>{"int64", "unknown"}, rt)) ? "int64" : "float64");
                } else {
                    if ((op_sym == "+") && (((py_contains(set<str>{"bytes", "bytearray"}, lt)) && (py_contains(set<str>{"bytes", "bytearray"}, rt))) || ((lt == "str") && (rt == "str")))) {
                        out_t = ((py_contains(set<str>{"bytes", "bytearray"}, lt)) && (py_contains(set<str>{"bytes", "bytearray"}, rt)) ? "bytes" : "str");
                    } else {
                        if ((lt == rt) && (py_contains(set<str>{"int64", "float64"}, lt))) {
                            out_t = lt;
                        } else {
                            if ((py_contains(set<str>{"int64", "float64"}, lt)) && (py_contains(set<str>{"int64", "float64"}, rt))) {
                                out_t = "float64";
                                if (lt == "int64")
                                    casts.append(dict<str, object>(dict<str, str>{{"on", "left"}, {"from", "int64"}, {"to", "float64"}, {"reason", "numeric_promotion"}}));
                                if (rt == "int64")
                                    casts.append(dict<str, object>(dict<str, str>{{"on", "right"}, {"from", "int64"}, {"to", "float64"}, {"reason", "numeric_promotion"}}));
                            } else {
                                if ((py_contains(set<str>{"&", "|", "^", "<<", ">>"}, op_sym)) && (lt == "int64") && (rt == "int64"))
                                    out_t = "int64";
                                else
                                    out_t = "unknown";
                            }
                        }
                    }
                }
            }
            
            int64 ls = py_to_int64(py_dict_get(py_dict_get(left, py_to_string("source_span")), "col")) - this->col_base;
            int64 rs = py_to_int64(py_dict_get(py_dict_get(right, py_to_string("source_span")), "end_col")) - this->col_base;
            return dict<str, object>{{"kind", make_object("BinOp")}, {"source_span", make_object(this->_node_span(ls, rs))}, {"resolved_type", make_object(out_t)}, {"borrow_kind", make_object("value")}, {"casts", make_object(casts)}, {"repr", make_object(this->_src_slice(ls, rs))}, {"left", make_object(left)}, {"op", make_object(py_dict_get(op_map, py_to_string(op_sym)))}, {"right", make_object(right)}};
        }
        dict<str, object> _parse_primary() {
            /* リテラル・名前・括弧式などの primary 式を解析する。 */
            dict<str, object> tok = this->_cur();
            if (py_dict_get(tok, py_to_string("k")) == "INT") {
                this->_eat("INT");
                str tok_v = py_to_string(py_dict_get(tok, py_to_string("v")));
                int64 tok_value = py_to_int64(tok_v);
                if ((py_startswith(tok_v, "0x")) || (py_startswith(tok_v, "0X"))) {
                    tok_value = py_to_int64_base(py_slice(tok_v, 2, py_len(tok_v)), py_to_int64(16));
                } else {
                    if ((py_startswith(tok_v, "0b")) || (py_startswith(tok_v, "0B"))) {
                        tok_value = py_to_int64_base(py_slice(tok_v, 2, py_len(tok_v)), py_to_int64(2));
                    } else {
                        if ((py_startswith(tok_v, "0o")) || (py_startswith(tok_v, "0O")))
                            tok_value = py_to_int64_base(py_slice(tok_v, 2, py_len(tok_v)), py_to_int64(8));
                    }
                }
                return dict<str, object>{{"kind", make_object("Constant")}, {"source_span", make_object(this->_node_span(int64(py_to_int64(py_dict_get(tok, py_to_string("s")))), int64(py_to_int64(py_dict_get(tok, py_to_string("e"))))))}, {"resolved_type", make_object("int64")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(py_dict_get(tok, py_to_string("v")))}, {"value", make_object(tok_value)}};
            }
            if (py_dict_get(tok, py_to_string("k")) == "FLOAT") {
                this->_eat("FLOAT");
                return dict<str, object>{{"kind", make_object("Constant")}, {"source_span", make_object(this->_node_span(int64(py_to_int64(py_dict_get(tok, py_to_string("s")))), int64(py_to_int64(py_dict_get(tok, py_to_string("e"))))))}, {"resolved_type", make_object("float64")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(py_dict_get(tok, py_to_string("v")))}, {"value", make_object(py_to_float64(py_dict_get(tok, py_to_string("v"))))}};
            }
            if (py_dict_get(tok, py_to_string("k")) == "STR") {
                this->_eat("STR");
                str raw = py_to_string(py_dict_get(tok, py_to_string("v")));
                // Support prefixed literals (f/r/b/u/rf/fr...) in expression parser.
                int64 p = 0;
                while ((p < py_len(raw)) && (py_contains("rRbBuUfF", raw[p]))) {
                    p++;
                }
                auto prefix = py_slice(raw, 0, p).lower();
                if (p >= py_len(raw))
                    p = 0;
                
                bool is_triple = (p + 2 < py_len(raw)) && (py_contains(set<str>{"'''", "\"\"\""}, py_slice(raw, p, p + 3)));
                str body;
                if (is_triple)
                    body = py_slice(raw, p + 3, -3);
                else
                    body = py_slice(raw, p + 1, -1);
                
                if (py_contains(prefix, "f")) {
                    list<dict<str, object>> values = list<dict<str, object>>{};
                    bool is_raw = py_contains(prefix, "r");
                    
                    int64 i = 0;
                    while (i < py_len(body)) {
                        auto j = body.find("{", i);
                        if (j < 0) {
                            _sh_append_fstring_literal(values, py_slice(body, i, py_len(body)), this->_node_span(int64(py_to_int64(py_dict_get(tok, py_to_string("s")))), int64(py_to_int64(py_dict_get(tok, py_to_string("e"))))), is_raw);
                            break;
                        }
                        if ((j + 1 < py_len(body)) && (body.at(j + 1) == '{')) {
                            _sh_append_fstring_literal(values, py_slice(body, i, j + 1), this->_node_span(int64(py_to_int64(py_dict_get(tok, py_to_string("s")))), int64(py_to_int64(py_dict_get(tok, py_to_string("e"))))), is_raw);
                            i = j + 2;
                            continue;
                        }
                        if (j > i)
                            _sh_append_fstring_literal(values, py_slice(body, i, j), this->_node_span(int64(py_to_int64(py_dict_get(tok, py_to_string("s")))), int64(py_to_int64(py_dict_get(tok, py_to_string("e"))))), is_raw);
                        auto k = body.find("}", j + 1);
                        if (k < 0)
                            throw _make_east_build_error("unsupported_syntax", "unterminated f-string placeholder in self_hosted parser", this->_node_span(int64(py_to_int64(py_dict_get(tok, py_to_string("s")))), int64(py_to_int64(py_dict_get(tok, py_to_string("e"))))), "Close f-string placeholder with `}`.");
                        auto inner_expr = py_strip(py_slice(body, j + 1, k));
                        dict<str, object> fv = dict<str, object>{{"kind", make_object("FormattedValue")}, {"value", make_object(_sh_parse_expr(inner_expr, this->line_no, this->col_base + py_dict_get(tok, py_to_string("s")), this->name_types, this->fn_return_types, this->class_method_return_types, this->class_base))}};
                        values.append(dict<str, object>(fv));
                        i = k + 1;
                    }
                    return dict<str, object>{{"kind", make_object("JoinedStr")}, {"source_span", make_object(this->_node_span(int64(py_to_int64(py_dict_get(tok, py_to_string("s")))), int64(py_to_int64(py_dict_get(tok, py_to_string("e"))))))}, {"resolved_type", make_object("str")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(raw)}, {"values", make_object(values)}};
                }
                str resolved_type = "str";
                if ((py_contains(prefix, "b")) && (!py_contains(prefix, "f")))
                    resolved_type = "bytes";
                body = _sh_decode_py_string_body(body, py_contains(prefix, "r"));
                return dict<str, object>{{"kind", make_object("Constant")}, {"source_span", make_object(this->_node_span(int64(py_to_int64(py_dict_get(tok, py_to_string("s")))), int64(py_to_int64(py_dict_get(tok, py_to_string("e"))))))}, {"resolved_type", make_object(resolved_type)}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(raw)}, {"value", make_object(body)}};
            }
            if (py_dict_get(tok, py_to_string("k")) == "NAME") {
                dict<str, object> name_tok = this->_eat("NAME");
                str nm = py_to_string(py_dict_get(name_tok, py_to_string("v")));
                if (py_contains(set<str>{"True", "False"}, nm))
                    return dict<str, object>{{"kind", make_object("Constant")}, {"source_span", make_object(this->_node_span(int64(py_to_int64(py_dict_get(name_tok, py_to_string("s")))), int64(py_to_int64(py_dict_get(name_tok, py_to_string("e"))))))}, {"resolved_type", make_object("bool")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(nm)}, {"value", make_object(nm == "True")}};
                if (nm == "None")
                    return dict<str, object>{{"kind", make_object("Constant")}, {"source_span", make_object(this->_node_span(int64(py_to_int64(py_dict_get(name_tok, py_to_string("s")))), int64(py_to_int64(py_dict_get(name_tok, py_to_string("e"))))))}, {"resolved_type", make_object("None")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(nm)}, {"value", make_object(::std::nullopt)}};
                auto t = py_dict_get_default(this->name_types, py_to_string(nm), "unknown");
                return dict<str, object>{{"kind", make_object("Name")}, {"source_span", make_object(this->_node_span(int64(py_to_int64(py_dict_get(name_tok, py_to_string("s")))), int64(py_to_int64(py_dict_get(name_tok, py_to_string("e"))))))}, {"resolved_type", make_object(t)}, {"borrow_kind", make_object((t != "unknown" ? "readonly_ref" : "value"))}, {"casts", make_object(list<object>{})}, {"repr", make_object(nm)}, {"id", make_object(nm)}};
            }
            if (py_dict_get(tok, py_to_string("k")) == "(") {
                dict<str, object> l = this->_eat("(");
                if (py_dict_get(this->_cur(), py_to_string("k")) == ")") {
                    dict<str, object> r = this->_eat(")");
                    return dict<str, object>{{"kind", make_object("Tuple")}, {"source_span", make_object(this->_node_span(int64(py_to_int64(py_dict_get(l, py_to_string("s")))), int64(py_to_int64(py_dict_get(r, py_to_string("e"))))))}, {"resolved_type", make_object("tuple[]")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(this->_src_slice(int64(py_to_int64(py_dict_get(l, py_to_string("s")))), int64(py_to_int64(py_dict_get(r, py_to_string("e"))))))}, {"elements", make_object(list<object>{})}};
                }
                dict<str, object> first = this->_parse_ifexp();
                if (py_dict_get(this->_cur(), py_to_string("k")) == ",") {
                    list<dict<str, object>> elements = list<dict<str, object>>{first};
                    while (py_dict_get(this->_cur(), py_to_string("k")) == ",") {
                        this->_eat(",");
                        if (py_dict_get(this->_cur(), py_to_string("k")) == ")")
                            break;
                        elements.append(dict<str, object>(this->_parse_ifexp()));
                    }
                    dict<str, object> r = this->_eat(")");
                    list<str> elem_types = [&]() -> list<str> {     list<str> __out;     for (auto e : elements) {         __out.append(py_to_string(dict_get_node(e, "resolved_type", "unknown")));     }     return __out; }();
                    return dict<str, object>{{"kind", make_object("Tuple")}, {"source_span", make_object(this->_node_span(int64(py_to_int64(py_dict_get(l, py_to_string("s")))), int64(py_to_int64(py_dict_get(r, py_to_string("e"))))))}, {"resolved_type", make_object("tuple[" + py_to_string(str(",").join(elem_types)) + "]")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(this->_src_slice(int64(py_to_int64(py_dict_get(l, py_to_string("s")))), int64(py_to_int64(py_dict_get(r, py_to_string("e"))))))}, {"elements", make_object(elements)}};
                }
                dict<str, object> r = this->_eat(")");
                first[py_to_string("source_span")] = make_object(this->_node_span(int64(py_to_int64(py_dict_get(l, py_to_string("s")))), int64(py_to_int64(py_dict_get(r, py_to_string("e"))))));
                first[py_to_string("repr")] = make_object(this->_src_slice(int64(py_to_int64(py_dict_get(l, py_to_string("s")))), int64(py_to_int64(py_dict_get(r, py_to_string("e"))))));
                return first;
            }
            if (py_dict_get(tok, py_to_string("k")) == "[") {
                dict<str, object> l = this->_eat("[");
                list<dict<str, object>> elements = list<dict<str, object>>{};
                if (py_dict_get(this->_cur(), py_to_string("k")) != "]") {
                    dict<str, object> first = this->_parse_ifexp();
                    // list comprehension: [elt for x in iter if cond]
                    if ((py_dict_get(this->_cur(), py_to_string("k")) == "NAME") && (py_dict_get(this->_cur(), py_to_string("v")) == "for")) {
                        this->_eat("NAME");
                        dict<str, object> tgt_tok = this->_eat("NAME");
                        dict<str, object> in_tok = this->_eat("NAME");
                        if (py_dict_get(in_tok, py_to_string("v")) != "in")
                            throw _make_east_build_error("unsupported_syntax", "expected 'in' in list comprehension", this->_node_span(int64(py_to_int64(py_dict_get(in_tok, py_to_string("s")))), int64(py_to_int64(py_dict_get(in_tok, py_to_string("e"))))), "Use `[x for x in iterable]` syntax.");
                        dict<str, object> iter_expr = this->_parse_ifexp();
                        if ((py_is_dict(iter_expr)) && (py_dict_get_maybe(iter_expr, "kind") == "Call") && (py_is_dict(py_dict_get_maybe(iter_expr, "func"))) && (py_dict_get_maybe(dict_get_node(iter_expr, "func", dict<str, object>{}), "kind") == "Name") && (py_dict_get_maybe(dict_get_node(iter_expr, "func", dict<str, object>{}), "id") == "range")) {
                            list<object> rargs = dict_get_node(iter_expr, "args", list<object>{});
                            dict<str, str> start_node;
                            object stop_node;
                            dict<str, str> step_node;
                            if (py_len(rargs) == 1) {
                                start_node = dict<str, object>{{"kind", make_object("Constant")}, {"source_span", make_object(this->_node_span(int64(py_to_int64(py_dict_get(tgt_tok, py_to_string("s")))), int64(py_to_int64(py_dict_get(tgt_tok, py_to_string("s"))))))}, {"resolved_type", make_object("int64")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object("0")}, {"value", make_object(0)}};
                                stop_node = make_object(rargs[0]);
                                step_node = dict<str, object>{{"kind", make_object("Constant")}, {"source_span", make_object(this->_node_span(int64(py_to_int64(py_dict_get(tgt_tok, py_to_string("s")))), int64(py_to_int64(py_dict_get(tgt_tok, py_to_string("s"))))))}, {"resolved_type", make_object("int64")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object("1")}, {"value", make_object(1)}};
                            } else {
                                if (py_len(rargs) == 2) {
                                    start_node = rargs[0];
                                    stop_node = make_object(rargs[1]);
                                    step_node = dict<str, object>{{"kind", make_object("Constant")}, {"source_span", make_object(this->_node_span(int64(py_to_int64(py_dict_get(tgt_tok, py_to_string("s")))), int64(py_to_int64(py_dict_get(tgt_tok, py_to_string("s"))))))}, {"resolved_type", make_object("int64")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object("1")}, {"value", make_object(1)}};
                                } else {
                                    start_node = rargs[0];
                                    stop_node = make_object(rargs[1]);
                                    step_node = rargs[2];
                                }
                            }
                            object step_const_obj = object{};
                            if (py_is_dict(step_node))
                                step_const_obj = make_object(py_dict_get_maybe(step_node, py_to_string("value")));
                            ::std::optional<int> step_const = ::std::nullopt;
                            if (py_is_int(step_const_obj))
                                step_const = py_to_int64(step_const_obj);
                            str mode = "dynamic";
                            if (step_const == 1) {
                                mode = "ascending";
                            } else {
                                if (step_const == -1)
                                    mode = "descending";
                            }
                            iter_expr = dict<str, object>{{"kind", make_object("RangeExpr")}, {"source_span", make_object(py_dict_get_maybe(iter_expr, "source_span"))}, {"resolved_type", make_object("range")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(dict_get_node(iter_expr, "repr", "range(...)"))}, {"start", make_object(start_node)}, {"stop", make_object(stop_node)}, {"step", make_object(step_node)}, {"range_mode", make_object(mode)}};
                        }
                        list<dict<str, object>> ifs = list<dict<str, object>>{};
                        while ((py_dict_get(this->_cur(), py_to_string("k")) == "NAME") && (py_dict_get(this->_cur(), py_to_string("v")) == "if")) {
                            this->_eat("NAME");
                            ifs.append(dict<str, object>(this->_parse_ifexp()));
                        }
                        dict<str, object> r = this->_eat("]");
                        str tgt_name = py_to_string(py_dict_get(tgt_tok, py_to_string("v")));
                        str tgt_ty = this->_iter_item_type(iter_expr);
                        dict<str, object> first_norm = first;
                        list<dict<str, object>> ifs_norm = ifs;
                        if (tgt_ty != "unknown") {
                            auto old_t = py_dict_get_default(this->name_types, py_to_string(tgt_name), "");
                            this->name_types[py_to_string(tgt_name)] = tgt_ty;
                            auto first_repr = py_dict_get_maybe(first, "repr");
                            int64 first_col = py_to_int64(py_dict_get_default(dict_get_node(first, "source_span", dict<str, object>{}), "col", this->col_base));
                            if ((py_is_str(first_repr)) && (first_repr != ""))
                                first_norm = _sh_parse_expr(first_repr, this->line_no, first_col, this->name_types, this->fn_return_types, this->class_method_return_types, this->class_base);
                            ifs_norm = list<object>{};
                            for (dict<str, object> cond : ifs) {
                                auto cond_repr = py_dict_get_maybe(cond, "repr");
                                int64 cond_col = py_to_int64(py_dict_get_default(dict_get_node(cond, "source_span", dict<str, object>{}), "col", this->col_base));
                                if ((py_is_str(cond_repr)) && (cond_repr != ""))
                                    ifs_norm.append(_sh_parse_expr(cond_repr, this->line_no, cond_col, this->name_types, this->fn_return_types, this->class_method_return_types, this->class_base));
                                else
                                    ifs_norm.append(cond);
                            }
                            if (old_t == "")
                                (this->name_types.contains(py_to_string(tgt_name)) ? this->name_types.pop(py_to_string(tgt_name)) : str());
                            else
                                this->name_types[py_to_string(tgt_name)] = old_t;
                        }
                        return dict<str, object>{{"kind", make_object("ListComp")}, {"source_span", make_object(this->_node_span(int64(py_to_int64(py_dict_get(l, py_to_string("s")))), int64(py_to_int64(py_dict_get(r, py_to_string("e"))))))}, {"resolved_type", make_object("list[" + py_to_string(dict_get_node(first_norm, "resolved_type", "unknown")) + "]")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(this->_src_slice(int64(py_to_int64(py_dict_get(l, py_to_string("s")))), int64(py_to_int64(py_dict_get(r, py_to_string("e"))))))}, {"elt", make_object(first_norm)}, {"generators", make_object(list<dict<str, object>>{dict<str, object>{{"target", make_object(dict<str, object>{{"kind", make_object("Name")}, {"source_span", make_object(this->_node_span(int64(py_to_int64(py_dict_get(tgt_tok, py_to_string("s")))), int64(py_to_int64(py_dict_get(tgt_tok, py_to_string("e"))))))}, {"resolved_type", make_object(tgt_ty)}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(tgt_name)}, {"id", make_object(tgt_name)}})}, {"iter", make_object(iter_expr)}, {"ifs", make_object(ifs_norm)}}})}};
                    }
                    
                    elements.append(dict<str, object>(first));
                    while (true) {
                        if (py_dict_get(this->_cur(), py_to_string("k")) == ",") {
                            this->_eat(",");
                            if (py_dict_get(this->_cur(), py_to_string("k")) == "]")
                                break;
                            elements.append(dict<str, object>(this->_parse_ifexp()));
                            continue;
                        }
                        break;
                    }
                }
                dict<str, object> r = this->_eat("]");
                str et = "unknown";
                if (py_len(elements) > 0) {
                    et = py_to_string(dict_get_node(elements[0], "resolved_type", "unknown"));
                    for (dict<str, object> e : py_slice(elements, 1, py_len(elements))) {
                        if (py_to_string(dict_get_node(e, "resolved_type", "unknown")) != et) {
                            et = "unknown";
                            break;
                        }
                    }
                }
                return dict<str, object>{{"kind", make_object("List")}, {"source_span", make_object(this->_node_span(int64(py_to_int64(py_dict_get(l, py_to_string("s")))), int64(py_to_int64(py_dict_get(r, py_to_string("e"))))))}, {"resolved_type", make_object("list[" + et + "]")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(this->_src_slice(int64(py_to_int64(py_dict_get(l, py_to_string("s")))), int64(py_to_int64(py_dict_get(r, py_to_string("e"))))))}, {"elements", make_object(elements)}};
            }
            if (py_dict_get(tok, py_to_string("k")) == "{") {
                dict<str, object> l = this->_eat("{");
                if (py_dict_get(this->_cur(), py_to_string("k")) == "}") {
                    dict<str, object> r = this->_eat("}");
                    return dict<str, object>{{"kind", make_object("Dict")}, {"source_span", make_object(this->_node_span(int64(py_to_int64(py_dict_get(l, py_to_string("s")))), int64(py_to_int64(py_dict_get(r, py_to_string("e"))))))}, {"resolved_type", make_object("dict[unknown,unknown]")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(this->_src_slice(int64(py_to_int64(py_dict_get(l, py_to_string("s")))), int64(py_to_int64(py_dict_get(r, py_to_string("e"))))))}, {"keys", make_object(list<object>{})}, {"values", make_object(list<object>{})}};
                }
                dict<str, object> first = this->_parse_ifexp();
                if (py_dict_get(this->_cur(), py_to_string("k")) == ":") {
                    list<dict<str, object>> keys = list<dict<str, object>>{first};
                    list<dict<str, object>> vals = list<dict<str, object>>{};
                    this->_eat(":");
                    vals.append(dict<str, object>(this->_parse_ifexp()));
                    while (py_dict_get(this->_cur(), py_to_string("k")) == ",") {
                        this->_eat(",");
                        if (py_dict_get(this->_cur(), py_to_string("k")) == "}")
                            break;
                        keys.append(dict<str, object>(this->_parse_ifexp()));
                        this->_eat(":");
                        vals.append(dict<str, object>(this->_parse_ifexp()));
                    }
                    dict<str, object> r = this->_eat("}");
                    str kt = (py_len(keys) > 0 ? py_to_string(dict_get_node(keys[0], "resolved_type", "unknown")) : "unknown");
                    str vt = (py_len(vals) > 0 ? py_to_string(dict_get_node(vals[0], "resolved_type", "unknown")) : "unknown");
                    return dict<str, object>{{"kind", make_object("Dict")}, {"source_span", make_object(this->_node_span(int64(py_to_int64(py_dict_get(l, py_to_string("s")))), int64(py_to_int64(py_dict_get(r, py_to_string("e"))))))}, {"resolved_type", make_object("dict[" + kt + "," + vt + "]")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(this->_src_slice(int64(py_to_int64(py_dict_get(l, py_to_string("s")))), int64(py_to_int64(py_dict_get(r, py_to_string("e"))))))}, {"keys", make_object(keys)}, {"values", make_object(vals)}};
                }
                list<dict<str, object>> elements = list<dict<str, object>>{first};
                while (py_dict_get(this->_cur(), py_to_string("k")) == ",") {
                    this->_eat(",");
                    if (py_dict_get(this->_cur(), py_to_string("k")) == "}")
                        break;
                    elements.append(dict<str, object>(this->_parse_ifexp()));
                }
                dict<str, object> r = this->_eat("}");
                str et = (py_len(elements) > 0 ? py_to_string(dict_get_node(elements[0], "resolved_type", "unknown")) : "unknown");
                return dict<str, object>{{"kind", make_object("Set")}, {"source_span", make_object(this->_node_span(int64(py_to_int64(py_dict_get(l, py_to_string("s")))), int64(py_to_int64(py_dict_get(r, py_to_string("e"))))))}, {"resolved_type", make_object("set[" + et + "]")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(this->_src_slice(int64(py_to_int64(py_dict_get(l, py_to_string("s")))), int64(py_to_int64(py_dict_get(r, py_to_string("e"))))))}, {"elements", make_object(elements)}};
            }
            throw _make_east_build_error("unsupported_syntax", "self_hosted parser cannot parse expression token: " + py_to_string(py_dict_get(tok, py_to_string("k"))), this->_node_span(int64(py_to_int64(py_dict_get(tok, py_to_string("s")))), int64(py_to_int64(py_dict_get(tok, py_to_string("e"))))), "Extend self_hosted expression parser for this syntax.");
        }
    };
    
    dict<str, object> _sh_parse_expr(const str& text, int64 line_no, int64 col_base, const dict<str, str>& name_types, const dict<str, str>& fn_return_types, const dict<str, dict<str, str>>& class_method_return_types, const dict<str, ::std::optional<str>>& class_base) {
        /* 1つの式文字列を self-hosted 方式で EAST 式ノードに変換する。 */
        auto txt = py_strip(text);
        if (txt == "")
            throw _make_east_build_error("unsupported_syntax", "empty expression in self_hosted backend", _sh_span(line_no, col_base, col_base), "Provide a non-empty expression.");
        _ShExprParser parser = _ShExprParser(txt, line_no, col_base + py_len(text) - py_len(py_lstrip(text)), name_types, fn_return_types, class_method_return_types, class_base);
        return parser.parse();
    }
    
    dict<str, object> _sh_parse_expr_lowered(const str& expr_txt, int64 ln_no, int64 col, const dict<str, str>& name_types) {
        /* 式文字列を EAST 式ノードへ変換する（簡易 lower を含む）。 */
        str raw = expr_txt;
        auto txt = py_strip(raw);
        
        // lambda は if-expression より結合が弱いので、
        // ここでの簡易 ifexp 分解を回避して self_hosted 式パーサへ委譲する。
        if (py_startswith(txt, "lambda "))
            return _sh_parse_expr(txt, ln_no, col, name_types, _SH_FN_RETURNS, _SH_CLASS_METHOD_RETURNS, _SH_CLASS_BASE);
        
        // if-expression: a if cond else b
        int64 p_if = _sh_split_top_keyword(txt, "if");
        int64 p_else = _sh_split_top_keyword(txt, "else");
        if ((p_if >= 0) && (p_else > p_if)) {
            auto body_txt = py_strip(py_slice(txt, 0, p_if));
            auto test_txt = py_strip(py_slice(txt, p_if + 2, p_else));
            auto else_txt = py_strip(py_slice(txt, p_else + 4, py_len(txt)));
            dict<str, object> body_node = _sh_parse_expr_lowered(body_txt, ln_no, col + txt.find(body_txt), name_types);
            dict<str, object> test_node = _sh_parse_expr_lowered(test_txt, ln_no, col + txt.find(test_txt), name_types);
            dict<str, object> else_node = _sh_parse_expr_lowered(else_txt, ln_no, col + txt.rfind(else_txt), name_types);
            object rt_obj = make_object(dict_get_node(body_node, "resolved_type", "unknown"));
            str rt = (py_is_str(rt_obj) ? py_to_string(rt_obj) : "unknown");
            object else_rt_obj = make_object(dict_get_node(else_node, "resolved_type", "unknown"));
            str else_rt = (py_is_str(else_rt_obj) ? py_to_string(else_rt_obj) : "unknown");
            if (rt != else_rt)
                rt = "unknown";
            return dict<str, object>{{"kind", make_object("IfExp")}, {"source_span", make_object(_sh_span(ln_no, col, col + py_len(raw)))}, {"resolved_type", make_object(rt)}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(txt)}, {"test", make_object(test_node)}, {"body", make_object(body_node)}, {"orelse", make_object(else_node)}};
        }
        
        // Normalize generator-arg any/all into list-comp form for self_hosted parser.
        ::std::optional<rc<pytra::std::re::Match>> m_any_all = pytra::std::re::match("^(any|all)\\((.+)\\)$", txt, pytra::std::re::S);
        if (!py_is_none(m_any_all)) {
            auto fn_name = pytra::std::re::group(m_any_all, 1);
            auto inner_arg = pytra::std::re::strip_group(m_any_all, 2);
            if ((_sh_split_top_keyword(inner_arg, "for") > 0) && (_sh_split_top_keyword(inner_arg, "in") > 0)) {
                dict<str, object> lc = _sh_parse_expr_lowered("[" + py_to_string(inner_arg) + "]", ln_no, col + txt.find(inner_arg), name_types);
                return dict<str, object>{{"kind", make_object("Call")}, {"source_span", make_object(_sh_span(ln_no, col, col + py_len(raw)))}, {"resolved_type", make_object("bool")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(txt)}, {"func", make_object(dict<str, object>{{"kind", make_object("Name")}, {"source_span", make_object(_sh_span(ln_no, col, col + py_len(fn_name)))}, {"resolved_type", make_object("unknown")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(fn_name)}, {"id", make_object(fn_name)}})}, {"args", make_object(list<dict<str, object>>{lc})}, {"keywords", make_object(list<object>{})}};
            }
        }
        
        // Normalize single generator-argument calls into list-comp argument form.
        // Example: ", ".join(f(x) for x in items) -> ", ".join([f(x) for x in items])
        if (py_endswith(txt, ")")) {
            int64 depth = 0;
            ::std::optional<str> in_str = ::std::nullopt;
            bool esc = false;
            int64 open_idx = -1;
            int64 close_idx = -1;
            for (auto __it_29 : py_enumerate(txt)) {
                auto idx = ::std::get<0>(__it_29);
                auto ch = ::std::get<1>(__it_29);
                if (!py_is_none(in_str)) {
                    if (esc) {
                        esc = false;
                    } else {
                        if (ch == "\\") {
                            esc = true;
                        } else {
                            if (ch == in_str)
                                in_str = ::std::nullopt;
                        }
                    }
                    continue;
                }
                if (py_contains(set<str>{"'", "\""}, ch)) {
                    in_str = ch;
                    continue;
                }
                if (ch == "(") {
                    if ((depth == 0) && (open_idx < 0))
                        open_idx = idx;
                    depth++;
                    continue;
                }
                if (ch == ")") {
                    depth--;
                    if (depth == 0)
                        close_idx = idx;
                    continue;
                }
                if ((open_idx > 0) && (close_idx == py_len(txt) - 1)) {
                    auto inner = py_strip(py_slice(txt, open_idx + 1, close_idx));
                    list<str> inner_parts = _sh_split_top_commas(inner);
                    if ((py_len(inner_parts) == 1) && (inner_parts[0] == inner) && (_sh_split_top_keyword(inner, "for") > 0) && (_sh_split_top_keyword(inner, "in") > 0)) {
                        auto rewritten = py_slice(txt, 0, open_idx + 1) + "[" + inner + "]" + py_slice(txt, close_idx, py_len(txt));
                        return _sh_parse_expr_lowered(rewritten, ln_no, col, name_types);
                    }
                }
            }
        }
        
        // Handle concatenation chains that include f-strings before generic parsing.
        list<str> plus_parts = _sh_split_top_plus(txt);
        if ((py_len(plus_parts) >= 2) && (py_any([&]() -> list<bool> {     list<bool> __out;     for (auto p : plus_parts) {         __out.append((py_startswith(p, "f\"")) || (py_startswith(p, "f'")));     }     return __out; }()))) {
            list<dict<str, object>> nodes = [&]() -> list<dict<str, object>> {     list<dict<str, object>> __out;     for (auto p : plus_parts) {         __out.append(_sh_parse_expr_lowered(p, ln_no, col + txt.find(p), name_types));     }     return __out; }();
            dict<str, object> node = nodes[0];
            for (dict<str, object> rhs : py_slice(nodes, 1, py_len(nodes)))
                node = dict<str, object>{{"kind", make_object("BinOp")}, {"source_span", make_object(_sh_span(ln_no, col, col + py_len(raw)))}, {"resolved_type", make_object("str")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(txt)}, {"left", make_object(node)}, {"op", make_object("Add")}, {"right", make_object(rhs)}};
            return node;
        }
        
        // dict-comp support: {k: v for x in it} / {k: v for a, b in it}
        if ((py_startswith(txt, "{")) && (py_endswith(txt, "}")) && (py_contains(txt, ":"))) {
            auto inner = py_strip(py_slice(txt, 1, -1));
            int64 p_for = _sh_split_top_keyword(inner, "for");
            if (p_for > 0) {
                auto head = py_strip(py_slice(inner, 0, p_for));
                auto tail = py_strip(py_slice(inner, p_for + 3, py_len(inner)));
                int64 p_in = _sh_split_top_keyword(tail, "in");
                if (p_in <= 0)
                    throw _make_east_build_error("unsupported_syntax", "invalid dict comprehension in self_hosted parser: " + py_to_string(txt), _sh_span(ln_no, col, col + py_len(raw)), "Use `{key: value for item in iterable}` form.");
                auto tgt_txt = py_strip(py_slice(tail, 0, p_in));
                auto iter_and_if_txt = py_strip(py_slice(tail, p_in + 2, py_len(tail)));
                p_if = _sh_split_top_keyword(iter_and_if_txt, "if");
                object iter_txt;
                str if_txt;
                if (p_if >= 0) {
                    iter_txt = make_object(py_strip(py_slice(iter_and_if_txt, 0, p_if)));
                    if_txt = py_strip(py_slice(iter_and_if_txt, p_if + 2, py_len(iter_and_if_txt)));
                } else {
                    iter_txt = make_object(iter_and_if_txt);
                    if_txt = "";
                }
                if (!py_contains(head, ":"))
                    throw _make_east_build_error("unsupported_syntax", "invalid dict comprehension pair in self_hosted parser: " + py_to_string(txt), _sh_span(ln_no, col, col + py_len(raw)), "Use `key: value` pair before `for`.");
                auto __tuple_32 = head.split(":", 1);
                auto ktxt = py_at(__tuple_32, 0);
                auto vtxt = py_at(__tuple_32, 1);
                ktxt = py_strip(ktxt);
                vtxt = py_strip(vtxt);
                dict<str, object> target_node = _sh_parse_expr_lowered(tgt_txt, ln_no, col + txt.find(tgt_txt), name_types);
                dict<str, object> iter_node = _sh_parse_expr_lowered(py_to_string(iter_txt), ln_no, col + txt.find(iter_txt), name_types);
                auto comp_types = _sh_bind_comp_target_types(name_types, target_node, iter_node);
                dict<str, object> key_node = _sh_parse_expr_lowered(ktxt, ln_no, col + txt.find(ktxt), comp_types);
                dict<str, object> val_node = _sh_parse_expr_lowered(vtxt, ln_no, col + txt.find(vtxt), comp_types);
                list<dict<str, object>> if_nodes = list<dict<str, object>>{};
                if (if_txt != "")
                    if_nodes.append(dict<str, object>(_sh_parse_expr_lowered(if_txt, ln_no, col + txt.find(if_txt), comp_types)));
                str kt = py_to_string(dict_get_node(key_node, "resolved_type", "unknown"));
                str vt = py_to_string(dict_get_node(val_node, "resolved_type", "unknown"));
                return dict<str, object>{{"kind", make_object("DictComp")}, {"source_span", make_object(_sh_span(ln_no, col, col + py_len(raw)))}, {"resolved_type", make_object("dict[" + kt + "," + vt + "]")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(txt)}, {"key", make_object(key_node)}, {"value", make_object(val_node)}, {"generators", make_object(list<dict<str, object>>{dict<str, object>{{"target", make_object(target_node)}, {"iter", make_object(iter_node)}, {"ifs", make_object(if_nodes)}, {"is_async", make_object(false)}}})}};
            }
        }
        
        // set-comp support: {x for x in it} / {x for a, b in it if cond}
        if ((py_startswith(txt, "{")) && (py_endswith(txt, "}")) && (!py_contains(txt, ":"))) {
            auto inner = py_strip(py_slice(txt, 1, -1));
            int64 p_for = _sh_split_top_keyword(inner, "for");
            if (p_for > 0) {
                auto elt_txt = py_strip(py_slice(inner, 0, p_for));
                auto tail = py_strip(py_slice(inner, p_for + 3, py_len(inner)));
                int64 p_in = _sh_split_top_keyword(tail, "in");
                if (p_in <= 0)
                    throw _make_east_build_error("unsupported_syntax", "invalid set comprehension in self_hosted parser: " + py_to_string(txt), _sh_span(ln_no, col, col + py_len(raw)), "Use `{elem for item in iterable}` form.");
                auto tgt_txt = py_strip(py_slice(tail, 0, p_in));
                auto iter_and_if_txt = py_strip(py_slice(tail, p_in + 2, py_len(tail)));
                p_if = _sh_split_top_keyword(iter_and_if_txt, "if");
                object iter_txt;
                str if_txt;
                if (p_if >= 0) {
                    iter_txt = make_object(py_strip(py_slice(iter_and_if_txt, 0, p_if)));
                    if_txt = py_strip(py_slice(iter_and_if_txt, p_if + 2, py_len(iter_and_if_txt)));
                } else {
                    iter_txt = make_object(iter_and_if_txt);
                    if_txt = "";
                }
                dict<str, object> iter_node = _sh_parse_expr_lowered(py_to_string(iter_txt), ln_no, col + txt.find(iter_txt), name_types);
                dict<str, object> target_node = _sh_parse_expr_lowered(tgt_txt, ln_no, col + txt.find(tgt_txt), name_types);
                auto comp_types = _sh_bind_comp_target_types(name_types, target_node, iter_node);
                dict<str, object> elt_node = _sh_parse_expr_lowered(elt_txt, ln_no, col + txt.find(elt_txt), comp_types);
                list<dict<str, object>> if_nodes = list<dict<str, object>>{};
                if (if_txt != "")
                    if_nodes.append(dict<str, object>(_sh_parse_expr_lowered(if_txt, ln_no, col + txt.find(if_txt), comp_types)));
                return dict<str, object>{{"kind", make_object("SetComp")}, {"source_span", make_object(_sh_span(ln_no, col, col + py_len(raw)))}, {"resolved_type", make_object("set[" + py_to_string(dict_get_node(elt_node, "resolved_type", "unknown")) + "]")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(txt)}, {"elt", make_object(elt_node)}, {"generators", make_object(list<dict<str, object>>{dict<str, object>{{"target", make_object(target_node)}, {"iter", make_object(iter_node)}, {"ifs", make_object(if_nodes)}, {"is_async", make_object(false)}}})}};
            }
        }
        
        // dict literal: {"a": 1, "b": 2}
        if ((py_startswith(txt, "{")) && (py_endswith(txt, "}")) && (py_contains(txt, ":"))) {
            auto inner = py_strip(py_slice(txt, 1, -1));
            list<dict<str, object>> entries = list<dict<str, object>>{};
            if (inner != "") {
                for (str part : _sh_split_top_commas(inner)) {
                    if (!py_contains(part, ":"))
                        throw _make_east_build_error("unsupported_syntax", "invalid dict entry in self_hosted parser: " + part, _sh_span(ln_no, col, col + py_len(raw)), "Use `key: value` form in dict literals.");
                    auto __tuple_33 = part.split(":", 1);
                    auto ktxt = py_at(__tuple_33, 0);
                    auto vtxt = py_at(__tuple_33, 1);
                    ktxt = py_strip(ktxt);
                    vtxt = py_strip(vtxt);
                    entries.append(dict<str, object>(dict<str, dict<str, object>>{{"key", _sh_parse_expr_lowered(ktxt, ln_no, col + txt.find(ktxt), name_types)}, {"value", _sh_parse_expr_lowered(vtxt, ln_no, col + txt.find(vtxt), name_types)}}));
                }
            }
            str kt = "unknown";
            str vt = "unknown";
            if (py_len(entries) > 0) {
                dict<str, object> first_key = py_dict_get(entries[0], py_to_string("key"));
                dict<str, object> first_value = py_dict_get(entries[0], py_to_string("value"));
                kt = py_to_string(dict_get_node(first_key, "resolved_type", "unknown"));
                vt = py_to_string(dict_get_node(first_value, "resolved_type", "unknown"));
            }
            return dict<str, object>{{"kind", make_object("Dict")}, {"source_span", make_object(_sh_span(ln_no, col, col + py_len(raw)))}, {"resolved_type", make_object("dict[" + kt + "," + vt + "]")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(txt)}, {"entries", make_object(entries)}};
        }
        
        // list-comp support: [expr for target in iter if cond]
        if ((py_startswith(txt, "[")) && (py_endswith(txt, "]"))) {
            auto inner = py_strip(py_slice(txt, 1, -1));
            int64 p_for = _sh_split_top_keyword(inner, "for");
            if (p_for > 0) {
                auto elt_txt = py_strip(py_slice(inner, 0, p_for));
                auto tail = py_strip(py_slice(inner, p_for + 3, py_len(inner)));
                int64 p_in = _sh_split_top_keyword(tail, "in");
                if (p_in <= 0)
                    throw _make_east_build_error("unsupported_syntax", "invalid list comprehension in self_hosted parser: " + py_to_string(txt), _sh_span(ln_no, col, col + py_len(raw)), "Use `[elem for item in iterable]` form.");
                auto tgt_txt = py_strip(py_slice(tail, 0, p_in));
                auto iter_and_if_txt = py_strip(py_slice(tail, p_in + 2, py_len(tail)));
                p_if = _sh_split_top_keyword(iter_and_if_txt, "if");
                object iter_txt;
                str if_txt;
                if (p_if >= 0) {
                    iter_txt = make_object(py_strip(py_slice(iter_and_if_txt, 0, p_if)));
                    if_txt = py_strip(py_slice(iter_and_if_txt, p_if + 2, py_len(iter_and_if_txt)));
                } else {
                    iter_txt = make_object(iter_and_if_txt);
                    if_txt = "";
                }
                dict<str, object> target_node = _sh_parse_expr_lowered(tgt_txt, ln_no, col + txt.find(tgt_txt), name_types);
                dict<str, object> iter_node = _sh_parse_expr_lowered(py_to_string(iter_txt), ln_no, col + txt.find(iter_txt), name_types);
                if ((py_is_dict(iter_node)) && (py_dict_get_maybe(iter_node, "kind") == "Call") && (py_is_dict(py_dict_get_maybe(iter_node, "func"))) && (py_dict_get_maybe(dict_get_node(iter_node, "func", dict<str, object>{}), "kind") == "Name") && (py_dict_get_maybe(dict_get_node(iter_node, "func", dict<str, object>{}), "id") == "range")) {
                    list<object> rargs = dict_get_node(iter_node, "args", list<object>{});
                    dict<str, str> start_node;
                    object stop_node;
                    dict<str, str> step_node;
                    if (py_len(rargs) == 1) {
                        start_node = dict<str, object>{{"kind", make_object("Constant")}, {"source_span", make_object(_sh_span(ln_no, col, col))}, {"resolved_type", make_object("int64")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object("0")}, {"value", make_object(0)}};
                        stop_node = make_object(rargs[0]);
                        step_node = dict<str, object>{{"kind", make_object("Constant")}, {"source_span", make_object(_sh_span(ln_no, col, col))}, {"resolved_type", make_object("int64")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object("1")}, {"value", make_object(1)}};
                    } else {
                        if (py_len(rargs) == 2) {
                            start_node = rargs[0];
                            stop_node = make_object(rargs[1]);
                            step_node = dict<str, object>{{"kind", make_object("Constant")}, {"source_span", make_object(_sh_span(ln_no, col, col))}, {"resolved_type", make_object("int64")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object("1")}, {"value", make_object(1)}};
                        } else {
                            start_node = rargs[0];
                            stop_node = make_object(rargs[1]);
                            step_node = rargs[2];
                        }
                    }
                    object step_const_obj = object{};
                    if (py_is_dict(step_node))
                        step_const_obj = make_object(py_dict_get_maybe(step_node, py_to_string("value")));
                    ::std::optional<int> step_const = ::std::nullopt;
                    if (py_is_int(step_const_obj))
                        step_const = py_to_int64(step_const_obj);
                    str mode = "dynamic";
                    if (step_const == 1) {
                        mode = "ascending";
                    } else {
                        if (step_const == -1)
                            mode = "descending";
                    }
                    iter_node = dict<str, object>{{"kind", make_object("RangeExpr")}, {"source_span", make_object(py_dict_get_maybe(iter_node, "source_span"))}, {"resolved_type", make_object("range")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(dict_get_node(iter_node, "repr", "range(...)"))}, {"start", make_object(start_node)}, {"stop", make_object(stop_node)}, {"step", make_object(step_node)}, {"range_mode", make_object(mode)}};
                }
                
                auto comp_types = _sh_bind_comp_target_types(name_types, target_node, iter_node);
                dict<str, object> elt_node = _sh_parse_expr_lowered(elt_txt, ln_no, col + txt.find(elt_txt), comp_types);
                list<dict<str, object>> if_nodes = list<dict<str, object>>{};
                if (if_txt != "")
                    if_nodes.append(dict<str, object>(_sh_parse_expr_lowered(if_txt, ln_no, col + txt.find(if_txt), comp_types)));
                str elem_t = py_to_string(dict_get_node(elt_node, "resolved_type", "unknown"));
                return dict<str, object>{{"kind", make_object("ListComp")}, {"source_span", make_object(_sh_span(ln_no, col, col + py_len(raw)))}, {"resolved_type", make_object("list[" + elem_t + "]")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(txt)}, {"elt", make_object(elt_node)}, {"generators", make_object(list<dict<str, object>>{dict<str, object>{{"target", make_object(target_node)}, {"iter", make_object(iter_node)}, {"ifs", make_object(if_nodes)}, {"is_async", make_object(false)}}})}};
            }
        }
        
        // Very simple list-comp support: [x for x in <iter>]
        ::std::optional<rc<pytra::std::re::Match>> m_lc = pytra::std::re::match("^\\[\\s*([A-Za-z_][A-Za-z0-9_]*)\\s+for\\s+([A-Za-z_][A-Za-z0-9_]*)\\s+in\\s+(.+)\\]$", txt);
        if (!py_is_none(m_lc)) {
            auto elt_name = pytra::std::re::group(m_lc, 1);
            auto tgt_name = pytra::std::re::group(m_lc, 2);
            object iter_txt = make_object(pytra::std::re::strip_group(m_lc, 3));
            dict<str, object> iter_node = _sh_parse_expr_lowered(py_to_string(iter_txt), ln_no, col + txt.find(iter_txt), name_types);
            str it_t = py_to_string(dict_get_node(iter_node, "resolved_type", "unknown"));
            str elem_t = "unknown";
            if ((py_startswith(it_t, "list[")) && (py_endswith(it_t, "]")))
                elem_t = py_slice(it_t, 5, -1);
            dict<str, str> elt_node = dict<str, object>{{"kind", make_object("Name")}, {"source_span", make_object(_sh_span(ln_no, col, col + py_len(elt_name)))}, {"resolved_type", make_object((elt_name == tgt_name ? elem_t : "unknown"))}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(elt_name)}, {"id", make_object(elt_name)}};
            return dict<str, object>{{"kind", make_object("ListComp")}, {"source_span", make_object(_sh_span(ln_no, col, col + py_len(raw)))}, {"resolved_type", make_object("list[" + elem_t + "]")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(txt)}, {"elt", make_object(elt_node)}, {"generators", make_object(list<dict<str, object>>{dict<str, object>{{"target", make_object(dict<str, object>{{"kind", make_object("Name")}, {"source_span", make_object(_sh_span(ln_no, col, col + py_len(tgt_name)))}, {"resolved_type", make_object("unknown")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(tgt_name)}, {"id", make_object(tgt_name)}})}, {"iter", make_object(iter_node)}, {"ifs", make_object(list<object>{})}}})}, {"lowered_kind", make_object("ListCompSimple")}};
        }
        
        if ((py_len(txt) >= 3) && (py_at(txt, py_to_int64(0)) == "f") && (py_contains(set<str>{"'", "\""}, py_at(txt, py_to_int64(1)))) && (py_at(txt, py_to_int64(-1)) == py_at(txt, py_to_int64(1)))) {
            auto quote = py_at(txt, py_to_int64(1));
            auto inner = py_slice(txt, 2, -1);
            list<dict<str, object>> values = list<dict<str, object>>{};
            
            int64 i = 0;
            while (i < py_len(inner)) {
                auto j = inner.find("{", i);
                if (j < 0) {
                    _sh_append_fstring_literal(values, py_slice(inner, i, py_len(inner)), _sh_span(ln_no, col, col + py_len(raw)));
                    break;
                }
                if ((j + 1 < py_len(inner)) && (inner[j + 1] == "{")) {
                    _sh_append_fstring_literal(values, py_slice(inner, i, j + 1), _sh_span(ln_no, col, col + py_len(raw)));
                    i = j + 2;
                    continue;
                }
                if (j > i)
                    _sh_append_fstring_literal(values, py_slice(inner, i, j), _sh_span(ln_no, col, col + py_len(raw)));
                auto k = inner.find("}", j + 1);
                if (k < 0)
                    throw _make_east_build_error("unsupported_syntax", "unterminated f-string placeholder in self_hosted parser", _sh_span(ln_no, col, col + py_len(raw)), "Close f-string placeholder with `}`.");
                auto inner_expr = py_strip(py_slice(inner, j + 1, k));
                values.append(dict<str, object>(dict<str, object>{{"kind", make_object("FormattedValue")}, {"value", make_object(_sh_parse_expr_lowered(inner_expr, ln_no, col, name_types))}}));
                i = k + 1;
            }
            return dict<str, object>{{"kind", make_object("JoinedStr")}, {"source_span", make_object(_sh_span(ln_no, col, col + py_len(raw)))}, {"resolved_type", make_object("str")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(txt)}, {"values", make_object(values)}};
        }
        
        list<str> tuple_parts = _sh_split_top_commas(txt);
        if (py_len(tuple_parts) >= 2) {
            list<dict<str, object>> elems = [&]() -> list<dict<str, object>> {     list<dict<str, object>> __out;     for (auto p : tuple_parts) {         __out.append(_sh_parse_expr_lowered(p, ln_no, col + txt.find(p), name_types));     }     return __out; }();
            list<str> elem_ts = [&]() -> list<str> {     list<str> __out;     for (auto e : elems) {         __out.append(py_to_string(dict_get_node(e, "resolved_type", "unknown")));     }     return __out; }();
            return dict<str, object>{{"kind", make_object("Tuple")}, {"source_span", make_object(_sh_span(ln_no, col, col + py_len(raw)))}, {"resolved_type", make_object("tuple[" + str(", ").join(elem_ts) + "]")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(txt)}, {"elements", make_object(elems)}};
        }
        
        return _sh_parse_expr(txt, ln_no, col, name_types, _SH_FN_RETURNS, _SH_CLASS_METHOD_RETURNS, _SH_CLASS_BASE);
    }
    
    list<dict<str, object>> _sh_parse_stmt_block_mutable(list<::std::tuple<int64, str>>& body_lines, dict<str, str>& name_types, const str& scope_label) {
        /* インデントブロックを文単位で解析し、EAST 文リストを返す。 */
        auto __tuple_36 = _sh_merge_logical_lines(body_lines);
        body_lines = ::std::get<0>(__tuple_36);
        dict<int64, ::std::tuple<int64, int64>> merged_line_end = ::std::get<1>(__tuple_36);
        
        list<dict<str, object>> stmts = list<dict<str, object>>{};
        list<dict<str, object>> pending_leading_trivia = list<dict<str, object>>{};
        int64 pending_blank_count = 0;
        
        int64 i = 0;
        while (i < py_len(body_lines)) {
            auto __tuple_37 = body_lines[i];
            int64 ln_no = ::std::get<0>(__tuple_37);
            str ln_txt = ::std::get<1>(__tuple_37);
            int64 indent = py_len(ln_txt) - py_len(py_lstrip(ln_txt, " "));
            auto raw_s = py_strip(ln_txt);
            str s = _sh_strip_inline_comment(raw_s);
            
            if (raw_s == "") {
                pending_blank_count++;
                i++;
                continue;
            }
            if (py_startswith(raw_s, "#")) {
                if (pending_blank_count > 0) {
                    pending_leading_trivia.append(dict<str, object>(dict<str, object>{{"kind", make_object("blank")}, {"count", make_object(pending_blank_count)}}));
                    pending_blank_count = 0;
                }
                auto text = py_slice(raw_s, 1, py_len(raw_s));
                if (py_startswith(text, " "))
                    text = py_slice(text, 1, py_len(text));
                pending_leading_trivia.append(dict<str, object>(dict<str, str>{{"kind", "comment"}, {"text", text}}));
                i++;
                continue;
            }
            if (s == "") {
                i++;
                continue;
            }
            
            if ((py_startswith(s, "if ")) && (py_endswith(s, ":"))) {
                auto cond_txt = py_strip(py_slice(s, py_len("if "), -1));
                auto cond_col = ln_txt.find(cond_txt);
                dict<str, object> cond_expr = _sh_parse_expr_lowered(cond_txt, ln_no, cond_col, name_types);
                auto __tuple_38 = _sh_collect_indented_block(body_lines, i + 1, indent);
                list<::std::tuple<int64, str>> then_block = ::std::get<0>(__tuple_38);
                int64 j = ::std::get<1>(__tuple_38);
                if (py_len(then_block) == 0)
                    throw _make_east_build_error("unsupported_syntax", "if body is missing in '" + scope_label + "'", _sh_span(ln_no, 0, py_len(ln_txt)), "Add indented if-body.");
                auto __tuple_39 = _sh_parse_if_tail(j, indent, body_lines, name_types, scope_label);
                list<dict<str, object>> else_stmt_list = ::std::get<0>(__tuple_39);
                j = ::std::get<1>(__tuple_39);
                pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, dict<str, object>{{"kind", make_object("If")}, {"source_span", make_object(_sh_block_end_span(body_lines, ln_no, ln_txt.find("if "), py_len(ln_txt), j))}, {"test", make_object(cond_expr)}, {"body", make_object(_sh_parse_stmt_block(then_block, name_types, scope_label))}, {"orelse", make_object(else_stmt_list)}});
                i = j;
                continue;
            }
            
            if ((py_startswith(s, "for ")) && (py_endswith(s, ":"))) {
                auto for_head = py_strip(py_slice(s, py_len("for "), -1));
                ::std::optional<::std::tuple<str, str>> split_for = _sh_split_top_level_in(for_head);
                if (py_is_none(split_for))
                    throw _make_east_build_error("unsupported_syntax", "self_hosted parser cannot parse for statement: " + s, _sh_span(ln_no, 0, py_len(ln_txt)), "Use `for target in iterable:` form.");
                auto __tuple_40 = *(split_for);
                str tgt_txt = ::std::get<0>(__tuple_40);
                str iter_txt = ::std::get<1>(__tuple_40);
                auto tgt_col = ln_txt.find(tgt_txt);
                auto iter_col = ln_txt.find(iter_txt);
                dict<str, object> target_expr = _sh_parse_expr_lowered(tgt_txt, ln_no, tgt_col, name_types);
                dict<str, object> iter_expr = _sh_parse_expr_lowered(iter_txt, ln_no, iter_col, name_types);
                auto __tuple_41 = _sh_collect_indented_block(body_lines, i + 1, indent);
                list<::std::tuple<int64, str>> body_block = ::std::get<0>(__tuple_41);
                int64 j = ::std::get<1>(__tuple_41);
                if (py_len(body_block) == 0)
                    throw _make_east_build_error("unsupported_syntax", "for body is missing in '" + scope_label + "'", _sh_span(ln_no, 0, py_len(ln_txt)), "Add indented for-body.");
                str t_ty = "unknown";
                str i_ty = py_to_string(dict_get_node(iter_expr, "resolved_type", "unknown"));
                if ((py_startswith(i_ty, "list[")) && (py_endswith(i_ty, "]"))) {
                    t_ty = py_slice(i_ty, 5, -1);
                } else {
                    if ((py_startswith(i_ty, "tuple[")) && (py_endswith(i_ty, "]"))) {
                        t_ty = "unknown";
                    } else {
                        if ((py_startswith(i_ty, "set[")) && (py_endswith(i_ty, "]"))) {
                            t_ty = py_slice(i_ty, 4, -1);
                        } else {
                            if (i_ty == "str") {
                                t_ty = "str";
                            } else {
                                if (py_contains(set<str>{"bytes", "bytearray"}, i_ty))
                                    t_ty = "uint8";
                            }
                        }
                    }
                }
                list<str> target_names = list<str>{};
                if ((py_is_dict(target_expr)) && (py_dict_get_maybe(target_expr, "kind") == "Name")) {
                    str nm = py_to_string(dict_get_node(target_expr, "id", ""));
                    if (nm != "")
                        target_names.append(str(nm));
                } else {
                    if ((py_is_dict(target_expr)) && (py_dict_get_maybe(target_expr, "kind") == "Tuple")) {
                        object elem_nodes_obj = make_object(dict_get_node(target_expr, "elements", list<object>{}));
                        list<dict<str, object>> elem_nodes = (py_is_list(elem_nodes_obj) ? elem_nodes_obj : list<object>{});
                        for (dict<str, object> e : elem_nodes) {
                            if ((py_is_dict(e)) && (py_dict_get_maybe(e, "kind") == "Name")) {
                                str nm = py_to_string(dict_get_node(e, "id", ""));
                                if (nm != "")
                                    target_names.append(str(nm));
                            }
                        }
                    }
                }
                if (t_ty != "unknown") {
                    for (str nm : target_names)
                        name_types[py_to_string(nm)] = t_ty;
                }
                if ((py_is_dict(target_expr)) && (py_dict_get_maybe(target_expr, "kind") == "Name") && (py_is_dict(iter_expr)) && (py_dict_get_maybe(iter_expr, "kind") == "Call") && (py_is_dict(py_dict_get_maybe(iter_expr, "func"))) && (py_dict_get_maybe(dict_get_node(iter_expr, "func", dict<str, object>{}), "kind") == "Name") && (py_dict_get_maybe(dict_get_node(iter_expr, "func", dict<str, object>{}), "id") == "range")) {
                    list<object> rargs = dict_get_node(iter_expr, "args", list<object>{});
                    dict<str, object> start_node;
                    dict<str, object> stop_node;
                    dict<str, object> step_node;
                    if (py_len(rargs) == 1) {
                        start_node = dict<str, object>{{"kind", make_object("Constant")}, {"source_span", make_object(_sh_span(ln_no, ln_txt.find("range"), ln_txt.find("range") + 5))}, {"resolved_type", make_object("int64")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object("0")}, {"value", make_object(0)}};
                        stop_node = rargs[0];
                        step_node = dict<str, object>{{"kind", make_object("Constant")}, {"source_span", make_object(_sh_span(ln_no, ln_txt.find("range"), ln_txt.find("range") + 5))}, {"resolved_type", make_object("int64")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object("1")}, {"value", make_object(1)}};
                    } else {
                        if (py_len(rargs) == 2) {
                            start_node = rargs[0];
                            stop_node = rargs[1];
                            step_node = dict<str, object>{{"kind", make_object("Constant")}, {"source_span", make_object(_sh_span(ln_no, ln_txt.find("range"), ln_txt.find("range") + 5))}, {"resolved_type", make_object("int64")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object("1")}, {"value", make_object(1)}};
                        } else {
                            start_node = rargs[0];
                            stop_node = rargs[1];
                            step_node = rargs[2];
                        }
                    }
                    str tgt = py_to_string(dict_get_node(target_expr, "id", ""));
                    if (tgt != "")
                        name_types[py_to_string(tgt)] = "int64";
                    object step_const_obj = object{};
                    if (py_is_dict(step_node))
                        step_const_obj = make_object(py_dict_get_maybe(step_node, "value"));
                    ::std::optional<int> step_const = ::std::nullopt;
                    if (py_is_int(step_const_obj))
                        step_const = py_to_int64(step_const_obj);
                    str mode = "dynamic";
                    if (step_const == 1) {
                        mode = "ascending";
                    } else {
                        if (step_const == -1)
                            mode = "descending";
                    }
                    pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, dict<str, object>{{"kind", make_object("ForRange")}, {"source_span", make_object(_sh_block_end_span(body_lines, ln_no, 0, py_len(ln_txt), j))}, {"target", make_object(target_expr)}, {"target_type", make_object("int64")}, {"start", make_object(start_node)}, {"stop", make_object(stop_node)}, {"step", make_object(step_node)}, {"range_mode", make_object(mode)}, {"body", make_object(_sh_parse_stmt_block(body_block, name_types, scope_label))}, {"orelse", make_object(list<object>{})}});
                    i = j;
                    continue;
                }
                pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, dict<str, object>{{"kind", make_object("For")}, {"source_span", make_object(_sh_block_end_span(body_lines, ln_no, 0, py_len(ln_txt), j))}, {"target", make_object(target_expr)}, {"target_type", make_object(t_ty)}, {"iter", make_object(iter_expr)}, {"body", make_object(_sh_parse_stmt_block(body_block, name_types, scope_label))}, {"orelse", make_object(list<object>{})}});
                i = j;
                continue;
            }
            
            if ((py_startswith(s, "with ")) && (py_endswith(s, ":"))) {
                ::std::optional<rc<pytra::std::re::Match>> m_with = pytra::std::re::match("^with\\s+(.+)\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*$", s, pytra::std::re::S);
                if (py_is_none(m_with))
                    throw _make_east_build_error("unsupported_syntax", "self_hosted parser cannot parse with statement: " + s, _sh_span(ln_no, 0, py_len(ln_txt)), "Use `with expr as name:` form.");
                auto ctx_txt = pytra::std::re::strip_group(m_with, 1);
                auto as_name = pytra::std::re::strip_group(m_with, 2);
                auto ctx_col = ln_txt.find(ctx_txt);
                auto as_col = ln_txt.find(as_name, ctx_col + py_len(ctx_txt));
                dict<str, object> ctx_expr = _sh_parse_expr_lowered(ctx_txt, ln_no, ctx_col, name_types);
                name_types[py_to_string(as_name)] = py_to_string(dict_get_node(ctx_expr, "resolved_type", "unknown"));
                auto __tuple_42 = _sh_collect_indented_block(body_lines, i + 1, indent);
                list<::std::tuple<int64, str>> body_block = ::std::get<0>(__tuple_42);
                int64 j = ::std::get<1>(__tuple_42);
                if (py_len(body_block) == 0)
                    throw _make_east_build_error("unsupported_syntax", "with body is missing in '" + scope_label + "'", _sh_span(ln_no, 0, py_len(ln_txt)), "Add indented with-body.");
                dict<str, str> assign_stmt = dict<str, object>{{"kind", make_object("Assign")}, {"source_span", make_object(_sh_stmt_span(merged_line_end, ln_no, as_col, py_len(ln_txt)))}, {"target", make_object(dict<str, object>{{"kind", make_object("Name")}, {"source_span", make_object(_sh_span(ln_no, as_col, as_col + py_len(as_name)))}, {"resolved_type", make_object(py_to_string(dict_get_node(ctx_expr, "resolved_type", "unknown")))}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(as_name)}, {"id", make_object(as_name)}})}, {"value", make_object(ctx_expr)}, {"declare", make_object(true)}, {"declare_init", make_object(true)}, {"decl_type", make_object(py_to_string(dict_get_node(ctx_expr, "resolved_type", "unknown")))}};
                dict<str, object> close_expr = _sh_parse_expr_lowered(py_to_string(as_name) + ".close()", ln_no, as_col, name_types);
                dict<str, str> try_stmt = dict<str, object>{{"kind", make_object("Try")}, {"source_span", make_object(_sh_block_end_span(body_lines, ln_no, ln_txt.find("with "), py_len(ln_txt), j))}, {"body", make_object(_sh_parse_stmt_block(body_block, name_types, scope_label))}, {"handlers", make_object(list<object>{})}, {"orelse", make_object(list<object>{})}, {"finalbody", make_object(list<dict<str, object>>{dict<str, object>{{"kind", make_object("Expr")}, {"source_span", make_object(_sh_stmt_span(merged_line_end, ln_no, as_col, py_len(ln_txt)))}, {"value", make_object(close_expr)}}})}};
                pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, assign_stmt);
                pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, try_stmt);
                i = j;
                continue;
            }
            
            if ((py_startswith(s, "while ")) && (py_endswith(s, ":"))) {
                auto cond_txt = py_strip(py_slice(s, py_len("while "), -1));
                auto cond_col = ln_txt.find(cond_txt);
                dict<str, object> cond_expr = _sh_parse_expr_lowered(cond_txt, ln_no, cond_col, name_types);
                auto __tuple_43 = _sh_collect_indented_block(body_lines, i + 1, indent);
                list<::std::tuple<int64, str>> body_block = ::std::get<0>(__tuple_43);
                int64 j = ::std::get<1>(__tuple_43);
                if (py_len(body_block) == 0)
                    throw _make_east_build_error("unsupported_syntax", "while body is missing in '" + scope_label + "'", _sh_span(ln_no, 0, py_len(ln_txt)), "Add indented while-body.");
                pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, dict<str, object>{{"kind", make_object("While")}, {"source_span", make_object(_sh_block_end_span(body_lines, ln_no, 0, py_len(ln_txt), j))}, {"test", make_object(cond_expr)}, {"body", make_object(_sh_parse_stmt_block(body_block, name_types, scope_label))}, {"orelse", make_object(list<object>{})}});
                i = j;
                continue;
            }
            
            if (s == "try:") {
                auto __tuple_44 = _sh_collect_indented_block(body_lines, i + 1, indent);
                list<::std::tuple<int64, str>> try_body = ::std::get<0>(__tuple_44);
                int64 j = ::std::get<1>(__tuple_44);
                if (py_len(try_body) == 0)
                    throw _make_east_build_error("unsupported_syntax", "try body is missing in '" + scope_label + "'", _sh_span(ln_no, 0, py_len(ln_txt)), "Add indented try-body.");
                list<dict<str, object>> handlers = list<dict<str, object>>{};
                list<dict<str, object>> finalbody = list<dict<str, object>>{};
                while (j < py_len(body_lines)) {
                    auto __tuple_45 = body_lines[j];
                    int64 h_no = ::std::get<0>(__tuple_45);
                    str h_ln = ::std::get<1>(__tuple_45);
                    auto h_s = py_strip(h_ln);
                    int64 h_indent = py_len(h_ln) - py_len(py_lstrip(h_ln, " "));
                    if (h_indent != indent)
                        break;
                    ::std::optional<::std::tuple<str, ::std::optional<str>>> exc_clause = _sh_parse_except_clause(h_s);
                    if (!py_is_none(exc_clause)) {
                        auto __tuple_46 = *(exc_clause);
                        str ex_type_txt = ::std::get<0>(__tuple_46);
                        ::std::optional<str> ex_name = ::std::get<1>(__tuple_46);
                        auto ex_type_col = h_ln.find(ex_type_txt);
                        if (ex_type_col < 0) {
                            ex_type_col = h_ln.find("except");
                            if (ex_type_col < 0)
                                ex_type_col = 0;
                        }
                        auto __tuple_47 = _sh_collect_indented_block(body_lines, j + 1, indent);
                        list<::std::tuple<int64, str>> h_body = ::std::get<0>(__tuple_47);
                        int64 k = ::std::get<1>(__tuple_47);
                        handlers.append(dict<str, object>(dict<str, object>{{"kind", make_object("ExceptHandler")}, {"type", make_object(_sh_parse_expr_lowered(ex_type_txt, h_no, ex_type_col, name_types))}, {"name", make_object(ex_name)}, {"body", make_object(_sh_parse_stmt_block(h_body, name_types, scope_label))}}));
                        j = k;
                        continue;
                    }
                    if (h_s == "finally:") {
                        auto __tuple_48 = _sh_collect_indented_block(body_lines, j + 1, indent);
                        list<::std::tuple<int64, str>> f_body = ::std::get<0>(__tuple_48);
                        int64 k = ::std::get<1>(__tuple_48);
                        finalbody = _sh_parse_stmt_block(f_body, name_types, scope_label);
                        j = k;
                        continue;
                    }
                    break;
                }
                pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, dict<str, object>{{"kind", make_object("Try")}, {"source_span", make_object(_sh_block_end_span(body_lines, ln_no, 0, py_len(ln_txt), j))}, {"body", make_object(_sh_parse_stmt_block(try_body, name_types, scope_label))}, {"handlers", make_object(handlers)}, {"orelse", make_object(list<object>{})}, {"finalbody", make_object(finalbody)}});
                i = j;
                continue;
            }
            
            if (py_startswith(s, "raise ")) {
                auto expr_txt = py_strip(py_slice(s, py_len("raise "), py_len(s)));
                auto expr_col = ln_txt.find(expr_txt);
                object cause_expr = object{};
                ::std::optional<::std::tuple<str, str>> cause_split = _sh_split_top_level_from(expr_txt);
                if (!py_is_none(cause_split)) {
                    auto __tuple_49 = *(cause_split);
                    str exc_txt = ::std::get<0>(__tuple_49);
                    str cause_txt = ::std::get<1>(__tuple_49);
                    expr_txt = exc_txt;
                    expr_col = ln_txt.find(expr_txt);
                    auto cause_col = ln_txt.find(cause_txt);
                    cause_expr = make_object(_sh_parse_expr_lowered(cause_txt, ln_no, cause_col, name_types));
                }
                pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, dict<str, object>{{"kind", make_object("Raise")}, {"source_span", make_object(_sh_stmt_span(merged_line_end, ln_no, ln_txt.find("raise "), py_len(ln_txt)))}, {"exc", make_object(_sh_parse_expr_lowered(expr_txt, ln_no, expr_col, name_types))}, {"cause", make_object(cause_expr)}});
                i++;
                continue;
            }
            
            if (s == "pass") {
                dict<str, object> pass_stmt = dict<str, object>{{"kind", make_object("Pass")}, {"source_span", make_object(_sh_stmt_span(merged_line_end, ln_no, indent, indent + 4))}};
                pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, pass_stmt);
                i++;
                continue;
            }
            
            if (s == "return") {
                auto rcol = ln_txt.find("return");
                pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, dict<str, object>{{"kind", make_object("Return")}, {"source_span", make_object(_sh_stmt_span(merged_line_end, ln_no, rcol, py_len(ln_txt)))}, {"value", make_object(::std::nullopt)}});
                i++;
                continue;
            }
            
            if (py_startswith(s, "return ")) {
                auto rcol = ln_txt.find("return ");
                auto expr_txt = py_strip(py_slice(ln_txt, rcol + py_len("return "), py_len(ln_txt)));
                auto expr_col = ln_txt.find(expr_txt, rcol + py_len("return "));
                pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, dict<str, object>{{"kind", make_object("Return")}, {"source_span", make_object(_sh_stmt_span(merged_line_end, ln_no, rcol, py_len(ln_txt)))}, {"value", make_object(_sh_parse_expr_lowered(expr_txt, ln_no, expr_col, name_types))}});
                i++;
                continue;
            }
            
            ::std::optional<::std::tuple<str, str, str>> parsed_typed = _sh_parse_typed_binding(s, true);
            str typed_target;
            str typed_ann;
            str typed_default;
            if (!py_is_none(parsed_typed)) {
                auto __tuple_50 = *(parsed_typed);
                typed_target = ::std::get<0>(__tuple_50);
                typed_ann = ::std::get<1>(__tuple_50);
                typed_default = ::std::get<2>(__tuple_50);
            } else {
                auto __tuple_51 = ::std::make_tuple("", "", "");
                typed_target = ::std::get<0>(__tuple_51);
                typed_ann = ::std::get<1>(__tuple_51);
                typed_default = ::std::get<2>(__tuple_51);
            }
            if ((!py_is_none(parsed_typed)) && (typed_default == "")) {
                str target_txt = typed_target;
                str ann_txt = typed_ann;
                str ann = _sh_ann_to_type(ann_txt);
                auto target_col = ln_txt.find(target_txt);
                dict<str, object> target_expr = _sh_parse_expr_lowered(target_txt, ln_no, target_col, name_types);
                if ((py_is_dict(target_expr)) && (py_dict_get_maybe(target_expr, "kind") == "Name"))
                    name_types[py_to_string(py_to_string(dict_get_node(target_expr, "id", "")))] = ann;
                pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, dict<str, object>{{"kind", make_object("AnnAssign")}, {"source_span", make_object(_sh_stmt_span(merged_line_end, ln_no, target_col, py_len(ln_txt)))}, {"target", make_object(target_expr)}, {"annotation", make_object(ann)}, {"value", make_object(::std::nullopt)}, {"declare", make_object(true)}, {"decl_type", make_object(ann)}});
                i++;
                continue;
            }
            
            if ((!py_is_none(parsed_typed)) && (typed_default != "")) {
                str target_txt = typed_target;
                str ann_txt = typed_ann;
                str expr_txt = typed_default;
                str ann = _sh_ann_to_type(ann_txt);
                auto expr_col = ln_txt.find(expr_txt);
                dict<str, object> val_expr = _sh_parse_expr_lowered(expr_txt, ln_no, expr_col, name_types);
                auto target_col = ln_txt.find(target_txt);
                dict<str, object> target_expr = _sh_parse_expr_lowered(target_txt, ln_no, target_col, name_types);
                if ((py_is_dict(target_expr)) && (py_dict_get_maybe(target_expr, "kind") == "Name"))
                    name_types[py_to_string(py_to_string(dict_get_node(target_expr, "id", "")))] = ann;
                pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, dict<str, object>{{"kind", make_object("AnnAssign")}, {"source_span", make_object(_sh_stmt_span(merged_line_end, ln_no, target_col, py_len(ln_txt)))}, {"target", make_object(target_expr)}, {"annotation", make_object(ann)}, {"value", make_object(val_expr)}, {"declare", make_object(true)}, {"decl_type", make_object(ann)}});
                i++;
                continue;
            }
            
            ::std::optional<::std::tuple<str, str, str>> parsed_aug = _sh_parse_augassign(s);
            if (!py_is_none(parsed_aug)) {
                auto __tuple_52 = *(parsed_aug);
                str target_txt = ::std::get<0>(__tuple_52);
                str aug_op = ::std::get<1>(__tuple_52);
                str expr_txt = ::std::get<2>(__tuple_52);
                dict<str, str> op_map = dict<str, str>{{"+=", "Add"}, {"-=", "Sub"}, {"*=", "Mult"}, {"/=", "Div"}, {"//=", "FloorDiv"}, {"%=", "Mod"}, {"&=", "BitAnd"}, {"|=", "BitOr"}, {"^=", "BitXor"}, {"<<=", "LShift"}, {">>=", "RShift"}};
                auto expr_col = ln_txt.find(expr_txt);
                auto target_col = ln_txt.find(target_txt);
                dict<str, object> target_expr = _sh_parse_expr_lowered(target_txt, ln_no, target_col, name_types);
                dict<str, object> val_expr = _sh_parse_expr_lowered(expr_txt, ln_no, expr_col, name_types);
                str target_ty = "unknown";
                if ((py_is_dict(target_expr)) && (py_dict_get_maybe(target_expr, "kind") == "Name"))
                    target_ty = py_dict_get_default(name_types, py_to_string(py_to_string(dict_get_node(target_expr, "id", ""))), "unknown");
                ::std::optional<str> decl_type = ::std::nullopt;
                if (target_ty != "unknown")
                    decl_type = target_ty;
                pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, dict<str, object>{{"kind", make_object("AugAssign")}, {"source_span", make_object(_sh_stmt_span(merged_line_end, ln_no, target_col, py_len(ln_txt)))}, {"target", make_object(target_expr)}, {"op", make_object(py_dict_get(op_map, py_to_string(aug_op)))}, {"value", make_object(val_expr)}, {"declare", make_object(false)}, {"decl_type", make_object(decl_type)}});
                i++;
                continue;
            }
            
            ::std::optional<rc<pytra::std::re::Match>> m_tasg = pytra::std::re::match("^([A-Za-z_][A-Za-z0-9_]*)\\s*,\\s*([A-Za-z_][A-Za-z0-9_]*)\\s*=\\s*(.+)$", s);
            if (!py_is_none(m_tasg)) {
                auto n1 = pytra::std::re::group(m_tasg, 1);
                auto n2 = pytra::std::re::group(m_tasg, 2);
                str expr_txt = pytra::std::re::strip_group(m_tasg, 3);
                auto expr_col = ln_txt.find(expr_txt);
                dict<str, object> rhs = _sh_parse_expr_lowered(expr_txt, ln_no, expr_col, name_types);
                auto c1 = ln_txt.find(n1);
                auto c2 = ln_txt.find(n2, c1 + py_len(n1));
                if ((py_is_dict(rhs)) && (py_dict_get_maybe(rhs, "kind") == "Tuple") && (py_len(dict_get_node(rhs, "elements", list<object>{})) == 2) && (py_is_dict(py_at(py_dict_get_maybe(rhs, "elements"), py_to_int64(0)))) && (py_is_dict(py_at(py_dict_get_maybe(rhs, "elements"), py_to_int64(1)))) && (py_dict_get_maybe(py_at(py_dict_get_maybe(rhs, "elements"), py_to_int64(0)), "kind") == "Name") && (py_dict_get_maybe(py_at(py_dict_get_maybe(rhs, "elements"), py_to_int64(1)), "kind") == "Name") && (py_to_string(py_dict_get_default(py_at(py_dict_get_maybe(rhs, "elements"), py_to_int64(0)), "id", "")) == n2) && (py_to_string(py_dict_get_default(py_at(py_dict_get_maybe(rhs, "elements"), py_to_int64(1)), "id", "")) == n1)) {
                    pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, dict<str, object>{{"kind", make_object("Swap")}, {"source_span", make_object(_sh_stmt_span(merged_line_end, ln_no, c1, py_len(ln_txt)))}, {"left", make_object(dict<str, object>{{"kind", make_object("Name")}, {"source_span", make_object(_sh_span(ln_no, c1, c1 + py_len(n1)))}, {"resolved_type", make_object(py_dict_get_default(name_types, py_to_string(n1), "unknown"))}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(n1)}, {"id", make_object(n1)}})}, {"right", make_object(dict<str, object>{{"kind", make_object("Name")}, {"source_span", make_object(_sh_span(ln_no, c2, c2 + py_len(n2)))}, {"resolved_type", make_object(py_dict_get_default(name_types, py_to_string(n2), "unknown"))}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(n2)}, {"id", make_object(n2)}})}});
                    i++;
                    continue;
                }
                dict<str, str> target_expr = dict<str, object>{{"kind", make_object("Tuple")}, {"source_span", make_object(_sh_span(ln_no, c1, c2 + py_len(n2)))}, {"resolved_type", make_object("unknown")}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(py_to_string(n1) + ", " + py_to_string(n2))}, {"elements", make_object(list<dict<str, object>>{dict<str, object>{{"kind", make_object("Name")}, {"source_span", make_object(_sh_span(ln_no, c1, c1 + py_len(n1)))}, {"resolved_type", make_object(py_dict_get_default(name_types, py_to_string(n1), "unknown"))}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(n1)}, {"id", make_object(n1)}}, dict<str, object>{{"kind", make_object("Name")}, {"source_span", make_object(_sh_span(ln_no, c2, c2 + py_len(n2)))}, {"resolved_type", make_object(py_dict_get_default(name_types, py_to_string(n2), "unknown"))}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(n2)}, {"id", make_object(n2)}}})}};
                pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, dict<str, object>{{"kind", make_object("Assign")}, {"source_span", make_object(_sh_stmt_span(merged_line_end, ln_no, c1, py_len(ln_txt)))}, {"target", make_object(target_expr)}, {"value", make_object(rhs)}, {"declare", make_object(false)}, {"decl_type", make_object(::std::nullopt)}});
                i++;
                continue;
            }
            
            ::std::optional<::std::tuple<str, str>> asg_split = _sh_split_top_level_assign(s);
            if (!py_is_none(asg_split)) {
                auto __tuple_53 = *(asg_split);
                str target_txt = ::std::get<0>(__tuple_53);
                str expr_txt = ::std::get<1>(__tuple_53);
                auto expr_col = ln_txt.find(expr_txt);
                auto target_col = ln_txt.find(target_txt);
                dict<str, object> target_expr = _sh_parse_expr_lowered(target_txt, ln_no, target_col, name_types);
                dict<str, object> val_expr = _sh_parse_expr_lowered(expr_txt, ln_no, expr_col, name_types);
                ::std::optional<str> decl_type = dict_get_node(val_expr, "resolved_type", "unknown");
                if ((py_is_dict(target_expr)) && (py_dict_get_maybe(target_expr, "kind") == "Name")) {
                    str nm = py_to_string(dict_get_node(target_expr, "id", ""));
                    if (nm != "")
                        name_types[py_to_string(nm)] = py_to_string(decl_type);
                }
                pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, dict<str, object>{{"kind", make_object("Assign")}, {"source_span", make_object(_sh_stmt_span(merged_line_end, ln_no, target_col, py_len(ln_txt)))}, {"target", make_object(target_expr)}, {"value", make_object(val_expr)}, {"declare", make_object(true)}, {"declare_init", make_object(true)}, {"decl_type", make_object(decl_type)}});
                i++;
                continue;
            }
            
            int64 expr_col = py_len(ln_txt) - py_len(py_lstrip(ln_txt, " "));
            dict<str, object> expr_stmt = _sh_parse_expr_lowered(s, ln_no, expr_col, name_types);
            pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, dict<str, object>{{"kind", make_object("Expr")}, {"source_span", make_object(_sh_stmt_span(merged_line_end, ln_no, expr_col, py_len(ln_txt)))}, {"value", make_object(expr_stmt)}});
            i++;
        }
        return stmts;
    }
    
    list<dict<str, object>> _sh_parse_stmt_block(const list<::std::tuple<int64, str>>& body_lines, const dict<str, str>& name_types, const str& scope_label) {
        /* 読み取り専用引数で受け取り、mutable 実体へコピーを渡す。 */
        list<::std::tuple<int64, str>> body_lines_copy = body_lines;
        dict<str, str> name_types_copy = name_types;
        return _sh_parse_stmt_block_mutable(body_lines_copy, name_types_copy, scope_label);
    }
    
    dict<str, object> convert_source_to_east_self_hosted(const str& source, const str& filename) {
        /* Python ソースを self-hosted パーサで EAST Module に変換する。 */
        auto lines = source.splitlines();
        list<str> leading_file_comments = list<str>{};
        list<dict<str, object>> leading_file_trivia = list<dict<str, object>>{};
        for (::std::any ln : lines) {
            auto s = py_strip(ln);
            if (s == "") {
                if (py_len(leading_file_comments) > 0)
                    leading_file_trivia.append(dict<str, object>(dict<str, object>{{"kind", make_object("blank")}, {"count", make_object(1)}}));
                continue;
            }
            if (py_startswith(s, "#")) {
                auto text = py_lstrip(py_slice(s, 1, py_len(s)));
                leading_file_comments.append(str(text));
                leading_file_trivia.append(dict<str, object>(dict<str, str>{{"kind", "comment"}, {"text", text}}));
                continue;
            }
            break;
        }
        
        dict<str, dict<str, str>> class_method_return_types = dict<str, dict<str, str>>{};
        dict<str, ::std::optional<str>> class_base = dict<str, ::std::optional<str>>{};
        dict<str, str> fn_returns = dict<str, str>{};
        
        ::std::optional<str> cur_cls = ::std::nullopt;
        int64 cur_cls_indent = 0;
        for (auto __it_54 : py_enumerate(lines)) {
            auto ln_no = ::std::get<0>(__it_54);
            auto ln = ::std::get<1>(__it_54);
            auto s = py_strip(ln);
            if (s == "")
                continue;
            int64 indent = py_len(ln) - py_len(py_lstrip(ln, " "));
            if ((!py_is_none(cur_cls)) && (indent <= cur_cls_indent) && (!(py_startswith(s, "#"))))
                cur_cls = ::std::nullopt;
            ::std::optional<::std::tuple<str, str>> cls_hdr = _sh_parse_class_header(py_to_string(ln));
            if (!py_is_none(cls_hdr)) {
                auto __tuple_55 = *(cls_hdr);
                str cur_cls_name = ::std::get<0>(__tuple_55);
                str cur_base = ::std::get<1>(__tuple_55);
                cur_cls = cur_cls_name;
                cur_cls_indent = indent;
                if (cur_base != "")
                    class_base[py_to_string(cur_cls_name)] = cur_base;
                else
                    class_base[py_to_string(cur_cls_name)] = ::std::nullopt;
                if (!py_contains(class_method_return_types, cur_cls_name)) {
                    dict<str, str> empty_methods = dict<str, str>{};
                    class_method_return_types[py_to_string(cur_cls_name)] = empty_methods;
                }
                continue;
            }
            if (py_is_none(cur_cls)) {
                auto sig = _sh_parse_def_sig(ln_no, py_to_string(ln));
                if (!py_is_none(sig))
                    fn_returns[py_to_string(py_to_string(py_dict_get(sig, "name")))] = py_to_string(py_dict_get(sig, "ret"));
                continue;
            }
            str cur_cls_name = (cur_cls).value();
            auto sig = _sh_parse_def_sig(ln_no, py_to_string(ln), cur_cls_name);
            if (!py_is_none(sig)) {
                dict<str, str> methods = py_dict_get(class_method_return_types, py_to_string(cur_cls_name));
                methods[py_to_string(py_to_string(py_dict_get(sig, "name")))] = py_to_string(py_dict_get(sig, "ret"));
                class_method_return_types[py_to_string(cur_cls_name)] = methods;
            }
        }
        
        _sh_set_parse_context(fn_returns, class_method_return_types, class_base);
        
        list<dict<str, object>> body_items = list<dict<str, object>>{};
        list<dict<str, object>> main_stmts = list<dict<str, object>>{};
        dict<str, str> import_module_bindings = dict<str, str>{};
        dict<str, dict<str, str>> import_symbol_bindings = dict<str, dict<str, str>>{};
        list<dict<str, object>> import_bindings = list<dict<str, object>>{};
        set<str> import_binding_names = set<str>{};
        bool first_item_attached = false;
        bool pending_dataclass = false;
        
        list<::std::tuple<int64, str>> top_lines = list<::std::tuple<int64, str>>{};
        int64 line_idx = 1;
        while (line_idx <= py_len(lines)) {
            top_lines.append(::std::tuple<int64, str>(::std::make_tuple(line_idx, py_at(lines, py_to_int64(line_idx - 1)))));
            line_idx++;
        }
        auto __tuple_56 = _sh_merge_logical_lines(top_lines);
        list<::std::tuple<int64, str>> top_merged_lines = ::std::get<0>(__tuple_56);
        dict<int64, ::std::tuple<int64, int64>> top_merged_end = ::std::get<1>(__tuple_56);
        dict<int64, str> top_merged_map = dict<int64, str>{};
        for (auto __it_57 : top_merged_lines) {
            auto top_ln_no = ::std::get<0>(__it_57);
            auto top_txt = ::std::get<1>(__it_57);
            top_merged_map[int64(py_to_int64(py_to_int64(top_ln_no)))] = py_to_string(top_txt);
        }
        int64 i = 1;
        while (i <= py_len(lines)) {
            auto ln_obj = py_dict_get_default(top_merged_map, int64(py_to_int64(i)), py_at(lines, py_to_int64(i - 1)));
            str ln = py_to_string(ln_obj);
            auto logical_end_pair = py_dict_get_default(top_merged_end, int64(py_to_int64(i)), ::std::make_tuple(i, py_len(py_at(lines, py_to_int64(i - 1)))));
            int64 logical_end = py_to_int64(py_at(logical_end_pair, py_to_int64(0)));
            auto s = py_strip(ln);
            if ((s == "") || (py_startswith(s, "#"))) {
                i++;
                continue;
            }
            if (py_startswith(ln, " ")) {
                i++;
                continue;
            }
            
            auto ln_main = py_strip(ln);
            bool is_main_guard = false;
            if ((py_startswith(ln_main, "if ")) && (py_endswith(ln_main, ":"))) {
                auto cond = py_strip(py_slice(ln_main, 3, -1));
                if (py_contains(set<str>{"__name__ == \"__main__\"", "__name__ == '__main__'", "\"__main__\" == __name__", "'__main__' == __name__"}, cond))
                    is_main_guard = true;
            }
            if (is_main_guard) {
                list<::std::tuple<int64, str>> block = list<::std::tuple<int64, str>>{};
                int64 j = i + 1;
                while (j <= py_len(lines)) {
                    auto bl = py_at(lines, py_to_int64(j - 1));
                    if (py_strip(bl) == "") {
                        block.append(::std::tuple<int64, str>(::std::make_tuple(j, bl)));
                        j++;
                        continue;
                    }
                    if (!(py_startswith(bl, " ")))
                        break;
                    block.append(::std::tuple<int64, str>(::std::make_tuple(j, bl)));
                    j++;
                }
                dict<str, str> main_name_types = dict<str, str>{};
                main_stmts = _sh_parse_stmt_block(block, main_name_types, "__main__");
                i = j;
                continue;
            }
            str sig_line = ln;
            int64 sig_end_line = logical_end;
            auto sig = _sh_parse_def_sig(i, sig_line);
            if (!py_is_none(sig)) {
                str fn_name = py_to_string(py_dict_get(sig, "name"));
                str fn_ret = py_to_string(py_dict_get(sig, "ret"));
                dict<str, str> arg_types = py_dict_get(sig, "arg_types");
                list<str> arg_order = py_dict_get(sig, "arg_order");
                object arg_defaults_raw_obj = make_object(py_dict_get_maybe(sig, "arg_defaults"));
                dict<str, object> arg_defaults_raw = (py_is_dict(arg_defaults_raw_obj) ? arg_defaults_raw_obj : dict<str, object>{});
                list<::std::tuple<int64, str>> block = list<::std::tuple<int64, str>>{};
                int64 j = sig_end_line + 1;
                while (j <= py_len(lines)) {
                    auto bl = py_at(lines, py_to_int64(j - 1));
                    if (py_strip(bl) == "") {
                        block.append(::std::tuple<int64, str>(::std::make_tuple(j, bl)));
                        j++;
                        continue;
                    }
                    if (!(py_startswith(bl, " ")))
                        break;
                    block.append(::std::tuple<int64, str>(::std::make_tuple(j, bl)));
                    j++;
                }
                if (py_len(block) == 0)
                    throw _make_east_build_error("unsupported_syntax", "self_hosted parser requires non-empty function body '" + fn_name + "'", _sh_span(i, 0, py_len(sig_line)), "Add return or assignment statements in function body.");
                list<dict<str, object>> stmts = _sh_parse_stmt_block(block, arg_types, fn_name);
                auto __tuple_58 = _sh_extract_leading_docstring(stmts);
                ::std::optional<str> docstring = ::std::get<0>(__tuple_58);
                stmts = ::std::get<1>(__tuple_58);
                dict<str, object> arg_defaults = dict<str, object>{};
                dict<str, int64> arg_index_map = dict<str, int64>{};
                for (auto __it_59 : py_enumerate(arg_order)) {
                    auto arg_pos = ::std::get<0>(__it_59);
                    auto arg_name = ::std::get<1>(__it_59);
                    arg_index_map[py_to_string(arg_name)] = py_to_int64(arg_pos);
                }
                dict<str, str> arg_usage_map = dict<str, str>{};
                for (::std::any arg_name : py_dict_keys(arg_types))
                    arg_usage_map[py_to_string(arg_name)] = "readonly";
                for (str arg_name : arg_order) {
                    if (py_contains(arg_defaults_raw, arg_name)) {
                        object default_obj = make_object(py_dict_get(arg_defaults_raw, py_to_string(arg_name)));
                        str default_txt = py_strip(py_to_string(default_obj));
                        if (default_txt != "") {
                            auto default_col = sig_line.find(default_txt);
                            if (default_col < 0)
                                default_col = 0;
                            arg_defaults[py_to_string(arg_name)] = make_object(_sh_parse_expr_lowered(default_txt, i, default_col, arg_types));
                        }
                    }
                }
                dict<str, object> item = dict<str, object>{{"kind", make_object("FunctionDef")}, {"name", make_object(fn_name)}, {"original_name", make_object(fn_name)}, {"source_span", make_object(dict<str, int64>{{"lineno", i}, {"col", 0}, {"end_lineno", ::std::get<0>(py_at(block, -1))}, {"end_col", py_len(::std::get<1>(py_at(block, -1)))}})}, {"arg_types", make_object(arg_types)}, {"arg_order", make_object(arg_order)}, {"arg_defaults", make_object(arg_defaults)}, {"arg_index", make_object(arg_index_map)}, {"return_type", make_object(fn_ret)}, {"arg_usage", make_object(arg_usage_map)}, {"renamed_symbols", make_object(dict<str, object>{})}, {"leading_comments", make_object(list<object>{})}, {"leading_trivia", make_object(list<object>{})}, {"docstring", make_object(docstring)}, {"body", make_object(stmts)}};
                if (!(first_item_attached)) {
                    item[py_to_string("leading_comments")] = make_object(leading_file_comments);
                    item[py_to_string("leading_trivia")] = make_object(leading_file_trivia);
                    first_item_attached = true;
                }
                body_items.append(dict<str, object>(item));
                i = j;
                continue;
            }
            
            if (s == "@dataclass") {
                pending_dataclass = true;
                i++;
                continue;
            }
            ::std::optional<rc<pytra::std::re::Match>> m_import = pytra::std::re::match("^import\\s+(.+)$", s, pytra::std::re::S);
            if (!py_is_none(m_import)) {
                auto names_txt = pytra::std::re::strip_group(m_import, 1);
                list<str> raw_parts = list<str>{};
                for (::std::any p : names_txt.split(",")) {
                    str p2 = py_strip(p);
                    if (p2 != "")
                        raw_parts.append(str(p2));
                }
                if (py_len(raw_parts) == 0)
                    throw _make_east_build_error("unsupported_syntax", "import statement has no module names", _sh_span(i, 0, py_len(ln)), "Use `import module` or `import module as alias`.");
                list<dict<str, ::std::optional<str>>> aliases = list<dict<str, ::std::optional<str>>>{};
                for (str part : raw_parts) {
                    ::std::optional<::std::tuple<str, str>> parsed_alias = _sh_parse_import_alias(part, true);
                    if (py_is_none(parsed_alias))
                        throw _make_east_build_error("unsupported_syntax", "unsupported import clause: " + part, _sh_span(i, 0, py_len(ln)), "Use `import module` or `import module as alias` form.");
                    auto __tuple_60 = *(parsed_alias);
                    str mod_name = ::std::get<0>(__tuple_60);
                    str as_name_txt = ::std::get<1>(__tuple_60);
                    auto bind_name = (as_name_txt != "" ? as_name_txt : py_at(mod_name.split("."), py_to_int64(0)));
                    _sh_append_import_binding(import_bindings, import_binding_names, mod_name, "", bind_name, "module", filename, i);
                    dict<str, ::std::optional<str>> alias_item = dict<str, object>{{"name", make_object(mod_name)}, {"asname", make_object(::std::nullopt)}};
                    if (as_name_txt != "")
                        alias_item[py_to_string("asname")] = as_name_txt;
                    aliases.append(dict<str, ::std::optional<str>>(alias_item));
                }
                body_items.append(dict<str, object>(dict<str, object>{{"kind", make_object("Import")}, {"source_span", make_object(_sh_span(i, 0, py_len(ln)))}, {"names", make_object(aliases)}}));
                i = logical_end + 1;
                continue;
            }
            if (py_startswith(s, "from ")) {
                str marker = " import ";
                auto pos = s.find(marker);
                if (pos >= 0) {
                    auto mod_txt = py_strip(py_slice(s, 5, pos));
                    if (py_startswith(mod_txt, "."))
                        throw _make_east_build_error("unsupported_syntax", "relative import is not supported", _sh_span(i, 0, py_len(ln)), "Use absolute import form: `from module import name`.");
                }
            }
            ::std::optional<rc<pytra::std::re::Match>> m_import_from = pytra::std::re::match("^from\\s+([A-Za-z_][A-Za-z0-9_\\.]*)\\s+import\\s+(.+)$", s, pytra::std::re::S);
            if (!py_is_none(m_import_from)) {
                str mod_name = pytra::std::re::strip_group(m_import_from, 1);
                auto names_txt = pytra::std::re::strip_group(m_import_from, 2);
                if (names_txt == "*")
                    throw _make_east_build_error("unsupported_syntax", "from-import wildcard is not supported", _sh_span(i, 0, py_len(ln)), "Import explicit symbol names instead of '*'.");
                list<str> raw_parts = list<str>{};
                for (::std::any p : names_txt.split(",")) {
                    str p2 = py_strip(p);
                    if (p2 != "")
                        raw_parts.append(str(p2));
                }
                if (py_len(raw_parts) == 0)
                    throw _make_east_build_error("unsupported_syntax", "from-import statement has no symbol names", _sh_span(i, 0, py_len(ln)), "Use `from module import name` form.");
                list<dict<str, ::std::optional<str>>> aliases = list<dict<str, ::std::optional<str>>>{};
                for (str part : raw_parts) {
                    ::std::optional<::std::tuple<str, str>> parsed_alias = _sh_parse_import_alias(part, false);
                    if (py_is_none(parsed_alias))
                        throw _make_east_build_error("unsupported_syntax", "unsupported from-import clause: " + part, _sh_span(i, 0, py_len(ln)), "Use `from module import name` or `... as alias`.");
                    auto __tuple_61 = *(parsed_alias);
                    str sym_name = ::std::get<0>(__tuple_61);
                    str as_name_txt = ::std::get<1>(__tuple_61);
                    auto bind_name = (as_name_txt != "" ? as_name_txt : sym_name);
                    // `Enum/IntEnum/IntFlag` は class 定義の lowering で吸収されるため、
                    // 依存ヘッダ解決用の ImportBinding には積まない。
                    if (!((mod_name == "pytra.std.enum") && (py_contains(set<str>{"Enum", "IntEnum", "IntFlag"}, sym_name))))
                        _sh_append_import_binding(import_bindings, import_binding_names, mod_name, sym_name, bind_name, "symbol", filename, i);
                    dict<str, ::std::optional<str>> alias_item = dict<str, object>{{"name", make_object(sym_name)}, {"asname", make_object(::std::nullopt)}};
                    if (as_name_txt != "")
                        alias_item[py_to_string("asname")] = as_name_txt;
                    aliases.append(dict<str, ::std::optional<str>>(alias_item));
                }
                body_items.append(dict<str, object>(dict<str, object>{{"kind", make_object("ImportFrom")}, {"source_span", make_object(_sh_span(i, 0, py_len(ln)))}, {"module", make_object(mod_name)}, {"names", make_object(aliases)}, {"level", make_object(0)}}));
                i = logical_end + 1;
                continue;
            }
            if (py_startswith(s, "@")) {
                i++;
                continue;
            }
            
            ::std::optional<::std::tuple<str, str>> cls_hdr = _sh_parse_class_header(ln);
            if (!py_is_none(cls_hdr)) {
                auto __tuple_62 = *(cls_hdr);
                str cls_name = ::std::get<0>(__tuple_62);
                str base = ::std::get<1>(__tuple_62);
                str base_name = base;
                bool is_enum_base = py_contains(set<str>{"Enum", "IntEnum", "IntFlag"}, base_name);
                int64 cls_indent = py_len(ln) - py_len(py_lstrip(ln, " "));
                list<::std::tuple<int64, str>> block = list<::std::tuple<int64, str>>{};
                int64 j = i + 1;
                while (j <= py_len(lines)) {
                    auto bl = py_at(lines, py_to_int64(j - 1));
                    if (py_strip(bl) == "") {
                        block.append(::std::tuple<int64, str>(::std::make_tuple(j, bl)));
                        j++;
                        continue;
                    }
                    int64 bind = py_len(bl) - py_len(py_lstrip(bl, " "));
                    if (bind <= cls_indent)
                        break;
                    block.append(::std::tuple<int64, str>(::std::make_tuple(j, bl)));
                    j++;
                }
                if (py_len(block) == 0)
                    throw _make_east_build_error("unsupported_syntax", "self_hosted parser requires non-empty class body '" + cls_name + "'", _sh_span(i, 0, py_len(ln)), "Add field or method definitions.");
                auto __tuple_63 = _sh_merge_logical_lines(block);
                list<::std::tuple<int64, str>> class_block = ::std::get<0>(__tuple_63);
                dict<int64, ::std::tuple<int64, int64>> _class_line_end = ::std::get<1>(__tuple_63);
                
                dict<str, str> field_types = dict<str, str>{};
                list<dict<str, object>> class_body = list<dict<str, object>>{};
                list<str> pending_method_decorators = list<str>{};
                str class_storage_hint_override = "";
                int64 k = 0;
                while (k < py_len(class_block)) {
                    auto __tuple_64 = class_block[k];
                    auto ln_no_raw = py_at(__tuple_64, 0);
                    auto ln_txt_raw = py_at(__tuple_64, 1);
                    int64 ln_no = py_to_int64(ln_no_raw);
                    str ln_txt = py_to_string(ln_txt_raw);
                    auto s2 = py_strip(pytra::std::re::sub("\\s+#.*$", "", ln_txt));
                    int64 bind = py_len(ln_txt) - py_len(py_lstrip(ln_txt, " "));
                    if (s2 == "") {
                        k++;
                        continue;
                    }
                    if ((bind == cls_indent + 4) && (py_startswith(s2, "@"))) {
                        auto dec_name = py_strip(py_slice(s2, 1, py_len(s2)));
                        if (dec_name != "")
                            pending_method_decorators.append(str(dec_name));
                        k++;
                        continue;
                    }
                    if ((bind == cls_indent + 4) && ((py_startswith(s2, "\"\"\"")) || (py_startswith(s2, "'''")))) {
                        auto q = py_slice(s2, 0, 3);
                        if ((s2.count(q) >= 2) && (py_len(s2) > 3)) {
                            k++;
                            continue;
                        }
                        k++;
                        while (k < py_len(class_block)) {
                            auto __tuple_65 = class_block[k];
                            auto _doc_no = py_at(__tuple_65, 0);
                            auto doc_txt = py_at(__tuple_65, 1);
                            if (py_contains(doc_txt, q)) {
                                k++;
                                break;
                            }
                            k++;
                        }
                        continue;
                    }
                    if (bind == cls_indent + 4) {
                        if ((py_startswith(s2, "__pytra_class_storage_hint__")) || (py_startswith(s2, "__pytra_storage_hint__"))) {
                            auto parts = s2.split("=", 1);
                            if (py_len(parts) == 2) {
                                auto rhs = py_strip(py_at(parts, py_to_int64(1)));
                                if (py_contains(set<str>{"\"value\"", "'value'"}, rhs)) {
                                    class_storage_hint_override = "value";
                                    k++;
                                    continue;
                                }
                                if (py_contains(set<str>{"\"ref\"", "'ref'"}, rhs)) {
                                    class_storage_hint_override = "ref";
                                    k++;
                                    continue;
                                }
                            }
                        }
                        ::std::optional<::std::tuple<str, str, str>> parsed_field = _sh_parse_typed_binding(s2, false);
                        if (!py_is_none(parsed_field)) {
                            auto __tuple_66 = *(parsed_field);
                            str fname = ::std::get<0>(__tuple_66);
                            str fty_txt = ::std::get<1>(__tuple_66);
                            str fdefault = ::std::get<2>(__tuple_66);
                            str fty = _sh_ann_to_type(fty_txt);
                            field_types[py_to_string(fname)] = fty;
                            ::std::optional<dict<str, object>> val_node = ::std::nullopt;
                            if (fdefault != "") {
                                auto fexpr_txt = py_strip(fdefault);
                                auto fexpr_col = ln_txt.find(fexpr_txt);
                                val_node = _sh_parse_expr_lowered(fexpr_txt, ln_no, fexpr_col, dict<str, object>{});
                            }
                            class_body.append(dict<str, object>(dict<str, object>{{"kind", make_object("AnnAssign")}, {"source_span", make_object(_sh_span(ln_no, ln_txt.find(fname), py_len(ln_txt)))}, {"target", make_object(dict<str, object>{{"kind", make_object("Name")}, {"source_span", make_object(_sh_span(ln_no, ln_txt.find(fname), ln_txt.find(fname) + py_len(fname)))}, {"resolved_type", make_object(fty)}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(fname)}, {"id", make_object(fname)}})}, {"annotation", make_object(fty)}, {"value", make_object(val_node)}, {"declare", make_object(true)}, {"decl_type", make_object(fty)}}));
                            k++;
                            continue;
                        }
                        if (is_enum_base) {
                            ::std::optional<::std::tuple<str, str>> enum_assign = _sh_split_top_level_assign(s2);
                            if (!py_is_none(enum_assign)) {
                                auto __tuple_67 = *(enum_assign);
                                str fname = ::std::get<0>(__tuple_67);
                                str fexpr_txt = ::std::get<1>(__tuple_67);
                                fname = py_strip(fname);
                                fexpr_txt = py_strip(fexpr_txt);
                                if ((!(_sh_is_identifier(fname))) || (fexpr_txt == "")) {
                                    k++;
                                    continue;
                                }
                                auto name_col = ln_txt.find(fname);
                                if (name_col < 0)
                                    name_col = 0;
                                auto expr_col = ln_txt.find(fexpr_txt, name_col + py_len(fname));
                                if (expr_col < 0)
                                    expr_col = name_col + py_len(fname) + 1;
                                dict<str, object> val_node = _sh_parse_expr_lowered(fexpr_txt, ln_no, expr_col, dict<str, object>{});
                                class_body.append(dict<str, object>(dict<str, object>{{"kind", make_object("Assign")}, {"source_span", make_object(_sh_span(ln_no, name_col, py_len(ln_txt)))}, {"target", make_object(dict<str, object>{{"kind", make_object("Name")}, {"source_span", make_object(_sh_span(ln_no, name_col, name_col + py_len(fname)))}, {"resolved_type", make_object(py_to_string(dict_get_node(val_node, "resolved_type", "unknown")))}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(fname)}, {"id", make_object(fname)}})}, {"value", make_object(val_node)}, {"declare", make_object(true)}, {"declare_init", make_object(true)}, {"decl_type", make_object(py_to_string(dict_get_node(val_node, "resolved_type", "unknown")))}}));
                                k++;
                                continue;
                            }
                        }
                        sig = _sh_parse_def_sig(ln_no, ln_txt, cls_name);
                        if (!py_is_none(sig)) {
                            str mname = py_to_string(py_dict_get(sig, "name"));
                            dict<str, str> marg_types = py_dict_get(sig, "arg_types");
                            list<str> marg_order = py_dict_get(sig, "arg_order");
                            object marg_defaults_raw_obj = make_object(py_dict_get_maybe(sig, "arg_defaults"));
                            dict<str, object> marg_defaults_raw = (py_is_dict(marg_defaults_raw_obj) ? marg_defaults_raw_obj : dict<str, object>{});
                            str mret = py_to_string(py_dict_get(sig, "ret"));
                            list<::std::tuple<int64, str>> method_block = list<::std::tuple<int64, str>>{};
                            int64 m = k + 1;
                            while (m < py_len(class_block)) {
                                ::std::tuple<int64, str> n_pair = class_block[m];
                                int64 n_no = py_to_int64(::std::get<0>(n_pair));
                                str n_txt = py_to_string(::std::get<1>(n_pair));
                                if (py_strip(n_txt) == "") {
                                    int64 t = m + 1;
                                    while ((t < py_len(class_block)) && (py_strip(py_at(class_block[t], py_to_int64(1))) == "")) {
                                        t++;
                                    }
                                    if (t >= py_len(class_block))
                                        break;
                                    ::std::tuple<int64, str> t_pair = class_block[t];
                                    str t_txt = py_to_string(::std::get<1>(t_pair));
                                    int64 t_indent = py_len(t_txt) - py_len(py_lstrip(t_txt, " "));
                                    if (t_indent <= bind)
                                        break;
                                    method_block.append(::std::tuple<int64, str>(::std::make_tuple(n_no, n_txt)));
                                    m++;
                                    continue;
                                }
                                int64 n_indent = py_len(n_txt) - py_len(py_lstrip(n_txt, " "));
                                if (n_indent <= bind)
                                    break;
                                method_block.append(::std::tuple<int64, str>(::std::make_tuple(n_no, n_txt)));
                                m++;
                            }
                            if (py_len(method_block) == 0)
                                throw _make_east_build_error("unsupported_syntax", "self_hosted parser requires non-empty method body '" + cls_name + "." + mname + "'", _sh_span(ln_no, 0, py_len(ln_txt)), "Add method statements.");
                            dict<str, str> local_types = marg_types;
                            list<str> field_names = py_dict_keys(field_types);
                            for (str fnm : field_names) {
                                str fty = py_dict_get(field_types, py_to_string(fnm));
                                local_types[py_to_string(fnm)] = fty;
                            }
                            list<dict<str, object>> stmts = _sh_parse_stmt_block(method_block, local_types, cls_name + "." + mname);
                            auto __tuple_68 = _sh_extract_leading_docstring(stmts);
                            ::std::optional<str> docstring = ::std::get<0>(__tuple_68);
                            stmts = ::std::get<1>(__tuple_68);
                            dict<str, object> marg_defaults = dict<str, object>{};
                            for (str arg_name : marg_order) {
                                if (py_contains(marg_defaults_raw, arg_name)) {
                                    object default_obj = make_object(py_dict_get(marg_defaults_raw, py_to_string(arg_name)));
                                    str default_txt = py_strip(py_to_string(default_obj));
                                    if (default_txt != "") {
                                        auto default_col = ln_txt.find(default_txt);
                                        if (default_col < 0)
                                            default_col = bind;
                                        marg_defaults[py_to_string(arg_name)] = make_object(_sh_parse_expr_lowered(default_txt, ln_no, default_col, local_types));
                                    }
                                }
                            }
                            if (mname == "__init__") {
                                for (dict<str, object> st : stmts) {
                                    if (py_dict_get_maybe(st, "kind") == "Assign") {
                                        auto tgt = py_dict_get_maybe(st, "target");
                                        object tgt_value = object{};
                                        if (py_is_dict(tgt))
                                            tgt_value = make_object(py_dict_get_maybe(tgt, "value"));
                                        ::std::optional<dict<str, object>> tgt_value_dict = ::std::nullopt;
                                        if (py_is_dict(tgt_value))
                                            tgt_value_dict = tgt_value;
                                        if ((py_is_dict(tgt)) && (py_dict_get_maybe(tgt, "kind") == "Attribute") && (!py_is_none(tgt_value_dict)) && (py_dict_get_maybe(tgt_value_dict, "kind") == "Name") && (py_dict_get_maybe(tgt_value_dict, "id") == "self")) {
                                            str fname = py_to_string(py_dict_get_default(tgt, "attr", ""));
                                            if (fname != "") {
                                                auto st_value = py_dict_get_maybe(st, "value");
                                                object st_value_rt = object{};
                                                if (py_is_dict(st_value))
                                                    st_value_rt = make_object(py_dict_get_maybe(st_value, "resolved_type"));
                                                object t_val = make_object(py_dict_get_maybe(st, "decl_type"));
                                                if ((!(py_is_str(t_val))) || (t_val == ""))
                                                    t_val = make_object(st_value_rt);
                                                if ((py_is_str(t_val)) && (t_val != ""))
                                                    field_types[py_to_string(fname)] = py_to_string(t_val);
                                            }
                                        }
                                    }
                                    if (py_dict_get_maybe(st, "kind") == "AnnAssign") {
                                        auto tgt = py_dict_get_maybe(st, "target");
                                        object tgt_value = object{};
                                        if (py_is_dict(tgt))
                                            tgt_value = make_object(py_dict_get_maybe(tgt, "value"));
                                        ::std::optional<dict<str, object>> tgt_value_dict = ::std::nullopt;
                                        if (py_is_dict(tgt_value))
                                            tgt_value_dict = tgt_value;
                                        if ((py_is_dict(tgt)) && (py_dict_get_maybe(tgt, "kind") == "Attribute") && (!py_is_none(tgt_value_dict)) && (py_dict_get_maybe(tgt_value_dict, "kind") == "Name") && (py_dict_get_maybe(tgt_value_dict, "id") == "self")) {
                                            str fname = py_to_string(py_dict_get_default(tgt, "attr", ""));
                                            auto ann = py_dict_get_maybe(st, "annotation");
                                            if ((fname != "") && (py_is_str(ann)) && (ann != ""))
                                                field_types[py_to_string(fname)] = ann;
                                        }
                                    }
                                }
                            }
                            dict<str, int64> arg_index_map = dict<str, int64>{};
                            int64 arg_pos = 0;
                            while (arg_pos < py_len(marg_order)) {
                                str arg_name = marg_order[arg_pos];
                                arg_index_map[py_to_string(arg_name)] = arg_pos;
                                arg_pos++;
                            }
                            dict<str, str> arg_usage_map = dict<str, str>{};
                            for (::std::any arg_name : py_dict_keys(marg_types))
                                arg_usage_map[py_to_string(arg_name)] = "readonly";
                            class_body.append(dict<str, object>(dict<str, object>{{"kind", make_object("FunctionDef")}, {"name", make_object(mname)}, {"original_name", make_object(mname)}, {"source_span", make_object(dict<str, int64>{{"lineno", ln_no}, {"col", bind}, {"end_lineno", ::std::get<0>(py_at(method_block, -1))}, {"end_col", py_len(::std::get<1>(py_at(method_block, -1)))}})}, {"arg_types", make_object(marg_types)}, {"arg_order", make_object(marg_order)}, {"arg_defaults", make_object(marg_defaults)}, {"arg_index", make_object(arg_index_map)}, {"return_type", make_object(mret)}, {"arg_usage", make_object(arg_usage_map)}, {"renamed_symbols", make_object(dict<str, object>{})}, {"decorators", make_object(pending_method_decorators)}, {"docstring", make_object(docstring)}, {"body", make_object(stmts)}}));
                            pending_method_decorators = list<object>{};
                            k = m;
                            continue;
                        }
                    }
                    throw _make_east_build_error("unsupported_syntax", "self_hosted parser cannot parse class statement: " + py_to_string(s2), _sh_span(ln_no, 0, py_len(ln_txt)), "Use field annotation or method definitions in class body.");
                }
                
                str storage_hint_override = class_storage_hint_override;
                ::std::optional<str> base_value = ::std::nullopt;
                if (base != "")
                    base_value = base;
                
                dict<str, object> cls_item = dict<str, object>{{"kind", make_object("ClassDef")}, {"name", make_object(cls_name)}, {"original_name", make_object(cls_name)}, {"source_span", make_object(dict<str, int64>{{"lineno", i}, {"col", 0}, {"end_lineno", ::std::get<0>(py_at(block, -1))}, {"end_col", py_len(::std::get<1>(py_at(block, -1)))}})}, {"base", make_object(base_value)}, {"dataclass", make_object(pending_dataclass)}, {"field_types", make_object(field_types)}, {"body", make_object(class_body)}};
                set<str> static_field_names = set<str>{};
                if (!(pending_dataclass)) {
                    for (dict<str, object> st : class_body) {
                        if (py_dict_get_maybe(st, "kind") == "AnnAssign") {
                            auto tgt = py_dict_get_maybe(st, "target");
                            if ((py_is_dict(tgt)) && (py_dict_get_maybe(tgt, "kind") == "Name")) {
                                str fname = py_to_string(py_dict_get_default(tgt, "id", ""));
                                if (fname != "")
                                    static_field_names.insert(fname);
                            }
                        }
                    }
                }
                bool has_del = py_any([&]() -> list<bool> {     list<bool> __out;     for (auto st : class_body) {         __out.append((py_is_dict(st)) && (py_dict_get_maybe(st, "kind") == "FunctionDef") && (py_dict_get_maybe(st, "name") == "__del__"));     }     return __out; }());
                set<str> instance_field_names = set<str>{};
                for (::std::any field_name : py_dict_keys(field_types)) {
                    if (!py_contains(static_field_names, field_name))
                        instance_field_names.insert(field_name);
                }
                // conservative hint:
                // - classes with instance state / __del__ / inheritance should keep reference semantics
                // - stateless, non-inherited classes can be value candidates
                if (storage_hint_override != "") {
                    cls_item[py_to_string("class_storage_hint")] = make_object(storage_hint_override);
                } else {
                    if (py_contains(set<str>{"Enum", "IntEnum", "IntFlag"}, base_name)) {
                        cls_item[py_to_string("class_storage_hint")] = make_object("value");
                    } else {
                        if ((py_len(instance_field_names) == 0) && (!(has_del)) && (base == ""))
                            cls_item[py_to_string("class_storage_hint")] = make_object("value");
                        else
                            cls_item[py_to_string("class_storage_hint")] = make_object("ref");
                    }
                }
                pending_dataclass = false;
                if (!(first_item_attached)) {
                    cls_item[py_to_string("leading_comments")] = make_object(leading_file_comments);
                    cls_item[py_to_string("leading_trivia")] = make_object(leading_file_trivia);
                    first_item_attached = true;
                }
                body_items.append(dict<str, object>(cls_item));
                i = j;
                continue;
            }
            
            ::std::optional<::std::tuple<str, str, str>> parsed_top_typed = _sh_parse_typed_binding(s, false);
            str top_name;
            str top_ann;
            str top_default;
            if (!py_is_none(parsed_top_typed)) {
                auto __tuple_70 = *(parsed_top_typed);
                top_name = ::std::get<0>(__tuple_70);
                top_ann = ::std::get<1>(__tuple_70);
                top_default = ::std::get<2>(__tuple_70);
            } else {
                auto __tuple_71 = ::std::make_tuple("", "", "");
                top_name = ::std::get<0>(__tuple_71);
                top_ann = ::std::get<1>(__tuple_71);
                top_default = ::std::get<2>(__tuple_71);
            }
            if ((!py_is_none(parsed_top_typed)) && (top_default != "")) {
                str name = top_name;
                str ann_txt = top_ann;
                str expr_txt = top_default;
                str ann = _sh_ann_to_type(ann_txt);
                auto expr_col = ln.find(expr_txt);
                body_items.append(dict<str, object>(dict<str, object>{{"kind", make_object("AnnAssign")}, {"source_span", make_object(_sh_span(i, ln.find(name), py_len(ln)))}, {"target", make_object(dict<str, object>{{"kind", make_object("Name")}, {"source_span", make_object(_sh_span(i, ln.find(name), ln.find(name) + py_len(name)))}, {"resolved_type", make_object(ann)}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(name)}, {"id", make_object(name)}})}, {"annotation", make_object(ann)}, {"value", make_object(_sh_parse_expr_lowered(expr_txt, i, expr_col, dict<str, object>{}))}, {"declare", make_object(true)}, {"decl_type", make_object(ann)}}));
                i = logical_end + 1;
                continue;
            }
            
            ::std::optional<::std::tuple<str, str>> asg_top = _sh_split_top_level_assign(s);
            if (!py_is_none(asg_top)) {
                auto __tuple_72 = *(asg_top);
                str asg_left = ::std::get<0>(__tuple_72);
                str asg_right = ::std::get<1>(__tuple_72);
                str name = py_strip(asg_left);
                if (!(_sh_is_identifier(name)))
                    throw _make_east_build_error("unsupported_syntax", "self_hosted parser cannot parse top-level statement: " + py_to_string(s), _sh_span(i, 0, py_len(ln)), "Use def/class/top-level typed assignment/main guard.");
                str expr_txt = py_strip(asg_right);
                auto expr_col = ln.find(expr_txt);
                if (expr_col < 0)
                    expr_col = 0;
                dict<str, object> val_node = _sh_parse_expr_lowered(expr_txt, i, expr_col, dict<str, object>{});
                str decl_type = py_to_string(dict_get_node(val_node, "resolved_type", "unknown"));
                body_items.append(dict<str, object>(dict<str, object>{{"kind", make_object("Assign")}, {"source_span", make_object(_sh_span(i, ln.find(name), py_len(ln)))}, {"target", make_object(dict<str, object>{{"kind", make_object("Name")}, {"source_span", make_object(_sh_span(i, ln.find(name), ln.find(name) + py_len(name)))}, {"resolved_type", make_object(decl_type)}, {"borrow_kind", make_object("value")}, {"casts", make_object(list<object>{})}, {"repr", make_object(name)}, {"id", make_object(name)}})}, {"value", make_object(val_node)}, {"declare", make_object(true)}, {"declare_init", make_object(true)}, {"decl_type", make_object(decl_type)}}));
                i = logical_end + 1;
                continue;
            }
            
            if (((py_startswith(s, "\"\"\"")) && (py_endswith(s, "\"\"\""))) || ((py_startswith(s, "'''")) && (py_endswith(s, "'''")))) {
                // Module-level docstring / standalone string expression.
                body_items.append(dict<str, object>(dict<str, object>{{"kind", make_object("Expr")}, {"source_span", make_object(_sh_span(i, 0, py_len(ln)))}, {"value", make_object(_sh_parse_expr_lowered(s, i, 0, dict<str, object>{}))}}));
                i = logical_end + 1;
                continue;
            }
            
            throw _make_east_build_error("unsupported_syntax", "self_hosted parser cannot parse top-level statement: " + py_to_string(s), _sh_span(i, 0, py_len(ln)), "Use def/class/top-level typed assignment/main guard.");
        }
        
        dict<str, str> renamed_symbols = dict<str, str>{};
        for (dict<str, object> item : body_items) {
            if ((py_dict_get_maybe(item, "kind") == "FunctionDef") && (py_dict_get_maybe(item, "name") == "main")) {
                renamed_symbols[py_to_string("main")] = "__pytra_main";
                item[py_to_string("name")] = make_object("__pytra_main");
            }
        }
        
        // 互換メタデータは ImportBinding 正本から導出する。
        import_module_bindings = dict<str, object>{};
        import_symbol_bindings = dict<str, object>{};
        list<dict<str, str>> qualified_symbol_refs = list<dict<str, str>>{};
        for (dict<str, object> binding : import_bindings) {
            auto module_id_obj = py_dict_get_maybe(binding, "module_id");
            auto local_name_obj = py_dict_get_maybe(binding, "local_name");
            auto export_name_obj = py_dict_get_maybe(binding, "export_name");
            auto binding_kind_obj = py_dict_get_maybe(binding, "binding_kind");
            str module_id = "";
            if (py_is_str(module_id_obj))
                module_id = module_id_obj;
            str local_name = "";
            if (py_is_str(local_name_obj))
                local_name = local_name_obj;
            str export_name = "";
            if (py_is_str(export_name_obj))
                export_name = export_name_obj;
            str binding_kind = "";
            if (py_is_str(binding_kind_obj))
                binding_kind = binding_kind_obj;
            if ((module_id == "") || (local_name == ""))
                continue;
            if (binding_kind == "module") {
                import_module_bindings[local_name] = module_id;
                continue;
            }
            if ((binding_kind == "symbol") && (export_name != "")) {
                dict<str, str> sym_binding = dict<str, str>{};
                sym_binding[py_to_string("module")] = module_id;
                sym_binding[py_to_string("name")] = export_name;
                import_symbol_bindings[local_name] = sym_binding;
                dict<str, str> qref = dict<str, str>{};
                qref[py_to_string("module_id")] = module_id;
                qref[py_to_string("symbol")] = export_name;
                qref[py_to_string("local_name")] = local_name;
                qualified_symbol_refs.append(dict<str, str>(qref));
            }
        }
        
        dict<str, object> source_span = dict<str, object>{};
        source_span[py_to_string("lineno")] = object{};
        source_span[py_to_string("col")] = object{};
        source_span[py_to_string("end_lineno")] = object{};
        source_span[py_to_string("end_col")] = object{};
        
        dict<str, object> meta = dict<str, object>{};
        meta[py_to_string("parser_backend")] = make_object("self_hosted");
        meta[py_to_string("import_bindings")] = make_object(import_bindings);
        meta[py_to_string("qualified_symbol_refs")] = make_object(qualified_symbol_refs);
        meta[py_to_string("import_modules")] = make_object(import_module_bindings);
        meta[py_to_string("import_symbols")] = make_object(import_symbol_bindings);
        
        dict<str, object> out = dict<str, object>{};
        out[py_to_string("kind")] = make_object("Module");
        out[py_to_string("source_path")] = make_object(filename);
        out[py_to_string("source_span")] = make_object(source_span);
        out[py_to_string("body")] = make_object(body_items);
        out[py_to_string("main_guard_body")] = make_object(main_stmts);
        out[py_to_string("renamed_symbols")] = make_object(renamed_symbols);
        out[py_to_string("meta")] = make_object(meta);
        return out;
    }
    
    dict<str, object> convert_source_to_east_with_backend(const str& source, const str& filename, const str& parser_backend = "self_hosted") {
        /* 指定バックエンドでソースを EAST へ変換する統一入口。 */
        if (parser_backend != "self_hosted")
            throw _make_east_build_error("unsupported_syntax", "unknown parser backend: " + parser_backend, dict<str, object>{}, "Use parser_backend=self_hosted.");
        return convert_source_to_east_self_hosted(source, filename);
    }
    
    dict<str, object> convert_path(const Path& input_path, const str& parser_backend = "self_hosted") {
        /* Python ファイルを読み込み、EAST ドキュメントへ変換する。 */
        str source = input_path.read_text();
        return convert_source_to_east_with_backend(source, py_to_string(input_path), parser_backend);
    }
    
}  // namespace pytra::compiler::east_parts::core
