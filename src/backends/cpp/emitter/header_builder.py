from __future__ import annotations

from pytra.std.typing import Any
from pytra.compiler.transpile_cli import (
    dict_any_get_dict,
    dict_any_get_dict_list,
    dict_any_get_list,
    dict_any_get_str,
    join_str_list,
    split_top_level_union,
    split_type_args,
    stmt_target_name,
)
from pytra.std.pathlib import Path


def build_cpp_header_from_east(
    east_module: dict[str, Any],
    source_path: Path,
    output_path: Path,
    top_namespace: str = "",
) -> str:
    """EAST から最小宣言のみの C++ ヘッダ文字列を生成する。"""
    body = dict_any_get_dict_list(east_module, "body")

    class_lines: list[str] = []
    fn_lines: list[str] = []
    var_lines: list[str] = []
    used_types: set[str] = set()
    seen_classes: set[str] = set()
    class_names: set[str] = set()
    ref_classes: set[str] = set()

    for st in body:
        if dict_any_get_str(st, "kind") == "ClassDef":
            cls_name = dict_any_get_str(st, "name")
            if cls_name != "":
                class_names.add(cls_name)
                hint = dict_any_get_str(st, "class_storage_hint", "ref")
                if hint == "ref":
                    ref_classes.add(cls_name)

    by_value_types = {
        "bool",
        "int8",
        "uint8",
        "int16",
        "uint16",
        "int32",
        "uint32",
        "int64",
        "uint64",
        "float32",
        "float64",
    }

    for st in body:
        kind = dict_any_get_str(st, "kind")
        if kind == "ClassDef":
            cls_name = dict_any_get_str(st, "name")
            if cls_name != "" and cls_name not in seen_classes:
                class_lines.append("struct " + cls_name + ";")
                seen_classes.add(cls_name)
        elif kind == "FunctionDef":
            name = dict_any_get_str(st, "name")
            if name != "":
                ret_t = dict_any_get_str(st, "return_type", "None")
                ret_cpp = _header_cpp_type_from_east(ret_t, ref_classes, class_names)
                used_types.add(ret_cpp)
                arg_types = dict_any_get_dict(st, "arg_types")
                arg_order = dict_any_get_list(st, "arg_order")
                parts: list[str] = []
                for an in arg_order:
                    if not isinstance(an, str):
                        continue
                    at = dict_any_get_str(arg_types, an, "Any")
                    at_cpp = _header_cpp_type_from_east(at, ref_classes, class_names)
                    used_types.add(at_cpp)
                    param_txt = (
                        at_cpp + " " + an if at_cpp in by_value_types else "const " + at_cpp + "& " + an
                    )
                    # NOTE:
                    # 既定引数は `.cpp` 側の定義にのみ付与する。
                    # ヘッダと定義の二重指定によるコンパイルエラーを避けるため、
                    # 宣言側では既定値を埋め込まない。
                    parts.append(param_txt)
                sep = ", "
                fn_lines.append(ret_cpp + " " + name + "(" + sep.join(parts) + ");")
        elif kind in {"Assign", "AnnAssign"}:
            name = stmt_target_name(st)
            if name == "":
                continue
            decl_t = dict_any_get_str(st, "decl_type")
            if decl_t == "" or decl_t == "unknown":
                tgt = dict_any_get_dict(st, "target")
                decl_t = dict_any_get_str(tgt, "resolved_type")
            if decl_t == "" or decl_t == "unknown":
                continue
            cpp_t = _header_cpp_type_from_east(decl_t, ref_classes, class_names)
            used_types.add(cpp_t)
            var_lines.append("extern " + cpp_t + " " + name + ";")

    includes: list[str] = []
    has_std_any = False
    has_std_int = False
    has_std_string = False
    has_std_vector = False
    has_std_tuple = False
    has_std_optional = False
    has_std_umap = False
    has_std_uset = False
    for t in used_types:
        if "::std::any" in t:
            has_std_any = True
        if "::std::int" in t or "::std::uint" in t:
            has_std_int = True
        if "::std::string" in t:
            has_std_string = True
        if "::std::vector" in t:
            has_std_vector = True
        if "::std::tuple" in t:
            has_std_tuple = True
        if "::std::optional" in t:
            has_std_optional = True
        if "::std::unordered_map" in t:
            has_std_umap = True
        if "::std::unordered_set" in t:
            has_std_uset = True
    if has_std_any:
        includes.append("#include <any>")
    if has_std_int:
        includes.append("#include <cstdint>")
    if has_std_string:
        includes.append("#include <string>")
    if has_std_vector:
        includes.append("#include <vector>")
    if has_std_tuple:
        includes.append("#include <tuple>")
    if has_std_optional:
        includes.append("#include <optional>")
    if has_std_umap:
        includes.append("#include <unordered_map>")
    if has_std_uset:
        includes.append("#include <unordered_set>")

    guard = _header_guard_from_path(str(output_path))
    lines: list[str] = []
    lines.append("// AUTO-GENERATED FILE. DO NOT EDIT.")
    lines.append("// source: " + str(source_path))
    lines.append("// generated-by: src/py2cpp.py")
    lines.append("")
    lines.append("#ifndef " + guard)
    lines.append("#define " + guard)
    lines.append("")
    for include in includes:
        lines.append(include)
    if len(includes) > 0:
        lines.append("")
    ns = top_namespace.strip()
    if ns != "":
        lines.append("namespace " + ns + " {")
        lines.append("")
    for class_line in class_lines:
        lines.append(class_line)
    if len(class_lines) > 0:
        lines.append("")
    for var_line in var_lines:
        lines.append(var_line)
    if len(var_lines) > 0 and len(fn_lines) > 0:
        lines.append("")
    for fn_line in fn_lines:
        lines.append(fn_line)
    if ns != "":
        lines.append("")
        lines.append("}  // namespace " + ns)
    lines.append("")
    lines.append("#endif  // " + guard)
    lines.append("")
    return join_str_list("\n", lines)


