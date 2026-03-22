from __future__ import annotations

from pytra.typing import Any
from toolchain.misc.transpile_cli import (
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
from toolchain.emit.cpp.emitter.profile_loader import load_cpp_identifier_rules


_HEADER_RESERVED_WORDS, _HEADER_RENAME_PREFIX = load_cpp_identifier_rules({})


def _header_safe_identifier(name: str) -> str:
    if name in _HEADER_RESERVED_WORDS:
        return _HEADER_RENAME_PREFIX + name
    return name


def _header_homogeneous_tuple_ellipsis_item_type(east_t: str) -> str:
    txt = east_t.strip()
    if not (txt.startswith("tuple[") and txt.endswith("]")):
        return ""
    inner = split_type_args(txt[6:-1].strip())
    if len(inner) != 2:
        return ""
    item_t = inner[0].strip()
    tail_t = inner[1].strip()
    if item_t == "" or tail_t != "...":
        return ""
    return item_t


def _header_dict_stmt_list(raw: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(raw, list):
        return out
    for item in raw:
        if isinstance(item, dict):
            out.append(item)
    return out


def _header_node_kind_from_dict(node_dict: dict[str, Any]) -> str:
    kind = node_dict.get("kind")
    if isinstance(kind, str):
        return kind.strip()
    return ""


def _header_mark_mutated_param_from_target(tgt: Any, params: set[str], out: set[str]) -> None:
    if not isinstance(tgt, dict):
        return
    _header_mark_mutated_param_from_target_inner(tgt, params, out)


def _header_extract_owner_name_id(owner_dict: dict[str, Any], params: set[str], out: set[str]) -> None:
    if _header_node_kind_from_dict(owner_dict) == "Name":
        nm = owner_dict.get("id")
        if isinstance(nm, str) and nm in params:
            out.add(nm)


def _header_mark_mutated_param_from_target_inner(tgt: dict[str, Any], params: set[str], out: set[str]) -> None:
    tkind = _header_node_kind_from_dict(tgt)
    if tkind == "Name":
        nm = tgt.get("id")
        if isinstance(nm, str) and nm in params:
            out.add(nm)
        return
    if tkind == "Attribute":
        owner = tgt.get("value")
        if isinstance(owner, dict):
            _header_extract_owner_name_id(owner, params, out)
        return
    if tkind == "Subscript":
        owner = tgt.get("value")
        if isinstance(owner, dict):
            _header_extract_owner_name_id(owner, params, out)
        return
    if tkind == "Tuple":
        elems = tgt.get("elements")
        if isinstance(elems, list):
            for elem in elems:
                _header_mark_mutated_param_from_target(elem, params, out)


def _header_collect_mutated_params_from_stmt(
    stmt: dict[str, Any],
    params: set[str],
    out: set[str],
    function_mutated_param_positions: dict[str, set[int]] | None = None,
) -> None:
    kind = _header_node_kind_from_dict(stmt)
    if kind in {"Assign", "AnnAssign", "AugAssign"}:
        _header_mark_mutated_param_from_target(stmt.get("target"), params, out)
    elif kind == "Swap":
        _header_mark_mutated_param_from_target(stmt.get("lhs"), params, out)
        _header_mark_mutated_param_from_target(stmt.get("rhs"), params, out)
    elif kind == "Expr":
        call = stmt.get("value")
        if isinstance(call, dict) and _header_node_kind_from_dict(call) == "Call":
            fn = call.get("func")
            if isinstance(fn, dict) and _header_node_kind_from_dict(fn) == "Attribute":
                owner = fn.get("value")
                if isinstance(owner, dict) and _header_node_kind_from_dict(owner) == "Name":
                    nm = owner.get("id")
                    attr = fn.get("attr")
                    if isinstance(nm, str) and isinstance(attr, str):
                        if nm in params and attr in {
                            "append",
                            "extend",
                            "insert",
                            "pop",
                            "clear",
                            "remove",
                            "discard",
                            "add",
                            "update",
                            "setdefault",
                            "sort",
                            "reverse",
                            "mkdir",
                            "write",
                            "write_text",
                            "close",
                        }:
                            out.add(nm)
            elif isinstance(fn, dict) and _header_node_kind_from_dict(fn) == "Name":
                fn_name = fn.get("id")
                if isinstance(fn_name, str) and function_mutated_param_positions is not None:
                    mutated_positions = function_mutated_param_positions.get(fn_name, set())
                    if isinstance(mutated_positions, set) and len(mutated_positions) > 0:
                        raw_args = call.get("args")
                        if isinstance(raw_args, list):
                            for idx, arg in enumerate(raw_args):
                                if idx in mutated_positions:
                                    _header_mark_mutated_param_from_target(arg, params, out)
    if kind == "If":
        for s in _header_dict_stmt_list(stmt.get("body")):
            _header_collect_mutated_params_from_stmt(s, params, out, function_mutated_param_positions)
        for s in _header_dict_stmt_list(stmt.get("orelse")):
            _header_collect_mutated_params_from_stmt(s, params, out, function_mutated_param_positions)
        return
    if kind in {"While", "For", "ForCore"}:
        for s in _header_dict_stmt_list(stmt.get("body")):
            _header_collect_mutated_params_from_stmt(s, params, out, function_mutated_param_positions)
        for s in _header_dict_stmt_list(stmt.get("orelse")):
            _header_collect_mutated_params_from_stmt(s, params, out, function_mutated_param_positions)
        return
    if kind == "Try":
        for s in _header_dict_stmt_list(stmt.get("body")):
            _header_collect_mutated_params_from_stmt(s, params, out, function_mutated_param_positions)
        for h in _header_dict_stmt_list(stmt.get("handlers")):
            for s in _header_dict_stmt_list(h.get("body")):
                _header_collect_mutated_params_from_stmt(s, params, out, function_mutated_param_positions)
        for s in _header_dict_stmt_list(stmt.get("orelse")):
            _header_collect_mutated_params_from_stmt(s, params, out, function_mutated_param_positions)
        for s in _header_dict_stmt_list(stmt.get("finalbody")):
            _header_collect_mutated_params_from_stmt(s, params, out, function_mutated_param_positions)


def _header_collect_mutated_params(
    body_stmts: list[dict[str, Any]],
    arg_names: list[str],
    *,
    function_mutated_param_positions: dict[str, set[int]] | None = None,
) -> set[str]:
    params = set(arg_names)
    out: set[str] = set()
    for st in body_stmts:
        _header_collect_mutated_params_from_stmt(st, params, out, function_mutated_param_positions)
    return out


def split_cpp_inline_class_defs(
    cpp_text: str,
    top_namespace: str = "",
    keep_class_decls: bool = True,
) -> str:
    """`struct/class` 内 inline method 定義を out-of-class 実装へ分離する。"""
    if cpp_text.strip() == "":
        return cpp_text
    lines = cpp_text.splitlines()
    if len(lines) == 0:
        return cpp_text
    start, end = _namespace_body_span(lines, top_namespace)
    if start < 0 or end <= start:
        return cpp_text
    out_lines: list[str] = []
    i = 0
    while i < len(lines):
        if i < start or i >= end:
            out_lines.append(lines[i])
            i += 1
            continue
        raw = lines[i]
        stripped = raw.lstrip()
        if not ((stripped.startswith("struct ") or stripped.startswith("class ")) and "{" in raw):
            out_lines.append(raw)
            i += 1
            continue
        cls_start = i
        depth = _brace_delta_ignoring_literals(raw)
        cls_lines: list[str] = [raw]
        i += 1
        while i < end and depth > 0:
            cur = lines[i]
            cls_lines.append(cur)
            depth += _brace_delta_ignoring_literals(cur)
            i += 1
        decl_lines, def_lines = _split_single_class_block(cls_lines)
        if keep_class_decls:
            out_lines.extend(decl_lines)
        if len(def_lines) > 0:
            if len(out_lines) > 0 and out_lines[-1] != "":
                out_lines.append("")
            out_lines.extend(def_lines)
        if i == cls_start:
            i += 1
    return join_str_list("\n", out_lines) + ("\n" if cpp_text.endswith("\n") else "")


def build_cpp_header_from_east(
    east_module: dict[str, Any],
    source_path: Path,
    output_path: Path,
    top_namespace: str = "",
    cpp_text: str = "",
) -> str:
    """EAST から最小宣言のみの C++ ヘッダ文字列を生成する。"""
    body = dict_any_get_dict_list(east_module, "body")
    class_blocks = _extract_cpp_class_blocks(cpp_text, top_namespace)
    class_block_names = _extract_class_names_from_blocks(class_blocks)

    class_lines: list[str] = []
    alias_lines: list[str] = []
    fn_lines: list[str] = []
    var_lines: list[str] = []
    cpp_to_alias: dict[str, str] = {}
    used_types: set[str] = set()
    seen_classes: set[str] = set()
    class_names: set[str] = set()
    ref_classes: set[str] = set()
    pyobj_ref_lists = True
    import_include_symbol_map = _header_import_include_symbol_map(east_module)

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

    function_mutated_param_positions: dict[str, set[int]] = {}
    for st in body:
        if dict_any_get_str(st, "kind") != "FunctionDef":
            continue
        name = dict_any_get_str(st, "name")
        if name == "":
            continue
        arg_types = dict_any_get_dict(st, "arg_types")
        arg_order = dict_any_get_list(st, "arg_order")
        body_stmts = _header_dict_stmt_list(st.get("body"))
        arg_names: list[str] = []
        for raw_name in arg_order:
            if isinstance(raw_name, str) and raw_name != "" and raw_name in arg_types:
                arg_names.append(raw_name)
        vararg_name = dict_any_get_str(st, "vararg_name", "")
        vararg_type = dict_any_get_str(st, "vararg_type", "")
        arg_names_for_mutated = list(arg_names)
        if vararg_name != "" and vararg_type != "":
            arg_names_for_mutated.append(vararg_name)
        mutated_params = _header_collect_mutated_params(
            body_stmts,
            arg_names_for_mutated,
            function_mutated_param_positions=function_mutated_param_positions,
        )
        function_mutated_param_positions[name] = {
            idx for idx, arg_name in enumerate(arg_names_for_mutated) if arg_name in mutated_params
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
                ret_abi_mode = _header_runtime_abi_ret_mode(st)
                ret_cpp = _header_cpp_signature_type_from_east(
                    ret_t,
                    ref_classes,
                    class_names,
                    runtime_abi_mode=ret_abi_mode,
                    pyobj_ref_lists=pyobj_ref_lists,
                )
                used_types.add(ret_cpp)
                arg_types = dict_any_get_dict(st, "arg_types")
                arg_usage = dict_any_get_dict(st, "arg_usage")
                arg_defaults = dict_any_get_dict(st, "arg_defaults")
                arg_order = dict_any_get_list(st, "arg_order")
                body_stmts = _header_dict_stmt_list(st.get("body"))
                arg_names: list[str] = []
                for raw_name in arg_order:
                    if isinstance(raw_name, str) and raw_name != "" and raw_name in arg_types:
                        arg_names.append(raw_name)
                vararg_name = dict_any_get_str(st, "vararg_name", "")
                vararg_type = dict_any_get_str(st, "vararg_type", "")
                arg_names_for_mutated = list(arg_names)
                if vararg_name != "" and vararg_type != "":
                    arg_names_for_mutated.append(vararg_name)
                mutated_params = _header_collect_mutated_params(
                    body_stmts,
                    arg_names_for_mutated,
                    function_mutated_param_positions=function_mutated_param_positions,
                )
                parts: list[str] = []
                for an in arg_order:
                    if not isinstance(an, str):
                        continue
                    at = dict_any_get_str(arg_types, an, "Any")
                    arg_abi_mode = _header_runtime_abi_arg_mode(st, an)
                    at_cpp = _header_cpp_signature_type_from_east(
                        at,
                        ref_classes,
                        class_names,
                        runtime_abi_mode=arg_abi_mode,
                        pyobj_ref_lists=pyobj_ref_lists,
                    )
                    used_types.add(at_cpp)
                    emitted_an = _header_safe_identifier(an)
                    usage = dict_any_get_str(arg_usage, an, "readonly")
                    if usage != "mutable" and an in mutated_params:
                        usage = "mutable"
                    borrow_cpp = _header_borrow_cpp_type(at, at_cpp, class_names, ref_classes)
                    if at_cpp in by_value_types:
                        param_txt = borrow_cpp + " " + emitted_an
                    elif usage == "mutable":
                        if (at_cpp.startswith("Object<") or at_cpp.startswith("rc<")) and not _header_is_class_borrow_type(at, at_cpp, class_names, ref_classes):
                            param_txt = at_cpp + "& " + emitted_an
                        else:
                            param_txt = borrow_cpp + " " + emitted_an if borrow_cpp == "object" else borrow_cpp + "& " + emitted_an
                    else:
                        if _header_is_class_borrow_type(at, at_cpp, class_names, ref_classes):
                            param_txt = "const " + borrow_cpp + "& " + emitted_an
                        else:
                            param_txt = "const " + borrow_cpp + "& " + emitted_an
                    if an in arg_defaults:
                        default_node = arg_defaults.get(an)
                        if isinstance(default_node, dict):
                            default_txt = _header_render_default_expr(
                                default_node,
                                at,
                                pyobj_ref_lists=pyobj_ref_lists,
                                ref_classes=ref_classes,
                                class_names=class_names,
                            )
                            if default_txt != "":
                                param_txt += " = " + default_txt
                    parts.append(param_txt)
                if vararg_name != "" and vararg_type != "":
                    list_t = "list[" + vararg_type + "]"
                    at_cpp = _header_cpp_signature_type_from_east(
                        list_t,
                        ref_classes,
                        class_names,
                        runtime_abi_mode="default",
                        pyobj_ref_lists=pyobj_ref_lists,
                    )
                    used_types.add(at_cpp)
                    emitted_vararg = _header_safe_identifier(vararg_name)
                    usage = dict_any_get_str(arg_usage, vararg_name, "readonly")
                    if usage != "mutable" and vararg_name in mutated_params:
                        usage = "mutable"
                    borrow_cpp = _header_borrow_cpp_type(list_t, at_cpp, class_names, ref_classes)
                    if at_cpp in by_value_types:
                        param_txt = borrow_cpp + " " + emitted_vararg
                    elif usage == "mutable":
                        if (at_cpp.startswith("Object<") or at_cpp.startswith("rc<")) and not _header_is_class_borrow_type(list_t, at_cpp, class_names, ref_classes):
                            param_txt = at_cpp + "& " + emitted_vararg
                        else:
                            param_txt = borrow_cpp + " " + emitted_vararg if borrow_cpp == "object" else borrow_cpp + "& " + emitted_vararg
                    else:
                        if _header_is_class_borrow_type(list_t, at_cpp, class_names, ref_classes):
                            param_txt = "const " + borrow_cpp + "& " + emitted_vararg
                        else:
                            param_txt = "const " + borrow_cpp + "& " + emitted_vararg
                    parts.append(param_txt)
                sep = ", "
                fn_lines.append(ret_cpp + " " + name + "(" + sep.join(parts) + ");")
        elif kind == "TypeAlias":
            alias_name = dict_any_get_str(st, "name")
            type_expr = dict_any_get_str(st, "type_expr")
            if alias_name != "" and type_expr != "":
                # Multi-type union → tagged struct
                _parts = [p.strip() for p in type_expr.split("|") if p.strip() != ""]
                _non_none = [p for p in _parts if p != "None"]
                _has_none = len(_non_none) < len(_parts)
                if len(_non_none) >= 2:
                    _struct_lines = _build_tagged_union_struct_lines(alias_name, _non_none, _has_none, ref_classes, class_names)
                    for sl in _struct_lines:
                        alias_lines.append(sl)
                else:
                    cpp_t = _header_cpp_type_from_east(type_expr, ref_classes, class_names)
                    used_types.add(cpp_t)
                    alias_lines.append("using " + alias_name + " = " + cpp_t + ";")
                cpp_to_alias[type_expr] = alias_name
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
    has_std_deque = False
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
        if "::std::deque" in t:
            has_std_deque = True
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
    if has_std_deque:
        includes.append("#include <deque>")
    if has_std_tuple:
        includes.append("#include <tuple>")
    if has_std_optional:
        includes.append("#include <optional>")
    if has_std_umap:
        includes.append("#include <unordered_map>")
    if has_std_uset:
        includes.append("#include <unordered_set>")
    if len(cpp_to_alias) > 0:
        sorted_keys = sorted(cpp_to_alias.keys(), key=len, reverse=True)
        def _apply_alias_subs(lines: list[str]) -> list[str]:
            result: list[str] = []
            for line in lines:
                for cpp_t in sorted_keys:
                    line = line.replace(cpp_t, cpp_to_alias[cpp_t])
                result.append(line)
            return result
        fn_lines = _apply_alias_subs(fn_lines)
        var_lines = _apply_alias_subs(var_lines)
    # inline union struct を .cpp テキストから抽出して class_blocks の前に挿入
    import re as _re
    for m in _re.finditer(r"^(struct _Union_\w+ \{.*?^\};)", cpp_text, _re.MULTILINE | _re.DOTALL):
        union_block = m.group(1)
        if union_block not in class_blocks:
            class_blocks.insert(0, union_block)
    decl_text = join_str_list("\n", class_blocks + class_lines + alias_lines + var_lines + fn_lines)
    raw_include_lines = _extract_cpp_include_lines(cpp_text, output_path)
    include_lines = _filter_cpp_include_lines_for_header(raw_include_lines, decl_text, top_namespace)
    for include_line in include_lines:
        if include_line not in includes:
            includes.append(include_line)
    for include_line in raw_include_lines:
        if include_line in includes:
            continue
        if _header_decl_uses_imported_symbol_include(include_line, decl_text, import_include_symbol_map):
            includes.append(include_line)
    if _header_decl_uses_exception_support(decl_text):
        exceptions_include = '#include "runtime/cpp/core/exceptions.h"'
        if exceptions_include not in includes:
            includes.append(exceptions_include)
    if _header_decl_uses_class_type_support(decl_text):
        runtime_include = '#include "core/py_runtime.h"'
        if runtime_include not in includes:
            includes.append(runtime_include)

    guard = _header_guard_from_path(str(output_path))
    lines: list[str] = []
    lines.append("// AUTO-GENERATED FILE. DO NOT EDIT.")
    lines.append("// source: " + str(source_path))
    lines.append("// generated-by: src/toolchain/emit/cpp/cli.py")
    lines.append("")
    lines.append("#ifndef " + guard)
    lines.append("#define " + guard)
    lines.append("")
    runtime_types_include = _header_runtime_types_include(used_types, len(class_blocks) > 0)
    if runtime_types_include != "":
        lines.append('#include "runtime/cpp/core/' + runtime_types_include + '"')
        lines.append("")
    for include in includes:
        lines.append(include)
    if len(includes) > 0:
        lines.append("")
    ns = top_namespace.strip()
    if ns != "":
        lines.append("namespace " + ns + " {")
        lines.append("")
    # inline union struct 定義を class forward decl の後、struct 定義の前に挿入
    for inline_line in _HEADER_INLINE_UNION_LINES:
        lines.append(inline_line)
    if len(_HEADER_INLINE_UNION_LINES) > 0:
        lines.append("")
    _HEADER_INLINE_UNION_LINES.clear()
    _HEADER_INLINE_UNION_EMITTED.clear()
    for class_line in class_lines:
        lines.append(class_line)
    if len(class_lines) > 0:
        lines.append("")
    for alias_line in alias_lines:
        lines.append(alias_line)
    if len(alias_lines) > 0:
        lines.append("")
    for var_line in var_lines:
        lines.append(var_line)
    if len(var_lines) > 0 and len(class_blocks) > 0:
        lines.append("")
    for class_block in class_blocks:
        for part_line in class_block.splitlines():
            lines.append(part_line)
        lines.append("")
    if (len(var_lines) > 0 or len(class_blocks) > 0) and len(fn_lines) > 0:
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


def _namespace_body_span(lines: list[str], top_namespace: str) -> tuple[int, int]:
    """namespace 本体行範囲（start, end）を返す。未解決時は全体範囲。"""
    if len(lines) == 0:
        return -1, -1
    ns = top_namespace.strip()
    end = len(lines)
    if ns == "":
        start = 0
    else:
        ns_open = "namespace " + ns + " {"
        ns_idx = -1
        for i, raw in enumerate(lines):
            if raw.strip() == ns_open:
                ns_idx = i
                break
        if ns_idx < 0:
            return 0, len(lines)
        start = ns_idx + 1
        depth = _brace_delta_ignoring_literals(lines[ns_idx])
        for i in range(ns_idx + 1, len(lines)):
            depth += _brace_delta_ignoring_literals(lines[i])
            if depth <= 0:
                end = i
                break
    for i in range(start, end):
        if "static void __pytra_module_init()" in lines[i]:
            end = i
            break
    return start, end


def _split_single_class_block(class_lines: list[str]) -> tuple[list[str], list[str]]:
    """単一 class/struct block を宣言部と out-of-class 定義へ分離する。"""
    if len(class_lines) < 2:
        return class_lines, []
    head = class_lines[0]
    tail = class_lines[-1]
    cls_name = _extract_class_name_from_header(head)
    if cls_name == "":
        return class_lines, []
    inner = class_lines[1:-1]
    decl_lines: list[str] = [head]
    def_lines: list[str] = []
    i = 0
    while i < len(inner):
        line = inner[i]
        stripped = line.strip()
        if stripped == "":
            decl_lines.append(line)
            i += 1
            continue
        if _is_class_method_start_line(stripped):
            method_lines, next_i = _collect_brace_block(inner, i)
            decl_sig = _method_decl_signature(method_lines[0])
            if decl_sig == "":
                decl_lines.extend(method_lines)
                i = next_i
                continue
            decl_lines.append(decl_sig)
            method_def = _build_out_of_class_method_def(method_lines, cls_name)
            if len(method_def) > 0:
                if len(def_lines) > 0:
                    def_lines.append("")
                def_lines.extend(method_def)
            i = next_i
            continue
        decl_lines.append(line)
        i += 1
    decl_lines.append(tail)
    return decl_lines, def_lines


def _extract_class_name_from_header(line: str) -> str:
    stripped = line.strip()
    if stripped.startswith("struct "):
        tail = stripped[7:]
    elif stripped.startswith("class "):
        tail = stripped[6:]
    else:
        return ""
    name = ""
    for ch in tail:
        if (ch >= "A" and ch <= "Z") or (ch >= "a" and ch <= "z") or (ch >= "0" and ch <= "9") or ch == "_":
            name += ch
        else:
            break
    return name


def _is_class_method_start_line(stripped: str) -> bool:
    if "{" not in stripped:
        return False
    if not stripped.endswith("{"):
        return False
    if "(" not in stripped or ")" not in stripped:
        return False
    bad_prefixes = ("if ", "for ", "while ", "switch ", "else", "do ", "try", "catch", "namespace ")
    for bad in bad_prefixes:
        if stripped.startswith(bad):
            return False
    return True


def _is_top_level_function_start_line(stripped: str) -> bool:
    if "{" not in stripped:
        return False
    if not stripped.endswith("{"):
        return False
    if "(" not in stripped or ")" not in stripped:
        return False
    bad_prefixes = (
        "if ",
        "for ",
        "while ",
        "switch ",
        "else",
        "do ",
        "try",
        "catch",
        "namespace ",
        "struct ",
        "class ",
    )
    for bad in bad_prefixes:
        if stripped.startswith(bad):
            return False
    return True


def _collect_brace_block(lines: list[str], start_idx: int) -> tuple[list[str], int]:
    out: list[str] = []
    depth = 0
    i = start_idx
    while i < len(lines):
        line = lines[i]
        out.append(line)
        depth += _brace_delta_ignoring_literals(line)
        i += 1
        if depth <= 0:
            break
    return out, i


def _method_decl_signature(first_line: str) -> str:
    prefix = first_line
    pos = prefix.rfind("{")
    if pos < 0:
        return ""
    sig = prefix[:pos].rstrip()
    paren_depth = 0
    closing_paren = -1
    saw_open = False
    i = 0
    while i < len(sig):
        ch = sig[i]
        if ch == "(":
            paren_depth += 1
            saw_open = True
        elif ch == ")":
            if paren_depth > 0:
                paren_depth -= 1
                if saw_open and paren_depth == 0:
                    closing_paren = i
                    break
        i += 1
    if closing_paren >= 0:
        tail = sig[closing_paren + 1 :]
        colon_pos = tail.find(":")
        if colon_pos >= 0:
            sig = sig[: closing_paren + 1]
    return sig.rstrip() + ";"


def _remove_method_decl_only_keywords(sig: str) -> str:
    txt = sig
    for token in [" override", " final"]:
        txt = txt.replace(token, "")
    prefixes = ["virtual ", "inline ", "static ", "constexpr ", "friend "]
    changed = True
    while changed:
        changed = False
        stripped = txt.lstrip()
        lead = txt[: len(txt) - len(stripped)]
        for p in prefixes:
            if stripped.startswith(p):
                stripped = stripped[len(p) :]
                txt = lead + stripped
                changed = True
                break
    return txt


def _build_out_of_class_method_def(method_lines: list[str], cls_name: str) -> list[str]:
    if len(method_lines) == 0:
        return []
    first = method_lines[0]
    last = method_lines[-1].strip()
    if not last.endswith("}"):
        return method_lines
    decl = first
    pos = decl.rfind("{")
    if pos < 0:
        return method_lines
    sig = decl[:pos].rstrip()
    sig = _remove_method_decl_only_keywords(sig)
    paren = sig.find("(")
    if paren < 0:
        return method_lines
    head = sig[:paren].rstrip()
    tail = sig[paren:]
    sp = head.rfind(" ")
    if sp >= 0:
        ret = head[:sp].strip()
        name = head[sp + 1 :].strip()
    else:
        ret = ""
        name = head.strip()
    if name == "":
        return method_lines
    tail = _strip_default_args_from_method_tail(tail)
    def_head = cls_name + "::" + name if ret == "" else (ret + " " + cls_name + "::" + name)
    out: list[str] = []
    out.append("    " + def_head + tail + " {")
    for inner in method_lines[1:-1]:
        if inner.startswith("        "):
            out.append("    " + inner[4:])
        else:
            out.append(inner)
    out.append("    }")
    return out


def strip_cpp_default_args_from_top_level_defs(cpp_text: str, top_namespace: str = "") -> str:
    """top-level 関数定義の既定引数を `.cpp` 用に除去する。"""
    if cpp_text.strip() == "":
        return cpp_text
    lines = cpp_text.splitlines()
    if len(lines) == 0:
        return cpp_text
    start, end = _namespace_body_span(lines, top_namespace)
    if start < 0 or end <= start:
        return cpp_text
    out_lines: list[str] = []
    i = 0
    while i < len(lines):
        if i < start or i >= end:
            out_lines.append(lines[i])
            i += 1
            continue
        raw = lines[i]
        stripped = raw.lstrip()
        if not _is_top_level_function_start_line(stripped):
            out_lines.append(raw)
            i += 1
            continue
        fn_lines, next_i = _collect_brace_block(lines, i)
        if len(fn_lines) == 0:
            i = next_i
            continue
        out_lines.append(_strip_default_args_from_function_def_line(fn_lines[0]))
        out_lines.extend(fn_lines[1:])
        i = next_i
    return join_str_list("\n", out_lines) + ("\n" if cpp_text.endswith("\n") else "")


def _strip_default_args_from_method_tail(tail: str) -> str:
    """`(T a = x, U b = y) ...` から `.cpp` 定義向けに既定引数を除去する。"""
    lp = tail.find("(")
    if lp < 0:
        return tail
    depth = 0
    rp = -1
    i = lp
    while i < len(tail):
        ch = tail[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                rp = i
                break
        i += 1
    if rp < 0:
        return tail
    params_txt = tail[lp + 1 : rp]
    suffix = tail[rp + 1 :]
    parts = _split_top_level_params(params_txt)
    if len(parts) == 0:
        return "()" + suffix
    clean_parts: list[str] = []
    for part in parts:
        p = part.strip()
        if p == "":
            continue
        eq_pos = _find_top_level_equal(p)
        if eq_pos >= 0:
            p = p[:eq_pos].rstrip()
        clean_parts.append(p)
    return "(" + join_str_list(", ", clean_parts) + ")" + suffix


def _strip_default_args_from_function_def_line(line: str) -> str:
    stripped = line.lstrip()
    indent = line[: len(line) - len(stripped)]
    brace_pos = stripped.rfind("{")
    if brace_pos < 0:
        return line
    sig = stripped[:brace_pos].rstrip()
    paren_pos = sig.find("(")
    if paren_pos < 0:
        return line
    head = sig[:paren_pos]
    tail = sig[paren_pos:]
    return indent + head + _strip_default_args_from_method_tail(tail) + " {"


def _split_top_level_params(params_txt: str) -> list[str]:
    out: list[str] = []
    cur_chars: list[str] = []
    ang = 0
    par = 0
    brk = 0
    brc = 0
    i = 0
    while i < len(params_txt):
        ch = params_txt[i]
        if ch == "<":
            ang += 1
        elif ch == ">":
            if ang > 0:
                ang -= 1
        elif ch == "(":
            par += 1
        elif ch == ")":
            if par > 0:
                par -= 1
        elif ch == "[":
            brk += 1
        elif ch == "]":
            if brk > 0:
                brk -= 1
        elif ch == "{":
            brc += 1
        elif ch == "}":
            if brc > 0:
                brc -= 1
        if ch == "," and ang == 0 and par == 0 and brk == 0 and brc == 0:
            out.append("".join(cur_chars))
            cur_chars = []
            i += 1
            continue
        cur_chars.append(ch)
        i += 1
    out.append("".join(cur_chars))
    return out


def _find_top_level_equal(text: str) -> int:
    ang = 0
    par = 0
    brk = 0
    brc = 0
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "<":
            ang += 1
        elif ch == ">":
            if ang > 0:
                ang -= 1
        elif ch == "(":
            par += 1
        elif ch == ")":
            if par > 0:
                par -= 1
        elif ch == "[":
            brk += 1
        elif ch == "]":
            if brk > 0:
                brk -= 1
        elif ch == "{":
            brc += 1
        elif ch == "}":
            if brc > 0:
                brc -= 1
        elif ch == "=" and ang == 0 and par == 0 and brk == 0 and brc == 0:
            return i
        i += 1
    return -1


def _extract_cpp_include_lines(cpp_text: str, output_path: Path) -> list[str]:
    """生成済み C++ からヘッダに必要な include 行を抽出する。"""
    if cpp_text.strip() == "":
        return []
    own_name = str(output_path).replace("\\", "/").split("/")[-1]
    out: list[str] = []
    seen: set[str] = set()
    for raw in cpp_text.splitlines():
        line = raw.strip()
        if not line.startswith("#include "):
            continue
        if own_name != "":
            q0 = line.find("\"")
            q1 = line.rfind("\"")
            if q0 >= 0 and q1 > q0:
                inc_path = line[q0 + 1 : q1].replace("\\", "/")
                if inc_path.split("/")[-1] == own_name:
                    continue
        if line == '#include "core/py_runtime.h"':
            continue
        if line in seen:
            continue
        seen.add(line)
        out.append(line)
    return out


def _filter_cpp_include_lines_for_header(
    include_lines: list[str],
    decl_text: str,
    top_namespace: str,
) -> list[str]:
    """ヘッダ宣言で実使用する include のみを残す。"""
    if len(include_lines) == 0:
        return []
    if decl_text.strip() == "":
        return []
    out: list[str] = []
    ns = top_namespace.strip()
    for include_line in include_lines:
        if _header_decl_uses_include(include_line, decl_text, ns):
            out.append(include_line)
    return out


def _strip_runtime_file_kind_suffix(name: str) -> str:
    """legacy runtime 種別 suffix を剥がす。"""
    if name.endswith(".gen") or name.endswith(".ext"):
        return name[: len(name) - 4]
    return name


def _header_decl_uses_include(include_line: str, decl_text: str, top_namespace: str) -> bool:
    """宣言テキストが当該 include 由来シンボルを参照しているか判定する。"""
    q0 = include_line.find("\"")
    q1 = include_line.rfind("\"")
    if q0 < 0 or q1 <= q0:
        # system include / 非標準形式は保守的に保持
        return True
    inc_path = include_line[q0 + 1 : q1].replace("\\", "/")
    parts = inc_path.split("/")
    if len(parts) == 0:
        return True
    file_name = parts[-1]
    dot = file_name.rfind(".")
    stem = file_name[:dot] if dot >= 0 else file_name
    stem = _strip_runtime_file_kind_suffix(stem)
    if stem == "":
        return True
    user_ns_prefix = "pytra_mod_" + stem
    if user_ns_prefix + "::" in decl_text or user_ns_prefix in decl_text:
        return True

    # runtime/cpp/<bucket>/<module>.gen.h|ext.h または
    # runtime/cpp/{generated,native,pytra}/<bucket>/<module>.h -> namespace prefix を導出
    ns_prefix = ""
    is_runtime_cpp_include = len(parts) >= 4 and parts[0] == "runtime" and parts[1] == "cpp"
    if is_runtime_cpp_include:
        bucket = parts[2]
        module_tail = "/".join(parts[3:])
        if bucket in {"generated", "native", "pytra"}:
            if len(parts) < 5:
                return True
            bucket = parts[3]
            module_tail = "/".join(parts[4:])
        dot2 = module_tail.rfind(".")
        module_tail = module_tail[:dot2] if dot2 >= 0 else module_tail
        module_tail = _strip_runtime_file_kind_suffix(module_tail)
        module_ns = module_tail.replace("/", "::")
        if bucket == "std":
            ns_prefix = "pytra::std::" + module_ns
        elif bucket == "utils":
            ns_prefix = "pytra::utils::" + module_ns
        elif bucket == "compiler":
            ns_prefix = "pytra::compiler::" + module_ns

    if ns_prefix != "":
        if ns_prefix + "::" in decl_text:
            return True
        if ns_prefix in decl_text:
            return True
        if top_namespace != "" and ns_prefix == top_namespace:
            # 同一 namespace 自体の include は宣言だけでは判別しにくいため保持
            return True

    if is_runtime_cpp_include:
        # runtime/cpp 配下は namespace 参照でのみ判定し、識別子名の偶然一致は無視する。
        return False

    # fallback: file stem が識別子として現れるなら保持
    return _contains_identifier_token(decl_text, stem)


def _header_module_local_include_name(module_name: str) -> str:
    module_txt = module_name.strip().replace("\\", "/")
    while module_txt.startswith("."):
        module_txt = module_txt[1:]
    if module_txt == "":
        return ""
    tail = module_txt.split(".")[-1]
    if tail == "__init__":
        return ""
    return tail + ".h"


def _header_import_include_symbol_map(east_module: dict[str, Any]) -> dict[str, set[str]]:
    meta = dict_any_get_dict(east_module, "meta")
    include_symbols: dict[str, set[str]] = {}
    import_symbols = dict_any_get_dict(meta, "import_symbols")
    for local_name, raw_sym in import_symbols.items():
        if not isinstance(local_name, str) or local_name == "":
            continue
        sym = raw_sym if isinstance(raw_sym, dict) else {}
        include_name = _header_module_local_include_name(dict_any_get_str(sym, "module"))
        if include_name == "":
            continue
        bucket = include_symbols.get(include_name)
        if not isinstance(bucket, set):
            bucket = set()
            include_symbols[include_name] = bucket
        bucket.add(local_name)
        export_name = dict_any_get_str(sym, "name")
        if export_name != "":
            bucket.add(export_name)
    import_bindings = dict_any_get_dict_list(meta, "import_bindings")
    for binding in import_bindings:
        include_name = _header_module_local_include_name(dict_any_get_str(binding, "module_id"))
        if include_name == "":
            continue
        bucket = include_symbols.get(include_name)
        if not isinstance(bucket, set):
            bucket = set()
            include_symbols[include_name] = bucket
        local_name = dict_any_get_str(binding, "local_name")
        export_name = dict_any_get_str(binding, "export_name")
        if local_name != "":
            bucket.add(local_name)
        if export_name != "":
            bucket.add(export_name)
    return include_symbols


def _header_decl_uses_imported_symbol_include(
    include_line: str,
    decl_text: str,
    include_symbol_map: dict[str, set[str]],
) -> bool:
    q0 = include_line.find("\"")
    q1 = include_line.rfind("\"")
    if q0 < 0 or q1 <= q0:
        return False
    inc_path = include_line[q0 + 1 : q1].replace("\\", "/")
    include_name = inc_path.split("/")[-1]
    symbols = include_symbol_map.get(include_name)
    if not isinstance(symbols, set) or len(symbols) == 0:
        return False
    for symbol in symbols:
        if _contains_identifier_token(decl_text, symbol):
            return True
    return False


def _header_decl_uses_exception_support(decl_text: str) -> bool:
    for exception_name in (
        "ValueError",
        "RuntimeError",
        "NotImplementedError",
        "TypeError",
        "IndexError",
        "KeyError",
        "SystemExit",
    ):
        if _contains_identifier_token(decl_text, exception_name):
            return True
    return False


def _header_decl_uses_class_type_support(decl_text: str) -> bool:
    return "PYTRA_DECLARE_CLASS_TYPE(" in decl_text or _contains_identifier_token(decl_text, "PYTRA_TID_OBJECT")


def _header_strip_rc_wrapper(cpp_type: str) -> str:
    txt = cpp_type.strip()
    if txt.startswith("Object<") and txt.endswith(">"):
        inner = txt[7:-1].strip()
        if inner != "":
            return inner
    if txt.startswith("rc<") and txt.endswith(">"):
        inner = txt[3:-1].strip()
        if inner != "":
            return inner
    return txt


def _header_is_class_borrow_type(
    east_type: str,
    cpp_type: str,
    class_names: set[str],
    ref_classes: set[str],
) -> bool:
    type_norm = east_type.strip()
    if type_norm in {"", "unknown", "Any", "object", "str", "bytes", "bytearray"}:
        return False
    for prefix in ("list[", "dict[", "set[", "tuple[", "deque[", "::std::optional<"):
        if type_norm.startswith(prefix):
            return False
    if cpp_type.strip().startswith("Object<") or cpp_type.strip().startswith("rc<"):
        return False
    cpp_norm = _header_strip_rc_wrapper(cpp_type)
    if cpp_norm in ref_classes:
        return False
    return cpp_norm in class_names


def _header_borrow_cpp_type(
    east_type: str,
    cpp_type: str,
    class_names: set[str],
    ref_classes: set[str],
) -> str:
    if _header_is_class_borrow_type(east_type, cpp_type, class_names, ref_classes):
        return _header_strip_rc_wrapper(cpp_type)
    return cpp_type


def _contains_identifier_token(text: str, token: str) -> bool:
    """`token` が識別子境界で現れるかを判定する。"""
    if token == "":
        return False
    i = 0
    n = len(text)
    m = len(token)
    while i + m <= n:
        if text[i : i + m] == token:
            left_ok = i == 0 or not _is_ident_char(text[i - 1])
            right_ok = i + m == n or not _is_ident_char(text[i + m])
            if left_ok and right_ok:
                return True
        i += 1
    return False


def _is_ident_char(ch: str) -> bool:
    return (ch >= "A" and ch <= "Z") or (ch >= "a" and ch <= "z") or (ch >= "0" and ch <= "9") or ch == "_"


def _extract_class_names_from_blocks(class_blocks: list[str]) -> set[str]:
    """抽出済み class/struct block からクラス名集合を得る。"""
    out: set[str] = set()
    for block in class_blocks:
        lines = block.splitlines()
        if len(lines) == 0:
            continue
        head = lines[0].strip()
        if head.startswith("struct "):
            tail = head[7:]
        elif head.startswith("class "):
            tail = head[6:]
        else:
            continue
        name = ""
        for ch in tail:
            if (ch >= "A" and ch <= "Z") or (ch >= "a" and ch <= "z") or (ch >= "0" and ch <= "9") or ch == "_":
                name += ch
            else:
                break
        if name != "":
            out.add(name)
    return out


def _extract_cpp_class_blocks(cpp_text: str, top_namespace: str) -> list[str]:
    """生成済み C++ から top-level class/struct 本文を抽出する。"""
    if cpp_text.strip() == "":
        return []
    lines = cpp_text.splitlines()
    if len(lines) == 0:
        return []
    start = 0
    end = len(lines)
    ns = top_namespace.strip()
    if ns != "":
        ns_open = "namespace " + ns + " {"
        ns_idx = -1
        for i, raw in enumerate(lines):
            if raw.strip() == ns_open:
                ns_idx = i
                break
        if ns_idx < 0:
            return []
        start = ns_idx + 1
        depth = _brace_delta_ignoring_literals(lines[ns_idx])
        for i in range(ns_idx + 1, len(lines)):
            depth += _brace_delta_ignoring_literals(lines[i])
            if depth <= 0:
                end = i
                break
    for i in range(start, end):
        if "static void __pytra_module_init()" in lines[i]:
            end = i
            break
    blocks: list[str] = []
    i = start
    while i < end:
        raw = lines[i]
        stripped = raw.lstrip()
        if not (stripped.startswith("struct ") or stripped.startswith("class ")):
            i += 1
            continue
        if "{" not in raw:
            i += 1
            continue
        depth = _brace_delta_ignoring_literals(raw)
        block_lines: list[str] = [raw]
        i += 1
        while i < end:
            line = lines[i]
            block_lines.append(line)
            depth += _brace_delta_ignoring_literals(line)
            if depth <= 0 and line.strip().endswith("};"):
                i += 1
                break
            i += 1
        blocks.append(join_str_list("\n", block_lines))
    return blocks


def _brace_delta_ignoring_literals(line: str) -> int:
    """文字列リテラルやコメント中の `{` `}` を無視して brace 差分を返す。"""
    depth = 0
    in_single = False
    in_double = False
    escaped = False
    i = 0
    while i < len(line):
        ch = line[i]
        nxt = line[i + 1] if i + 1 < len(line) else ""
        if escaped:
            escaped = False
            i += 1
            continue
        if in_single:
            if ch == "\\":
                escaped = True
            elif ch == "'":
                in_single = False
            i += 1
            continue
        if in_double:
            if ch == "\\":
                escaped = True
            elif ch == "\"":
                in_double = False
            i += 1
            continue
        if ch == "/" and nxt == "/":
            break
        if ch == "/" and nxt == "*":
            break
        if ch == "'":
            in_single = True
        elif ch == "\"":
            in_double = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        i += 1
    return depth


def _header_runtime_types_include(used_types: set[str], has_class_blocks: bool) -> str:
    """生成ヘッダが必要とする最小 runtime 型ヘッダ名を返す。"""
    if has_class_blocks:
        return "py_runtime.h"
    scalar_markers = (
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
    )
    rich_markers = (
        "str",
        "bytes",
        "bytearray",
        "object",
        "list<",
        "dict<",
        "set<",
        "Object<",
    )
    needs_scalar = False
    needs_rich = False
    for t in used_types:
        txt = t.strip()
        if txt in {"", "void", "bool"}:
            continue
        for marker in rich_markers:
            if marker in txt:
                needs_rich = True
                break
        if needs_rich:
            break
        for marker in scalar_markers:
            if marker in txt:
                needs_scalar = True
                break
    if needs_rich:
        return "py_types.h"
    if needs_scalar:
        return "py_scalar_types.h"
    return ""


def _pytra_tid_for_east_type(east_type: str) -> str:
    """EAST 型名から PYTRA_TID 定数名を返す。"""
    t = east_type.strip()
    if t == "None":
        return "PYTRA_TID_NONE"
    if t == "bool":
        return "PYTRA_TID_BOOL"
    if t in {"int", "int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64"}:
        return "PYTRA_TID_INT"
    if t in {"float", "float32", "float64"}:
        return "PYTRA_TID_FLOAT"
    if t == "str":
        return "PYTRA_TID_STR"
    if t.startswith("list[") or t == "list":
        return "PYTRA_TID_LIST"
    if t.startswith("dict[") or t == "dict":
        return "PYTRA_TID_DICT"
    if t.startswith("set[") or t == "set":
        return "PYTRA_TID_SET"
    return t + "::PYTRA_TYPE_ID"


def _tagged_union_field_name(east_type: str) -> str:
    """EAST 型名からフィールド名を生成する。"""
    return east_type.lower().replace("[", "_").replace("]", "").replace(",", "_").replace(" ", "") + "_val"


# inline union struct 定義の蓄積用グローバル
_HEADER_INLINE_UNION_EMITTED: set[str] = set()
_HEADER_INLINE_UNION_LINES: list[str] = []


def _build_tagged_union_struct_lines(
    name: str, non_none: list[str], has_none: bool,
    ref_classes: set[str], class_names: set[str],
) -> list[str]:
    """type X = A | B | ... から C++ tagged struct 定義行を生成する。"""
    lines: list[str] = []
    tag_entries: list[tuple[str, str, str]] = []  # (tid_expr, cpp_type, field_name)
    for p in non_none:
        cpp_t = _header_cpp_type_from_east(p, ref_classes, class_names)
        tid_expr = _pytra_tid_for_east_type(p)
        field_name = _tagged_union_field_name(p)
        if name in cpp_t or p == name:
            if cpp_t.startswith("list<"):
                cpp_t = "Object<" + cpp_t + ">"
            elif cpp_t.startswith("dict<"):
                cpp_t = "Object<" + cpp_t + ">"
        tag_entries.append((tid_expr, cpp_t, field_name))
    lines.append("struct " + name + " {")
    lines.append("    pytra_type_id tag;")
    for _, cpp_t, field_name in tag_entries:
        lines.append("    " + cpp_t + " " + field_name + ";")
    lines.append("")
    default_tid = "PYTRA_TID_NONE" if has_none else tag_entries[0][0]
    lines.append("    " + name + "() : tag(" + default_tid + ") {}")
    for tid_expr, cpp_t, field_name in tag_entries:
        lines.append("    " + name + "(const " + cpp_t + "& v) : tag(" + tid_expr + "), " + field_name + "(v) {}")
    if has_none:
        lines.append("    " + name + "(::std::monostate) : tag(PYTRA_TID_NONE) {}")
    lines.append("};")
    lines.append("")
    return lines


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
        return "Object<" + t + ">"
    if t in class_names:
        return t
    prim: dict[str, str] = {
        "int": "int64",
        "float": "float64",
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
        "Path": "pytra::std::pathlib::Path",
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
        # 一般ユニオン（2型以上）→ tagged struct
        has_none = len(non_none) < len(parts)
        name_parts: list[str] = []
        for p in non_none:
            name_parts.append(p.replace("[", "_").replace("]", "").replace(",", "_").replace(" ", ""))
        if has_none:
            name_parts.append("None")
        struct_name = "_Union_" + "_".join(name_parts)
        # inline union struct 定義をグローバルに蓄積
        if struct_name not in _HEADER_INLINE_UNION_EMITTED:
            _HEADER_INLINE_UNION_EMITTED.add(struct_name)
            _HEADER_INLINE_UNION_LINES.extend(
                _build_tagged_union_struct_lines(struct_name, non_none, has_none, ref_classes, class_names)
            )
        return struct_name
    if t.startswith("list[") and t.endswith("]"):
        inner = t[5:-1].strip()
        return "list<" + _header_cpp_type_from_east(inner, ref_classes, class_names) + ">"
    if t.startswith("deque[") and t.endswith("]"):
        inner = t[6:-1].strip()
        return "::std::deque<" + _header_cpp_type_from_east(inner, ref_classes, class_names) + ">"
    if t.startswith("set[") and t.endswith("]"):
        inner = t[4:-1].strip()
        return "set<" + _header_cpp_type_from_east(inner, ref_classes, class_names) + ">"
    if t.startswith("dict[") and t.endswith("]"):
        inner = split_type_args(t[5:-1].strip())
        if len(inner) == 2:
            return "dict<" + _header_cpp_type_from_east(inner[0], ref_classes, class_names) + ", " + _header_cpp_type_from_east(inner[1], ref_classes, class_names) + ">"
        return "dict<str, object>"
    if t.startswith("tuple[") and t.endswith("]"):
        homogeneous_tuple_item_t = _header_homogeneous_tuple_ellipsis_item_type(t)
        if homogeneous_tuple_item_t != "":
            return "list<" + _header_cpp_type_from_east(homogeneous_tuple_item_t, ref_classes, class_names) + ">"
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
            return "Object<" + ns_t + ">"
        return ns_t
    return t


def _header_is_concrete_type_for_typed_list(east_t: str) -> bool:
    txt = east_t.strip()
    if txt in {"", "unknown", "Any", "object", "None"}:
        return False
    parts_union = split_top_level_union(txt)
    if len(parts_union) > 1:
        for part in parts_union:
            if not _header_is_concrete_type_for_typed_list(part):
                return False
        return True
    if txt.startswith("list[") and txt.endswith("]"):
        return _header_is_concrete_type_for_typed_list(txt[5:-1].strip())
    if txt.startswith("tuple[") and txt.endswith("]"):
        for part in split_type_args(txt[6:-1].strip()):
            if not _header_is_concrete_type_for_typed_list(part):
                return False
        return True
    if txt.startswith("dict[") and txt.endswith("]"):
        inner = split_type_args(txt[5:-1].strip())
        if len(inner) != 2:
            return False
        return _header_is_concrete_type_for_typed_list(inner[0]) and _header_is_concrete_type_for_typed_list(inner[1])
    if txt.startswith("set[") and txt.endswith("]"):
        return _header_is_concrete_type_for_typed_list(txt[4:-1].strip())
    return True


def _header_cpp_signature_type_from_east(
    east_t: str,
    ref_classes: set[str],
    class_names: set[str],
    *,
    runtime_abi_mode: str = "default",
    pyobj_ref_lists: bool = False,
) -> str:
    txt = east_t.strip()
    use_ref_first_lists = pyobj_ref_lists and runtime_abi_mode not in {"value", "value_mut", "value_readonly"}
    if use_ref_first_lists and txt.startswith("list[") and txt.endswith("]") and _header_is_concrete_type_for_typed_list(txt[5:-1].strip()):
        value_cpp = _header_cpp_type_from_east(txt, ref_classes, class_names)
        if value_cpp != "bytearray":
            return "Object<" + value_cpp + ">"
    return _header_cpp_type_from_east(txt, ref_classes, class_names)


def _header_runtime_abi_meta(fn_node: dict[str, Any]) -> dict[str, Any]:
    meta = dict_any_get_dict(fn_node, "meta")
    runtime_abi = dict_any_get_dict(meta, "runtime_abi_v1")
    schema_version = runtime_abi.get("schema_version")
    if not isinstance(schema_version, int) or int(schema_version) != 1:
        return {}
    return runtime_abi


def _header_runtime_abi_arg_mode(fn_node: dict[str, Any], arg_name: str) -> str:
    runtime_abi = _header_runtime_abi_meta(fn_node)
    args = dict_any_get_dict(runtime_abi, "args")
    mode = dict_any_get_str(args, arg_name, "default")
    return mode if mode != "" else "default"


def _header_runtime_abi_ret_mode(fn_node: dict[str, Any]) -> str:
    runtime_abi = _header_runtime_abi_meta(fn_node)
    mode = dict_any_get_str(runtime_abi, "ret", "default")
    return mode if mode != "" else "default"


def _header_guard_from_path(path: str) -> str:
    """ヘッダパスから include guard を生成する。"""
    src = path.replace("\\", "/")
    prefix0 = "src/runtime/cpp/"
    prefix00 = "runtime/cpp/"
    if src.startswith(prefix0):
        src = src[len(prefix0) :]
    elif src.startswith(prefix00):
        src = src[len(prefix00) :]
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
        return "pytra::std::pathlib::Path(\"\")"
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
        elif ch == "\b":
            out_chars.append("\\b")
        elif ch == "\f":
            out_chars.append("\\f")
        elif ch == "\n":
            out_chars.append("\\n")
        elif ch == "\r":
            out_chars.append("\\r")
        elif ch == "\t":
            out_chars.append("\\t")
        else:
            out_chars.append(ch)
    return "\"" + "".join(out_chars) + "\""


def _header_render_default_expr(
    node: dict[str, Any],
    east_target_t: str,
    *,
    pyobj_ref_lists: bool = False,
    ref_classes: set[str] | None = None,
    class_names: set[str] | None = None,
) -> str:
    """EAST の既定値ノードを C++ ヘッダ宣言用の式文字列へ変換する。"""
    ref_class_names = ref_classes if ref_classes is not None else set()
    known_class_names = class_names if class_names is not None else set()
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
        homogeneous_tuple_item_t = _header_homogeneous_tuple_ellipsis_item_type(east_target_t)
        if len(elems) == 0 and homogeneous_tuple_item_t == "":
            return "::std::tuple<>{}"
        parts: list[str] = []
        elem_target_t = homogeneous_tuple_item_t if homogeneous_tuple_item_t != "" else "Any"
        for e in elems:
            txt = _header_render_default_expr(
                e,
                elem_target_t,
                pyobj_ref_lists=pyobj_ref_lists,
                ref_classes=ref_class_names,
                class_names=known_class_names,
            )
            if txt == "":
                return ""
            parts.append(txt)
        if len(parts) == 0:
            return ""
        if homogeneous_tuple_item_t != "":
            return (
                _header_cpp_type_from_east(east_target_t, ref_class_names, known_class_names)
                + "{"
                + join_str_list(", ", parts)
                + "}"
            )
        return "::std::make_tuple(" + join_str_list(", ", parts) + ")"
    if kind == "List":
        elems = dict_any_get_dict_list(node, "elements")
        if len(elems) == 0:
            txt = east_target_t.strip()
            if txt.startswith("list[") and txt.endswith("]"):
                default_txt = _header_cpp_type_from_east(txt, set(), set()) + "{}"
                sig_t = _header_cpp_signature_type_from_east(txt, set(), set(), pyobj_ref_lists=True)
                if pyobj_ref_lists and (sig_t.startswith("Object<") or sig_t.startswith("rc<")):
                    return "make_object_from_value(" + default_txt + ")"
                return default_txt
        return ""
    if kind == "Dict":
        entries = dict_any_get_dict_list(node, "entries")
        if len(entries) == 0:
            txt = east_target_t.strip()
            if txt.startswith("dict[") and txt.endswith("]"):
                return _header_cpp_type_from_east(txt, set(), set()) + "{}"
        return ""
    if kind == "Set":
        elems = dict_any_get_dict_list(node, "elements")
        if len(elems) == 0:
            txt = east_target_t.strip()
            if txt.startswith("set[") and txt.endswith("]"):
                return _header_cpp_type_from_east(txt, set(), set()) + "{}"
        return ""
    _ = east_target_t
    return ""
