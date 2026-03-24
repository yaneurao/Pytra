"""Built-in function and container method registry.

Loads signatures from builtins.py.east1, containers.py.east1, and stdlib EAST1 files.
Runtime binding metadata (module, symbol, tag) is extracted from meta.extern_v2
in the EAST1 nodes — no hardcoded tables.

§5 準拠: Any/object 禁止、pytra.std.* のみ使用。
§5.7 準拠: ハードコードテーブル禁止。extern_v2 を正本とする。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pytra.std.json import JsonVal
from pytra.std import json
from pytra.std.pathlib import Path

from toolchain2.resolve.py.type_norm import normalize_type


@dataclass
class ExternV2:
    """Runtime binding metadata from meta.extern_v2."""
    module: str
    symbol: str
    tag: str


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
    extern: ExternV2 | None = None  # from meta.extern_v2


@dataclass
class VarSig:
    """Variable declaration extracted from EAST1."""
    name: str
    var_type: str  # normalized type
    extern: ExternV2 | None = None


@dataclass
class ClassSig:
    """Class signature extracted from EAST1."""
    name: str
    bases: list[str]
    methods: dict[str, FuncSig]
    fields: dict[str, str]  # field_name → normalized type
    template_params: list[str] = field(default_factory=list)
    extern: ExternV2 | None = None


@dataclass
class ModuleSig:
    """Module-level signatures from a stdlib EAST1."""
    module_id: str  # e.g., "math", "pytra.std.math"
    functions: dict[str, FuncSig] = field(default_factory=dict)
    variables: dict[str, VarSig] = field(default_factory=dict)
    classes: dict[str, ClassSig] = field(default_factory=dict)


@dataclass
class BuiltinRegistry:
    """Registry of built-in functions, container methods, and stdlib signatures."""
    # Built-in functions (len, print, str, etc.)
    functions: dict[str, FuncSig] = field(default_factory=dict)
    # Container/type classes (list, dict, str, set, etc.)
    classes: dict[str, ClassSig] = field(default_factory=dict)
    # Stdlib modules (math, time, etc.)
    stdlib_modules: dict[str, ModuleSig] = field(default_factory=dict)

    def lookup_function(self, name: str) -> FuncSig | None:
        return self.functions.get(name)

    def lookup_method(self, owner_base: str, method: str) -> FuncSig | None:
        cls: ClassSig | None = self.classes.get(owner_base)
        if cls is None:
            return None
        return cls.methods.get(method)

    def lookup_stdlib_function(self, module_id: str, name: str) -> FuncSig | None:
        """Look up a function in a stdlib module."""
        mod: ModuleSig | None = self.stdlib_modules.get(module_id)
        if mod is not None:
            f: FuncSig | None = mod.functions.get(name)
            if f is not None:
                return f
        # Try canonical form: "math" → "pytra.std.math"
        canonical: str = "pytra.std." + module_id if "." not in module_id else module_id
        mod2: ModuleSig | None = self.stdlib_modules.get(canonical)
        if mod2 is not None:
            return mod2.functions.get(name)
        return None

    def lookup_stdlib_variable(self, module_id: str, name: str) -> VarSig | None:
        """Look up a variable in a stdlib module."""
        mod: ModuleSig | None = self.stdlib_modules.get(module_id)
        if mod is not None:
            v: VarSig | None = mod.variables.get(name)
            if v is not None:
                return v
        canonical: str = "pytra.std." + module_id if "." not in module_id else module_id
        mod2: ModuleSig | None = self.stdlib_modules.get(canonical)
        if mod2 is not None:
            return mod2.variables.get(name)
        return None

    def is_builtin(self, name: str) -> bool:
        return name in self.functions


# --- Extraction helpers ---

def _extract_extern_v2(node: dict[str, JsonVal]) -> ExternV2 | None:
    """Extract ExternV2 from a node's meta.extern_v2."""
    meta = node.get("meta")
    if not isinstance(meta, dict):
        return None
    ev2 = meta.get("extern_v2")
    if not isinstance(ev2, dict):
        return None
    module_val = ev2.get("module")
    symbol_val = ev2.get("symbol")
    tag_val = ev2.get("tag")
    module: str = str(module_val) if isinstance(module_val, str) else ""
    symbol: str = str(symbol_val) if isinstance(symbol_val, str) else ""
    tag: str = str(tag_val) if isinstance(tag_val, str) else ""
    if module == "" and symbol == "" and tag == "":
        return None
    return ExternV2(module=module, symbol=symbol, tag=tag)


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
    extern: ExternV2 | None = _extract_extern_v2(node)
    return FuncSig(
        name=name,
        arg_names=arg_names,
        arg_types=arg_types,
        return_type=ret,
        decorators=decs,
        is_method=is_method,
        owner_class=owner,
        extern=extern,
    )


