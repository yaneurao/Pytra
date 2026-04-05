"""EAST3 -> Dart source emitter."""

from __future__ import annotations

from typing import Any

from pytra.std import json
from pytra.std.pathlib import Path

from toolchain.emit.common.code_emitter import (
    build_import_alias_map,
    load_runtime_mapping,
    RuntimeMapping,
    should_skip_module,
)
from toolchain.emit.swift.emitter import (
    reject_backend_homogeneous_tuple_ellipsis_type_exprs,
)


_RUNTIME_SYMBOL_INDEX_PATH = Path(__file__).resolve().parents[4] / "tools" / "runtime_symbol_index.json"
_RUNTIME_SYMBOL_INDEX_CACHE: dict[str, Any] | None = None


def _load_runtime_symbol_index() -> dict[str, Any]:
    global _RUNTIME_SYMBOL_INDEX_CACHE
    if _RUNTIME_SYMBOL_INDEX_CACHE is not None:
        return _RUNTIME_SYMBOL_INDEX_CACHE
    if not _RUNTIME_SYMBOL_INDEX_PATH.exists():
        _RUNTIME_SYMBOL_INDEX_CACHE = {}
        return _RUNTIME_SYMBOL_INDEX_CACHE
    try:
        raw_obj = json.loads_obj(_RUNTIME_SYMBOL_INDEX_PATH.read_text())
        raw = raw_obj.raw if raw_obj is not None else {}
        _RUNTIME_SYMBOL_INDEX_CACHE = raw if isinstance(raw, dict) else {}
    except Exception:
        _RUNTIME_SYMBOL_INDEX_CACHE = {}
    return _RUNTIME_SYMBOL_INDEX_CACHE


def _runtime_module_doc(module_id: str) -> dict[str, Any]:
    modules = _load_runtime_symbol_index().get("modules")
    if not isinstance(modules, dict):
        return {}
    doc = modules.get(module_id)
    return doc if isinstance(doc, dict) else {}


def runtime_module_exists(module_id: str) -> bool:
    return len(_runtime_module_doc(module_id)) > 0


def _find_runtime_modules_by_leaf(module_id: str) -> list[str]:
    mod = module_id.strip()
    if mod == "":
        return []
    modules = _load_runtime_symbol_index().get("modules")
    if not isinstance(modules, dict):
        return []
    matches: list[str] = []
    for candidate_any in modules.keys():
        if not isinstance(candidate_any, str):
            continue
        candidate = candidate_any.strip()
        if candidate == "":
            continue
        parts = candidate.split(".")
        if len(parts) > 0 and parts[-1] == mod:
            matches.append(candidate)
    return matches


def canonical_runtime_module_id(module_id: str) -> str:
    mod = module_id.strip()
    if mod == "":
        return ""
    if runtime_module_exists(mod):
        return mod
    if "." not in mod:
        matches = _find_runtime_modules_by_leaf(mod)
        if len(matches) == 1:
            return matches[0]
    return mod


def lookup_runtime_module_symbols(module_id: str) -> dict[str, Any]:
    symbols = _runtime_module_doc(module_id).get("symbols")
    return symbols if isinstance(symbols, dict) else {}


def lookup_runtime_module_group(module_id: str) -> str:
    group = _runtime_module_doc(module_id).get("runtime_group")
    return group if isinstance(group, str) else ""


def resolve_import_binding_runtime_module(module_id: str, export_name: str, binding_kind: str) -> str:
    mod = canonical_runtime_module_id(module_id.strip())
    if mod == "":
        return ""
    if binding_kind in {"module", "implicit_builtin"}:
        return mod if runtime_module_exists(mod) else ""
    if binding_kind != "symbol":
        return ""
    child_module = mod + "." + export_name.strip() if export_name.strip() != "" else ""
    if child_module != "" and runtime_module_exists(child_module):
        return child_module
    symbols = lookup_runtime_module_symbols(mod)
    if export_name in symbols:
        return mod
    return ""


def resolve_import_binding_doc(module_id: str, export_name: str, binding_kind: str) -> dict[str, Any]:
    source_module_id = module_id.strip()
    source_export_name = export_name.strip()
    source_binding_kind = binding_kind.strip()
    runtime_module_id = resolve_import_binding_runtime_module(
        source_module_id,
        source_export_name,
        source_binding_kind,
    )
    if runtime_module_id == "":
        return {}
    out: dict[str, Any] = {
        "source_module_id": source_module_id,
        "source_export_name": source_export_name,
        "source_binding_kind": source_binding_kind,
        "runtime_module_id": runtime_module_id,
        "runtime_group": lookup_runtime_module_group(runtime_module_id),
    }
    if source_binding_kind == "module":
        out["resolved_binding_kind"] = "module"
        return out
    child_module = canonical_runtime_module_id(source_module_id)
    if child_module != "" and runtime_module_id != child_module:
        out["resolved_binding_kind"] = "module"
        return out
    symbol_doc = lookup_runtime_module_symbols(runtime_module_id).get(source_export_name)
    if not isinstance(symbol_doc, dict):
        return out
    out["resolved_binding_kind"] = "symbol"
    out["runtime_symbol"] = source_export_name
    kind = symbol_doc.get("kind")
    if isinstance(kind, str) and kind != "":
        out["runtime_symbol_kind"] = kind
    dispatch = symbol_doc.get("dispatch")
    if isinstance(dispatch, str) and dispatch != "":
        out["runtime_symbol_dispatch"] = dispatch
    semantic_tag = symbol_doc.get("semantic_tag")
    if isinstance(semantic_tag, str) and semantic_tag != "":
        out["runtime_semantic_tag"] = semantic_tag
    adapter_kind = symbol_doc.get("call_adapter_kind")
    if isinstance(adapter_kind, str) and adapter_kind != "":
        out["runtime_call_adapter_kind"] = adapter_kind
    extern_doc = symbol_doc.get("extern_v1")
    if isinstance(extern_doc, dict):
        extern_kind = extern_doc.get("kind")
        if isinstance(extern_kind, str) and extern_kind != "":
            out["runtime_extern_kind"] = extern_kind
    return out


_DART_KEYWORDS = {
    "abstract",
    "as",
    "assert",
    "async",
    "await",
    "break",
    "case",
    "catch",
    "class",
    "const",
    "continue",
    "covariant",
    "default",
    "deferred",
    "do",
    "dynamic",
    "else",
    "enum",
    "export",
    "extends",
    "extension",
    "external",
    "factory",
    "false",
    "final",
    "finally",
    "for",
    "Function",
    "get",
    "hide",
    "if",
    "implements",
    "import",
    "in",
    "interface",
    "is",
    "late",
    "library",
    "mixin",
    "new",
    "null",
    "of",
    "on",
    "operator",
    "part",
    "required",
    "rethrow",
    "return",
    "set",
    "show",
    "static",
    "super",
    "switch",
    "sync",
    "this",
    "throw",
    "true",
    "try",
    "typedef",
    "var",
    "void",
    "while",
    "with",
    "yield",
}
# Dart top-level built-in names that user-defined identifiers should not shadow.
# Dart top-level built-in type/class names that user-defined identifiers
# should not shadow.  Function names like print are excluded because Pytra's
# runtime may reference them and _safe_ident cannot distinguish user
# definitions from runtime references.
_DART_RESERVED_BUILTINS = {
    "identical", "override",
    "int", "double", "num", "String", "bool", "List", "Map", "Set",
    "Object", "Type", "Symbol", "Future", "Stream", "Iterable",
    "Iterator", "Duration", "DateTime", "RegExp", "Error",
    "StateError", "ArgumentError", "RangeError",
    "FormatException", "UnsupportedError",
    "Comparable", "Pattern", "Match", "Sink", "StringSink",
    "Null", "Never", "Enum",
}
_NIL_FREE_DECL_TYPES = {"int", "int64", "float", "float64", "bool"}
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
    if out == "_":
        out = "unused_"
    if out[0].isdigit():
        out = "d_" + out
    if out in _DART_KEYWORDS:
        out = out + "_"
    while out in _DART_RESERVED_BUILTINS:
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
    wildcard_modules: dict[str, str] = {}
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
                wildcard_module = module_path if module_path != "" else _relative_import_module_path(module_id)
                if wildcard_module != "":
                    wildcard_modules[wildcard_module] = wildcard_module
                j += 1
                continue
            asname_any = ent.get("asname")
            local_name = asname_any if isinstance(asname_any, str) and asname_any != "" else name
            local_rendered = _safe_ident(local_name, "value")
            target_name = _safe_ident(name, "value")
            aliases[local_rendered] = (
                target_name if module_path == "" else module_path + "." + target_name
            )
            j += 1
        i += 1
    if len(wildcard_modules) == 0:
        return aliases
    meta_any = east_doc.get("meta")
    meta = meta_any if isinstance(meta_any, dict) else {}
    import_symbols_any = meta.get("import_symbols")
    import_symbols = import_symbols_any if isinstance(import_symbols_any, dict) else {}
    wildcard_resolved: dict[str, bool] = {module_id: False for module_id in wildcard_modules}
    for local_name_any, binding_any in import_symbols.items():
        if not isinstance(local_name_any, str) or local_name_any == "":
            continue
        if not isinstance(binding_any, dict):
            continue
        binding_module_any = binding_any.get("module")
        binding_symbol_any = binding_any.get("name")
        binding_module = (
            _relative_import_module_path(binding_module_any)
            if isinstance(binding_module_any, str)
            else ""
        )
        binding_symbol = binding_symbol_any if isinstance(binding_symbol_any, str) else ""
        if binding_module not in wildcard_resolved or binding_symbol == "":
            continue
        local_rendered = _safe_ident(local_name_any, "value")
        target_name = _safe_ident(binding_symbol, "value")
        aliases[local_rendered] = (
            target_name if binding_module == "" else binding_module + "." + target_name
        )
        wildcard_resolved[binding_module] = True
    unresolved = [module_id for module_id, resolved in wildcard_resolved.items() if not resolved]
    if len(unresolved) > 0:
        raise RuntimeError(
            "dart native emitter: unsupported relative import form: wildcard import"
        )
    return aliases


def _dart_string(text: str) -> str:
    out = text.replace("\\", "\\\\")
    out = out.replace('"', '\\"')
    out = out.replace("\t", "\\t")
    out = out.replace("\r", "\\r")
    out = out.replace("\n", "\\n")
    out = out.replace("$", "\\$")
    return '"' + out + '"'


def _module_id_to_import_path(module_id: str, ext: str, root_rel_prefix: str) -> str:
    """module_id から機械的にインポートパスを生成する (§3)."""
    parts = module_id.split(".")
    rel_parts = parts[1:] if len(parts) >= 2 and parts[0] == "pytra" else parts
    rel = ".".join(rel_parts)
    return root_rel_prefix + rel.replace(".", "/") + ext


def _module_id_to_native_import_path(module_id: str, ext: str, root_rel_prefix: str) -> str:
    """module_id から _native ファイルのインポートパスを生成する (§4)."""
    parts = module_id.split(".")
    rel_parts = parts[1:] if len(parts) >= 2 and parts[0] == "pytra" else parts
    rel = ".".join(rel_parts)
    return root_rel_prefix + rel.replace(".", "/") + "_native" + ext


def _binop_symbol(op: str) -> str:
    if op == "Add":
        return "+"
    if op == "Sub":
        return "-"
    if op == "Mult":
        return "*"
    if op == "Div":
        return "/"
    if op == "Mod":
        return "%"
    if op == "LShift":
        return "<<"
    if op == "RShift":
        return ">>"
    if op == "BitAnd":
        return "&"
    if op == "BitOr":
        return "|"
    if op == "BitXor":
        return "^"
    if op == "FloorDiv":
        return "~/"
    return "+"


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
    return "=="




def _reject_unsupported_relative_import_forms(body_any: Any) -> None:
    if not isinstance(body_any, list):
        return
    i = 0
    while i < len(body_any):
        stmt = body_any[i]
        i += 1
        if not isinstance(stmt, dict):
            continue
        kind = stmt.get("kind")
        if kind != "Import" and kind != "ImportFrom":
            continue
        module_any = stmt.get("module")
        module_id = module_any if isinstance(module_any, str) else ""
        level_any = stmt.get("level")
        level = level_any if isinstance(level_any, int) else 0
        if level <= 0 and not module_id.startswith("."):
            continue
        names_any = stmt.get("names")
        names = names_any if isinstance(names_any, list) else []
        j = 0
        while j < len(names):
            ent = names[j]
            if isinstance(ent, dict) and ent.get("name") == "*":
                raise RuntimeError(
                    "dart native emitter: unsupported relative import form: wildcard import"
                )
            j += 1
        if kind == "ImportFrom":
            continue
        raise RuntimeError(
            "dart native emitter: unsupported relative import form: relative import"
        )


