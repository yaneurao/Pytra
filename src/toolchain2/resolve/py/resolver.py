"""east1 → east2 resolver: 型解決 + 正規化 (Python 固有 → 言語非依存).

責務:
  - 型注釈の正規化 (int→int64, float→float64 等)
  - 全式の resolved_type 確定
  - borrow_kind の判定
  - cast 挿入 (数値昇格等)
  - built-in → py_* ノード変換
  - semantic_tag / runtime_module_id / runtime_symbol 付与
  - range() → ForRange 変換
  - arg_usage / arg_type_exprs / return_type_expr 生成
  - schema_version / dispatch_mode 付与

§5 準拠: Any/object 禁止、pytra.std.* のみ使用。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pytra.std import json
from pytra.std.json import JsonVal
from pytra.std.pathlib import Path

from toolchain2.resolve.py.type_norm import (
    normalize_type,
    make_type_expr,
    is_numeric,
    is_int_type,
    is_float_type,
    extract_base_type,
    extract_type_args,
)
from toolchain2.resolve.py.builtin_registry import (
    BuiltinRegistry,
    load_builtin_registry,
    FuncSig,
    ClassSig,
    ExternV2,
    VarSig,
)
from toolchain2.resolve.py.normalize_order import normalize_field_order


@dataclass
class ResolveResult:
    """resolve の結果。"""
    east2_doc: dict[str, JsonVal]
    source_path: str


@dataclass
class Scope:
    """Variable type environment."""
    vars: dict[str, str] = field(default_factory=dict)
    parent: Scope | None = None

    def lookup(self, name: str) -> str:
        v: str = self.vars.get(name, "")
        if v != "":
            return v
        if self.parent is not None:
            return self.parent.lookup(name)
        return "unknown"

    def define(self, name: str, typ: str) -> None:
        self.vars[name] = typ

    def child(self) -> Scope:
        return Scope(parent=self)


@dataclass
class ResolveContext:
    """Resolution state for a single module."""
    registry: BuiltinRegistry
    scope: Scope
    # Import info
    import_symbols: dict[str, dict[str, str]] = field(default_factory=dict)  # local→{module, name}
    import_modules: dict[str, str] = field(default_factory=dict)  # local→module_id
    # Functions defined in this module
    module_functions: dict[str, FuncSig] = field(default_factory=dict)
    # Classes defined in this module
    module_classes: dict[str, ClassSig] = field(default_factory=dict)
    # Tracked implicit builtin modules
    used_builtin_modules: set[str] = field(default_factory=set)
    # Current function parameters (for borrow_kind: readonly_ref)
    current_params: set[str] = field(default_factory=set)
    # Whether we're inside a class body
    in_class: bool = False
    # Source file path
    source_file: str = ""
    # Runtime symbol index (loaded lazily)
    _runtime_index: dict[str, JsonVal] | None = None

    def load_runtime_index(self) -> dict[str, JsonVal]:
        if self._runtime_index is not None:
            return self._runtime_index
        try:
            idx_path: Path = Path("tools/runtime_symbol_index.json")
            if idx_path.exists():
                text: str = idx_path.read_text(encoding="utf-8")
                raw: JsonVal = json.loads(text).raw
                if isinstance(raw, dict):
                    self._runtime_index = raw
                    return raw
        except Exception:
            pass
        self._runtime_index = {}
        return self._runtime_index

    def lookup_runtime_module_group(self, module_id: str) -> str:
        idx: dict[str, JsonVal] = self.load_runtime_index()
        mods = idx.get("modules")
        if not isinstance(mods, dict):
            return ""
        mod = mods.get(module_id)
        if not isinstance(mod, dict):
            return ""
        grp = mod.get("runtime_group")
        return str(grp) if isinstance(grp, str) else ""

    def lookup_runtime_symbol_doc(self, module_id: str, symbol: str) -> dict[str, JsonVal]:
        idx: dict[str, JsonVal] = self.load_runtime_index()
        mods = idx.get("modules")
        if not isinstance(mods, dict):
            return {}
        mod = mods.get(module_id)
        if not isinstance(mod, dict):
            return {}
        syms = mod.get("symbols")
        if not isinstance(syms, dict):
            return {}
        sym = syms.get(symbol)
        if not isinstance(sym, dict):
            return {}
        return sym

    def lookup_adapter_kind(self, module_id: str, symbol: str) -> str:
        doc: dict[str, JsonVal] = self.lookup_runtime_symbol_doc(module_id, symbol)
        ak = doc.get("call_adapter_kind")
        return str(ak) if isinstance(ak, str) else ""

    def runtime_module_exists(self, module_id: str) -> bool:
        idx: dict[str, JsonVal] = self.load_runtime_index()
        mods = idx.get("modules")
        if not isinstance(mods, dict):
            return False
        return module_id in mods

    def canonical_module_id(self, module_id: str) -> str:
        mod: str = module_id.strip()
        if mod.startswith("pytra.") or mod.startswith("toolchain."):
            return mod
        if "." not in mod and mod != "":
            candidate: str = "pytra.std." + mod
            if self.runtime_module_exists(candidate):
                return candidate
        return mod

    # Renamed symbols mapping (original_name → name)
    renamed_symbols: dict[str, str] = field(default_factory=dict)

    def lookup_function(self, name: str) -> FuncSig | None:
        """Look up function: module-local first (with rename), then builtins."""
        local: FuncSig | None = self.module_functions.get(name)
        if local is not None:
            return local
        # Check renamed symbols
        renamed: str = self.renamed_symbols.get(name, "")
        if renamed != "":
            local2: FuncSig | None = self.module_functions.get(renamed)
            if local2 is not None:
                return local2
        return self.registry.lookup_function(name)

    def lookup_class(self, name: str) -> ClassSig | None:
        """Look up class: module-local first, then builtins."""
        local: ClassSig | None = self.module_classes.get(name)
        if local is not None:
            return local
        return self.registry.classes.get(name)


# ---------------------------------------------------------------------------
# Expression type resolution
# ---------------------------------------------------------------------------

def _resolve_expr(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    """Resolve the type of an expression node, mutating it in place.
    Returns the resolved_type string."""
    kind_val = expr.get("kind")
    kind: str = str(kind_val) if isinstance(kind_val, str) else ""

    if kind == "Constant":
        return _resolve_constant(expr, ctx)
    if kind == "Name":
        return _resolve_name(expr, ctx)
    if kind == "BinOp":
        return _resolve_binop(expr, ctx)
    if kind == "UnaryOp":
        return _resolve_unaryop(expr, ctx)
    if kind == "Compare":
        return _resolve_compare(expr, ctx)
    if kind == "BoolOp":
        return _resolve_boolop(expr, ctx)
    if kind == "Call":
        return _resolve_call(expr, ctx)
    if kind == "Attribute":
        return _resolve_attribute(expr, ctx)
    if kind == "Subscript":
        return _resolve_subscript(expr, ctx)
    if kind == "List":
        return _resolve_list(expr, ctx)
    if kind == "Dict":
        return _resolve_dict(expr, ctx)
    if kind == "Set":
        return _resolve_set(expr, ctx)
    if kind == "Tuple":
        return _resolve_tuple(expr, ctx)
    if kind == "IfExp":
        return _resolve_ifexp(expr, ctx)
    if kind == "ListComp":
        return _resolve_listcomp(expr, ctx)
    if kind == "Starred":
        return _resolve_starred(expr, ctx)
    if kind == "JoinedStr":
        expr["resolved_type"] = "str"
        # Resolve child values
        values = expr.get("values")
        if isinstance(values, list):
            for v in values:
                if isinstance(v, dict):
                    _resolve_expr(v, ctx)
        return "str"

    # Fallback: resolve children recursively
    rt = expr.get("resolved_type")
    if not isinstance(rt, str) or rt == "":
        expr["resolved_type"] = "unknown"
    for key in expr:
        val = expr[key]
        if isinstance(val, dict) and "kind" in val:
            _resolve_expr(val, ctx)
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, dict) and "kind" in item:
                    _resolve_expr(item, ctx)
    rt2 = expr.get("resolved_type")
    return str(rt2) if isinstance(rt2, str) else "unknown"


def _resolve_constant(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    val = expr.get("value")
    if val is None:
        t: str = "None"
    elif isinstance(val, bool):
        t = "bool"
    elif isinstance(val, int):
        t = "int64"
    elif isinstance(val, float):
        t = "float64"
    elif isinstance(val, str):
        t = "str"
    else:
        t = "unknown"
    expr["resolved_type"] = t
    return t


def _resolve_name(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    name_val = expr.get("id")
    name: str = str(name_val) if isinstance(name_val, str) else ""
    t: str = ctx.scope.lookup(name)
    expr["resolved_type"] = t
    # Borrow kind: readonly_ref for typed names (references to known variables)
    # value for untyped (function names, unknown)
    if t != "unknown":
        expr["borrow_kind"] = "readonly_ref"
    return t


def _resolve_binop(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    left = expr.get("left")
    right = expr.get("right")
    lt: str = "unknown"
    rt: str = "unknown"
    if isinstance(left, dict):
        lt = _resolve_expr(left, ctx)
    if isinstance(right, dict):
        rt = _resolve_expr(right, ctx)

    op_val = expr.get("op")
    op: str = str(op_val) if isinstance(op_val, str) else ""

    # Determine result type
    result: str = _binop_result_type(lt, rt, op)
    expr["resolved_type"] = result

    # Cast insertion for numeric promotion
    if is_int_type(lt) and is_float_type(rt):
        casts = expr.get("casts")
        if isinstance(casts, list):
            casts.append({"on": "left", "from": lt, "to": rt, "reason": "numeric_promotion"})
    elif is_float_type(lt) and is_int_type(rt):
        casts = expr.get("casts")
        if isinstance(casts, list):
            casts.append({"on": "right", "from": rt, "to": lt, "reason": "numeric_promotion"})

    return result


def _binop_result_type(lt: str, rt: str, op: str) -> str:
    """Determine result type of a binary operation."""
    # String operations
    if lt == "str" and rt == "str":
        if op == "Add":
            return "str"
        if op == "Mod":
            return "str"
    if lt == "str" and is_int_type(rt) and op == "Mult":
        return "str"
    if is_int_type(lt) and rt == "str" and op == "Mult":
        return "str"

    # Path operations
    if lt == "Path" or rt == "Path":
        if op == "Div":
            return "Path"

    # Division always produces float
    if op == "Div":
        if is_numeric(lt) and is_numeric(rt):
            return "float64"

    # Floor division and modulo with ints produce int
    if op == "FloorDiv" or op == "Mod":
        if is_int_type(lt) and is_int_type(rt):
            return lt
        if is_float_type(lt) or is_float_type(rt):
            return "float64"

    # Numeric promotion
    if is_float_type(lt) or is_float_type(rt):
        return "float64"
    if is_int_type(lt) and is_int_type(rt):
        return lt  # Same int type

    # Bitwise operations on ints
    if op == "BitAnd" or op == "BitOr" or op == "BitXor" or op == "LShift" or op == "RShift":
        if is_int_type(lt):
            return lt

    # Boolean operations
    if lt == "bool" and rt == "bool":
        return "bool"

    # Fallback
    if lt != "unknown":
        return lt
    if rt != "unknown":
        return rt
    return "unknown"


def _resolve_unaryop(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    operand = expr.get("operand")
    ot: str = "unknown"
    if isinstance(operand, dict):
        ot = _resolve_expr(operand, ctx)
    op_val = expr.get("op")
    op: str = str(op_val) if isinstance(op_val, str) else ""
    if op == "Not":
        expr["resolved_type"] = "bool"
        return "bool"
    if op == "USub" or op == "UAdd":
        expr["resolved_type"] = ot
        return ot
    if op == "Invert":
        expr["resolved_type"] = ot
        return ot
    expr["resolved_type"] = ot
    return ot


def _resolve_compare(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    left = expr.get("left")
    if isinstance(left, dict):
        _resolve_expr(left, ctx)
    comps = expr.get("comparators")
    if isinstance(comps, list):
        for c in comps:
            if isinstance(c, dict):
                _resolve_expr(c, ctx)
    expr["resolved_type"] = "bool"
    return "bool"


def _resolve_boolop(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    values = expr.get("values")
    if isinstance(values, list):
        for v in values:
            if isinstance(v, dict):
                _resolve_expr(v, ctx)
    # BoolOp (and/or) always resolves to bool in Pytra
    expr["resolved_type"] = "bool"
    return "bool"


def _resolve_call(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    func = expr.get("func")
    if not isinstance(func, dict):
        expr["resolved_type"] = "unknown"
        return "unknown"

    func_kind: str = str(func.get("kind", ""))

    # Method call: obj.method(...)
    if func_kind == "Attribute":
        return _resolve_method_call(expr, func, ctx)

    # Simple function call: f(...)
    if func_kind == "Name":
        return _resolve_simple_call(expr, func, ctx)

    # Fallback
    _resolve_expr(func, ctx)
    _resolve_call_args(expr, ctx)
    expr["resolved_type"] = "unknown"
    return "unknown"


def _resolve_call_args(expr: dict[str, JsonVal], ctx: ResolveContext) -> None:
    """Resolve types of call arguments."""
    args = expr.get("args")
    if isinstance(args, list):
        for a in args:
            if isinstance(a, dict):
                _resolve_expr(a, ctx)
    keywords = expr.get("keywords")
    if isinstance(keywords, list):
        for kw in keywords:
            if isinstance(kw, dict):
                val = kw.get("value")
                if isinstance(val, dict):
                    _resolve_expr(val, ctx)


def _resolve_simple_call(expr: dict[str, JsonVal], func: dict[str, JsonVal], ctx: ResolveContext) -> str:
    """Resolve a simple Name-based function call."""
    name_val = func.get("id")
    name: str = str(name_val) if isinstance(name_val, str) else ""

    # Resolve arguments first
    _resolve_call_args(expr, ctx)

    # Built-in function?
    if ctx.registry.is_builtin(name):
        return _resolve_builtin_call(expr, func, name, ctx)

    # Imported symbol?
    imp: dict[str, str] = ctx.import_symbols.get(name, {})
    if len(imp) > 0:
        return _resolve_imported_call(expr, func, name, imp, ctx)

    # Module-local function?
    local_func: FuncSig | None = ctx.lookup_function(name)
    if local_func is not None:
        t: str = local_func.return_type
        expr["resolved_type"] = t
        func["resolved_type"] = "unknown"
        return t

    # Class constructor?
    local_class: ClassSig | None = ctx.lookup_class(name)
    if local_class is not None:
        expr["resolved_type"] = name
        func["resolved_type"] = "unknown"
        return name

    # Unknown
    func["resolved_type"] = "unknown"
    expr["resolved_type"] = "unknown"
    return "unknown"


def _resolve_builtin_call(
    expr: dict[str, JsonVal],
    func: dict[str, JsonVal],
    name: str,
    ctx: ResolveContext,
) -> str:
    """Resolve a built-in function call (print, len, int, etc.)."""
    # Determine return type
    sig: FuncSig | None = ctx.registry.lookup_function(name)
    ret: str = "unknown"
    if sig is not None:
        ret = sig.return_type

    # Type-specific overrides based on arguments
    args = expr.get("args")
    arg_types: list[str] = []
    if isinstance(args, list):
        for a in args:
            if isinstance(a, dict):
                at = a.get("resolved_type")
                arg_types.append(str(at) if isinstance(at, str) else "unknown")

    # Cast functions: int(x) → int64, float(x) → float64, etc.
    if name == "int":
        ret = "int64"
    elif name == "float":
        ret = "float64"
    elif name == "str":
        ret = "str"
    elif name == "bool":
        ret = "bool"
    elif name == "len":
        ret = "int64"
    elif name == "ord":
        ret = "int64"
    elif name == "chr":
        ret = "str"
    elif name == "abs":
        if len(arg_types) > 0:
            ret = arg_types[0]
        else:
            ret = "int64"
    elif name == "round":
        ret = "int64"
    elif name == "repr":
        ret = "str"
    elif name == "print":
        ret = "None"
    elif name == "isinstance" or name == "issubclass":
        ret = "bool"
    elif name == "min" or name == "max":
        # Generic: return type of first argument
        if len(arg_types) > 0:
            ret = arg_types[0]
    elif name == "sorted" or name == "reversed":
        if len(arg_types) > 0:
            ret = arg_types[0]
    elif name == "enumerate":
        if len(arg_types) > 0:
            inner: str = arg_types[0]
            elem: str = "unknown"
            if inner.startswith("list[") and inner.endswith("]"):
                elem = inner[5:-1]
            ret = "list[tuple[int64, " + elem + "]]"
    elif name == "zip":
        if len(arg_types) >= 2:
            t1: str = arg_types[0]
            t2: str = arg_types[1]
            e1: str = "unknown"
            e2: str = "unknown"
            if t1.startswith("list[") and t1.endswith("]"):
                e1 = t1[5:-1]
            if t2.startswith("list[") and t2.endswith("]"):
                e2 = t2[5:-1]
            ret = "list[tuple[" + e1 + ", " + e2 + "]]"
    elif name == "sum":
        if len(arg_types) > 0:
            inner2: str = arg_types[0]
            if inner2.startswith("list[") and inner2.endswith("]"):
                ret = inner2[5:-1]
            else:
                ret = "int64"
    elif name == "any" or name == "all":
        ret = "bool"

    expr["resolved_type"] = ret
    func["resolved_type"] = "unknown"

    # Add runtime metadata from extern_v2
    extern: ExternV2 | None = sig.extern if sig is not None else None

    expr["lowered_kind"] = "BuiltinCall"
    expr["builtin_name"] = name
    if extern is not None:
        # runtime_call = extern.symbol (e.g., "py_print", "len")
        expr["runtime_call"] = extern.symbol
        expr["runtime_module_id"] = extern.module
        expr["runtime_symbol"] = extern.symbol
        # Adapter kind from runtime index
        adapter: str = ctx.lookup_adapter_kind(extern.module, extern.symbol)
        if adapter == "":
            adapter = "builtin"
        expr["runtime_call_adapter_kind"] = adapter
        if extern.tag != "":
            expr["semantic_tag"] = extern.tag
        # Track implicit builtin module
        ctx.used_builtin_modules.add(extern.module)

    return ret


def _resolve_imported_call(
    expr: dict[str, JsonVal],
    func: dict[str, JsonVal],
    local_name: str,
    imp: dict[str, str],
    ctx: ResolveContext,
) -> str:
    """Resolve a call to an imported symbol."""
    module_id: str = imp.get("module", "")
    export_name: str = imp.get("name", "")
    if export_name == "":
        export_name = local_name

    func["resolved_type"] = "unknown"

    # Determine return type from stdlib registry if available
    ret: str = "unknown"
    stdlib_func: FuncSig | None = ctx.registry.lookup_stdlib_function(module_id, export_name)
    if stdlib_func is not None:
        ret = stdlib_func.return_type

    runtime_module: str = ctx.canonical_module_id(module_id)

    # Only annotate with runtime call info if the symbol exists in the runtime index
    sym_doc: dict[str, JsonVal] = ctx.lookup_runtime_symbol_doc(runtime_module, export_name)
    has_runtime_entry: bool = len(sym_doc) > 0

    if has_runtime_entry:
        # Qualify with short module name for stdlib
        short_mod: str = module_id
        if short_mod.startswith("pytra.std."):
            short_mod = short_mod[len("pytra.std."):]
        elif short_mod.startswith("pytra."):
            short_mod = ""
        if short_mod != "" and "." not in short_mod:
            qualified_call: str = short_mod + "." + export_name
        else:
            qualified_call = export_name
        expr["resolved_runtime_call"] = qualified_call
        expr["resolved_runtime_source"] = "import_symbol"
        expr["runtime_module_id"] = runtime_module
        expr["runtime_symbol"] = export_name

        # Adapter kind
        adapter: str = ctx.lookup_adapter_kind(runtime_module, export_name)
        if adapter == "":
            grp: str = ctx.lookup_runtime_module_group(runtime_module)
            if grp == "built_in":
                adapter = "builtin"
            else:
                adapter = "extern_delegate"
        expr["runtime_call_adapter_kind"] = adapter

    expr["resolved_type"] = ret
    return ret


def _resolve_method_call(
    expr: dict[str, JsonVal],
    func: dict[str, JsonVal],
    ctx: ResolveContext,
) -> str:
    """Resolve a method call (obj.method(...))."""
    value = func.get("value")
    attr_val = func.get("attr")
    attr: str = str(attr_val) if isinstance(attr_val, str) else ""

    # Resolve receiver
    receiver_type: str = "unknown"
    if isinstance(value, dict):
        receiver_type = _resolve_expr(value, ctx)

    # Resolve arguments
    _resolve_call_args(expr, ctx)

    # Module attribute call (math.sqrt etc.)
    if isinstance(value, dict) and value.get("kind") == "Name":
        receiver_name: str = str(value.get("id", ""))
        mod_id: str = ctx.import_modules.get(receiver_name, "")
        if mod_id != "":
            return _resolve_module_attr_call(expr, func, receiver_name, mod_id, attr, ctx)

    # Container method call (list.append, str.split, etc.)
    owner_base: str = extract_base_type(receiver_type)
    method_sig: FuncSig | None = ctx.registry.lookup_method(owner_base, attr)
    if method_sig is not None:
        return _resolve_container_method_call(expr, func, receiver_type, owner_base, attr, method_sig, ctx)

    # User-defined class method
    cls: ClassSig | None = ctx.lookup_class(owner_base)
    if cls is not None:
        msig: FuncSig | None = cls.methods.get(attr)
        if msig is not None:
            ret: str = _substitute_type_params(msig.return_type, receiver_type, cls)
            expr["resolved_type"] = ret
            func["resolved_type"] = "unknown"
            return ret

    # Fallback
    func["resolved_type"] = "unknown"
    expr["resolved_type"] = "unknown"
    return "unknown"


def _resolve_module_attr_call(
    expr: dict[str, JsonVal],
    func: dict[str, JsonVal],
    receiver_name: str,
    module_id: str,
    attr: str,
    ctx: ResolveContext,
) -> str:
    """Resolve a module.attr() call (e.g., math.sqrt(x))."""
    # Look up in stdlib registry first
    stdlib_func: FuncSig | None = ctx.registry.lookup_stdlib_function(module_id, attr)
    extern: ExternV2 | None = stdlib_func.extern if stdlib_func is not None else None

    # Determine return type
    ret: str = "unknown"
    if stdlib_func is not None:
        ret = stdlib_func.return_type
    if ret == "unknown":
        ret = _infer_stdlib_return_type(ctx.canonical_module_id(module_id), attr, expr, ctx)

    expr["resolved_type"] = ret
    func["resolved_type"] = "unknown"

    # Runtime metadata from extern_v2
    if extern is not None:
        expr["resolved_runtime_call"] = receiver_name + "." + attr
        expr["resolved_runtime_source"] = "module_attr"
        expr["runtime_module_id"] = module_id
        expr["runtime_symbol"] = extern.symbol
        # Adapter kind from runtime index
        adapter: str = ctx.lookup_adapter_kind(extern.module, extern.symbol)
        if adapter != "":
            expr["runtime_call_adapter_kind"] = adapter
        expr["semantic_tag"] = extern.tag
    else:
        # Fallback for unresolved stdlib calls
        expr["resolved_runtime_call"] = receiver_name + "." + attr
        expr["resolved_runtime_source"] = "module_attr"
        expr["runtime_module_id"] = module_id
        expr["runtime_symbol"] = attr
        canonical: str = ctx.canonical_module_id(module_id)
        adapter2: str = ctx.lookup_adapter_kind(canonical, attr)
        if adapter2 != "":
            expr["runtime_call_adapter_kind"] = adapter2
        expr["semantic_tag"] = "stdlib.method." + attr

    return ret


def _infer_stdlib_return_type(canonical: str, attr: str, expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    """Infer return type for stdlib module.attr calls."""
    # math module: most return float64
    if canonical == "pytra.std.math":
        if attr == "floor" or attr == "ceil":
            return "float64"
        if attr == "sqrt" or attr == "sin" or attr == "cos" or attr == "tan":
            return "float64"
        if attr == "log" or attr == "log2" or attr == "log10" or attr == "exp":
            return "float64"
        if attr == "fabs" or attr == "pow" or attr == "hypot" or attr == "atan2":
            return "float64"
        if attr == "pi" or attr == "e" or attr == "tau" or attr == "inf":
            return "float64"
        if attr == "isnan" or attr == "isinf" or attr == "isfinite":
            return "bool"
        return "float64"  # Default for math

    # time module
    if canonical == "pytra.std.time":
        if attr == "time" or attr == "perf_counter" or attr == "monotonic":
            return "float64"
        if attr == "sleep":
            return "None"
        return "float64"

    # random module
    if canonical == "pytra.std.random":
        if attr == "random":
            return "float64"
        if attr == "randint" or attr == "randrange":
            return "int64"
        if attr == "uniform":
            return "float64"
        if attr == "seed":
            return "None"
        if attr == "shuffle":
            return "None"
        if attr == "choice":
            # Return element type from argument
            args = expr.get("args")
            if isinstance(args, list) and len(args) > 0:
                first = args[0]
                if isinstance(first, dict):
                    ft = first.get("resolved_type")
                    if isinstance(ft, str) and ft.startswith("list[") and ft.endswith("]"):
                        return ft[5:-1]
            return "unknown"
        return "unknown"

    # os module
    if canonical == "pytra.std.os":
        return "unknown"

    # pathlib module
    if canonical == "pytra.std.pathlib":
        return "Path"

    # json module
    if canonical == "pytra.std.json":
        if attr == "loads":
            return "JsonValue"
        if attr == "loads_obj":
            return "JsonObj"
        if attr == "loads_arr":
            return "JsonArr"
        if attr == "dumps" or attr == "dumps_jv":
            return "str"
        return "unknown"

    return "unknown"


def _resolve_container_method_call(
    expr: dict[str, JsonVal],
    func: dict[str, JsonVal],
    receiver_type: str,
    owner_base: str,
    method: str,
    method_sig: FuncSig,
    ctx: ResolveContext,
) -> str:
    """Resolve a container method call (list.append, str.split, etc.)."""
    # Substitute type parameters
    cls: ClassSig | None = ctx.registry.classes.get(owner_base)
    ret: str = method_sig.return_type
    if cls is not None:
        ret = _substitute_type_params(ret, receiver_type, cls)
    ret = normalize_type(ret)

    expr["resolved_type"] = ret
    func["resolved_type"] = "unknown"

    # Runtime owner: the receiver expression
    value = func.get("value")
    if isinstance(value, dict):
        from toolchain2.common.jv import deep_copy_json
        owner_copy: JsonVal = deep_copy_json(value)
        expr["runtime_owner"] = owner_copy

    # Runtime metadata from extern_v2 (正本)
    method_extern: ExternV2 | None = method_sig.extern
    if method_extern is not None and method_extern.module != "":
        mod = method_extern.module
        runtime_call_name = method_extern.symbol
    else:
        # Fallback: owner_base.method pattern
        mod = _default_container_module(owner_base)
        runtime_call_name = owner_base + "." + method
    sym: str = runtime_call_name  # e.g., "list.append" or "str.join"
    expr["lowered_kind"] = "BuiltinCall"
    expr["builtin_name"] = method
    expr["runtime_call"] = runtime_call_name
    if mod != "":
        expr["runtime_module_id"] = mod
    expr["runtime_symbol"] = sym
    adapter: str = "builtin"
    expr["runtime_call_adapter_kind"] = adapter
    # semantic_tag from extern_v2 or fallback
    if method_extern is not None and method_extern.tag != "":
        expr["semantic_tag"] = method_extern.tag
    else:
        expr["semantic_tag"] = "stdlib.method." + method

    return ret


def _default_container_module(owner_base: str) -> str:
    """Fallback runtime module for container types (when no extern_v2)."""
    if owner_base == "list":
        return "pytra.core.list"
    if owner_base == "dict":
        return "pytra.core.dict"
    if owner_base == "set":
        return "pytra.core.set"
    if owner_base == "str":
        return "pytra.core.str"
    if owner_base == "tuple":
        return "pytra.core.tuple"
    if owner_base == "deque":
        return "pytra.std.collections"
    return ""


def _substitute_type_params(ret_type: str, concrete_type: str, cls: ClassSig) -> str:
    """Substitute generic type parameters (T, K, V) with concrete types."""
    if len(cls.template_params) == 0:
        return ret_type

    type_args: list[str] = extract_type_args(concrete_type)
    if len(type_args) == 0:
        return ret_type

    result: str = ret_type
    for i in range(min(len(cls.template_params), len(type_args))):
        param: str = cls.template_params[i]
        arg: str = type_args[i]
        result = result.replace(param, arg)

    return result


def _resolve_attribute(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    value = expr.get("value")
    attr_val = expr.get("attr")
    attr: str = str(attr_val) if isinstance(attr_val, str) else ""

    receiver_type: str = "unknown"
    if isinstance(value, dict):
        receiver_type = _resolve_expr(value, ctx)

    # Module-level attribute access (e.g., math.pi)
    if isinstance(value, dict) and value.get("kind") == "Name":
        receiver_name: str = str(value.get("id", ""))
        mod_id: str = ctx.import_modules.get(receiver_name, "")
        if mod_id != "":
            canonical: str = ctx.canonical_module_id(mod_id)
            t: str = _infer_module_attr_type(canonical, attr, ctx)
            expr["resolved_type"] = t
            return t

    # Class field access — check field_types from ClassDef (parse が収集済み)
    owner_base: str = extract_base_type(receiver_type)

    # Look up in module classes first (field_types from EAST1)
    cls_sig: ClassSig | None = ctx.module_classes.get(owner_base)
    if cls_sig is None:
        cls_sig = ctx.module_classes.get(receiver_type)
    if cls_sig is not None and attr in cls_sig.fields:
        ft: str = cls_sig.fields[attr]
        ft_resolved: str = normalize_type(ft)
        expr["resolved_type"] = ft_resolved
        return ft_resolved

    # Fall back to builtin registry classes
    cls2: ClassSig | None = ctx.registry.classes.get(owner_base)
    if cls2 is not None and attr in cls2.fields:
        ft2: str = cls2.fields[attr]
        ft2_resolved: str = _substitute_type_params(ft2, receiver_type, cls2)
        expr["resolved_type"] = normalize_type(ft2_resolved)
        return normalize_type(ft2_resolved)

    expr["resolved_type"] = "unknown"
    return "unknown"


def _infer_module_attr_type(canonical: str, attr: str, ctx: ResolveContext) -> str:
    """Infer type of a module-level attribute (e.g., math.pi)."""
    # Look up in stdlib registry
    var_sig: VarSig | None = ctx.registry.lookup_stdlib_variable(canonical, attr)
    if var_sig is not None:
        return var_sig.var_type
    return "unknown"


def _resolve_subscript(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    value = expr.get("value")
    slice_node = expr.get("slice")

    vt: str = "unknown"
    if isinstance(value, dict):
        vt = _resolve_expr(value, ctx)
    if isinstance(slice_node, dict):
        _resolve_expr(slice_node, ctx)

    # list[T][i] → T
    if vt.startswith("list[") and vt.endswith("]"):
        elem: str = vt[5:-1]
        expr["resolved_type"] = elem
        return elem

    # dict[K,V][k] → V
    if vt.startswith("dict[") and vt.endswith("]"):
        inner: str = vt[5:-1]
        args: list[str] = extract_type_args(vt)
        if len(args) >= 2:
            expr["resolved_type"] = args[1]
            return args[1]

    # str[i] → str
    if vt == "str":
        expr["resolved_type"] = "str"
        return "str"

    # tuple[...][i] → depends on index
    if vt.startswith("tuple[") and vt.endswith("]"):
        args2: list[str] = extract_type_args(vt)
        # If constant index, return that element type
        if isinstance(slice_node, dict) and slice_node.get("kind") == "Constant":
            idx = slice_node.get("value")
            if isinstance(idx, int) and 0 <= idx < len(args2):
                expr["resolved_type"] = args2[idx]
                return args2[idx]
        if len(args2) > 0:
            expr["resolved_type"] = args2[0]
            return args2[0]

    expr["resolved_type"] = "unknown"
    return "unknown"


def _resolve_list(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    elems = expr.get("elements")
    elem_type: str = "unknown"
    if isinstance(elems, list):
        for e in elems:
            if isinstance(e, dict):
                t: str = _resolve_expr(e, ctx)
                if elem_type == "unknown":
                    elem_type = t
    if elem_type != "unknown":
        result: str = "list[" + elem_type + "]"
    else:
        result = "list[unknown]"
    expr["resolved_type"] = result
    return result


def _resolve_dict(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    kt: str = "unknown"
    vt: str = "unknown"
    # EAST1 uses "entries" format: [{key: ..., value: ...}, ...]
    entries = expr.get("entries")
    if isinstance(entries, list):
        for entry in entries:
            if isinstance(entry, dict):
                key_node = entry.get("key")
                val_node = entry.get("value")
                if isinstance(key_node, dict):
                    t: str = _resolve_expr(key_node, ctx)
                    if kt == "unknown":
                        kt = t
                if isinstance(val_node, dict):
                    t2: str = _resolve_expr(val_node, ctx)
                    if vt == "unknown":
                        vt = t2
    else:
        # Fallback: separate keys/values arrays
        keys = expr.get("keys")
        values = expr.get("values")
        if isinstance(keys, list):
            for k in keys:
                if isinstance(k, dict):
                    t3: str = _resolve_expr(k, ctx)
                    if kt == "unknown":
                        kt = t3
        if isinstance(values, list):
            for v in values:
                if isinstance(v, dict):
                    t4: str = _resolve_expr(v, ctx)
                    if vt == "unknown":
                        vt = t4
    result: str = "dict[" + kt + "," + vt + "]"
    expr["resolved_type"] = result
    return result


def _resolve_set(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    elems = expr.get("elements")
    elem_type: str = "unknown"
    if isinstance(elems, list):
        for e in elems:
            if isinstance(e, dict):
                t: str = _resolve_expr(e, ctx)
                if elem_type == "unknown":
                    elem_type = t
    result: str = "set[" + elem_type + "]"
    expr["resolved_type"] = result
    return result


def _resolve_tuple(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    elems = expr.get("elements")
    types: list[str] = []
    if isinstance(elems, list):
        for e in elems:
            if isinstance(e, dict):
                t: str = _resolve_expr(e, ctx)
                types.append(t)
    if len(types) > 0:
        result: str = "tuple[" + ", ".join(types) + "]"
    else:
        result = "tuple[]"
    expr["resolved_type"] = result
    return result


def _resolve_ifexp(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    test = expr.get("test")
    body = expr.get("body")
    orelse = expr.get("orelse")
    if isinstance(test, dict):
        _resolve_expr(test, ctx)
    bt: str = "unknown"
    if isinstance(body, dict):
        bt = _resolve_expr(body, ctx)
    if isinstance(orelse, dict):
        _resolve_expr(orelse, ctx)
    expr["resolved_type"] = bt
    return bt


def _resolve_listcomp(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    generators = expr.get("generators")
    comp_scope: Scope = ctx.scope.child()
    old_scope: Scope = ctx.scope

    if isinstance(generators, list):
        for gen in generators:
            if isinstance(gen, dict):
                iter_expr = gen.get("iter")
                if isinstance(iter_expr, dict):
                    it: str = _resolve_expr(iter_expr, ctx)
                    # Extract element type from iterable
                    elem: str = "unknown"
                    if it.startswith("list[") and it.endswith("]"):
                        elem = it[5:-1]
                    elif it.startswith("set[") and it.endswith("]"):
                        elem = it[4:-1]
                    target = gen.get("target")
                    if isinstance(target, dict) and target.get("kind") == "Name":
                        var_name = target.get("id")
                        if isinstance(var_name, str):
                            comp_scope.define(var_name, elem)
                            target["resolved_type"] = elem
                # Resolve filter conditions
                ifs = gen.get("ifs")
                if isinstance(ifs, list):
                    ctx.scope = comp_scope
                    for cond in ifs:
                        if isinstance(cond, dict):
                            _resolve_expr(cond, ctx)
                    ctx.scope = old_scope

    # Resolve elt in comprehension scope
    ctx.scope = comp_scope
    elt = expr.get("elt")
    elt_type: str = "unknown"
    if isinstance(elt, dict):
        elt_type = _resolve_expr(elt, ctx)
    ctx.scope = old_scope

    result: str = "list[" + elt_type + "]"
    expr["resolved_type"] = result
    return result


def _resolve_starred(expr: dict[str, JsonVal], ctx: ResolveContext) -> str:
    value = expr.get("value")
    if isinstance(value, dict):
        vt: str = _resolve_expr(value, ctx)
        expr["resolved_type"] = vt
        return vt
    expr["resolved_type"] = "unknown"
    return "unknown"


# ---------------------------------------------------------------------------
# Statement resolution
# ---------------------------------------------------------------------------

def _resolve_stmt(stmt: dict[str, JsonVal], ctx: ResolveContext) -> None:
    """Resolve types within a statement."""
    kind_val = stmt.get("kind")
    kind: str = str(kind_val) if isinstance(kind_val, str) else ""

    if kind == "FunctionDef":
        _resolve_function_def(stmt, ctx)
    elif kind == "ClassDef":
        _resolve_class_def(stmt, ctx)
    elif kind == "Assign":
        _resolve_assign(stmt, ctx)
    elif kind == "AnnAssign":
        _resolve_ann_assign(stmt, ctx)
    elif kind == "AugAssign":
        _resolve_aug_assign(stmt, ctx)
    elif kind == "Return":
        value = stmt.get("value")
        if isinstance(value, dict):
            _resolve_expr(value, ctx)
    elif kind == "Expr":
        value = stmt.get("value")
        if isinstance(value, dict):
            _resolve_expr(value, ctx)
    elif kind == "If":
        _resolve_if(stmt, ctx)
    elif kind == "While":
        _resolve_while(stmt, ctx)
    elif kind == "For":
        _resolve_for(stmt, ctx)
    elif kind == "ForRange":
        _resolve_for_range(stmt, ctx)
    elif kind == "Try":
        _resolve_try(stmt, ctx)
    elif kind == "With":
        _resolve_with(stmt, ctx)
    elif kind == "Yield":
        value = stmt.get("value")
        if isinstance(value, dict):
            _resolve_expr(value, ctx)
    elif kind == "ImportFrom":
        pass  # Already processed during pre-scan
    elif kind == "Raise":
        exc = stmt.get("exc")
        if isinstance(exc, dict):
            _resolve_expr(exc, ctx)
    elif kind == "Break" or kind == "Continue" or kind == "Pass":
        pass
    elif kind == "Delete":
        targets = stmt.get("targets")
        if isinstance(targets, list):
            for t in targets:
                if isinstance(t, dict):
                    _resolve_expr(t, ctx)
    else:
        # Generic: resolve all child expressions
        _resolve_children(stmt, ctx)


def _resolve_children(node: dict[str, JsonVal], ctx: ResolveContext) -> None:
    """Recursively resolve any child expression nodes."""
    for key in node:
        val = node[key]
        if isinstance(val, dict) and "kind" in val:
            kind_val = val.get("kind")
            if isinstance(kind_val, str):
                # Check if it's an expression or statement
                if kind_val in {"FunctionDef", "ClassDef", "Assign", "AnnAssign", "AugAssign",
                                "Return", "Expr", "If", "While", "For", "ForRange", "Try", "With",
                                "Break", "Continue", "Pass", "Yield", "ImportFrom", "Raise", "Delete"}:
                    _resolve_stmt(val, ctx)
                else:
                    _resolve_expr(val, ctx)
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, dict) and "kind" in item:
                    kind_val2 = item.get("kind")
                    if isinstance(kind_val2, str):
                        if kind_val2 in {"FunctionDef", "ClassDef", "Assign", "AnnAssign",
                                          "AugAssign", "Return", "Expr", "If", "While", "For",
                                          "ForRange", "Try", "With", "Break", "Continue", "Pass",
                                          "Yield", "ImportFrom", "Raise", "Delete"}:
                            _resolve_stmt(item, ctx)
                        else:
                            _resolve_expr(item, ctx)


def _resolve_function_def(stmt: dict[str, JsonVal], ctx: ResolveContext) -> None:
    """Resolve a FunctionDef: normalize types, compute arg_usage, etc."""
    # Normalize arg_types
    arg_types_raw = stmt.get("arg_types")
    arg_types: dict[str, str] = {}
    if isinstance(arg_types_raw, dict):
        for k, v in arg_types_raw.items():
            if isinstance(v, str):
                norm: str = normalize_type(v)
                arg_types[k] = norm
                arg_types_raw[k] = norm

    # Normalize return_type
    ret_raw = stmt.get("return_type")
    ret: str = "unknown"
    if isinstance(ret_raw, str):
        ret = normalize_type(ret_raw)
        stmt["return_type"] = ret

    # Build arg_type_exprs / return_type_expr
    # Class methods get null (type info comes from class definition)
    ate_key_exists: bool = "arg_type_exprs" in stmt
    ate_is_null: bool = ate_key_exists and stmt.get("arg_type_exprs") is None
    if ate_is_null or ctx.in_class:
        pass  # Don't add the field — golden omits it for class methods
    else:
        arg_type_exprs: dict[str, JsonVal] = {}
        for k, t in arg_types.items():
            arg_type_exprs[k] = make_type_expr(t)
        stmt["arg_type_exprs"] = arg_type_exprs

    rte_key_exists: bool = "return_type_expr" in stmt
    rte_is_null: bool = rte_key_exists and stmt.get("return_type_expr") is None
    if rte_is_null or ctx.in_class:
        pass  # Don't add the field — golden omits it for class methods
    else:
        stmt["return_type_expr"] = make_type_expr(ret)

    # Resolve default values
    defaults_raw = stmt.get("arg_defaults")
    if isinstance(defaults_raw, dict):
        for dk, dv in defaults_raw.items():
            if isinstance(dv, dict) and "kind" in dv:
                _resolve_expr(dv, ctx)

    # Compute arg_usage
    arg_order_raw = stmt.get("arg_order")
    arg_order: list[str] = []
    if isinstance(arg_order_raw, list):
        for a in arg_order_raw:
            if isinstance(a, str):
                arg_order.append(a)

    arg_usage: dict[str, str] = _compute_arg_usage(arg_order, stmt)
    stmt["arg_usage"] = arg_usage

    # Create function scope
    fn_scope: Scope = ctx.scope.child()
    for name, typ in arg_types.items():
        fn_scope.define(name, typ)

    # Normalize yield_value_type
    yvt_raw = stmt.get("yield_value_type")
    if isinstance(yvt_raw, str) and yvt_raw != "unknown":
        stmt["yield_value_type"] = normalize_type(yvt_raw)

    # Resolve body in function scope
    old_scope: Scope = ctx.scope
    old_params: set[str] = ctx.current_params
    ctx.scope = fn_scope
    ctx.current_params = set(arg_order)
    body = stmt.get("body")
    if isinstance(body, list):
        for s in body:
            if isinstance(s, dict):
                _resolve_stmt(s, ctx)
    ctx.scope = old_scope
    ctx.current_params = old_params


def _compute_arg_usage(arg_order: list[str], func: dict[str, JsonVal]) -> dict[str, str]:
    """Compute arg_usage: readonly or reassigned for each parameter."""
    usage: dict[str, str] = {}
    for name in arg_order:
        usage[name] = "readonly"

    # Collect reassigned names in function body
    body = func.get("body")
    if isinstance(body, list):
        reassigned: set[str] = set()
        _collect_reassigned(body, reassigned)
        for name in arg_order:
            if name in reassigned:
                usage[name] = "reassigned"

    return usage


def _collect_reassigned(stmts: list[JsonVal], out: set[str]) -> None:
    """Collect variable names that are reassigned in statements."""
    for s in stmts:
        if not isinstance(s, dict):
            continue
        kind = s.get("kind")
        if kind == "Assign":
            targets = s.get("targets")
            if isinstance(targets, list):
                for t in targets:
                    if isinstance(t, dict) and t.get("kind") == "Name":
                        name = t.get("id")
                        if isinstance(name, str):
                            out.add(name)
            else:
                target = s.get("target")
                if isinstance(target, dict) and target.get("kind") == "Name":
                    name2 = target.get("id")
                    if isinstance(name2, str):
                        out.add(name2)
        elif kind == "AugAssign":
            target3 = s.get("target")
            if isinstance(target3, dict) and target3.get("kind") == "Name":
                name3 = target3.get("id")
                if isinstance(name3, str):
                    out.add(name3)
        elif kind == "AnnAssign":
            target4 = s.get("target")
            if isinstance(target4, dict) and target4.get("kind") == "Name":
                name4 = target4.get("id")
                if isinstance(name4, str):
                    out.add(name4)

        # Recurse into blocks
        for block_key in ["body", "orelse", "finalbody", "handlers"]:
            block = s.get(block_key)
            if isinstance(block, list):
                _collect_reassigned(block, out)


def _resolve_class_def(stmt: dict[str, JsonVal], ctx: ResolveContext) -> None:
    """Resolve a ClassDef."""
    name_val = stmt.get("name")
    class_name: str = str(name_val) if isinstance(name_val, str) else ""

    # Add class_storage_hint if not present
    if "class_storage_hint" not in stmt:
        base_val = stmt.get("base")
        has_base: bool = base_val is not None and isinstance(base_val, str) and base_val != ""
        is_dataclass: bool = stmt.get("dataclass") is True
        ft = stmt.get("field_types")
        has_fields: bool = isinstance(ft, dict) and len(ft) > 0
        # Classes with base, @dataclass, or mutable fields use "ref"
        stmt["class_storage_hint"] = "ref" if (has_base or is_dataclass or has_fields) else "value"

    # Normalize field_types
    ft_raw = stmt.get("field_types")
    if isinstance(ft_raw, dict):
        for fk, fv in ft_raw.items():
            if isinstance(fv, str):
                ft_raw[fk] = normalize_type(fv)

    # Collect fields from body
    cls_scope: Scope = ctx.scope.child()
    cls_scope.define("self", class_name)

    # Define class fields in scope
    cls_sig: ClassSig | None = ctx.module_classes.get(class_name)
    if cls_sig is not None:
        for fname, ftype in cls_sig.fields.items():
            cls_scope.define(fname, ftype)

    old_scope: Scope = ctx.scope
    old_in_class: bool = ctx.in_class
    ctx.scope = cls_scope
    ctx.in_class = True
    body = stmt.get("body")
    if isinstance(body, list):
        for item in body:
            if isinstance(item, dict):
                _resolve_stmt(item, ctx)
    ctx.scope = old_scope
    ctx.in_class = old_in_class


def _resolve_assign(stmt: dict[str, JsonVal], ctx: ResolveContext) -> None:
    """Resolve an Assign statement."""
    value = stmt.get("value")
    vt: str = "unknown"
    if isinstance(value, dict):
        vt = _resolve_expr(value, ctx)

    # Resolve target(s) and add decl_type
    # Assign target Name nodes get resolved_type = "unknown" (they're declarations)
    targets = stmt.get("targets")
    if isinstance(targets, list):
        for t in targets:
            if isinstance(t, dict):
                if t.get("kind") == "Name":
                    name_val = t.get("id")
                    if isinstance(name_val, str):
                        ctx.scope.define(name_val, vt)
                        t["resolved_type"] = "unknown"
                elif t.get("kind") == "Tuple":
                    _resolve_expr(t, ctx)
                    # Define tuple element variables
                    elems = t.get("elements")
                    if isinstance(elems, list):
                        tup_types: list[str] = extract_type_args(vt) if vt.startswith("tuple[") else []
                        for idx_t, elem in enumerate(elems):
                            if isinstance(elem, dict) and elem.get("kind") == "Name":
                                elem_name = elem.get("id")
                                if isinstance(elem_name, str):
                                    et: str = tup_types[idx_t] if idx_t < len(tup_types) else "unknown"
                                    ctx.scope.define(elem_name, et)
                else:
                    _resolve_expr(t, ctx)
    else:
        target = stmt.get("target")
        if isinstance(target, dict):
            if target.get("kind") == "Name":
                name_val2 = target.get("id")
                if isinstance(name_val2, str):
                    ctx.scope.define(name_val2, vt)
                    target["resolved_type"] = "unknown"
            else:
                _resolve_expr(target, ctx)

    # Add decl_type only for declarations (declare=true)
    declare_val = stmt.get("declare")
    if declare_val is True:
        if vt != "unknown":
            stmt["decl_type"] = vt
        if isinstance(value, dict):
            stmt["declare_init"] = True
    elif declare_val is False:
        # Re-assignment: decl_type should be null if present
        if "decl_type" in stmt:
            pass  # preserve existing
        # Don't add decl_type for non-declarations


def _resolve_ann_assign(stmt: dict[str, JsonVal], ctx: ResolveContext) -> None:
    """Resolve an AnnAssign (annotated assignment)."""
    # Normalize annotation
    ann_raw = stmt.get("annotation")
    ann_type: str = "unknown"
    if isinstance(ann_raw, str):
        ann_type = normalize_type(ann_raw)
        stmt["annotation"] = ann_type

    # Add annotation_type_expr and decl_type_expr
    stmt["annotation_type_expr"] = make_type_expr(ann_type)
    stmt["decl_type"] = ann_type
    stmt["decl_type_expr"] = make_type_expr(ann_type)

    # Resolve value
    value = stmt.get("value")
    if isinstance(value, dict):
        _resolve_expr(value, ctx)

    # Resolve target
    target = stmt.get("target")
    if isinstance(target, dict) and target.get("kind") == "Name":
        name_val = target.get("id")
        if isinstance(name_val, str):
            ctx.scope.define(name_val, ann_type)
            target["resolved_type"] = ann_type
            target["type_expr"] = make_type_expr(ann_type)


def _resolve_aug_assign(stmt: dict[str, JsonVal], ctx: ResolveContext) -> None:
    """Resolve an AugAssign (augmented assignment like +=)."""
    target = stmt.get("target")
    value = stmt.get("value")

    tt: str = "unknown"
    if isinstance(target, dict):
        tt = _resolve_expr(target, ctx)
        # AugAssign target keeps its resolved_type (it reads the current value)
    if isinstance(value, dict):
        _resolve_expr(value, ctx)

    if tt != "unknown":
        stmt["decl_type"] = tt


def _resolve_if(stmt: dict[str, JsonVal], ctx: ResolveContext) -> None:
    test = stmt.get("test")
    if isinstance(test, dict):
        _resolve_expr(test, ctx)
    body = stmt.get("body")
    if isinstance(body, list):
        for s in body:
            if isinstance(s, dict):
                _resolve_stmt(s, ctx)
    orelse = stmt.get("orelse")
    if isinstance(orelse, list):
        for s in orelse:
            if isinstance(s, dict):
                _resolve_stmt(s, ctx)


def _resolve_while(stmt: dict[str, JsonVal], ctx: ResolveContext) -> None:
    test = stmt.get("test")
    if isinstance(test, dict):
        _resolve_expr(test, ctx)
    body = stmt.get("body")
    if isinstance(body, list):
        for s in body:
            if isinstance(s, dict):
                _resolve_stmt(s, ctx)
    orelse = stmt.get("orelse")
    if isinstance(orelse, list):
        for s in orelse:
            if isinstance(s, dict):
                _resolve_stmt(s, ctx)


def _resolve_for(stmt: dict[str, JsonVal], ctx: ResolveContext) -> None:
    """Resolve a For statement — may convert to ForRange."""
    iter_expr = stmt.get("iter")
    target = stmt.get("target")

    # Check for range() conversion
    if isinstance(iter_expr, dict) and _is_range_call(iter_expr):
        _convert_for_to_forrange(stmt, iter_expr, ctx)
        return

    # Regular for loop
    it: str = "unknown"
    if isinstance(iter_expr, dict):
        it = _resolve_expr(iter_expr, ctx)

    # Determine target type from iterable
    elem_type: str = "unknown"
    if it.startswith("list[") and it.endswith("]"):
        elem_type = it[5:-1]
    elif it.startswith("set[") and it.endswith("]"):
        elem_type = it[4:-1]
    elif it == "str":
        elem_type = "str"
    elif it.startswith("dict[") and it.endswith("]"):
        # Iterating over dict gives keys
        targs: list[str] = extract_type_args(it)
        if len(targs) >= 1:
            elem_type = targs[0]

    # Add iteration metadata
    stmt["target_type"] = elem_type
    iter_mode: str = "static_fastpath"
    if it == "unknown":
        iter_mode = "dynamic"
    stmt["iter_mode"] = iter_mode
    stmt["iter_source_type"] = it
    stmt["iter_element_type"] = elem_type

    # Add iterable traits to iter expression
    if isinstance(iter_expr, dict):
        iter_expr["iterable_trait"] = "yes"
        iter_expr["iter_protocol"] = "static_range"
        iter_expr["iter_element_type"] = elem_type

    # Define loop variable
    if isinstance(target, dict) and target.get("kind") == "Name":
        var_name = target.get("id")
        if isinstance(var_name, str):
            ctx.scope.define(var_name, elem_type)
            target["resolved_type"] = elem_type
    elif isinstance(target, dict):
        _resolve_expr(target, ctx)

    # Resolve body
    body = stmt.get("body")
    if isinstance(body, list):
        for s in body:
            if isinstance(s, dict):
                _resolve_stmt(s, ctx)
    orelse = stmt.get("orelse")
    if isinstance(orelse, list):
        for s in orelse:
            if isinstance(s, dict):
                _resolve_stmt(s, ctx)


def _is_range_call(expr: dict[str, JsonVal]) -> bool:
    """Check if expr is a call to range()."""
    if expr.get("kind") != "Call":
        return False
    func = expr.get("func")
    if not isinstance(func, dict):
        return False
    return func.get("kind") == "Name" and func.get("id") == "range"


def _convert_for_to_forrange(
    stmt: dict[str, JsonVal],
    iter_call: dict[str, JsonVal],
    ctx: ResolveContext,
) -> None:
    """Convert for..in range() to ForRange node."""
    args = iter_call.get("args")
    if not isinstance(args, list):
        return

    # Resolve range arguments
    for a in args:
        if isinstance(a, dict):
            _resolve_expr(a, ctx)

    # Use the range() function name span for synthesized constants
    range_func = iter_call.get("func")
    source_span = range_func.get("source_span", {}) if isinstance(range_func, dict) else iter_call.get("source_span", {})

    if len(args) == 1:
        start_node: dict[str, JsonVal] = {
            "kind": "Constant",
            "source_span": source_span,
            "resolved_type": "int64",
            "casts": [],
            "borrow_kind": "value",
            "repr": "0",
            "value": 0,
        }
        stop_node = args[0] if isinstance(args[0], dict) else {}
        step_node: dict[str, JsonVal] = {
            "kind": "Constant",
            "source_span": source_span,
            "resolved_type": "int64",
            "casts": [],
            "borrow_kind": "value",
            "repr": "1",
            "value": 1,
        }
    elif len(args) == 2:
        start_node = args[0] if isinstance(args[0], dict) else {}
        stop_node = args[1] if isinstance(args[1], dict) else {}
        step_node = {
            "kind": "Constant",
            "source_span": source_span,
            "resolved_type": "int64",
            "casts": [],
            "borrow_kind": "value",
            "repr": "1",
            "value": 1,
        }
    elif len(args) >= 3:
        start_node = args[0] if isinstance(args[0], dict) else {}
        stop_node = args[1] if isinstance(args[1], dict) else {}
        step_node = args[2] if isinstance(args[2], dict) else {}
    else:
        return

    # Determine range_mode
    range_mode: str = "ascending"
    if isinstance(step_node, dict) and step_node.get("kind") == "Constant":
        sv = step_node.get("value")
        if isinstance(sv, int):
            if sv < 0:
                range_mode = "descending"
            elif sv == 1:
                range_mode = "ascending"
            else:
                range_mode = "dynamic"
    elif isinstance(step_node, dict) and step_node.get("kind") == "UnaryOp":
        op = step_node.get("op")
        if op == "USub":
            range_mode = "descending"
        else:
            range_mode = "dynamic"
    else:
        range_mode = "dynamic"

    # Convert the For node to ForRange
    stmt["kind"] = "ForRange"
    stmt["target_type"] = "int64"
    stmt["start"] = start_node
    stmt["stop"] = stop_node
    stmt["step"] = step_node
    stmt["range_mode"] = range_mode

    # Remove iter (no longer needed)
    if "iter" in stmt:
        del stmt["iter"]

    # Define loop variable
    target = stmt.get("target")
    if isinstance(target, dict) and target.get("kind") == "Name":
        var_name = target.get("id")
        if isinstance(var_name, str):
            ctx.scope.define(var_name, "int64")
            target["resolved_type"] = "unknown"  # ForRange target is "unknown" in golden

    # Resolve body
    body = stmt.get("body")
    if isinstance(body, list):
        for s in body:
            if isinstance(s, dict):
                _resolve_stmt(s, ctx)
    orelse = stmt.get("orelse")
    if isinstance(orelse, list):
        for s in orelse:
            if isinstance(s, dict):
                _resolve_stmt(s, ctx)


def _resolve_for_range(stmt: dict[str, JsonVal], ctx: ResolveContext) -> None:
    """Resolve an already-converted ForRange."""
    start = stmt.get("start")
    stop = stmt.get("stop")
    step = stmt.get("step")
    if isinstance(start, dict):
        _resolve_expr(start, ctx)
    if isinstance(stop, dict):
        _resolve_expr(stop, ctx)
    if isinstance(step, dict):
        _resolve_expr(step, ctx)

    target = stmt.get("target")
    if isinstance(target, dict) and target.get("kind") == "Name":
        var_name = target.get("id")
        if isinstance(var_name, str):
            ctx.scope.define(var_name, "int64")

    body = stmt.get("body")
    if isinstance(body, list):
        for s in body:
            if isinstance(s, dict):
                _resolve_stmt(s, ctx)


def _resolve_try(stmt: dict[str, JsonVal], ctx: ResolveContext) -> None:
    body = stmt.get("body")
    if isinstance(body, list):
        for s in body:
            if isinstance(s, dict):
                _resolve_stmt(s, ctx)
    handlers = stmt.get("handlers")
    if isinstance(handlers, list):
        for h in handlers:
            if isinstance(h, dict):
                handler_body = h.get("body")
                if isinstance(handler_body, list):
                    for s in handler_body:
                        if isinstance(s, dict):
                            _resolve_stmt(s, ctx)
    orelse = stmt.get("orelse")
    if isinstance(orelse, list):
        for s in orelse:
            if isinstance(s, dict):
                _resolve_stmt(s, ctx)
    finalbody = stmt.get("finalbody")
    if isinstance(finalbody, list):
        for s in finalbody:
            if isinstance(s, dict):
                _resolve_stmt(s, ctx)


def _resolve_with(stmt: dict[str, JsonVal], ctx: ResolveContext) -> None:
    items = stmt.get("items")
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict):
                context_expr = item.get("context_expr")
                if isinstance(context_expr, dict):
                    _resolve_expr(context_expr, ctx)
    body = stmt.get("body")
    if isinstance(body, list):
        for s in body:
            if isinstance(s, dict):
                _resolve_stmt(s, ctx)


# ---------------------------------------------------------------------------
# Import resolution helpers
# ---------------------------------------------------------------------------

def _build_import_resolution_meta(
    ctx: ResolveContext,
    east1_meta: dict[str, JsonVal],
) -> None:
    """Enhance import_resolution bindings with runtime info."""
    ir = east1_meta.get("import_resolution")
    if not isinstance(ir, dict):
        # Build from import_bindings
        bindings_raw = east1_meta.get("import_bindings")
        if isinstance(bindings_raw, list):
            ir = {"schema_version": 1, "bindings": bindings_raw, "qualified_refs": []}
            east1_meta["import_resolution"] = ir
        else:
            return

    ir["schema_version"] = 1

    bindings = ir.get("bindings")
    if isinstance(bindings, list):
        enhanced: list[JsonVal] = []
        for b in bindings:
            if isinstance(b, dict):
                enhanced.append(_enhance_binding(b, ctx))
        ir["bindings"] = enhanced

    # Add qualified_refs from import_symbols
    qrefs_raw = east1_meta.get("qualified_symbol_refs")
    if isinstance(qrefs_raw, list):
        ir["qualified_refs"] = qrefs_raw

    # Add implicit builtin bindings
    existing_modules: set[str] = set()
    if isinstance(bindings, list):
        for b in bindings:
            if isinstance(b, dict):
                mid = b.get("module_id")
                if isinstance(mid, str):
                    existing_modules.add(mid)

    # Check for additional builtin modules from import_bindings
    ib_raw = east1_meta.get("import_bindings")
    if isinstance(ib_raw, list):
        for ib in ib_raw:
            if isinstance(ib, dict):
                mid2 = ib.get("module_id")
                if isinstance(mid2, str):
                    existing_modules.add(mid2)

    for mod in sorted(ctx.used_builtin_modules):
        if mod not in existing_modules:
            imp_binding: dict[str, JsonVal] = {
                "module_id": mod,
                "export_name": "",
                "local_name": mod,
                "binding_kind": "implicit_builtin",
                "source_file": ctx.source_file,
                "source_line": 0,
                "source_module_id": mod,
                "source_binding_kind": "implicit_builtin",
                "runtime_module_id": mod,
                "runtime_group": ctx.lookup_runtime_module_group(mod),
            }
            final_bindings = ir.get("bindings")
            if isinstance(final_bindings, list):
                final_bindings.append(imp_binding)

            # Also add to import_bindings compatibility list
            ib_compat: dict[str, JsonVal] = {
                "module_id": mod,
                "export_name": "",
                "local_name": mod,
                "binding_kind": "implicit_builtin",
                "source_file": ctx.source_file,
                "source_line": 0,
            }
            ib_list = east1_meta.get("import_bindings")
            if isinstance(ib_list, list):
                ib_list.append(ib_compat)


def _enhance_binding(binding: dict[str, JsonVal], ctx: ResolveContext) -> dict[str, JsonVal]:
    """Enhance a single import binding with runtime resolution info."""
    module_id_val = binding.get("module_id")
    module_id: str = str(module_id_val) if isinstance(module_id_val, str) else ""
    export_name_val = binding.get("export_name")
    export_name: str = str(export_name_val) if isinstance(export_name_val, str) else ""
    binding_kind_val = binding.get("binding_kind")
    binding_kind: str = str(binding_kind_val) if isinstance(binding_kind_val, str) else ""

    canonical: str = ctx.canonical_module_id(module_id)
    runtime_group: str = ctx.lookup_runtime_module_group(canonical)

    binding["source_module_id"] = module_id
    binding["source_export_name"] = export_name
    binding["source_binding_kind"] = binding_kind
    binding["runtime_module_id"] = canonical
    binding["runtime_group"] = runtime_group

    if binding_kind == "module":
        binding["resolved_binding_kind"] = "module"
        return binding

    if binding_kind == "implicit_builtin":
        return binding

    # Symbol binding: look up in runtime index
    sym_doc: dict[str, JsonVal] = ctx.lookup_runtime_symbol_doc(canonical, export_name)
    if len(sym_doc) > 0:
        binding["resolved_binding_kind"] = "symbol"
        binding["runtime_symbol"] = export_name
        kind_v = sym_doc.get("kind")
        if isinstance(kind_v, str) and kind_v != "":
            binding["runtime_symbol_kind"] = kind_v
        dispatch_v = sym_doc.get("dispatch")
        if isinstance(dispatch_v, str) and dispatch_v != "":
            binding["runtime_symbol_dispatch"] = dispatch_v
        stag_v = sym_doc.get("semantic_tag")
        if isinstance(stag_v, str) and stag_v != "":
            binding["runtime_semantic_tag"] = stag_v
        adapter_v = sym_doc.get("call_adapter_kind")
        if isinstance(adapter_v, str) and adapter_v != "":
            binding["runtime_call_adapter_kind"] = adapter_v

    return binding


# ---------------------------------------------------------------------------
# Pre-scan: collect module-level signatures before resolution
# ---------------------------------------------------------------------------

def _prescan_module(doc: dict[str, JsonVal], ctx: ResolveContext) -> None:
    """Pre-scan module body to collect function/class signatures and imports."""
    # Collect renamed symbols
    rs_raw = doc.get("renamed_symbols")
    if isinstance(rs_raw, dict):
        for k, v in rs_raw.items():
            if isinstance(k, str) and isinstance(v, str):
                ctx.renamed_symbols[k] = v

    meta = doc.get("meta")
    if isinstance(meta, dict):
        # Collect import info
        im_raw = meta.get("import_modules")
        if isinstance(im_raw, dict):
            for k, v in im_raw.items():
                if isinstance(v, str):
                    ctx.import_modules[k] = v
        is_raw = meta.get("import_symbols")
        if isinstance(is_raw, dict):
            for k, v in is_raw.items():
                if isinstance(v, dict):
                    mod = v.get("module")
                    nm = v.get("name")
                    ctx.import_symbols[k] = {
                        "module": str(mod) if isinstance(mod, str) else "",
                        "name": str(nm) if isinstance(nm, str) else k,
                    }

    # Collect function and class signatures
    body = doc.get("body")
    if isinstance(body, list):
        for item in body:
            if not isinstance(item, dict):
                continue
            kind = item.get("kind")
            if kind == "FunctionDef":
                sig: FuncSig = _extract_func_sig_for_prescan(item)
                ctx.module_functions[sig.name] = sig
            elif kind == "ClassDef":
                csig: ClassSig = _extract_class_sig_for_prescan(item)
                ctx.module_classes[csig.name] = csig
                # Register class as a scope type
                ctx.scope.define(csig.name, csig.name)

    # Also scan main_guard_body
    mgb = doc.get("main_guard_body")
    if isinstance(mgb, list):
        for item in mgb:
            if not isinstance(item, dict):
                continue
            kind = item.get("kind")
            if kind == "FunctionDef":
                sig2: FuncSig = _extract_func_sig_for_prescan(item)
                ctx.module_functions[sig2.name] = sig2


def _extract_func_sig_for_prescan(node: dict[str, JsonVal]) -> FuncSig:
    """Extract a function signature during prescan (before full resolution)."""
    name_val = node.get("name")
    name: str = str(name_val) if isinstance(name_val, str) else ""
    arg_types_raw = node.get("arg_types")
    arg_types: dict[str, str] = {}
    if isinstance(arg_types_raw, dict):
        for k, v in arg_types_raw.items():
            if isinstance(v, str):
                arg_types[k] = normalize_type(v)
    arg_order_raw = node.get("arg_order")
    arg_names: list[str] = []
    if isinstance(arg_order_raw, list):
        for a in arg_order_raw:
            if isinstance(a, str):
                arg_names.append(a)
    ret_raw = node.get("return_type")
    ret: str = normalize_type(str(ret_raw)) if isinstance(ret_raw, str) else "unknown"
    return FuncSig(name=name, arg_names=arg_names, arg_types=arg_types, return_type=ret, decorators=[])


def _extract_class_sig_for_prescan(node: dict[str, JsonVal]) -> ClassSig:
    """Extract a class signature during prescan."""
    name_val = node.get("name")
    name: str = str(name_val) if isinstance(name_val, str) else ""
    bases_raw = node.get("bases")
    bases: list[str] = []
    if isinstance(bases_raw, list):
        for b in bases_raw:
            if isinstance(b, str):
                bases.append(b)
    methods: dict[str, FuncSig] = {}
    fields: dict[str, str] = {}
    body_raw = node.get("body")
    if isinstance(body_raw, list):
        for item in body_raw:
            if not isinstance(item, dict):
                continue
            kind = item.get("kind")
            if kind == "FunctionDef":
                msig: FuncSig = _extract_func_sig_for_prescan(item)
                msig.is_method = True
                msig.owner_class = name
                methods[msig.name] = msig
            elif kind == "AnnAssign":
                target = item.get("target")
                if isinstance(target, dict) and target.get("kind") == "Name":
                    fld_name = target.get("id")
                    ann = item.get("annotation")
                    if isinstance(fld_name, str) and isinstance(ann, str):
                        fields[fld_name] = normalize_type(ann)
    # Also extract from field_types (top-level ClassDef field from parse)
    ft_raw = node.get("field_types")
    if isinstance(ft_raw, dict):
        for fk, fv in ft_raw.items():
            if isinstance(fk, str) and isinstance(fv, str) and fk not in fields:
                fields[fk] = normalize_type(fv)
    return ClassSig(name=name, bases=bases, methods=methods, fields=fields)


# ---------------------------------------------------------------------------
# Main resolve entry point
# ---------------------------------------------------------------------------

def resolve_east1_to_east2(
    east1_doc: dict[str, JsonVal],
    registry: BuiltinRegistry | None = None,
) -> dict[str, JsonVal]:
    """Resolve a single EAST1 document to EAST2.

    Mutates east1_doc in place and returns it.
    """
    if registry is None:
        registry = BuiltinRegistry()

    source_path_val = east1_doc.get("source_path")
    source_file: str = str(source_path_val) if isinstance(source_path_val, str) else ""

    ctx: ResolveContext = ResolveContext(
        registry=registry,
        scope=Scope(),
        source_file=source_file,
    )

    # Pre-scan: collect module-level info
    _prescan_module(east1_doc, ctx)

    # Resolve body
    body = east1_doc.get("body")
    if isinstance(body, list):
        for stmt in body:
            if isinstance(stmt, dict):
                _resolve_stmt(stmt, ctx)

    # Resolve main_guard_body
    mgb = east1_doc.get("main_guard_body")
    if isinstance(mgb, list):
        for stmt in mgb:
            if isinstance(stmt, dict):
                _resolve_stmt(stmt, ctx)

    # Post-processing: metadata
    east1_doc["east_stage"] = 2
    east1_doc["schema_version"] = 1

    meta = east1_doc.get("meta")
    if isinstance(meta, dict):
        if "parser_backend" not in meta:
            meta["parser_backend"] = "self_hosted"
        if "dispatch_mode" not in meta:
            meta["dispatch_mode"] = "native"
        # Enhance import resolution
        _build_import_resolution_meta(ctx, meta)

    # Normalize field ordering to match golden files
    normalized: JsonVal = normalize_field_order(east1_doc)
    if isinstance(normalized, dict):
        east1_doc.clear()
        east1_doc.update(normalized)

    return east1_doc


def resolve_file(
    input_path: Path,
    registry: BuiltinRegistry | None = None,
) -> ResolveResult:
    """Load and resolve an EAST1 file."""
    text: str = input_path.read_text(encoding="utf-8")
    raw: JsonVal = json.loads(text).raw
    if not isinstance(raw, dict):
        raise ValueError("east1 document must be a JSON object: " + str(input_path))
    east2_doc: dict[str, JsonVal] = raw
    resolve_east1_to_east2(east2_doc, registry=registry)
    source_path_val = east2_doc.get("source_path")
    sp: str = str(source_path_val) if source_path_val is not None else ""
    return ResolveResult(east2_doc=east2_doc, source_path=sp)


def east2_output_path_from_east1(east1_path: Path) -> Path:
    """Derive east2 output path from east1 path.

    a.py.east1 → a.east2 (.py removed)
    """
    name: str = east1_path.name
    if name.endswith(".py.east1"):
        base: str = name[: len(name) - len(".py.east1")]
        return east1_path.parent / (base + ".east2")
    if name.endswith(".east1"):
        base2: str = name[: len(name) - len(".east1")]
        return east1_path.parent / (base2 + ".east2")
    return east1_path.parent / (name + ".east2")