def _extract_class_sig(node: dict[str, JsonVal]) -> ClassSig:
    """Extract ClassSig from a ClassDef EAST1 node."""
    name_val = node.get("name")
    name: str = str(name_val) if name_val is not None else ""
    bases_raw = node.get("bases")
    base_raw = node.get("base")
    bases: list[str] = []
    if isinstance(bases_raw, list):
        for b in bases_raw:
            if isinstance(b, str):
                bases.append(b)
    elif isinstance(base_raw, str):
        bases.append(base_raw)
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
                inner: str = d[9:-1] if d.endswith(")") else ""
                for p in inner.split(","):
                    p2: str = p.strip().strip("'\"")
                    if p2 != "":
                        tparams.append(p2)
    extern: ExternV2 | None = _extract_extern_v2(node)
    return ClassSig(name=name, bases=bases, methods=methods, fields=fields,
                    template_params=tparams, extern=extern)


def _load_module_sig(east1_path: Path, module_id: str) -> ModuleSig:
    """Load a module's signatures from an EAST1 file."""
    msig: ModuleSig = ModuleSig(module_id=module_id)
    text: str = east1_path.read_text(encoding="utf-8")
    raw: JsonVal = json.loads(text).raw
    if not isinstance(raw, dict):
        return msig
    body = raw.get("body")
    if not isinstance(body, list):
        return msig
    for item in body:
        if not isinstance(item, dict):
            continue
        kind = item.get("kind")
        if kind == "FunctionDef":
            sig: FuncSig = _extract_func_sig(item, is_method=False, owner="")
            msig.functions[sig.name] = sig
        elif kind == "ClassDef":
            csig: ClassSig = _extract_class_sig(item)
            msig.classes[csig.name] = csig
        elif kind == "AnnAssign":
            target = item.get("target")
            if isinstance(target, dict) and target.get("kind") == "Name":
                var_name_val = target.get("id")
                if isinstance(var_name_val, str):
                    ann_val = item.get("annotation")
                    var_type: str = normalize_type(str(ann_val)) if isinstance(ann_val, str) else "unknown"
                    extern_v: ExternV2 | None = _extract_extern_v2(item)
                    msig.variables[var_name_val] = VarSig(
                        name=var_name_val, var_type=var_type, extern=extern_v,
                    )
    return msig


def load_builtin_registry(
    builtins_east1_path: Path | None = None,
    containers_east1_path: Path | None = None,
    stdlib_dir: Path | None = None,
) -> BuiltinRegistry:
    """Load the builtin registry from EAST1 declaration files.

    Runtime metadata comes from meta.extern_v2 — no hardcoded tables.
    """
    reg: BuiltinRegistry = BuiltinRegistry()

    # Load built-in functions
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

    # Load container classes
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

    # Load stdlib modules
    if stdlib_dir is not None and stdlib_dir.exists():
        # Enumerate all .py.east1 files in stdlib dir
        # Use manual listing since pytra.std.glob might not support this
        import_candidates: list[str] = [
            "math", "time", "sys", "os", "os_path", "glob", "subprocess",
        ]
        for mod_name in import_candidates:
            east1_file: Path = stdlib_dir / (mod_name + ".py.east1")
            if east1_file.exists():
                canonical: str = "pytra.std." + mod_name
                msig: ModuleSig = _load_module_sig(east1_file, canonical)
                reg.stdlib_modules[canonical] = msig
                # Also register with short name
                reg.stdlib_modules[mod_name] = msig

    return reg