class DartNativeEmitter:
    def __init__(self, east_doc: dict[str, Any]) -> None:
        if not isinstance(east_doc, dict):
            raise RuntimeError("lang=dart invalid east document: root must be dict")
        ed: dict[str, Any] = east_doc
        kind = ed.get("kind")
        if kind != "Module":
            raise RuntimeError("lang=dart invalid root kind: " + str(kind))
        if ed.get("east_stage") != 3:
            raise RuntimeError("lang=dart unsupported east_stage: " + str(ed.get("east_stage")))
        self.east_doc = east_doc
        self.lines: list[str] = []
        self.indent = 0
        self.tmp_seq = 0
        self.class_names: set[str] = set()
        self.intflag_classes: set[str] = set()  # classes extending IntEnum/IntFlag → use int type
        self.imported_modules: set[str] = set()
        self.import_alias_modules: dict[str, str] = {}
        self._module_aliases: dict[str, str] = {}
        self.function_names: set[str] = set()
        self.relative_import_name_aliases: dict[str, str] = {}
        self.current_class_name: str = ""
        self.current_class_base_name: str = ""
        self.current_class_is_trait: bool = False
        self._local_type_stack: list[dict[str, str]] = [{}]  # [0] = module-level frame
        self._ref_var_stack: list[set[str]] = []
        self._local_var_stack: list[set[str]] = []
        self._needs_math_import = False
        self._needs_io_import = False
        self._class_field_types: dict[str, dict[str, str]] = {}
        self._function_return_types: dict[str, str] = {}
        # emit_context (injected by emit_all_modules)
        meta_any = east_doc.get("meta")
        meta = meta_any if isinstance(meta_any, dict) else {}
        self.import_alias_modules = build_import_alias_map(meta)
        mapping_path = Path(__file__).resolve().parents[3] / "runtime" / "dart" / "mapping.json"
        self._mapping: RuntimeMapping = load_runtime_mapping(mapping_path)
        emit_ctx_any = meta.get("emit_context")
        emit_ctx = emit_ctx_any if isinstance(emit_ctx_any, dict) else {}
        self._module_id: str = emit_ctx.get("module_id", "") if isinstance(emit_ctx.get("module_id"), str) else ""
        self._root_rel_prefix: str = emit_ctx.get("root_rel_prefix", "./") if isinstance(emit_ctx.get("root_rel_prefix"), str) else "./"
        self._is_entry: bool = bool(emit_ctx.get("is_entry", False))
        self._has_extern_delegation: bool = False

    def _walk_nodes(self, root: Any) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        if isinstance(root, dict):
            out.append(root)
            for value in root.values():
                out.extend(self._walk_nodes(value))
        elif isinstance(root, list):
            for item in root:
                out.extend(self._walk_nodes(item))
        return out

    def _next_module_alias(self, base_alias: str) -> str:
        alias = "__mod_" + _safe_ident(base_alias, "mod")
        if alias not in self.imported_modules:
            return alias
        seq = 2
        while True:
            candidate = alias + "_" + str(seq)
            if candidate not in self.imported_modules:
                return candidate
            seq += 1

    def _resolve_module_attr_module_id(self, node: Any) -> str:
        if not isinstance(node, dict) or node.get("kind") != "Attribute":
            return ""
        owner_node = node.get("value")
        attr_raw = node.get("attr") if isinstance(node.get("attr"), str) else ""
        if attr_raw == "":
            return ""
        owner_module_id = ""
        if isinstance(owner_node, dict) and owner_node.get("kind") == "Name":
            owner_name = _safe_ident(owner_node.get("id"), "")
            owner_module_id = self.import_alias_modules.get(owner_name, "")
        elif isinstance(owner_node, dict) and owner_node.get("kind") == "Attribute":
            owner_module_id = self._resolve_module_attr_module_id(owner_node)
        if owner_module_id == "":
            return ""
        resolved = resolve_import_binding_doc(owner_module_id, attr_raw, "symbol")
        if resolved.get("resolved_binding_kind") != "module":
            return ""
        runtime_mod = resolved.get("runtime_module_id")
        if not isinstance(runtime_mod, str) or runtime_mod == "":
            return ""
        return canonical_runtime_module_id(runtime_mod)

    def _resolve_module_owner_alias(self, owner_node: Any) -> str:
        if not isinstance(owner_node, dict):
            return ""
        if owner_node.get("kind") == "Name":
            owner_name = _safe_ident(owner_node.get("id"), "")
            module_id = self.import_alias_modules.get(owner_name, "")
            if module_id != "":
                mapped_name = self.relative_import_name_aliases.get(owner_name, owner_name)
                if mapped_name in self.imported_modules:
                    return mapped_name
            return ""
        if owner_node.get("kind") != "Attribute":
            return ""
        module_id = self._resolve_module_attr_module_id(owner_node)
        if module_id == "":
            return ""
        return self._module_aliases.get(module_id, "")

    def _is_module_owner_node(self, owner_node: Any) -> bool:
        if not isinstance(owner_node, dict):
            return False
        if owner_node.get("kind") == "Name":
            resolved_type = owner_node.get("resolved_type")
            return isinstance(resolved_type, str) and resolved_type == "module"
        if owner_node.get("kind") == "Attribute":
            resolved_type = owner_node.get("resolved_type")
            if isinstance(resolved_type, str) and resolved_type == "module":
                return True
            return self._resolve_module_attr_module_id(owner_node) != ""
        return False

    def _lookup_mapped_call(self, runtime_module_id: str, attr: str) -> str:
        if runtime_module_id != "":
            if runtime_module_id + "." + attr in self._mapping.calls:
                return self._mapping.calls[runtime_module_id + "." + attr]
            module_parts = runtime_module_id.split(".")
            if len(module_parts) >= 3 and module_parts[0] == "pytra" and module_parts[1] == "std":
                short_key = ".".join(module_parts[2:]) + "." + attr
                if short_key in self._mapping.calls:
                    return self._mapping.calls[short_key]
        return self._mapping.calls.get(attr, "")

    def _expand_mapped_call(self, mapped: str, rendered_args: list[str]) -> str:
        if mapped.startswith("__NUM_METHOD__:"):
            method_name = mapped[len("__NUM_METHOD__:"):]
            if len(rendered_args) == 0:
                return "0"
            return "(" + rendered_args[0] + " as num)." + method_name + "()"
        return ""

    # --- type mapping ---

    def _dart_type(self, east_type: Any) -> str:
        """Map an EAST type string to a Dart type string."""
        if not isinstance(east_type, str) or east_type == "":
            return "dynamic"
        t = east_type.strip()
        if t in {"Any", "object", "unknown"}:
            return "dynamic"
        if t == "int" or t == "int64" or t == "int32" or t == "int16" or t == "int8":
            return "int"
        if t == "uint8" or t == "uint16" or t == "uint32" or t == "uint64" or t == "byte":
            return "int"
        if t == "float" or t == "float64" or t == "float32":
            return "double"
        if t == "bool":
            return "bool"
        if t == "str" or t == "string":
            return "String"
        if t == "None":
            return "void"
        if t in {"bytes", "bytearray"}:
            return "List<int>"
        # Optional: T | None
        if t.find("|") != -1:
            parts = [p.strip() for p in t.split("|")]
            non_none = [p for p in parts if p != "None"]
            has_none = len(non_none) < len(parts)
            if has_none and len(non_none) == 1:
                return self._dart_type(non_none[0]) + "?"
            if not has_none and len(non_none) == 1:
                return self._dart_type(non_none[0])
            return "dynamic"
        # list[T]
        if t.startswith("list[") and t.endswith("]"):
            inner = t[5:-1].strip()
            return "List<" + self._dart_type(inner) + ">"
        # dict[K, V]
        if t.startswith("dict[") and t.endswith("]"):
            inner = t[5:-1]
            parts = self._split_generic_args(inner)
            if len(parts) == 2:
                return "Map<" + self._dart_type(parts[0]) + ", " + self._dart_type(parts[1]) + ">"
            return "Map<dynamic, dynamic>"
        # tuple[...] → List<dynamic>
        if t.startswith("tuple[") and t.endswith("]"):
            return "List<dynamic>"
        # set[T]
        if t.startswith("set[") and t.endswith("]"):
            inner = t[4:-1].strip()
            return "Set<" + self._dart_type(inner) + ">"
        # callable
        if t.startswith("callable") or t == "callable":
            return "Function"
        # User-defined class
        if t in self.class_names:
            # IntEnum/IntFlag subclasses: use int type for bitwise ops support
            if t in self.intflag_classes:
                return "int"
            return t
        return "dynamic"

    def _split_generic_args(self, inner: str) -> list[str]:
        """Split 'K, V' respecting nested brackets."""
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
        if len(current) > 0:
            parts.append("".join(current).strip())
        return parts

    def _dart_return_type(self, stmt: dict[str, Any]) -> str:
        """Get the Dart return type for a function statement.

        Container types use ``dynamic`` to avoid type mismatch.
        """
        rt = stmt.get("return_type")
        if isinstance(rt, str) and rt.strip() != "":
            dart_t = self._dart_type(rt)
            if dart_t.startswith("List<") or dart_t.startswith("Map<") or dart_t.startswith("Set<"):
                return "dynamic"
            return dart_t
        return "dynamic"

    def _dart_arg_type(self, stmt: dict[str, Any], arg_name: str) -> str:
        """Get the Dart type for a function argument.
        """
        arg_types_any = stmt.get("arg_types")
        arg_types = arg_types_any if isinstance(arg_types_any, dict) else {}
        t = arg_types.get(arg_name)
        if isinstance(t, str) and t.strip() != "":
            dart_t = self._dart_type(t)
            if dart_t.startswith("List<") or dart_t.startswith("Map<") or dart_t.startswith("Set<"):
                return "dynamic"
            return dart_t
        return "dynamic"

    def _dart_decl_type(self, stmt: dict[str, Any], value_node: Any) -> str:
        """Get Dart type for a variable declaration from decl_type, annotation, or inference.

        Container types (List/Map/Set) use ``var`` to avoid type mismatch
        with runtime helpers that return ``dynamic``.
        """
        raw = ""
        decl_type_any = stmt.get("decl_type")
        if isinstance(decl_type_any, str) and decl_type_any.strip() != "":
            raw = decl_type_any.strip()
        if raw == "":
            anno_any = stmt.get("annotation")
            if isinstance(anno_any, str) and anno_any.strip() != "":
                raw = anno_any.strip()
        if raw == "":
            raw = self._infer_decl_type_from_expr(value_node)
        if raw == "":
            return "var"
        dart_t = self._dart_type(raw)
        # Container types → var (runtime helpers return dynamic)
        if dart_t.startswith("List<") or dart_t.startswith("Map<") or dart_t.startswith("Set<"):
            return "var"
        return dart_t

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

    def _container_kind_from_decl_type(self, type_name: Any) -> str:
        if not isinstance(type_name, str):
            return ""
        ts: str = type_name
        if ts.startswith("dict["):
            return "dict"
        if ts.startswith("list[") or ts.startswith("tuple[") or ts.startswith("set["):
            return "list"
        if type_name in {"bytes", "bytearray"}:
            return "list"
        return ""

    def _is_container_east_type(self, type_name: Any) -> bool:
        return self._container_kind_from_decl_type(type_name) != ""

    def _push_function_context(self, stmt: dict[str, Any], arg_names: list[str], arg_order: list[Any]) -> None:
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
                if self._is_container_east_type(arg_type):
                    ref_vars.add(safe_name)
            i += 1
        self._local_type_stack.append(type_map)
        self._ref_var_stack.append(ref_vars)
        self._local_var_stack.append(local_vars)

    def _pop_function_context(self) -> None:
        if len(self._local_type_stack) > 0:
            self._local_type_stack.pop()
        if len(self._ref_var_stack) > 0:
            self._ref_var_stack.pop()
        if len(self._local_var_stack) > 0:
            self._local_var_stack.pop()

    def _const_int_literal(self, node_any: Any) -> int | None:
        if not isinstance(node_any, dict):
            return None
        nd5: dict[str, Any] = node_any
        kind = nd5.get("kind")
        if kind == "Constant":
            value = nd5.get("value")
            if isinstance(value, bool):
                return None
            if isinstance(value, int):
                return value
            return None
        if kind == "UnaryOp" and str(nd5.get("op")) == "USub":
            operand = self._const_int_literal(nd5.get("operand"))
            if operand is None:
                return None
            return -operand
        return None

    def _resolved_runtime_call(self, expr_any: Any) -> str:
        if not isinstance(expr_any, dict):
            return ""
        ed2: dict[str, Any] = expr_any
        runtime_call = ed2.get("runtime_call")
        if isinstance(runtime_call, str) and runtime_call != "":
            return runtime_call
        resolved_runtime_call = ed2.get("resolved_runtime_call")
        if isinstance(resolved_runtime_call, str) and resolved_runtime_call != "":
            return resolved_runtime_call
        return ""

    def _is_sequence_expr(self, node_any: Any) -> bool:
        if not isinstance(node_any, dict):
            return False
        nd4: dict[str, Any] = node_any
        kind = nd4.get("kind")
        if kind in {"List", "Tuple", "JoinedStr", "Dict", "Set"}:
            return True
        if kind == "Constant" and isinstance(nd4.get("value"), str):
            return True
        resolved = self._lookup_expr_type(node_any)
        if (
            resolved == "str"
            or resolved.startswith("list[")
            or resolved.startswith("tuple[")
            or resolved.startswith("dict[")
            or resolved.startswith("set[")
        ):
            return True
        return False

    def _is_list_expr(self, node_any: Any) -> bool:
        """Return True if node is definitively a list/sequence (not a string)."""
        if not isinstance(node_any, dict):
            return False
        kind = node_any.get("kind")
        if kind == "List":
            return True
        if kind == "ListComp":
            return True
        resolved = self._lookup_expr_type(node_any)
        if resolved.startswith("list[") or resolved == "list":
            return True
        return False

    def _render_cond_expr(self, test_any: Any) -> str:
        test = self._render_expr(test_any)
        if self._is_sequence_expr(test_any):
            return "pytraTruthy(" + test + ")"
        # Dynamic/unknown type: use pytraTruthy to handle Python truthiness
        if isinstance(test_any, dict):
            resolved = self._lookup_expr_type(test_any)
            if resolved in {"", "dynamic", "unknown", "Any", "object"} or resolved in {"bytes", "bytearray"}:
                return "pytraTruthy(" + test + ")"
        return test

    def _render_format_spec(self, val_expr: str, fmt_spec: Any) -> str:
        """Render a Python format spec (e.g. '4d', '.4f') to Dart string formatting."""
        import re as _re
        if not isinstance(fmt_spec, str) or fmt_spec == "":
            return "(" + val_expr + ").toString()"
        # Parse: [[fill]align][sign][#][0][width][grouping][.precision][type]
        m = _re.match(r'^([<>^=]?)(\+|-| )?#?0?(\d*)([_,]?)(?:\.(\d+))?([bcdeEfFgGnosxX%]?)$', fmt_spec)
        if not m:
            return "(" + val_expr + ").toString()"
        align, _sign, width_str, _group, precision_str, type_char = m.groups()
        width = int(width_str) if width_str else 0
        precision = int(precision_str) if precision_str else -1
        # Float types
        if type_char in ("f", "F", "e", "E", "g", "G"):
            if precision >= 0:
                result = "(" + val_expr + ").toStringAsFixed(" + str(precision) + ")"
            else:
                result = "(" + val_expr + ").toStringAsFixed(6)"
            if width > 0:
                result = result + ".padLeft(" + str(width) + ")"
            return result
        # Integer types
        if type_char in ("d", "i", ""):
            result = "(" + val_expr + ").toString()"
            if width > 0:
                pad_fn = ".padLeft(" if (align == "" or align == ">") else ".padRight("
                result = result + pad_fn + str(width) + ")"
            return result
        # Hex
        if type_char in ("x", "X"):
            result = "(" + val_expr + ").toRadixString(16)"
            if type_char == "X":
                result = result + ".toUpperCase()"
            if width > 0:
                result = result + ".padLeft(" + str(width) + ")"
            return result
        return "(" + val_expr + ").toString()"

    def _is_str_expr(self, node_any: Any) -> bool:
        if not isinstance(node_any, dict):
            return False
        nd3: dict[str, Any] = node_any
        if nd3.get("kind") == "Constant" and isinstance(nd3.get("value"), str):
            return True
        return self._lookup_expr_type(node_any) == "str"

    def _lookup_expr_type(self, node_any: Any) -> str:
        if not isinstance(node_any, dict):
            return ""
        nd2: dict[str, Any] = node_any
        resolved = nd2.get("resolved_type")
        if isinstance(resolved, str) and resolved not in {"", "unknown"}:
            return resolved
        kind = nd2.get("kind")
        if kind == "Name":
            safe_name = _safe_ident(nd2.get("id"), "")
            if safe_name != "":
                # Search all frames from innermost to outermost
                for frame in reversed(self._local_type_stack):
                    mapped = frame.get(safe_name)
                    if isinstance(mapped, str) and mapped != "":
                        return mapped
        if kind == "Constant":
            value = nd2.get("value")
            if isinstance(value, bool):
                return "bool"
            if isinstance(value, int):
                return "int"
            if isinstance(value, float):
                return "float"
            if isinstance(value, str):
                return "str"
        if kind in {"List", "Tuple"}:
            return "list[Any]"
        if kind == "Dict":
            return "dict[Any,Any]"
        if kind == "Set":
            return "set[Any]"
        return ""

    def _infer_decl_type_from_expr(self, node_any: Any) -> str:
        inferred = self._lookup_expr_type(node_any)
        if inferred == "":
            return ""
        if inferred in {"bool", "int", "float", "str"}:
            return inferred
        if (
            inferred.startswith("list[")
            or inferred.startswith("tuple[")
            or inferred.startswith("dict[")
            or inferred.startswith("set[")
        ):
            return inferred
        return ""

    def _is_extern_var(self, stmt: dict[str, Any]) -> bool:
        """Check if a statement is an extern() variable declaration (§4).

        Uses meta.extern_var_v1 as the canonical detection method,
        or detects Assign with value = extern(...) call pattern.
        """
        meta_any = stmt.get("meta")
        if isinstance(meta_any, dict) and isinstance(meta_any.get("extern_var_v1"), dict):
            return True
        # Detect: x = extern(some.attr) or x = extern(some_val)
        value_any = stmt.get("value")
        if isinstance(value_any, dict) and value_any.get("kind") == "Call":
            func = value_any.get("func")
            if isinstance(func, dict) and func.get("kind") == "Name" and func.get("id") == "extern":
                return True
        return False

    def _extern_var_symbol(self, stmt: dict[str, Any], default_name: str) -> str:
        """Get the __native symbol name for an extern var."""
        meta_any = stmt.get("meta")
        if isinstance(meta_any, dict):
            ev1 = meta_any.get("extern_var_v1")
            if isinstance(ev1, dict):
                sym = ev1.get("symbol", "")
                if isinstance(sym, str) and sym != "":
                    return sym
        # Fallback: extract attribute name from extern(module.attr) call
        value_any = stmt.get("value")
        if isinstance(value_any, dict) and value_any.get("kind") == "Call":
            args_any = value_any.get("args")
            if isinstance(args_any, list) and len(args_any) > 0:
                arg = args_any[0]
                if isinstance(arg, dict) and arg.get("kind") == "Attribute":
                    return _safe_ident(arg.get("attr"), default_name)
                if isinstance(arg, dict) and arg.get("kind") == "Name":
                    return _safe_ident(arg.get("id"), default_name)
        return default_name

    def _scan_extern_usage(self, body: list[dict[str, Any]]) -> None:
        """Pre-scan body for @extern functions/variables to set _has_extern_delegation."""
        for stmt in body:
            kind = stmt.get("kind")
            if kind == "FunctionDef":
                decorators_any = stmt.get("decorators")
                decorators = decorators_any if isinstance(decorators_any, list) else []
                if "extern" in decorators:
                    self._has_extern_delegation = True
                    return
            if kind in {"AnnAssign", "Assign"}:
                if self._is_extern_var(stmt):
                    self._has_extern_delegation = True
                    return

    def transpile(self) -> str:
        module_comments = self._module_leading_comment_lines(prefix="// ")
        if len(module_comments) > 0:
            self.lines.extend(module_comments)
            self.lines.append("")
        body = self._dict_list(self.east_doc.get("body"))
        main_guard = self._dict_list(self.east_doc.get("main_guard_body"))
        self._scan_module_symbols(body)
        # Pre-scan for @extern to know if __native import is needed
        self._scan_extern_usage(body)
        # Emit imports header
        self._emit_imports(body)
        # Runtime helpers are provided by py_runtime.dart (no inline emit needed)
        # Emit body
        for stmt in body:
            self._emit_stmt(stmt)
        # Emit main guard — only for entry modules (§8)
        if self._is_entry:
            self._emit_line("")
            self._emit_line("void main() {")
            self.indent += 1
            for stmt in main_guard:
                self._emit_stmt(stmt)
            self.indent -= 1
            self._emit_line("}")
        return "\n".join(self.lines).rstrip() + "\n"

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
        self.lines.append(("  " * self.indent) + text)

    def _emit_block(self, body_any: Any) -> None:
        body = self._dict_list(body_any)
        if len(body) == 0:
            return
        i = 0
        while i < len(body):
            self._emit_stmt(body[i])
            i += 1

    def _has_continue_in_block(self, body_any: Any) -> bool:
        body = self._dict_list(body_any)
        i = 0
        while i < len(body):
            stmt = body[i]
            kind = stmt.get("kind")
            if kind == "Continue":
                return True
            if kind == "Expr":
                value_any = stmt.get("value")
                if isinstance(value_any, dict) and value_any.get("kind") == "Name":
                    if str(value_any.get("id")) == "continue":
                        return True
            if kind == "If":
                if self._has_continue_in_block(stmt.get("body")):
                    return True
                if self._has_continue_in_block(stmt.get("orelse")):
                    return True
            if kind == "ForCore" or kind == "While":
                if self._has_continue_in_block(stmt.get("body")):
                    return True
            i += 1
        return False

    def _scan_module_symbols(self, body: list[dict[str, Any]]) -> None:
        self.class_names = set()
        self.intflag_classes = set()
        self.imported_modules = set()
        self._module_aliases = {}
        self.function_names = set()
        self._function_return_types = {}
        self._class_field_types = {}
        self._class_method_names: dict[str, set[str]] = {}  # cls_name → method names
        self._toplevel_fn_conflicts: set[str] = set()  # function names shadowed by class methods
        self.relative_import_name_aliases = _collect_relative_import_name_aliases(self.east_doc)
        for stmt in body:
            kind = stmt.get("kind")
            if kind == "ClassDef":
                cls_name = _safe_ident(stmt.get("name"), "Class_")
                self.class_names.add(cls_name)
                base_any = stmt.get("base")
                base_safe = _safe_ident(base_any, "") if isinstance(base_any, str) else ""
                if base_safe in {"IntEnum", "IntFlag", "IntEnum_", "IntFlag_"}:
                    self.intflag_classes.add(cls_name)
                # Collect field types
                fields: dict[str, str] = {}
                cls_body = stmt.get("body")
                if isinstance(cls_body, list):
                    for sub in cls_body:
                        if isinstance(sub, dict) and sub.get("kind") == "AnnAssign":
                            target_any = sub.get("target")
                            if isinstance(target_any, dict) and target_any.get("kind") == "Name":
                                fname = _safe_ident(target_any.get("id"), "field")
                                ftype = sub.get("annotation")
                                if not isinstance(ftype, str) or ftype.strip() == "":
                                    ftype = sub.get("decl_type")
                                if isinstance(ftype, str) and ftype.strip() != "":
                                    fields[fname] = ftype.strip()
                        if isinstance(sub, dict) and sub.get("kind") == "FunctionDef":
                            fn_name = _safe_ident(sub.get("name"), "fn")
                            rt = sub.get("return_type")
                            if isinstance(rt, str) and rt.strip() != "":
                                self._function_return_types[cls_name + "." + fn_name] = rt.strip()
                            # Track class method names for conflict detection
                            if cls_name not in self._class_method_names:
                                self._class_method_names[cls_name] = set()
                            self._class_method_names[cls_name].add(fn_name)
                field_types_any = stmt.get("field_types")
                if isinstance(field_types_any, dict):
                    for fk, fv in field_types_any.items():
                        if isinstance(fk, str) and isinstance(fv, str) and fv.strip() != "":
                            fields[_safe_ident(fk, "field")] = fv.strip()
                self._class_field_types[cls_name] = fields
                continue
            if kind == "FunctionDef":
                fn_name = _safe_ident(stmt.get("name"), "fn")
                self.function_names.add(fn_name)
                rt = stmt.get("return_type")
                if isinstance(rt, str) and rt.strip() != "":
                    self._function_return_types[fn_name] = rt.strip()
                continue
            if kind == "Import":
                names_any = stmt.get("names")
                names = names_any if isinstance(names_any, list) else []
                for ent in names:
                    if not isinstance(ent, dict):
                        continue
                    module_name = ent.get("name")
                    if not isinstance(module_name, str) or module_name == "":
                        continue
                    asname = ent.get("asname")
                    alias = asname if isinstance(asname, str) and asname != "" else module_name.split(".")[-1]
                    resolved = resolve_import_binding_doc(module_name, "", "module")
                    if len(resolved) > 0:
                        self.imported_modules.add(_safe_ident(alias, "mod"))
                continue
            if kind == "ImportFrom":
                module_name = stmt.get("module")
                if not isinstance(module_name, str):
                    continue
                level_any = stmt.get("level")
                level = level_any if isinstance(level_any, int) else 0
                names_any = stmt.get("names")
                names = names_any if isinstance(names_any, list) else []
                for ent in names:
                    if not isinstance(ent, dict):
                        continue
                    symbol = ent.get("name")
                    if not isinstance(symbol, str) or symbol == "":
                        continue
                    asname = ent.get("asname")
                    alias = asname if isinstance(asname, str) and asname != "" else symbol
                    if level > 0 or module_name.startswith("."):
                        module_path = _relative_import_module_path(module_name)
                        if module_path == "":
                            self.imported_modules.add(_safe_ident(alias, "mod"))
                        continue
                    resolved = resolve_import_binding_doc(module_name, symbol, "symbol")
                    if resolved.get("resolved_binding_kind") == "module":
                        self.imported_modules.add(_safe_ident(alias, "mod"))
        # Compute conflicts: top-level function names that are also class method names
        all_method_names: set[str] = set()
        for methods in self._class_method_names.values():
            all_method_names.update(methods)
        self._toplevel_fn_conflicts = self.function_names & all_method_names

    def _render_name_expr(self, expr_any: dict[str, Any]) -> str:
        ident = _safe_ident(expr_any.get("id"), "value")
        if ident == "self" and self.current_class_name != "":
            return "this"
        if ident == "main" and "__pytra_main" in self.function_names and "main" not in self.function_names:
            ident = "__pytra_main"
        return self.relative_import_name_aliases.get(ident, ident)

    def _emit_imports(self, body: list[dict[str, Any]]) -> None:
        """Emit import section using build_import_alias_map (§3/§7).

        Uses _module_id_to_import_path to compute paths from module_id
        without hardcoding any specific module names (§1).
        """
        rt_prefix = self._root_rel_prefix
        dart_import_lines: list[str] = []
        alias_lines: list[str] = []
        # Always import py_runtime
        dart_import_lines.append("import '" + rt_prefix + "built_in/py_runtime.dart';")
        # Use build_import_alias_map + resolve_import_binding_doc (§3/§7)
        meta_any = self.east_doc.get("meta")
        meta = meta_any if isinstance(meta_any, dict) else {}
        self.import_alias_modules = build_import_alias_map(meta)
        # Track which module_ids we've already emitted import statements for
        imported_module_paths: dict[str, str] = {}  # module_id -> dart alias
        mod_alias_seq = 0
        # Scan body for import statements and use resolve_import_binding_doc
        for stmt in body:
            stmt_kind = stmt.get("kind")
            if stmt_kind == "Import":
                names_any = stmt.get("names")
                names = names_any if isinstance(names_any, list) else []
                for ent in names:
                    if not isinstance(ent, dict):
                        continue
                    mod = ent.get("name")
                    if not isinstance(mod, str) or mod == "":
                        continue
                    asname = ent.get("asname")
                    alias = asname if isinstance(asname, str) and asname != "" else mod.split(".")[-1]
                    public_alias = _safe_ident(alias, "mod")
                    alias_txt = self._next_module_alias(public_alias)
                    resolved = resolve_import_binding_doc(mod, "", "module")
                    if len(resolved) == 0:
                        continue
                    runtime_mod = resolved.get("runtime_module_id", "")
                    if runtime_mod == "":
                        runtime_mod = mod
                    mod_canon = canonical_runtime_module_id(runtime_mod)
                    if mod_canon == "":
                        mod_canon = runtime_mod
                    imp_path = _module_id_to_import_path(mod_canon, ".dart", rt_prefix)
                    dart_import_lines.append("import '" + imp_path + "' as " + alias_txt + ";")
                    imported_module_paths[mod_canon] = alias_txt
                    self._module_aliases[mod_canon] = alias_txt
                    self.imported_modules.add(alias_txt)
                    self.relative_import_name_aliases[public_alias] = alias_txt
            elif stmt_kind == "ImportFrom":
                mod = stmt.get("module")
                if not isinstance(mod, str):
                    continue
                level_any = stmt.get("level")
                level = level_any if isinstance(level_any, int) else 0
                if level > 0 or mod.startswith("."):
                    continue
                names_any = stmt.get("names")
                names = names_any if isinstance(names_any, list) else []
                for ent in names:
                    if not isinstance(ent, dict):
                        continue
                    sym = ent.get("name")
                    if not isinstance(sym, str) or sym == "":
                        continue
                    asname = ent.get("asname")
                    alias = asname if isinstance(asname, str) and asname != "" else sym
                    alias_txt = _safe_ident(alias, sym)
                    # Skip compile-time-only symbols
                    if sym in _COMPILETIME_STD_IMPORT_SYMBOLS:
                        continue
                    resolved = resolve_import_binding_doc(mod, sym, "symbol")
                    if len(resolved) == 0:
                        # Unresolved import (e.g., Python stdlib) — skip
                        continue
                    resolved_kind = resolved.get("resolved_binding_kind", "")
                    runtime_mod = resolved.get("runtime_module_id", "")
                    if runtime_mod == "":
                        runtime_mod = mod
                    mod_canon = canonical_runtime_module_id(runtime_mod)
                    if mod_canon == "":
                        mod_canon = runtime_mod
                    if resolved_kind == "module":
                        # Submodule import (e.g., from pytra.utils import png)
                        public_alias = alias_txt
                        alias_txt = self._next_module_alias(public_alias)
                        imp_path = _module_id_to_import_path(mod_canon, ".dart", rt_prefix)
                        dart_import_lines.append("import '" + imp_path + "' as " + alias_txt + ";")
                        imported_module_paths[mod_canon] = alias_txt
                        self._module_aliases[mod_canon] = alias_txt
                        self.imported_modules.add(alias_txt)
                        self.relative_import_name_aliases[public_alias] = alias_txt
                    else:
                        # Symbol import (e.g., from pytra.std.time import perf_counter)
                        if mod_canon not in imported_module_paths:
                            mod_alias_seq += 1
                            mod_alias = "__mod_" + str(mod_alias_seq)
                            imp_path = _module_id_to_import_path(mod_canon, ".dart", rt_prefix)
                            dart_import_lines.append("import '" + imp_path + "' as " + mod_alias + ";")
                            imported_module_paths[mod_canon] = mod_alias
                        mod_alias = imported_module_paths[mod_canon]
                        runtime_sym_kind = resolved.get("runtime_symbol_kind", "")
                        # Use original symbol name (sym) for module access, alias_txt for local name
                        sym_safe = _safe_ident(sym, sym)
                        if runtime_sym_kind == "class":
                            # Class constructor: use name alias (module.Class) instead of var
                            self.relative_import_name_aliases[alias_txt] = mod_alias + "." + sym_safe
                        else:
                            alias_lines.append("var " + alias_txt + " = " + mod_alias + "." + sym_safe + ";")
        for node in self._walk_nodes(body):
            runtime_module_id = node.get("runtime_module_id") if isinstance(node, dict) and isinstance(node.get("runtime_module_id"), str) else ""
            if runtime_module_id != "":
                runtime_mod_canon = canonical_runtime_module_id(runtime_module_id)
                if (
                    runtime_mod_canon != ""
                    and runtime_mod_canon not in imported_module_paths
                    and runtime_module_exists(runtime_mod_canon)
                    and not should_skip_module(runtime_mod_canon, self._mapping)
                ):
                    runtime_alias = self._next_module_alias(runtime_mod_canon.split(".")[-1])
                    runtime_path = _module_id_to_import_path(runtime_mod_canon, ".dart", rt_prefix)
                    dart_import_lines.append("import '" + runtime_path + "' as " + runtime_alias + ";")
                    imported_module_paths[runtime_mod_canon] = runtime_alias
                    self._module_aliases[runtime_mod_canon] = runtime_alias
                    self.imported_modules.add(runtime_alias)
            nested_module_id = self._resolve_module_attr_module_id(node)
            if nested_module_id == "" or nested_module_id in imported_module_paths:
                continue
            nested_alias = self._next_module_alias(nested_module_id.split(".")[-1])
            nested_path = _module_id_to_import_path(nested_module_id, ".dart", rt_prefix)
            dart_import_lines.append("import '" + nested_path + "' as " + nested_alias + ";")
            imported_module_paths[nested_module_id] = nested_alias
            self._module_aliases[nested_module_id] = nested_alias
            self.imported_modules.add(nested_alias)
        # If this module has @extern delegation, add the __native import (§4/§5.1)
        if self._has_extern_delegation and self._module_id != "":
            native_path = _module_id_to_native_import_path(self._module_id, ".dart", rt_prefix)
            dart_import_lines.append("import '" + native_path + "' as __native;")
        # Emit all lines with Dart import directives first, then alias lines
        for line in dart_import_lines:
            self._emit_line(line)
        if len(dart_import_lines) > 0 and len(alias_lines) > 0:
            self._emit_line("")
        for line in alias_lines:
            self._emit_line(line)
        if len(dart_import_lines) > 0 or len(alias_lines) > 0:
            self._emit_line("")

    def _emit_stmt(self, stmt: dict[str, Any]) -> None:
        self._emit_leading_trivia(stmt, prefix="// ")
        kind = stmt.get("kind")
        if kind in {"Import", "ImportFrom"}:
            return
        if kind == "ClassDef":
            self._emit_class_def(stmt)
            return
        if kind == "FunctionDef" or kind == "ClosureDef":
            self._emit_function_def(stmt)
            return
        if kind == "Return":
            value_node = stmt.get("value")
            if value_node is None:
                self._emit_line("return;")
            else:
                val = self._render_expr(value_node)
                self._emit_line("return " + val + ";")
            return
        if kind == "AnnAssign":
            # §4: extern() variable → __native delegation (detect via meta.extern_var_v1)
            if self._is_extern_var(stmt):
                target_node = stmt.get("target")
                if isinstance(target_node, dict) and target_node.get("kind") == "Name":
                    var_name = _safe_ident(target_node.get("id"), "value")
                    sym_name = self._extern_var_symbol(stmt, var_name)
                    decl_type_any = stmt.get("decl_type")
                    decl_type = decl_type_any.strip() if isinstance(decl_type_any, str) else ""
                    if decl_type == "":
                        anno_any = stmt.get("annotation")
                        if isinstance(anno_any, str):
                            decl_type = anno_any.strip()
                    dart_t = self._dart_type(decl_type) if decl_type != "" else "dynamic"
                    self._emit_line("final " + dart_t + " " + var_name + " = __native." + sym_name + ";")
                    return
            value_node = stmt.get("value")
            target_node = stmt.get("target")
            target = self._render_target(target_node)
            value = self._render_expr(value_node) if isinstance(value_node, dict) else "null"
            if isinstance(target_node, dict) and target_node.get("kind") == "Name":
                target_name = _safe_ident(target_node.get("id"), "value")
                decl_type_any = stmt.get("decl_type")
                decl_type = decl_type_any.strip() if isinstance(decl_type_any, str) else ""
                if decl_type == "":
                    anno_any = stmt.get("annotation")
                    if isinstance(anno_any, str):
                        anno_s: str = anno_any
                        decl_type = anno_s.strip()
                if decl_type == "":
                    decl_type = self._infer_decl_type_from_expr(value_node)
                dart_t_raw = self._dart_type(decl_type) if decl_type != "" else "var"
                dart_t = "var" if (dart_t_raw.startswith("List<") or dart_t_raw.startswith("Map<") or dart_t_raw.startswith("Set<")) else dart_t_raw
                if value_node is None and bool(stmt.get("declare")):
                    if decl_type in _NIL_FREE_DECL_TYPES:
                        if decl_type != "":
                            self._current_type_map()[target_name] = decl_type
                        if len(self._local_var_stack) > 0:
                            self._current_local_vars().add(target_name)
                        self._emit_line(dart_t + " " + target + ";")
                        return
                # null assignment to non-nullable type → use late or nullable
                if value == "null" and dart_t not in {"var", "dynamic"} and not dart_t.endswith("?"):
                    if decl_type != "":
                        self._current_type_map()[target_name] = decl_type
                    if len(self._local_var_stack) > 0:
                        self._current_local_vars().add(target_name)
                    self._emit_line("late " + dart_t + " " + target + ";")
                    return
                if decl_type != "":
                    self._current_type_map()[target_name] = decl_type
                if len(self._local_var_stack) > 0:
                    self._current_local_vars().add(target_name)
                self._emit_line(dart_t + " " + target + " = " + value + ";")
            else:
                self._emit_line(target + " = " + value + ";")
            return
        if kind == "Assign":
            # §4: extern() variable → __native delegation (Assign without type annotation)
            if self._is_extern_var(stmt):
                self._has_extern_delegation = True
                target_any_ev = stmt.get("target")
                if isinstance(target_any_ev, dict) and target_any_ev.get("kind") == "Name":
                    var_name = _safe_ident(target_any_ev.get("id"), "value")
                    sym_name = self._extern_var_symbol(stmt, var_name)
                    self._emit_line("final dynamic " + var_name + " = __native." + sym_name + ";")
                    return
            target_any = stmt.get("target")
            if isinstance(target_any, dict):
                td2: dict[str, Any] = target_any
                if td2.get("kind") == "Tuple":
                    self._emit_tuple_assign(target_any, stmt.get("value"))
                    return
                target = self._render_target(target_any)
                value = self._coerce_assignment_expr(target_any, self._render_expr(stmt.get("value")))
                if isinstance(target_any, dict) and td2.get("kind") == "Name":
                    target_name = _safe_ident(td2.get("id"), "value")
                    if target_name.startswith("__tup_"):
                        is_module_level = len(self._local_var_stack) == 0
                        already_declared = not is_module_level and target_name in self._current_local_vars()
                        tuple_value = "pytraTupleView(" + value + ")"
                        if not already_declared:
                            if not is_module_level:
                                self._current_local_vars().add(target_name)
                            self._emit_line("var " + target + " = " + tuple_value + ";")
                            return
                        self._emit_line(target + " = " + tuple_value + ";")
                        return
                    decl_type_any = stmt.get("decl_type")
                    decl_type = decl_type_any.strip() if isinstance(decl_type_any, str) else ""
                    if decl_type == "":
                        mapped_decl = self._current_type_map().get(target_name)
                        decl_type = mapped_decl.strip() if isinstance(mapped_decl, str) else ""
                    if decl_type == "":
                        decl_type = self._infer_decl_type_from_expr(stmt.get("value"))
                    if decl_type != "":
                        self._current_type_map()[target_name] = decl_type
                    is_module_level = len(self._local_var_stack) == 0
                    already_declared = not is_module_level and target_name in self._current_local_vars()
                    if not already_declared:
                        if not is_module_level:
                            self._current_local_vars().add(target_name)
                        dart_t_raw = self._dart_type(decl_type) if decl_type != "" else "var"
                        dart_t = "var" if (dart_t_raw.startswith("List<") or dart_t_raw.startswith("Map<") or dart_t_raw.startswith("Set<")) else dart_t_raw
                        self._emit_line(dart_t + " " + target + " = " + value + ";")
                        return
                self._emit_line(target + " = " + value + ";")
                return
            targets = stmt.get("targets")
            if isinstance(targets, list) and len(targets) > 0 and isinstance(targets[0], dict):
                if targets[0].get("kind") == "Tuple":
                    self._emit_tuple_assign(targets[0], stmt.get("value"))
                    return
                target = self._render_target(targets[0])
                value = self._coerce_assignment_expr(targets[0], self._render_expr(stmt.get("value")))
                if targets[0].get("kind") == "Name":
                    target_name = _safe_ident(targets[0].get("id"), "value")
                    if target_name.startswith("__tup_"):
                        is_module_level = len(self._local_var_stack) == 0
                        already_declared = not is_module_level and target_name in self._current_local_vars()
                        tuple_value = "pytraTupleView(" + value + ")"
                        if not already_declared:
                            if not is_module_level:
                                self._current_local_vars().add(target_name)
                            self._emit_line("var " + target + " = " + tuple_value + ";")
                            return
                        self._emit_line(target + " = " + tuple_value + ";")
                        return
                    decl_type_any = stmt.get("decl_type")
                    decl_type = decl_type_any.strip() if isinstance(decl_type_any, str) else ""
                    if decl_type == "":
                        mapped_decl = self._current_type_map().get(target_name)
                        decl_type = mapped_decl.strip() if isinstance(mapped_decl, str) else ""
                    if decl_type == "":
                        decl_type = self._infer_decl_type_from_expr(stmt.get("value"))
                    if decl_type != "":
                        self._current_type_map()[target_name] = decl_type
                    is_module_level = len(self._local_var_stack) == 0
                    already_declared = not is_module_level and target_name in self._current_local_vars()
                    if not already_declared:
                        if not is_module_level:
                            self._current_local_vars().add(target_name)
                        dart_t_raw = self._dart_type(decl_type) if decl_type != "" else "var"
                        dart_t = "var" if (dart_t_raw.startswith("List<") or dart_t_raw.startswith("Map<") or dart_t_raw.startswith("Set<")) else dart_t_raw
                        self._emit_line(dart_t + " " + target + " = " + value + ";")
                        return
                self._emit_line(target + " = " + value + ";")
                return
            raise RuntimeError("lang=dart unsupported assign shape")
        if kind == "AugAssign":
            target = self._render_target(stmt.get("target"))
            op = str(stmt.get("op"))
            value = self._render_expr(stmt.get("value"))
            op_token = _binop_symbol(op)
            # If target is int-typed, cast the augmented result to avoid num promotion
            target_type = self._lookup_expr_type(stmt.get("target"))
            if target_type in {"int", "int64", "int32"} and op in {"Add", "Sub", "Mult", "Mod", "FloorDiv"}:
                self._emit_line(target + " = ((" + target + " " + op_token + " " + value + ") as int);")
            else:
                self._emit_line(target + " " + op_token + "= " + value + ";")
            return
        if kind == "Swap":
            self._emit_swap(stmt)
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
            self._emit_line(self._render_expr(value_any) + ";")
            return
        if kind == "Raise":
            exc_any = stmt.get("exc")
            if isinstance(exc_any, dict):
                self._emit_line("throw " + self._render_expr(exc_any) + ";")
            else:
                self._emit_line("rethrow;")
            return
        if kind == "Try":
            body = self._dict_list(stmt.get("body"))
            self._emit_line("try {")
            self.indent += 1
            i = 0
            while i < len(body):
                self._emit_stmt(body[i])
                i += 1
            self.indent -= 1
            handlers_any = stmt.get("handlers")
            handlers = handlers_any if isinstance(handlers_any, list) else []
            if len(handlers) > 0:
                i = 0
                while i < len(handlers):
                    h = handlers[i]
                    if isinstance(h, dict):
                        hd: dict[str, Any] = h
                        handler_name = hd.get("name")
                        handler_type = self._render_except_handler_type(hd.get("type"))
                        if isinstance(handler_name, str) and handler_name != "":
                            if handler_type != "":
                                self._emit_line("} on " + handler_type + " catch (" + _safe_ident(handler_name, "e") + ") {")
                            else:
                                self._emit_line("} catch (" + _safe_ident(handler_name, "e") + ") {")
                        else:
                            if handler_type != "":
                                self._emit_line("} on " + handler_type + " catch (e) {")
                            else:
                                self._emit_line("} catch (e) {")
                        self.indent += 1
                        h_body = self._dict_list(hd.get("body"))
                        j = 0
                        while j < len(h_body):
                            self._emit_stmt(h_body[j])
                            j += 1
                        self.indent -= 1
                    i += 1
            elif len(self._dict_list(stmt.get("finalbody"))) == 0:
                self._emit_line("} catch (e) {")
                self.indent += 1
                self._emit_line("// handler")
                self.indent -= 1
            finalbody = self._dict_list(stmt.get("finalbody"))
            if len(finalbody) > 0:
                self._emit_line("} finally {")
                self.indent += 1
                i = 0
                while i < len(finalbody):
                    self._emit_stmt(finalbody[i])
                    i += 1
                self.indent -= 1
            self._emit_line("}")
            return
        if kind == "If":
            self._emit_if(stmt)
            return
        if kind == "ForCore":
            self._emit_for_core(stmt)
            return
        if kind == "While":
            self._emit_while(stmt)
            return
        if kind == "Pass":
            self._emit_line("/* pass */")
            return
        if kind == "TypeAlias":
            # type X = A | B — no runtime effect in Dart, emit as comment
            alias_name = _safe_ident(stmt.get("name"), "T")
            self._emit_line("// type alias: " + alias_name)
            return
        if kind == "Yield":
            val = self._render_expr(stmt.get("value"))
            self._emit_line("yield " + val + ";")
            return
        if kind == "VarDecl":
            self._emit_var_decl(stmt)
            return
        raise RuntimeError("lang=dart unsupported stmt kind: " + str(kind))

    def _fn_emit_name(self, name: str) -> str:
        """Return the Dart name for a top-level function, avoiding class method conflicts."""
        if name in self._toplevel_fn_conflicts:
            return "_pytra_top_" + name
        return name

    def _emit_function_def(self, stmt: dict[str, Any]) -> None:
        name = _safe_ident(stmt.get("name"), "fn")
        arg_order_any = stmt.get("arg_order")
        args = arg_order_any if isinstance(arg_order_any, list) else []
        vararg_name_any = stmt.get("vararg_name")
        if isinstance(vararg_name_any, str) and vararg_name_any.strip() != "":
            args = list(args) + [vararg_name_any]
        arg_defaults_any = stmt.get("arg_defaults")
        arg_defaults = arg_defaults_any if isinstance(arg_defaults_any, dict) else {}
        arg_names: list[str] = []
        for a in args:
            arg_names.append(_safe_ident(a, "arg"))
        # @extern function → delegate to runtime helper
        decorators_any = stmt.get("decorators")
        decorators = decorators_any if isinstance(decorators_any, list) else []
        if "extern" in decorators:
            self._emit_extern_function(stmt, name, arg_names)
            return
        param_parts: list[str] = []
        optional_parts: list[str] = []
        for a_raw, a_safe in zip(args, arg_names):
            raw_name = a_raw if isinstance(a_raw, str) else a_safe
            at = self._dart_arg_type(stmt, raw_name)
            if raw_name in arg_defaults:
                default_node = arg_defaults[raw_name]
                default_val = self._render_param_default_expr(default_node)
                optional_parts.append(at + " " + a_safe + " = " + default_val)
            else:
                param_parts.append(at + " " + a_safe)
        if len(optional_parts) > 0:
            params = ", ".join(param_parts + ["[" + ", ".join(optional_parts) + "]"]) if len(param_parts) > 0 else "[" + ", ".join(optional_parts) + "]"
        else:
            params = ", ".join(param_parts)
        ret_type = self._dart_return_type(stmt)
        # Rename top-level functions that conflict with class method names
        emit_name = self._fn_emit_name(name) if self.current_class_name == "" else name
        self._emit_line(ret_type + " " + emit_name + "(" + params + ") {")
        self.indent += 1
        self._push_function_context(stmt, arg_names, args)
        self._emit_block(stmt.get("body"))
        self._pop_function_context()
        self.indent -= 1
        self._emit_line("}")
        self._emit_line("")

    def _emit_extern_function(self, stmt: dict[str, Any], name: str, arg_names: list[str]) -> None:
        """Emit @extern function as __native delegation (§4/§5.1).

        Generates: ret_type name(params) { return __native.name(args); }
        The __native import is tracked and emitted in the import header.
        """
        original_name = stmt.get("original_name")
        fn_name = original_name if isinstance(original_name, str) and original_name != "" else name
        # Mark that this module needs a __native import
        self._has_extern_delegation = True
        # Build parameter list using dynamic types to accept any caller convention.
        # @extern functions delegate to __native which handles type coercion.
        arg_order_any = stmt.get("arg_order")
        args_raw = arg_order_any if isinstance(arg_order_any, list) else []
        arg_defaults_any = stmt.get("arg_defaults")
        arg_defaults = arg_defaults_any if isinstance(arg_defaults_any, dict) else {}
        all_arg_names: list[str] = list(arg_names)
        # Append default args that aren't in arg_order
        for dk in arg_defaults:
            dk_safe = _safe_ident(dk, "arg")
            if dk_safe not in all_arg_names:
                all_arg_names.append(dk_safe)
        # Use List<dynamic> args to forward any number of arguments
        param_parts: list[str] = []
        optional_parts: list[str] = []
        for idx, a_safe in enumerate(all_arg_names):
            raw_name = args_raw[idx] if idx < len(args_raw) else a_safe
            at = self._dart_arg_type(stmt, raw_name if isinstance(raw_name, str) else a_safe)
            if at in {"double", "int"}:
                at = "num"
            dk_key = raw_name if isinstance(raw_name, str) else a_safe
            if dk_key in arg_defaults:
                default_node = arg_defaults[dk_key]
                default_val = self._render_param_default_expr(default_node)
                optional_parts.append("dynamic " + a_safe + " = " + default_val)
            else:
                param_parts.append(at + " " + a_safe)
        if len(optional_parts) > 0:
            params = ", ".join(param_parts + ["[" + ", ".join(optional_parts) + "]"]) if len(param_parts) > 0 else "[" + ", ".join(optional_parts) + "]"
        else:
            params = ", ".join(param_parts)
        call_args = ", ".join(all_arg_names)
        ret_type = self._dart_return_type(stmt)
        # §5.1: function name matches original Python name exactly
        self._emit_line(ret_type + " " + fn_name + "(" + params + ") {")
        self.indent += 1
        self._emit_line("return __native." + fn_name + "(" + call_args + ");")
        self.indent -= 1
        self._emit_line("}")
        self._emit_line("")

    def _emit_if(self, stmt: dict[str, Any]) -> None:
        test = self._render_cond_expr(stmt.get("test"))
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

    def _emit_class_def(self, stmt: dict[str, Any]) -> None:
        cls_name = _safe_ident(stmt.get("name"), "Class_")
        base_any = stmt.get("base")
        base_name_raw = _safe_ident(base_any, "") if isinstance(base_any, str) else ""
        base_name = self.relative_import_name_aliases.get(base_name_raw, base_name_raw) if base_name_raw != "" else ""
        meta_any = stmt.get("meta")
        meta = meta_any if isinstance(meta_any, dict) else {}
        is_trait = isinstance(meta.get("trait_v1"), dict)
        implements_traits: list[str] = []
        implements_meta = meta.get("implements_v1")
        if isinstance(implements_meta, dict):
            traits_any = implements_meta.get("traits")
            if isinstance(traits_any, list):
                for trait_any in traits_any:
                    if isinstance(trait_any, str) and trait_any != "":
                        implements_traits.append(_safe_ident(trait_any, "Trait"))
        is_dataclass = bool(stmt.get("dataclass"))
        # Enum base classes are Python-specific markers; skip extends in Dart
        _ENUM_BASE_CLASSES = {"Enum_", "IntEnum", "IntFlag", "IntEnum_", "IntFlag_"}
        if base_name in _ENUM_BASE_CLASSES:
            base_name = ""
        class_head = ("abstract class " if is_trait else "class ") + cls_name
        if base_name != "":
            class_head += " extends " + base_name
        if not is_trait and len(implements_traits) > 0:
            class_head += " implements " + ", ".join(implements_traits)
        self._emit_line(class_head + " {")
        self.indent += 1
        prev_trait = self.current_class_is_trait
        self.current_class_is_trait = is_trait
        body = self._dict_list(stmt.get("body"))
        field_types = self._class_field_types.get(cls_name, {})
        # Collect fields for dataclass or from AnnAssign
        fields: list[str] = []
        field_defaults: dict[str, str] = {}
        static_fields: set[str] = set()
        late_fields: set[str] = set()  # non-dataclass fields declared as `late`
        for sub in body:
            if sub.get("kind") == "AnnAssign":
                target_any = sub.get("target")
                if isinstance(target_any, dict) and target_any.get("kind") == "Name":
                    field_name = _safe_ident(target_any.get("id"), "field")
                    fields.append(field_name)
                    ft = field_types.get(field_name, "")
                    dart_ft = self._dart_type(ft) if ft != "" else "dynamic"
                    # Non-dataclass class-level AnnAssign → static (with value) or late (no value)
                    value_node = sub.get("value")
                    if not is_dataclass and isinstance(value_node, dict):
                        static_fields.add(field_name)
                        default_val = self._render_expr(value_node)
                        self._emit_line("static " + dart_ft + " " + field_name + " = " + default_val + ";")
                        # Don't add to instance fields list
                        fields.pop()
                    elif not is_dataclass:
                        # Non-dataclass annotation without value → late instance field (not ctor param)
                        self._emit_line("late " + dart_ft + " " + field_name + ";")
                        fields.pop()
                        late_fields.add(field_name)
                    else:
                        self._emit_line(dart_ft + " " + field_name + ";")
                    # Collect default value for constructor
                    if isinstance(value_node, dict):
                        field_defaults[field_name] = self._render_expr(value_node)
            elif sub.get("kind") == "Assign" and not is_dataclass:
                # Class-level Assign (e.g. X = 0,) → static field
                t = sub.get("target")
                if not isinstance(t, dict):
                    # fallback: targets list
                    targets_any = sub.get("targets")
                    if isinstance(targets_any, list) and len(targets_any) == 1:
                        t = targets_any[0]
                if isinstance(t, dict) and t.get("kind") == "Name":
                    field_name = _safe_ident(t.get("id"), "field")
                    value_node = sub.get("value")
                    val_str = self._render_expr(value_node) if isinstance(value_node, dict) else "null"
                    static_fields.add(field_name)
                    self._emit_line("static dynamic " + field_name + " = " + val_str + ";")
        # Scan __init__ for self.xxx = ... assignments to declare fields
        has_init = False
        for sub in body:
            if sub.get("kind") not in {"FunctionDef", "ClosureDef"}:
                continue
            if sub.get("name") == "__init__":
                has_init = True
                init_body = sub.get("body")
                if isinstance(init_body, list):
                    for init_stmt in init_body:
                        if not isinstance(init_stmt, dict):
                            continue
                        sk = init_stmt.get("kind")
                        if sk != "Assign" and sk != "AnnAssign":
                            continue
                        t_any = init_stmt.get("target")
                        if not isinstance(t_any, dict):
                            t_list = init_stmt.get("targets")
                            if isinstance(t_list, list) and len(t_list) > 0:
                                t_any = t_list[0]
                        if not isinstance(t_any, dict) or t_any.get("kind") != "Attribute":
                            continue
                        owner = t_any.get("value")
                        if not isinstance(owner, dict) or _safe_ident(owner.get("id"), "") not in {"self", "self_"}:
                            continue
                        attr_name = _safe_ident(t_any.get("attr"), "field")
                        if attr_name not in fields and attr_name not in late_fields and attr_name not in static_fields:
                            fields.append(attr_name)
                            self._emit_line("dynamic " + attr_name + ";")
        for sub in body:
            if sub.get("kind") not in {"FunctionDef", "ClosureDef"}:
                continue
            self._emit_class_method(cls_name, base_name, sub)
        if not has_init and len(fields) > 0:
            required_params: list[str] = []
            optional_params: list[str] = []
            for f in fields:
                if f in static_fields:
                    continue  # skip static fields from constructor
                if f in field_defaults:
                    optional_params.append("this." + f + " = " + field_defaults[f])
                else:
                    required_params.append("this." + f)
            if len(optional_params) == 0:
                params = ", ".join(required_params)
                self._emit_line(cls_name + "(" + params + ");")
            else:
                all_params = ", ".join(required_params + ["[" + ", ".join(optional_params) + "]"]) if len(required_params) > 0 else "[" + ", ".join(optional_params) + "]"
                self._emit_line(cls_name + "(" + all_params + ");")
        self.indent -= 1
        self._emit_line("}")
        self._emit_line("")
        self.current_class_is_trait = prev_trait

    def _emit_class_method(self, cls_name: str, base_name: str, stmt: dict[str, Any]) -> None:
        method_name = _safe_ident(stmt.get("name"), "method")
        decorators_any = stmt.get("decorators")
        decorators = decorators_any if isinstance(decorators_any, list) else []
        is_static = "staticmethod" in decorators
        arg_order_any = stmt.get("arg_order")
        arg_order = arg_order_any if isinstance(arg_order_any, list) else []
        vararg_name_any = stmt.get("vararg_name")
        if isinstance(vararg_name_any, str) and vararg_name_any.strip() != "":
            arg_order = list(arg_order) + [vararg_name_any]
        arg_defaults_any = stmt.get("arg_defaults")
        arg_defaults = arg_defaults_any if isinstance(arg_defaults_any, dict) else {}
        args: list[str] = []
        raw_args: list[str] = []
        for i_idx, arg in enumerate(arg_order):
            arg_name = _safe_ident(arg, "arg")
            if not is_static and i_idx == 0 and (arg_name == "self_" or arg_name == "self"):
                continue
            args.append(arg_name)
            raw_args.append(arg if isinstance(arg, str) else arg_name)
        prev_class = self.current_class_name
        prev_base = self.current_class_base_name
        prev_trait = self.current_class_is_trait
        self.current_class_name = cls_name
        self.current_class_base_name = base_name
        param_parts: list[str] = []
        optional_parts: list[str] = []
        for a_raw, a_safe in zip(raw_args, args):
            at = self._dart_arg_type(stmt, a_raw)
            if a_raw in arg_defaults:
                default_node = arg_defaults[a_raw]
                default_val = self._render_param_default_expr(default_node)
                optional_parts.append(at + " " + a_safe + " = " + default_val)
            else:
                param_parts.append(at + " " + a_safe)
        if len(optional_parts) > 0:
            params = ", ".join(param_parts + ["[" + ", ".join(optional_parts) + "]"]) if len(param_parts) > 0 else "[" + ", ".join(optional_parts) + "]"
        else:
            params = ", ".join(param_parts)
        static_prefix = "static " if is_static else ""
        if method_name == "__init__":
            super_args, body_stmts = self._extract_super_init(stmt.get("body"))
            header = cls_name + "(" + params + ")"
            if super_args is not None:
                header += " : super(" + ", ".join(super_args) + ")"
            self._emit_line(header + " {")
            self.indent += 1
            self._push_function_context(stmt, args, arg_order[1:] if len(arg_order) > 0 else arg_order)
            self._emit_block(body_stmts)
            self._pop_function_context()
            self.indent -= 1
            self._emit_line("}")
            self._emit_line("")
            self.current_class_name = prev_class
            self.current_class_base_name = prev_base
            self.current_class_is_trait = prev_trait
            return
        if method_name == "__str__":
            method_name = "toString"
        ret_type = self._dart_return_type(stmt)
        is_property = "property" in decorators
        if self.current_class_is_trait and len(self._dict_list(stmt.get("body"))) == 0:
            self._emit_line(ret_type + " " + method_name + "(" + params + ");")
            self._emit_line("")
            self.current_class_name = prev_class
            self.current_class_base_name = prev_base
            self.current_class_is_trait = prev_trait
            return
        if is_property:
            # @property → Dart getter
            self._emit_line(ret_type + " get " + method_name + " {")
            self.indent += 1
            self._push_function_context(stmt, args, arg_order[1:] if len(arg_order) > 0 else arg_order)
            self._emit_block(stmt.get("body"))
            self._pop_function_context()
            self.indent -= 1
            self._emit_line("}")
            self._emit_line("")
            self.current_class_name = prev_class
            self.current_class_base_name = prev_base
            self.current_class_is_trait = prev_trait
            return
        self._emit_line(static_prefix + ret_type + " " + method_name + "(" + params + ") {")
        self.indent += 1
        self._push_function_context(stmt, args, arg_order[1:] if len(arg_order) > 0 else arg_order)
        self._emit_block(stmt.get("body"))
        self._pop_function_context()
        self.indent -= 1
        self._emit_line("}")
        self._emit_line("")
        self.current_class_name = prev_class
        self.current_class_base_name = prev_base
        self.current_class_is_trait = prev_trait

    def _extract_super_init(self, body_any: Any) -> tuple[list[str] | None, list[dict[str, Any]]]:
        body = self._dict_list(body_any)
        if len(body) == 0:
            return None, body
        first = body[0]
        if first.get("kind") != "Expr":
            return None, body
        value_any = first.get("value")
        if not isinstance(value_any, dict) or value_any.get("kind") != "Call":
            return None, body
        func_any = value_any.get("func")
        if not isinstance(func_any, dict) or func_any.get("kind") != "Attribute":
            return None, body
        attr_name = func_any.get("attr") if isinstance(func_any.get("attr"), str) else ""
        if attr_name != "__init__":
            return None, body
        owner_any = func_any.get("value")
        if not isinstance(owner_any, dict) or owner_any.get("kind") != "Call":
            return None, body
        owner_func = owner_any.get("func")
        if not isinstance(owner_func, dict) or owner_func.get("kind") != "Name":
            return None, body
        owner_name = owner_func.get("id") if isinstance(owner_func.get("id"), str) else ""
        if owner_name not in {"super", "_super"}:
            return None, body
        args_any = value_any.get("args")
        args = args_any if isinstance(args_any, list) else []
        return [self._render_expr(arg) for arg in args], body[1:]

    def _for_needs_tmp_start(self, target_name: str, start_expr: str) -> bool:
        """Check if start expression references the target variable (shadowing risk)."""
        # Simple check: target_name appears as a word boundary in start_expr
        # e.g. start="y" target="y" → True
        if target_name == start_expr:
            return True
        # Check for target_name as substring with non-alnum boundaries
        i = 0
        while i < len(start_expr):
            pos = start_expr.find(target_name, i)
            if pos < 0:
                break
            end_pos = pos + len(target_name)
            left_ok = pos == 0 or not (start_expr[pos - 1].isalnum() or start_expr[pos - 1] == "_")
            right_ok = end_pos >= len(start_expr) or not (start_expr[end_pos].isalnum() or start_expr[end_pos] == "_")
            if left_ok and right_ok:
                return True
            i = pos + 1
        return False

    def _emit_for_core(self, stmt: dict[str, Any]) -> None:
        iter_mode = str(stmt.get("iter_mode"))
        target_plan = stmt.get("target_plan")
        target_name = "it"
        if isinstance(target_plan, dict) and target_plan.get("kind") == "NameTarget":
            target_name = _safe_ident(target_plan.get("id"), "it")
        if iter_mode == "static_fastpath":
            iter_plan = stmt.get("iter_plan")
            if not isinstance(iter_plan, dict):
                raise RuntimeError("lang=dart unsupported forcore static_fastpath shape")
            id2: dict[str, Any] = iter_plan
            if id2.get("kind") != "StaticRangeForPlan":
                raise RuntimeError("lang=dart unsupported forcore static_fastpath shape")
            start = self._render_expr(id2.get("start"))
            stop = self._render_expr(id2.get("stop"))
            step = self._render_expr(id2.get("step"))
            step_const = self._const_int_literal(id2.get("step"))
            range_mode = str(id2.get("range_mode") or "")
            if range_mode not in {"ascending", "descending", "dynamic"}:
                if isinstance(step_const, int):
                    if step_const > 0:
                        range_mode = "ascending"
                    elif step_const < 0:
                        range_mode = "descending"
                    else:
                        range_mode = "dynamic"
                else:
                    range_mode = "dynamic"
            if range_mode == "ascending":
                if self._for_needs_tmp_start(target_name, start):
                    tmp = self._next_tmp_name("__forStart")
                    self._emit_line("var " + tmp + " = " + start + ";")
                    self._emit_line("for (var " + target_name + " = " + tmp + "; " + target_name + " < " + stop + "; " + target_name + ("++" if step_const == 1 else " += " + step) + ") {")
                elif step_const == 1:
                    self._emit_line("for (var " + target_name + " = " + start + "; " + target_name + " < " + stop + "; " + target_name + "++) {")
                else:
                    self._emit_line("for (var " + target_name + " = " + start + "; " + target_name + " < " + stop + "; " + target_name + " += " + step + ") {")
                self.indent += 1
                self._emit_block(stmt.get("body"))
                self.indent -= 1
                self._emit_line("}")
                return
            if range_mode == "descending":
                if self._for_needs_tmp_start(target_name, start):
                    tmp = self._next_tmp_name("__forStart")
                    self._emit_line("var " + tmp + " = " + start + ";")
                    self._emit_line("for (var " + target_name + " = " + tmp + "; " + target_name + " > " + stop + "; " + target_name + " += " + step + ") {")
                else:
                    self._emit_line("for (var " + target_name + " = " + start + "; " + target_name + " > " + stop + "; " + target_name + " += " + step + ") {")
                self.indent += 1
                self._emit_block(stmt.get("body"))
                self.indent -= 1
                self._emit_line("}")
                return
            # Dynamic range mode
            start_tmp = self._next_tmp_name("__pytraRangeStart")
            stop_tmp = self._next_tmp_name("__pytraRangeStop")
            step_tmp = self._next_tmp_name("__pytraRangeStep")
            self._emit_line("var " + start_tmp + " = " + start + ";")
            self._emit_line("var " + stop_tmp + " = " + stop + ";")
            self._emit_line("var " + step_tmp + " = " + step + ";")
            self._emit_line("if (" + step_tmp + " > 0) {")
            self.indent += 1
            self._emit_line("for (var " + target_name + " = " + start_tmp + "; " + target_name + " < " + stop_tmp + "; " + target_name + " += " + step_tmp + ") {")
            self.indent += 1
            self._emit_block(stmt.get("body"))
            self.indent -= 1
            self._emit_line("}")
            self.indent -= 1
            self._emit_line("} else if (" + step_tmp + " < 0) {")
            self.indent += 1
            self._emit_line("for (var " + target_name + " = " + start_tmp + "; " + target_name + " > " + stop_tmp + "; " + target_name + " += " + step_tmp + ") {")
            self.indent += 1
            self._emit_block(stmt.get("body"))
            self.indent -= 1
            self._emit_line("}")
            self.indent -= 1
            self._emit_line("}")
            return
        if iter_mode == "runtime_protocol":
            iter_plan = stmt.get("iter_plan")
            if not isinstance(iter_plan, dict):
                raise RuntimeError("lang=dart unsupported forcore runtime shape")
            id_node: dict[str, Any] = iter_plan
            iter_expr_node = id_node.get("iter_expr")
            iter_expr = self._render_expr(iter_expr_node)
            # Dart String is not Iterable; convert to list of chars
            iter_type = self._lookup_expr_type(iter_expr_node)
            if iter_type == "str":
                iter_expr = iter_expr + ".split('')"
            tuple_target = isinstance(target_plan, dict) and target_plan.get("kind") == "TupleTarget"
            if tuple_target and isinstance(target_plan, dict):
                iter_name = self._next_tmp_name("__it")
                self._emit_line("for (var " + iter_name + " in " + iter_expr + ") {")
                self.indent += 1
                direct_names_any = target_plan.get("direct_unpack_names")
                direct_names = direct_names_any if isinstance(direct_names_any, list) else []
                if len(direct_names) > 0:
                    i = 0
                    while i < len(direct_names):
                        name_any = direct_names[i]
                        if isinstance(name_any, str) and name_any != "":
                            local_name = _safe_ident(name_any, "it")
                            self._emit_line("var " + local_name + " = " + iter_name + "[" + str(i) + "];")
                        i += 1
                else:
                    elems_any = target_plan.get("elements")
                    elems = elems_any if isinstance(elems_any, list) else []
                    i = 0
                    while i < len(elems):
                        elem = elems[i]
                        if isinstance(elem, dict) and elem.get("kind") == "NameTarget":
                            local_name = _safe_ident(elem.get("id"), "it")
                            self._emit_line("var " + local_name + " = " + iter_name + "[" + str(i) + "];")
                        i += 1
                self._emit_block(stmt.get("body"))
                self.indent -= 1
                self._emit_line("}")
                return
            self._emit_line("for (var " + target_name + " in " + iter_expr + ") {")
            self.indent += 1
            self._emit_block(stmt.get("body"))
            self.indent -= 1
            self._emit_line("}")
            return
        raise RuntimeError("lang=dart unsupported forcore iter_mode: " + iter_mode)

    def _emit_var_decl(self, stmt: dict[str, Any]) -> None:
        """Emit a hoisted variable declaration (VarDecl node)."""
        name_raw = stmt.get("name")
        name = _safe_ident(name_raw, "v") if isinstance(name_raw, str) else "v"
        var_type_any = stmt.get("type")
        var_type = var_type_any.strip() if isinstance(var_type_any, str) else ""
        dart_t = self._dart_type(var_type) if var_type != "" else "var"
        if var_type != "":
            self._current_type_map()[name] = var_type
        if len(self._local_var_stack) > 0:
            self._current_local_vars().add(name)
        if var_type in _NIL_FREE_DECL_TYPES:
            self._emit_line(dart_t + " " + name + ";")
        else:
            self._emit_line("late " + dart_t + " " + name + ";")

    def _emit_while(self, stmt: dict[str, Any]) -> None:
        test = self._render_cond_expr(stmt.get("test"))
        self._emit_line("while (" + test + ") {")
        self.indent += 1
        self._emit_block(stmt.get("body"))
        self.indent -= 1
        self._emit_line("}")

    def _next_tmp_name(self, prefix: str = "__pytraTmp") -> str:
        self.tmp_seq += 1
        return prefix + "_" + str(self.tmp_seq)

    def _emit_tuple_assign(self, tuple_target: dict[str, Any], value_any: Any) -> None:
        elems_any = tuple_target.get("elements")
        elems = elems_any if isinstance(elems_any, list) else []
        if len(elems) == 0:
            raise RuntimeError("lang=dart unsupported tuple assign target: empty")
        tmp_name = self._next_tmp_name("__pytraTuple")
        value_expr = self._render_expr(value_any)
        self._emit_line("var " + tmp_name + " = pytraTupleView(" + value_expr + ");")
        i = 0
        while i < len(elems):
            elem_any = elems[i]
            if isinstance(elem_any, dict):
                target_txt = self._render_target(elem_any)
                if (
                    isinstance(elem_any, dict)
                    and elem_any.get("kind") == "Name"
                    and len(self._local_var_stack) > 0
                ):
                    target_name = _safe_ident(elem_any.get("id"), "value")
                    if target_name not in self._current_local_vars():
                        self._current_local_vars().add(target_name)
                        self._emit_line("var " + target_txt + " = " + tmp_name + "[" + str(i) + "];")
                        i += 1
                        continue
                self._emit_line(target_txt + " = " + tmp_name + "[" + str(i) + "];")
            i += 1

    def _emit_swap(self, stmt: dict[str, Any]) -> None:
        left = self._render_target(stmt.get("left"))
        right = self._render_target(stmt.get("right"))
        tmp_name = self._next_tmp_name("__swap")
        self._emit_line("var " + tmp_name + " = " + left + ";")
        self._emit_line(left + " = " + right + ";")
        self._emit_line(right + " = " + tmp_name + ";")

    def _render_target(self, target_any: Any) -> str:
        if not isinstance(target_any, dict):
            return "null"
        tad: dict[str, Any] = target_any
        if tad.get("kind") == "Name":
            return _safe_ident(tad.get("id"), "value")
        if tad.get("kind") == "Attribute":
            owner = self._render_expr(tad.get("value"))
            attr = _safe_ident(tad.get("attr"), "field")
            return owner + "." + attr
        if tad.get("kind") == "Subscript":
            owner = self._render_expr(tad.get("value"))
            index_node = tad.get("slice")
            if isinstance(index_node, dict):
                ind: dict[str, Any] = index_node
                if ind.get("kind") == "Slice":
                    raise RuntimeError("lang=dart unsupported slice assignment target")
            index = self._render_expr(index_node)
            return owner + "[" + index + "]"
        target_kind = tad.get("kind")
        raise RuntimeError("lang=dart unsupported assignment target: " + str(target_kind))

    def _render_expr(self, expr_any: Any) -> str:
        if not isinstance(expr_any, dict):
            return "null"
        ed: dict[str, Any] = expr_any
        kind = ed.get("kind")
        if kind == "Constant":
            return self._render_constant(ed.get("value"))
        if kind == "Name":
            return self._render_name_expr(expr_any)
        if kind == "BinOp":
            left_node = ed.get("left")
            right_node = ed.get("right")
            left = self._render_expr(left_node)
            right = self._render_expr(right_node)
            op_raw = str(ed.get("op"))
            op = _binop_symbol(op_raw)
            if op_raw == "Mult" and (self._is_sequence_expr(left_node) or self._is_sequence_expr(right_node)):
                return "pytraRepeatSeq(" + left + ", " + right + ")"
            # List + List → use spread to avoid Dart type mismatch (List<int> + List<dynamic>)
            if op_raw == "Add" and (self._is_list_expr(left_node) or self._is_list_expr(right_node)):
                return "[..." + left + ", ..." + right + "]"
            return "(" + left + " " + op + " " + right + ")"
        if kind == "UnaryOp":
            operand = self._render_expr(ed.get("operand"))
            op = str(ed.get("op"))
            if op == "USub":
                return "(-" + operand + ")"
            if op == "UAdd":
                return "(+" + operand + ")"
            if op == "Invert":
                return "(~" + operand + ")"
            if op == "Not":
                return "(!" + operand + ")"
            return operand
        if kind == "Compare":
            ops = ed.get("ops")
            comps = ed.get("comparators")
            if not isinstance(ops, list) or not isinstance(comps, list) or len(ops) == 0 or len(comps) == 0:
                return "false"
            left_node = ed.get("left")
            right_node = comps[0]
            left = self._render_expr(left_node)
            right = self._render_expr(right_node)
            op0 = str(ops[0])
            if op0 == "In":
                return "pytraContains(" + right + ", " + left + ")"
            if op0 == "NotIn":
                return "(!pytraContains(" + right + ", " + left + "))"
            if op0 == "Is":
                return "(" + left + " == " + right + ")"
            if op0 == "IsNot":
                return "(" + left + " != " + right + ")"
            # String relational comparison: use compareTo() since Dart String lacks <, <=, >, >=
            if op0 in {"Lt", "LtE", "Gt", "GtE"}:
                left_t = self._lookup_expr_type(left_node)
                right_t = self._lookup_expr_type(right_node)
                if left_t == "str" or right_t == "str":
                    sym = _cmp_symbol(op0)
                    return "(" + left + ".compareTo(" + right + ") " + sym + " 0)"
            return "(" + left + " " + _cmp_symbol(op0) + " " + right + ")"
        if kind == "BoolOp":
            values_any = ed.get("values")
            values = values_any if isinstance(values_any, list) else []
            if len(values) == 0:
                return "false"
            op = str(ed.get("op"))
            # If any operand is non-bool, Python or/and returns the value itself.
            # Use pytraOr/pytraAnd runtime helpers that implement Python semantics.
            def _is_bool_type(n: dict) -> bool:
                rt = n.get("resolved_type", "")
                return rt in {"bool", ""}
            any_nonbool = any(not _is_bool_type(v) for v in values if isinstance(v, dict))
            if any_nonbool:
                fn = "pytraAnd" if op == "And" else "pytraOr"
                # Fold pairwise: pytraOr(a, pytraOr(b, c))
                rendered = [self._render_expr(v) for v in values]
                result = rendered[0]
                for r in rendered[1:]:
                    result = fn + "(" + result + ", " + r + ")"
                return result
            delim = " && " if op == "And" else " || "
            out: list[str] = []
            for v in values:
                out.append(self._render_cond_expr(v))
            return "(" + delim.join(out) + ")"
        if kind == "Call":
            return self._render_call(expr_any)
        if kind == "Lambda":
            args_any = ed.get("args")
            args = args_any if isinstance(args_any, list) else []
            if len(args) == 0 and isinstance(args_any, dict):
                nested_args_any = args_any.get("args")
                args = nested_args_any if isinstance(nested_args_any, list) else []
            required_params: list[str] = []
            optional_params: list[str] = []
            for arg_any in args:
                if not isinstance(arg_any, dict):
                    continue
                nm = _safe_ident(arg_any.get("arg"), "arg")
                default_node = arg_any.get("default")
                if isinstance(default_node, dict):
                    optional_params.append(nm + " = " + self._render_expr(default_node))
                else:
                    required_params.append(nm)
            all_params = required_params
            if optional_params:
                all_params = required_params + ["[" + ", ".join(optional_params) + "]"]
            body = self._render_expr(ed.get("body"))
            return "(" + ", ".join(all_params) + ") => " + body
        if kind == "List":
            elems_any = ed.get("elements")
            elems = elems_any if isinstance(elems_any, list) else []
            out: list[str] = []
            for e in elems:
                out.append(self._render_expr(e))
            return "[" + ", ".join(out) + "]"
        if kind == "Tuple":
            elems_any = ed.get("elements")
            elems = elems_any if isinstance(elems_any, list) else []
            out: list[str] = []
            for e in elems:
                out.append(self._render_expr(e))
            return "[" + ", ".join(out) + "]"
        if kind == "Set":
            elems_any = ed.get("elements")
            elems = elems_any if isinstance(elems_any, list) else []
            out: list[str] = []
            for e in elems:
                out.append(self._render_expr(e))
            return "pytraSetLiteral([" + ", ".join(out) + "])"
        if kind == "ListComp":
            return self._render_list_comp(ed)
        if kind == "SetComp":
            return self._render_set_comp(ed)
        if kind == "DictComp":
            return self._render_dict_comp(ed)
        if kind == "Dict":
            keys_any = ed.get("keys")
            values_any = ed.get("values")
            keys = keys_any if isinstance(keys_any, list) else []
            values = values_any if isinstance(values_any, list) else []
            if len(keys) == 0 or len(values) == 0:
                entries_any = ed.get("entries")
                entries = entries_any if isinstance(entries_any, list) else []
                if len(entries) == 0:
                    return "{}"
                pairs_from_entries: list[str] = []
                i = 0
                while i < len(entries):
                    ent = entries[i]
                    if isinstance(ent, dict):
                        ed2: dict[str, Any] = ent
                        k = self._render_expr(ed2.get("key"))
                        v = self._render_expr(ed2.get("value"))
                        pairs_from_entries.append(k + ": " + v)
                    i += 1
                if len(pairs_from_entries) == 0:
                    return "{}"
                return "{" + ", ".join(pairs_from_entries) + "}"
            pairs: list[str] = []
            i = 0
            while i < len(keys) and i < len(values):
                k = self._render_expr(keys[i])
                v = self._render_expr(values[i])
                pairs.append(k + ": " + v)
                i += 1
            return "{" + ", ".join(pairs) + "}"
        if kind == "Subscript":
            owner = self._render_expr(ed.get("value"))
            index_node = ed.get("slice")
            owner_node = ed.get("value")
            owner_type = self._lookup_expr_type(owner_node) if isinstance(owner_node, dict) else ""
            if isinstance(index_node, dict) and index_node.get("kind") == "Slice":
                lower_node = index_node.get("lower")
                upper_node = index_node.get("upper")
                lower = self._render_expr(lower_node) if isinstance(lower_node, dict) else "0"
                upper = self._render_expr(upper_node) if isinstance(upper_node, dict) else "null"
                if owner_type == "str":
                    if upper == "null":
                        return "pytraStrSlice(" + owner + ", " + lower + ", null)"
                    return "pytraStrSlice(" + owner + ", " + lower + ", " + upper + ")"
                if upper == "null":
                    return "pytraSlice(" + owner + ", " + lower + ", null)"
                return "pytraSlice(" + owner + ", " + lower + ", " + upper + ")"
            index = self._render_expr(index_node)
            # Dict subscript: no negative index adjustment
            if owner_type.startswith("dict["):
                return owner + "[" + index + "]"
            # If index is clearly non-numeric (string key), use direct access
            index_type = self._lookup_expr_type(index_node)
            if index_type == "str":
                return owner + "[" + index + "]"
            return "pytraIndex(" + owner + ", " + index + ")"
        if kind == "Attribute":
            attr_raw = ed.get("attr") if isinstance(ed.get("attr"), str) else ""
            # type(x).__name__ → x.runtimeType.toString()
            owner_node = ed.get("value")
            if isinstance(owner_node, dict) and owner_node.get("kind") == "Name":
                owner_name = _safe_ident(owner_node.get("id"), "")
                if owner_name == "env" and attr_raw == "target":
                    return '"dart"'
            if attr_raw == "__name__" and isinstance(owner_node, dict) and owner_node.get("kind") == "Call":
                fn = owner_node.get("func")
                if isinstance(fn, dict) and fn.get("kind") == "Name" and fn.get("id") == "type":
                    args_any = owner_node.get("args")
                    args = args_any if isinstance(args_any, list) else []
                    if len(args) == 1:
                        return "(" + self._render_expr(args[0]) + ").runtimeType.toString()"
            owner = self._render_expr(owner_node)
            attr = _safe_ident(attr_raw, "field")
            return owner + "." + attr
        if kind == "IsInstance":
            value = self._render_expr(ed.get("value"))
            expected_any = ed.get("expected_type_id")
            expected = ""
            expected_name_any = ed.get("expected_type_name")
            if isinstance(expected_name_any, str) and expected_name_any != "":
                expected = expected_name_any
            if isinstance(expected_any, dict) and expected_any.get("kind") == "Name":
                expected_raw = expected_any.get("id")
                if expected == "":
                    expected = expected_raw if isinstance(expected_raw, str) and expected_raw != "" else "object"
            if expected in {"int", "int64", "PYTRA_TID_INT"}:
                return "(" + value + " is int)"
            if expected in {"float", "float64", "PYTRA_TID_FLOAT"}:
                return "(" + value + " is double)"
            if expected in {"str", "string", "PYTRA_TID_STR"}:
                return "(" + value + " is String)"
            if expected in {"bool", "PYTRA_TID_BOOL"}:
                return "(" + value + " is bool)"
            if expected in {"list", "PYTRA_TID_LIST"}:
                return "(" + value + " is List)"
            if expected in {"dict", "PYTRA_TID_DICT"}:
                return "(" + value + " is Map)"
            if expected in {"set_"}:
                return "(" + value + " is Set)"
            if expected in {"tuple"}:
                return "(" + value + " is List)"
            if expected in self.class_names:
                return "(" + value + " is " + expected + ")"
            return "false"
        if kind == "IsSubtype" or kind == "IsSubclass":
            return "false"
        if kind == "IfExp":
            test = self._render_expr(ed.get("test"))
            body = self._render_expr(ed.get("body"))
            orelse = self._render_expr(ed.get("orelse"))
            return "(pytraTruthy(" + test + ") ? (" + body + ") : (" + orelse + "))"
        if kind == "JoinedStr":
            values_any = ed.get("values")
            values = values_any if isinstance(values_any, list) else []
            if len(values) == 0:
                return "''"
            parts: list[str] = []
            for item in values:
                item_d = item if isinstance(item, dict) else {}
                item_kind = item_d.get("kind")
                if item_kind == "Constant" and isinstance(item_d.get("value"), str):
                    parts.append(self._render_expr(item_d))
                elif item_kind == "FormattedValue":
                    fmt_spec = item_d.get("format_spec")
                    val_expr = self._render_expr(item_d.get("value"))
                    parts.append(self._render_format_spec(val_expr, fmt_spec))
                else:
                    parts.append("(" + self._render_expr(item_d) + ").toString()")
            return "(" + " + ".join(parts) + ")"
        if kind == "Box":
            return self._render_expr(ed.get("value"))
        if kind == "Unbox":
            return self._render_expr(ed.get("value"))
        if kind == "ObjTypeId":
            return "null /* obj_type_id */"
        if kind == "ObjStr":
            return "(" + self._render_expr(ed.get("value")) + ").toString()"
        if kind == "ObjBool":
            val = self._render_expr(ed.get("value"))
            return "pytraTruthy(" + val + ")"
        if kind == "ObjLen":
            return "(" + self._render_expr(ed.get("value")) + ").length"
        raise RuntimeError("lang=dart unsupported expr kind: " + str(kind))

    def _render_call(self, expr: dict[str, Any]) -> str:
        func_any = expr.get("func")
        args_any = expr.get("args")
        args = args_any if isinstance(args_any, list) else []
        keywords_any = expr.get("keywords")
        keywords = keywords_any if isinstance(keywords_any, list) else []
        rendered_args: list[str] = []
        for arg in args:
            rendered_args.append(self._render_expr(arg))
        kw_rendered: dict[str, str] = {}
        kw_values_in_order: list[str] = []
        for kw_any in keywords:
            if not isinstance(kw_any, dict):
                continue
            key_any = kw_any.get("arg")
            if not isinstance(key_any, str) or key_any == "":
                continue
            rendered_kw = self._render_expr(kw_any.get("value"))
            kw_rendered[key_any] = rendered_kw
            kw_values_in_order.append(rendered_kw)
        semantic_tag_any = expr.get("semantic_tag")
        semantic_tag = semantic_tag_any if isinstance(semantic_tag_any, str) else ""
        runtime_call = self._resolved_runtime_call(expr)
        if semantic_tag.startswith("stdlib.") and semantic_tag != "stdlib.symbol.Path" and runtime_call == "":
            raise RuntimeError("lang=dart unresolved stdlib runtime call: " + semantic_tag)
        if isinstance(func_any, dict) and func_any.get("kind") == "Name":
            raw_fn_name = func_any.get("id") if isinstance(func_any.get("id"), str) else ""
            fn_name = _safe_ident(raw_fn_name, "fn")
            if raw_fn_name == "cast":
                # cast(Type, value) → (value as Type)
                if len(rendered_args) >= 2:
                    # First arg is the type — get the raw type name from the EAST node
                    type_arg = args[0] if len(args) > 0 else None
                    type_name = ""
                    if isinstance(type_arg, dict) and type_arg.get("kind") == "Name":
                        type_name = type_arg.get("id", "")
                    dart_type = self._dart_type(type_name) if type_name != "" else "dynamic"
                    if dart_type == "dynamic":
                        return rendered_args[1]
                    return "(" + rendered_args[1] + " as " + dart_type + ")"
                if len(rendered_args) == 1:
                    return rendered_args[0]
                return "null"
            if raw_fn_name == "print":
                return "pytraPrint([" + ", ".join(rendered_args) + "])"
            if raw_fn_name == "int":
                if len(rendered_args) == 0:
                    return "0"
                return "pytraInt(" + rendered_args[0] + ")"
            if raw_fn_name == "float":
                if len(rendered_args) == 0:
                    return "0.0"
                return "pytraFloat(" + rendered_args[0] + ")"
            if raw_fn_name == "bool":
                if len(rendered_args) == 0:
                    return "false"
                return "pytraTruthy(" + rendered_args[0] + ")"
            if raw_fn_name == "str" or raw_fn_name == "py_to_string":
                if len(rendered_args) == 0:
                    return "''"
                arg0 = args[0] if len(args) > 0 else None
                if isinstance(arg0, dict):
                    arg_type = self._lookup_expr_type(arg0)
                    if arg0.get("kind") == "Tuple" or arg_type.startswith("tuple["):
                        return "pytraTupleStr(pytraTupleView(" + rendered_args[0] + "))"
                return "pytraStr(" + rendered_args[0] + ")"
            if raw_fn_name == "len":
                if len(rendered_args) == 0:
                    return "0"
                return "(" + rendered_args[0] + ").length"
            if raw_fn_name == "max":
                self._needs_math_import = True
                if len(rendered_args) == 0:
                    return "0"
                if len(rendered_args) == 2:
                    return "((" + rendered_args[0] + ") > (" + rendered_args[1] + ") ? (" + rendered_args[0] + ") : (" + rendered_args[1] + "))"
                return "[" + ", ".join(rendered_args) + "].reduce((a, b) => a > b ? a : b)"
            if raw_fn_name == "min":
                self._needs_math_import = True
                if len(rendered_args) == 0:
                    return "0"
                if len(rendered_args) == 2:
                    return "((" + rendered_args[0] + ") < (" + rendered_args[1] + ") ? (" + rendered_args[0] + ") : (" + rendered_args[1] + "))"
                return "[" + ", ".join(rendered_args) + "].reduce((a, b) => a < b ? a : b)"
            if raw_fn_name == "abs":
                if len(rendered_args) == 0:
                    return "0"
                return "(" + rendered_args[0] + ").abs()"
            if raw_fn_name == "sum":
                if len(rendered_args) == 0:
                    return "0"
                return "((" + rendered_args[0] + ").fold<num>(0, (a, b) => a + (b as num)))"
            if raw_fn_name == "enumerate":
                if len(rendered_args) == 0:
                    return "[]"
                return "(" + rendered_args[0] + ").asMap().entries.map((e) => [e.key, e.value]).toList()"
            if raw_fn_name == "sorted":
                if len(rendered_args) == 0:
                    return "[]"
                return "(List.from(" + rendered_args[0] + ")..sort())"
            if raw_fn_name == "reversed":
                if len(rendered_args) == 0:
                    return "[]"
                return "(" + rendered_args[0] + ").reversed.toList()"
            if raw_fn_name == "zip":
                if len(rendered_args) < 2:
                    return "[]"
                return "pytraZip(" + ", ".join(rendered_args) + ")"
            if raw_fn_name == "range":
                if len(rendered_args) == 1:
                    return "List.generate(" + rendered_args[0] + ", (i) => i)"
                if len(rendered_args) == 2:
                    return "List.generate((" + rendered_args[1] + ") - (" + rendered_args[0] + "), (i) => i + (" + rendered_args[0] + "))"
                return "List.generate(((" + rendered_args[1] + ") - (" + rendered_args[0] + ")) ~/ (" + rendered_args[2] + "), (i) => (" + rendered_args[0] + ") + i * (" + rendered_args[2] + "))"
            if raw_fn_name == "set" or raw_fn_name == "set_":
                if len(rendered_args) == 0:
                    return "pytraNewSet()"
                return "pytraSetFrom(" + rendered_args[0] + ")"
            if raw_fn_name == "list":
                if len(rendered_args) == 0:
                    return "[]"
                return "List<dynamic>.from(" + rendered_args[0] + ")"
            if raw_fn_name == "dict":
                if len(rendered_args) == 0:
                    return "{}"
                return "Map<dynamic, dynamic>.from(" + rendered_args[0] + ")"
            if raw_fn_name == "tuple":
                if len(rendered_args) == 0:
                    return "[]"
                return "List<dynamic>.from(" + rendered_args[0] + ")"
            if raw_fn_name == "chr":
                if len(rendered_args) == 0:
                    return "''"
                return "String.fromCharCode(" + rendered_args[0] + ")"
            if raw_fn_name == "ord":
                if len(rendered_args) == 0:
                    return "0"
                return "(" + rendered_args[0] + ").codeUnitAt(0)"
            if raw_fn_name == "bytearray":
                if len(rendered_args) == 0:
                    return "<int>[]"
                return "pytraBytearray(" + rendered_args[0] + ")"
            if raw_fn_name == "bytes":
                if len(rendered_args) == 0:
                    return "<int>[]"
                return "pytraBytes(" + rendered_args[0] + ")"
            mapped_name = self._mapping.calls.get(raw_fn_name, "")
            mapped_expr = self._expand_mapped_call(mapped_name, rendered_args)
            if mapped_expr != "":
                return mapped_expr
            if fn_name in self.class_names:
                return fn_name + "(" + ", ".join(rendered_args + kw_values_in_order) + ")"
            # Use alias if calling a top-level function that conflicts with a class method name
            if fn_name in self._toplevel_fn_conflicts and fn_name in self.function_names:
                return "_pytra_top_" + fn_name + "(" + ", ".join(rendered_args + kw_values_in_order) + ")"
            rendered_name = self._render_name_expr(func_any)
            return rendered_name + "(" + ", ".join(rendered_args + kw_values_in_order) + ")"
        if isinstance(func_any, dict) and func_any.get("kind") == "Attribute":
            owner_node = func_any.get("value")
            raw_attr = func_any.get("attr") if isinstance(func_any.get("attr"), str) else ""
            attr = _safe_ident(raw_attr, "call")
            if isinstance(owner_node, dict) and owner_node.get("kind") == "Call":
                super_func = owner_node.get("func")
                if isinstance(super_func, dict) and super_func.get("kind") == "Name":
                    super_name = str(super_func.get("id"))
                    if super_name in {"super", "_super"}:
                        if attr == "__init__":
                            return "/* super().__init__() */"
                        if self.current_class_base_name != "":
                            return "super." + attr + "(" + ", ".join(rendered_args) + ")"
            module_alias = self._resolve_module_owner_alias(owner_node)
            runtime_module_id = expr.get("runtime_module_id") if isinstance(expr.get("runtime_module_id"), str) else ""
            if runtime_module_id == "" and isinstance(owner_node, dict) and owner_node.get("kind") == "Attribute":
                runtime_module_id = self._resolve_module_attr_module_id(owner_node)
            if module_alias == "" and runtime_module_id != "" and self._is_module_owner_node(owner_node):
                module_alias = self._module_aliases.get(canonical_runtime_module_id(runtime_module_id), "")
            mapped_name = self._lookup_mapped_call(runtime_module_id, raw_attr)
            mapped_expr = self._expand_mapped_call(mapped_name, rendered_args)
            if mapped_expr != "":
                return mapped_expr
            if module_alias != "":
                return module_alias + "." + attr + "(" + ", ".join(rendered_args + kw_values_in_order) + ")"
            owner = self._render_expr(owner_node)
            owner_type = self._lookup_expr_type(owner_node)
            if isinstance(owner_node, dict) and owner_node.get("kind") == "Name":
                owner_name = _safe_ident(owner_node.get("id"), "")
                if owner_name in self.imported_modules:
                    return owner + "." + attr + "(" + ", ".join(rendered_args + kw_values_in_order) + ")"
            # String methods
            if owner_type == "str" or attr in {
                "isdigit",
                "isalpha",
                "isalnum",
                "isspace",
                "strip",
                "lstrip",
                "rstrip",
                "startswith",
                "endswith",
                "find",
                "rfind",
                "replace",
                "split",
                "splitlines",
                "upper",
                "lower",
            }:
                if attr == "isdigit":
                    return "pytraStrIsdigit(" + owner + ")"
                if attr == "isalpha":
                    return "pytraStrIsalpha(" + owner + ")"
                if attr == "isalnum":
                    return "pytraStrIsalnum(" + owner + ")"
                if attr == "isspace":
                    return "pytraStrIsspace(" + owner + ")"
                if attr == "strip":
                    return owner + ".trim()"
                if attr == "lstrip":
                    return owner + ".trimLeft()"
                if attr == "rstrip":
                    return owner + ".trimRight()"
                if attr == "startswith" and len(rendered_args) >= 1:
                    return owner + ".startsWith(" + rendered_args[0] + ")"
                if attr == "endswith" and len(rendered_args) >= 1:
                    return owner + ".endsWith(" + rendered_args[0] + ")"
                if attr == "join" and len(rendered_args) >= 1:
                    return "(" + rendered_args[0] + ").join(" + owner + ")"
                if attr == "find" and len(rendered_args) >= 1:
                    return owner + ".indexOf(" + rendered_args[0] + ")"
                if attr == "rfind" and len(rendered_args) >= 1:
                    return owner + ".lastIndexOf(" + rendered_args[0] + ")"
                if attr == "count" and len(rendered_args) >= 1:
                    return "pytraStrCount(" + owner + ", " + rendered_args[0] + ")"
                if attr == "index" and len(rendered_args) >= 1:
                    return "pytraStrIndex(" + owner + ", " + rendered_args[0] + ")"
                if attr == "replace" and len(rendered_args) >= 2:
                    return owner + ".replaceAll(" + rendered_args[0] + ", " + rendered_args[1] + ")"
                if attr == "split":
                    sep = rendered_args[0] if len(rendered_args) >= 1 else "' '"
                    return owner + ".split(" + sep + ")"
                if attr == "splitlines":
                    return owner + ".split('\\n')"
                if attr == "upper":
                    return owner + ".toUpperCase()"
                if attr == "lower":
                    return owner + ".toLowerCase()"
            # List methods
            is_list_like = owner_type.startswith("list[") or owner_type in ("list", "bytes", "bytearray")
            if is_list_like:
                if attr == "append" and len(rendered_args) == 1:
                    return owner + ".add(" + rendered_args[0] + ")"
                if attr == "extend" and len(rendered_args) == 1:
                    return owner + ".addAll(" + self._coerce_iterable_arg(owner_type, rendered_args[0]) + ")"
                if attr == "pop":
                    if len(rendered_args) == 0:
                        return owner + ".removeLast()"
                    return owner + ".removeAt(" + rendered_args[0] + ")"
                if attr == "insert" and len(rendered_args) == 2:
                    return owner + ".insert(" + rendered_args[0] + ", " + rendered_args[1] + ")"
                if attr == "remove" and len(rendered_args) == 1:
                    return owner + ".remove(" + rendered_args[0] + ")"
                if attr == "index" and len(rendered_args) >= 1:
                    return owner + ".indexOf(" + rendered_args[0] + ")"
                if attr == "sort":
                    return owner + ".sort()"
                if attr == "reverse":
                    return "(" + owner + " = " + owner + ".reversed.toList())"
                if attr == "copy":
                    return "List.from(" + owner + ")"
            if owner_type == "deque":
                if attr == "append" and len(rendered_args) == 1:
                    return owner + ".add(" + rendered_args[0] + ")"
                if attr == "appendleft" and len(rendered_args) == 1:
                    return owner + ".appendleft(" + rendered_args[0] + ")"
                if attr == "popleft" and len(rendered_args) == 0:
                    return owner + ".popleft()"
                if attr == "pop" and len(rendered_args) == 0:
                    return owner + ".removeLast()"
                if attr == "clear" and len(rendered_args) == 0:
                    return owner + ".clear()"
            if owner_type.startswith("set[") or owner_type == "set":
                if attr == "discard" and len(rendered_args) == 1:
                    return owner + ".remove(" + rendered_args[0] + ")"
                if attr == "add" and len(rendered_args) == 1:
                    return owner + ".add(" + rendered_args[0] + ")"
            # Dict methods
            if raw_attr == "get":
                key = rendered_args[0] if len(rendered_args) >= 1 else "null"
                default = rendered_args[1] if len(rendered_args) >= 2 else "null"
                return "(" + owner + "[" + key + "] ?? " + default + ")"
            if attr == "keys":
                return owner + ".keys.toList()"
            if attr == "values":
                return owner + ".values.toList()"
            if attr == "items":
                return "((" + owner + ") as Map).entries.map((e) => [e.key, e.value]).toList()"
            if attr == "update" and len(rendered_args) == 1:
                return owner + ".addAll(" + self._coerce_iterable_arg(owner_type, rendered_args[0]) + ")"
            if attr == "pop" and len(rendered_args) >= 1:
                return owner + ".remove(" + rendered_args[0] + ")!"
            if attr == "setdefault" and len(rendered_args) >= 2:
                return owner + ".putIfAbsent(" + rendered_args[0] + ", () => " + rendered_args[1] + ")"
            return owner + "." + attr + "(" + ", ".join(rendered_args + kw_values_in_order) + ")"
        # Lambda immediate call: (lambda x: body)(arg) → ((x) => body)(arg)
        if isinstance(func_any, dict) and func_any.get("kind") == "Lambda":
            lambda_expr = self._render_expr(func_any)
            return "(" + lambda_expr + ")(" + ", ".join(rendered_args) + ")"
        # Fallback: render func expression and call it
        func_expr = self._render_expr(func_any)
        return func_expr + "(" + ", ".join(rendered_args + kw_values_in_order) + ")"

    def _render_list_comp(self, ed: dict[str, Any]) -> str:
        gens_any = ed.get("generators")
        gens = gens_any if isinstance(gens_any, list) else []
        if len(gens) == 0 or not isinstance(gens[0], dict):
            return "[]"
        gen = gens[0]
        target_any = gen.get("target")
        iter_any = gen.get("iter")
        if not isinstance(target_any, dict) or not isinstance(iter_any, dict):
            return "[]"
        td: dict[str, Any] = target_any
        elt = self._render_expr(ed.get("elt"))
        # Collect condition
        cond_expr = ""
        ifs_any = gen.get("ifs")
        if isinstance(ifs_any, list) and len(ifs_any) > 0:
            cond_parts: list[str] = []
            for cond_any in ifs_any:
                cond_parts.append(self._render_expr(cond_any))
            cond_expr = " && ".join(cond_parts)
        id_node: dict[str, Any] = iter_any
        if id_node.get("kind") == "RangeExpr":
            loop_var = _safe_ident(td.get("id"), "__lc_i") if td.get("kind") == "Name" else "__lc_i"
            start = self._render_expr(id_node.get("start"))
            stop = self._render_expr(id_node.get("stop"))
            step = self._render_expr(id_node.get("step"))
            step_const = self._const_int_literal(id_node.get("step"))
            insert_stmt = "__out.add(" + elt + ");"
            if cond_expr != "":
                insert_stmt = "if (" + cond_expr + ") { " + insert_stmt + " }"
            if step_const == 1:
                return (
                    "(() { var __out = []; for (var " + loop_var + " = " + start
                    + "; " + loop_var + " < " + stop + "; " + loop_var + "++) { "
                    + insert_stmt + " } return __out; })()"
                )
            return (
                "(() { var __out = []; for (var " + loop_var + " = " + start
                + "; " + loop_var + " < " + stop + "; " + loop_var + " += " + step + ") { "
                + insert_stmt + " } return __out; })()"
            )
        # General iterable comprehension
        iter_expr = self._render_expr(iter_any)
        # String iteration: wrap with .split('') for Dart
        iter_type = self._lookup_expr_type(iter_any)
        if iter_type == "str" or (isinstance(iter_any, dict) and iter_any.get("resolved_type") == "str"):
            iter_expr = iter_expr + ".split('')"
        insert_stmt = "__out.add(" + elt + ");"
        if cond_expr != "":
            insert_stmt = "if (" + cond_expr + ") { " + insert_stmt + " }"
        if td.get("kind") == "Tuple":
            # Tuple unpacking: for wi, xi in zip(...) → for (var __lc_i in ...) { var wi = __lc_i[0]; var xi = __lc_i[1]; ... }
            elems_any = td.get("elements")
            elems = elems_any if isinstance(elems_any, list) else []
            unpack = " ".join(
                "var " + _safe_ident(e.get("id"), "__lc_e" + str(i)) + " = __lc_i[" + str(i) + "];"
                for i, e in enumerate(elems) if isinstance(e, dict) and e.get("kind") == "Name"
            )
            return (
                "(() { var __out = []; for (var __lc_i in " + iter_expr + ") { "
                + unpack + " " + insert_stmt + " } return __out; })()"
            )
        loop_var = _safe_ident(td.get("id"), "__lc_i")
        return (
            "(() { var __out = []; for (var " + loop_var + " in " + iter_expr + ") { "
            + insert_stmt + " } return __out; })()"
        )

    def _render_except_handler_type(self, type_any: Any) -> str:
        if not isinstance(type_any, dict):
            return ""
        kind = type_any.get("kind")
        if kind == "Name":
            return _safe_ident(type_any.get("id"), "")
        if kind == "Attribute":
            return self._render_expr(type_any)
        resolved = type_any.get("resolved_type")
        if isinstance(resolved, str) and resolved != "":
            return self._dart_type(resolved)
        return ""

    def _render_param_default_expr(self, default_any: Any) -> str:
        if not isinstance(default_any, dict):
            return "null"
        kind = default_any.get("kind")
        if kind == "List":
            elems_any = default_any.get("elements")
            elems = elems_any if isinstance(elems_any, list) else []
            rendered = [self._render_expr(elem) for elem in elems]
            return "const [" + ", ".join(rendered) + "]"
        if kind == "Tuple":
            elems_any = default_any.get("elements")
            elems = elems_any if isinstance(elems_any, list) else []
            rendered = [self._render_expr(elem) for elem in elems]
            return "const [" + ", ".join(rendered) + "]"
        if kind == "Dict":
            keys_any = default_any.get("keys")
            values_any = default_any.get("values")
            keys = keys_any if isinstance(keys_any, list) else []
            values = values_any if isinstance(values_any, list) else []
            pairs: list[str] = []
            i = 0
            while i < len(keys) and i < len(values):
                pairs.append(self._render_expr(keys[i]) + ": " + self._render_expr(values[i]))
                i += 1
            return "const {" + ", ".join(pairs) + "}"
        if kind == "Set":
            elems_any = default_any.get("elements")
            elems = elems_any if isinstance(elems_any, list) else []
            rendered = [self._render_expr(elem) for elem in elems]
            return "const {" + ", ".join(rendered) + "}"
        return self._render_expr(default_any)

    def _coerce_assignment_expr(self, target_any: Any, value_expr: str) -> str:
        if not isinstance(target_any, dict):
            return value_expr
        if target_any.get("kind") == "Attribute":
            owner_any = target_any.get("value")
            if isinstance(owner_any, dict) and owner_any.get("kind") == "Name":
                owner_name = _safe_ident(owner_any.get("id"), "")
                if owner_name in {"self", "self_"} and self.current_class_name != "":
                    field_name = _safe_ident(target_any.get("attr"), "field")
                    field_types = self._class_field_types.get(self.current_class_name, {})
                    field_type = field_types.get(field_name, "")
                    dart_t = self._dart_type(field_type) if field_type != "" else ""
                    if dart_t.startswith("List<"):
                        return dart_t + ".from(" + value_expr + ")"
                    if dart_t.startswith("Map<"):
                        return dart_t + ".from(" + value_expr + ")"
                    if dart_t.startswith("Set<"):
                        return dart_t + ".from(" + value_expr + ")"
        return value_expr

    def _coerce_iterable_arg(self, owner_type: str, value_expr: str) -> str:
        dart_t = self._dart_type(owner_type) if owner_type != "" else ""
        if dart_t.startswith("List<"):
            return dart_t + ".from(" + value_expr + ")"
        if dart_t.startswith("Set<"):
            return dart_t + ".from(" + value_expr + ")"
        if dart_t.startswith("Map<"):
            return dart_t + ".from(" + value_expr + ")"
        return value_expr

    def _render_set_comp(self, ed: dict[str, Any]) -> str:
        gens_any = ed.get("generators")
        gens = gens_any if isinstance(gens_any, list) else []
        if len(gens) == 0 or not isinstance(gens[0], dict):
            return "pytraNewSet()"
        gen = gens[0]
        target_any = gen.get("target")
        iter_any = gen.get("iter")
        if not isinstance(target_any, dict) or not isinstance(iter_any, dict):
            return "pytraNewSet()"
        td: dict[str, Any] = target_any
        elt = self._render_expr(ed.get("elt"))
        cond_expr = ""
        ifs_any = gen.get("ifs")
        if isinstance(ifs_any, list) and len(ifs_any) > 0:
            cond_parts: list[str] = []
            for cond_any in ifs_any:
                cond_parts.append(self._render_expr(cond_any))
            cond_expr = " && ".join(cond_parts)
        loop_var = _safe_ident(td.get("id"), "__sc_i") if td.get("kind") == "Name" else "__sc_i"
        iter_expr = self._render_expr(iter_any)
        insert_stmt = "__out.add(" + elt + ");"
        if cond_expr != "":
            insert_stmt = "if (" + cond_expr + ") { " + insert_stmt + " }"
        return (
            "(() { var __out = pytraNewSet(); for (var " + loop_var + " in " + iter_expr + ") { "
            + insert_stmt + " } return __out; })()"
        )

    def _render_dict_comp(self, ed: dict[str, Any]) -> str:
        gens_any = ed.get("generators")
        gens = gens_any if isinstance(gens_any, list) else []
        if len(gens) == 0 or not isinstance(gens[0], dict):
            return "{}"
        gen = gens[0]
        target_any = gen.get("target")
        iter_any = gen.get("iter")
        if not isinstance(target_any, dict) or not isinstance(iter_any, dict):
            return "{}"
        td: dict[str, Any] = target_any
        key_expr = self._render_expr(ed.get("key"))
        value_expr = self._render_expr(ed.get("value"))
        cond_expr = ""
        ifs_any = gen.get("ifs")
        if isinstance(ifs_any, list) and len(ifs_any) > 0:
            cond_parts: list[str] = []
            for cond_any in ifs_any:
                cond_parts.append(self._render_expr(cond_any))
            cond_expr = " && ".join(cond_parts)
        loop_var = _safe_ident(td.get("id"), "__dc_i") if td.get("kind") == "Name" else "__dc_i"
        iter_rendered = self._render_expr(iter_any)
        insert_stmt = "__out[" + key_expr + "] = " + value_expr + ";"
        if cond_expr != "":
            insert_stmt = "if (" + cond_expr + ") { " + insert_stmt + " }"
        return (
            "(() { var __out = {}; for (var " + loop_var + " in " + iter_rendered + ") { "
            + insert_stmt + " } return __out; })()"
        )

    def _render_constant(self, value: Any) -> str:
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            return str(value)
        if isinstance(value, str):
            return _dart_string(value)
        return "null"


