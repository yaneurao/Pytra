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

from toolchain.resolve.py.type_norm import normalize_type


def _split_source_signature_fields(signature: str) -> list[str]:
    parts: list[str] = []
    current = ""
    depth = 0
    for ch in signature:
        if ch == "," and depth == 0:
            field = current.strip()
            if field != "":
                parts.append(field)
            current = ""
            continue
        if ch in "([":
            depth += 1
        elif ch in ")]" and depth > 0:
            depth -= 1
        current += ch
    tail = current.strip()
    if tail != "":
        parts.append(tail)
    return parts


@dataclass
class ExternV2:
    """Runtime binding metadata from meta.extern_v2."""
    module: str
    symbol: str
    tag: str
    kind: str = ""  # "method" for class methods, "" for functions


@dataclass
class FuncSig:
    """Function signature extracted from EAST1."""
    name: str
    arg_names: list[str]
    arg_types: dict[str, str]  # normalized types
    return_type: str  # normalized type
    decorators: list[str]
    vararg_name: str = ""
    vararg_type: str = ""
    is_method: bool = False
    owner_class: str = ""
    extern_v2: ExternV2 | None = None  # from meta.extern_v2
    self_is_mutable: bool = False


@dataclass
class VarSig:
    """Variable declaration extracted from EAST1."""
    name: str
    var_type: str  # normalized type
    extern_v2: ExternV2 | None = None


@dataclass
class ClassSig:
    """Class signature extracted from EAST1."""
    name: str
    bases: list[str]
    methods: dict[str, FuncSig]
    fields: dict[str, str]  # field_name → normalized type
    decorators: list[str] = field(default_factory=list)
    is_trait: bool = False
    implements_traits: list[str] = field(default_factory=list)
    template_params: list[str] = field(default_factory=list)
    extern_v2: ExternV2 | None = None


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

    def lookup_stdlib_class(self, module_id: str, name: str) -> ClassSig | None:
        """Look up a class in a stdlib module."""
        mod: ModuleSig | None = self.stdlib_modules.get(module_id)
        if mod is not None:
            cls: ClassSig | None = mod.classes.get(name)
            if cls is not None:
                return cls
        canonical: str = "pytra.std." + module_id if "." not in module_id else module_id
        mod2: ModuleSig | None = self.stdlib_modules.get(canonical)
        if mod2 is not None:
            return mod2.classes.get(name)
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

    def find_stdlib_class(self, name: str) -> ClassSig | None:
        """Find a stdlib class by simple class name across loaded modules."""
        seen: set[int] = set()
        for mod in self.stdlib_modules.values():
            mod_id = id(mod)
            if mod_id in seen:
                continue
            seen.add(mod_id)
            cls: ClassSig | None = mod.classes.get(name)
            if cls is not None:
                return cls
        return None

    def find_stdlib_class_module(self, cls_sig: ClassSig) -> str:
        """Return the stdlib module id that owns ``cls_sig``, or "" if not found."""
        seen: set[int] = set()
        for module_id, mod in self.stdlib_modules.items():
            mod_key = id(mod)
            if mod_key in seen:
                continue
            seen.add(mod_key)
            for candidate in mod.classes.values():
                if candidate is cls_sig:
                    return module_id
        return ""

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
    kind_val = ev2.get("kind")
    kind: str = str(kind_val) if isinstance(kind_val, str) else ""
    if module == "" and symbol == "" and tag == "":
        return None
    return ExternV2(module=module, symbol=symbol, tag=tag, kind=kind)


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
    vararg_name_val = node.get("vararg_name")
    vararg_name: str = str(vararg_name_val) if isinstance(vararg_name_val, str) else ""
    vararg_type_raw = node.get("vararg_type")
    vararg_type: str = normalize_type(str(vararg_type_raw)) if isinstance(vararg_type_raw, str) else ""
    decs_raw = node.get("decorators")
    decs: list[str] = []
    if isinstance(decs_raw, list):
        for d in decs_raw:
            if isinstance(d, str):
                decs.append(d)
    extern_v2: ExternV2 | None = _extract_extern_v2(node)
    return FuncSig(name=name, arg_names=arg_names, arg_types=arg_types, return_type=ret, decorators=decs, vararg_name=vararg_name, vararg_type=vararg_type, is_method=is_method, owner_class=owner, extern_v2=extern_v2)