def _header_cpp_type_from_east(
    east_t: str,
    ref_classes: set[str],
    class_names: set[str],
) -> str:
    """EAST 型名を runtime header 向け C++ 型名へ変換する。"""
    t = east_t.strip()
    if t == "":
        return "object"
    if t in ref_classes:
        return "rc<" + t + ">"
    if t in class_names:
        return t
    prim: dict[str, str] = {
        "int8": "int8",
        "uint8": "uint8",
        "int16": "int16",
        "uint16": "uint16",
        "int32": "int32",
        "uint32": "uint32",
        "int64": "int64",
        "uint64": "uint64",
        "float32": "float32",
        "float64": "float64",
        "bool": "bool",
        "str": "str",
        "bytes": "bytes",
        "bytearray": "bytearray",
        "None": "void",
        "Any": "object",
        "object": "object",
        "unknown": "object",
    }
    if t in prim:
        return prim[t]
    parts_union = split_top_level_union(t)
    if len(parts_union) > 1:
        parts = parts_union
        non_none: list[str] = []
        for part in parts:
            p = part.strip()
            if p != "None":
                non_none.append(p)
        if len(parts) == 2 and len(non_none) == 1:
            return "::std::optional<" + _header_cpp_type_from_east(non_none[0], ref_classes, class_names) + ">"
        folded: list[str] = []
        for part in non_none:
            p = part
            if p == "bytearray":
                p = "bytes"
            if p not in folded:
                folded.append(p)
        if len(folded) == 1:
            only = folded[0]
            return _header_cpp_type_from_east(only, ref_classes, class_names)
        return "object"
    if t.startswith("list[") and t.endswith("]"):
        inner = t[5:-1].strip()
        return "list<" + _header_cpp_type_from_east(inner, ref_classes, class_names) + ">"
    if t.startswith("set[") and t.endswith("]"):
        inner = t[4:-1].strip()
        return "set<" + _header_cpp_type_from_east(inner, ref_classes, class_names) + ">"
    if t.startswith("dict[") and t.endswith("]"):
        inner = split_type_args(t[5:-1].strip())
        if len(inner) == 2:
            return "dict<" + _header_cpp_type_from_east(inner[0], ref_classes, class_names) + ", " + _header_cpp_type_from_east(inner[1], ref_classes, class_names) + ">"
        return "dict<str, object>"
    if t.startswith("tuple[") and t.endswith("]"):
        inner = split_type_args(t[6:-1].strip())
        vals: list[str] = []
        for part in inner:
            vals.append(_header_cpp_type_from_east(part, ref_classes, class_names))
        sep = ", "
        return "::std::tuple<" + sep.join(vals) + ">"
    if "." in t:
        ns_t = t.replace(".", "::")
        dot = t.rfind(".")
        leaf = t[dot + 1 :] if dot >= 0 else t
        if leaf != "" and (leaf[0] >= "A" and leaf[0] <= "Z"):
            return "rc<" + ns_t + ">"
        return ns_t
    return t


