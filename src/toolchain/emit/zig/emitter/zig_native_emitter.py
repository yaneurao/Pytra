"""EAST3 -> Zig native emitter (minimal skeleton)."""

from __future__ import annotations

from typing import Any

from toolchain.emit.common.emitter.code_emitter import (
    CodeEmitter,
    reject_backend_homogeneous_tuple_ellipsis_type_exprs,
    reject_backend_typed_vararg_signatures,
)

# CodeEmitter のユーティリティを standalone で使うためのインスタンス
_code_emitter_utils = CodeEmitter.__new__(CodeEmitter)

from toolchain.frontends.runtime_symbol_index import (
    canonical_runtime_module_id,
    lookup_runtime_module_symbols,
    lookup_runtime_symbol_doc,
    resolve_import_binding_doc,
)


_ZIG_KEYWORDS = {
    "addrspace", "align", "allowzero", "and", "anyframe", "anytype",
    "asm", "async", "await", "break", "callconv", "catch", "comptime",
    "const", "continue", "defer", "else", "enum", "errdefer", "error",
    "export", "extern", "false", "fn", "for", "if", "inline",
    "linksection", "noalias", "nosuspend", "null", "opaque", "or",
    "orelse", "packed", "pub", "resume", "return", "struct", "suspend",
    "switch", "test", "threadlocal", "true", "try", "undefined",
    "union", "unreachable", "var", "volatile", "while",
}
# Zig std built-in type/namespace names that user-defined identifiers should
# not shadow.  Names used by the Pytra runtime (print, math, etc.) are
# excluded since _safe_ident cannot distinguish user vs runtime references.
_ZIG_RESERVED_BUILTINS = {
    "std",
    "i8", "i16", "i32", "i64", "i128",
    "u8", "u16", "u32", "u64", "u128",
    "f16", "f32", "f64", "f128",
    "usize", "isize", "bool",
    "void", "anyerror",
    "allocator", "ArrayList", "HashMap",
    "mem", "fmt", "debug", "heap", "io", "os", "fs",
    "testing", "log",
}
_NIL_FREE_DECL_TYPES = {"int", "int64", "float", "float64", "bool", "str"}
_COMPILETIME_STD_IMPORT_SYMBOLS = {"abi", "template", "extern"}


def _safe_ident(name: Any, fallback: str = "value") -> str:
    if not isinstance(name, str) or name == "":
        return fallback
    chars: list[str] = []
    i = 0
    while i < len(name):
        ch = name[i]
        if ch.isalnum() or ch == "_":
            chars.append(ch)
        else:
            chars.append("_")
        i += 1
    out = "".join(chars)
    if out == "":
        out = fallback
    if out[0].isdigit():
        out = "_" + out
    if out == "_":
        out = "_unused"
    if out in _ZIG_KEYWORDS:
        out = "@\"" + out + "\""
    while out in _ZIG_RESERVED_BUILTINS:
        out = out + "_"
    return out


def _relative_import_module_path(module_id: str) -> str:
    parts = [
        _safe_ident(part, "module")
        for part in module_id.lstrip(".").split(".")
        if part != ""
    ]
    return ".".join(parts)