_REPO_ROOT = Path(__file__).resolve().parents[5]


def _has_handwritten_runtime(module_id: str) -> bool:
    """Check if a hand-written .dart file exists in src/runtime/dart/ for this module."""
    parts = module_id.split(".")
    if len(parts) < 2 or parts[0] != "pytra":
        return False
    rel = ".".join(parts[1:])
    runtime_path = _REPO_ROOT / "src" / "runtime" / "dart" / (rel.replace(".", "/") + ".dart")
    return runtime_path.exists()


def emit_dart_module(east_doc: dict[str, Any]) -> str:
    """Emit a complete Dart source file from a linked EAST3 document."""
    # built_in modules are provided by py_runtime — skip emit
    meta_any = east_doc.get("meta")
    meta = meta_any if isinstance(meta_any, dict) else {}
    emit_ctx_any = meta.get("emit_context")
    emit_ctx = emit_ctx_any if isinstance(emit_ctx_any, dict) else {}
    module_id = emit_ctx.get("module_id", "") if isinstance(emit_ctx.get("module_id"), str) else ""
    module_parts = module_id.split(".")
    if len(module_parts) >= 3 and module_parts[0] == "pytra" and module_parts[1] == "built_in":
        return ""
    # Skip modules that have hand-written runtime replacements
    if _has_handwritten_runtime(module_id):
        return ""
    reject_backend_homogeneous_tuple_ellipsis_type_exprs(east_doc, backend_name="Dart backend")
    return DartNativeEmitter(east_doc).transpile()


def transpile_to_dart_native(east_doc: dict[str, Any]) -> str:
    """Compatibility alias for older callers."""
    return emit_dart_module(east_doc)