def _overlay_container_mutability_from_source(reg: BuiltinRegistry, source_path: Path) -> None:
    """Overlay canonical containers.py signatures onto registry.

    EAST1 declaration files currently normalize away `mut[...]` annotations, so
    the built-in registry supplements method signatures from the source of truth.
    """
    if not source_path.exists():
        return
    current_class = ""
    class_indent = -1
    pending_decorators: list[str] = []
    for raw_line in source_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if stripped == "" or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        if current_class != "" and indent <= class_indent and not stripped.startswith("@"):
            current_class = ""
            class_indent = -1
        if not stripped.startswith("@") and indent <= class_indent:
            pending_decorators = []
        if stripped.startswith("class ") and stripped.endswith(":"):
            class_name = stripped[len("class "):]
            if "(" in class_name:
                class_name = class_name.split("(", 1)[0].strip()
            if ":" in class_name:
                class_name = class_name.split(":", 1)[0].strip()
            current_class = class_name.strip()
            class_indent = indent
            pending_decorators = []
            continue
        if stripped.startswith("@"):
            pending_decorators.append(stripped[1:])
            continue
        if current_class == "" or not stripped.startswith("def "):
            continue
        open_paren = stripped.find("(")
        close_paren = stripped.rfind(")")
        if open_paren <= len("def ") or close_paren <= open_paren:
            continue
        method_name = stripped[len("def "):open_paren].strip()
        signature = stripped[open_paren + 1:close_paren]
        return_type = "None"
        arrow = stripped.find("->", close_paren)
        if arrow >= 0:
            tail = stripped[arrow + 2:]
            colon = tail.find(":")
            if colon >= 0:
                return_type = tail[:colon].strip()
            else:
                return_type = tail.strip()
        if method_name == "":
            continue
        cls = reg.classes.get(current_class)
        if cls is None:
            continue
        arg_names: list[str] = []
        arg_types: dict[str, str] = {}
        self_is_mutable = False
        for field in _split_source_signature_fields(signature):
            field_text = field
            default_pos = field_text.find("=")
            if default_pos >= 0:
                field_text = field_text[:default_pos].strip()
            if field_text == "":
                continue
            if ":" in field_text:
                name_part, type_part = field_text.split(":", 1)
                arg_name = name_part.strip()
                arg_type = normalize_type(type_part.strip())
            else:
                arg_name = field_text.strip()
                arg_type = "unknown"
            if arg_name == "":
                continue
            arg_names.append(arg_name)
            arg_types[arg_name] = arg_type
            if arg_name == "self" and "mut[" in field_text:
                self_is_mutable = True
        method_sig = cls.methods.get(method_name)
        if method_sig is None:
            method_sig = FuncSig(
                name=method_name,
                arg_names=arg_names,
                arg_types=arg_types,
                return_type=normalize_type(return_type),
                decorators=list(pending_decorators),
                is_method=True,
                owner_class=current_class,
                self_is_mutable=self_is_mutable,
            )
            cls.methods[method_name] = method_sig
        else:
            method_sig.arg_names = arg_names
            method_sig.arg_types = arg_types
            method_sig.return_type = normalize_type(return_type)
            method_sig.self_is_mutable = self_is_mutable
            if len(pending_decorators) > 0:
                method_sig.decorators = list(pending_decorators)
        pending_decorators = []