def _collect_relative_import_name_aliases(east_doc: dict[str, Any]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    body_any = east_doc.get("body")
    body = body_any if isinstance(body_any, list) else []
    i = 0
    while i < len(body):
        stmt = body[i]
        if not isinstance(stmt, dict):
            i += 1
            continue
        sd: dict[str, Any] = stmt
        if sd.get("kind") != "ImportFrom":
            i += 1
            continue
        module_any = sd.get("module")
        module_id = module_any if isinstance(module_any, str) else ""
        level_any = sd.get("level")
        level = level_any if isinstance(level_any, int) else 0
        if level <= 0 and not module_id.startswith("."):
            i += 1
            continue
        module_path = _relative_import_module_path(module_id)
        names_any = sd.get("names")
        names = names_any if isinstance(names_any, list) else []
        j = 0
        while j < len(names):
            ent = names[j]
            if not isinstance(ent, dict):
                j += 1
                continue
            name_any = ent.get("name")
            name = name_any if isinstance(name_any, str) else ""
            if name == "":
                j += 1
                continue
            if name == "*":
                raise RuntimeError(
                    "zig native emitter: unsupported relative import form: wildcard import"
                )
            asname_any = ent.get("asname")
            local_name = asname_any if isinstance(asname_any, str) and asname_any != "" else name
            local_rendered = _safe_ident(local_name, "value")
            target_name = _safe_ident(name, "value")
            aliases[local_rendered] = (
                target_name if module_path == "" else module_path + "." + target_name
            )
            j += 1
        i += 1
    return aliases


def _zig_string(text: str) -> str:
    out = text.replace("\\", "\\\\")
    out = out.replace('"', '\\"')
    out = out.replace("\t", "\\t")
    out = out.replace("\r", "\\r")
    out = out.replace("\n", "\\n")
    return '"' + out + '"'


def _binop_precedence(op: str) -> int:
    """Zig 演算子優先順位（高い値 = 高い優先度）。"""
    if op in {"Mult", "Div", "FloorDiv", "Mod"}:
        return 6
    if op in {"Add", "Sub"}:
        return 5
    if op in {"LShift", "RShift"}:
        return 4
    if op == "BitAnd":
        return 3
    if op == "BitXor":
        return 2
    if op == "BitOr":
        return 1
    if op == "Pow":
        return 7
    return 0


def _binop_symbol(op: str) -> str:
    if op == "Add":
        return "+"
    if op == "Sub":
        return "-"
    if op == "Mult":
        return "*"
    if op == "Div":
        return "/"
    if op == "FloorDiv":
        return "/@"
    if op == "Mod":
        return "%"
    if op == "Pow":
        return "**"
    if op == "LShift":
        return "<<"
    if op == "RShift":
        return ">>"
    if op == "BitOr":
        return "|"
    if op == "BitXor":
        return "^"
    if op == "BitAnd":
        return "&"
    raise RuntimeError("lang=zig unsupported binop: " + op)


def _cmp_symbol(op: str) -> str:
    if op == "Eq":
        return "=="
    if op == "NotEq":
        return "!="
    if op == "Lt":
        return "<"
    if op == "LtE":
        return "<="
    if op == "Gt":
        return ">"
    if op == "GtE":
        return ">="
    if op == "Is":
        return "=="
    if op == "IsNot":
        return "!="
    raise RuntimeError("lang=zig unsupported compare op: " + op)


def _runtime_module_symbol_names(runtime_module_id: str) -> tuple[str, ...]:
    symbols = lookup_runtime_module_symbols(runtime_module_id)
    if symbols is None:
        return ()
    return tuple(s.name for s in symbols)


def _runtime_symbol_call_adapter_kind(runtime_module_id: str, runtime_symbol: str) -> str:
    doc = lookup_runtime_symbol_doc(runtime_module_id, runtime_symbol)
    if doc is None:
        return ""
    return doc.call_adapter_kind


def _runtime_symbol_semantic_tag(runtime_module_id: str, runtime_symbol: str) -> str:
    doc = lookup_runtime_symbol_doc(runtime_module_id, runtime_symbol)
    if doc is None:
        return ""
    return doc.semantic_tag


def _is_math_runtime_symbol(runtime_module_id: str, runtime_symbol: str) -> bool:
    tag = _runtime_symbol_semantic_tag(runtime_module_id, runtime_symbol)
    return tag == "math"


def _is_perf_counter_runtime_symbol(runtime_module_id: str, runtime_symbol: str) -> bool:
    return runtime_symbol == "perf_counter" or runtime_symbol == "perf_counter_ns"


def _is_compile_time_std_import_symbol(module_id: str, symbol: str) -> bool:
    return symbol in _COMPILETIME_STD_IMPORT_SYMBOLS


def _pascal_symbol_name(name: str) -> str:
    parts = name.split("_")
    out_parts: list[str] = []
    for part in parts:
        if part == "":
            continue
        out_parts.append(part[0].upper() + part[1:])
    return "".join(out_parts)


def _runtime_symbol_alias_expr(runtime_module_id: str, runtime_symbol: str) -> str:
    doc = lookup_runtime_symbol_doc(runtime_module_id, runtime_symbol)
    if doc is None:
        return "__pytra_" + runtime_symbol
    adapter = doc.call_adapter_kind
    if adapter == "direct":
        return "__pytra_" + runtime_symbol
    if adapter == "method":
        return "__pytra_" + runtime_symbol
    return "__pytra_" + runtime_symbol


class ZigNativeEmitter:
    def __init__(self, east_doc: dict[str, Any], is_submodule: bool = False) -> None:
        if not isinstance(east_doc, dict):
            raise RuntimeError("lang=zig invalid east document: root must be dict")
        ed: dict[str, Any] = east_doc
        kind = ed.get("kind")
        if kind != "Module":
            raise RuntimeError("lang=zig invalid root kind: " + str(kind))
        if ed.get("east_stage") != 3:
            raise RuntimeError("lang=zig unsupported east_stage: " + str(ed.get("east_stage")))
        self.east_doc = east_doc
        self.is_submodule = is_submodule
        self.lines: list[str] = []
        self.indent = 0
        self.tmp_seq = 0
        self.class_names: set[str] = set()
        self.imported_modules: set[str] = set()
        self.function_names: set[str] = set()
        self.relative_import_name_aliases: dict[str, str] = {}
        self.current_class_name: str = ""
        self.current_class_base_name: str = ""
        self._dataclass_names: set[str] = set()
        self._dataclass_fields: dict[str, list[str]] = {}
        self._classes_with_init: set[str] = set()
        self._classes_with_del: set[str] = set()
        self._classes_with_mut_method: set[str] = set()
        self._class_base: dict[str, str] = {}
        self._class_methods: dict[str, set[str]] = {}
        self._static_fields: dict[str, list[tuple[str, str, str]]] = {}  # cls -> [(field, type, default)]
        self._vtable_root: dict[str, str] = {}  # cls -> vtable root class
        self._vtable_methods: dict[str, list[str]] = {}  # root cls -> [method names]
        self._class_return_types: dict[str, dict[str, str]] = {}  # cls -> {method: return_type}
        self._local_type_stack: list[dict[str, str]] = []
        self._ref_var_stack: list[set[str]] = []
        self._local_var_stack: list[set[str]] = []
        self._mutated_var_stack: list[set[str]] = []
        self._hoisted_var_names: set[str] = set()
        # タプル型の名前付き typedef: normalized_type → zig_name
        self._tuple_typedefs: dict[str, str] = {}
        self._tuple_typedef_seq: int = 0
        # Class context for parameter shadowing detection
        self._current_class_name: str = ""
        self._current_class_methods: list[dict[str, Any]] = []
        # Parameter rename stack: original_name → zig_name (for shadowing avoidance)
        self._param_rename_stack: list[dict[str, str]] = []

    def _zig_tuple_type(self, normalized_tuple_type: str) -> str:
        """タプル型を名前付き型として返す。初出時に typedef を登録する。"""
        if normalized_tuple_type in self._tuple_typedefs:
            return self._tuple_typedefs[normalized_tuple_type]
        parts = self._split_generic(normalized_tuple_type[6:-1])
        inner_types = [self._zig_type(p.strip()) for p in parts]
        name = "Tuple" + str(self._tuple_typedef_seq)
        self._tuple_typedef_seq += 1
        self._tuple_typedefs[normalized_tuple_type] = name
        return name

    def _emit_tuple_typedefs(self) -> None:
        """登録されたタプル typedef をモジュール先頭に出力する。"""
        for norm_type, name in self._tuple_typedefs.items():
            parts = self._split_generic(norm_type[6:-1])
            inner_types = [self._zig_type(p.strip()) for p in parts]
            fields = ", ".join("_" + str(i) + ": " + zt for i, zt in enumerate(inner_types))
            self._emit_line("const " + name + " = struct { " + fields + " };")

    def _current_type_map(self) -> dict[str, str]:
        if len(self._local_type_stack) == 0:
            return {}
        return self._local_type_stack[-1]

    def _current_ref_vars(self) -> set[str]:
        if len(self._ref_var_stack) == 0:
            return set()
        return self._ref_var_stack[-1]

    def _current_local_vars(self) -> set[str]:
        if len(self._local_var_stack) == 0:
            return set()
        return self._local_var_stack[-1]

    def _current_mutated_vars(self) -> set[str]:
        if len(self._mutated_var_stack) == 0:
            return set()
        return self._mutated_var_stack[-1]

    def _scan_mutated_vars(self, body_any: Any) -> set[str]:
        """関数本体をスキャンし、再代入・AugAssign される変数名を集める。"""
        mutated: set[str] = set()
        body = self._dict_list(body_any)
        for stmt in body:
            kind = stmt.get("kind")
            if kind == "AugAssign":
                target = stmt.get("target")
                if isinstance(target, dict) and target.get("kind") == "Name":
                    mutated.add(_safe_ident(target.get("id"), ""))
            elif kind == "Assign":
                # Subscript 代入: dict[key] = val / list[idx] = val → owner は mutated
                target = stmt.get("target")
                if isinstance(target, dict) and target.get("kind") == "Subscript":
                    sub_val = target.get("value")
                    if isinstance(sub_val, dict) and sub_val.get("kind") == "Name":
                        mutated.add(_safe_ident(sub_val.get("id"), ""))
            elif kind == "If":
                mutated.update(self._scan_mutated_vars(stmt.get("body")))
                mutated.update(self._scan_mutated_vars(stmt.get("orelse")))
            elif kind == "ForCore":
                tp = stmt.get("target_plan")
                if isinstance(tp, dict) and tp.get("kind") == "NameTarget":
                    mutated.add(_safe_ident(tp.get("id"), ""))
                mutated.update(self._scan_mutated_vars(stmt.get("body")))
            elif kind == "ForRange":
                target = stmt.get("target")
                if isinstance(target, dict) and target.get("kind") == "Name":
                    mutated.add(_safe_ident(target.get("id"), ""))
                mutated.update(self._scan_mutated_vars(stmt.get("body")))
            elif kind == "While":
                mutated.update(self._scan_mutated_vars(stmt.get("body")))
            elif kind == "Swap":
                left = stmt.get("left")
                right = stmt.get("right")
                if isinstance(left, dict) and left.get("kind") == "Name":
                    mutated.add(_safe_ident(left.get("id"), ""))
                if isinstance(right, dict) and right.get("kind") == "Name":
                    mutated.add(_safe_ident(right.get("id"), ""))
            elif kind == "Try":
                mutated.update(self._scan_mutated_vars(stmt.get("body")))
                handlers = stmt.get("handlers")
                if isinstance(handlers, list):
                    for h in handlers:
                        if isinstance(h, dict):
                            mutated.update(self._scan_mutated_vars(h.get("body")))
                mutated.update(self._scan_mutated_vars(stmt.get("finalbody")))
        # AnnAssign で宣言された変数名を集め、Assign で再代入されるものを mutated に追加
        # トップレベルで宣言された変数を集め、ネスト内での再代入を検出
        declared: set[str] = set()
        for stmt in body:
            kind = stmt.get("kind")
            if kind in {"AnnAssign", "Assign"}:
                target = stmt.get("target")
                if isinstance(target, dict) and target.get("kind") == "Name":
                    declared.add(_safe_ident(target.get("id"), ""))
        # 同一スコープ内の Assign 重複（2回目は再代入）+ ネスト内の再代入を検出
        assign_seen: set[str] = set()
        for stmt in body:
            kind = stmt.get("kind")
            if kind in {"Assign", "AnnAssign"}:
                target = stmt.get("target")
                if isinstance(target, dict) and target.get("kind") == "Name":
                    n = _safe_ident(target.get("id"), "")
                    if n in assign_seen:
                        mutated.add(n)
                    assign_seen.add(n)
            elif kind == "ForCore":
                self._scan_reassign_to_declared(stmt.get("body"), declared, mutated)
            elif kind == "ForRange":
                self._scan_reassign_to_declared(stmt.get("body"), declared, mutated)
            elif kind == "While":
                self._scan_reassign_to_declared(stmt.get("body"), declared, mutated)
            elif kind == "If":
                self._scan_reassign_to_declared(stmt.get("body"), declared, mutated)
                self._scan_reassign_to_declared(stmt.get("orelse"), declared, mutated)
        return mutated

    def _scan_reassign_to_declared(self, body_any: Any, declared: set[str], mutated: set[str]) -> None:
        """declared に含まれる変数名への Assign/AugAssign をネスト含めて検出する。"""
        body = self._dict_list(body_any)
        for stmt in body:
            kind = stmt.get("kind")
            if kind == "Assign":
                target = stmt.get("target")
                if isinstance(target, dict) and target.get("kind") == "Name":
                    n = _safe_ident(target.get("id"), "")
                    if n in declared:
                        mutated.add(n)
                targets = stmt.get("targets")
                if isinstance(targets, list):
                    for t in targets:
                        if isinstance(t, dict) and t.get("kind") == "Name":
                            n = _safe_ident(t.get("id"), "")
                            if n in declared:
                                mutated.add(n)
            elif kind == "AugAssign":
                target = stmt.get("target")
                if isinstance(target, dict) and target.get("kind") == "Name":
                    n = _safe_ident(target.get("id"), "")
                    if n in declared:
                        mutated.add(n)
            elif kind == "If":
                self._scan_reassign_to_declared(stmt.get("body"), declared, mutated)
                self._scan_reassign_to_declared(stmt.get("orelse"), declared, mutated)
            elif kind == "ForCore":
                self._scan_reassign_to_declared(stmt.get("body"), declared, mutated)
            elif kind == "ForRange":
                self._scan_reassign_to_declared(stmt.get("body"), declared, mutated)
            elif kind == "While":
                self._scan_reassign_to_declared(stmt.get("body"), declared, mutated)
            elif kind == "Try":
                self._scan_reassign_to_declared(stmt.get("body"), declared, mutated)

    def _is_var_mutated(self, name: str) -> bool:
        return name in self._current_mutated_vars()

    def _needs_var_for_type(self, decl_type: str) -> bool:
        """型が mutable メソッドを持つクラスなら var が必要（ポインタ型では不要）。"""
        t = self._normalize_type(decl_type)
        # dict 型は put で mutation するが、read-only 使用もある
        # _is_var_mutated で Subscript 代入を検出する方が正確
        # ポインタ型（*ClassName）なら const でもフィールド変更可能
        if t in self.class_names:
            return False
        return t in self._classes_with_mut_method

    def _body_uses_name(self, body_any: Any, name: str) -> bool:
        """body 内で指定した名前が Name ノードの id として参照されているか判定する。"""
        if not isinstance(body_any, list):
            return False
        return self._node_uses_name(body_any, name)

    def _node_uses_name(self, node: Any, name: str) -> bool:
        """AST ノードツリー内で Name.id == name の参照を検索する。"""
        if isinstance(node, dict):
            nd: dict[str, Any] = node
            if nd.get("kind") == "Name" and nd.get("id") == name:
                return True
            for key, val in nd.items():
                # Skip non-structural fields
                if key in {"repr", "source_span", "resolved_type", "semantic_tag",
                           "runtime_call", "resolved_runtime_call", "runtime_module_id",
                           "runtime_symbol", "escape_summary", "type_expr_summary_v1"}:
                    continue
                if self._node_uses_name(val, name):
                    return True
            return False
        if isinstance(node, list):
            for item in node:
                if self._node_uses_name(item, name):
                    return True
        return False

    def _strip_dead_branches(self, body_any: Any) -> list[dict[str, Any]]:
        """body から dead branch (if false / isinstance) を除去したリストを返す。"""
        if not isinstance(body_any, list):
            return []
        result: list[dict[str, Any]] = []
        for stmt in body_any:
            if not isinstance(stmt, dict):
                continue
            if stmt.get("kind") == "If":
                test = stmt.get("test")
                if isinstance(test, dict):
                    if test.get("kind") == "Constant" and test.get("value") is False:
                        # Dead branch: skip body, include only orelse
                        orelse = stmt.get("orelse")
                        if isinstance(orelse, list):
                            result.extend(self._strip_dead_branches(orelse))
                        continue
                    if test.get("kind") == "IsInstance":
                        orelse = stmt.get("orelse")
                        if isinstance(orelse, list):
                            result.extend(self._strip_dead_branches(orelse))
                        continue
            result.append(stmt)
        return result

    def _body_mutates_self(self, body_any: Any) -> bool:
        """body 内で self のフィールドに代入があるか判定する。"""
        body = self._dict_list(body_any)
        for stmt in body:
            kind = stmt.get("kind")
            if kind in {"Assign", "AnnAssign", "AugAssign"}:
                target = stmt.get("target")
                if isinstance(target, dict) and target.get("kind") == "Attribute":
                    val = target.get("value")
                    if isinstance(val, dict) and val.get("kind") == "Name" and val.get("id") == "self":
                        return True
        return False

    def _push_function_context(self, stmt: dict[str, Any], arg_names: list[str], arg_order: list[Any]) -> None:
        self._hoisted_var_names = set()
        type_map: dict[str, str] = {}
        ref_vars: set[str] = set()
        local_vars: set[str] = set(arg_names)
        arg_types_any = stmt.get("arg_types")
        arg_types = arg_types_any if isinstance(arg_types_any, dict) else {}
        i = 0
        while i < len(arg_names):
            safe_name = arg_names[i]
            raw_name = arg_order[i] if i < len(arg_order) else safe_name
            arg_type_any = arg_types.get(raw_name)
            if not isinstance(arg_type_any, str):
                arg_type_any = arg_types.get(safe_name)
            arg_type = arg_type_any.strip() if isinstance(arg_type_any, str) else ""
            if arg_type != "":
                type_map[safe_name] = arg_type
            i += 1
        self._local_type_stack.append(type_map)
        self._ref_var_stack.append(ref_vars)
        self._local_var_stack.append(local_vars)
        self._mutated_var_stack.append(self._scan_mutated_vars(stmt.get("body")))

    def _pop_function_context(self) -> None:
        if len(self._local_type_stack) > 0:
            self._local_type_stack.pop()
        if len(self._ref_var_stack) > 0:
            self._ref_var_stack.pop()
        if len(self._local_var_stack) > 0:
            self._local_var_stack.pop()
        if len(self._mutated_var_stack) > 0:
            self._mutated_var_stack.pop()

    def _is_top_level_decl(self, stmt: dict[str, Any]) -> bool:
        """トップレベル宣言（関数/クラス/import/型エイリアス）かどうか判定する。"""
        kind = stmt.get("kind")
        return kind in {"FunctionDef", "ClassDef", "Import", "ImportFrom", "TypeAlias"}

    def _is_top_level_var(self, stmt: dict[str, Any]) -> bool:
        """トップレベル変数宣言（Assign/AnnAssign で Name ターゲット）かどうか判定する。"""
        kind = stmt.get("kind")
        if kind == "AnnAssign":
            target = stmt.get("target")
            return isinstance(target, dict) and target.get("kind") == "Name"
        if kind == "Assign":
            target = stmt.get("target")
            if isinstance(target, dict) and target.get("kind") == "Name":
                return True
            targets = stmt.get("targets")
            if isinstance(targets, list) and len(targets) > 0:
                if isinstance(targets[0], dict) and targets[0].get("kind") == "Name":
                    return True
        return False

    def _emit_top_level_var(self, stmt: dict[str, Any]) -> None:
        """トップレベル変数をモジュールスコープの var として emit する。"""
        kind = stmt.get("kind")
        target_node = None
        if kind == "AnnAssign":
            target_node = stmt.get("target")
        elif kind == "Assign":
            target_node = stmt.get("target")
            if target_node is None:
                targets = stmt.get("targets")
                if isinstance(targets, list) and len(targets) > 0:
                    target_node = targets[0]
        if not isinstance(target_node, dict) or target_node.get("kind") != "Name":
            return
        target_name = _safe_ident(target_node.get("id"), "value")
        # extern() 変数 → __native 委譲（spec-emitter-guide §4）
        value_node = stmt.get("value")
        inner_val = value_node
        if isinstance(inner_val, dict) and inner_val.get("kind") == "Unbox":
            inner_val = inner_val.get("value")
        if isinstance(inner_val, dict) and inner_val.get("kind") == "Call":
            vfunc = inner_val.get("func")
            if isinstance(vfunc, dict) and vfunc.get("id") in {"extern", "@\"extern\""}:
                self._ensure_native_import()
                decl_type = self._infer_decl_type(stmt)
                zig_ty = self._zig_type(decl_type)
                self._emit_line("pub const " + target_name + ": " + zig_ty + " = __native." + target_name + ";")
                return
        decl_type = self._infer_decl_type(stmt)
        zig_ty = self._zig_type(decl_type)
        value = self._render_expr(value_node) if isinstance(value_node, dict) else "undefined"
        self._emit_line("var " + target_name + ": " + zig_ty + " = " + value + ";")

    def transpile(self) -> str:
        module_comments = self._module_leading_comment_lines(prefix="// ")
        if len(module_comments) > 0:
            self.lines.extend(module_comments)
            self.lines.append("")
        self.lines.append("const std = @import(\"std\");")
        rt_path = self._root_rel_prefix() + "built_in/py_runtime.zig"
        self.lines.append("const pytra = @import(\"" + rt_path + "\");")
        body = self._dict_list(self.east_doc.get("body"))
        main_guard = self._dict_list(self.east_doc.get("main_guard_body"))
        self._scan_module_symbols(body)
        # import 文から @import を生成
        self._emit_imports(body)
        self.lines.append("")
        # 静的フィールドをモジュールスコープに emit
        for cls_name, sfields in self._static_fields.items():
            for field_name, field_type, default_val in sfields:
                zig_ty = self._zig_type(field_type)
                self._emit_line("var Module_" + cls_name + "_" + field_name + ": " + zig_ty + " = " + default_val + ";")
        # トップレベル変数をモジュールスコープに emit
        for stmt in body:
            if self._is_top_level_var(stmt):
                self._emit_top_level_var(stmt)
        # トップレベル宣言（fn, struct）を emit
        for stmt in body:
            if self._is_top_level_decl(stmt):
                self._emit_stmt(stmt)
        # vtable を emit
        self._emit_vtables()
        # §8: 残りのステートメント + main_guard_body (is_entry のみ) を pub fn main() に入れる
        ectx_main = self._get_emit_context()
        is_entry = ectx_main.get("is_entry", False) if isinstance(ectx_main, dict) else False
        top_stmts: list[dict[str, Any]] = []
        for stmt in body:
            if not self._is_top_level_decl(stmt) and not self._is_top_level_var(stmt):
                top_stmts.append(stmt)
        if is_entry:
            for stmt in main_guard:
                top_stmts.append(stmt)
        if len(top_stmts) > 0:
            self._mutated_var_stack.append(self._scan_mutated_vars(top_stmts))
            self._local_var_stack.append(set())
            self._local_type_stack.append({})
            self._ref_var_stack.append(set())
            self.lines.append("pub fn main() void {")
            self.indent += 1
            for stmt in top_stmts:
                self._emit_stmt(stmt)
            self.indent -= 1
            self.lines.append("}")
            self._pop_function_context()
        self._fixup_unused_obj_vars()
        # タプル typedef をモジュール先頭（import 直後）に挿入
        if len(self._tuple_typedefs) > 0:
            insert_idx = 0
            # @import 行の直後を探す
            for li in range(len(self.lines)):
                line = self.lines[li].strip()
                if line.startswith("const ") and "@import" in line:
                    insert_idx = li + 1
            typedef_lines: list[str] = []
            for norm_type, name in self._tuple_typedefs.items():
                parts = self._split_generic(norm_type[6:-1])
                inner_types: list[str] = []
                for p in parts:
                    inner_types.append(self._zig_type(p.strip()))
                fields = ", ".join("_" + str(i) + ": " + zt for i, zt in enumerate(inner_types))
                typedef_lines.append("const " + name + " = struct { " + fields + " };")
            for tl in reversed(typedef_lines):
                self.lines.insert(insert_idx, tl)
        return "\n".join(self.lines).rstrip() + "\n"

    def _fixup_unused_obj_vars(self) -> None:
        """後処理: 未使用 const に _ = を挿入、未 mutated var を const に降格。"""
        import re
        decl_re = re.compile(r"^(\s+)(const|var)\s+(\w+)\s*:")
        # mutation パターン: var_name = / var_name += / var_name -= etc.
        import re as _re_mut
        def _is_mutated_after(var_name: str, start: int) -> bool:
            # var_name の mutation を検出:
            # 1. var_name = / += / -= 等（直接代入）
            # 2. var_name.field = （フィールド代入）
            # 3. var_name.put( / var_name.append( 等（メソッド mutation）
            pat_assign = _re_mut.compile(r'\b' + _re_mut.escape(var_name) + r'(\.\w+)?\s*(\+\=|\-\=|\*\=|/\=|\=(?!\=))')
            pat_method = _re_mut.compile(r'\b' + _re_mut.escape(var_name) + r'\.(put|append|extend|pop)\s*\(')
            j = start
            while j < len(self.lines):
                if pat_assign.search(self.lines[j]) or pat_method.search(self.lines[j]):
                    return True
                j += 1
            return False

        insertions: list[tuple[int, str]] = []
        replacements: list[tuple[int, str, str]] = []
        i = 0
        while i < len(self.lines):
            m = decl_re.match(self.lines[i])
            if m is not None:
                indent = m.group(1)
                kw = m.group(2)
                var_name = m.group(3)
                # 後続行で var_name が使用されているか
                used = False
                j = i + 1
                while j < len(self.lines):
                    line = self.lines[j]
                    if var_name in line and "_ = " + var_name not in line:
                        used = True
                        break
                    j += 1
                if not used:
                    # 未使用 const → _ = を挿入
                    if kw == "const":
                        insertions.append((i + 1, indent + "_ = " + var_name + ";"))
                    else:
                        # 未使用 var → const に降格 + _ = 挿入
                        replacements.append((i, "var " + var_name, "const " + var_name))
                        insertions.append((i + 1, indent + "_ = " + var_name + ";"))
                elif kw == "var" and not _is_mutated_after(var_name, i + 1):
                    # 使用されるが mutation されない var → const に降格
                    replacements.append((i, "var " + var_name, "const " + var_name))
            i += 1
        for line_idx, old, new in replacements:
            self.lines[line_idx] = self.lines[line_idx].replace(old, new, 1)
        for idx, line in reversed(insertions):
            self.lines.insert(idx, line)

    def _dict_list(self, value: Any) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            return []
        out: list[dict[str, Any]] = []
        for item in value:
            if isinstance(item, dict):
                out.append(item)
        return out

    def _block_has_return_stmt(self, body_any: Any) -> bool:
        body = self._dict_list(body_any)
        i = 0
        while i < len(body):
            if body[i].get("kind") == "Return":
                return True
            i += 1
        return False

    def _module_leading_comment_lines(self, prefix: str) -> list[str]:
        trivia = self._dict_list(self.east_doc.get("module_leading_trivia"))
        out: list[str] = []
        for item in trivia:
            kind = item.get("kind")
            if kind == "comment":
                text = item.get("text")
                if isinstance(text, str):
                    out.append(prefix + text)
                continue
            if kind == "blank":
                count = item.get("count")
                n = count if isinstance(count, int) and count > 0 else 1
                i = 0
                while i < n:
                    out.append("")
                    i += 1
        while len(out) > 0 and out[-1] == "":
            out.pop()
        return out

    def _emit_leading_trivia(self, stmt: dict[str, Any], prefix: str) -> None:
        trivia = self._dict_list(stmt.get("leading_trivia"))
        for item in trivia:
            kind = item.get("kind")
            if kind == "comment":
                text = item.get("text")
                if isinstance(text, str):
                    self._emit_line(prefix + text)
                continue
            if kind == "blank":
                count = item.get("count")
                n = count if isinstance(count, int) and count > 0 else 1
                i = 0
                while i < n:
                    self._emit_line("")
                    i += 1

    def _emit_line(self, text: str) -> None:
        self.lines.append(("    " * self.indent) + text)

    def _emit_block(self, body_any: Any) -> None:
        body = self._dict_list(body_any)
        for stmt in body:
            self._emit_stmt(stmt)

    def _scan_module_symbols(self, body: list[dict[str, Any]]) -> None:
        for stmt in body:
            kind = stmt.get("kind")
            if kind == "FunctionDef":
                name = _safe_ident(stmt.get("name"), "fn")
                self.function_names.add(name)
            if kind == "ClassDef":
                name = _safe_ident(stmt.get("name"), "Class")
                self.class_names.add(name)
                base_any = stmt.get("base")
                if isinstance(base_any, str) and base_any.strip() != "":
                    self._class_base[name] = _safe_ident(base_any.strip(), "")
                methods: set[str] = set()
                cls_body = self._dict_list(stmt.get("body"))
                for sub in cls_body:
                    if sub.get("kind") == "FunctionDef":
                        m_name = sub.get("name")
                        if isinstance(m_name, str) and m_name != "__init__":
                            methods.add(m_name)
                self._class_methods[name] = methods
                if bool(stmt.get("dataclass")):
                    self._dataclass_names.add(name)
                    fields: list[str] = []
                    for sub in cls_body:
                        if sub.get("kind") == "AnnAssign":
                            target_any = sub.get("target")
                            if isinstance(target_any, dict) and target_any.get("kind") == "Name":
                                fields.append(_safe_ident(target_any.get("id"), "field"))
                    self._dataclass_fields[name] = fields
                # 静的フィールドの検出: AnnAssign で初期値付き + メソッド内で ClassName.field としてアクセス
                static_fields: list[tuple[str, str, str]] = []
                for sub in cls_body:
                    if sub.get("kind") == "AnnAssign":
                        target_any = sub.get("target")
                        if isinstance(target_any, dict) and target_any.get("kind") == "Name":
                            field_name = _safe_ident(target_any.get("id"), "field")
                            value_node = sub.get("value")
                            if isinstance(value_node, dict):
                                decl_type = self._infer_decl_type(sub)
                                default_val = self._render_expr(value_node)
                                # メソッド body で ClassName.field パターンがあるか
                                body_text = str(cls_body)
                                class_dot_field = "'" + str(stmt.get("name")) + "'"
                                if class_dot_field in body_text:
                                    static_fields.append((field_name, decl_type, default_val))
                if len(static_fields) > 0:
                    self._static_fields[name] = static_fields
                for sub in cls_body:
                    if sub.get("kind") == "FunctionDef":
                        if sub.get("name") == "__init__":
                            self._classes_with_init.add(name)
                        elif sub.get("name") == "__del__":
                            self._classes_with_del.add(name)
                        elif self._body_mutates_self(sub.get("body")):
                            self._classes_with_mut_method.add(name)
                # メソッドの戻り値型を記録
                cls_ret_types: dict[str, str] = {}
                for sub in cls_body:
                    if sub.get("kind") == "FunctionDef":
                        m_name = sub.get("name")
                        ret = sub.get("return_type")
                        if isinstance(m_name, str) and isinstance(ret, str):
                            cls_ret_types[m_name] = ret.strip()
                self._class_return_types[name] = cls_ret_types
        # __del__ があるクラスも vtable 対象にする（rc + drop が必要）
        for cls_name in self._classes_with_del:
            if cls_name not in self._vtable_root:
                self._vtable_root[cls_name] = cls_name
                if cls_name not in self._vtable_methods:
                    self._vtable_methods[cls_name] = []
        # vtable 検出: 継承階層でメソッドが override されている場合
        for cls_name in self.class_names:
            base = self._class_base.get(cls_name, "")
            if base == "":
                continue
            own = self._class_methods.get(cls_name, set())
            # 基底を辿って root を見つける
            root = base
            while self._class_base.get(root, "") != "":
                root = self._class_base[root]
            # root のメソッドと override を収集
            if root not in self._vtable_methods:
                all_methods: list[str] = []
                seen_m: set[str] = set()
                # root から全子孫のメソッドを収集
                for cn in self.class_names:
                    r = cn
                    while self._class_base.get(r, "") != "":
                        r = self._class_base[r]
                    if r != root:
                        continue
                    for m in self._class_methods.get(cn, set()):
                        if m not in seen_m:
                            all_methods.append(m)
                            seen_m.add(m)
                self._vtable_methods[root] = all_methods
            self._vtable_root[cls_name] = root
            self._vtable_root[root] = root

    def _has_vtable(self, cls_name: str) -> bool:
        return cls_name in self._vtable_root

    def _get_vtable_root(self, cls_name: str) -> str:
        return self._vtable_root.get(cls_name, cls_name)

    def _emit_vtables(self) -> None:
        """vtable struct, wrapper 関数, vtable インスタンスを emit する。"""
        emitted_roots: set[str] = set()
        for root, methods in self._vtable_methods.items():
            if root in emitted_roots:
                continue
            emitted_roots.add(root)
            # VTable struct
            vt_name = root + "VT"
            self._emit_line("const " + vt_name + " = struct {")
            self.indent += 1
            for m in methods:
                ret_type = self._find_method_return_type(root, m)
                zig_ret = self._zig_type(ret_type)
                self._emit_line(m + ": *const fn (*anyopaque) " + zig_ret + ",")
            self.indent -= 1
            self._emit_line("};")
            self._emit_line("")
            # 階層内の全クラスの wrapper + vtable instance
            for cls_name in self.class_names:
                cls_root = self._vtable_root.get(cls_name, "")
                if cls_root != root:
                    continue
                # wrapper 関数と vtable instance
                for m in methods:
                    impl_cls = self._find_method_impl(cls_name, m)
                    ret_type = self._class_return_types.get(impl_cls, {}).get(m, "")
                    if ret_type == "":
                        ret_type = self._find_method_return_type(root, m)
                    zig_ret = self._zig_type(ret_type)
                    wrapper_name = cls_name + "_" + m + "_wrap"
                    self._emit_line("fn " + wrapper_name + "(_: *anyopaque) " + zig_ret + " {")
                    self.indent += 1
                    self._emit_line("return " + impl_cls + "." + m + "(undefined);")
                    self.indent -= 1
                    self._emit_line("}")
                # drop wrapper for __del__
                if cls_name in self._classes_with_del:
                    drop_name = cls_name + "_drop_wrap"
                    self._emit_line("fn " + drop_name + "(p: *anyopaque) void {")
                    self.indent += 1
                    self._emit_line("const self: *" + cls_name + " = @ptrCast(@alignCast(p));")
                    self._emit_line(cls_name + ".__del__(self);")
                    self.indent -= 1
                    self._emit_line("}")
                # vtable instance
                vt_inst = cls_name + "_vt"
                field_inits: list[str] = []
                for m in methods:
                    field_inits.append("." + m + " = " + cls_name + "_" + m + "_wrap")
                self._emit_line("const " + vt_inst + " = " + vt_name + "{ " + ", ".join(field_inits) + " };")
                self._emit_line("")

    def _find_method_return_type(self, root: str, method: str) -> str:
        """vtable root から全子孫を辿り、method の戻り値型を見つける。"""
        for cls_name in self.class_names:
            r = self._vtable_root.get(cls_name, "")
            if r != root:
                continue
            ret = self._class_return_types.get(cls_name, {}).get(method, "")
            if ret != "":
                return ret
        return ""

    def _find_method_impl(self, cls_name: str, method: str) -> str:
        """cls_name から基底を辿り、method を実装しているクラスを返す。"""
        current = cls_name
        while current != "":
            if method in self._class_methods.get(current, set()):
                return current
            current = self._class_base.get(current, "")
        return cls_name

    def _get_emit_context(self) -> dict[str, Any]:
        meta = self.east_doc.get("meta")
        if isinstance(meta, dict):
            ectx = meta.get("emit_context")
            if isinstance(ectx, dict):
                return ectx
        return {}

    def _root_rel_prefix(self) -> str:
        rr = self._get_emit_context().get("root_rel_prefix", "./")
        if rr == "./":
            return ""
        return rr

    def _module_id_to_import_path(self, module_id: str) -> str:
        """module_id から Zig import パスを機械的に生成（spec-emitter-guide §3）。"""
        rel = module_id
        if rel.startswith("pytra."):
            rel = rel[len("pytra."):]
        return self._root_rel_prefix() + rel.replace(".", "/") + ".zig"

    def _emit_imports(self, body: list[dict[str, Any]]) -> None:
        """import_bindings から Zig の @import を生成（§3: linker 解決済み情報を使用）。"""
        from toolchain.emit.common.emitter.code_emitter import build_import_alias_map
        emitted: set[str] = set()
        self._import_alias_map = build_import_alias_map(self.east_doc.get("meta", {}))
        _DECORATORS = {"abi", "extern", "template"}
        meta = self.east_doc.get("meta")
        meta = meta if isinstance(meta, dict) else {}
        import_bindings_any = meta.get("import_bindings")
        import_bindings = import_bindings_any if isinstance(import_bindings_any, list) else []
        for binding in import_bindings:
            if not isinstance(binding, dict):
                continue
            module_id = binding.get("module_id", "")
            if not isinstance(module_id, str) or module_id == "":
                continue
            # Skip pytra.built_in (provided by py_runtime.zig)
            if module_id.startswith("pytra.built_in"):
                continue
            # Skip non-pytra modules (Python stdlib used by @extern source)
            if not module_id.startswith("pytra.") and not module_id.startswith("."):
                continue
            binding_kind = binding.get("binding_kind", "")
            export_name = binding.get("export_name", "")
            local_name = binding.get("local_name", "")
            if isinstance(export_name, str) and export_name in _DECORATORS:
                continue
            # Mechanically derive import path from module_id (§3)
            rel = module_id
            if rel.startswith("pytra."):
                rel = rel[len("pytra."):]
            # Parent module with symbol binding → sub-module
            if "." not in rel and binding_kind == "symbol" and isinstance(export_name, str) and export_name != "":
                if export_name in _DECORATORS:
                    continue
                imported_module = module_id + "." + export_name
            else:
                imported_module = module_id
            import_path = self._module_id_to_import_path(imported_module)
            safe_mod = _safe_ident(imported_module.split(".")[-1], "mod")
            if safe_mod not in emitted:
                self._emit_line("const " + safe_mod + " = @import(\"" + import_path + "\");")
                emitted.add(safe_mod)
            # Symbol binding: add const alias (e.g. const Path = pathlib.Path;)
            if binding_kind == "symbol" and isinstance(local_name, str) and local_name != "":
                safe_local = _safe_ident(local_name, "fn")
                if safe_local != safe_mod and safe_local not in emitted:
                    self._emit_line("const " + safe_local + " = " + safe_mod + "." + _safe_ident(export_name, "fn") + ";")
                    emitted.add(safe_local)

    def _emit_stmt(self, stmt: dict[str, Any]) -> None:
        self._emit_leading_trivia(stmt, prefix="// ")
        kind = stmt.get("kind")
        if kind in {"Import", "ImportFrom"}:
            return
        if kind == "ClassDef":
            self._emit_class_def(stmt)
            return
        if kind == "FunctionDef":
            self._emit_function_def(stmt)
            return
        if kind == "Return":
            val = self._render_expr(stmt.get("value"))
            if val == "null":
                self._emit_line("return;")
            else:
                self._emit_line("return " + val + ";")
            return
        if kind == "AnnAssign":
            target_node = stmt.get("target")
            target = self._render_target(target_node)
            value_node = stmt.get("value")
            # extern() 変数 → __native 委譲（spec-emitter-guide §4）
            # Unbox ラッパーを透過
            inner_val = value_node
            if isinstance(inner_val, dict) and inner_val.get("kind") == "Unbox":
                inner_val = inner_val.get("value")
            if isinstance(inner_val, dict) and inner_val.get("kind") == "Call":
                vfunc = inner_val.get("func")
                if isinstance(vfunc, dict) and (vfunc.get("id") == "extern" or vfunc.get("id") == "@\"extern\""):
                    self._ensure_native_import()
                    decl_type = self._infer_decl_type(stmt)
                    zig_ty = self._zig_type(decl_type)
                    self._emit_line("pub const " + target + ": " + zig_ty + " = __native." + target + ";")
                    return
            value = self._render_expr(value_node) if isinstance(value_node, dict) else "undefined"
            if isinstance(target_node, dict) and target_node.get("kind") == "Name":
                target_name = _safe_ident(target_node.get("id"), "value")
                decl_type = self._infer_decl_type(stmt)
                if decl_type != "":
                    self._current_type_map()[target_name] = decl_type
                zig_ty = self._zig_type(decl_type)
                # PyObject fallback の場合、値の resolved_type で型を補正
                if zig_ty == "pytra.PyObject" and isinstance(value_node, dict):
                    val_resolved = self._get_expr_type(value_node)
                    if val_resolved in {"float64", "float32", "float"}:
                        zig_ty = "f64"
                    elif val_resolved in {"int64", "int32"}:
                        zig_ty = "i64"
                # VarDecl で既に宣言済みなら再代入
                already_declared = len(self._local_var_stack) > 0 and target_name in self._current_local_vars()
                if already_declared:
                    if value_node is not None:
                        self._emit_line(target + " = " + value + ";")
                    return
                if len(self._local_var_stack) > 0:
                    self._current_local_vars().add(target_name)
                decl_kw = "var" if (self._is_var_mutated(target_name) or self._needs_var_for_type(decl_type)) else "const"
                if value_node is None and bool(stmt.get("declare")):
                    self._emit_line("var " + target + ": " + zig_ty + " = undefined;")
                else:
                    # 空 dict リテラル: decl_type の値型で初期化
                    if isinstance(value_node, dict) and value_node.get("kind") == "Dict":
                        entries = value_node.get("entries")
                        if (entries is None or (isinstance(entries, list) and len(entries) == 0)):
                            if decl_type.startswith("dict[") and decl_type.endswith("]"):
                                parts = self._split_generic(decl_type[5:-1])
                                if len(parts) == 2:
                                    val_zig = self._zig_type(parts[1].strip())
                                    value = "pytra.make_str_dict(" + val_zig + ")"
                    # 型キャスト挿入: i64 変数に f64 値、f64 変数に i64 値
                    val_type = self._get_expr_type(value_node) if isinstance(value_node, dict) else ""
                    _INT_T = {"int64", "int32", "int16", "int8", "uint8", "uint16", "uint32", "uint64"}
                    _FLOAT_T = {"float64", "float32", "float"}
                    norm_decl = self._normalize_type(decl_type)
                    if norm_decl in _INT_T and val_type in _FLOAT_T:
                        value = "@as(i64, @intFromFloat(" + value + "))"
                    elif norm_decl in _FLOAT_T and val_type in _INT_T:
                        value = "@as(f64, @floatFromInt(" + value + "))"
                    self._emit_line(decl_kw + " " + target + ": " + zig_ty + " = " + value + ";")
                    norm_type = self._normalize_type(decl_type)
                    if norm_type in self.class_names and self._has_vtable(norm_type):
                        self._emit_line("defer " + target + ".release();")

            else:
                self._emit_line(target + " = " + value + ";")
            return
        if kind == "Assign":
            target_any = stmt.get("target")
            if isinstance(target_any, dict):
                td2: dict[str, Any] = target_any
                if td2.get("kind") == "Tuple":
                    self._emit_tuple_assign(target_any, stmt.get("value"))
                    return
                # Subscript 代入: list[idx] = val → list_set
                if td2.get("kind") == "Subscript":
                    sub_val = td2.get("value")
                    sub_val_type = self._get_expr_type(sub_val) if isinstance(sub_val, dict) else ""
                    if sub_val_type.startswith("list[") or sub_val_type in {"bytearray", "bytes"}:
                        obj_expr = self._render_expr(sub_val)
                        idx_expr = self._render_expr(td2.get("slice"))
                        val_expr = self._render_expr(stmt.get("value"))
                        elem = "i64"
                        if sub_val_type.startswith("list[") and sub_val_type.endswith("]"):
                            elem = self._zig_type(sub_val_type[5:-1].strip())
                        elif sub_val_type in {"bytearray", "bytes"}:
                            elem = "u8"
                        if elem in {"u8", "i8", "i16", "u16", "i32", "u32", "i64", "u64"}:
                            val_expr = "@intCast(" + val_expr + ")"
                        self._emit_line("pytra.list_set(" + obj_expr + ", " + elem + ", " + idx_expr + ", " + val_expr + ");")
                        return
                    # dict[key] = val → .put(key, val)
                    if sub_val_type.startswith("dict["):
                        obj_expr = self._render_expr(sub_val)
                        idx_expr = self._render_expr(td2.get("slice"))
                        val_expr = self._render_expr(stmt.get("value"))
                        self._emit_line(obj_expr + ".put(" + idx_expr + ", " + val_expr + ") catch {};")
                        return
                target = self._render_target(target_any)
                value = self._render_expr(stmt.get("value"))
                if td2.get("kind") == "Name":
                    target_name = _safe_ident(td2.get("id"), "value")
                    decl_type = self._infer_decl_type(stmt)
                    if decl_type == "":
                        decl_type = self._get_expr_type(stmt.get("value"))
                    if decl_type != "":
                        self._current_type_map()[target_name] = decl_type
                    if len(self._local_var_stack) > 0 and target_name not in self._current_local_vars():
                        self._current_local_vars().add(target_name)
                        zig_ty = self._zig_type(decl_type)
                        # PyObject fallback → 値の型推論で型を補正
                        if zig_ty == "pytra.PyObject" and isinstance(stmt.get("value"), dict):
                            val_resolved = self._lookup_expr_type(stmt.get("value"))
                            if val_resolved in {"float64", "float32", "float"}:
                                zig_ty = "f64"
                                decl_type = val_resolved
                                self._current_type_map()[target_name] = decl_type
                            elif val_resolved in {"int64", "int32"}:
                                zig_ty = "i64"
                                decl_type = val_resolved
                                self._current_type_map()[target_name] = decl_type
                        decl_kw = "var" if (self._is_var_mutated(target_name) or self._needs_var_for_type(decl_type)) else "const"
                        self._emit_line(decl_kw + " " + target + ": " + zig_ty + " = " + value + ";")
                        norm_type = self._normalize_type(decl_type)
                        if norm_type in self.class_names and self._has_vtable(norm_type):
                            self._emit_line("defer " + target + ".release();")
                        return
                # 既存変数への再代入 — pytra.Obj なら release + retain
                if td2.get("kind") == "Name":
                    old_type = self._current_type_map().get(target_name, "")
                    if self._normalize_type(old_type) in self.class_names and self._has_vtable(self._normalize_type(old_type)):
                        self._emit_line(target + ".release();")
                        self._emit_line(target + " = " + value + ".retain();")
                        return
                # 型キャスト: 変数型と値型の不一致を補正
                if td2.get("kind") == "Name":
                    var_type = self._current_type_map().get(target_name, "")
                    val_type = self._get_expr_type(stmt.get("value"))
                    norm_var = self._normalize_type(var_type)
                    _INT_T = {"int64", "int32", "int16", "int8", "uint8", "uint16", "uint32", "uint64"}
                    _FLOAT_T = {"float64", "float32", "float"}
                    if norm_var in _INT_T and val_type in _FLOAT_T:
                        value = "@as(i64, @intFromFloat(" + value + "))"
                    elif norm_var in _FLOAT_T and val_type in _INT_T:
                        value = "@as(f64, @floatFromInt(" + value + "))"
                self._emit_line(target + " = " + value + ";")
                return
            targets = stmt.get("targets")
            if isinstance(targets, list) and len(targets) > 0 and isinstance(targets[0], dict):
                if targets[0].get("kind") == "Tuple":
                    self._emit_tuple_assign(targets[0], stmt.get("value"))
                    return
                target = self._render_target(targets[0])
                value = self._render_expr(stmt.get("value"))
                if targets[0].get("kind") == "Name":
                    target_name = _safe_ident(targets[0].get("id"), "value")
                    decl_type = self._infer_decl_type(stmt)
                    if decl_type == "":
                        decl_type = self._get_expr_type(stmt.get("value"))
                    if decl_type != "":
                        self._current_type_map()[target_name] = decl_type
                    if len(self._local_var_stack) > 0 and target_name not in self._current_local_vars():
                        self._current_local_vars().add(target_name)
                        zig_ty = self._zig_type(decl_type)
                        # PyObject fallback → 値の型推論で型を補正
                        if zig_ty == "pytra.PyObject" and isinstance(stmt.get("value"), dict):
                            val_resolved = self._lookup_expr_type(stmt.get("value"))
                            if val_resolved in {"float64", "float32", "float"}:
                                zig_ty = "f64"
                                decl_type = val_resolved
                                self._current_type_map()[target_name] = decl_type
                            elif val_resolved in {"int64", "int32"}:
                                zig_ty = "i64"
                                decl_type = val_resolved
                                self._current_type_map()[target_name] = decl_type
                        decl_kw = "var" if (self._is_var_mutated(target_name) or self._needs_var_for_type(decl_type)) else "const"
                        self._emit_line(decl_kw + " " + target + ": " + zig_ty + " = " + value + ";")
                        if decl_kw == "const" and zig_ty in {"i64", "i32", "i16", "i8", "u8", "u16", "u32", "u64", "f64", "f32", "bool", "[]const u8"}:
                            self._emit_line("_ = " + target + ";")
                        return
                self._emit_line(target + " = " + value + ";")
                return
            raise RuntimeError("lang=zig unsupported assign shape")
        if kind == "AugAssign":
            target = self._render_target(stmt.get("target"))
            op = str(stmt.get("op"))
            value = self._render_expr(stmt.get("value"))
            aug_op = self._aug_assign_op(op)
            self._emit_line(target + " " + aug_op + " " + value + ";")
            return
        if kind == "Expr":
            value_any = stmt.get("value")
            if isinstance(value_any, dict) and value_any.get("kind") == "Constant":
                if isinstance(value_any.get("value"), str):
                    return
            if isinstance(value_any, dict) and value_any.get("kind") == "Name":
                loop_kw = str(value_any.get("id"))
                if loop_kw == "break":
                    self._emit_line("break;")
                    return
                if loop_kw == "continue":
                    self._emit_line("continue;")
                    return
            expr_text = self._render_expr(value_any)
            if isinstance(value_any, dict) and value_any.get("kind") == "Call":
                resolved = self._get_expr_type(value_any)
                if resolved in {"None", ""}:
                    self._emit_line(expr_text + ";")
                else:
                    self._emit_line("_ = " + expr_text + ";")
            else:
                self._emit_line("_ = " + expr_text + ";")
            return
        if kind == "Raise":
            exc_any = stmt.get("exc")
            if isinstance(exc_any, dict) and exc_any.get("kind") == "Call":
                fn_any = exc_any.get("func")
                if isinstance(fn_any, dict) and fn_any.get("kind") == "Name":
                    fn_name = _safe_ident(fn_any.get("id"), "")
                    args_any = exc_any.get("args")
                    args = args_any if isinstance(args_any, list) else []
                    if len(args) > 0:
                        self._emit_line("@panic(" + self._render_expr(args[0]) + ");")
                        return
                    self._emit_line("@panic(\"error\");")
                    return
            if isinstance(exc_any, dict):
                self._emit_line("@panic(" + self._render_expr(exc_any) + ");")
            else:
                self._emit_line("@panic(\"error\");")
            return
        if kind == "Try":
            body = self._dict_list(stmt.get("body"))
            for sub in body:
                self._emit_stmt(sub)
            return
        if kind == "If":
            self._emit_if(stmt)
            return
        if kind == "ForCore":
            self._emit_for_core(stmt)
            return
        if kind == "ForRange":
            self._emit_for_range(stmt)
            return
        if kind == "While":
            self._emit_while(stmt)
            return
        if kind == "Pass":
            self._emit_line("// pass")
            return
        if kind == "Swap":
            self._emit_swap(stmt)
            return
        if kind == "TypeAlias":
            alias_name = _safe_ident(stmt.get("name"), "T")
            self._emit_line("const " + alias_name + " = PyObject;  // type alias")
            return
        if kind == "Yield":
            val = self._render_expr(stmt.get("value"))
            self._emit_line("_ = " + val + ";  // yield (unsupported)")
            return
        if kind == "Delete":
            return
        if kind == "Assert":
            test = self._render_expr(stmt.get("test"))
            self._emit_line("std.debug.assert(" + test + ");")
            return
        if kind == "Global" or kind == "Nonlocal":
            return
        if kind == "VarDecl":
            self._emit_var_decl(stmt)
            return
        raise RuntimeError("lang=zig unsupported stmt kind: " + str(kind))

    def _emit_var_decl(self, stmt: dict[str, Any]) -> None:
        """Emit a hoisted variable declaration (VarDecl node).

        If the variable is captured by a nested for loop (ForCore target_plan),
        skip the VarDecl to avoid shadow errors in Zig.
        """
        name_raw = stmt.get("name")
        name = _safe_ident(name_raw, "v") if isinstance(name_raw, str) else "v"
        var_type_any = stmt.get("type")
        var_type = var_type_any.strip() if isinstance(var_type_any, str) else ""
        if var_type != "":
            self._current_type_map()[name] = var_type
        if len(self._local_var_stack) > 0:
            self._current_local_vars().add(name)
        self._hoisted_var_names.add(name)
        # object/unknown 型は具体型を推論 (PyObject は i64 alias なので float 代入に不適)
        if var_type in {"object", "unknown", "Any", ""}:
            inferred = self._infer_hoisted_var_type_from_body(name)
            if inferred != "":
                var_type = inferred
                self._current_type_map()[name] = var_type
        zig_ty = self._zig_type(var_type) if var_type != "" else "pytra.PyObject"
        self._emit_line("var " + name + ": " + zig_ty + " = undefined;")

    def _infer_hoisted_var_type_from_body(self, name: str) -> str:
        """VarDecl の型が object/unknown の場合、EAST 全体の Assign から具体型を推論。"""
        body = self._dict_list(self.east_doc.get("body"))
        main_guard = self._dict_list(self.east_doc.get("main_guard_body"))
        result = self._find_first_assign_type(body, name)
        if result == "":
            result = self._find_first_assign_type(main_guard, name)
        return result

    def _find_first_assign_type(self, nodes: list[dict[str, Any]], name: str) -> str:
        for node in nodes:
            if not isinstance(node, dict):
                continue
            kind = node.get("kind", "")
            if kind in ("Assign", "AnnAssign"):
                target = node.get("target")
                if isinstance(target, dict) and target.get("kind") == "Name":
                    if _safe_ident(target.get("id"), "") == name:
                        val = node.get("value")
                        if isinstance(val, dict):
                            t = self._lookup_expr_type(val)
                            if t != "" and t != "unknown":
                                return t
            # Recurse into blocks
            for key in ("body", "orelse", "finalbody"):
                sub = node.get(key)
                if isinstance(sub, list):
                    result = self._find_first_assign_type(sub, name)
                    if result != "":
                        return result
            # Also check handlers
            handlers = node.get("handlers")
            if isinstance(handlers, list):
                for h in handlers:
                    if isinstance(h, dict):
                        sub = h.get("body")
                        if isinstance(sub, list):
                            result = self._find_first_assign_type(sub, name)
                            if result != "":
                                return result
        return ""

    def _is_for_capture_var(self, name: str) -> bool:
        """Check if name is used as a for-loop capture variable in current function body."""
        # Walk the current function's body to find ForCore with matching target
        if len(self._local_var_stack) == 0:
            return False
        # Search east_doc body recursively for ForCore target matching name
        body = self.east_doc.get("body", [])
        return self._find_for_capture(body, name)

    def _find_for_capture(self, nodes: Any, name: str) -> bool:
        if not isinstance(nodes, list):
            return False
        for node in nodes:
            if not isinstance(node, dict):
                continue
            kind = node.get("kind", "")
            if kind == "ForCore":
                tp = node.get("target_plan")
                if isinstance(tp, dict) and tp.get("kind") == "NameTarget":
                    if _safe_ident(tp.get("id"), "") == name:
                        return True
                if self._find_for_capture(node.get("body", []), name):
                    return True
            elif kind == "ForRange":
                target = node.get("target")
                if isinstance(target, dict) and target.get("kind") == "Name":
                    if _safe_ident(target.get("id"), "") == name:
                        return True
                if self._find_for_capture(node.get("body", []), name):
                    return True
            elif kind == "FunctionDef":
                if self._find_for_capture(node.get("body", []), name):
                    return True
            elif kind == "While":
                if self._find_for_capture(node.get("body", []), name):
                    return True
            elif kind == "If":
                if self._find_for_capture(node.get("body", []), name):
                    return True
                if self._find_for_capture(node.get("orelse", []), name):
                    return True
        return False

    def _resolve_arg_zig_type(self, arg_name: str, raw_name: Any, arg_types: dict[str, Any]) -> str:
        """引数の型を EAST3 の arg_types から解決して Zig 型を返す。"""
        raw_any = arg_types.get(raw_name) if isinstance(raw_name, str) else None
        if not isinstance(raw_any, str):
            raw_any = arg_types.get(arg_name)
        py_type = raw_any.strip() if isinstance(raw_any, str) else ""
        return self._zig_type(py_type)

    def _ensure_native_import(self) -> None:
        """__native import を1度だけ出力する（@extern 関数/変数の委譲用）。"""
        if not hasattr(self, "_extern_native_emitted"):
            self._extern_native_emitted = False
        if not self._extern_native_emitted:
            ectx = self._get_emit_context()
            module_id = ectx.get("module_id", "")
            clean_id = module_id.replace(".east", "")
            parts = clean_id.split(".")
            leaf = parts[-1] if len(parts) > 0 else "unknown"
            native_path = leaf + "_native.zig"
            self._emit_line("const __native = @import(\"" + native_path + "\");")
            self._extern_native_emitted = True

    def _emit_extern_delegation(self, stmt: dict[str, Any], name: str) -> None:
        """@extern 関数の native 委譲コードを生成（spec-emitter-guide §4/§5.1）。"""
        self._ensure_native_import()
        # 引数リスト
        arg_order_any = stmt.get("arg_order")
        args = arg_order_any if isinstance(arg_order_any, list) else []
        arg_types_any = stmt.get("arg_types")
        arg_types = arg_types_any if isinstance(arg_types_any, dict) else {}
        arg_strs: list[str] = []
        call_args: list[str] = []
        for a in args:
            safe_name = _safe_ident(a, "arg")
            raw_type = arg_types.get(a)
            py_t = raw_type.strip() if isinstance(raw_type, str) else ""
            zig_ty = self._zig_type(py_t)
            arg_strs.append(safe_name + ": " + zig_ty)
            call_args.append(safe_name)
        ret_type_any = stmt.get("return_type")
        ret_py = ret_type_any.strip() if isinstance(ret_type_any, str) else ""
        ret_zig = self._zig_type(ret_py) if ret_py != "" else "void"
        if ret_zig == "pytra.PyObject":
            ret_zig = "f64"  # extern 関数の戻り値は通常スカラー
        sig = "pub fn " + name + "(" + ", ".join(arg_strs) + ") " + ret_zig
        if ret_zig == "void":
            self._emit_line(sig + " { __native." + name + "(" + ", ".join(call_args) + "); }")
        else:
            self._emit_line(sig + " { return __native." + name + "(" + ", ".join(call_args) + "); }")

    def _emit_function_def(self, stmt: dict[str, Any]) -> None:
        name = _safe_ident(stmt.get("name"), "fn_")
        # @extern decorator → native 委譲コードを生成（spec-emitter-guide §4）
        decorators = stmt.get("decorators")
        if isinstance(decorators, list) and "extern" in decorators:
            self._emit_extern_delegation(stmt, name)
            return
        arg_order_any = stmt.get("arg_order")
        args = arg_order_any if isinstance(arg_order_any, list) else []
        arg_names: list[str] = []
        for a in args:
            arg_names.append(_safe_ident(a, "arg"))
        arg_strs: list[str] = []
        # Zig parameters are immutable; detect reassigned params and rename.
        reassigned_params = _code_emitter_utils._collect_reassigned_params(stmt)
        mutable_copies: list[tuple[str, str]] = []
        arg_types_any = stmt.get("arg_types")
        arg_types = arg_types_any if isinstance(arg_types_any, dict) else {}
        arg_usage = stmt.get("arg_usage")
        arg_usage = arg_usage if isinstance(arg_usage, dict) else {}
        # Collect sibling method names for shadowing detection (§ Zig param shadow)
        sibling_method_names: set[str] = set()
        if self._current_class_name != "":
            for sib in self._current_class_methods:
                sib_name = sib.get("name", "") if isinstance(sib, dict) else ""
                if sib_name != "":
                    sibling_method_names.add(sib_name)
        fn_live_body = self._strip_dead_branches(stmt.get("body"))
        i = 0
        while i < len(arg_names):
            raw_name = args[i] if i < len(args) else arg_names[i]
            zig_ty = self._resolve_arg_zig_type(arg_names[i], raw_name, arg_types)
            param_name = arg_names[i]
            # Check unused: EAST3 arg_usage or body scan (excluding dead branches)
            is_unused = raw_name not in arg_usage
            if not is_unused:
                is_unused = not self._body_uses_name(fn_live_body, param_name)
            if is_unused:
                param_name = "_"
            # Rename param if it shadows a sibling method name
            elif raw_name in sibling_method_names and raw_name != name:
                param_name = param_name + "_param"
                arg_names[i] = param_name
            # Reassigned params or mutable container params: rename and copy to var
            raw_type_any = arg_types.get(raw_name) if isinstance(raw_name, str) else None
            if not isinstance(raw_type_any, str):
                raw_type_any = arg_types.get(arg_names[i])
            py_t = raw_type_any.strip() if isinstance(raw_type_any, str) else ""
            norm_t = self._normalize_type(py_t)
            needs_mut = False
            if norm_t.startswith("list[") or norm_t in {"bytearray", "bytes"}:
                # body 内で .append/.extend 等が呼ばれるか or subscript 代入があるか
                mutated_in_body = self._scan_mutated_vars(stmt.get("body"))
                if arg_names[i] in mutated_in_body:
                    needs_mut = True
            if raw_name in reassigned_params or param_name in reassigned_params or needs_mut:
                param_alias = _code_emitter_utils._mutable_param_name(arg_names[i])
                mutable_copies.append((arg_names[i], param_alias))
                arg_strs.append(param_alias + ": " + zig_ty)
            else:
                arg_strs.append(param_name + ": " + zig_ty)
            i += 1
        ret_type_any = stmt.get("return_type")
        ret_py = ret_type_any.strip() if isinstance(ret_type_any, str) else ""
        ret_type = self._zig_type(ret_py)
        fn_kw = "pub fn" if self.is_submodule else "fn"
        self._emit_line(fn_kw + " " + name + "(" + ", ".join(arg_strs) + ") " + ret_type + " {")
        self.indent += 1
        # Copy renamed params to mutable local vars
        for orig_name, param_alias in mutable_copies:
            self._emit_line("var " + orig_name + " = " + param_alias + ";")
        self._push_function_context(stmt, arg_names, args)
        self._emit_block(stmt.get("body"))
        self._pop_function_context()
        self.indent -= 1
        self._emit_line("}")
        self._emit_line("")

    def _emit_if(self, stmt: dict[str, Any]) -> None:
        test_node = stmt.get("test")
        # Skip dead branches (isinstance lowered to false, constant false)
        if isinstance(test_node, dict):
            if test_node.get("kind") == "Constant" and test_node.get("value") is False:
                orelse = self._dict_list(stmt.get("orelse"))
                for sub in orelse:
                    self._emit_stmt(sub)
                return
            if test_node.get("kind") == "IsInstance":
                orelse = self._dict_list(stmt.get("orelse"))
                for sub in orelse:
                    self._emit_stmt(sub)
                return
        test = self._render_cond_expr(test_node)
        self._emit_line("if (" + test + ") {")
        self.indent += 1
        self._emit_block(stmt.get("body"))
        self.indent -= 1
        orelse = self._dict_list(stmt.get("orelse"))
        if len(orelse) > 0:
            self._emit_line("} else {")
            self.indent += 1
            for sub in orelse:
                self._emit_stmt(sub)
            self.indent -= 1
        self._emit_line("}")

    def _emit_for_core(self, stmt: dict[str, Any]) -> None:
        target_plan = stmt.get("target_plan")
        iter_plan = stmt.get("iter_plan")
        target_name = "_"
        tuple_unpack_names: list[str] = []
        if isinstance(target_plan, dict) and target_plan.get("kind") == "TupleTarget":
            # タプル展開: for (item, item2) in iterable → capture as struct then unpack
            elements = target_plan.get("elements")
            if isinstance(elements, list):
                for elt in elements:
                    if isinstance(elt, dict) and elt.get("kind") == "NameTarget":
                        tuple_unpack_names.append(_safe_ident(elt.get("id"), "v"))
            target_name = "__for_tuple_" + str(self.tmp_seq)
            self.tmp_seq += 1
        elif isinstance(target_plan, dict) and target_plan.get("kind") == "NameTarget":
            target_name = _safe_ident(target_plan.get("id"), "i")
        elif isinstance(stmt.get("target"), dict) and stmt["target"].get("kind") == "Name":
            target_name = _safe_ident(stmt["target"].get("id"), "i")
        if isinstance(iter_plan, dict) and iter_plan.get("kind") == "StaticRangeForPlan":
            self._emit_static_range_for(stmt, target_name, iter_plan)
            return
        if isinstance(iter_plan, dict) and iter_plan.get("kind") == "RuntimeIterForPlan":
            iter_expr_node = iter_plan.get("iter_expr")
            if isinstance(iter_expr_node, dict):
                iter_expr = self._render_expr(iter_expr_node)
                iter_type = self._get_expr_type(iter_expr_node)
                if iter_type.startswith("list[") or iter_type in {"bytearray", "bytes"}:
                    elem = "i64"
                    if iter_type.startswith("list[") and iter_type.endswith("]"):
                        elem = self._zig_type(iter_type[5:-1].strip())
                    elif iter_type in {"bytearray", "bytes"}:
                        elem = "u8"
                    iter_expr = "pytra.list_items(" + iter_expr + ", " + elem + ")"
                capture_name = target_name
                reassign_after_capture = False
                # If loop variable is unused in body, use _ to avoid Zig error
                if not self._body_uses_name(self._strip_dead_branches(stmt.get("body")), target_name):
                    capture_name = "_"
                elif target_name in self._hoisted_var_names:
                    capture_name = "_cap_" + target_name
                    reassign_after_capture = True
                self._emit_line("for (" + iter_expr + ") |" + capture_name + "| {")
                self.indent += 1
                if reassign_after_capture:
                    self._emit_line(target_name + " = " + capture_name + ";")
                elif len(self._local_var_stack) > 0:
                    self._current_local_vars().add(target_name)
                self._emit_tuple_unpack_in_for(tuple_unpack_names, capture_name)
                self._emit_block(stmt.get("body"))
                self.indent -= 1
                self._emit_line("}")
                return
        iter_any = stmt.get("iter")
        if isinstance(iter_any, dict) and iter_any.get("kind") == "Call":
            func_any = iter_any.get("func")
            if isinstance(func_any, dict) and func_any.get("kind") == "Name":
                fname = str(func_any.get("id"))
                if fname == "range":
                    self._emit_range_for_from_call(stmt, target_name, iter_any)
                    return
        iter_expr = self._render_expr(iter_any)
        iter_type = self._get_expr_type(iter_any) if isinstance(iter_any, dict) else ""
        if iter_type.startswith("list[") or iter_type in {"bytearray", "bytes"}:
            elem = "i64"
            if iter_type.startswith("list[") and iter_type.endswith("]"):
                elem = self._zig_type(iter_type[5:-1].strip())
            elif iter_type in {"bytearray", "bytes"}:
                elem = "u8"
            iter_expr = "pytra.list_items(" + iter_expr + ", " + elem + ")"
        capture_name = target_name
        reassign_after_capture = False
        if len(self._local_var_stack) > 0 and target_name in self._current_local_vars():
            capture_name = "_cap_" + target_name
            reassign_after_capture = True
        self._emit_line("for (" + iter_expr + ") |" + capture_name + "| {")
        self.indent += 1
        if reassign_after_capture:
            self._emit_line(target_name + " = " + capture_name + ";")
        elif len(self._local_var_stack) > 0:
            self._current_local_vars().add(target_name)
        self._emit_tuple_unpack_in_for(tuple_unpack_names, capture_name)
        self._emit_block(stmt.get("body"))
        self.indent -= 1
        self._emit_line("}")

    def _emit_tuple_unpack_in_for(self, names: list[str], capture: str) -> None:
        """for ループキャプチャ変数からタプルフィールドを展開する。"""
        if len(names) == 0:
            return
        i = 0
        while i < len(names):
            n = names[i]
            decl_kw = "var" if self._is_var_mutated(n) else "const"
            self._emit_line(decl_kw + " " + n + " = " + capture + "._" + str(i) + ";")
            if len(self._local_var_stack) > 0:
                self._current_local_vars().add(n)
            i += 1

    def _emit_for_range(self, stmt: dict[str, Any]) -> None:
        """ForRange ノード（ListComp lowering 由来）を while ループに展開する。"""
        target_node = stmt.get("target")
        target_name = "_unused"
        if isinstance(target_node, dict) and target_node.get("kind") == "Name":
            target_name = _safe_ident(target_node.get("id"), "i")
        start = self._render_expr(stmt.get("start"))
        stop = self._render_expr(stmt.get("stop"))
        step_node = stmt.get("step")
        step = self._render_expr(step_node) if isinstance(step_node, dict) else "1"
        already_exists = target_name in self._hoisted_var_names or (len(self._local_var_stack) > 0 and target_name in self._current_local_vars())
        if already_exists:
            self._emit_line(target_name + " = " + start + ";")
        else:
            self._emit_line("var " + target_name + ": i64 = " + start + ";")
            if len(self._local_var_stack) > 0:
                self._current_local_vars().add(target_name)
        self._emit_line("while (" + target_name + " < " + stop + ") : (" + target_name + " += " + step + ") {")
        self.indent += 1
        self._emit_block(stmt.get("body"))
        self.indent -= 1
        self._emit_line("}")

    def _emit_static_range_for(self, stmt: dict[str, Any], target_name: str, plan: dict[str, Any]) -> None:
        start = self._render_expr(plan.get("start"))
        stop = self._render_expr(plan.get("stop"))
        step_any = plan.get("step")
        step = self._render_expr(step_any) if isinstance(step_any, dict) else "1"
        already_exists = target_name in self._hoisted_var_names or (len(self._local_var_stack) > 0 and target_name in self._current_local_vars())
        if already_exists:
            # Reuse existing variable (avoid shadow)
            self._emit_line(target_name + " = " + start + ";")
        else:
            self._emit_line("var " + target_name + ": i64 = " + start + ";")
            if len(self._local_var_stack) > 0:
                self._current_local_vars().add(target_name)
        self._emit_line("while (" + target_name + " < " + stop + ") : (" + target_name + " += " + step + ") {")
        self.indent += 1
        self._emit_block(stmt.get("body"))
        self.indent -= 1
        self._emit_line("}")

    def _emit_range_for_from_call(self, stmt: dict[str, Any], target_name: str, iter_node: dict[str, Any]) -> None:
        args_any = iter_node.get("args")
        args = args_any if isinstance(args_any, list) else []
        if len(args) == 1:
            end = self._render_expr(args[0])
            self._emit_line("var " + target_name + ": i64 = 0;")
            self._emit_line("while (" + target_name + " < " + end + ") : (" + target_name + " += 1) {")
        elif len(args) == 2:
            start = self._render_expr(args[0])
            end = self._render_expr(args[1])
            self._emit_line("var " + target_name + ": i64 = " + start + ";")
            self._emit_line("while (" + target_name + " < " + end + ") : (" + target_name + " += 1) {")
        elif len(args) == 3:
            start = self._render_expr(args[0])
            end = self._render_expr(args[1])
            step = self._render_expr(args[2])
            self._emit_line("var " + target_name + ": i64 = " + start + ";")
            self._emit_line("while (" + target_name + " < " + end + ") : (" + target_name + " += " + step + ") {")
        else:
            self._emit_line("// unsupported range args count")
            self._emit_line("while (false) {")
        self.indent += 1
        if len(self._local_var_stack) > 0:
            self._current_local_vars().add(target_name)
        self._emit_block(stmt.get("body"))
        self.indent -= 1
        self._emit_line("}")

    def _emit_while(self, stmt: dict[str, Any]) -> None:
        test = self._render_cond_expr(stmt.get("test"))
        self._emit_line("while (" + test + ") {")
        self.indent += 1
        self._emit_block(stmt.get("body"))
        self.indent -= 1
        self._emit_line("}")

    def _scan_init_fields(self, body: list[dict[str, Any]], arg_types: dict[str, Any]) -> list[tuple[str, str]]:
        """__init__ body から self.field = ... のフィールドを抽出する。"""
        fields: list[tuple[str, str]] = []
        seen: set[str] = set()
        for stmt in body:
            kind = stmt.get("kind")
            if kind not in {"Assign", "AnnAssign"}:
                continue
            target = stmt.get("target")
            if not isinstance(target, dict) or target.get("kind") != "Attribute":
                continue
            val = target.get("value")
            if not isinstance(val, dict) or val.get("kind") != "Name" or val.get("id") != "self":
                continue
            field_name = _safe_ident(target.get("attr"), "field")
            if field_name in seen:
                continue
            seen.add(field_name)
            decl_type = ""
            if kind == "AnnAssign":
                decl_type = self._infer_decl_type(stmt)
            if decl_type == "":
                value_node = stmt.get("value")
                if isinstance(value_node, dict):
                    if value_node.get("kind") == "Name":
                        src_name = str(value_node.get("id"))
                        src_type = arg_types.get(src_name)
                        if isinstance(src_type, str) and src_type.strip() != "":
                            decl_type = src_type.strip()
                    if decl_type == "":
                        decl_type = self._get_expr_type(value_node)
            fields.append((field_name, decl_type))
        return fields

    def _get_base_methods(self, cls_name: str) -> list[tuple[str, str]]:
        """基底クラスのメソッド名と基底クラス名のペアを再帰的に収集する。"""
        base = self._class_base.get(cls_name, "")
        if base == "":
            return []
        result: list[tuple[str, str]] = []
        base_methods = self._class_methods.get(base, set())
        for m in base_methods:
            result.append((m, base))
        result.extend(self._get_base_methods(base))
        return result

    def _emit_class_def(self, stmt: dict[str, Any]) -> None:
        cls_name = _safe_ident(stmt.get("name"), "Class")
        base_name = self._class_base.get(cls_name, "")
        # Track class context for param shadowing detection
        old_class_name = self._current_class_name
        old_class_methods = self._current_class_methods
        self._current_class_name = cls_name
        body_all = self._dict_list(stmt.get("body"))
        self._current_class_methods = [s for s in body_all if isinstance(s, dict) and s.get("kind") == "FunctionDef"]
        struct_kw = "pub const" if self.is_submodule else "const"
        self._emit_line(struct_kw + " " + cls_name + " = struct {")
        self.indent += 1
        # composition: 基底クラスフィールド
        if base_name != "":
            self._emit_line("_base: " + base_name + " = " + base_name + "{},")
        body = self._dict_list(stmt.get("body"))
        # __init__ body から struct フィールドを抽出
        emitted_fields: set[str] = set()
        dataclass_fields: list[str] = []
        if bool(stmt.get("dataclass")):
            for sub in body:
                if sub.get("kind") != "AnnAssign":
                    continue
                target_any = sub.get("target")
                if isinstance(target_any, dict) and target_any.get("kind") == "Name":
                    field_name = _safe_ident(target_any.get("id"), "field")
                    decl_type_any = sub.get("decl_type")
                    decl_type = decl_type_any.strip() if isinstance(decl_type_any, str) else ""
                    if decl_type == "":
                        anno_any = sub.get("annotation")
                        if isinstance(anno_any, str):
                            decl_type = anno_any.strip()
                    zig_ty = self._zig_type(decl_type)
                    value_node = sub.get("value")
                    if isinstance(value_node, dict):
                        default_val = self._render_expr(value_node)
                        self._emit_line(field_name + ": " + zig_ty + " = " + default_val + ",")
                    else:
                        self._emit_line(field_name + ": " + zig_ty + ",")
                    dataclass_fields.append(field_name)
                    emitted_fields.add(field_name)
        for sub in body:
            if sub.get("kind") == "FunctionDef" and sub.get("name") == "__init__":
                init_body = self._dict_list(sub.get("body"))
                init_arg_types = sub.get("arg_types")
                init_arg_types = init_arg_types if isinstance(init_arg_types, dict) else {}
                init_fields = self._scan_init_fields(init_body, init_arg_types)
                for field_name, field_type in init_fields:
                    if field_name not in emitted_fields:
                        zig_ty = self._zig_type(field_type)
                        self._emit_line(field_name + ": " + zig_ty + " = undefined,")
                        emitted_fields.add(field_name)
                break
        for sub in body:
            if sub.get("kind") == "AnnAssign" and bool(stmt.get("dataclass")):
                continue
            if sub.get("kind") == "FunctionDef":
                self._emit_class_method(cls_name, sub)
            elif sub.get("kind") == "AnnAssign":
                target_any = sub.get("target")
                if isinstance(target_any, dict) and target_any.get("kind") == "Name":
                    field_name = _safe_ident(target_any.get("id"), "field")
                    # 静的フィールドはモジュールスコープに emit 済み → struct から除外
                    static_field_names = {sf[0] for sf in self._static_fields.get(cls_name, [])}
                    if field_name in static_field_names:
                        continue
                    decl_type_any = sub.get("decl_type")
                    decl_type = decl_type_any.strip() if isinstance(decl_type_any, str) else ""
                    if decl_type == "":
                        anno_any = sub.get("annotation")
                        if isinstance(anno_any, str):
                            decl_type = anno_any.strip()
                    zig_ty = self._zig_type(decl_type)
                    if field_name not in emitted_fields:
                        value_node = sub.get("value")
                        if isinstance(value_node, dict):
                            default_val = self._render_expr(value_node)
                            self._emit_line(field_name + ": " + zig_ty + " = " + default_val + ",")
                        else:
                            self._emit_line(field_name + ": " + zig_ty + " = undefined,")
                        emitted_fields.add(field_name)
        # 基底クラスの未 override メソッドの委譲関数を生成
        if base_name != "":
            own_methods = self._class_methods.get(cls_name, set())
            base_method_pairs = self._get_base_methods(cls_name)
            for method_name, origin_cls in base_method_pairs:
                if method_name not in own_methods:
                    ret_type = self._class_return_types.get(origin_cls, {}).get(method_name, "")
                    zig_ret = self._zig_type(ret_type)
                    self._emit_line("pub fn " + method_name + "(_: *const " + cls_name + ") " + zig_ret + " {")
                    self.indent += 1
                    self._emit_line("return " + origin_cls + "." + method_name + "(undefined);")
                    self.indent -= 1
                    self._emit_line("}")
                    self._emit_line("")
        self.indent -= 1
        self._emit_line("};")
        self._emit_line("")
        self._current_class_name = old_class_name
        self._current_class_methods = old_class_methods

    def _emit_class_method(self, cls_name: str, stmt: dict[str, Any]) -> None:
        method_name = _safe_ident(stmt.get("name"), "method")
        arg_order_any = stmt.get("arg_order")
        arg_order = arg_order_any if isinstance(arg_order_any, list) else []
        args: list[str] = []
        arg_strs: list[str] = []
        arg_types_any = stmt.get("arg_types")
        arg_types = arg_types_any if isinstance(arg_types_any, dict) else {}
        has_self = False
        self_used = self._body_uses_name(stmt.get("body"), "self")
        # EAST3 の mutates_self フラグを優先（call graph 伝播済み）
        ms_flag = stmt.get("mutates_self")
        if isinstance(ms_flag, bool):
            self_mutated = ms_flag
        else:
            self_mutated = self._body_mutates_self(stmt.get("body"))
            if not self_mutated:
                self_mutated = cls_name in self._classes_with_mut_method
        sibling_names: set[str] = set()
        for sib in self._current_class_methods:
            sn = sib.get("name", "") if isinstance(sib, dict) else ""
            if sn != "":
                sibling_names.add(sn)
        live_body = self._strip_dead_branches(stmt.get("body"))
        param_renames: dict[str, str] = {}  # original → renamed
        for i, arg in enumerate(arg_order):
            arg_name = _safe_ident(arg, "arg")
            if i == 0 and arg_name == "self":
                has_self = True
                if not self_used:
                    arg_strs.append("_: *const " + cls_name)
                elif self_mutated:
                    arg_strs.append("self: *" + cls_name)
                else:
                    arg_strs.append("self: *const " + cls_name)
                continue
            # Unused param (not referenced in live branches) → _
            if not self._body_uses_name(live_body, arg_name):
                args.append("_")
                zig_ty = self._resolve_arg_zig_type(arg_name, arg, arg_types)
                arg_strs.append("_: " + zig_ty)
                continue
            # Param name shadows sibling method → rename + track mapping
            if arg_name in sibling_names and arg_name != method_name:
                new_name = arg_name + "_arg"
                param_renames[arg_name] = new_name
                arg_name = new_name
            args.append(arg_name)
            zig_ty = self._resolve_arg_zig_type(arg_name, arg, arg_types)
            arg_strs.append(arg_name + ": " + zig_ty)
        prev_class = self.current_class_name
        self.current_class_name = cls_name
        ret_type_any = stmt.get("return_type")
        ret_py = ret_type_any.strip() if isinstance(ret_type_any, str) else ""
        ret_type = self._zig_type(ret_py)
        if method_name == "__init__":
            self._emit_line("pub fn init(" + ", ".join(arg_strs[1:]) + ") " + cls_name + " {")
            self.indent += 1
            self._emit_line("var self: " + cls_name + " = undefined;")
            self._param_rename_stack.append(param_renames)
            self._push_function_context(stmt, args, arg_order[1:] if len(arg_order) > 0 else arg_order)
            self._emit_block(stmt.get("body"))
            self._pop_function_context()
            self._param_rename_stack.pop()
            self._emit_line("return self;")
            self.indent -= 1
            self._emit_line("}")
            self._emit_line("")
        else:
            # Emit method body to a temporary buffer, then post-check for unused params
            saved_lines = self.lines
            self.lines = []
            self.indent += 1
            self._param_rename_stack.append(param_renames)
            self._push_function_context(stmt, args, arg_order[1:] if len(arg_order) > 0 else arg_order)
            self._emit_block(stmt.get("body"))
            self._pop_function_context()
            self._param_rename_stack.pop()
            self.indent -= 1
            method_body_lines = self.lines
            self.lines = saved_lines
            # Determine which non-self params are actually used in generated code
            body_text = "\n".join(method_body_lines)
            actual_unused: list[str] = []
            for p in args:
                if p == "_" or p == "self":
                    continue
                # Check if param name (or its renamed form) appears in the generated body
                check_name = p
                if check_name not in body_text:
                    actual_unused.append(p)
            # Rebuild arg_strs with _ for truly unused params
            final_arg_strs: list[str] = []
            for astr in arg_strs:
                replaced = False
                for unused_p in actual_unused:
                    if astr.startswith(unused_p + ":"):
                        final_arg_strs.append("_: " + astr.split(": ", 1)[1])
                        replaced = True
                        break
                if not replaced:
                    final_arg_strs.append(astr)
            self._emit_line("pub fn " + method_name + "(" + ", ".join(final_arg_strs) + ") " + ret_type + " {")
            self.lines.extend(method_body_lines)
            self._emit_line("}")
            self._emit_line("")
        self.current_class_name = prev_class

    def _emit_tuple_assign(self, target_any: Any, value_any: Any) -> None:
        if not isinstance(target_any, dict):
            return
        # elements (EAST3) or elts (legacy)
        elts_any = target_any.get("elements")
        if not isinstance(elts_any, list):
            elts_any = target_any.get("elts")
        elts = elts_any if isinstance(elts_any, list) else []
        value_expr = self._render_expr(value_any)
        tmp = "__tmp_" + str(self.tmp_seq)
        self.tmp_seq += 1
        self._emit_line("const " + tmp + " = " + value_expr + ";")
        i = 0
        while i < len(elts):
            elt = elts[i]
            if isinstance(elt, dict):
                field_access = tmp + "._" + str(i)
                elt_kind = elt.get("kind")
                # Subscript target → list_set
                if elt_kind == "Subscript":
                    sub_val = elt.get("value")
                    sub_val_type = self._get_expr_type(sub_val) if isinstance(sub_val, dict) else ""
                    if sub_val_type.startswith("list[") or sub_val_type in {"bytearray", "bytes"}:
                        obj_expr = self._render_expr(sub_val)
                        idx_expr = self._render_expr(elt.get("slice"))
                        elem = "i64"
                        if sub_val_type.startswith("list[") and sub_val_type.endswith("]"):
                            elem = self._zig_type(sub_val_type[5:-1].strip())
                        elif sub_val_type in {"bytearray", "bytes"}:
                            elem = "u8"
                        val_cast = "@intCast(" + field_access + ")" if elem in {"u8", "i8", "i16", "u16", "i32", "u32", "i64", "u64"} else field_access
                        self._emit_line("pytra.list_set(" + obj_expr + ", " + elem + ", " + idx_expr + ", " + val_cast + ");")
                        i += 1
                        continue
                name = self._render_target(elt)
                # EAST3 unused: true on tuple element → use _ discard
                is_unused_elt = bool(elt.get("unused", False))
                elt_id_raw = elt.get("id", "") if elt_kind == "Name" else ""
                if is_unused_elt or (isinstance(elt_id_raw, str) and elt_id_raw == "_"):
                    self._emit_line("_ = " + field_access + ";")
                    i += 1
                    continue
                if len(self._local_var_stack) > 0 and elt_kind == "Name":
                    elt_name = _safe_ident(elt.get("id"), "value")
                    if elt_name not in self._current_local_vars():
                        self._current_local_vars().add(elt_name)
                        decl_kw = "var" if self._is_var_mutated(elt_name) else "const"
                        self._emit_line(decl_kw + " " + name + " = " + field_access + ";")
                        i += 1
                        continue
                self._emit_line(name + " = " + field_access + ";")
            i += 1

    def _emit_swap(self, stmt: dict[str, Any]) -> None:
        lhs_node = stmt.get("lhs") if stmt.get("lhs") is not None else stmt.get("left")
        rhs_node = stmt.get("rhs") if stmt.get("rhs") is not None else stmt.get("right")
        # list Subscript の swap: list_get + list_set
        lhs_is_list_sub = self._is_list_subscript(lhs_node)
        rhs_is_list_sub = self._is_list_subscript(rhs_node)
        if lhs_is_list_sub and rhs_is_list_sub:
            tmp = "__swap_tmp_" + str(self.tmp_seq)
            self.tmp_seq += 1
            lobj, lidx, lelem = self._list_subscript_parts(lhs_node)
            robj, ridx, relem = self._list_subscript_parts(rhs_node)
            self._emit_line("const " + tmp + " = pytra.list_get(" + lobj + ", " + lelem + ", " + lidx + ");")
            self._emit_line("pytra.list_set(" + lobj + ", " + lelem + ", " + lidx + ", pytra.list_get(" + robj + ", " + relem + ", " + ridx + "));")
            self._emit_line("pytra.list_set(" + robj + ", " + relem + ", " + ridx + ", " + tmp + ");")
            return
        left = self._render_target(lhs_node)
        right = self._render_target(rhs_node)
        tmp = "__swap_tmp_" + str(self.tmp_seq)
        self.tmp_seq += 1
        self._emit_line("const " + tmp + " = " + left + ";")
        self._emit_line(left + " = " + right + ";")
        self._emit_line(right + " = " + tmp + ";")

    def _is_list_subscript(self, node: Any) -> bool:
        if not isinstance(node, dict) or node.get("kind") != "Subscript":
            return False
        sub_val = node.get("value")
        sub_type = self._get_expr_type(sub_val) if isinstance(sub_val, dict) else ""
        return sub_type.startswith("list[") or sub_type in {"bytearray", "bytes"}

    def _list_subscript_parts(self, node: dict[str, Any]) -> tuple[str, str, str]:
        sub_val = node.get("value")
        sub_type = self._get_expr_type(sub_val) if isinstance(sub_val, dict) else ""
        obj_expr = self._render_expr(sub_val)
        idx_expr = self._render_expr(node.get("slice"))
        elem = "i64"
        if sub_type.startswith("list[") and sub_type.endswith("]"):
            elem = self._zig_type(sub_type[5:-1].strip())
        elif sub_type in {"bytearray", "bytes"}:
            elem = "u8"
        return obj_expr, idx_expr, elem

    def _render_target(self, node: Any) -> str:
        if not isinstance(node, dict):
            return "_"
        nd: dict[str, Any] = node
        kind = nd.get("kind")
        if kind == "Name":
            return _safe_ident(nd.get("id"), "value")
        if kind == "Attribute":
            val_node = nd.get("value")
            attr = _safe_ident(nd.get("attr"), "attr")
            if isinstance(val_node, dict) and val_node.get("kind") == "Name":
                owner = _safe_ident(val_node.get("id"), "")
                if owner in self._static_fields:
                    for sf_name, _, _ in self._static_fields[owner]:
                        if sf_name == attr:
                            return "Module_" + owner + "_" + attr
            obj = self._render_expr(val_node)
            return obj + "." + attr
        if kind == "Subscript":
            obj = self._render_expr(nd.get("value"))
            idx = self._render_expr(nd.get("slice"))
            return obj + "[" + idx + "]"
        return "_"

    def _render_cond_expr(self, expr_any: Any) -> str:
        if not isinstance(expr_any, dict):
            return "true"
        ed: dict[str, Any] = expr_any
        kind = ed.get("kind")
        if kind == "Constant":
            v = ed.get("value")
            if v is True:
                return "true"
            if v is False:
                return "false"
        if kind == "Call":
            func_any = ed.get("func")
            if isinstance(func_any, dict) and func_any.get("kind") == "Name":
                fname = _safe_ident(func_any.get("id"), "")
                if fname == "__pytra_truthy":
                    args_any = ed.get("args")
                    args = args_any if isinstance(args_any, list) else []
                    if len(args) > 0:
                        return "pytra.truthy(" + self._render_expr(args[0]) + ")"
        rendered = self._render_expr(expr_any)
        # i64 の条件式は != 0 で bool に変換
        expr_type = self._lookup_expr_type(expr_any) if isinstance(expr_any, dict) else ""
        if expr_type in {"int64", "int32", "int16", "int8", "uint8", "uint16", "uint32", "uint64"}:
            return "(" + rendered + " != 0)"
        # list/Obj の条件式は list_len > 0 に変換（Python の truthiness）
        if expr_type.startswith("list[") or expr_type in {"bytearray", "bytes"}:
            elem = "i64"
            if expr_type.startswith("list[") and expr_type.endswith("]"):
                elem = self._zig_type(expr_type[5:-1].strip())
            elif expr_type in {"bytearray", "bytes"}:
                elem = "u8"
            return "(pytra.list_len(" + rendered + ", " + elem + ") > 0)"
        return rendered

    def _render_expr(self, expr_any: Any) -> str:
        if expr_any is None:
            return "null"
        if not isinstance(expr_any, dict):
            return str(expr_any)
        ed: dict[str, Any] = expr_any
        kind = ed.get("kind")
        if kind == "Constant":
            return self._render_constant(ed)
        if kind == "Name":
            name = _safe_ident(ed.get("id"), "value")
            if name == "True":
                return "true"
            if name == "False":
                return "false"
            if name == "None":
                return "null"
            # Apply param rename mapping (for Zig shadowing avoidance)
            i_pr = len(self._param_rename_stack) - 1
            while i_pr >= 0:
                renamed = self._param_rename_stack[i_pr].get(name)
                if renamed is not None:
                    return renamed
                i_pr -= 1
            return name
        if kind == "BinOp":
            left = self._render_expr(ed.get("left"))
            right = self._render_expr(ed.get("right"))
            op = str(ed.get("op"))
            # BinOp の子は常に括弧で囲む（浮動小数点の演算順序を Python と完全一致させる）
            left_type = self._lookup_expr_type(ed.get("left"))
            right_type = self._lookup_expr_type(ed.get("right"))
            # Fallback: check resolved_type if _lookup_expr_type returns empty
            if left_type == "":
                left_type = self._get_expr_type(ed.get("left"))
            if right_type == "":
                right_type = self._get_expr_type(ed.get("right"))
            # int/float 混合演算: int 側を @floatFromInt でラップ
            _INT_TYPES = {"int64", "int32", "int16", "int8", "uint8", "uint16", "uint32", "uint64"}
            _FLOAT_TYPES = {"float64", "float32", "float"}
            if op not in {"LShift", "RShift", "BitOr", "BitXor", "BitAnd", "FloorDiv"}:
                if left_type in _INT_TYPES and right_type in _FLOAT_TYPES:
                    left = "@as(f64, @floatFromInt(" + left + "))"
                elif left_type in _FLOAT_TYPES and right_type in _INT_TYPES:
                    right = "@as(f64, @floatFromInt(" + right + "))"
            if op == "Add":
                if left_type == "str" or right_type == "str":
                    return "pytra.str_concat(" + left + ", " + right + ")"
            # list * int → list replication (ブロック式)
            if op == "Mult":
                if left_type.startswith("list[") or left_type in {"bytearray", "bytes"}:
                    # [val] * n → make_list + n 回 append
                    left_node = ed.get("left")
                    elem_type = "i64"
                    if left_type.startswith("list[") and left_type.endswith("]"):
                        elem_type = self._zig_type(left_type[5:-1].strip())
                    elif left_type in {"bytearray", "bytes"}:
                        elem_type = "u8"
                    # 左辺が単一要素リテラルなら直接展開
                    if isinstance(left_node, dict) and left_node.get("kind") == "List":
                        elts_any = left_node.get("elements")
                        if not isinstance(elts_any, list):
                            elts_any = left_node.get("elts")
                        elts = elts_any if isinstance(elts_any, list) else []
                        if len(elts) == 1:
                            val = self._render_expr(elts[0])
                            blk = "__rep_blk_" + str(self.tmp_seq)
                            self.tmp_seq += 1
                            return blk + ": { const __rl = pytra.make_list(" + elem_type + "); var __ri: i64 = 0; while (__ri < " + right + ") : (__ri += 1) { pytra.list_append(__rl, " + elem_type + ", " + val + "); } break :" + blk + " __rl; }"
                    # 一般ケース: Obj list × int → pytra.Obj (未対応 fallback)
                    return "pytra.empty_list()"
            if op == "Pow":
                return "std.math.pow(f64, " + left + ", " + right + ")"
            if op == "FloorDiv":
                return "@divFloor(" + left + ", " + right + ")"
            if op == "Div":
                left_type = self._lookup_expr_type(ed.get("left"))
                right_type = self._lookup_expr_type(ed.get("right"))
                if left_type in {"float64", "float32", "float"} or right_type in {"float64", "float32", "float"}:
                    return "(" + left + " / " + right + ")"
                return "(@as(f64, @floatFromInt(" + left + ")) / @as(f64, @floatFromInt(" + right + ")))"
            if op == "Mod":
                return "@mod(" + left + ", " + right + ")"
            if op in {"LShift", "RShift"}:
                sym = _binop_symbol(op)
                # LHS を常に i64 に昇格（EAST3 の型と Zig の実際の型が異なる場合の安全策）
                left = "@as(i64, " + left + ")"
                return "(" + left + " " + sym + " @intCast(" + right + "))"
            sym = _binop_symbol(op)
            return "(" + left + " " + sym + " " + right + ")"
        if kind == "UnaryOp":
            op = str(ed.get("op"))
            operand = self._render_expr(ed.get("operand"))
            if op == "USub":
                return "-" + operand
            if op == "UAdd":
                return "+" + operand
            if op == "Not":
                return "!" + operand
            if op == "Invert":
                return "~" + operand
            return operand
        if kind == "Compare":
            return self._render_compare(ed)
        if kind == "BoolOp":
            op = str(ed.get("op"))
            values_any = ed.get("values")
            values = values_any if isinstance(values_any, list) else []
            parts: list[str] = []
            for v in values:
                parts.append(self._render_expr(v))
            joiner = " and " if op == "And" else " or "
            return "(" + joiner.join(parts) + ")"
        if kind == "Unbox":
            return self._render_expr(ed.get("value"))
        if kind == "Box":
            return self._render_expr(ed.get("value"))
        if kind == "ObjStr":
            inner = self._render_expr(ed.get("value"))
            return "pytra.to_str(" + inner + ")"
        if kind == "ObjLen":
            inner = self._render_expr(ed.get("value"))
            inner_type = self._lookup_expr_type(ed.get("value"))
            elem = "i64"
            if inner_type.startswith("list[") and inner_type.endswith("]"):
                elem = self._zig_type(inner_type[5:-1].strip())
            elif inner_type in {"bytearray", "bytes"}:
                elem = "u8"
            # ObjLen は Python の len() なので、Obj コンテナ前提で list_len を使う
            zig_inner_type = self._zig_type(inner_type) if inner_type != "" else ""
            if inner_type.startswith("list[") or inner_type in {"bytearray", "bytes"} or zig_inner_type == "pytra.Obj" or inner_type in {"", "unknown"}:
                return "pytra.list_len(" + inner + ", " + elem + ")"
            return "@as(i64, @intCast(" + inner + ".len))"
        if kind == "Call":
            return self._render_call(ed)
        if kind == "Attribute":
            val_node = ed.get("value")
            attr = _safe_ident(ed.get("attr"), "attr")
            if isinstance(val_node, dict) and val_node.get("kind") == "Name":
                owner = _safe_ident(val_node.get("id"), "")
                if owner in self._static_fields:
                    for sf_name, _, _ in self._static_fields[owner]:
                        if sf_name == attr:
                            return "Module_" + owner + "_" + attr
            obj = self._render_expr(val_node)
            # Obj-managed list の .len → pytra.list_len
            if attr == "len":
                val_type = self._lookup_expr_type(val_node) if isinstance(val_node, dict) else ""
                zig_val_type = self._zig_type(val_type) if val_type != "" else ""
                # Obj 型（list/dict/unknown のコンテナ）なら list_len を使う
                is_obj_container = val_type.startswith("list[") or val_type in {"bytearray", "bytes"} or zig_val_type == "pytra.Obj"
                if is_obj_container:
                    elem = "i64"
                    if val_type.startswith("list[") and val_type.endswith("]"):
                        elem = self._zig_type(val_type[5:-1].strip())
                    elif val_type in {"bytearray", "bytes"}:
                        elem = "u8"
                    return "pytra.list_len(" + obj + ", " + elem + ")"
            return obj + "." + attr
        if kind == "Subscript":
            value_node = ed.get("value")
            obj = self._render_expr(value_node)
            slice_node = ed.get("slice")
            obj_type = self._lookup_expr_type(value_node)
            # 文字列スライス: str[start:end]
            if isinstance(slice_node, dict) and slice_node.get("kind") == "Slice":
                lower = self._render_expr(slice_node.get("lower")) if slice_node.get("lower") is not None else "0"
                upper_node = slice_node.get("upper")
                if upper_node is not None:
                    upper = self._render_expr(upper_node)
                else:
                    upper = "@as(i64, @intCast(" + obj + ".len))"
                if obj_type == "str":
                    return "pytra.str_slice(" + obj + ", " + lower + ", " + upper + ")"
                return obj + "[" + lower + ".." + upper + "]"
            idx = self._render_expr(slice_node)
            if obj_type.startswith("dict["):
                # dict get with default
                parts = self._split_generic(obj_type[5:-1])
                val_zig = "i64"
                if len(parts) == 2:
                    val_zig = self._zig_type(parts[1].strip())
                return "pytra.dict_get_default(" + val_zig + ", " + obj + ", " + idx + ", 0)"
            if obj_type.startswith("list[") or obj_type in {"bytearray", "bytes"}:
                elem_type = "i64"
                if obj_type.startswith("list[") and obj_type.endswith("]"):
                    elem_type = self._zig_type(obj_type[5:-1].strip())
                elif obj_type in {"bytearray", "bytes"}:
                    elem_type = "u8"
                return "pytra.list_get(" + obj + ", " + elem_type + ", " + idx + ")"
            # 文字列インデックス: str[i]
            if obj_type == "str":
                return "pytra.str_index(" + obj + ", " + idx + ")"
            return obj + "[@intCast(" + idx + ")]"
        if kind == "List":
            elts_any = ed.get("elts")
            if not isinstance(elts_any, list):
                elts_any = ed.get("elements")
            elts = elts_any if isinstance(elts_any, list) else []
            items = [self._render_expr(e) for e in elts]
            resolved = self._get_expr_type(ed)
            if resolved.startswith("list["):
                inner = resolved[5:-1].strip() if resolved.endswith("]") else ""
                zig_elem = self._zig_type(inner) if inner != "" else "i64"
                # タプル型要素の list はブロック式で make_list + append に展開
                if inner.startswith("tuple["):
                    if len(items) == 0:
                        return "pytra.make_list(" + zig_elem + ")"
                    blk_label = "__list_blk_" + str(self.tmp_seq)
                    self.tmp_seq += 1
                    parts: list[str] = []
                    parts.append(blk_label + ": {")
                    parts.append(" const __bl = pytra.make_list(" + zig_elem + ");")
                    for item in items:
                        parts.append(" pytra.list_append(__bl, " + zig_elem + ", " + item + ");")
                    parts.append(" break :" + blk_label + " __bl; }")
                    return "".join(parts)
                return "pytra.list_from(" + zig_elem + ", &[_]" + zig_elem + "{ " + ", ".join(items) + " })"
            if len(items) == 0:
                return "pytra.list_from(i64, &[_]i64{})"
            return "&.{ " + ", ".join(items) + " }"
        if kind == "Tuple":
            elts_any = ed.get("elts")
            if not isinstance(elts_any, list):
                elts_any = ed.get("elements")
            elts = elts_any if isinstance(elts_any, list) else []
            items = [self._render_expr(e) for e in elts]
            # 名前付きフィールドの struct リテラルを生成 (._0, ._1, ...)
            field_inits: list[str] = []
            j = 0
            while j < len(items):
                field_inits.append("._" + str(j) + " = " + items[j])
                j += 1
            return ".{ " + ", ".join(field_inits) + " }"
        if kind == "Dict":
            return self._render_dict(ed)
        if kind == "JoinedStr":
            return self._render_joined_str(ed)
        if kind == "IfExp":
            test = self._render_cond_expr(ed.get("test"))
            body_node = ed.get("body")
            orelse_node = ed.get("orelse")
            body_expr = self._render_expr(body_node)
            orelse_expr = self._render_expr(orelse_node)
            # comptime_int リテラルを @as(i64, ...) にキャスト
            if isinstance(body_node, dict) and body_node.get("kind") == "Constant" and isinstance(body_node.get("value"), int):
                body_expr = "@as(i64, " + body_expr + ")"
            if isinstance(orelse_node, dict) and orelse_node.get("kind") == "Constant" and isinstance(orelse_node.get("value"), int):
                orelse_expr = "@as(i64, " + orelse_expr + ")"
            return "if (" + test + ") " + body_expr + " else " + orelse_expr
        if kind == "FormattedValue":
            return self._render_expr(ed.get("value"))
        if kind == "Lambda":
            arg_order_any = ed.get("arg_order")
            args = arg_order_any if isinstance(arg_order_any, list) else []
            arg_names = [_safe_ident(a, "arg") for a in args]
            body_expr = self._render_expr(ed.get("body"))
            return "struct { fn call(" + ", ".join(a + ": PyObject" for a in arg_names) + ") PyObject { return " + body_expr + "; } }.call"
        if kind == "ListComp" or kind == "SetComp" or kind == "DictComp" or kind == "GeneratorExp":
            return "pytra.empty_list()"
        if kind == "Starred":
            return self._render_expr(ed.get("value"))
        if kind == "Slice":
            lower = self._render_expr(ed.get("lower")) if isinstance(ed.get("lower"), dict) else "0"
            upper = self._render_expr(ed.get("upper")) if isinstance(ed.get("upper"), dict) else "null"
            return "pytra.slice(" + lower + ", " + upper + ")"
        if kind == "IsInstance":
            return self._render_isinstance(ed)
        return "null"

    def _render_isinstance(self, node: dict[str, Any]) -> str:
        """IsInstance ノードを静的に解決する。"""
        value_node = node.get("value")
        type_node = node.get("expected_type_id")
        if not isinstance(value_node, dict) or not isinstance(type_node, dict):
            return "false"
        obj_type = self._get_expr_type(value_node)
        if obj_type == "":
            obj_type = _safe_ident(value_node.get("id"), "")
            obj_type = self._current_type_map().get(obj_type, "")
        target_type = _safe_ident(type_node.get("id"), "")
        if obj_type == "" or target_type == "":
            return "false"
        if self._is_subclass_of(obj_type, target_type):
            return "true"
        return "false"

    def _is_subclass_of(self, cls: str, base: str) -> bool:
        """cls が base と同一か、base の子孫かを判定する。"""
        current = cls
        while current != "":
            if current == base:
                return True
            current = self._class_base.get(current, "")
        return False

    def _render_constant(self, node: dict[str, Any]) -> str:
        v = node.get("value")
        if v is None:
            return "null"
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, int):
            return str(v)
        if isinstance(v, float):
            return str(v)
        if isinstance(v, str):
            return _zig_string(v)
        return str(v)

    def _render_compare(self, node: dict[str, Any]) -> str:
        left = self._render_expr(node.get("left"))
        ops_any = node.get("ops")
        ops = ops_any if isinstance(ops_any, list) else []
        comparators_any = node.get("comparators")
        comparators = comparators_any if isinstance(comparators_any, list) else []
        if len(ops) == 0 or len(comparators) == 0:
            return left
        parts: list[str] = []
        prev = left
        prev_node = node.get("left")
        i = 0
        while i < len(ops):
            right = self._render_expr(comparators[i])
            op_str = str(ops[i])
            if op_str == "In":
                parts.append("pytra.contains(" + right + ", " + prev + ")")
            elif op_str == "NotIn":
                parts.append("!pytra.contains(" + right + ", " + prev + ")")
            else:
                # 文字列比較は std.mem.eql を使う
                left_type = self._lookup_expr_type(prev_node) if isinstance(prev_node, dict) else ""
                right_type = self._lookup_expr_type(comparators[i]) if isinstance(comparators[i], dict) else ""
                is_str_cmp = (left_type == "str" or right_type == "str")
                if is_str_cmp and op_str in ("Eq", "NotEq"):
                    eql_call = "std.mem.eql(u8, " + prev + ", " + right + ")"
                    if op_str == "Eq":
                        parts.append(eql_call)
                    else:
                        parts.append("!" + eql_call)
                else:
                    sym = _cmp_symbol(op_str)
                    parts.append(prev + " " + sym + " " + right)
            prev = right
            prev_node = comparators[i]
            i += 1
        if len(parts) == 1:
            return parts[0]
        return "(" + " and ".join(parts) + ")"

    def _render_call(self, node: dict[str, Any]) -> str:
        func_any = node.get("func")
        args_any = node.get("args")
        args = args_any if isinstance(args_any, list) else []
        arg_strs = [self._render_expr(a) for a in args]
        if isinstance(func_any, dict):
            fkind = func_any.get("kind")
            if fkind == "Name":
                fname = _safe_ident(func_any.get("id"), "fn_")
                # Python main → EAST __pytra_main リネーム対応
                if fname == "main" and "__pytra_main" in self.function_names:
                    fname = "__pytra_main"
                if fname == "print":
                    if len(args) == 1 and isinstance(args[0], dict) and args[0].get("kind") == "Call":
                        inner_func = args[0].get("func")
                        if isinstance(inner_func, dict) and inner_func.get("kind") == "Name":
                            inner_fname = str(inner_func.get("id"))
                            if inner_fname == "py_assert_stdout":
                                inner_args = args[0].get("args")
                                inner_args = inner_args if isinstance(inner_args, list) else []
                                if len(inner_args) >= 2:
                                    return self._render_expr(inner_args[1]) + "()"
                    if len(arg_strs) == 0:
                        return "pytra.print(\"\")"
                    if len(arg_strs) == 1:
                        return "pytra.print(" + arg_strs[0] + ")"
                    if len(arg_strs) == 2:
                        return "pytra.print2(" + arg_strs[0] + ", " + arg_strs[1] + ")"
                    if len(arg_strs) == 3:
                        return "pytra.print3(" + arg_strs[0] + ", " + arg_strs[1] + ", " + arg_strs[2] + ")"
                    return "pytra.print(" + arg_strs[0] + ")"
                if fname == "len":
                    if len(args) > 0:
                        arg_t = self._get_expr_type(args[0])
                        if arg_t.startswith("list[") or arg_t in {"bytearray", "bytes"}:
                            elem = "i64"
                            if arg_t.startswith("list[") and arg_t.endswith("]"):
                                elem = self._zig_type(arg_t[5:-1].strip())
                            elif arg_t in {"bytearray", "bytes"}:
                                elem = "u8"
                            return "pytra.list_len(" + arg_strs[0] + ", " + elem + ")"
                    if len(arg_strs) > 0:
                        return "@as(i64, @intCast(" + arg_strs[0] + ".len))"
                    return "0"
                if fname == "int":
                    if len(arg_strs) > 0:
                        arg_t = self._lookup_expr_type(args[0]) if len(args) > 0 else ""
                        if arg_t == "":
                            arg_t = self._get_expr_type(args[0]) if len(args) > 0 else ""
                        if arg_t == "str":
                            return "pytra.str_to_int(" + arg_strs[0] + ")"
                        if arg_t in {"float64", "float32", "float"}:
                            return "@as(i64, @intFromFloat(" + arg_strs[0] + "))"
                        if arg_t in {"int64", "int32", "int16", "int8", "uint8", "uint16", "uint32", "uint64"}:
                            return "@as(i64, @intCast(" + arg_strs[0] + "))"
                        # 型不明: @intFromFloat で安全に変換（int にも @as(f64,...) 経由で対応）
                        return "@as(i64, @intFromFloat(@as(f64, " + arg_strs[0] + ")))"
                    return "0"
                if fname == "float":
                    if len(arg_strs) > 0:
                        return "@as(f64, " + arg_strs[0] + ")"
                    return "0.0"
                if fname == "str":
                    if len(arg_strs) > 0:
                        return "pytra.to_str(" + arg_strs[0] + ")"
                    return "\"\""
                if fname == "abs":
                    if len(arg_strs) > 0:
                        return "std.math.absInt(" + arg_strs[0] + ")"
                    return "0"
                if fname == "bytearray":
                    if len(arg_strs) > 0:
                        return "pytra.bytearray(" + arg_strs[0] + ")"
                    return "pytra.bytearray(0)"
                if fname == "bytes":
                    if len(arg_strs) > 0:
                        arg_t = self._lookup_expr_type(args[0]) if len(args) > 0 else ""
                        if arg_t.startswith("list["):
                            return "pytra.list_to_bytes(" + arg_strs[0] + ")"
                        return arg_strs[0]
                    return "&[_]u8{}"
                # perf_counter は @extern 委譲経由 (time モジュール) で提供
                # import されていれば perf_counter() としてアクセス可能
                if fname == "cast":
                    # cast(T, value) is a Python type narrowing hint; just return the value
                    if len(arg_strs) >= 2:
                        return arg_strs[1]
                    return arg_strs[0] if len(arg_strs) == 1 else "null"
                if fname == "@\"extern\"" or fname == "extern":
                    # @extern(value) → value を直接返す
                    if len(arg_strs) > 0:
                        return arg_strs[0]
                    return "0"
                if fname == "open":
                    if len(arg_strs) > 0:
                        return "pytra.file_open(" + arg_strs[0] + ")"
                    return "pytra.file_open(\"\")"
                if fname == "range":
                    return "pytra.empty_list()"
                if fname == "enumerate":
                    if len(arg_strs) > 0:
                        return arg_strs[0]
                    return "pytra.empty_list()"
                if fname == "sorted":
                    if len(arg_strs) > 0:
                        return arg_strs[0]
                    return "pytra.empty_list()"
                if fname == "reversed":
                    if len(arg_strs) > 0:
                        return arg_strs[0]
                    return "pytra.empty_list()"
                if fname == "min":
                    if len(arg_strs) >= 2:
                        return "@min(" + arg_strs[0] + ", " + arg_strs[1] + ")"
                if fname == "max":
                    if len(arg_strs) >= 2:
                        return "@max(" + arg_strs[0] + ", " + arg_strs[1] + ")"
                if fname == "isinstance":
                    return "pytra.isinstance_check(" + ", ".join(arg_strs) + ")"
                if fname == "py_assert_stdout":
                    if len(args) >= 2:
                        fn_expr = self._render_expr(args[1])
                        return fn_expr + "()"
                    return "{}"
                # Local class or imported class constructor (resolved_type matches func name)
                call_resolved = str(node.get("resolved_type", ""))
                is_local_class = fname in self.class_names
                is_imported_class = not is_local_class and call_resolved == fname and fname != "" and fname[0].isupper()
                if is_imported_class:
                    # Imported class: use Type.init(args)
                    return "pytra.make_object(" + fname + ", " + fname + ".init(" + ", ".join(arg_strs) + "))"
                if is_local_class:
                    if self._has_vtable(fname):
                        vt_inst = "&" + fname + "_vt"
                        drop_arg = fname + "_drop_wrap" if fname in self._classes_with_del else "null"
                        make_fn = "pytra.make_obj_drop"
                        if fname in self._classes_with_init:
                            return make_fn + "(" + fname + ", " + fname + ".init(" + ", ".join(arg_strs) + "), @ptrCast(" + vt_inst + "), " + drop_arg + ")"
                        return make_fn + "(" + fname + ", " + fname + "{}, @ptrCast(" + vt_inst + "), " + drop_arg + ")"
                    if fname in self._dataclass_names:
                        fields = self._dataclass_fields.get(fname, [])
                        field_inits: list[str] = []
                        j = 0
                        while j < len(fields) and j < len(arg_strs):
                            field_inits.append("." + fields[j] + " = " + arg_strs[j])
                            j += 1
                        return "pytra.make_object(" + fname + ", " + fname + "{ " + ", ".join(field_inits) + " })"
                    if fname in self._classes_with_init:
                        return "pytra.make_object(" + fname + ", " + fname + ".init(" + ", ".join(arg_strs) + "))"
                    return "pytra.make_object(" + fname + ", " + fname + "{})"
                return fname + "(" + ", ".join(arg_strs) + ")"
            if fkind == "Attribute":
                obj_node_for_attr = func_any.get("value")
                attr = _safe_ident(func_any.get("attr"), "method")
                # super().method() → BaseClass.method(undefined)
                if isinstance(obj_node_for_attr, dict) and obj_node_for_attr.get("kind") == "Call":
                    super_func = obj_node_for_attr.get("func")
                    if isinstance(super_func, dict) and super_func.get("kind") == "Name" and super_func.get("id") == "super":
                        base = self._class_base.get(self.current_class_name, "")
                        if base != "":
                            return base + "." + attr + "(undefined)"
                obj = self._render_expr(obj_node_for_attr)
                # math.* → サブモジュール内は math_native.*、メインモジュールはそのまま
                if isinstance(obj_node_for_attr, dict) and obj_node_for_attr.get("kind") == "Name" and str(obj_node_for_attr.get("id")) == "math":
                    if attr in {"sin", "cos", "tan", "asin", "acos", "atan", "exp", "log", "log2", "log10", "sqrt", "fabs", "floor", "ceil", "round", "fmod", "hypot", "atan2", "pow", "log_"}:
                        zig_attr = attr if attr != "log_" else "log"
                        # math 関数は f64 引数を期待 — int 引数を自動変換
                        _INT_TYPES_M = {"int64", "int32", "int16", "int8", "uint8", "uint16", "uint32", "uint64"}
                        coerced_args: list[str] = []
                        j = 0
                        while j < len(args):
                            a_type = self._lookup_expr_type(args[j]) if j < len(args) else ""
                            if a_type == "":
                                a_type = self._get_expr_type(args[j]) if isinstance(args[j], dict) else ""
                            if a_type in _INT_TYPES_M:
                                coerced_args.append("@as(f64, @floatFromInt(" + arg_strs[j] + "))")
                            else:
                                coerced_args.append(arg_strs[j])
                            j += 1
                        if self.is_submodule:
                            return "math_native." + zig_attr + "(" + ", ".join(coerced_args) + ")"
                        return obj + "." + zig_attr + "(" + ", ".join(coerced_args) + ")"
                if attr == "isdigit":
                    return "pytra.char_isdigit(" + obj + ")"
                if attr == "isalpha":
                    return "pytra.char_isalpha(" + obj + ")"
                if attr == "get":
                    obj_type = self._lookup_expr_type(obj_node_for_attr)
                    if obj_type.startswith("dict["):
                        parts = self._split_generic(obj_type[5:-1])
                        val_zig = "i64"
                        if len(parts) == 2:
                            val_zig = self._zig_type(parts[1].strip())
                        if len(arg_strs) >= 2:
                            return "pytra.dict_get_default(" + val_zig + ", " + obj + ", " + arg_strs[0] + ", " + arg_strs[1] + ")"
                        if len(arg_strs) == 1:
                            return "pytra.dict_get_default(" + val_zig + ", " + obj + ", " + arg_strs[0] + ", 0)"
                if attr == "append":
                    if len(arg_strs) > 0:
                        obj_type = self._lookup_expr_type(obj_node_for_attr)
                        elem_type = "i64"
                        if obj_type.startswith("list[") and obj_type.endswith("]"):
                            inner_raw = obj_type[5:-1].strip()
                            elem_type = self._zig_type(inner_raw)
                            # list[unknown] → 要素型は pytra.Obj (ネスト list 等)
                            if elem_type == "pytra.PyObject" and inner_raw in {"unknown", "Any", "object"}:
                                elem_type = "pytra.Obj"
                        elif obj_type in {"bytearray", "bytes"}:
                            elem_type = "u8"
                        if elem_type in {"u8", "i8", "i16", "u16", "i32", "u32", "i64", "u64"}:
                            return "pytra.list_append(" + obj + ", " + elem_type + ", @intCast(" + arg_strs[0] + "))"
                        return "pytra.list_append(" + obj + ", " + elem_type + ", " + arg_strs[0] + ")"
                if attr == "join":
                    # Only str.join → str_join_sep; module.join passes through
                    owner_type = self._lookup_expr_type(obj_node_for_attr) if isinstance(obj_node_for_attr, dict) else ""
                    if owner_type == "str":
                        if len(arg_strs) > 0:
                            arg_type = self._lookup_expr_type(args[0]) if len(args) > 0 else ""
                            if arg_type.startswith("list["):
                                return "pytra.str_join_sep(" + obj + ", pytra.list_items(" + arg_strs[0] + ", []const u8))"
                            return "pytra.str_join_sep(" + obj + ", " + arg_strs[0] + ")"
                        return "pytra.str_join_sep(" + obj + ", &.{})"
                if attr == "pop":
                    obj_type = self._lookup_expr_type(obj_node_for_attr)
                    elem_type = "i64"
                    if obj_type.startswith("list[") and obj_type.endswith("]"):
                        elem_type = self._zig_type(obj_type[5:-1].strip())
                    elif obj_type in {"bytearray", "bytes"}:
                        elem_type = "u8"
                    return "pytra.list_pop(" + obj + ", " + elem_type + ")"
                if attr == "extend":
                    if len(arg_strs) > 0:
                        obj_type = self._lookup_expr_type(obj_node_for_attr)
                        elem_type = "i64"
                        if obj_type.startswith("list[") and obj_type.endswith("]"):
                            elem_type = self._zig_type(obj_type[5:-1].strip())
                        elif obj_type in {"bytearray", "bytes"}:
                            elem_type = "u8"
                        return "pytra.list_extend(" + obj + ", " + elem_type + ", " + arg_strs[0] + ")"
                if attr == "write":
                    if len(arg_strs) > 0:
                        return "pytra.file_write(" + obj + ", " + arg_strs[0] + ")"
                if attr == "close":
                    return "pytra.file_close(" + obj + ")"
                if attr == "sqrt":
                    if len(arg_strs) > 0:
                        return "std.math.sqrt(@as(f64, " + arg_strs[0] + "))"
                    return "std.math.sqrt(@as(f64, " + obj + "))"
                # vtable ディスパッチ: obj の型がクラスかつ vtable あり
                # ただしメソッド内の self.method() は直接呼び出し
                obj_node = func_any.get("value")
                is_self_call = isinstance(obj_node, dict) and obj_node.get("kind") == "Name" and obj_node.get("id") == "self"
                obj_type = self._lookup_expr_type(obj_node)
                if obj_type in self.class_names and self._has_vtable(obj_type) and not is_self_call:
                    root = self._get_vtable_root(obj_type)
                    vt_name = root + "VT"
                    return obj + ".vt(" + vt_name + ")." + attr + "(" + obj + ".data)"
                return obj + "." + attr + "(" + ", ".join(arg_strs) + ")"
        fn_expr = self._render_expr(func_any)
        return fn_expr + "(" + ", ".join(arg_strs) + ")"

    def _render_dict(self, node: dict[str, Any]) -> str:
        entries_any = node.get("entries")
        entries: list[dict[str, Any]] = []
        if isinstance(entries_any, list):
            for e in entries_any:
                if isinstance(e, dict):
                    entries.append(e)
        if len(entries) == 0:
            # 空 dict
            resolved = self._get_expr_type(node)
            if resolved.startswith("dict["):
                parts = self._split_generic(resolved[5:-1] if resolved.endswith("]") else "")
                if len(parts) == 2:
                    val_t = self._zig_type(parts[1].strip())
                    return "pytra.make_str_dict(" + val_t + ")"
            return "pytra.make_str_dict(i64)"
        val_parts: list[str] = []
        key_parts: list[str] = []
        for entry in entries:
            key_parts.append(self._render_expr(entry.get("key")))
            val_parts.append(self._render_expr(entry.get("value")))
        resolved = self._get_expr_type(node)
        val_zig = "i64"
        if resolved.startswith("dict[") and resolved.endswith("]"):
            dparts = self._split_generic(resolved[5:-1])
            if len(dparts) == 2:
                val_zig = self._zig_type(dparts[1].strip())
        return "pytra.make_str_dict_from(" + val_zig + ", " + "&[_][]const u8{ " + ", ".join(key_parts) + " }, " + "&[_]" + val_zig + "{ " + ", ".join(val_parts) + " })"

    def _render_joined_str(self, node: dict[str, Any]) -> str:
        values_any = node.get("values")
        values = values_any if isinstance(values_any, list) else []
        parts: list[str] = []
        for v in values:
            if isinstance(v, dict):
                if v.get("kind") == "Constant" and isinstance(v.get("value"), str):
                    parts.append(_zig_string(str(v.get("value"))))
                else:
                    parts.append("pytra.to_str(" + self._render_expr(v) + ")")
            else:
                parts.append(_zig_string(str(v)))
        if len(parts) == 0:
            return "\"\""
        if len(parts) == 1:
            return parts[0]
        return "pytra.str_join(&.{ " + ", ".join(parts) + " })"

    def _normalize_type(self, t: str) -> str:
        """Python 型名を内部正規表現へ変換する。"""
        s = t.strip()
        if s == "":
            return ""
        if s == "int":
            return "int64"
        if s == "float":
            return "float64"
        if s == "byte":
            return "uint8"
        if s == "any":
            return "Any"
        if s.startswith("list[") and s.endswith("]"):
            inner = self._normalize_type(s[5:-1])
            return "list[" + inner + "]"
        if s.startswith("set[") and s.endswith("]"):
            inner = self._normalize_type(s[4:-1])
            return "set[" + inner + "]"
        if s.startswith("dict[") and s.endswith("]"):
            inner = s[5:-1]
            parts = self._split_generic(inner)
            if len(parts) == 2:
                return "dict[" + self._normalize_type(parts[0]) + ", " + self._normalize_type(parts[1]) + "]"
        if s.startswith("tuple[") and s.endswith("]"):
            inner = s[6:-1]
            parts = self._split_generic(inner)
            normed: list[str] = []
            for p in parts:
                normed.append(self._normalize_type(p))
            return "tuple[" + ", ".join(normed) + "]"
        if s.find("|") != -1:
            parts = [self._normalize_type(p.strip()) for p in s.split("|")]
            return "|".join(parts)
        return s

    def _split_generic(self, inner: str) -> list[str]:
        """ジェネリック型引数をカンマで分割する（ネスト考慮）。"""
        parts: list[str] = []
        depth = 0
        current: list[str] = []
        i = 0
        while i < len(inner):
            ch = inner[i]
            if ch == "[":
                depth += 1
                current.append(ch)
            elif ch == "]":
                depth -= 1
                current.append(ch)
            elif ch == "," and depth == 0:
                parts.append("".join(current).strip())
                current = []
            else:
                current.append(ch)
            i += 1
        tail = "".join(current).strip()
        if tail != "":
            parts.append(tail)
        return parts

    def _zig_type(self, py_type: str) -> str:
        """正規化済み Python 型名を Zig 型名へ変換する。"""
        t = self._normalize_type(py_type)
        if t == "":
            return "pytra.PyObject"
        if t in {"Any", "object"}:
            return "pytra.PyObject"
        if t == "unknown":
            return "pytra.Obj"
        # --- スカラー型 ---
        if t == "bool":
            return "bool"
        if t == "int8":
            return "i8"
        if t == "uint8":
            return "u8"
        if t == "int16":
            return "i16"
        if t == "uint16":
            return "u16"
        if t == "int32":
            return "i32"
        if t == "uint32":
            return "u32"
        if t == "int64":
            return "i64"
        if t == "uint64":
            return "u64"
        if t == "float32":
            return "f32"
        if t == "float64":
            return "f64"
        if t == "str":
            return "[]const u8"
        if t == "bytes" or t == "bytearray":
            return "pytra.Obj"
        if t == "None":
            return "void"
        # --- Union / Optional ---
        if t.find("|") != -1:
            parts = [p.strip() for p in t.split("|")]
            non_none = [p for p in parts if p != "None"]
            has_none = len(non_none) < len(parts)
            if has_none and len(non_none) == 1:
                return "?" + self._zig_type(non_none[0])
            if len(non_none) == 1:
                return self._zig_type(non_none[0])
            return "pytra.PyObject"
        # --- コンテナ型 ---
        if t.startswith("list[") and t.endswith("]"):
            return "pytra.Obj"
        if t.startswith("set[") and t.endswith("]"):
            return "pytra.PyObject"
        if t.startswith("dict[") and t.endswith("]"):
            parts = self._split_generic(t[5:-1])
            if len(parts) == 2:
                val_t = self._zig_type(parts[1].strip())
                key_t = self._normalize_type(parts[0].strip())
                if key_t == "str":
                    return "std.StringHashMap(" + val_t + ")"
            return "std.StringHashMap(PyObject)"
        if t.startswith("tuple[") and t.endswith("]"):
            parts = self._split_generic(t[6:-1])
            if len(parts) == 2 and parts[1].strip() == "...":
                return "pytra.Obj"
            return self._zig_tuple_type(t)
        # --- クラス名 ---
        if t in self.class_names:
            if self._has_vtable(t):
                return "pytra.Obj"
            return "*" + t
        return "pytra.PyObject"

    def _get_expr_type(self, expr_any: Any) -> str:
        """EAST3 式ノードの resolved_type を正規化して返す。"""
        if not isinstance(expr_any, dict):
            return ""
        resolved = expr_any.get("resolved_type")
        if isinstance(resolved, str) and resolved.strip() != "" and resolved.strip() != "unknown":
            return self._normalize_type(resolved.strip())
        return ""

    def _infer_decl_type(self, stmt: dict[str, Any]) -> str:
        """変数宣言ノードから型を推論する（decl_type → annotation → value の resolved_type）。"""
        decl_type_any = stmt.get("decl_type")
        if isinstance(decl_type_any, str) and decl_type_any.strip() not in {"", "unknown"}:
            return self._normalize_type(decl_type_any.strip())
        anno_any = stmt.get("annotation")
        if isinstance(anno_any, str) and anno_any.strip() not in {"", "unknown"}:
            return self._normalize_type(anno_any.strip())
        value_any = stmt.get("value")
        if isinstance(value_any, dict):
            return self._get_expr_type(value_any)
        return ""

    def _lookup_expr_type(self, expr_any: Any) -> str:
        if not isinstance(expr_any, dict):
            return ""
        ed: dict[str, Any] = expr_any
        resolved = self._get_expr_type(ed)
        if resolved != "":
            return resolved
        kind = ed.get("kind")
        if kind == "Name":
            name = _safe_ident(ed.get("id"), "value")
            return self._current_type_map().get(name, "")
        if kind == "Constant":
            v = ed.get("value")
            if isinstance(v, bool):
                return "bool"
            if isinstance(v, int):
                return "int64"
            if isinstance(v, float):
                return "float64"
            if isinstance(v, str):
                return "str"
        # math.* 呼び出しは float64 を返す
        if kind == "Call":
            func = ed.get("func")
            if isinstance(func, dict) and func.get("kind") == "Attribute":
                obj_node = func.get("value")
                if isinstance(obj_node, dict) and obj_node.get("kind") == "Name" and str(obj_node.get("id")) == "math":
                    attr = str(func.get("attr"))
                    if attr in {"sin", "cos", "tan", "asin", "acos", "atan", "exp", "log", "log2", "log10", "sqrt", "fabs", "floor", "ceil", "round", "fmod", "hypot", "atan2", "pow"}:
                        return "float64"
        # BinOp の型推論: float が含まれれば float64
        if kind == "BinOp":
            lt = self._lookup_expr_type(ed.get("left"))
            rt = self._lookup_expr_type(ed.get("right"))
            _FT = {"float64", "float32", "float"}
            _IT = {"int64", "int32", "int16", "int8", "uint8", "uint16", "uint32", "uint64"}
            if lt in _FT or rt in _FT:
                return "float64"
            if lt in _IT and rt in _IT:
                return "int64"
        return ""

    def _aug_assign_op(self, op: str) -> str:
        if op == "Add":
            return "+="
        if op == "Sub":
            return "-="
        if op == "Mult":
            return "*="
        if op == "Div":
            return "/="
        if op == "Mod":
            return "%="
        if op == "BitOr":
            return "|="
        if op == "BitXor":
            return "^="
        if op == "BitAnd":
            return "&="
        if op == "LShift":
            return "<<="
        if op == "RShift":
            return ">>="
        return "+="


def cls_name_init(cls_name: str, arg_strs: list[str]) -> str:
    return cls_name + ".init(" + ", ".join(arg_strs) + ")"


def transpile_to_zig_native(east_doc: dict[str, Any], is_submodule: bool = False) -> str:
    """EAST3 ドキュメントを Zig native ソースへ変換する。"""
    reject_backend_typed_vararg_signatures(east_doc, backend_name="Zig backend")
    reject_backend_homogeneous_tuple_ellipsis_type_exprs(east_doc, backend_name="Zig backend")
    return ZigNativeEmitter(east_doc, is_submodule=is_submodule).transpile()