def _header_guard_from_path(path: str) -> str:
    """ヘッダパスから include guard を生成する。"""
    src = path.replace("\\", "/")
    prefix1 = "src/runtime/cpp/pytra/"
    prefix2 = "runtime/cpp/pytra/"
    if src.startswith(prefix1):
        src = src[len(prefix1) :]
    elif src.startswith(prefix2):
        src = src[len(prefix2) :]
    src = "PYTRA_" + src.upper()
    out_chars: list[str] = []
    i = 0
    while i < len(src):
        ch = src[i]
        ok = ((ch >= "A" and ch <= "Z") or (ch >= "0" and ch <= "9"))
        if ok:
            out_chars.append(ch)
        else:
            out_chars.append("_")
        i += 1
    out = "".join(out_chars).lstrip("_")
    if not out.endswith("_H"):
        out += "_H"
    return out


def _header_allows_none_default(east_t: str) -> bool:
    """ヘッダ既定値で `None`（optional）を許容する型か判定する。"""
    txt = east_t.strip()
    if txt.startswith("optional[") and txt.endswith("]"):
        return True
    if "|" in txt:
        parts = txt.split("|")
        i = 0
        while i < len(parts):
            part = str(parts[i])
            if part.strip() == "None":
                return True
            i += 1
    return txt == "None"


def _header_none_default_expr_for_type(east_t: str) -> str:
    """ヘッダ既定値で `None` を型別既定値へ変換する。"""
    txt = east_t.strip()
    if txt in {"", "unknown", "Any", "object"}:
        return "object{}"
    if _header_allows_none_default(txt):
        return "::std::nullopt"
    if txt in {"int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}:
        return "0"
    if txt in {"float32", "float64"}:
        return "0.0"
    if txt == "bool":
        return "false"
    if txt == "str":
        return "str()"
    if txt == "bytes":
        return "bytes()"
    if txt == "bytearray":
        return "bytearray()"
    if txt == "Path":
        return "Path()"
    cpp_t = _header_cpp_type_from_east(txt, set(), set())
    if cpp_t.startswith("::std::optional<"):
        return "::std::nullopt"
    return cpp_t + "{}"


def _cpp_string_lit(s: str) -> str:
    """Python 文字列を C++ 文字列リテラルへエスケープ変換する。"""
    out_chars: list[str] = []
    for ch in s:
        if ch == "\\":
            out_chars.append("\\\\")
        elif ch == "\"":
            out_chars.append("\\\"")
        elif ch == "\n":
            out_chars.append("\\n")
        elif ch == "\r":
            out_chars.append("\\r")
        elif ch == "\t":
            out_chars.append("\\t")
        else:
            out_chars.append(ch)
    return "\"" + "".join(out_chars) + "\""


def _header_render_default_expr(node: dict[str, Any], east_target_t: str) -> str:
    """EAST の既定値ノードを C++ ヘッダ宣言用の式文字列へ変換する。"""
    kind = dict_any_get_str(node, "kind")
    if kind == "Constant":
        val = node.get("value")
        if val is None:
            return _header_none_default_expr_for_type(east_target_t)
        if isinstance(val, bool):
            return "true" if val else "false"
        if isinstance(val, int):
            return str(val)
        if isinstance(val, float):
            return str(val)
        if isinstance(val, str):
            return _cpp_string_lit(val)
        return ""
    if kind == "Name":
        ident = dict_any_get_str(node, "id")
        if ident == "None":
            return _header_none_default_expr_for_type(east_target_t)
        if ident == "True":
            return "true"
        if ident == "False":
            return "false"
        return ""
    if kind == "Tuple":
        elems = dict_any_get_dict_list(node, "elements")
        if len(elems) == 0:
            return "::std::tuple<>{}"
        parts: list[str] = []
        for e in elems:
            txt = _header_render_default_expr(e, "Any")
            if txt == "":
                return ""
            parts.append(txt)
        if len(parts) == 0:
            return ""
        return "::std::make_tuple(" + join_str_list(", ", parts) + ")"
    _ = east_target_t
    return ""