def _overlay_class_sigs_from_source(reg: BuiltinRegistry, source_path: Path) -> None:
    """Overlay @extern-style class signatures from canonical Python source."""
    if not source_path.exists():
        return
    current_class = ""
    current_bases: list[str] = []
    class_indent = -1
    pending_decorators: list[str] = []
    for raw_line in source_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if stripped == "" or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        if current_class != "" and indent <= class_indent and not stripped.startswith("@"):
            current_class = ""
            current_bases = []
            class_indent = -1
        if not stripped.startswith("@") and indent <= class_indent:
            pending_decorators = []
        if stripped.startswith("class ") and stripped.endswith(":"):
            header = stripped[len("class "):-1].strip()
            class_name = header
            bases: list[str] = []
            if "(" in header and header.endswith(")"):
                class_name = header.split("(", 1)[0].strip()
                inner = header[header.find("(") + 1:-1]
                for part in inner.split(","):
                    base_name = part.strip()
                    if base_name != "":
                        bases.append(normalize_type(base_name))
            current_class = class_name.strip()
            current_bases = bases
            class_indent = indent
            cls = reg.classes.get(current_class)
            if cls is None:
                reg.classes[current_class] = ClassSig(
                    name=current_class,
                    bases=list(current_bases),
                    methods={},
                    fields={},
                    decorators=list(pending_decorators),
                )
            else:
                if len(cls.bases) == 0 and len(current_bases) > 0:
                    cls.bases = list(current_bases)
                if len(cls.decorators) == 0 and len(pending_decorators) > 0:
                    cls.decorators = list(pending_decorators)
            pending_decorators = []
            continue
        if stripped.startswith("@"):
            pending_decorators.append(stripped[1:])
            continue
        if current_class == "" or not stripped.startswith("def "):
            continue
        open_paren = stripped.find("(")
        close_paren = stripped.rfind(")")
        if open_paren <= len("def ") or close_paren <= open_paren:
            continue
        method_name = stripped[len("def "):open_paren].strip()
        signature = stripped[open_paren + 1:close_paren]
        return_type = "None"
        arrow = stripped.find("->", close_paren)
        if arrow >= 0:
            tail = stripped[arrow + 2:]
            colon = tail.find(":")
            if colon >= 0:
                return_type = tail[:colon].strip()
            else:
                return_type = tail.strip()
        if method_name == "":
            continue
        cls = reg.classes.get(current_class)
        if cls is None:
            continue
        arg_names: list[str] = []
        arg_types: dict[str, str] = {}
        self_is_mutable = False
        for field in _split_source_signature_fields(signature):
            field_text = field
            default_pos = field_text.find("=")
            if default_pos >= 0:
                field_text = field_text[:default_pos].strip()
            if field_text == "":
                continue
            if ":" in field_text:
                name_part, type_part = field_text.split(":", 1)
                arg_name = name_part.strip()
                arg_type = normalize_type(type_part.strip())
            else:
                arg_name = field_text.strip()
                arg_type = "unknown"
            if arg_name == "":
                continue
            arg_names.append(arg_name)
            arg_types[arg_name] = arg_type
            if arg_name == "self" and "mut[" in field:
                self_is_mutable = True
        method_sig = cls.methods.get(method_name)
        if method_sig is None:
            method_sig = FuncSig(
                name=method_name,
                arg_names=arg_names,
                arg_types=arg_types,
                return_type=normalize_type(return_type),
                decorators=list(pending_decorators),
                is_method=True,
                owner_class=current_class,
                self_is_mutable=self_is_mutable,
            )
            cls.methods[method_name] = method_sig
        else:
            method_sig.arg_names = arg_names
            method_sig.arg_types = arg_types
            method_sig.return_type = normalize_type(return_type)
            method_sig.self_is_mutable = self_is_mutable
            if len(pending_decorators) > 0:
                method_sig.decorators = list(pending_decorators)
        pending_decorators = []


