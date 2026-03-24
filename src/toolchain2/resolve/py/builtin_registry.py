"""Built-in function and container method registry.

Loads signatures from builtins.py.east1 and containers.py.east1,
and provides runtime binding metadata for built-in calls.

§5 準拠: Any/object 禁止、pytra.std.* のみ使用。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pytra.std.json import JsonVal
from pytra.std import json
from pytra.std.pathlib import Path

from toolchain2.resolve.py.type_norm import normalize_type


# --- Builtin semantic tags (matches frontend_semantics.py) ---

_BUILTIN_SEMANTIC_TAGS: dict[str, str] = {
    "print": "core.print",
    "len": "core.len",
    "range": "iter.range",
    "zip": "iter.zip",
    "iter": "iter.init",
    "next": "iter.next",
    "reversed": "iter.reversed",
    "enumerate": "iter.enumerate",
    "str": "cast.str",
    "int": "cast.int",
    "float": "cast.float",
    "bool": "cast.bool",
    "ord": "cast.ord",
    "chr": "cast.chr",
    "min": "math.min",
    "max": "math.max",
    "any": "logic.any",
    "all": "logic.all",
    "bytes": "ctor.bytes",
    "bytearray": "ctor.bytearray",
    "list": "ctor.list",
    "set": "ctor.set",
    "dict": "ctor.dict",
    "open": "io.open",
    "Exception": "error.raise_ctor",
    "RuntimeError": "error.raise_ctor",
    "NotImplementedError": "error.raise_ctor",
    "isinstance": "type.isinstance",
    "issubclass": "type.issubclass",
    "cast": "cast.typed",
    "abs": "math.abs",
    "round": "math.round",
    "repr": "cast.repr",
    "sorted": "iter.sorted",
    "sum": "math.sum",
}

# Builtin name → runtime module ID
_BUILTIN_RUNTIME_MODULES: dict[str, str] = {
    "print": "pytra.built_in.io_ops",
    "len": "pytra.core.py_runtime",
    "range": "pytra.built_in.sequence",
    "int": "pytra.core.py_runtime",
    "float": "pytra.core.py_runtime",
    "str": "pytra.core.py_runtime",
    "bool": "pytra.core.py_runtime",
    "abs": "pytra.core.py_runtime",
    "round": "pytra.core.py_runtime",
    "ord": "pytra.built_in.scalar_ops",
    "chr": "pytra.built_in.scalar_ops",
    "isinstance": "pytra.core.py_runtime",
    "issubclass": "pytra.core.py_runtime",
    "min": "pytra.built_in.numeric_ops",
    "max": "pytra.built_in.numeric_ops",
    "sum": "pytra.built_in.numeric_ops",
    "any": "pytra.built_in.predicates",
    "all": "pytra.built_in.predicates",
    "enumerate": "pytra.built_in.iter_ops",
    "zip": "pytra.built_in.zip_ops",
    "reversed": "pytra.built_in.iter_ops",
    "sorted": "pytra.built_in.iter_ops",
    "repr": "pytra.core.py_runtime",
    "open": "pytra.core.io",
}

# Builtin name → runtime symbol name
_BUILTIN_RUNTIME_SYMBOLS: dict[str, str] = {
    "print": "py_print",
    "len": "len",
    "int": "int",
    "float": "float",
    "str": "str",
    "bool": "bool",
    "abs": "py_abs",
    "round": "py_round",
    "ord": "py_ord",
    "chr": "py_chr",
    "isinstance": "isinstance",
    "issubclass": "issubclass",
    "min": "py_min",
    "max": "py_max",
    "sum": "sum",
    "any": "py_any",
    "all": "py_all",
    "enumerate": "py_enumerate_object",
    "zip": "zip",
    "reversed": "py_reversed_object",
    "sorted": "py_sorted",
    "repr": "repr",
    "range": "py_range",
    "open": "open",
}

# Builtin name → runtime_call (py_* function name)
_BUILTIN_RUNTIME_CALLS: dict[str, str] = {
    "print": "py_print",
    "len": "py_len",
    "int": "static_cast",
    "float": "static_cast",
    "str": "py_to_string",
    "bool": "py_to_bool",
    "abs": "py_abs",
    "round": "py_round",
    "ord": "py_ord",
    "chr": "py_chr",
    "min": "py_min",
    "max": "py_max",
    "repr": "py_repr",
}

# Container method → runtime module
_CONTAINER_METHOD_MODULES: dict[str, str] = {
    "list": "pytra.core.list",
    "dict": "pytra.core.dict",
    "set": "pytra.core.set",
    "str": "pytra.core.str",
    "tuple": "pytra.core.py_runtime",
    "deque": "pytra.std.collections",
}

# Specific method overrides: (owner, method) → (runtime_module, runtime_call)
_METHOD_RUNTIME_OVERRIDES: dict[tuple[str, str], tuple[str, str]] = {
    ("str", "join"): ("pytra.built_in.string_ops", "py_join"),
    ("str", "split"): ("pytra.built_in.string_ops", "py_split"),
    ("str", "strip"): ("pytra.built_in.string_ops", "py_strip"),
    ("str", "lstrip"): ("pytra.built_in.string_ops", "py_lstrip"),
    ("str", "rstrip"): ("pytra.built_in.string_ops", "py_rstrip"),
    ("str", "replace"): ("pytra.built_in.string_ops", "py_replace"),
    ("str", "find"): ("pytra.built_in.string_ops", "py_find"),
    ("str", "rfind"): ("pytra.built_in.string_ops", "py_rfind"),
    ("str", "startswith"): ("pytra.built_in.string_ops", "py_startswith"),
    ("str", "endswith"): ("pytra.built_in.string_ops", "py_endswith"),
    ("str", "count"): ("pytra.built_in.string_ops", "py_count"),
    ("str", "upper"): ("pytra.built_in.string_ops", "py_upper"),
    ("str", "lower"): ("pytra.built_in.string_ops", "py_lower"),
    ("str", "isdigit"): ("pytra.built_in.string_ops", "py_isdigit"),
    ("str", "isalpha"): ("pytra.built_in.string_ops", "py_isalpha"),
    ("str", "isalnum"): ("pytra.built_in.string_ops", "py_isalnum"),
    ("str", "isupper"): ("pytra.built_in.string_ops", "py_isupper"),
    ("str", "islower"): ("pytra.built_in.string_ops", "py_islower"),
    ("str", "zfill"): ("pytra.built_in.string_ops", "py_zfill"),
}

def get_method_runtime_override(owner_base: str, method: str) -> tuple[str, str] | None:
    """Get runtime module/call override for specific methods."""
    return _METHOD_RUNTIME_OVERRIDES.get((owner_base, method))

# Implicit builtin modules needed per builtin name
_IMPLICIT_BUILTIN_MODULES: dict[str, str] = {
    "print": "pytra.built_in.io_ops",
    "len": "pytra.core.py_runtime",
    "int": "pytra.built_in.scalar_ops",
    "float": "pytra.built_in.scalar_ops",
    "str": "pytra.built_in.scalar_ops",
    "bool": "pytra.built_in.scalar_ops",
    "ord": "pytra.built_in.scalar_ops",
    "chr": "pytra.built_in.scalar_ops",
    "abs": "pytra.built_in.scalar_ops",
    "round": "pytra.built_in.scalar_ops",
    "min": "pytra.built_in.numeric_ops",
    "max": "pytra.built_in.numeric_ops",
    "sum": "pytra.built_in.numeric_ops",
    "isinstance": "pytra.built_in.scalar_ops",
    "issubclass": "pytra.built_in.scalar_ops",
    "enumerate": "pytra.built_in.iter_ops",
    "zip": "pytra.built_in.zip_ops",
    "reversed": "pytra.built_in.iter_ops",
    "sorted": "pytra.built_in.iter_ops",
    "any": "pytra.built_in.predicates",
    "all": "pytra.built_in.predicates",
    "repr": "pytra.built_in.scalar_ops",
}


@dataclass
class FuncSig:
    """Function signature extracted from EAST1."""
    name: str
    arg_names: list[str]
    arg_types: dict[str, str]  # normalized types
    return_type: str  # normalized type
    decorators: list[str]
    is_method: bool = False
    owner_class: str = ""


@dataclass
class ClassSig:
    """Class signature extracted from EAST1."""
    name: str
    bases: list[str]
    methods: dict[str, FuncSig]
    fields: dict[str, str]  # field_name → normalized type
    template_params: list[str] = field(default_factory=list)


@dataclass
class BuiltinRegistry:
    """Registry of built-in functions, container methods, and stdlib signatures."""
    functions: dict[str, FuncSig] = field(default_factory=dict)
    classes: dict[str, ClassSig] = field(default_factory=dict)

    def lookup_function(self, name: str) -> FuncSig | None:
        return self.functions.get(name)

    def lookup_method(self, owner_base: str, method: str) -> FuncSig | None:
        cls: ClassSig | None = self.classes.get(owner_base)
        if cls is None:
            return None
        return cls.methods.get(method)

    def get_builtin_semantic_tag(self, name: str) -> str:
        return _BUILTIN_SEMANTIC_TAGS.get(name, "")

    def get_builtin_runtime_module(self, name: str) -> str:
        return _BUILTIN_RUNTIME_MODULES.get(name, "")

    def get_builtin_runtime_symbol(self, name: str) -> str:
        return _BUILTIN_RUNTIME_SYMBOLS.get(name, "")

    def get_builtin_runtime_call(self, name: str) -> str:
        return _BUILTIN_RUNTIME_CALLS.get(name, "")

    def get_implicit_builtin_module(self, name: str) -> str:
        return _IMPLICIT_BUILTIN_MODULES.get(name, "")

    def get_container_method_module(self, owner_base: str) -> str:
        return _CONTAINER_METHOD_MODULES.get(owner_base, "")

    def is_builtin(self, name: str) -> bool:
        return name in _BUILTIN_SEMANTIC_TAGS


def _extract_func_sig(node: dict[str, JsonVal], is_method: bool, owner: str) -> FuncSig:
    """Extract FuncSig from a FunctionDef EAST1 node."""
    name_val = node.get("name")
    name: str = str(name_val) if name_val is not None else ""
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
    decs_raw = node.get("decorators")
    decs: list[str] = []
    if isinstance(decs_raw, list):
        for d in decs_raw:
            if isinstance(d, str):
                decs.append(d)
    return FuncSig(
        name=name,
        arg_names=arg_names,
        arg_types=arg_types,
        return_type=ret,
        decorators=decs,
        is_method=is_method,
        owner_class=owner,
    )


def _extract_class_sig(node: dict[str, JsonVal]) -> ClassSig:
    """Extract ClassSig from a ClassDef EAST1 node."""
    name_val = node.get("name")
    name: str = str(name_val) if name_val is not None else ""
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
                sig: FuncSig = _extract_func_sig(item, is_method=True, owner=name)
                methods[sig.name] = sig
            elif kind == "AnnAssign":
                target = item.get("target")
                if isinstance(target, dict) and target.get("kind") == "Name":
                    field_name_val = target.get("id")
                    if isinstance(field_name_val, str):
                        ann_val = item.get("annotation")
                        if isinstance(ann_val, str):
                            fields[field_name_val] = normalize_type(ann_val)
    # Template params from decorators
    decs_raw = node.get("decorators")
    tparams: list[str] = []
    if isinstance(decs_raw, list):
        for d in decs_raw:
            if isinstance(d, str) and d.startswith("template("):
                # e.g. template("T") or template("K", "V")
                inner: str = d[9:-1] if d.endswith(")") else ""
                for p in inner.split(","):
                    p2: str = p.strip().strip("'\"")
                    if p2 != "":
                        tparams.append(p2)
    return ClassSig(name=name, bases=bases, methods=methods, fields=fields, template_params=tparams)


def load_builtin_registry(
    builtins_east1_path: Path | None = None,
    containers_east1_path: Path | None = None,
) -> BuiltinRegistry:
    """Load the builtin registry from EAST1 declaration files."""
    reg: BuiltinRegistry = BuiltinRegistry()

    if builtins_east1_path is not None and builtins_east1_path.exists():
        text: str = builtins_east1_path.read_text(encoding="utf-8")
        raw: JsonVal = json.loads(text).raw
        if isinstance(raw, dict):
            body = raw.get("body")
            if isinstance(body, list):
                for item in body:
                    if not isinstance(item, dict):
                        continue
                    kind = item.get("kind")
                    if kind == "FunctionDef":
                        sig: FuncSig = _extract_func_sig(item, is_method=False, owner="")
                        reg.functions[sig.name] = sig

    if containers_east1_path is not None and containers_east1_path.exists():
        text2: str = containers_east1_path.read_text(encoding="utf-8")
        raw2: JsonVal = json.loads(text2).raw
        if isinstance(raw2, dict):
            body2 = raw2.get("body")
            if isinstance(body2, list):
                for item2 in body2:
                    if not isinstance(item2, dict):
                        continue
                    kind2 = item2.get("kind")
                    if kind2 == "ClassDef":
                        csig: ClassSig = _extract_class_sig(item2)
                        reg.classes[csig.name] = csig

    return reg