def _default_containers_source_path() -> Path:
    repo_root = Path(__file__).resolve().parents[4]
    return repo_root / "src" / "pytra" / "built_in" / "containers.py"


def _default_io_source_path() -> Path:
    repo_root = Path(__file__).resolve().parents[4]
    return repo_root / "src" / "pytra" / "built_in" / "io.py"


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
    decorators: list[str] = []
    tparams: list[str] = []
    if isinstance(decs_raw, list):
        for d in decs_raw:
            if not isinstance(d, str):
                continue
            decorators.append(d)
            if d.startswith("template("):
                inner = ""
                if d.endswith(")"):
                    inner = d[9:-1]
                for p in inner.split(","):
                    p2 = p.strip()
                    p2 = p2.strip("'")
                    p2 = p2.strip('"')
                    if p2 != "":
                        tparams.append(p2)
    is_trait = "trait" in decorators
    implements_traits: list[str] = []
    for decorator in decorators:
        if not decorator.startswith("implements(") or not decorator.endswith(")"):
            continue
        inner2 = decorator[len("implements("):-1]
        for part in inner2.split(","):
            name2 = part.strip()
            if name2 != "":
                implements_traits.append(name2)
    extern_v2: ExternV2 | None = _extract_extern_v2(node)
    # Fallback: well-known container template params
    if len(tparams) == 0:
        if name == "list" or name == "set" or name == "deque":
            tparams = ["T"]
        elif name == "dict":
            tparams = ["K", "V"]
        elif name == "Iterable":
            tparams = ["T"]
    return ClassSig(name=name, bases=bases, methods=methods, fields=fields, decorators=decorators, is_trait=is_trait, implements_traits=implements_traits, template_params=tparams, extern_v2=extern_v2)


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
                        name=var_name_val, var_type=var_type, extern_v2=extern_v,
                    )
    return msig


def _merge_module_sig(dst: ModuleSig, src: ModuleSig) -> None:
    """Merge src into dst, keeping runtime-source entries authoritative."""
    for name, sig in src.functions.items():
        if name not in dst.functions:
            dst.functions[name] = sig
    for name, sig in src.variables.items():
        if name not in dst.variables:
            dst.variables[name] = sig
    for name, cls in src.classes.items():
        existing: ClassSig | None = dst.classes.get(name)
        if existing is None:
            dst.classes[name] = cls
            continue
        for method_name, method_sig in cls.methods.items():
            if method_name not in existing.methods:
                existing.methods[method_name] = method_sig
        for field_name, field_type in cls.fields.items():
            if field_name not in existing.fields:
                existing.fields[field_name] = field_type
        if len(existing.bases) == 0 and len(cls.bases) > 0:
            existing.bases = cls.bases
        if len(existing.template_params) == 0 and len(cls.template_params) > 0:
            existing.template_params = cls.template_params
        if existing.extern_v2 is None and cls.extern_v2 is not None:
            existing.extern_v2 = cls.extern_v2


def _module_aliases(module_id: str) -> list[str]:
    aliases: list[str] = [module_id]
    for prefix in ("pytra.std.", "pytra.utils.", "pytra.built_in."):
        if module_id.startswith(prefix):
            aliases.append(module_id[len(prefix):])
    return aliases


def _register_stdlib_module(reg: BuiltinRegistry, module_id: str, msig: ModuleSig) -> None:
    canonical: str = module_id if module_id.startswith("pytra.") else "pytra.std." + module_id
    existing: ModuleSig | None = reg.stdlib_modules.get(canonical)
    if existing is not None:
        _merge_module_sig(existing, msig)
        msig = existing
    for alias in _module_aliases(canonical):
        reg.stdlib_modules[alias] = msig
    if canonical.startswith("pytra.built_in."):
        for name, sig in msig.functions.items():
            if name not in reg.functions:
                reg.functions[name] = sig
        for name, cls in msig.classes.items():
            if name not in reg.classes:
                reg.classes[name] = cls


def _retarget_string_method_runtime_modules(reg: BuiltinRegistry) -> None:
    str_cls = reg.classes.get("str")
    string_ops = reg.stdlib_modules.get("pytra.built_in.string_ops")
    if str_cls is None or string_ops is None:
        return

    for method_name, sig in str_cls.methods.items():
        extern_v2 = sig.extern_v2
        if extern_v2 is None or extern_v2.module != "pytra.core.str":
            continue
        if not extern_v2.symbol.startswith("str."):
            continue
        candidate_symbol = "py_" + method_name
        if candidate_symbol not in string_ops.functions:
            continue
        sig.extern_v2 = ExternV2(
            module="pytra.built_in.string_ops",
            symbol=extern_v2.symbol,
            tag=extern_v2.tag,
            kind=extern_v2.kind,
        )


def _candidate_module_dirs(base_dir: Path, group: str) -> list[Path]:
    """Return runtime module directories in merge order for std/utils/built_in overlays."""
    dirs: list[Path] = []
    if base_dir.exists():
        if len(base_dir.parents) >= 4 and base_dir.parents[3].name == "test":
            test_root: Path = base_dir.parents[3]
            repo_root: Path = test_root.parent
            runtime_dir = repo_root / "src" / "runtime" / "east" / group
            pytra_dir = test_root / "pytra" / "east1" / "py" / group
            include_dir = test_root / "include" / "east1" / "py" / group
            candidates = (runtime_dir, pytra_dir, include_dir)
            for candidate in candidates:
                if candidate.exists():
                    dirs.append(candidate)
        else:
            repo_root2 = base_dir.parents[3] if len(base_dir.parents) >= 4 else None
            if group == "std":
                dirs.append(base_dir)
            elif repo_root2 is not None:
                sibling = repo_root2 / "src" / "runtime" / "east" / group
                if sibling.exists():
                    dirs.append(sibling)
    unique: list[Path] = []
    seen: set[str] = set()
    for candidate2 in dirs:
        key: str = str(candidate2)
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate2)
    return unique


def _module_name_from_module_path(module_file: Path, stdlib_dir: Path) -> str:
    rel: Path = module_file.relative_to(stdlib_dir)
    name: str = str(rel)
    if name.endswith(".py.east1"):
        return name[: -len(".py.east1")].replace("/", ".")
    if name.endswith(".east1"):
        return name[: -len(".east1")].replace("/", ".")
    if name.endswith(".east"):
        return name[: -len(".east")].replace("/", ".")
    return rel.stem.replace("/", ".")


def load_builtin_registry(
    builtins_east1_path: Path | None = None,
    containers_east1_path: Path | None = None,
    stdlib_dir: Path | None = None,
    containers_source_path: Path | None = None,
    io_source_path: Path | None = None,
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
        for group, prefix in (
            ("std", "pytra.std."),
            ("utils", "pytra.utils."),
            ("built_in", "pytra.built_in."),
        ):
            for module_dir in _candidate_module_dirs(stdlib_dir, group):
                module_files = sorted(module_dir.glob("*.east"), key=str) + sorted(module_dir.glob("*.east1"), key=str)
                for module_file in module_files:
                    mod_name: str = _module_name_from_module_path(module_file, module_dir)
                    canonical: str = prefix + mod_name
                    msig: ModuleSig = _load_module_sig(module_file, canonical)
                    _register_stdlib_module(reg, canonical, msig)

    _retarget_string_method_runtime_modules(reg)
    if containers_source_path is None:
        containers_source_path = _default_containers_source_path()
    if containers_source_path is not None:
        _overlay_container_mutability_from_source(reg, containers_source_path)
    if io_source_path is None:
        io_source_path = _default_io_source_path()
    if io_source_path is not None:
        _overlay_class_sigs_from_source(reg, io_source_path)

    return reg
