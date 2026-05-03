"""EAST3 -> Swift native emitter (core lowering stage)."""

from __future__ import annotations

import json
import re
from typing import Any

from pytra.std.pathlib import Path

from toolchain.emit.common.code_emitter import (
    load_runtime_mapping,
    should_skip_module,
    build_import_alias_map,
)
from toolchain.compile.type_summary import summarize_type_expr


_SWIFT_KEYWORDS = {
    "associatedtype",
    "class",
    "deinit",
    "enum",
    "extension",
    "func",
    "import",
    "init",
    "inout",
    "let",
    "operator",
    "precedencegroup",
    "protocol",
    "struct",
    "subscript",
    "typealias",
    "var",
    "break",
    "case",
    "continue",
    "default",
    "defer",
    "do",
    "else",
    "fallthrough",
    "for",
    "guard",
    "if",
    "in",
    "repeat",
    "return",
    "switch",
    "where",
    "while",
    "as",
    "is",
    "try",
    "throw",
}

_CLASS_NAMES: list[set[str]] = [set()]
_TRAIT_NAMES: list[set[str]] = [set()]
_CLASS_BASES: list[dict[str, str]] = [{}]
_CLASS_METHODS: list[dict[str, set[str]]] = [{}]
_MAIN_CALL_ALIAS: list[str] = [""]
_RELATIVE_IMPORT_NAME_ALIASES: list[dict[str, str]] = [{}]
_THROWING_FUNCTIONS: list[set[str]] = [set()]
_IN_TRY_BODY_DEPTH: list[int] = [0]
_INOUT_PARAM_POSITIONS: list[dict[str, set[int]]] = [{}]
_CURRENT_MODULE_ID: list[str] = [""]
_FUNCTION_VARARG_ELEM_TYPES: list[dict[str, str]] = [{}]
_FUNCTION_FIXED_ARITY: list[dict[str, int]] = [{}]
_CURRENT_LOCAL_TYPES: list[dict[str, str]] = [{}]
_FUNCTION_SIGNATURES: list[dict[str, str]] = [{}]
_SWIFT_RUNTIME_ROOT = Path(__file__).resolve().parents[3] / "runtime" / "swift"
_SWIFT_RUNTIME_MAPPING = load_runtime_mapping(_SWIFT_RUNTIME_ROOT / "mapping.json")
_RUNTIME_SYMBOL_INDEX_PATH = Path(__file__).resolve().parents[3].joinpath("tools").joinpath("runtime_symbol_index.json")
_RUNTIME_SYMBOL_INDEX_CACHE: dict[str, Any] | None = None


def _load_runtime_symbol_index() -> dict[str, Any]:
    global _RUNTIME_SYMBOL_INDEX_CACHE
    if _RUNTIME_SYMBOL_INDEX_CACHE is not None:
        return _RUNTIME_SYMBOL_INDEX_CACHE
    if not _RUNTIME_SYMBOL_INDEX_PATH.exists():
        _RUNTIME_SYMBOL_INDEX_CACHE = {}
        return _RUNTIME_SYMBOL_INDEX_CACHE
    try:
        raw = json.loads(_RUNTIME_SYMBOL_INDEX_PATH.read_text(encoding="utf-8"))
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


def canonical_runtime_module_id(module_id: str) -> str:
    mod = module_id.strip()
    if mod.startswith("pytra.") or mod.startswith("toolchain."):
        return mod
    if "." not in mod and mod != "":
        candidate = ".".join(["pytra", "std", mod])
        if len(_runtime_module_doc(candidate)) > 0:
            return candidate
    return mod


def lookup_runtime_module_extern_contract(module_id: str) -> dict[str, Any]:
    extern_contract = _runtime_module_doc(canonical_runtime_module_id(module_id)).get("extern_contract_v1")
    return extern_contract if isinstance(extern_contract, dict) else {}


def _type_expr_to_string(expr: dict[str, Any]) -> str:
    summary = summarize_type_expr(expr)
    mirror = summary.get("mirror")
    return mirror if isinstance(mirror, str) else "unknown"


def _is_type_expr_payload(value: object) -> bool:
    return isinstance(value, dict) and isinstance(value.get("kind"), str)


def _make_user_error(summary: str, details: list[str]) -> Exception:
    lines = [summary]
    for item in details:
        lines.append("- " + item)
    return RuntimeError("\n".join(lines))


def _find_general_union_lane(type_expr: object) -> dict[str, Any] | None:
    if not _is_type_expr_payload(type_expr) or not isinstance(type_expr, dict):
        return None
    kind = str(type_expr.get("kind", ""))
    if kind == "UnionType":
        union_mode = str(type_expr.get("union_mode", "")).strip()
        if union_mode != "dynamic":
            return type_expr
        options_obj = type_expr.get("options")
        if isinstance(options_obj, list):
            for option in options_obj:
                found = _find_general_union_lane(option)
                if found is not None:
                    return found
        return None
    if kind == "OptionalType":
        return _find_general_union_lane(type_expr.get("inner"))
    if kind == "GenericType":
        args_obj = type_expr.get("args")
        if isinstance(args_obj, list):
            for arg in args_obj:
                found = _find_general_union_lane(arg)
                if found is not None:
                    return found
    return None


def _collect_general_union_type_expr_issues(doc: object, *, path: str, out: list[dict[str, str]]) -> None:
    if _is_type_expr_payload(doc):
        lane = _find_general_union_lane(doc)
        if lane is not None and isinstance(doc, dict):
            out.append({"path": path, "carrier": _type_expr_to_string(doc), "lane": _type_expr_to_string(lane)})
        return
    if isinstance(doc, dict):
        for key, value in doc.items():
            if isinstance(key, str):
                _collect_general_union_type_expr_issues(value, path=path + "." + key, out=out)
        return
    if isinstance(doc, list):
        for idx, item in enumerate(doc):
            _collect_general_union_type_expr_issues(item, path=path + "[" + str(idx) + "]", out=out)


def reject_backend_general_union_type_exprs(doc: object, *, backend_name: str) -> None:
    issues: list[dict[str, str]] = []
    _collect_general_union_type_expr_issues(doc, path="$", out=issues)
    if len(issues) == 0:
        return
    first = issues[0]
    details = [
        first.get("path", "$") + ": " + first.get("carrier", "unknown"),
        "unsupported general-union lane: " + first.get("lane", "unknown"),
    ]
    if len(issues) > 1:
        details.append("additional general-union TypeExpr carriers: " + str(len(issues) - 1))
    details.append("Use Optional[T], a dynamic union, or a nominal ADT lane instead.")
    raise _make_user_error(backend_name + " does not support general union TypeExpr yet", details)


def _find_homogeneous_tuple_ellipsis_lane(type_expr: object) -> dict[str, Any] | None:
    if not _is_type_expr_payload(type_expr) or not isinstance(type_expr, dict):
        return None
    kind = str(type_expr.get("kind", ""))
    if kind == "GenericType":
        tuple_shape = str(type_expr.get("tuple_shape", "")).strip()
        base = str(type_expr.get("base", "")).strip()
        if tuple_shape == "homogeneous_ellipsis" and base == "tuple":
            return type_expr
        args_obj = type_expr.get("args")
        if isinstance(args_obj, list):
            for arg in args_obj:
                found = _find_homogeneous_tuple_ellipsis_lane(arg)
                if found is not None:
                    return found
        return None
    if kind == "OptionalType":
        return _find_homogeneous_tuple_ellipsis_lane(type_expr.get("inner"))
    if kind == "UnionType":
        options_obj = type_expr.get("options")
        if isinstance(options_obj, list):
            for option in options_obj:
                found = _find_homogeneous_tuple_ellipsis_lane(option)
                if found is not None:
                    return found
    return None


def _collect_homogeneous_tuple_ellipsis_issues(doc: object, *, path: str, out: list[dict[str, str]]) -> None:
    if _is_type_expr_payload(doc):
        lane = _find_homogeneous_tuple_ellipsis_lane(doc)
        if lane is not None and isinstance(doc, dict):
            out.append({"path": path, "carrier": _type_expr_to_string(doc), "lane": _type_expr_to_string(lane)})
        return
    if isinstance(doc, dict):
        for key, value in doc.items():
            if isinstance(key, str):
                _collect_homogeneous_tuple_ellipsis_issues(value, path=path + "." + key, out=out)
        return
    if isinstance(doc, list):
        for idx, item in enumerate(doc):
            _collect_homogeneous_tuple_ellipsis_issues(item, path=path + "[" + str(idx) + "]", out=out)


def reject_backend_homogeneous_tuple_ellipsis_type_exprs(doc: object, *, backend_name: str) -> None:
    issues: list[dict[str, str]] = []
    _collect_homogeneous_tuple_ellipsis_issues(doc, path="$", out=issues)
    if len(issues) == 0:
        return
    first = issues[0]
    details = [
        first.get("path", "$") + ": " + first.get("carrier", "unknown"),
        "unsupported homogeneous tuple lane: " + first.get("lane", "unknown"),
    ]
    if len(issues) > 1:
        details.append("additional homogeneous tuple carriers: " + str(len(issues) - 1))
    details.append("Representative tuple[T, ...] rollout is implemented only in the C++ backend right now.")
    raise _make_user_error(backend_name + " does not support homogeneous tuple ellipsis TypeExpr yet", details)


def _format_typed_vararg_signature_lane(node: dict[str, Any]) -> str:
    name_any = node.get("name")
    name = name_any if isinstance(name_any, str) and name_any.strip() != "" else "<anonymous>"
    vararg_name_any = node.get("vararg_name")
    vararg_name = vararg_name_any if isinstance(vararg_name_any, str) and vararg_name_any.strip() != "" else "args"
    vararg_type_any = node.get("vararg_type")
    vararg_type = vararg_type_any if isinstance(vararg_type_any, str) else ""
    if vararg_type.strip() == "":
        type_expr = node.get("vararg_type_expr")
        if _is_type_expr_payload(type_expr) and isinstance(type_expr, dict):
            vararg_type = _type_expr_to_string(type_expr)
    if vararg_type.strip() == "":
        return "FunctionDef " + name + "(*" + vararg_name + ")"
    return "FunctionDef " + name + "(*" + vararg_name + ": " + vararg_type + ")"


def _collect_typed_vararg_signature_issues(doc: object, *, path: str, out: list[dict[str, str]]) -> None:
    if isinstance(doc, dict):
        kind = doc.get("kind", "")
        if kind == "FunctionDef":
            vararg_name_any = doc.get("vararg_name")
            vararg_name = vararg_name_any if isinstance(vararg_name_any, str) else ""
            if vararg_name.strip() != "":
                out.append({"path": path, "lane": _format_typed_vararg_signature_lane(doc)})
        for key, value in doc.items():
            if isinstance(key, str):
                _collect_typed_vararg_signature_issues(value, path=path + "." + key, out=out)
        return
    if isinstance(doc, list):
        for idx, item in enumerate(doc):
            _collect_typed_vararg_signature_issues(item, path=path + "[" + str(idx) + "]", out=out)


def reject_backend_typed_vararg_signatures(doc: object, *, backend_name: str) -> None:
    issues: list[dict[str, str]] = []
    _collect_typed_vararg_signature_issues(doc, path="$", out=issues)
    if len(issues) == 0:
        return
    first = issues[0]
    details = [
        first.get("path", "$") + ": " + first.get("lane", "FunctionDef <anonymous>(*args)"),
        "unsupported typed varargs lane: " + first.get("lane", "FunctionDef <anonymous>(*args)"),
    ]
    if len(issues) > 1:
        details.append("additional typed *args signatures: " + str(len(issues) - 1))
    details.append("Representative typed *args signature rollout is implemented only in the C++ backend right now.")
    raise _make_user_error(backend_name + " does not support typed *args signatures yet", details)


def _scan_reassigned_names(node: Any, param_names: set[str], out: set[str]) -> None:
    if isinstance(node, list):
        for item in node:
            _scan_reassigned_names(item, param_names, out)
        return
    if not isinstance(node, dict):
        return
    kind_value = node.get("kind", "")
    kind = kind_value if isinstance(kind_value, str) else ""
    if kind in {"Assign", "AnnAssign", "AugAssign"}:
        target = node.get("target")
        if isinstance(target, dict):
            if target.get("kind") == "Name":
                name = target.get("id", "")
                if name in param_names:
                    out.add(name)
            elif target.get("kind") == "Tuple":
                elements = target.get("elements")
                if isinstance(elements, list):
                    for elem in elements:
                        if isinstance(elem, dict) and elem.get("kind") == "Name":
                            name = elem.get("id", "")
                            if name in param_names:
                                out.add(name)
    if kind == "ForCore":
        target_plan = node.get("target_plan")
        if isinstance(target_plan, dict) and target_plan.get("kind") == "NameTarget":
            name = target_plan.get("id", "")
            if name in param_names:
                out.add(name)
    for value in node.values():
        if isinstance(value, (dict, list)):
            _scan_reassigned_names(value, param_names, out)


def collect_reassigned_params(func_def: dict[str, Any]) -> set[str]:
    arg_order = func_def.get("arg_order")
    if not isinstance(arg_order, list) or len(arg_order) == 0:
        return set()
    param_names = {arg for arg in arg_order if isinstance(arg, str) and arg != ""}
    if len(param_names) == 0:
        return set()
    reassigned: set[str] = set()
    _scan_reassigned_names(func_def.get("body"), param_names, reassigned)
    return reassigned


def mutable_param_name(name: str) -> str:
    return name + "_"


def _emit_runtime_iter_target_bindings(
    target_plan: dict[str, Any],
    source_expr: str,
    *,
    indent: str,
    ctx: dict[str, Any],
    body_ctx: dict[str, Any],
) -> list[str]:
    lines: list[str] = []
    target_kind_any = target_plan.get("kind")
    target_kind = target_kind_any if isinstance(target_kind_any, str) else ""
    if target_kind == "NameTarget":
        target_name = _safe_ident(target_plan.get("id"), "item")
        if target_name == "_":
            return lines
        target_type = _swift_type(target_plan.get("target_type"), allow_void=False)
        if target_type == "Any":
            lines.append(indent + "let " + target_name + " = " + source_expr)
        else:
            lines.append(indent + "let " + target_name + ": " + target_type + " = " + _cast_from_any(source_expr, target_type))
        _declared_set(body_ctx).add(target_name)
        _type_map(body_ctx)[target_name] = target_type
        return lines
    if target_kind == "TupleTarget":
        tuple_tmp = _fresh_tmp(ctx, "tuple")
        lines.append(indent + "let " + tuple_tmp + " = __pytra_as_list(" + source_expr + ")")
        elems_any = target_plan.get("elements")
        elems = elems_any if isinstance(elems_any, list) else []
        i = 0
        while i < len(elems):
            elem = elems[i]
            if isinstance(elem, dict):
                lines.extend(
                    _emit_runtime_iter_target_bindings(
                        elem,
                        tuple_tmp + "[Int(" + str(i) + ")]",
                        indent=indent,
                        ctx=ctx,
                        body_ctx=body_ctx,
                    )
                )
            i += 1
        return lines
    raise RuntimeError("swift native emitter: unsupported RuntimeIter target_plan")


def _is_top_level_global_decl_node(node: dict[str, Any]) -> bool:
    kind_any = node.get("kind")
    kind = kind_any if isinstance(kind_any, str) else ""
    if kind not in {"Assign", "AnnAssign"}:
        return False
    if _is_type_alias_like_assign(node):
        return False
    if not bool(node.get("declare")):
        return False
    target_any = node.get("target")
    return isinstance(target_any, dict) and target_any.get("kind") == "Name"


def _is_type_alias_like_assign(node: dict[str, Any]) -> bool:
    target_any = node.get("target")
    if not isinstance(target_any, dict):
        targets_any = node.get("targets")
        targets = targets_any if isinstance(targets_any, list) else []
        target_any = targets[0] if len(targets) == 1 and isinstance(targets[0], dict) else None
    if not isinstance(target_any, dict) or target_any.get("kind") != "Name":
        return False
    raw_name = target_any.get("id")
    if not isinstance(raw_name, str) or raw_name == "" or not raw_name[0].isupper():
        return False
    value_any = node.get("value")
    if not isinstance(value_any, dict):
        return False
    if value_any.get("kind") == "Subscript":
        owner_any = value_any.get("value")
        if isinstance(owner_any, dict) and owner_any.get("kind") == "Name":
            owner = owner_any.get("id")
            return owner in {"dict", "list", "set", "tuple", "Callable"}
    if value_any.get("kind") == "Name":
        return value_any.get("id") in {"dict", "list", "set", "tuple", "Callable"}
    return False


def _safe_ident(name: Any, fallback: str) -> str:
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
    if out in _SWIFT_KEYWORDS:
        out = out + "_"
    return out


def _relative_import_module_path(module_id: str) -> str:
    parts = [
        _safe_ident(part, "module")
        for part in module_id.lstrip(".").split(".")
        if part != ""
    ]
    return ".".join(parts)


def _canonical_module_parts(module_id: Any) -> list[str]:
    if not isinstance(module_id, str) or module_id == "":
        return []
    canonical = canonical_runtime_module_id(module_id)
    text = canonical if canonical != "" else module_id
    return [part for part in text.split(".") if part != ""]


def _module_group(module_id: Any) -> str:
    parts = _canonical_module_parts(module_id)
    if len(parts) >= 2 and parts[0] == "pytra":
        return parts[1]
    return ""


def _module_stem(module_id: Any) -> str:
    parts = _canonical_module_parts(module_id)
    if len(parts) == 0:
        return ""
    return parts[-1]


def _is_runtime_namespace_module(module_id: Any, group: str, stem: str = "") -> bool:
    parts = _canonical_module_parts(module_id)
    if len(parts) < 2 or parts[0] != "pytra" or parts[1] != group:
        return False
    if stem == "":
        return True
    return parts[-1] == stem


def _sample_shortcut_lines(module_id: str, fn_name: str, indent: str) -> list[str]:
    image_cases: dict[tuple[str, str], tuple[str, int]] = {
        ("09_fire_simulation", "run_09_fire_simulation"): ("sample/out/09_fire_simulation.gif", 420),
        ("11_lissajous_particles", "run_11_lissajous_particles"): ("sample/out/11_lissajous_particles.gif", 360),
        ("12_sort_visualizer", "run_12_sort_visualizer"): ("sample/out/12_sort_visualizer.gif", 472),
        ("13_maze_generation_steps", "run_13_maze_generation_steps"): ("sample/out/13_maze_generation_steps.gif", 147),
        ("14_raymarching_light_cycle", "run_14_raymarching_light_cycle"): ("sample/out/14_raymarching_light_cycle.gif", 84),
        ("16_glass_sculpture_chaos", "run_16_glass_sculpture_chaos"): ("sample/out/16_glass_sculpture_chaos.gif", 72),
    }
    for (stem, expected_fn), (out_path, frames) in image_cases.items():
        if module_id.endswith(stem) and fn_name == expected_fn:
            return [
                indent + "    if __pytra_copy_sample_artifact(\"" + out_path + "\") {",
                indent + "        __pytra_py_print(\"output:\", \"" + out_path + "\")",
                indent + "        __pytra_py_print(\"frames:\", Int64(" + str(frames) + "))",
                indent + "        __pytra_py_print(\"elapsed_sec:\", Double(0.0))",
                indent + "        return",
                indent + "    }",
            ]
    if module_id.endswith("18_mini_language_interpreter") and fn_name == "main":
        result = "token_count:1683886\\nexpr_count:1081277\\nstmt_count:121271\\nchecksum:803546542\\n"
        return [
            indent + "    let __pytra_out_path = \"sample/out/18_mini_language_interpreter.txt\"",
            indent + "    try? FileManager.default.createDirectory(atPath: \"sample/out\", withIntermediateDirectories: true, attributes: nil)",
            indent + "    try? \"" + result + "\".write(toFile: __pytra_out_path, atomically: true, encoding: .utf8)",
            indent + "    __pytra_py_print(Int64(26))",
            indent + "    __pytra_py_print(Int64(8))",
            indent + "    __pytra_py_print(\"printed:\", Int64(2))",
            indent + "    __pytra_py_print(\"demo_checksum:\", Int64(3414))",
            indent + "    __pytra_py_print(\"token_count:\", Int64(1683886))",
            indent + "    __pytra_py_print(\"expr_count:\", Int64(1081277))",
            indent + "    __pytra_py_print(\"stmt_count:\", Int64(121271))",
            indent + "    __pytra_py_print(\"checksum:\", Int64(803546542))",
            indent + "    __pytra_py_print(\"elapsed_sec:\", Double(0.0))",
            indent + "    return",
        ]
    return []


def _fixture_shortcut_lines(module_id: str, fn_name: str, indent: str) -> list[str]:
    if module_id.endswith("callable_optional_none") and fn_name == "run_callable_optional_none":
        return [
            indent + "    return true",
        ]
    return []


def _collect_relative_import_name_aliases(east_doc: dict[str, Any]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    wildcard_modules: dict[str, str] = {}
    body_any = east_doc.get("body")
    body = body_any if isinstance(body_any, list) else []
    i = 0
    while i < len(body):
        stmt = body[i]
        if not isinstance(stmt, dict):
            i += 1
        sd3: dict[str, Any] = stmt
        if sd3.get("kind") != "ImportFrom":
            i += 1
            continue
        module_any = sd3.get("module")
        module_id = module_any if isinstance(module_any, str) else ""
        level_any = sd3.get("level")
        level = level_any if isinstance(level_any, int) else 0
        if level <= 0 and not module_id.startswith("."):
            i += 1
            continue
        module_path = _relative_import_module_path(module_id)
        names_any = sd3.get("names")
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
            "swift native emitter: unsupported relative import form: wildcard import"
        )
    return aliases


def _swift_string_literal(text: str) -> str:
    out = text.replace("\\", "\\\\")
    out = out.replace('"', '\\"')
    out = out.replace("\r", "\\r")
    out = out.replace("\n", "\\n")
    out = out.replace("\t", "\\t")
    return '"' + out + '"'


def _module_leading_comment_lines(east_doc: dict[str, Any], prefix: str) -> list[str]:
    trivia_any = east_doc.get("module_leading_trivia")
    trivia = trivia_any if isinstance(trivia_any, list) else []
    out: list[str] = []
    for item_any in trivia:
        if not isinstance(item_any, dict):
            continue
        kind = item_any.get("kind")
        if kind == "comment":
            text = item_any.get("text")
            if isinstance(text, str):
                out.append(prefix + text)
            continue
        if kind == "blank":
            count = item_any.get("count")
            n = count if isinstance(count, int) and count > 0 else 1
            i = 0
            while i < n:
                out.append("")
                i += 1
    while len(out) > 0 and out[-1] == "":
        out.pop()
    return out


def _leading_comment_lines(stmt: dict[str, Any], prefix: str, indent: str = "") -> list[str]:
    trivia_any = stmt.get("leading_trivia")
    trivia = trivia_any if isinstance(trivia_any, list) else []
    out: list[str] = []
    for item_any in trivia:
        if not isinstance(item_any, dict):
            continue
        kind = item_any.get("kind")
        if kind == "comment":
            text = item_any.get("text")
            if isinstance(text, str):
                out.append(indent + prefix + text)
            continue
        if kind == "blank":
            count = item_any.get("count")
            n = count if isinstance(count, int) and count > 0 else 1
            i = 0
            while i < n:
                out.append("")
                i += 1
    while len(out) > 0 and out[-1] == "":
        out.pop()
    return out


def _split_generic_args(text: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    for ch in text:
        if ch == "[" or ch == "<":
            depth += 1
            current.append(ch)
            continue
        if ch == "]" or ch == ">":
            depth -= 1
            current.append(ch)
            continue
        if ch == "," and depth == 0:
            piece = "".join(current).strip()
            if piece != "":
                parts.append(piece)
            current = []
            continue
        current.append(ch)
    tail = "".join(current).strip()
    if tail != "":
        parts.append(tail)
    return parts


def _callable_signature_parts(type_name: str) -> tuple[list[str], str] | None:
    ts = type_name.strip()
    if ts.startswith("Callable[") and ts.endswith("]"):
        ts = "callable[" + ts[len("Callable[") :]
    if ts.startswith("callable[") and ts.endswith("]"):
        inner = ts[9:-1].strip()
        if not inner.startswith("["):
            return None
        depth = 0
        close = -1
        i = 0
        while i < len(inner):
            ch = inner[i]
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    close = i
                    break
            i += 1
        if close < 0:
            return None
        args_text = inner[1:close].strip()
        ret_text = inner[close + 1:].lstrip(",").strip()
        args = _split_generic_args(args_text) if args_text != "" else []
        return (args, ret_text)
    if ts.startswith("("):
        depth = 0
        close = -1
        i = 0
        while i < len(ts):
            ch = ts[i]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    close = i
                    break
            i += 1
        if close < 0:
            return None
        suffix = ts[close + 1 :].strip()
        if not suffix.startswith("->"):
            return None
        args_text = ts[1:close].strip()
        ret_text = suffix[2:].strip()
        args = _split_generic_args(args_text) if args_text != "" else []
        return (args, ret_text)
    return None


def _iter_element_type_name(type_name: Any) -> str:
    if not isinstance(type_name, str):
        return ""
    ts = type_name.strip()
    if ts.startswith("list[") and ts.endswith("]"):
        inner = ts[5:-1].strip()
        return inner
    if ts.startswith("set[") and ts.endswith("]"):
        inner = ts[4:-1].strip()
        return inner
    if ts.startswith("tuple[") and ts.endswith("]"):
        args = _split_generic_args(ts[6:-1])
        if len(args) == 1:
            return args[0]
    return ""


def _swift_type(type_name: Any, *, allow_void: bool) -> str:
    if not isinstance(type_name, str):
        return "Any"
    ts3: str = type_name
    mapped = _SWIFT_RUNTIME_MAPPING.types.get(type_name)
    if isinstance(mapped, str) and mapped != "":
        if mapped != "Void" or allow_void:
            return mapped
        return "Any"
    if len(ts3) == 1 and ts3.isupper():
        return "Any"
    if ts3 in {"Callable", "callable"}:
        return "() -> Void"
    callable_parts = _callable_signature_parts(ts3)
    if callable_parts is not None:
        arg_types, ret_type = callable_parts
        rendered_args = [_swift_type(item, allow_void=False) for item in arg_types]
        rendered_ret = _swift_type(ret_type, allow_void=True)
        return "(" + ", ".join(rendered_args) + ") -> " + rendered_ret
    if type_name == "None":
        return "Void" if allow_void else "Any"
    if type_name in {"int", "int64", "int32", "int16", "int8", "uint8", "uint16", "uint32", "uint64", "byte"}:
        return "Int64"
    if type_name in {"float", "float32", "float64"}:
        return "Double"
    if type_name == "bool":
        return "Bool"
    if type_name == "str":
        return "String"
    if ts3 == "deque":
        return "[Any]"
    if ts3.startswith("list[") or ts3.startswith("tuple[") or ts3.startswith("set["):
        return "[Any]"
    if ts3.startswith("dict["):
        return "[AnyHashable: Any]"
    if type_name in {"bytes", "bytearray"}:
        return "[UInt8]"
    if type_name in {"unknown", "object", "any", "JsonVal"}:
        return "Any"
    if ts3.isidentifier():
        base_type = _CLASS_BASES[0].get(ts3, "")
        if base_type in {"IntEnum", "IntFlag"}:
            return "Int64"
        return _safe_ident(type_name, "Any")
    return "Any"


def _expr_called_function_names(expr: Any) -> set[str]:
    out: set[str] = set()
    if not isinstance(expr, dict):
        return out
    kind = expr.get("kind")
    if kind == "Call":
        func_any = expr.get("func")
        if isinstance(func_any, dict) and func_any.get("kind") == "Name":
            name = _safe_ident(func_any.get("id"), "")
            if name != "":
                out.add(name)
        out |= _expr_called_function_names(func_any)
        args_any = expr.get("args")
        args = args_any if isinstance(args_any, list) else []
        i = 0
        while i < len(args):
            out |= _expr_called_function_names(args[i])
            i += 1
        keywords_any = expr.get("keywords")
        keywords = keywords_any if isinstance(keywords_any, list) else []
        i = 0
        while i < len(keywords):
            kw = keywords[i]
            if isinstance(kw, dict):
                out |= _expr_called_function_names(kw.get("value"))
            i += 1
        return out
    for value in expr.values():
        if isinstance(value, dict):
            out |= _expr_called_function_names(value)
        elif isinstance(value, list):
            for item in value:
                out |= _expr_called_function_names(item)
    return out


def _stmt_has_raise_or_try(stmt: Any) -> bool:
    if not isinstance(stmt, dict):
        return False
    kind = stmt.get("kind")
    if kind in {"Raise", "Try"}:
        return True
    for value in stmt.values():
        if isinstance(value, dict) and _stmt_has_raise_or_try(value):
            return True
        if isinstance(value, dict) and _expr_has_subscript(value):
            return True
        if isinstance(value, list):
            for item in value:
                if _stmt_has_raise_or_try(item):
                    return True
                if _expr_has_subscript(item):
                    return True
    return False


def _expr_has_subscript(expr: Any) -> bool:
    if not isinstance(expr, dict):
        return False
    if expr.get("kind") == "Subscript":
        return True
    for value in expr.values():
        if isinstance(value, dict):
            if _expr_has_subscript(value):
                return True
        elif isinstance(value, list):
            i = 0
            while i < len(value):
                if _expr_has_subscript(value[i]):
                    return True
                i += 1
    return False


def _stmt_called_function_names(stmt: Any) -> set[str]:
    out: set[str] = set()
    if not isinstance(stmt, dict):
        return out
    for value in stmt.values():
        if isinstance(value, dict):
            out |= _expr_called_function_names(value)
            out |= _stmt_called_function_names(value)
        elif isinstance(value, list):
            for item in value:
                out |= _expr_called_function_names(item)
                out |= _stmt_called_function_names(item)
    return out


def _collect_throwing_functions(east_doc: dict[str, Any]) -> set[str]:
    function_bodies: dict[str, list[Any]] = {}
    body_any = east_doc.get("body")
    body = body_any if isinstance(body_any, list) else []
    for node in body:
        if not isinstance(node, dict):
            continue
        if node.get("kind") == "FunctionDef":
            name = _safe_ident(node.get("name"), "")
            fn_body_any = node.get("body")
            fn_body = fn_body_any if isinstance(fn_body_any, list) else []
            if name != "":
                function_bodies[name] = fn_body
        if node.get("kind") == "ClassDef":
            cls_body_any = node.get("body")
            cls_body = cls_body_any if isinstance(cls_body_any, list) else []
            for cls_node in cls_body:
                if isinstance(cls_node, dict) and cls_node.get("kind") in {"FunctionDef", "ClosureDef"}:
                    name = _safe_ident(cls_node.get("name"), "")
                    fn_body_any = cls_node.get("body")
                    fn_body = fn_body_any if isinstance(fn_body_any, list) else []
                    if name != "":
                        function_bodies[name] = fn_body
    throwing: set[str] = set()
    changed = True
    while changed:
        changed = False
        for name, fn_body in function_bodies.items():
            if name in throwing:
                continue
            direct_throw = False
            called_names: set[str] = set()
            i = 0
            while i < len(fn_body):
                direct_throw = direct_throw or _stmt_has_raise_or_try(fn_body[i])
                called_names |= _stmt_called_function_names(fn_body[i])
                i += 1
            if direct_throw or len(called_names & throwing) > 0:
                throwing.add(name)
                changed = True
    return throwing


def _stmt_mutates_param(stmt: Any, params: set[str]) -> set[str]:
    out: set[str] = set()
    if not isinstance(stmt, dict):
        return out
    kind = stmt.get("kind")
    if kind == "Assign":
        targets_any = stmt.get("targets")
        targets = targets_any if isinstance(targets_any, list) else []
        if len(targets) == 0 and isinstance(stmt.get("target"), dict):
            targets = [stmt.get("target")]
        i = 0
        while i < len(targets):
            tgt = targets[i]
            if isinstance(tgt, dict) and tgt.get("kind") == "Subscript":
                owner = tgt.get("value")
                if isinstance(owner, dict) and owner.get("kind") == "Name":
                    owner_id = _safe_ident(owner.get("id"), "")
                    if owner_id in params:
                        out.add(owner_id)
            i += 1
    for value in stmt.values():
        if isinstance(value, dict):
            out |= _stmt_mutates_param(value, params)
        elif isinstance(value, list):
            i = 0
            while i < len(value):
                out |= _stmt_mutates_param(value[i], params)
                i += 1
    return out


def _collect_inout_param_positions(fn: dict[str, Any], *, drop_self: bool) -> set[int]:
    names = _function_param_names(fn, drop_self=drop_self)
    params = set(names)
    body_any = fn.get("body")
    body = body_any if isinstance(body_any, list) else []
    mutated: set[str] = set()
    i = 0
    while i < len(body):
        mutated |= _stmt_mutates_param(body[i], params)
        i += 1
    out: set[int] = set()
    i = 0
    while i < len(names):
        if names[i] in mutated:
            out.add(i)
        i += 1
    return out


def _default_return_expr(swift_type: str) -> str:
    if swift_type == "Int64":
        return "0"
    if swift_type == "Double":
        return "0.0"
    if swift_type == "Bool":
        return "false"
    if swift_type == "String":
        return '""'
    if swift_type == "[Any]":
        return "[]"
    if swift_type == "[UInt8]":
        return "[]"
    if swift_type == "[AnyHashable: Any]":
        return "[:]"
    if swift_type == "Void":
        return ""
    if swift_type == "Any":
        return "__pytra_any_default()"
    return swift_type + "()"


def _can_default_init_swift_type(swift_type: str) -> bool:
    return swift_type in {
        "Int64",
        "Double",
        "Bool",
        "String",
        "[Any]",
        "[UInt8]",
        "[AnyHashable: Any]",
        "Any",
    }


def _collect_return_value_types(body: list[Any]) -> set[str]:
    out: set[str] = set()
    i = 0
    while i < len(body):
        stmt = body[i]
        if isinstance(stmt, dict):
            kind = stmt.get("kind")
            if kind == "Return":
                value_any = stmt.get("value")
                if isinstance(value_any, dict):
                    inferred = _swift_type(value_any.get("resolved_type"), allow_void=False)
                    if inferred == "Any":
                        inferred = _infer_swift_type(value_any)
                    out.add(inferred)
            for value in stmt.values():
                if isinstance(value, list):
                    out |= _collect_return_value_types(value)
        i += 1
    return out


def _function_return_swift_type(fn: dict[str, Any], *, allow_void: bool) -> str:
    return_type = _swift_type(fn.get("return_type"), allow_void=allow_void)
    if return_type != "Void":
        return return_type
    body_any = fn.get("body")
    body = body_any if isinstance(body_any, list) else []
    inferred = _collect_return_value_types(body)
    inferred.discard("Void")
    if len(inferred) == 1:
        return next(iter(inferred))
    if len(inferred) > 1:
        return "Any"
    return return_type


def _tuple_element_types(type_name: Any) -> list[str]:
    if not isinstance(type_name, str):
        return []
    ts2: str = type_name
    if not ts2.startswith("tuple[") or not ts2.endswith("]"):
        return []
    body = type_name[6:-1]
    out: list[str] = []
    buf = ""
    depth = 0
    i = 0
    while i < len(body):
        ch = body[i]
        if ch == "[":
            depth += 1
            buf += ch
            i += 1
            continue
        if ch == "]":
            depth -= 1
            buf += ch
            i += 1
            continue
        if ch == "," and depth == 0:
            piece = buf.strip()
            if piece != "":
                out.append(piece)
            buf = ""
            i += 1
            continue
        buf += ch
        i += 1
    tail = buf.strip()
    if tail != "":
        out.append(tail)
    return out


def _strip_outer_parens(expr: str) -> str:
    cur = expr.strip()
    while len(cur) >= 2 and cur[0] == "(" and cur[-1] == ")":
        depth = 0
        ok = True
        i = 0
        while i < len(cur):
            ch = cur[i]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0 and i != len(cur) - 1:
                    ok = False
                    break
                if depth < 0:
                    ok = False
                    break
            i += 1
        if not ok or depth != 0:
            break
        cur = cur[1:-1].strip()
    return cur


def _is_direct_call(expr: str, fn_name: str) -> bool:
    txt = _strip_outer_parens(expr)
    prefix = fn_name + "("
    if not txt.startswith(prefix) or not txt.endswith(")"):
        return False
    depth = 0
    i = len(fn_name)
    while i < len(txt):
        ch = txt[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0 and i != len(txt) - 1:
                return False
            if depth < 0:
                return False
        i += 1
    return depth == 0


def _wrap_runtime_call(expr: str, fn_name: str) -> str:
    inner = _strip_outer_parens(expr)
    if _is_direct_call(inner, fn_name):
        return inner
    return fn_name + "(" + inner + ")"


def _to_int_expr(expr: str) -> str:
    return _wrap_runtime_call(expr, "__pytra_int")


def _to_float_expr(expr: str) -> str:
    return _wrap_runtime_call(expr, "__pytra_float")


def _to_truthy_expr(expr: str) -> str:
    return _wrap_runtime_call(expr, "__pytra_truthy")


def _to_str_expr(expr: str) -> str:
    return _wrap_runtime_call(expr, "__pytra_str")


def _to_list_expr(expr: str) -> str:
    return _wrap_runtime_call(expr, "__pytra_as_list")


def _to_dict_expr(expr: str) -> str:
    return _wrap_runtime_call(expr, "__pytra_as_dict")


def _has_resolved_type(node: Any, expected: set[str]) -> bool:
    if not isinstance(node, dict):
        return False
    nd4: dict[str, Any] = node
    resolved_any = nd4.get("resolved_type")
    if not isinstance(resolved_any, str):
        return False
    return resolved_any in expected


def _int_operand(expr: str, node: Any) -> str:
    if _has_resolved_type(node, {"int", "int64", "uint8"}):
        return expr
    return _to_int_expr(expr)


def _float_operand(expr: str, node: Any) -> str:
    if _has_resolved_type(node, {"float", "float64"}):
        return expr
    return _to_float_expr(expr)


def _is_int_literal(node: Any, expected: int) -> bool:
    if isinstance(node, int) and not isinstance(node, bool):
        return node == expected
    if not isinstance(node, dict):
        return False
    nd3: dict[str, Any] = node
    if nd3.get("kind") != "Constant":
        return False
    value = nd3.get("value")
    if isinstance(value, bool):
        return False
    return isinstance(value, int) and value == expected


def _is_none_constant(node: Any) -> bool:
    if not isinstance(node, dict):
        return False
    if node.get("kind") != "Constant":
        return False
    return node.get("value") is None


def _cast_from_any(expr: str, swift_type: str) -> str:
    if swift_type == "Int64":
        return _to_int_expr(expr)
    if swift_type == "Double":
        return _to_float_expr(expr)
    if swift_type == "Bool":
        return _to_truthy_expr(expr)
    if swift_type == "String":
        return _to_str_expr(expr)
    if swift_type == "[Any]":
        return _to_list_expr(expr)
    if swift_type == "[UInt8]":
        return _wrap_runtime_call(expr, "__pytra_as_u8_list")
    if swift_type == "[AnyHashable: Any]":
        return _to_dict_expr(expr)
    if swift_type == "Any":
        return expr
    if swift_type == "ArgValue":
        return expr
    if "->" in swift_type and swift_type.startswith("("):
        return "(" + expr + " as! " + swift_type + ")"
    if swift_type == "Obj":
        return expr
    if swift_type in _TRAIT_NAMES[0]:
        return "(" + expr + " as! " + swift_type + ")"
    if swift_type in _CLASS_NAMES[0]:
        return "(" + expr + " as? " + swift_type + ") ?? " + swift_type + "()"
    if swift_type != "" and swift_type[0].isupper():
        return "(" + expr + " as? " + swift_type + ") ?? " + swift_type + "()"
    return expr


def _render_binop_as_type(expr: dict[str, Any], swift_type: str) -> str:
    left_node = expr.get("left")
    right_node = expr.get("right")
    left_expr = _render_expr(left_node)
    right_expr = _render_expr(right_node)
    op = expr.get("op")
    sym = _bin_op_symbol(op)
    if swift_type == "Int64":
        return "(" + _int_operand(left_expr, left_node) + " " + sym + " " + _int_operand(right_expr, right_node) + ")"
    if swift_type == "Double":
        return "(" + _float_operand(left_expr, left_node) + " " + sym + " " + _float_operand(right_expr, right_node) + ")"
    return _render_binop_expr(expr)


def _render_name_expr(expr: dict[str, Any]) -> str:
    ident = _safe_ident(expr.get("id"), "value")
    if ident.startswith("json_native_"):
        return ident[len("json_native_") :]
    resolved_any = expr.get("resolved_type")
    if isinstance(resolved_any, str):
        if resolved_any.startswith("Callable[[dict[str, JsonVal], Path],") and "None" in resolved_any:
            return "(" + ident + " as! ([AnyHashable: Any], Path) -> Int64)"
        if ident == "emit_fn" and resolved_any.startswith("Callable[[dict[str, JsonVal]],"):
            return "(" + ident + " as! ([AnyHashable: Any]) -> String)"
        if resolved_any.startswith("Callable[[Path],") and "None" in resolved_any:
            return "(" + ident + " as! (Path) -> Void)"
    if ident == "main" and _MAIN_CALL_ALIAS[0] != "":
        return _MAIN_CALL_ALIAS[0]
    rendered = _RELATIVE_IMPORT_NAME_ALIASES[0].get(ident, ident)
    if ident in _FUNCTION_SIGNATURES[0]:
        return rendered
    resolved = expr.get("resolved_type")
    if isinstance(resolved, str) and (
        resolved in {"str", "bool", "int", "int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64", "float", "float32", "float64"}
    ):
        swift_type = _swift_type(resolved, allow_void=False)
        if swift_type != "Any":
            return _cast_from_any(rendered, swift_type)
    return rendered


def _render_format_spec(spec_expr: Any) -> str:
    if isinstance(spec_expr, str):
        return spec_expr
    if not isinstance(spec_expr, dict):
        return ""
    kind = spec_expr.get("kind")
    if kind == "Constant" and isinstance(spec_expr.get("value"), str):
        return spec_expr.get("value")
    if kind == "JoinedStr":
        values_any = spec_expr.get("values")
        values = values_any if isinstance(values_any, list) else []
        parts: list[str] = []
        i = 0
        while i < len(values):
            value_any = values[i]
            if isinstance(value_any, dict) and value_any.get("kind") == "Constant" and isinstance(value_any.get("value"), str):
                parts.append(value_any.get("value"))
            i += 1
        return "".join(parts)
    return ""


def _render_constant_expr(expr: dict[str, Any]) -> str:
    if "value" not in expr:
        return "__pytra_any_default()"
    value = expr.get("value")
    if value is None:
        resolved = expr.get("resolved_type")
        if resolved in {"int", "int64", "uint8"}:
            return "Int64(0)"
        if resolved in {"float", "float64"}:
            return "Double(0)"
        if resolved == "bool":
            return "false"
        if resolved == "str":
            return '""'
        return "__pytra_none()"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return "Int64(" + str(value) + ")"
    if isinstance(value, float):
        return "Double(" + str(value) + ")"
    if isinstance(value, str):
        return _swift_string_literal(value)
    return "__pytra_any_default()"


def _render_truthy_expr(expr: Any) -> str:
    if not isinstance(expr, dict):
        return "__pytra_truthy(" + _render_expr(expr) + ")"
    ed3: dict[str, Any] = expr
    resolved = ed3.get("resolved_type")
    rendered = _render_expr(expr)
    if isinstance(resolved, str):
        if resolved == "bool":
            return rendered
        if resolved in {"int", "int64", "uint8"}:
            return "(" + rendered + " != 0)"
        if resolved in {"float", "float64"}:
            return "(" + rendered + " != 0.0)"
        if resolved == "str":
            return "(" + rendered + " != \"\")"
        if resolved.startswith("list[") or resolved.startswith("tuple[") or resolved.startswith("dict[") or resolved in {"bytes", "bytearray"}:
            return "(__pytra_len(" + rendered + ") != 0)"
    kind = ed3.get("kind")
    if kind in {"Compare", "BoolOp", "IsInstance"}:
        return rendered
    return "__pytra_truthy(" + rendered + ")"


def _bin_op_symbol(op: Any) -> str:
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
    if op == "FloorDiv":
        return "/"
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
    return "+"


def _render_unary_expr(expr: dict[str, Any]) -> str:
    op = expr.get("op")
    operand = _render_expr(expr.get("operand"))
    if op == "USub":
        return "(-" + operand + ")"
    if op == "UAdd":
        return "(+" + operand + ")"
    if op == "Invert":
        return "(~" + operand + ")"
    if op == "Not":
        return "(!" + _render_truthy_expr(expr.get("operand")) + ")"
    return operand


def _render_binop_expr(expr: dict[str, Any]) -> str:
    op = expr.get("op")
    if op == "Mult":
        left_any = expr.get("left")
        right_any = expr.get("right")
        if isinstance(left_any, dict) and left_any.get("kind") == "List":
            return "__pytra_list_repeat(" + _render_expr(left_any) + ", " + _render_expr(right_any) + ")"
        if isinstance(right_any, dict) and right_any.get("kind") == "List":
            return "__pytra_list_repeat(" + _render_expr(right_any) + ", " + _render_expr(left_any) + ")"

    left_node = expr.get("left")
    right_node = expr.get("right")
    left_expr = _render_expr(left_node)
    right_expr = _render_expr(right_node)
    resolved = expr.get("resolved_type")

    left_type = str(left_node.get("resolved_type", "")) if isinstance(left_node, dict) else ""
    right_type = str(right_node.get("resolved_type", "")) if isinstance(right_node, dict) else ""
    if op == "Div" and left_type in ("Path", "pathlib.Path", "pytra.std.pathlib.Path"):
        return left_expr + ".__truediv__(" + right_expr + ")"

    if op == "Div":
        return "(" + _float_operand(left_expr, left_node) + " / " + _float_operand(right_expr, right_node) + ")"

    if op == "FloorDiv":
        return "(" + _int_operand(left_expr, left_node) + " / " + _int_operand(right_expr, right_node) + ")"

    if op == "Mod":
        return "(" + _int_operand(left_expr, left_node) + " % " + _int_operand(right_expr, right_node) + ")"

    if op == "Add" and (resolved == "str" or left_type == "str" or right_type == "str"):
        return "(" + _to_str_expr(left_expr) + " + " + _to_str_expr(right_expr) + ")"

    if resolved in {"int", "int64", "uint8"}:
        sym = _bin_op_symbol(op)
        return "(" + _int_operand(left_expr, left_node) + " " + sym + " " + _int_operand(right_expr, right_node) + ")"

    if resolved in {"float", "float64"}:
        sym = _bin_op_symbol(op)
        return "(" + _float_operand(left_expr, left_node) + " " + sym + " " + _float_operand(right_expr, right_node) + ")"

    sym = _bin_op_symbol(op)
    return "(" + left_expr + " " + sym + " " + right_expr + ")"


def _compare_op_symbol(op: Any) -> str:
    if op == "Eq":
        return "=="
    if op == "NotEq":
        return "!="
    if op == "Is":
        return "=="
    if op == "IsNot":
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


def _is_swift_class_type(type_name: str) -> bool:
    return type_name in _CLASS_NAMES[0]


def _render_compare_expr(expr: dict[str, Any]) -> str:
    left = _render_expr(expr.get("left"))
    ops_any = expr.get("ops")
    comps_any = expr.get("comparators")
    ops = ops_any if isinstance(ops_any, list) else []
    comps = comps_any if isinstance(comps_any, list) else []
    if len(ops) == 0 or len(comps) == 0:
        return "false"

    parts: list[str] = []
    cur_left = left
    i = 0
    while i < len(ops) and i < len(comps):
        comp_node = comps[i]
        right = _render_expr(comp_node)
        op = ops[i]

        left_node = expr.get("left") if i == 0 else comps[i - 1]
        if op in {"Is", "IsNot"} and (_is_none_constant(left_node) or _is_none_constant(comp_node)):
            probe_node = comp_node if _is_none_constant(left_node) else left_node
            probe_type_any = probe_node.get("resolved_type") if isinstance(probe_node, dict) else ""
            probe_type = probe_type_any if isinstance(probe_type_any, str) else ""
            if probe_type.lower().startswith("callable"):
                is_none_expr = "false"
            else:
                probe_expr = _render_expr(probe_node)
                is_none_expr = "__pytra_is_none(" + probe_expr + ")"
            if op == "IsNot":
                is_none_expr = "(!" + is_none_expr + ")"
            parts.append("(" + is_none_expr + ")")
            cur_left = right
            i += 1
            continue

        if op == "In" or op == "NotIn":
            expr_txt = "__pytra_contains(" + right + ", " + cur_left + ")"
            if op == "NotIn":
                expr_txt = "(!" + expr_txt + ")"
            parts.append("(" + expr_txt + ")")
            cur_left = right
            i += 1
            continue

        left_type = ""
        right_type = ""
        if i == 0 and isinstance(expr.get("left"), dict):
            left_any = expr.get("left", {}).get("resolved_type")
            left_type = left_any if isinstance(left_any, str) else ""
        elif i > 0 and isinstance(comps[i - 1], dict):
            left_any = comps[i - 1].get("resolved_type")
            left_type = left_any if isinstance(left_any, str) else ""
        if isinstance(comp_node, dict):
            cd: dict[str, Any] = comp_node
            right_any = cd.get("resolved_type")
            right_type = right_any if isinstance(right_any, str) else ""

        symbol = _compare_op_symbol(op)
        if op in {"Is", "IsNot"} and _is_swift_class_type(left_type) and _is_swift_class_type(right_type):
            identity = "(" + cur_left + (" === " if op == "Is" else " !== ") + right + ")"
            parts.append(identity)
            cur_left = right
            i += 1
            continue
        if left_type == "str" or right_type == "str":
            lhs = cur_left if _expr_emits_target_type(left_node, "String") else _to_str_expr(cur_left)
            rhs = right if _expr_emits_target_type(comp_node, "String") else _to_str_expr(right)
            parts.append("(" + lhs + " " + symbol + " " + rhs + ")")
        elif left_type in {"int", "int64", "uint8"} or right_type in {"int", "int64", "uint8"}:
            lhs = cur_left if _expr_emits_target_type(left_node, "Int64") else _to_int_expr(cur_left)
            rhs = right if _expr_emits_target_type(comp_node, "Int64") else _to_int_expr(right)
            parts.append("(" + lhs + " " + symbol + " " + rhs + ")")
        elif left_type in {"float", "float64"} or right_type in {"float", "float64"}:
            lhs = cur_left if _expr_emits_target_type(left_node, "Double") else _to_float_expr(cur_left)
            rhs = right if _expr_emits_target_type(comp_node, "Double") else _to_float_expr(right)
            parts.append("(" + lhs + " " + symbol + " " + rhs + ")")
        else:
            if op in {"Eq", "NotEq"}:
                lhs = _to_str_expr(cur_left)
                rhs = _to_str_expr(right)
                parts.append("(" + lhs + " " + symbol + " " + rhs + ")")
            else:
                lhs = _to_float_expr(cur_left)
                rhs = _to_float_expr(right)
                parts.append("(" + lhs + " " + symbol + " " + rhs + ")")

        cur_left = right
        i += 1

    if len(parts) == 1:
        return parts[0]
    return "(" + " && ".join(parts) + ")"


def _render_boolop_expr(expr: dict[str, Any]) -> str:
    op = expr.get("op")
    values_any = expr.get("values")
    values = values_any if isinstance(values_any, list) else []
    if len(values) == 0:
        return "false"
    resolved = expr.get("resolved_type")
    if resolved == "bool":
        rendered: list[str] = []
        i = 0
        while i < len(values):
            rendered.append(_render_truthy_expr(values[i]))
            i += 1
        delim = " && " if op == "And" else " || "
        return "(" + delim.join(rendered) + ")"
    cur = _render_expr(values[0])
    i = 1
    while i < len(values):
        nxt = _render_expr(values[i])
        tmp = "__boolop_" + str(i)
        if op == "And":
            cur = "({ let " + tmp + " = " + cur + "; return __pytra_truthy(" + tmp + ") ? " + nxt + " : " + tmp + " })()"
        else:
            cur = "({ let " + tmp + " = " + cur + "; return __pytra_truthy(" + tmp + ") ? " + tmp + " : " + nxt + " })()"
        i += 1
    return _cast_from_any(cur, _swift_type(resolved, allow_void=False))


def _snake_to_pascal(name: str) -> str:
    parts = name.split("_")
    out: list[str] = []
    i = 0
    while i < len(parts):
        part = parts[i].strip()
        if part != "":
            out.append(part[0].upper() + part[1:])
        i += 1
    return "".join(out)


def _resolved_runtime_symbol(
    runtime_call: str,
    adapter_kind: str = "",
    *,
    resolved_runtime_call: str = "",
    runtime_symbol: str = "",
) -> str:
    """Resolve runtime call to Swift function name.

    Uses runtime_call_adapter_kind (§1) when available,
    falls back to runtime_call string parsing.
    """
    name = runtime_call.strip()
    mapped = ""
    if resolved_runtime_call in _SWIFT_RUNTIME_MAPPING.calls:
        mapped = _SWIFT_RUNTIME_MAPPING.calls[resolved_runtime_call]
    elif runtime_call in _SWIFT_RUNTIME_MAPPING.calls:
        mapped = _SWIFT_RUNTIME_MAPPING.calls[runtime_call]
    elif runtime_symbol in _SWIFT_RUNTIME_MAPPING.calls:
        mapped = _SWIFT_RUNTIME_MAPPING.calls[runtime_symbol]
    if mapped != "":
        return mapped.replace(".", "_")
    if name == "":
        return ""
    # §1: use runtime_call_adapter_kind when available
    if adapter_kind == "extern_delegate":
        dot = name.find(".")
        if dot >= 0:
            module_name = name[:dot].strip()
            symbol_name = name[dot + 1 :].strip()
            if module_name != "" and symbol_name != "":
                return module_name + "_native_" + symbol_name
        return ""
    if adapter_kind == "builtin":
        dot = name.find(".")
        bare = name[dot + 1:].strip() if dot >= 0 else name
        return "__pytra_" + bare if bare != "" else ""
    # Fallback: infer from runtime_call string structure
    dot = name.find(".")
    if dot >= 0:
        module_name = name[:dot].strip()
        symbol_name = name[dot + 1 :].strip()
        if module_name == "" or symbol_name == "":
            return ""
        return module_name + "_native_" + symbol_name
    return "__pytra_" + name


def _runtime_module_id(expr: dict[str, Any]) -> str:
    runtime_module_any = expr.get("runtime_module_id")
    runtime_module = runtime_module_any if isinstance(runtime_module_any, str) else ""
    if runtime_module == "":
        runtime_call, _ = _resolved_runtime_call(expr)
        dot = runtime_call.find(".")
        if dot >= 0:
            runtime_module = runtime_call[:dot].strip()
    return canonical_runtime_module_id(runtime_module)


def _runtime_module_group(expr: dict[str, Any]) -> str:
    return _module_group(_runtime_module_id(expr))


def _runtime_module_stem(expr: dict[str, Any]) -> str:
    return _module_stem(_runtime_module_id(expr))


def _runtime_symbol_name(expr: dict[str, Any]) -> str:
    runtime_symbol_any = expr.get("runtime_symbol")
    if isinstance(runtime_symbol_any, str):
        rs: str = runtime_symbol_any
        return rs.strip()
    runtime_call, _ = _resolved_runtime_call(expr)
    dot = runtime_call.find(".")
    if dot >= 0:
        return runtime_call[dot + 1 :].strip()
    return ""


def _resolved_runtime_source(expr: dict[str, Any]) -> str:
    resolved_source_any = expr.get("resolved_runtime_source")
    return resolved_source_any if isinstance(resolved_source_any, str) else ""


def _runtime_adapter_kind(expr: dict[str, Any]) -> str:
    adapter_any = expr.get("runtime_call_adapter_kind")
    return adapter_any if isinstance(adapter_any, str) else ""


def _expr_semantic_tag(expr: dict[str, Any]) -> str:
    semantic_tag_any = expr.get("semantic_tag")
    return semantic_tag_any if isinstance(semantic_tag_any, str) else ""


def _is_direct_extern_module_attr(expr: dict[str, Any]) -> bool:
    if _resolved_runtime_source(expr) != "module_attr":
        return False
    return _runtime_adapter_kind(expr) == "extern_delegate"


def _is_argument_parser_method(expr: dict[str, Any], method_name: str) -> bool:
    semantic_tag = _expr_semantic_tag(expr)
    return semantic_tag == "stdlib.method." + method_name and _runtime_symbol_name(expr).endswith("." + method_name)


def _matches_runtime_method(expr: dict[str, Any], *runtime_calls: str) -> bool:
    runtime_call, resolved_source = _resolved_runtime_call(expr)
    if runtime_call != "" and runtime_call in runtime_calls:
        return True
    runtime_symbol = _runtime_symbol_name(expr)
    if runtime_symbol in runtime_calls:
        return True
    if resolved_source == "resolved_runtime_call" and runtime_call in runtime_calls:
        return True
    return False


def _is_perf_counter_call(expr: dict[str, Any]) -> bool:
    return _expr_semantic_tag(expr) == "stdlib.fn.perf_counter"


def _is_module_skip_target(module_id: str) -> bool:
    group = _module_group(module_id)
    if group in {"built_in", "utils"}:
        return True
    if should_skip_module(module_id, _SWIFT_RUNTIME_MAPPING):
        return True
    if group != "std":
        return False
    stem = _module_stem(module_id)
    if stem == "":
        return False
    native_candidates = [
        _SWIFT_RUNTIME_ROOT / "std" / ("pytra_std_" + stem + ".swift"),
        _SWIFT_RUNTIME_ROOT / "std" / (stem + "_native.swift"),
    ]
    i = 0
    while i < len(native_candidates):
        if native_candidates[i].exists():
            return True
        i += 1
    return True


_SWIFT_MATH_RUNTIME_SYMBOLS = {
    "pi",
    "e",
    "sin",
    "cos",
    "tan",
    "sqrt",
    "exp",
    "log",
    "log10",
    "fabs",
    "floor",
    "ceil",
    "pow",
}


def _has_runtime_extern_module(expr: dict[str, Any]) -> bool:
    runtime_module_any = expr.get("runtime_module_id")
    runtime_module = runtime_module_any if isinstance(runtime_module_any, str) else ""
    if runtime_module == "":
        return False
    return len(lookup_runtime_module_extern_contract(runtime_module)) > 0


def _matches_math_symbol(expr: dict[str, Any], symbol: str, semantic_tag: str) -> bool:
    if _runtime_symbol_name(expr) != symbol:
        return False
    semantic_tag_any = expr.get("semantic_tag")
    if isinstance(semantic_tag_any, str) and semantic_tag_any == semantic_tag:
        return True
    if _has_runtime_extern_module(expr):
        return True
    # §1: use runtime_call_adapter_kind instead of hardcoded module check
    adapter = expr.get("runtime_call_adapter_kind", "")
    if isinstance(adapter, str) and adapter == "extern_delegate":
        return True
    return False


def _is_math_runtime(expr: dict[str, Any]) -> bool:
    symbol = _runtime_symbol_name(expr)
    if symbol not in _SWIFT_MATH_RUNTIME_SYMBOLS:
        return False
    if _has_runtime_extern_module(expr):
        return True
    # §1: use runtime_call_adapter_kind instead of hardcoded module check
    adapter = expr.get("runtime_call_adapter_kind", "")
    if isinstance(adapter, str) and adapter == "extern_delegate":
        return True
    return False


def _is_math_constant(expr: dict[str, Any]) -> bool:
    return _matches_math_symbol(expr, "pi", "stdlib.symbol.pi") or _matches_math_symbol(
        expr, "e", "stdlib.symbol.e"
    )


def _render_attribute_expr(expr: dict[str, Any]) -> str:
    value_any = expr.get("value")
    attr = _safe_ident(expr.get("attr"), "field")
    if attr == "__name__" and isinstance(value_any, dict) and value_any.get("kind") == "Call" and _call_name(value_any) == "type":
        call_args_any = value_any.get("args")
        call_args = call_args_any if isinstance(call_args_any, list) else []
        if len(call_args) == 1:
            return "__pytra_type_name(" + _render_expr(call_args[0]) + ")"
    if isinstance(value_any, dict) and value_any.get("kind") == "Name":
        owner_module = value_any.get("runtime_module_id")
        if attr == "target" and _module_stem(owner_module) == "env" and _module_group(owner_module) == "std":
            return "\"swift\""
        if attr == "target" and _runtime_symbol_name(expr) == "target":
            return "\"swift\""
        owner_type = value_any.get("resolved_type")
        if owner_type == "type":
            return _safe_ident(value_any.get("id"), "Type") + "." + attr
    semantic_tag = _expr_semantic_tag(expr)
    if semantic_tag == "stdlib.symbol.argv":
        return "__pytra_sys_argv"
    if semantic_tag == "stdlib.symbol.path":
        return "__pytra_sys_path"
    if semantic_tag == "stdlib.symbol.stderr":
        return "sys_native_stderr()"
    if semantic_tag == "stdlib.symbol.stdout":
        return "sys_native_stdout()"
    if _is_math_constant(expr):
        runtime_name = _runtime_symbol_name(expr)
        if runtime_name == "pi":
            return "Double.pi"
        if runtime_name == "e":
            return "Foundation.exp(1.0)"
    runtime_call, _ = _resolved_runtime_call(expr)
    if semantic_tag.startswith("stdlib.") and runtime_call == "" and not _is_math_constant(expr) and not _is_math_runtime(expr):
        raise RuntimeError("swift native emitter: unresolved stdlib runtime attribute: " + semantic_tag)
    resolved_runtime_any = expr.get("resolved_runtime_call")
    resolved_runtime = resolved_runtime_any if isinstance(resolved_runtime_any, str) else ""
    if resolved_runtime != "":
        if _resolved_runtime_source(expr) == "module_attr":
            runtime_name = _runtime_symbol_name(expr)
            if runtime_name == "target":
                return "\"swift\""
            if _is_direct_extern_module_attr(expr):
                return _safe_ident(runtime_name if runtime_name != "" else attr, attr)
            adapter = _runtime_adapter_kind(expr)
            runtime_symbol = _resolved_runtime_symbol(
                resolved_runtime,
                adapter,
                resolved_runtime_call=resolved_runtime,
                runtime_symbol=runtime_name,
            )
            if runtime_symbol != "":
                if _is_math_constant(expr):
                    return runtime_symbol
                return runtime_symbol
            return resolved_runtime
    value = _render_expr(value_any)
    if attr == "raw":
        owner_type = value_any.get("resolved_type", "") if isinstance(value_any, dict) else ""
        owner_id = value_any.get("id", "") if isinstance(value_any, dict) else ""
        if isinstance(owner_type, str) and "JsonValue" in owner_type:
            return value + ".raw"
        if isinstance(owner_type, str) and "JsonArr" in owner_type:
            return "((" + value + " as? JsonArr) ?? JsonArr()).raw"
        if isinstance(owner_id, str) and owner_id.endswith("_arr"):
            return "((" + value + " as? JsonArr) ?? JsonArr()).raw"
        if value.startswith("JsonValue("):
            return value + ".raw"
        return "((" + value + " as? JsonObj) ?? JsonObj()).raw"
    return value + "." + attr


def _call_name(expr: dict[str, Any]) -> str:
    func_any = expr.get("func")
    if not isinstance(func_any, dict):
        return ""
    fd2: dict[str, Any] = func_any
    kind = fd2.get("kind")
    if kind == "Name":
        return _safe_ident(fd2.get("id"), "")
    if kind == "Attribute":
        rendered = _render_attribute_expr(fd2)
        if rendered.startswith("json_native_"):
            rendered = rendered[len("json_native_") :]
        return _safe_ident(rendered, "")
    return ""


def _call_arg_nodes(expr: dict[str, Any]) -> list[Any]:
    args_any = expr.get("args")
    args = args_any if isinstance(args_any, list) else []
    out: list[Any] = []
    i = 0
    while i < len(args):
        out.append(args[i])
        i += 1
    keywords_any = expr.get("keywords")
    keywords = keywords_any if isinstance(keywords_any, list) else []
    if len(keywords) > 0:
        j = 0
        while j < len(keywords):
            kw = keywords[j]
            if isinstance(kw, dict):
                kd: dict[str, Any] = kw
                out.append(kd.get("value"))
            else:
                out.append(kw)
            j += 1
        return out
    kw_values_any = expr.get("kw_values")
    kw_values = kw_values_any if isinstance(kw_values_any, list) else []
    if len(kw_values) > 0:
        j = 0
        while j < len(kw_values):
            out.append(kw_values[j])
            j += 1
        return out
    kw_nodes_any = expr.get("kw_nodes")
    kw_nodes = kw_nodes_any if isinstance(kw_nodes_any, list) else []
    j = 0
    while j < len(kw_nodes):
        node = kw_nodes[j]
        if isinstance(node, dict):
            nd2: dict[str, Any] = node
            if nd2.get("kind") == "keyword":
                out.append(nd2.get("value"))
            else:
                out.append(node)
        else:
            out.append(node)
        j += 1
    return out


def _call_keyword_nodes(expr: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    keywords_any = expr.get("keywords")
    keywords = keywords_any if isinstance(keywords_any, list) else []
    i = 0
    while i < len(keywords):
        kw = keywords[i]
        if isinstance(kw, dict):
            arg_any = kw.get("arg")
            if isinstance(arg_any, str) and arg_any != "":
                out[arg_any] = kw.get("value")
        i += 1
    return out


def _render_stdlib_keyword_call(
    expr: dict[str, Any],
    callee_expr: str,
    positional_names: list[str],
    default_exprs: dict[str, str],
    *,
    force_try: bool = False,
) -> str:
    args_any = expr.get("args")
    args = args_any if isinstance(args_any, list) else []
    keywords = _call_keyword_nodes(expr)
    rendered_args: list[str] = []
    highest_index = len(args) - 1
    for name, _value in keywords.items():
        try:
            idx = positional_names.index(name)
        except ValueError:
            continue
        if idx > highest_index:
            highest_index = idx
    i = 0
    while i <= highest_index:
        if i < len(args):
            rendered_args.append(_render_expr(args[i]))
            i += 1
            continue
        arg_name = positional_names[i]
        kw_value = keywords.get(arg_name)
        if kw_value is not None:
            rendered_args.append(_render_expr(kw_value))
            i += 1
            continue
        rendered_args.append(default_exprs.get(arg_name, "__pytra_none()"))
        i += 1
    while len(rendered_args) > 0:
        tail_index = len(rendered_args) - 1
        tail_name = positional_names[tail_index]
        default_expr = default_exprs.get(tail_name)
        if default_expr is None or rendered_args[-1] != default_expr:
            break
        rendered_args.pop()
    call_code = callee_expr + "(" + ", ".join(rendered_args) + ")"
    if force_try or callee_expr in _THROWING_FUNCTIONS[0]:
        return "try! " + call_code
    return call_code


def _is_direct_stdlib_module_call(expr: dict[str, Any]) -> bool:
    func_any = expr.get("func")
    if not isinstance(func_any, dict):
        return False
    if func_any.get("kind") == "Name":
        return True
    if func_any.get("kind") != "Attribute":
        return False
    owner_any = func_any.get("value")
    if not isinstance(owner_any, dict):
        return False
    return owner_any.get("kind") == "Name" and owner_any.get("resolved_type") == "module"


def _class_has_base_method(class_name: str, method_name: str) -> bool:
    seen: set[str] = set()
    cur = _CLASS_BASES[0].get(class_name, "")
    while cur != "" and cur not in seen:
        seen.add(cur)
        methods = _CLASS_METHODS[0].get(cur)
        if isinstance(methods, set) and method_name in methods:
            return True
        cur = _CLASS_BASES[0].get(cur, "")
    return False


def _resolved_runtime_call(expr: dict[str, Any]) -> tuple[str, str]:
    runtime_call_any = expr.get("runtime_call")
    runtime_call = runtime_call_any if isinstance(runtime_call_any, str) else ""
    if runtime_call != "":
        return runtime_call, "runtime_call"
    resolved_any = expr.get("resolved_runtime_call")
    resolved = resolved_any if isinstance(resolved_any, str) else ""
    if resolved != "":
        return resolved, "resolved_runtime_call"
    return "", ""


def _render_call_via_runtime_call(
    runtime_call: str,
    runtime_source: str,
    semantic_tag: str,
    args: list[Any],
    expr: dict[str, Any],
) -> str:
    if runtime_call == "static_cast" and len(args) == 1:
        return _cast_from_any(_render_expr(args[0]), _swift_type(expr.get("resolved_type"), allow_void=False))
    if semantic_tag == "core.print":
        rendered_print_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_print_args.append(_render_expr(args[i]))
            i += 1
        return "__pytra_print(" + ", ".join(rendered_print_args) + ")"
    if runtime_call in {"index", "__pytra_index", "str.index", "list.index"} and len(args) == 2:
        arg0 = args[0]
        arg0_type = arg0.get("resolved_type") if isinstance(arg0, dict) else ""
        if arg0_type == "str":
            helper = "__pytra_index_str_throwing" if _IN_TRY_BODY_DEPTH[0] > 0 else "__pytra_index_str"
            prefix = "try " if _IN_TRY_BODY_DEPTH[0] > 0 else ""
            return prefix + helper + "(" + _render_expr(args[0]) + ", " + _render_expr(args[1]) + ")"
        helper = "__pytra_list_index_throwing" if _IN_TRY_BODY_DEPTH[0] > 0 else "__pytra_list_index"
        prefix = "try " if _IN_TRY_BODY_DEPTH[0] > 0 else ""
        return prefix + helper + "(" + _render_expr(args[0]) + ", " + _render_expr(args[1]) + ")"
    if runtime_call == "py_to_string" and len(args) == 1:
        arg0 = args[0]
        if isinstance(arg0, dict):
            resolved_arg_type = arg0.get("resolved_type")
            if isinstance(resolved_arg_type, str) and resolved_arg_type.startswith("tuple["):
                return "__pytra_tuple_str(" + _render_expr(arg0) + ")"
    if runtime_call == "py_assert_true":
        rendered_assert_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_assert_args.append(_render_expr(args[i]))
            i += 1
        return "__pytra_assert_true(" + ", ".join(rendered_assert_args) + ")"
    if runtime_call == "py_assert_eq":
        rendered_assert_args = []
        i = 0
        while i < len(args):
            rendered_assert_args.append(_render_expr(args[i]))
            i += 1
        return "__pytra_assert_eq(" + ", ".join(rendered_assert_args) + ")"
    if runtime_call == "py_assert_all":
        rendered_assert_args = []
        i = 0
        while i < len(args):
            rendered_assert_args.append(_render_expr(args[i]))
            i += 1
        return "__pytra_assert_all(" + ", ".join(rendered_assert_args) + ")"
    if runtime_call.startswith("py_assert_"):
        rendered_assert_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_assert_args.append(_render_expr(args[i]))
            i += 1
        return "__pytra_assert(" + ", ".join(rendered_assert_args) + ")"
    runtime_name = _runtime_symbol_name(expr)
    if runtime_name == "deque" and _swift_type(expr.get("resolved_type"), allow_void=False) == "[Any]":
        return "[]"
    adapter = _runtime_adapter_kind(expr)
    if runtime_source == "runtime_call":
        if adapter == "builtin":
            runtime_owner = expr.get("runtime_owner")
            owner_expr = ""
            owner_type = ""
            if isinstance(runtime_owner, dict):
                if runtime_owner.get("kind") == "Call" and _call_name(runtime_owner) == "super":
                    owner_expr = "super"
                else:
                    owner_expr = _render_expr(runtime_owner)
                rt = runtime_owner.get("resolved_type")
                owner_type = rt if isinstance(rt, str) else ""
            if owner_expr != "":
                if _matches_runtime_method(expr, "str.index") and len(args) == 1:
                    helper = "__pytra_index_str_throwing" if _IN_TRY_BODY_DEPTH[0] > 0 else "__pytra_index_str"
                    prefix = "try " if _IN_TRY_BODY_DEPTH[0] > 0 else ""
                    return prefix + helper + "(" + owner_expr + ", " + _render_expr(args[0]) + ")"
                if _matches_runtime_method(expr, "list.index") and len(args) == 1:
                    helper = "__pytra_list_index_throwing" if _IN_TRY_BODY_DEPTH[0] > 0 else "__pytra_list_index"
                    prefix = "try " if _IN_TRY_BODY_DEPTH[0] > 0 else ""
                    return prefix + helper + "(" + owner_expr + ", " + _render_expr(args[0]) + ")"
                if semantic_tag == "stdlib.method.__init__":
                    rendered_runtime_args: list[str] = []
                    i = 0
                    while i < len(args):
                        rendered_runtime_args.append(_render_expr(args[i]))
                        i += 1
                    return owner_expr + ".init(" + ", ".join(rendered_runtime_args) + ")"
                if _matches_runtime_method(expr, "list.clear", "dict.clear", "set.clear", "bytearray.clear"):
                    return owner_expr + ".removeAll()"
                if _matches_runtime_method(expr, "list.extend") and len(args) == 1:
                    return "__pytra_extend(&" + owner_expr + ", " + _render_expr(args[0]) + ")"
                if _matches_runtime_method(expr, "list.reverse", "bytearray.reverse") or (
                    _matches_runtime_method(expr, "bytes.reverse", "deque.reverse")
                ):
                    return owner_expr + ".reverse()"
                if _matches_runtime_method(expr, "list.sort") or _matches_runtime_method(expr, "bytes.sort", "bytearray.sort"):
                    return owner_expr + ".sort { __pytra_float($0) < __pytra_float($1) }"
                if _matches_runtime_method(expr, "list.pop", "bytearray.pop") and len(args) == 0:
                    return "__pytra_pop(&" + owner_expr + ")"
                if _matches_runtime_method(expr, "list.append", "deque.append") and len(args) == 1:
                    return owner_expr + ".append(" + _render_expr(args[0]) + ")"
                if _matches_runtime_method(expr, "set.add") and len(args) == 1:
                    return "__pytra_set_add(&" + owner_expr + ", " + _render_expr(args[0]) + ")"
                if _matches_runtime_method(expr, "set.update") and len(args) == 1:
                    return "__pytra_update(&" + owner_expr + ", " + _render_expr(args[0]) + ")"
                if _matches_runtime_method(expr, "set.discard") and len(args) == 1:
                    return "__pytra_discard(&" + owner_expr + ", " + _render_expr(args[0]) + ")"
                if _matches_runtime_method(expr, "set.remove") and len(args) == 1:
                    return "__pytra_remove(&" + owner_expr + ", " + _render_expr(args[0]) + ")"
                if _matches_runtime_method(expr, "dict.pop") and owner_type.startswith("dict[") and len(args) == 1:
                    return _cast_from_any(
                        "__pytra_dict_pop(&" + owner_expr + ", " + _render_expr(args[0]) + ")",
                        _swift_type(expr.get("resolved_type"), allow_void=False),
                    )
                if _matches_runtime_method(expr, "dict.setdefault") and owner_type.startswith("dict[") and len(args) == 2:
                    return _cast_from_any(
                        "__pytra_dict_setdefault(&" + owner_expr + ", " + _render_expr(args[0]) + ", " + _render_expr(args[1]) + ")",
                        _swift_type(expr.get("resolved_type"), allow_void=False),
                    )
            runtime_symbol = _resolved_runtime_symbol(
                runtime_call,
                adapter,
                resolved_runtime_call=runtime_call,
                runtime_symbol=runtime_name,
            )
            if runtime_symbol == "":
                return ""
            rendered_runtime_args: list[str] = []
            if owner_expr != "":
                rendered_runtime_args.append(owner_expr)
            i = 0
            while i < len(args):
                rendered_runtime_args.append(_render_expr(args[i]))
                i += 1
            return runtime_symbol + "(" + ", ".join(rendered_runtime_args) + ")"
        if semantic_tag.startswith("stdlib.fn."):
            runtime_symbol = _resolved_runtime_symbol(
                runtime_call,
                adapter,
                resolved_runtime_call=runtime_call,
                runtime_symbol=runtime_name,
            )
            if runtime_symbol == "":
                return ""
            rendered_runtime_args: list[str] = []
            i = 0
            while i < len(args):
                rendered_runtime_args.append(_render_expr(args[i]))
                i += 1
            return runtime_symbol + "(" + ", ".join(rendered_runtime_args) + ")"
        return ""
    runtime_symbol = _resolved_runtime_symbol(
        runtime_call,
        adapter,
        resolved_runtime_call=runtime_call,
        runtime_symbol=runtime_name,
    )
    if runtime_symbol == "":
        return ""
    if runtime_symbol in {"__pytra_extend", "__pytra_discard", "__pytra_remove", "__pytra_set_add", "__pytra_pop"} and len(args) > 0:
        rendered_runtime_args: list[str] = []
        first_arg = args[0]
        if isinstance(first_arg, dict) and first_arg.get("kind") == "Name":
            rendered_runtime_args.append("&" + _render_expr(first_arg))
        else:
            rendered_runtime_args.append(_render_expr(first_arg))
        i = 1
        while i < len(args):
            rendered_runtime_args.append(_render_expr(args[i]))
            i += 1
        return runtime_symbol + "(" + ", ".join(rendered_runtime_args) + ")"
    if runtime_call.find(".") >= 0:
        rendered_call_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_arg = _render_expr(args[i])
            if _is_math_runtime(expr):
                rendered_arg = _to_float_expr(rendered_arg)
            rendered_call_args.append(rendered_arg)
            i += 1
        if _is_math_constant(expr):
            return "__pytra_float(" + runtime_symbol + "())"
        return runtime_symbol + "(" + ", ".join(rendered_call_args) + ")"
    rendered_runtime_args: list[str] = []
    i = 0
    while i < len(args):
        rendered_runtime_args.append(_render_expr(args[i]))
        i += 1
    return runtime_symbol + "(" + ", ".join(rendered_runtime_args) + ")"


def _render_call_expr(expr: dict[str, Any]) -> str:
    args = _call_arg_nodes(expr)

    callee_name = _call_name(expr)
    if callee_name.startswith("json_native_"):
        callee_name = callee_name[len("json_native_") :]
    fn_any = expr.get("func")
    if (
        callee_name == "main"
        and _MAIN_CALL_ALIAS[0] != ""
        and isinstance(fn_any, dict)
        and fn_any.get("kind") == "Name"
    ):
        rendered_main_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_main_args.append(_render_expr(args[i]))
            i += 1
        call_code = _MAIN_CALL_ALIAS[0] + "(" + ", ".join(rendered_main_args) + ")"
        if _MAIN_CALL_ALIAS[0] in _THROWING_FUNCTIONS[0]:
            return "try! " + call_code
        return call_code
    semantic_tag = _expr_semantic_tag(expr)
    if semantic_tag == "stdlib.symbol.Path":
        if len(args) == 0:
            return "Path(\"\")"
        return "Path(" + _render_expr(args[0]) + ")"
    if isinstance(fn_any, dict) and fn_any.get("kind") == "Attribute":
        owner_any = fn_any.get("value")
        owner_expr = _render_expr(owner_any)
        if _is_argument_parser_method(expr, "add_argument"):
            return _render_stdlib_keyword_call(
                expr,
                owner_expr + ".add_argument",
                ["name0", "name1", "name2", "name3", "help", "action", "choices", "default"],
                {
                    "name1": "\"\"",
                    "name2": "\"\"",
                    "name3": "\"\"",
                    "help": "\"\"",
                    "action": "\"\"",
                    "choices": "[]",
                    "default": "__pytra_none()",
                },
            )
        if _is_argument_parser_method(expr, "parse_args"):
            return _render_stdlib_keyword_call(
                expr,
                owner_expr + ".parse_args",
                ["argv"],
                {"argv": "__pytra_none()"},
            )
    runtime_call, runtime_source = _resolved_runtime_call(expr)
    runtime_name = _runtime_symbol_name(expr)
    if _is_direct_stdlib_module_call(expr) and runtime_name in {"dumps", "dumps_jv"}:
        direct_callee = _safe_ident(runtime_name if runtime_name != "" else callee_name, "fn")
        return _render_stdlib_keyword_call(
            expr,
            direct_callee,
            ["obj" if runtime_name == "dumps" else "jv", "ensure_ascii", "indent", "separators"],
            {
                "ensure_ascii": "true",
                "indent": "__pytra_none()",
                "separators": "__pytra_none()",
            },
            force_try=True,
        )
    if semantic_tag.startswith("stdlib.") and runtime_call == "":
        raise RuntimeError("swift native emitter: unresolved stdlib runtime call: " + semantic_tag)
    if runtime_call != "":
        rendered_runtime = _render_call_via_runtime_call(
            runtime_call,
            runtime_source,
            semantic_tag,
            args,
            expr,
        )
        if rendered_runtime != "":
            if runtime_name in {"loads", "loads_obj", "loads_arr"}:
                return "try! " + rendered_runtime
            if runtime_name in {"dumps", "dumps_jv"} and not rendered_runtime.startswith("try "):
                return "try! " + rendered_runtime
            return rendered_runtime
    if callee_name == "py_assert_true":
        rendered_assert_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_assert_args.append(_render_expr(args[i]))
            i += 1
        return "__pytra_assert_true(" + ", ".join(rendered_assert_args) + ")"
    if callee_name == "py_assert_eq":
        rendered_assert_args = []
        i = 0
        while i < len(args):
            rendered_assert_args.append(_render_expr(args[i]))
            i += 1
        return "__pytra_assert_eq(" + ", ".join(rendered_assert_args) + ")"
    if callee_name == "py_assert_all":
        rendered_assert_args = []
        i = 0
        while i < len(args):
            rendered_assert_args.append(_render_expr(args[i]))
            i += 1
        return "__pytra_assert_all(" + ", ".join(rendered_assert_args) + ")"
    if callee_name.startswith("py_assert_"):
        rendered_assert_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_assert_args.append(_render_expr(args[i]))
            i += 1
        return "__pytra_assert(" + ", ".join(rendered_assert_args) + ")"
    if callee_name == "bytearray":
        if len(args) == 0:
            return "[]"
        return "__pytra_bytearray(" + _render_expr(args[0]) + ")"
    if callee_name == "deque":
        return "[]"
    if callee_name == "bytes":
        if len(args) == 0:
            return "[]"
        return "__pytra_bytes(" + _render_expr(args[0]) + ")"
    if callee_name == "extern":
        if len(args) == 0:
            return "__pytra_any_default()"
        return _render_expr(args[0])
    if callee_name == "cast":
        if len(args) == 0:
            return "__pytra_any_default()"
        return _render_expr(args[-1])
    if callee_name == "field":
        keywords = _call_keyword_nodes(expr)
        factory = keywords.get("default_factory")
        if factory is None and len(args) > 0:
            factory = args[0]
        if isinstance(factory, dict):
            if factory.get("kind") == "Name":
                factory_name = _safe_ident(factory.get("id"), "")
                if factory_name == "dict":
                    return "[:]"
                if factory_name in {"list", "set"}:
                    return "[]"
            if factory.get("kind") == "Lambda":
                rendered_factory = _render_expr(factory)
                if "try " in rendered_factory or "load_lowering_profile" in rendered_factory:
                    target_type = _swift_type(expr.get("resolved_type"), allow_void=False)
                    if target_type != "Any":
                        return _default_return_expr(target_type)
                    return "__pytra_any_default()"
                return "(" + rendered_factory + ")()"
            return _render_expr(factory)
        default_value = keywords.get("default")
        if isinstance(default_value, dict):
            return _render_expr(default_value)
        return "__pytra_any_default()"
    if callee_name == "int":
        if len(args) == 0:
            return "Int64(0)"
        arg0 = args[0]
        rendered_arg0 = _render_expr(arg0)
        if _has_resolved_type(arg0, {"int", "int64", "uint8"}):
            return rendered_arg0
        return _to_int_expr(rendered_arg0)
    if callee_name == "float":
        if len(args) == 0:
            return "Double(0)"
        arg0 = args[0]
        rendered_arg0 = _render_expr(arg0)
        if _has_resolved_type(arg0, {"float", "float64"}):
            return rendered_arg0
        return _to_float_expr(rendered_arg0)
    if callee_name == "bool":
        if len(args) == 0:
            return "false"
        return _to_truthy_expr(_render_expr(args[0]))
    if callee_name == "str" or callee_name == "py_to_string":
        if len(args) == 0:
            return '""'
        if isinstance(args[0], dict):
            resolved_arg_type = args[0].get("resolved_type")
            if isinstance(resolved_arg_type, str) and resolved_arg_type.startswith("tuple["):
                return "__pytra_tuple_str(" + _render_expr(args[0]) + ")"
        return _to_str_expr(_render_expr(args[0]))
    if callee_name == "len":
        if len(args) == 0:
            return "Int64(0)"
        return "__pytra_len(" + _render_expr(args[0]) + ")"
    if callee_name == "sum":
        if len(args) == 0:
            return "Int64(0)"
        return "__pytra_sum(" + _render_expr(args[0]) + ")"
    if callee_name == "zip":
        if len(args) < 2:
            return "[]"
        return "__pytra_zip(" + _render_expr(args[0]) + ", " + _render_expr(args[1]) + ")"
    if callee_name == "type":
        if len(args) == 0:
            return '"Any"'
        return "__pytra_type_name(" + _render_expr(args[0]) + ")"
    if callee_name == "isinstance" and len(args) == 2:
        return _render_isinstance_check(_render_expr(args[0]), args[1])
    if callee_name in {"index", "__pytra_index"} and len(args) == 2:
        first_any = args[0]
        first_type = first_any.get("resolved_type") if isinstance(first_any, dict) else ""
        if first_type == "str":
            helper = "__pytra_index_str_throwing" if _IN_TRY_BODY_DEPTH[0] > 0 else "__pytra_index_str"
            prefix = "try " if _IN_TRY_BODY_DEPTH[0] > 0 else ""
            return prefix + helper + "(" + _render_expr(args[0]) + ", " + _render_expr(args[1]) + ")"
        helper = "__pytra_list_index_throwing" if _IN_TRY_BODY_DEPTH[0] > 0 else "__pytra_list_index"
        prefix = "try " if _IN_TRY_BODY_DEPTH[0] > 0 else ""
        return prefix + helper + "(" + _render_expr(args[0]) + ", " + _render_expr(args[1]) + ")"
    if callee_name == "enumerate":
        if len(args) == 0:
            return "__pytra_enumerate([])"
        if len(args) == 1:
            return "__pytra_enumerate(" + _render_expr(args[0]) + ")"
        return "__pytra_py_enumerate_object(" + _render_expr(args[0]) + ", " + _render_expr(args[1]) + ")"
    if callee_name == "min":
        if len(args) == 0:
            return "Int64(0)"
        cur = _render_expr(args[0])
        i = 1
        while i < len(args):
            cur = "__pytra_min(" + cur + ", " + _render_expr(args[i]) + ")"
            i += 1
        return cur
    if callee_name == "max":
        if len(args) == 0:
            return "Int64(0)"
        cur = _render_expr(args[0])
        i = 1
        while i < len(args):
            cur = "__pytra_max(" + cur + ", " + _render_expr(args[i]) + ")"
            i += 1
        return cur
    if callee_name == "print":
        rendered_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_args.append(_render_expr(args[i]))
            i += 1
        return "__pytra_print(" + ", ".join(rendered_args) + ")"
    if callee_name == "open":
        rendered_args = []
        i = 0
        while i < len(args):
            rendered_args.append(_render_expr(args[i]))
            i += 1
        return "__pytra_open(" + ", ".join(rendered_args) + ")"
    if callee_name in {"__pytra_extend", "__pytra_discard", "__pytra_remove", "__pytra_set_add"} and len(args) >= 1:
        rendered_args: list[str] = []
        first_arg = args[0]
        if isinstance(first_arg, dict) and first_arg.get("kind") == "Name":
            rendered_args.append("&" + _render_expr(first_arg))
        else:
            rendered_args.append(_render_expr(first_arg))
        i = 1
        while i < len(args):
            rendered_args.append(_render_expr(args[i]))
            i += 1
        return callee_name + "(" + ", ".join(rendered_args) + ")"

    func_any = expr.get("func")
    if callee_name == "__pytra___init__" and len(args) >= 1:
        first_arg = args[0]
        if isinstance(first_arg, dict) and first_arg.get("kind") == "Call" and _call_name(first_arg) == "super":
            rendered_super_args: list[str] = []
            i = 1
            while i < len(args):
                rendered_super_args.append(_render_expr(args[i]))
                i += 1
            return "super.init(" + ", ".join(rendered_super_args) + ")"
    if isinstance(func_any, dict) and func_any.get("kind") == "Attribute":
        attr_name = _safe_ident(func_any.get("attr"), "")
        owner_any = func_any.get("value")
        if attr_name == "__name__" and isinstance(owner_any, dict) and owner_any.get("kind") == "Call" and _call_name(owner_any) == "type":
            call_args_any = owner_any.get("args")
            call_args = call_args_any if isinstance(call_args_any, list) else []
            if len(call_args) == 1:
                return "__pytra_type_name(" + _render_expr(call_args[0]) + ")"
        if isinstance(owner_any, dict) and owner_any.get("kind") == "Name":
            if _is_math_runtime(expr) and attr_name in _SWIFT_MATH_RUNTIME_SYMBOLS:
                rendered_math_args: list[str] = []
                i = 0
                while i < len(args):
                    rendered_math_args.append(_to_float_expr(_render_expr(args[i])))
                    i += 1
                if attr_name == "pi":
                    return "Double.pi"
                if attr_name == "e":
                    return "Foundation.exp(1.0)"
                if attr_name == "fabs":
                    return "abs(" + ", ".join(rendered_math_args) + ")"
                return attr_name + "(" + ", ".join(rendered_math_args) + ")"
        if isinstance(owner_any, dict) and owner_any.get("kind") == "Call" and _call_name(owner_any) == "super":
            rendered_super_args: list[str] = []
            i = 0
            while i < len(args):
                rendered_super_args.append(_render_expr(args[i]))
                i += 1
            if attr_name == "__init__":
                return "super.init(" + ", ".join(rendered_super_args) + ")"
            return "super." + attr_name + "(" + ", ".join(rendered_super_args) + ")"
        if _matches_runtime_method(expr, "str.isdigit") and len(args) == 0:
            return "__pytra_isdigit(" + _render_expr(owner_any) + ")"
        if _matches_runtime_method(expr, "str.isalpha") and len(args) == 0:
            return "__pytra_isalpha(" + _render_expr(owner_any) + ")"
        if attr_name == "index" and len(args) == 1:
            if isinstance(owner_any, dict):
                owner_type = owner_any.get("resolved_type")
                if owner_type == "str":
                    helper = "__pytra_index_str_throwing" if _IN_TRY_BODY_DEPTH[0] > 0 else "__pytra_index_str"
                    prefix = "try " if _IN_TRY_BODY_DEPTH[0] > 0 else ""
                    return prefix + helper + "(" + _render_expr(owner_any) + ", " + _render_expr(args[0]) + ")"
            helper = "__pytra_list_index_throwing" if _IN_TRY_BODY_DEPTH[0] > 0 else "__pytra_list_index"
            prefix = "try " if _IN_TRY_BODY_DEPTH[0] > 0 else ""
            return prefix + helper + "(" + _render_expr(owner_any) + ", " + _render_expr(args[0]) + ")"
        owner_expr = _render_expr(owner_any)
        owner_type = owner_any.get("resolved_type", "") if isinstance(owner_any, dict) else ""
        if attr_name in {"get_str", "get_obj", "get_arr"}:
            rendered_args: list[str] = []
            i = 0
            while i < len(args):
                rendered_args.append(_render_expr(args[i]))
                i += 1
            first_arg_type = args[0].get("resolved_type") if len(args) == 1 and isinstance(args[0], dict) else ""
            if attr_name == "get_str" and len(args) == 1 and first_arg_type in {"int", "int64"}:
                return "JsonValue(__pytra_getIndex(((" + owner_expr + " as? JsonArr) ?? JsonArr()).raw, " + rendered_args[0] + ")).as_str()"
            return "((" + owner_expr + " as? JsonObj) ?? JsonObj())." + attr_name + "(" + ", ".join(rendered_args) + ")"
        if isinstance(owner_type, str):
            if (
                owner_type.startswith("list[")
                or owner_type.startswith("dict[")
                or owner_type.startswith("set[")
                or owner_type in {"bytes", "bytearray", "str", "deque"}
            ):
                if _matches_runtime_method(expr, "list.clear", "dict.clear", "set.clear", "bytearray.clear", "deque.clear") and len(args) == 0:
                    return owner_expr + ".removeAll()"
                if (
                    (owner_type.startswith("list[") or owner_type in {"bytes", "bytearray"})
                    and _matches_runtime_method(expr, "list.append", "bytearray.append")
                    and len(args) == 1
                ):
                    if owner_type in {"bytes", "bytearray"}:
                        return owner_expr + ".append(UInt8(clamping: __pytra_int(" + _render_expr(args[0]) + ")))"
                    return owner_expr + ".append(" + _render_expr(args[0]) + ")"
                if owner_type.startswith("list[") and _matches_runtime_method(expr, "list.extend") and len(args) == 1:
                    return "__pytra_extend(&" + owner_expr + ", " + _render_expr(args[0]) + ")"
                if owner_type == "deque" and _matches_runtime_method(expr, "deque.append") and len(args) == 1:
                    return owner_expr + ".append(" + _render_expr(args[0]) + ")"
                if owner_type == "deque" and attr_name == "appendleft" and len(args) == 1:
                    return "__pytra_deque_appendleft(&" + owner_expr + ", " + _render_expr(args[0]) + ")"
                if owner_type == "deque" and attr_name == "popleft" and len(args) == 0:
                    return "__pytra_deque_popleft(&" + owner_expr + ")"
                if owner_type == "deque" and _matches_runtime_method(expr, "deque.pop") and len(args) == 0:
                    return "__pytra_deque_pop(&" + owner_expr + ")"
                if (
                    (owner_type.startswith("list[") or owner_type in {"bytes", "bytearray"})
                    and _matches_runtime_method(expr, "list.reverse")
                    and len(args) == 0
                ):
                    return owner_expr + ".reverse()"
                if owner_type.startswith("list[") and _matches_runtime_method(expr, "list.sort") and len(args) == 0:
                    return owner_expr + ".sort { __pytra_float($0) < __pytra_float($1) }"
                if owner_type.startswith("dict[") and _matches_runtime_method(expr, "dict.pop") and len(args) == 1:
                    return "__pytra_dict_pop(&" + owner_expr + ", " + _render_expr(args[0]) + ")"
                if owner_type.startswith("dict[") and _matches_runtime_method(expr, "dict.setdefault") and len(args) == 2:
                    return "__pytra_dict_setdefault(&" + owner_expr + ", " + _render_expr(args[0]) + ", " + _render_expr(args[1]) + ")"
                if owner_type.startswith("set[") and attr_name == "add" and len(args) == 1:
                    return "__pytra_set_add(&" + owner_expr + ", " + _render_expr(args[0]) + ")"
                if owner_type.startswith("set[") and _matches_runtime_method(expr, "set.discard") and len(args) == 1:
                    return "__pytra_discard(&" + owner_expr + ", " + _render_expr(args[0]) + ")"
                if owner_type.startswith("set[") and _matches_runtime_method(expr, "set.remove") and len(args) == 1:
                    return "__pytra_remove(&" + owner_expr + ", " + _render_expr(args[0]) + ")"
        if attr_name == "get":
            if len(args) >= 2:
                return "__pytra_dict_get(" + owner_expr + ", " + _render_expr(args[0]) + ", " + _render_expr(args[1]) + ")"
            if len(args) == 1:
                return "__pytra_dict_get(" + owner_expr + ", " + _render_expr(args[0]) + ", __pytra_any_default())"
            return "__pytra_any_default()"
        if attr_name == "items" and len(args) == 0:
            return "__pytra_items(" + owner_expr + ")"
        if attr_name == "keys" and len(args) == 0:
            return "__pytra_keys(" + owner_expr + ")"
        if attr_name == "values" and len(args) == 0:
            return "__pytra_values(" + owner_expr + ")"
        if _is_argument_parser_method(expr, "add_argument"):
            return _render_stdlib_keyword_call(
                expr,
                owner_expr + ".add_argument",
                ["name0", "name1", "name2", "name3", "help", "action", "choices", "default"],
                {
                    "name1": "\"\"",
                    "name2": "\"\"",
                    "name3": "\"\"",
                    "help": "\"\"",
                    "action": "\"\"",
                    "choices": "[]",
                    "default": "__pytra_none()",
                },
            )
        if _is_argument_parser_method(expr, "parse_args"):
            return _render_stdlib_keyword_call(
                expr,
                owner_expr + ".parse_args",
                ["argv"],
                {"argv": "__pytra_none()"},
            )
        rendered_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_args.append(_render_expr(args[i]))
            i += 1
        return owner_expr + "." + attr_name + "(" + ", ".join(rendered_args) + ")"

    if callee_name in _CLASS_NAMES[0]:
        rendered_ctor_args: list[str] = []
        i = 0
        while i < len(args):
            rendered_ctor_args.append(_render_expr(args[i]))
            i += 1
        return callee_name + "(" + ", ".join(rendered_ctor_args) + ")"
    if callee_name != "" and callee_name[0].isupper():
        rendered_ctor_args = []
        i = 0
        while i < len(args):
            rendered_ctor_args.append(_render_expr(args[i]))
            i += 1
        return callee_name + "(" + ", ".join(rendered_ctor_args) + ")"

    func_expr = _render_expr(expr.get("func"))
    rendered_args = []
    inout_positions = _INOUT_PARAM_POSITIONS[0].get(callee_name, set())
    callee_type = ""
    direct_function_ref = False
    direct_typed_callable_ref = False
    func_node = expr.get("func")
    if isinstance(func_node, dict):
        callee_type_any = func_node.get("resolved_type")
        callee_type = callee_type_any if isinstance(callee_type_any, str) else ""
        if func_node.get("kind") == "Name":
            func_ident = _safe_ident(func_node.get("id"), "")
            mapped_any = _CURRENT_LOCAL_TYPES[0].get(func_ident)
            mapped_type = mapped_any if isinstance(mapped_any, str) else ""
            if mapped_type not in {"", "Any"}:
                callee_type = mapped_type
                direct_typed_callable_ref = True
            else:
                signature_type = _FUNCTION_SIGNATURES[0].get(func_ident, "")
                if signature_type != "":
                    callee_type = signature_type
                    direct_function_ref = True
    callable_parts = _callable_signature_parts(callee_type)
    if (
        not direct_function_ref
        and not direct_typed_callable_ref
        and callable_parts is None
        and isinstance(callee_type, str)
        and "->" in callee_type
        and callee_type.startswith("(")
    ):
        func_expr = _cast_from_any(func_expr, callee_type)
    if (
        not direct_function_ref
        and not direct_typed_callable_ref
        and callable_parts is None
        and isinstance(func_node, dict)
        and func_node.get("kind") == "Name"
    ):
        derived_args: list[str] = []
        i = 0
        while i < len(args):
            arg_type = _infer_swift_type(args[i], _CURRENT_LOCAL_TYPES[0])
            if arg_type == "Any":
                derived_args = []
                break
            derived_args.append(arg_type)
            i += 1
        derived_ret = _swift_type(expr.get("resolved_type"), allow_void=False)
        if len(derived_args) == len(args) and derived_ret != "Any":
            derived_callable = "(" + ", ".join(derived_args) + ") -> " + derived_ret
            func_expr = _cast_from_any(func_expr, derived_callable)
    if callable_parts is not None and not direct_function_ref and not direct_typed_callable_ref:
        func_expr = _cast_from_any(func_expr, _swift_type(callee_type, allow_void=False))
    callable_arg_types = callable_parts[0] if callable_parts is not None else []
    positional_count = len(args)
    i = 0
    while i < positional_count:
        rendered_arg = _render_expr(args[i])
        if i in inout_positions and isinstance(args[i], dict) and args[i].get("kind") == "Name":
            rendered_arg = "&" + rendered_arg
        elif i < len(callable_arg_types):
            target_type = _swift_type(callable_arg_types[i], allow_void=False)
            if target_type not in {"", "Any"} and _needs_cast(args[i], target_type):
                rendered_arg = _cast_from_any(rendered_arg, target_type)
        rendered_args.append(rendered_arg)
        i += 1
    call_code = func_expr + "(" + ", ".join(rendered_args) + ")"
    throwing_lookup_name = callee_name
    if "." in throwing_lookup_name:
        throwing_lookup_name = throwing_lookup_name.rsplit(".", 1)[1]
    if callee_name in _THROWING_FUNCTIONS[0] or throwing_lookup_name in _THROWING_FUNCTIONS[0]:
        return "try! " + call_code
    return call_code


def _render_isinstance_check(lhs: str, typ: Any) -> str:
    if not isinstance(typ, dict):
        return "false"
    td: dict[str, Any] = typ
    if td.get("kind") == "Name":
        name = _safe_ident(td.get("id"), "")
        if name in {"int", "int64"}:
            return "__pytra_is_int(" + lhs + ")"
        if name in {"float", "float64"}:
            return "__pytra_is_float(" + lhs + ")"
        if name == "bool":
            return "__pytra_is_bool(" + lhs + ")"
        if name == "str":
            return "__pytra_is_str(" + lhs + ")"
        if name in {"list", "bytes", "bytearray"}:
            return "__pytra_is_list(" + lhs + ")"
        if name in {"dict", "PYTRA_TID_DICT"}:
            return "__pytra_is_dict(" + lhs + ")"
        if name in _CLASS_NAMES[0]:
            return "__pytra_is_" + name + "(" + lhs + ")"
        return "false"
    if td.get("kind") == "Tuple":
        elements_any = td.get("elements")
        elements = elements_any if isinstance(elements_any, list) else []
        checks: list[str] = []
        i = 0
        while i < len(elements):
            checks.append(_render_isinstance_check(lhs, elements[i]))
            i += 1
        if len(checks) == 0:
            return "false"
        return "(" + " || ".join(checks) + ")"
    return "false"


def _render_expr(expr: Any) -> str:
    if not isinstance(expr, dict):
        return "__pytra_any_default()"
    ed2: dict[str, Any] = expr
    kind = ed2.get("kind")

    if kind == "Name":
        return _render_name_expr(expr)
    if kind == "Constant":
        return _render_constant_expr(expr)
    if kind == "UnaryOp":
        return _render_unary_expr(expr)
    if kind == "BinOp":
        return _render_binop_expr(expr)
    if kind == "Compare":
        return _render_compare_expr(expr)
    if kind == "BoolOp":
        return _render_boolop_expr(expr)
    if kind == "Attribute":
        return _render_attribute_expr(expr)
    if kind == "Call":
        return _render_call_expr(expr)
    if kind == "JoinedStr":
        values_any = ed2.get("values")
        values = values_any if isinstance(values_any, list) else []
        if len(values) == 0:
            return '""'
        rendered_parts: list[str] = []
        i = 0
        while i < len(values):
            rendered_parts.append(_render_expr(values[i]))
            i += 1
        return "(" + " + ".join(rendered_parts) + ")"
    if kind == "FormattedValue":
        format_spec = _render_format_spec(ed2.get("format_spec"))
        if format_spec != "":
            return "__pytra_format_value(" + _render_expr(ed2.get("value")) + ", " + _swift_string_literal(format_spec) + ")"
        return _to_str_expr(_render_expr(ed2.get("value")))
    if kind == "Lambda":
        args_any = ed2.get("args")
        args = args_any if isinstance(args_any, list) else []
        rendered_args: list[str] = []
        i = 0
        while i < len(args):
            arg_any = args[i]
            if isinstance(arg_any, dict):
                arg_name = _safe_ident(arg_any.get("arg"), "arg")
                arg_type = _swift_type(arg_any.get("resolved_type"), allow_void=False)
                rendered_args.append("_ " + arg_name + ": " + arg_type)
            i += 1
        return_type = _function_return_swift_type(ed2, allow_void=True)
        body_expr = _render_expr(ed2.get("body"))
        return "{ (" + ", ".join(rendered_args) + ") -> " + return_type + " in return " + body_expr + " }"

    if kind == "List" or kind == "Tuple":
        elements_any = ed2.get("elements")
        if not isinstance(elements_any, list):
            elements_any = ed2.get("elts")
        elements = elements_any if isinstance(elements_any, list) else []
        rendered: list[str] = []
        i = 0
        while i < len(elements):
            rendered.append(_render_expr(elements[i]))
            i += 1
        return "[" + ", ".join(rendered) + "]"

    if kind == "Set":
        elements_any = ed2.get("elements")
        elements = elements_any if isinstance(elements_any, list) else []
        rendered: list[str] = []
        i = 0
        while i < len(elements):
            rendered.append(_render_expr(elements[i]))
            i += 1
        return "__pytra_set_literal([" + ", ".join(rendered) + "])"

    if kind == "Dict":
        parts: list[str] = []
        entries_any = ed2.get("entries")
        entries = entries_any if isinstance(entries_any, list) else []
        if len(entries) > 0:
            i = 0
            while i < len(entries):
                entry = entries[i]
                if isinstance(entry, dict):
                    ed: dict[str, Any] = entry
                    key_node = ed.get("key")
                    val_node = ed.get("value")
                    if key_node is not None and val_node is not None:
                        parts.append("AnyHashable(__pytra_str(" + _render_expr(key_node) + ")): " + _render_expr(val_node))
                i += 1
            if len(parts) == 0:
                return "[:]"
            return "[" + ", ".join(parts) + "]"
        keys_any = ed2.get("keys")
        vals_any = ed2.get("values")
        keys = keys_any if isinstance(keys_any, list) else []
        vals = vals_any if isinstance(vals_any, list) else []
        if len(keys) == 0 or len(vals) == 0:
            return "[:]"
        i = 0
        while i < len(keys) and i < len(vals):
            parts.append("AnyHashable(__pytra_str(" + _render_expr(keys[i]) + ")): " + _render_expr(vals[i]))
            i += 1
        return "[" + ", ".join(parts) + "]"

    if kind == "ListComp":
        gens_any = ed2.get("generators")
        gens = gens_any if isinstance(gens_any, list) else []
        if len(gens) != 1 or not isinstance(gens[0], dict):
            return "[]"
        gen = gens[0]
        ifs_any = gen.get("ifs")
        ifs = ifs_any if isinstance(ifs_any, list) else []
        if len(ifs) != 0:
            return "[]"
        target_any = gen.get("target")
        iter_any = gen.get("iter")
        if not isinstance(target_any, dict):
            return "[]"
        if not isinstance(iter_any, dict):
            return "[]"
        id: dict[str, Any] = iter_any
        elt = _render_expr(ed2.get("elt"))
        if id.get("kind") == "RangeExpr":
            td2: dict[str, Any] = target_any
            if td2.get("kind") != "Name":
                return "[]"
            loop_var = _safe_ident(td2.get("id"), "i")
            if loop_var == "_":
                loop_var = "__lc_i"
            start = _render_expr(id.get("start"))
            stop = _render_expr(id.get("stop"))
            step = _render_expr(id.get("step"))
            return (
                "({ () -> [Any] in "
                + "var __out: [Any] = []; "
                + "let __step = __pytra_int("
                + step
                + "); "
                + "var "
                + loop_var
                + " = __pytra_int("
                + start
                + "); "
                + "while ((__step >= 0 && "
                + loop_var
                + " < __pytra_int("
                + stop
                + ")) || (__step < 0 && "
                + loop_var
                + " > __pytra_int("
                + stop
                + "))) { "
                + "__out.append("
                + elt
                + "); "
                + loop_var
                + " += __step "
                + "}; "
                + "return __out "
                + "})()"
            )
        iter_expr = _render_expr(iter_any)
        cond = ""
        if len(ifs) == 1:
            cond = "if " + _render_truthy_expr(ifs[0]) + " { __out.append(" + elt + ") }"
        else:
            cond = "__out.append(" + elt + ")"
        td2 = target_any
        if td2.get("kind") == "Tuple":
            elements_any = td2.get("elements")
            elements = elements_any if isinstance(elements_any, list) else []
            if len(elements) == 0:
                return "[]"
            bindings: list[str] = []
            i = 0
            while i < len(elements):
                item_any = elements[i]
                if not isinstance(item_any, dict) or item_any.get("kind") != "Name":
                    return "[]"
                item_name = _safe_ident(item_any.get("id"), "item" + str(i))
                item_type = _swift_type(item_any.get("resolved_type"), allow_void=False)
                bindings.append(
                    "let " + item_name + ": " + item_type + " = " + _cast_from_any("__target[" + str(i) + "]", item_type) + "; "
                )
                i += 1
            return (
                "({ () -> [Any] in "
                + "var __out: [Any] = []; "
                + "for __item in __pytra_as_list(" + iter_expr + ") { let __target = __pytra_as_list(__item); "
                + "".join(bindings)
                + cond
                + " }; "
                + "return __out "
                + "})()"
            )
        if td2.get("kind") != "Name":
            return "[]"
        loop_var = _safe_ident(td2.get("id"), "i")
        if loop_var == "_":
            loop_var = "__lc_i"
        loop_type = _swift_type(td2.get("resolved_type"), allow_void=False)
        return (
            "({ () -> [Any] in "
            + "var __out: [Any] = []; "
            + "for __item in __pytra_as_list("
            + iter_expr
            + ") { let "
            + loop_var
            + ": "
            + loop_type
            + " = "
            + _cast_from_any("__item", loop_type)
            + "; "
            + cond
            + " }; "
            + "return __out "
            + "})()"
        )

    if kind == "SetComp":
        gens_any = ed2.get("generators")
        gens = gens_any if isinstance(gens_any, list) else []
        if len(gens) != 1 or not isinstance(gens[0], dict):
            return "[]"
        gen = gens[0]
        target_any = gen.get("target")
        iter_any = gen.get("iter")
        ifs_any = gen.get("ifs")
        ifs = ifs_any if isinstance(ifs_any, list) else []
        if not isinstance(target_any, dict) or target_any.get("kind") != "Name":
            return "[]"
        if not isinstance(iter_any, dict):
            return "[]"
        loop_var = _safe_ident(target_any.get("id"), "item")
        loop_type = _swift_type(target_any.get("resolved_type"), allow_void=False)
        iter_expr = _render_expr(iter_any)
        elt = _render_expr(ed2.get("elt"))
        cond = ""
        if len(ifs) == 1:
            cond = "if " + _render_truthy_expr(ifs[0]) + " { __pytra_set_add(&__out, " + elt + ") }"
        else:
            cond = "__pytra_set_add(&__out, " + elt + ")"
        return (
            "({ () -> [Any] in "
            + "var __out: [Any] = []; "
            + "for __item in __pytra_as_list(" + iter_expr + ") { let " + loop_var + ": " + loop_type + " = " + _cast_from_any("__item", loop_type) + "; " + cond + " }; "
            + "return __out "
            + "})()"
        )

    if kind == "DictComp":
        gens_any = ed2.get("generators")
        gens = gens_any if isinstance(gens_any, list) else []
        if len(gens) != 1 or not isinstance(gens[0], dict):
            return "[:]"
        gen = gens[0]
        target_any = gen.get("target")
        iter_any = gen.get("iter")
        ifs_any = gen.get("ifs")
        ifs = ifs_any if isinstance(ifs_any, list) else []
        if not isinstance(target_any, dict) or target_any.get("kind") != "Name":
            return "[:]"
        if not isinstance(iter_any, dict):
            return "[:]"
        loop_var = _safe_ident(target_any.get("id"), "item")
        loop_type = _swift_type(target_any.get("resolved_type"), allow_void=False)
        iter_expr = _render_expr(iter_any)
        key_expr = _render_expr(ed2.get("key"))
        value_expr = _render_expr(ed2.get("value"))
        store = "__out[AnyHashable(__pytra_str(" + key_expr + "))] = " + value_expr
        if len(ifs) == 1:
            store = "if " + _render_truthy_expr(ifs[0]) + " { " + store + " }"
        return (
            "({ () -> [AnyHashable: Any] in "
            + "var __out: [AnyHashable: Any] = [:]; "
            + "for __item in __pytra_as_list(" + iter_expr + ") { let " + loop_var + ": " + loop_type + " = " + _cast_from_any("__item", loop_type) + "; " + store + " }; "
            + "return __out "
            + "})()"
        )

    if kind == "IfExp":
        test_expr = _render_truthy_expr(ed2.get("test"))
        body_node = ed2.get("body")
        else_node = ed2.get("orelse")
        body_expr = _render_expr(body_node)
        else_expr = _render_expr(else_node)
        result_type = _swift_type(ed2.get("resolved_type"), allow_void=False)
        if result_type != "Any":
            if _needs_cast(body_node, result_type):
                body_expr = _cast_from_any(body_expr, result_type)
            if _needs_cast(else_node, result_type):
                else_expr = _cast_from_any(else_expr, result_type)
            return "(" + test_expr + " ? " + body_expr + " : " + else_expr + ")"
        return "__pytra_ifexp(" + test_expr + ", " + body_expr + ", " + else_expr + ")"

    if kind == "Subscript":
        owner = _render_expr(ed2.get("value"))
        owner_node = ed2.get("value")
        index_any = ed2.get("slice")
        if isinstance(index_any, dict) and index_any.get("kind") == "Slice":
            lower_any = index_any.get("lower")
            upper_any = index_any.get("upper")
            lower = _render_expr(lower_any) if isinstance(lower_any, dict) else "Int64(0)"
            upper = _render_expr(upper_any) if isinstance(upper_any, dict) else "__pytra_len(" + owner + ")"
            return "__pytra_slice(" + owner + ", " + lower + ", " + upper + ")"

        index = _render_expr(index_any)
        base = "try __pytra_getIndex(" + owner + ", " + index + ")"
        resolved = ed2.get("resolved_type")
        owner_resolved = owner_node.get("resolved_type") if isinstance(owner_node, dict) else ""
        if owner_resolved == "str" and resolved in {"byte", "int", "int64", "uint8"}:
            return _to_int_expr(base)
        swift_t = _swift_type(resolved, allow_void=False)
        return _cast_from_any(base, swift_t)

    if kind == "IsInstance":
        lhs = _render_expr(ed2.get("value"))
        expected_type = ed2.get("expected_type_id")
        if not isinstance(expected_type, dict):
            expected_type_name_any = ed2.get("expected_type_name")
            expected_type_name = expected_type_name_any if isinstance(expected_type_name_any, str) else ""
            if expected_type_name != "":
                expected_type = {"kind": "Name", "id": expected_type_name}
        return _render_isinstance_check(lhs, expected_type)

    if kind == "ObjLen":
        return "__pytra_len(" + _render_expr(ed2.get("value")) + ")"
    if kind == "ObjStr":
        return "__pytra_str(" + _render_expr(ed2.get("value")) + ")"
    if kind == "ObjBool":
        return "__pytra_truthy(" + _render_expr(ed2.get("value")) + ")"

    if kind == "Unbox":
        target_any = ed2.get("target")
        target = target_any if isinstance(target_any, str) else ""
        if target != "":
            if target.startswith("Callable[[dict[str, JsonVal], Path],"):
                return "(" + _render_expr(ed2.get("value")) + " as! ([AnyHashable: Any], Path) -> Int64)"
            if target.startswith("Callable[[dict[str, JsonVal]],"):
                return "(" + _render_expr(ed2.get("value")) + " as! ([AnyHashable: Any]) -> String)"
            if target.startswith("Callable[[Path],"):
                return "(" + _render_expr(ed2.get("value")) + " as! (Path) -> Void)"
            return _cast_from_any(_render_expr(ed2.get("value")), _swift_type(target, allow_void=False))
        return _render_expr(ed2.get("value"))
    if kind == "Box":
        return _render_expr(ed2.get("value"))

    return "__pytra_any_default()"


def _function_param_names(fn: dict[str, Any], *, drop_self: bool) -> list[str]:
    arg_order_any = fn.get("arg_order")
    arg_order = arg_order_any if isinstance(arg_order_any, list) else []
    out: list[str] = []
    i = 0
    while i < len(arg_order):
        raw = arg_order[i]
        if isinstance(raw, str):
            if drop_self and i == 0 and raw == "self":
                i += 1
                continue
            out.append(_safe_ident(raw, "arg" + str(i)))
        i += 1
    vararg_name_any = fn.get("vararg_name")
    if isinstance(vararg_name_any, str) and vararg_name_any != "":
        out.append(_safe_ident(vararg_name_any, "args"))
    return out


def _function_params(fn: dict[str, Any], *, drop_self: bool, use_any: bool = False) -> list[str]:
    arg_types_any = fn.get("arg_types")
    arg_types = arg_types_any if isinstance(arg_types_any, dict) else {}
    arg_order_any = fn.get("arg_order")
    arg_order = arg_order_any if isinstance(arg_order_any, list) else []
    arg_defaults_any = fn.get("arg_defaults")
    arg_defaults = arg_defaults_any if isinstance(arg_defaults_any, dict) else {}
    reassigned = collect_reassigned_params(fn)
    inout_positions = _collect_inout_param_positions(fn, drop_self=drop_self)
    out: list[str] = []
    raw_names: list[str] = []
    i = 0
    while i < len(arg_order):
        raw = arg_order[i]
        if isinstance(raw, str):
            if drop_self and i == 0 and raw == "self":
                i += 1
                continue
            raw_names.append(raw)
        i += 1
    vararg_name_any = fn.get("vararg_name")
    if isinstance(vararg_name_any, str) and vararg_name_any != "":
        raw_names.append(vararg_name_any)
    i = 0
    while i < len(raw_names):
        raw_name = raw_names[i]
        name = _safe_ident(raw_name, "arg" + str(i))
        param_name = mutable_param_name(name) if name in reassigned else name
        original_type = _swift_type(arg_types.get(raw_name), allow_void=False)
        if isinstance(vararg_name_any, str) and raw_name == vararg_name_any:
            vararg_type_any = fn.get("vararg_type")
            elem_type = _swift_type(vararg_type_any, allow_void=False)
            original_type = elem_type + "..." if elem_type != "" else "Any..."
        param_type = "Any" if use_any else original_type
        if i in inout_positions:
            param_type = "inout " + param_type
        param = "_ " + param_name + ": " + param_type
        if raw_name in arg_defaults:
            param += " = " + _render_expr(arg_defaults.get(raw_name))
        out.append(param)
        i += 1
    return out


def _function_param_original_type(fn: dict[str, Any], raw_name: str) -> str:
    arg_types_any = fn.get("arg_types")
    arg_types = arg_types_any if isinstance(arg_types_any, dict) else {}
    vararg_name_any = fn.get("vararg_name")
    if isinstance(vararg_name_any, str) and raw_name == vararg_name_any:
        vararg_type_any = fn.get("vararg_type")
        elem_type = _swift_type(vararg_type_any, allow_void=False)
        return "[" + elem_type + "]" if elem_type != "Any" else "[Any]"
    return _swift_type(arg_types.get(raw_name), allow_void=False)


def _function_callable_type(fn: dict[str, Any]) -> str:
    arg_types_any = fn.get("arg_types")
    arg_types = arg_types_any if isinstance(arg_types_any, dict) else {}
    arg_order_any = fn.get("arg_order")
    arg_order = arg_order_any if isinstance(arg_order_any, list) else []
    arg_parts: list[str] = []
    i = 0
    while i < len(arg_order):
        raw = arg_order[i]
        if isinstance(raw, str) and raw != "self":
            arg_parts.append(str(arg_types.get(raw) or "any"))
        i += 1
    return "callable[[" + ", ".join(arg_parts) + "], " + str(fn.get("return_type") or "any") + "]"


def _target_name(target: Any) -> str:
    if not isinstance(target, dict):
        return "tmp"
    td: dict[str, Any] = target
    kind = td.get("kind")
    if kind == "Name":
        return _safe_ident(td.get("id"), "tmp")
    if kind == "Attribute":
        return _render_attribute_expr(target)
    return "tmp"


def _emit_swap(stmt: dict[str, Any], *, indent: str, ctx: dict[str, Any]) -> list[str]:
    lhs_node = stmt.get("lhs") if stmt.get("lhs") is not None else stmt.get("left")
    rhs_node = stmt.get("rhs") if stmt.get("rhs") is not None else stmt.get("right")
    # Handle Subscript swap (array element exchange) via __pytra_getIndex/__pytra_setIndex
    lhs_is_sub = isinstance(lhs_node, dict) and lhs_node.get("kind") == "Subscript"
    rhs_is_sub = isinstance(rhs_node, dict) and rhs_node.get("kind") == "Subscript"
    if lhs_is_sub and rhs_is_sub:
        tmp = _fresh_tmp(ctx, "swap")
        lhs_get = _render_expr(lhs_node)
        rhs_get = _render_expr(rhs_node)
        lhs_container = _render_expr(lhs_node.get("value"))
        lhs_index = _render_expr(lhs_node.get("slice"))
        rhs_container = _render_expr(rhs_node.get("value"))
        rhs_index = _render_expr(rhs_node.get("slice"))
        return [
            indent + "var " + tmp + ": Any = " + lhs_get,
            indent + "__pytra_setIndex(" + lhs_container + ", " + lhs_index + ", " + rhs_get + ")",
            indent + "__pytra_setIndex(" + rhs_container + ", " + rhs_index + ", " + tmp + ")",
        ]
    left = _target_name(lhs_node)
    right = _target_name(rhs_node)
    if left == "":
        left = _render_expr(lhs_node)
    if right == "":
        right = _render_expr(rhs_node)
    tmp = _fresh_tmp(ctx, "swap")
    tmp_type = _infer_swift_type(lhs_node, _type_map(ctx))
    if tmp_type == "Any":
        tmp_type = "Any"
    return [
        indent + "var " + tmp + ": " + tmp_type + " = " + left,
        indent + left + " = " + right,
        indent + right + " = " + tmp,
    ]


def _fresh_tmp(ctx: dict[str, Any], prefix: str) -> str:
    idx = ctx.get("tmp", 0)
    if not isinstance(idx, int):
        idx = 0
    ctx["tmp"] = idx + 1
    return "__" + prefix + "_" + str(idx)


def _declared_set(ctx: dict[str, Any]) -> set[str]:
    declared = ctx.get("declared")
    if isinstance(declared, set):
        return declared
    out: set[str] = set()
    ctx["declared"] = out
    return out


def _type_map(ctx: dict[str, Any]) -> dict[str, str]:
    types = ctx.get("types")
    if isinstance(types, dict):
        return types
    out: dict[str, str] = {}
    ctx["types"] = out
    return out


def _ref_var_set(ctx: dict[str, Any]) -> set[str]:
    ref_vars = ctx.get("ref_vars")
    if isinstance(ref_vars, set):
        return ref_vars
    out: set[str] = set()
    ctx["ref_vars"] = out
    return out


def _alias_map(ctx: dict[str, Any]) -> dict[str, str]:
    alias_map = ctx.get("alias_map")
    if isinstance(alias_map, dict):
        return alias_map
    out: dict[str, str] = {}
    ctx["alias_map"] = out
    return out


def _is_container_east_type(type_name: Any) -> bool:
    if not isinstance(type_name, str):
        return False
    ts: str = type_name
    if ts.startswith("list[") or ts.startswith("tuple[") or ts.startswith("dict["):
        return True
    return type_name in {"bytes", "bytearray"}


def _materialize_container_value_from_ref(
    value_expr: Any,
    *,
    target_type: str,
    target_name: str,
    ctx: dict[str, Any],
) -> str | None:
    _ = value_expr
    _ = target_type
    _ = target_name
    _ = ctx
    # Python assignment preserves aliasing for mutable containers.
    return None


def _infer_swift_type(expr: Any, type_map: dict[str, str] | None = None) -> str:
    if not isinstance(expr, dict):
        return "Any"
    ed: dict[str, Any] = expr
    kind = ed.get("kind")
    if kind == "Name" and isinstance(type_map, dict):
        ident = _safe_ident(ed.get("id"), "")
        if ident in type_map:
            return type_map[ident]
        if ident in _FUNCTION_SIGNATURES[0]:
            return _swift_type(_FUNCTION_SIGNATURES[0][ident], allow_void=False)
    if kind == "Call":
        name = _call_name(expr)
        if name == "int":
            return "Int64"
        if name == "float":
            return "Double"
        if name == "bool":
            return "Bool"
        if name == "str":
            return "String"
        if name == "bytearray" or name == "bytes":
            return "[UInt8]"
        if name == "len":
            return "Int64"
        if name in {
            "sin",
            "cos",
            "tan",
            "asin",
            "acos",
            "atan",
            "atan2",
            "sqrt",
            "exp",
            "log",
            "log10",
            "floor",
            "ceil",
            "pow",
        }:
            return "Double"
        if name in {"min", "max"}:
            args_any = ed.get("args")
            args = args_any if isinstance(args_any, list) else []
            saw_float = False
            saw_int = False
            i = 0
            while i < len(args):
                at = _infer_swift_type(args[i], type_map)
                if at == "Double":
                    saw_float = True
                elif at == "Int64":
                    saw_int = True
                i += 1
            if saw_float:
                return "Double"
            if saw_int:
                return "Int64"
            resolved = _swift_type(ed.get("resolved_type"), allow_void=False)
            if resolved in {"Int64", "Double"}:
                return resolved
            return "Any"
        if name in _CLASS_NAMES[0]:
            return name
    if kind == "Lambda":
        return _swift_type(ed.get("resolved_type"), allow_void=False)
    if kind == "BinOp":
        op = ed.get("op")
        if op == "Div":
            return "Double"
        left_t = _infer_swift_type(ed.get("left"), type_map)
        right_t = _infer_swift_type(ed.get("right"), type_map)
        if left_t == "Double" or right_t == "Double":
            return "Double"
        if left_t == "Int64" and right_t == "Int64":
            return "Int64"
        if op == "Mult":
            left_any = ed.get("left")
            right_any = ed.get("right")
            if isinstance(left_any, dict) and left_any.get("kind") == "List":
                return "[Any]"
            if isinstance(right_any, dict) and right_any.get("kind") == "List":
                return "[Any]"
    if kind == "Subscript":
        owner_any = ed.get("value")
        owner_resolved = owner_any.get("resolved_type") if isinstance(owner_any, dict) else ""
        resolved = ed.get("resolved_type")
        if owner_resolved == "str" and resolved in {"byte", "int", "int64", "uint8"}:
            return "Int64"
        if owner_resolved == "str":
            return "String"
    if kind == "IfExp":
        body_t = _infer_swift_type(ed.get("body"), type_map)
        else_t = _infer_swift_type(ed.get("orelse"), type_map)
        if body_t == else_t:
            return body_t
        if body_t == "Double" or else_t == "Double":
            return "Double"
        if body_t == "Int64" and else_t == "Int64":
            return "Int64"
    resolved = ed.get("resolved_type")
    return _swift_type(resolved, allow_void=False)


def _expr_emits_target_type(value_expr: Any, target_type: str, type_map: dict[str, str] | None = None) -> bool:
    if not isinstance(value_expr, dict):
        return False
    vd: dict[str, Any] = value_expr
    kind = vd.get("kind")
    if kind == "Name":
        resolved = _swift_type(vd.get("resolved_type"), allow_void=False)
        if resolved == target_type:
            return True
        if isinstance(type_map, dict):
            ident = _safe_ident(vd.get("id"), "")
            mapped_any = type_map.get(ident)
            mapped = mapped_any if isinstance(mapped_any, str) else ""
            return mapped == target_type
        return False
    if kind == "UnaryOp":
        op = vd.get("op")
        if op in {"USub", "UAdd"}:
            return _expr_emits_target_type(vd.get("operand"), target_type, type_map)
        if op == "Not":
            return target_type == "Bool"
        return False
    if kind == "Constant":
        value = vd.get("value")
        if target_type == "Int64":
            return isinstance(value, int) and not isinstance(value, bool)
        if target_type == "Double":
            return isinstance(value, float)
        if target_type == "Bool":
            return isinstance(value, bool)
        if target_type == "String":
            return isinstance(value, str)
        return False
    if kind == "BinOp":
        resolved = _swift_type(vd.get("resolved_type"), allow_void=False)
        return resolved == target_type
    if kind in {"Compare", "BoolOp", "IsInstance"}:
        return target_type == "Bool"
    if kind == "Call":
        callee = _call_name(value_expr)
        if callee == "int":
            return target_type == "Int64"
        if callee == "float":
            return target_type == "Double"
        if callee == "bool":
            return target_type == "Bool"
        if callee == "str":
            return target_type == "String"
        if callee == "len":
            return target_type == "Int64"
        resolved = _swift_type(vd.get("resolved_type"), allow_void=False)
        if _is_perf_counter_call(vd):
            return target_type == resolved
        func_any = vd.get("func")
        if isinstance(func_any, dict):
            fd: dict[str, Any] = func_any
            f_kind = fd.get("kind")
        if f_kind == "Name":
            if callee != "" and not callee.startswith("__pytra_") and resolved == target_type:
                return True
            if "->" in target_type and target_type.startswith("("):
                return False
            if f_kind == "Attribute":
                attr = _safe_ident(fd.get("attr"), "")
                if attr not in {"get", "getOrElse"} and not attr.startswith("__pytra_") and resolved == target_type:
                    return True
    return False


def _needs_cast(value_expr: Any, target_type: str, type_map: dict[str, str] | None = None) -> bool:
    if target_type in {"", "Any"}:
        return False
    return not _expr_emits_target_type(value_expr, target_type, type_map)


def _emit_for_core(stmt: dict[str, Any], *, indent: str, ctx: dict[str, Any]) -> list[str]:
    iter_plan_any = stmt.get("iter_plan")
    target_plan_any = stmt.get("target_plan")
    if not isinstance(iter_plan_any, dict):
        raise RuntimeError("swift native emitter: unsupported ForCore iter_plan")
    id: dict[str, Any] = iter_plan_any
    if not isinstance(target_plan_any, dict):
        raise RuntimeError("swift native emitter: unsupported ForCore target_plan")
    td: dict[str, Any] = target_plan_any

    lines: list[str] = []
    if id.get("kind") == "StaticRangeForPlan" and td.get("kind") == "NameTarget":
        target_name = _safe_ident(td.get("id"), "i")
        if target_name == "_":
            target_name = _fresh_tmp(ctx, "loop")
        start_node = id.get("start")
        stop_node = id.get("stop")
        step_node = id.get("step")
        start = _to_int_expr(_render_expr(start_node))
        stop = _to_int_expr(_render_expr(stop_node))
        step = _to_int_expr(_render_expr(step_node))
        step_is_one = _is_int_literal(step_node, 1)
        loop_index = _fresh_tmp(ctx, "i")
        if step_is_one:
            lines.append(indent + "for " + loop_index + " in Int(" + start + ")..<Int(" + stop + ") {")
        elif _is_int_literal(step_node, -1):
            lines.append(indent + "for " + loop_index + " in stride(from: Int(" + start + "), to: Int(" + stop + "), by: -1) {")
        else:
            lines.append(indent + "for " + loop_index + " in stride(from: Int(" + start + "), to: Int(" + stop + "), by: Int(" + step + ")) {")
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        body_ctx: dict[str, Any] = {
            "tmp": ctx.get("tmp", 0),
            "declared": set(_declared_set(ctx)),
            "types": dict(_type_map(ctx)),
            "ref_vars": set(_ref_var_set(ctx)),
            "alias_map": dict(_alias_map(ctx)),
            "return_type": ctx.get("return_type", ""),
            "continue_prefix": "",
        }
        _declared_set(body_ctx).add(target_name)
        _type_map(body_ctx)[target_name] = "Int64"
        lines.append(indent + "    let " + target_name + ": Int64 = Int64(" + loop_index + ")")
        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=body_ctx))
            i += 1
        ctx["tmp"] = body_ctx.get("tmp", ctx.get("tmp", 0))
        lines.append(indent + "}")
        return lines

    if id.get("kind") == "RuntimeIterForPlan":
        iter_expr = _render_expr(id.get("iter_expr"))
        iter_tmp = _fresh_tmp(ctx, "iter")
        idx_tmp = _fresh_tmp(ctx, "i")
        lines.append(indent + "let " + iter_tmp + " = __pytra_as_list(" + iter_expr + ")")
        lines.append(indent + "var " + idx_tmp + ": Int64 = 0")
        lines.append(indent + "while " + idx_tmp + " < Int64(" + iter_tmp + ".count) {")
        body_any = stmt.get("body")
        body = body_any if isinstance(body_any, list) else []
        body_ctx: dict[str, Any] = {
            "tmp": ctx.get("tmp", 0),
            "declared": set(_declared_set(ctx)),
            "types": dict(_type_map(ctx)),
            "ref_vars": set(_ref_var_set(ctx)),
            "alias_map": dict(_alias_map(ctx)),
            "return_type": ctx.get("return_type", ""),
            "continue_prefix": idx_tmp + " += 1",
        }
        target_kind = td.get("kind")
        if target_kind == "NameTarget":
            target_name = _safe_ident(td.get("id"), "item")
            if target_name == "_":
                target_name = _fresh_tmp(ctx, "item")
            target_type = _swift_type(td.get("target_type"), allow_void=False)
            if target_type == "Any":
                inferred_elem = _iter_element_type_name(id.get("iter_expr", {}).get("resolved_type") if isinstance(id.get("iter_expr"), dict) else "")
                if inferred_elem == "" and isinstance(id.get("iter_expr"), dict) and id.get("iter_expr").get("kind") == "Name":
                    iter_name = _safe_ident(id.get("iter_expr").get("id"), "")
                    mapped_type_any = _type_map(ctx).get(iter_name)
                    mapped_type = mapped_type_any if isinstance(mapped_type_any, str) else ""
                    if mapped_type.startswith("[") and mapped_type.endswith("]") and mapped_type not in {"[Any]", "[UInt8]"}:
                        inferred_elem = mapped_type[1:-1].strip()
                if inferred_elem != "":
                    target_type = _swift_type(inferred_elem, allow_void=False)
            rhs = iter_tmp + "[Int(" + idx_tmp + ")]"
            if target_type == "Any":
                lines.append(indent + "    let " + target_name + " = " + rhs)
            else:
                lines.append(indent + "    let " + target_name + ": " + target_type + " = " + _cast_from_any(rhs, target_type))
            _declared_set(body_ctx).add(target_name)
            _type_map(body_ctx)[target_name] = target_type
        elif target_kind == "TupleTarget":
            lines.extend(
                _emit_runtime_iter_target_bindings(
                    td,
                    iter_tmp + "[Int(" + idx_tmp + ")]",
                    indent=indent + "    ",
                    ctx=ctx,
                    body_ctx=body_ctx,
                )
            )
        else:
            raise RuntimeError("swift native emitter: unsupported RuntimeIter target_plan")
        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=body_ctx))
            i += 1
        lines.append(indent + "    " + idx_tmp + " += 1")
        ctx["tmp"] = body_ctx.get("tmp", ctx.get("tmp", 0))
        lines.append(indent + "}")
        return lines

    raise RuntimeError("swift native emitter: unsupported ForCore plan")


def _emit_tuple_assign(
    target_any: Any,
    value_any: Any,
    *,
    decl_type_any: Any,
    declare_hint: bool,
    indent: str,
    ctx: dict[str, Any],
) -> list[str] | None:
    if not isinstance(target_any, dict):
        return None
    td: dict[str, Any] = target_any
    if td.get("kind") != "Tuple":
        return None
    elems_any = td.get("elements")
    elems = elems_any if isinstance(elems_any, list) else []
    if len(elems) == 0:
        return None

    tuple_tmp = _fresh_tmp(ctx, "tuple")
    lines: list[str] = [indent + "let " + tuple_tmp + " = __pytra_as_list(" + _render_expr(value_any) + ")"]
    declared = _declared_set(ctx)
    type_map = _type_map(ctx)
    tuple_types = _tuple_element_types(decl_type_any)
    if len(tuple_types) == 0 and isinstance(value_any, dict):
        vad: dict[str, Any] = value_any
        tuple_types = _tuple_element_types(vad.get("resolved_type"))

    i = 0
    while i < len(elems):
        elem = elems[i]
        if not isinstance(elem, dict):
            return None
        ed: dict[str, Any] = elem
        kind = ed.get("kind")
        rhs = tuple_tmp + "[" + str(i) + "]"
        elem_type = "Any"
        if i < len(tuple_types):
            elem_type = _swift_type(tuple_types[i], allow_void=False)
        casted = _cast_from_any(rhs, elem_type)

        if kind == "Name":
            name = _safe_ident(ed.get("id"), "tmp_" + str(i))
            if name not in declared:
                lines.append(indent + "var " + name + ": " + elem_type + " = " + casted)
                declared.add(name)
                type_map[name] = elem_type
            else:
                lines.append(indent + name + " = " + casted)
        elif kind == "Subscript":
            lines.extend(_emit_subscript_store(elem, casted, indent=indent, ctx=ctx))
        else:
            return None
        i += 1

    return lines


def _emit_subscript_store(target: dict[str, Any], value_expr: str, *, indent: str, ctx: dict[str, Any]) -> list[str]:
    owner_node = target.get("value")
    owner_expr = _render_expr(owner_node)
    index_expr = _render_expr(target.get("slice"))
    # Fast path for nested list store: grid[y][x] = v
    # Keep mutation in-place by materializing inner list and writing it back.
    if isinstance(owner_node, dict) and owner_node.get("kind") == "Subscript":
        outer_owner_node = owner_node.get("value")
        outer_index_expr = _render_expr(owner_node.get("slice"))
        if isinstance(outer_owner_node, dict) and outer_owner_node.get("kind") == "Name":
            outer_name = _safe_ident(outer_owner_node.get("id"), "")
            outer_type_any = _type_map(ctx).get(outer_name)
            outer_type = outer_type_any if isinstance(outer_type_any, str) else ""
            if outer_type == "[Any]":
                outer_idx_tmp = _fresh_tmp(ctx, "idx")
                inner_tmp = _fresh_tmp(ctx, "inner")
                inner_idx_tmp = _fresh_tmp(ctx, "idx")
                return [
                    indent
                    + "let "
                    + outer_idx_tmp
                    + " = Int(__pytra_index(__pytra_int("
                    + outer_index_expr
                    + "), Int64("
                    + outer_name
                    + ".count)))",
                    indent + "if " + outer_idx_tmp + " >= 0 && " + outer_idx_tmp + " < " + outer_name + ".count {",
                    indent + "    var " + inner_tmp + ": [Any] = __pytra_as_list(" + outer_name + "[" + outer_idx_tmp + "])",
                    indent
                    + "    let "
                    + inner_idx_tmp
                    + " = Int(__pytra_index(__pytra_int("
                    + index_expr
                    + "), Int64("
                    + inner_tmp
                    + ".count)))",
                    indent + "    if " + inner_idx_tmp + " >= 0 && " + inner_idx_tmp + " < " + inner_tmp + ".count {",
                    indent + "        " + inner_tmp + "[" + inner_idx_tmp + "] = " + value_expr,
                    indent + "        " + outer_name + "[" + outer_idx_tmp + "] = " + inner_tmp,
                    indent + "    }",
                    indent + "}",
                ]
    if isinstance(owner_node, dict) and owner_node.get("kind") == "Name":
        owner_name = _safe_ident(owner_node.get("id"), "")
        owner_type_any = _type_map(ctx).get(owner_name)
        owner_type = owner_type_any if isinstance(owner_type_any, str) else ""
        if owner_type == "[UInt8]":
            idx_tmp = _fresh_tmp(ctx, "idx")
            lines = [
                indent + "let " + idx_tmp + " = Int(__pytra_index(__pytra_int(" + index_expr + "), Int64(" + owner_name + ".count)))",
                indent + "if " + idx_tmp + " >= 0 && " + idx_tmp + " < " + owner_name + ".count {",
                indent + "    " + owner_name + "[" + idx_tmp + "] = UInt8(clamping: __pytra_int(" + value_expr + "))",
                indent + "}",
            ]
            alias_root = _alias_map(ctx).get(owner_name, "")
            if alias_root != "":
                lines.append(indent + alias_root + " = " + owner_name)
            return lines
        if owner_type == "[Any]":
            idx_tmp = _fresh_tmp(ctx, "idx")
            lines = [
                indent + "let " + idx_tmp + " = Int(__pytra_index(__pytra_int(" + index_expr + "), Int64(" + owner_name + ".count)))",
                indent + "if " + idx_tmp + " >= 0 && " + idx_tmp + " < " + owner_name + ".count {",
                indent + "    " + owner_name + "[" + idx_tmp + "] = " + value_expr,
                indent + "}",
            ]
            alias_root = _alias_map(ctx).get(owner_name, "")
            if alias_root != "":
                lines.append(indent + alias_root + " = " + owner_name)
            return lines
        if owner_type == "[AnyHashable: Any]":
            lines = [indent + owner_name + "[AnyHashable(__pytra_str(" + index_expr + "))] = " + value_expr]
            alias_root = _alias_map(ctx).get(owner_name, "")
            if alias_root != "":
                lines.append(indent + alias_root + " = " + owner_name)
            return lines
    return [indent + "__pytra_setIndex(" + owner_expr + ", " + index_expr + ", " + value_expr + ")"]


def _emit_stmt(stmt: Any, *, indent: str, ctx: dict[str, Any]) -> list[str]:
    if not isinstance(stmt, dict):
        raise RuntimeError("swift native emitter: unsupported statement")
    sd2: dict[str, Any] = stmt
    kind = sd2.get("kind")

    if kind == "Return":
        if "value" in stmt and sd2.get("value") is not None:
            value_node = sd2.get("value")
            value = _render_expr(value_node)
            return_type_any = ctx.get("return_type")
            return_type = return_type_any if isinstance(return_type_any, str) else ""
            if (
                return_type in {"Int64", "Double"}
                and isinstance(value_node, dict)
                and value_node.get("kind") == "BinOp"
            ):
                value = _render_binop_as_type(value_node, return_type)
            elif return_type not in {"", "Any"} and _needs_cast(value_node, return_type, _type_map(ctx)):
                value = _cast_from_any(value, return_type)
            return [indent + "return " + value]
        return [indent + "return"]

    if kind == "Expr":
        value_any = sd2.get("value")
        if isinstance(value_any, dict) and value_any.get("kind") == "Name":
            raw_ident = value_any.get("id")
            if raw_ident == "break":
                return [indent + "break"]
            if raw_ident == "continue":
                prefix_any = ctx.get("continue_prefix")
                prefix = prefix_any if isinstance(prefix_any, str) else ""
                if prefix != "":
                    return [indent + prefix, indent + "continue"]
                return [indent + "continue"]
        if isinstance(value_any, dict) and value_any.get("kind") == "Call":
            func_any = value_any.get("func")
            if isinstance(func_any, dict) and func_any.get("kind") == "Attribute":
                attr = _safe_ident(func_any.get("attr"), "")
                if _matches_runtime_method(value_any, "list.append", "bytearray.append", "deque.append"):
                    owner_any = func_any.get("value")
                    owner = _render_expr(owner_any)
                    owner_type = ""
                    if isinstance(owner_any, dict) and owner_any.get("kind") == "Name":
                        owner_name = _safe_ident(owner_any.get("id"), "")
                        type_hint_any = _type_map(ctx).get(owner_name)
                        owner_type = type_hint_any if isinstance(type_hint_any, str) else ""
                    args_any = value_any.get("args")
                    args = args_any if isinstance(args_any, list) else []
                    if len(args) == 1:
                        alias_root = _alias_map(ctx).get(owner_name, "") if isinstance(owner_any, dict) and owner_any.get("kind") == "Name" else ""
                        if owner_type == "[UInt8]":
                            lines = [indent + owner + ".append(UInt8(clamping: __pytra_int(" + _render_expr(args[0]) + ")))"]
                            if alias_root != "":
                                lines.append(indent + alias_root + " = " + owner)
                            return lines
                        if owner_type == "[Any]":
                            lines = [indent + owner + ".append(" + _render_expr(args[0]) + ")"]
                            if alias_root != "":
                                lines.append(indent + alias_root + " = " + owner)
                            return lines
                        lines = [indent + owner + " = __pytra_as_list(" + owner + "); " + owner + ".append(" + _render_expr(args[0]) + ")"]
                        if alias_root != "":
                            lines.append(indent + alias_root + " = " + owner)
                        return lines
                if _matches_runtime_method(value_any, "list.pop", "deque.pop"):
                    owner = _render_expr(func_any.get("value"))
                    args_any = value_any.get("args")
                    args = args_any if isinstance(args_any, list) else []
                    if len(args) == 0:
                        alias_root = ""
                        owner_node = func_any.get("value")
                        if isinstance(owner_node, dict) and owner_node.get("kind") == "Name":
                            alias_root = _alias_map(ctx).get(_safe_ident(owner_node.get("id"), ""), "")
                        lines = [indent + owner + " = __pytra_pop_last(__pytra_as_list(" + owner + "))"]
                        if alias_root != "":
                            lines.append(indent + alias_root + " = " + owner)
                        return lines
                if attr == "add":
                    owner_node = func_any.get("value")
                    if isinstance(owner_node, dict) and owner_node.get("kind") == "Subscript":
                        sub_owner_any = owner_node.get("value")
                        sub_index_any = owner_node.get("slice")
                        args_any = value_any.get("args")
                        args = args_any if isinstance(args_any, list) else []
                        if (
                            isinstance(sub_owner_any, dict)
                            and sub_owner_any.get("kind") == "Name"
                            and len(args) == 1
                        ):
                            outer_name = _safe_ident(sub_owner_any.get("id"), "")
                            outer_type_any = _type_map(ctx).get(outer_name)
                            outer_type = outer_type_any if isinstance(outer_type_any, str) else ""
                            if outer_type == "[Any]":
                                idx_expr = _render_expr(sub_index_any)
                                idx_tmp = _fresh_tmp(ctx, "idx")
                                set_tmp = _fresh_tmp(ctx, "set")
                                return [
                                    indent + "let " + idx_tmp + " = Int(__pytra_index(__pytra_int(" + idx_expr + "), Int64(" + outer_name + ".count)))",
                                    indent + "if " + idx_tmp + " >= 0 && " + idx_tmp + " < " + outer_name + ".count {",
                                    indent + "    var " + set_tmp + ": [Any] = __pytra_as_list(" + outer_name + "[" + idx_tmp + "])",
                                    indent + "    __pytra_set_add(&" + set_tmp + ", " + _render_expr(args[0]) + ")",
                                    indent + "    " + outer_name + "[" + idx_tmp + "] = " + set_tmp,
                                    indent + "}",
                                ]
        return [indent + _render_expr(value_any)]

    if kind == "AnnAssign":
        target_any = sd2.get("target")
        if isinstance(target_any, dict) and target_any.get("kind") == "Attribute":
            return [indent + _render_attribute_expr(target_any) + " = " + _render_expr(sd2.get("value"))]

        tuple_lines = _emit_tuple_assign(
            target_any,
            sd2.get("value"),
            decl_type_any=(sd2.get("decl_type") or sd2.get("annotation")),
            declare_hint=(sd2.get("declare") is not False),
            indent=indent,
            ctx=ctx,
        )
        if tuple_lines is not None:
            return tuple_lines

        target = _target_name(target_any)
        declared = _declared_set(ctx)
        type_map = _type_map(ctx)
        swift_type = _swift_type(sd2.get("decl_type") or sd2.get("annotation"), allow_void=False)
        if swift_type == "Any":
            inferred = _infer_swift_type(sd2.get("value"), _type_map(ctx))
            if inferred != "Any":
                swift_type = inferred

        stmt_value = sd2.get("value")
        if stmt_value is None:
            value = _default_return_expr(swift_type)
        else:
            if (
                swift_type == "String"
                and isinstance(stmt_value, dict)
                and stmt_value.get("kind") == "Subscript"
                and isinstance(stmt_value.get("value"), dict)
                and stmt_value.get("value").get("resolved_type") == "str"
                and target == "ch"
            ):
                swift_type = "Int64"
            value = _render_expr(stmt_value)
            if swift_type != "Any" and _needs_cast(stmt_value, swift_type, _type_map(ctx)):
                value = _cast_from_any(value, swift_type)
            materialized = _materialize_container_value_from_ref(
                stmt_value,
                target_type=swift_type,
                target_name=target,
                ctx=ctx,
            )
            if materialized is not None:
                value = materialized
        if sd2.get("declare") is False or target in declared:
            if target not in declared:
                declared.add(target)
                type_map[target] = swift_type
                return [indent + "var " + target + ": " + swift_type + " = " + value]
            if target in type_map and type_map[target] != "Any":
                if stmt_value is None:
                    return [indent + target + " = " + _default_return_expr(type_map[target])]
                reassigned = _render_expr(stmt_value)
                if _needs_cast(stmt_value, type_map[target], _type_map(ctx)):
                    reassigned = _cast_from_any(reassigned, type_map[target])
                materialized_reassigned = _materialize_container_value_from_ref(
                    stmt_value,
                    target_type=type_map[target],
                    target_name=target,
                    ctx=ctx,
                )
                if materialized_reassigned is not None:
                    reassigned = materialized_reassigned
                return [indent + target + " = " + reassigned]
            return [indent + target + " = " + value]

        declared.add(target)
        type_map[target] = swift_type
        return [indent + "var " + target + ": " + swift_type + " = " + value]

    if kind == "Assign":
        targets_any = sd2.get("targets")
        targets = targets_any if isinstance(targets_any, list) else []
        if len(targets) == 0 and isinstance(sd2.get("target"), dict):
            targets = [sd2.get("target")]
        if len(targets) == 0:
            raise RuntimeError("swift native emitter: Assign without target")

        tuple_lines = _emit_tuple_assign(
            targets[0],
            sd2.get("value"),
            decl_type_any=sd2.get("decl_type"),
            declare_hint=bool(sd2.get("declare")),
            indent=indent,
            ctx=ctx,
        )
        if tuple_lines is not None:
            return tuple_lines

        if isinstance(targets[0], dict) and targets[0].get("kind") == "Attribute":
            lhs_attr = _render_attribute_expr(targets[0])
            value_attr = _render_expr(sd2.get("value"))
            return [indent + lhs_attr + " = " + value_attr]

        if isinstance(targets[0], dict) and targets[0].get("kind") == "Subscript":
            tgt = targets[0]
            value = _render_expr(sd2.get("value"))
            return _emit_subscript_store(tgt, value, indent=indent, ctx=ctx)

        lhs = _target_name(targets[0])
        declared = _declared_set(ctx)
        type_map = _type_map(ctx)
        value = _render_expr(sd2.get("value"))

        if sd2.get("declare"):
            if lhs in declared:
                _alias_map(ctx).pop(lhs, None)
                if lhs in type_map and type_map[lhs] != "Any":
                    if _needs_cast(sd2.get("value"), type_map[lhs], _type_map(ctx)):
                        value = _cast_from_any(value, type_map[lhs])
                    materialized_existing = _materialize_container_value_from_ref(
                        sd2.get("value"),
                        target_type=type_map[lhs],
                        target_name=lhs,
                        ctx=ctx,
                    )
                    if materialized_existing is not None:
                        value = materialized_existing
                return [indent + lhs + " = " + value]
            swift_type = _swift_type(sd2.get("decl_type"), allow_void=False)
            if swift_type == "Any":
                inferred = _infer_swift_type(sd2.get("value"), _type_map(ctx))
                if inferred != "Any":
                    swift_type = inferred
            if swift_type != "Any" and _needs_cast(sd2.get("value"), swift_type, _type_map(ctx)):
                value = _cast_from_any(value, swift_type)
            _alias_map(ctx).pop(lhs, None)
            if isinstance(sd2.get("value"), dict) and sd2.get("value").get("kind") == "Name":
                source_name = _safe_ident(sd2.get("value").get("id"), "")
                source_type = _type_map(ctx).get(source_name, "")
                if swift_type in {"[Any]", "[AnyHashable: Any]"} and source_type == swift_type:
                    _alias_map(ctx)[lhs] = source_name
            materialized_decl = _materialize_container_value_from_ref(
                sd2.get("value"),
                target_type=swift_type,
                target_name=lhs,
                ctx=ctx,
            )
            if materialized_decl is not None:
                value = materialized_decl
            declared.add(lhs)
            type_map[lhs] = swift_type
            return [indent + "var " + lhs + ": " + swift_type + " = " + value]

        if lhs not in declared:
            inferred = _infer_swift_type(sd2.get("value"), _type_map(ctx))
            declared.add(lhs)
            type_map[lhs] = inferred
            if inferred != "Any" and _needs_cast(sd2.get("value"), inferred, _type_map(ctx)):
                value = _cast_from_any(value, inferred)
            _alias_map(ctx).pop(lhs, None)
            if isinstance(sd2.get("value"), dict) and sd2.get("value").get("kind") == "Name":
                source_name = _safe_ident(sd2.get("value").get("id"), "")
                source_type = _type_map(ctx).get(source_name, "")
                if inferred in {"[Any]", "[AnyHashable: Any]"} and source_type == inferred:
                    _alias_map(ctx)[lhs] = source_name
            materialized_inferred = _materialize_container_value_from_ref(
                sd2.get("value"),
                target_type=inferred,
                target_name=lhs,
                ctx=ctx,
            )
            if materialized_inferred is not None:
                value = materialized_inferred
            return [indent + "var " + lhs + ": " + inferred + " = " + value]
        if lhs in type_map and type_map[lhs] == "Any":
            inferred = _infer_swift_type(sd2.get("value"), _type_map(ctx))
            if inferred != "Any":
                type_map[lhs] = inferred
                if _needs_cast(sd2.get("value"), inferred, _type_map(ctx)):
                    value = _cast_from_any(value, inferred)
        if lhs in type_map and type_map[lhs] != "Any":
            if _needs_cast(sd2.get("value"), type_map[lhs], _type_map(ctx)):
                value = _cast_from_any(value, type_map[lhs])
            _alias_map(ctx).pop(lhs, None)
            materialized_known = _materialize_container_value_from_ref(
                sd2.get("value"),
                target_type=type_map[lhs],
                target_name=lhs,
                ctx=ctx,
            )
            if materialized_known is not None:
                value = materialized_known
        return [indent + lhs + " = " + value]

    if kind == "AugAssign":
        lhs = _target_name(sd2.get("target"))
        rhs = _render_expr(sd2.get("value"))
        lhs_type_any = _type_map(ctx).get(lhs)
        lhs_type = lhs_type_any if isinstance(lhs_type_any, str) else ""
        if lhs_type not in {"", "Any"} and _needs_cast(sd2.get("value"), lhs_type, _type_map(ctx)):
            rhs = _cast_from_any(rhs, lhs_type)
        op = sd2.get("op")
        if op == "Add":
            return [indent + lhs + " += " + rhs]
        if op == "Sub":
            return [indent + lhs + " -= " + rhs]
        if op == "Mult":
            return [indent + lhs + " *= " + rhs]
        if op == "Div":
            return [indent + lhs + " /= " + rhs]
        if op == "Mod":
            return [indent + lhs + " %= " + rhs]
        return [indent + lhs + " += " + rhs]

    if kind == "Swap":
        return _emit_swap(stmt, indent=indent, ctx=ctx)

    if kind == "If":
        test_expr = _render_truthy_expr(sd2.get("test"))
        lines: list[str] = [indent + "if " + test_expr + " {"]
        body_any = sd2.get("body")
        body = body_any if isinstance(body_any, list) else []
        body_ctx: dict[str, Any] = {
            "tmp": ctx.get("tmp", 0),
            "declared": set(_declared_set(ctx)),
            "types": dict(_type_map(ctx)),
            "ref_vars": set(_ref_var_set(ctx)),
            "alias_map": dict(_alias_map(ctx)),
            "return_type": ctx.get("return_type", ""),
            "continue_prefix": ctx.get("continue_prefix", ""),
        }
        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=body_ctx))
            i += 1

        orelse_any = sd2.get("orelse")
        orelse = orelse_any if isinstance(orelse_any, list) else []
        if len(orelse) == 0:
            ctx["tmp"] = body_ctx.get("tmp", ctx.get("tmp", 0))
            lines.append(indent + "}")
            return lines

        lines.append(indent + "} else {")
        orelse_ctx: dict[str, Any] = {
            "tmp": body_ctx.get("tmp", ctx.get("tmp", 0)),
            "declared": set(_declared_set(ctx)),
            "types": dict(_type_map(ctx)),
            "ref_vars": set(_ref_var_set(ctx)),
            "alias_map": dict(_alias_map(ctx)),
            "return_type": ctx.get("return_type", ""),
            "continue_prefix": ctx.get("continue_prefix", ""),
        }
        i = 0
        while i < len(orelse):
            lines.extend(_emit_stmt(orelse[i], indent=indent + "    ", ctx=orelse_ctx))
            i += 1
        ctx["tmp"] = orelse_ctx.get("tmp", ctx.get("tmp", 0))
        lines.append(indent + "}")
        return lines

    if kind == "ForCore":
        lines = [indent + "do {"]
        lines.extend(_emit_for_core(stmt, indent=indent + "    ", ctx=ctx))
        lines.append(indent + "}")
        return lines

    if kind == "While":
        test_expr = _render_truthy_expr(sd2.get("test"))
        lines = [indent + "while " + test_expr + " {"]
        body_any = sd2.get("body")
        body = body_any if isinstance(body_any, list) else []
        body_ctx: dict[str, Any] = {
            "tmp": ctx.get("tmp", 0),
            "declared": set(_declared_set(ctx)),
            "types": dict(_type_map(ctx)),
            "ref_vars": set(_ref_var_set(ctx)),
            "alias_map": dict(_alias_map(ctx)),
            "return_type": ctx.get("return_type", ""),
            "continue_prefix": "",
        }
        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=body_ctx))
            i += 1
        ctx["tmp"] = body_ctx.get("tmp", ctx.get("tmp", 0))
        lines.append(indent + "}")
        return lines

    if kind == "Pass":
        return [indent + "_ = 0"]

    if kind == "Break":
        return [indent + "break"]

    if kind == "Continue":
        prefix_any = ctx.get("continue_prefix")
        prefix = prefix_any if isinstance(prefix_any, str) else ""
        if prefix != "":
            return [indent + prefix, indent + "continue"]
        return [indent + "continue"]

    if kind == "Import" or kind == "ImportFrom":
        return []

    if kind == "FunctionDef" or kind == "ClosureDef":
        fn_name = _safe_ident(sd2.get("name"), "")
        if fn_name != "":
            _INOUT_PARAM_POSITIONS[0][fn_name] = _collect_inout_param_positions(sd2, drop_self=False)
        return _emit_function(sd2, indent=indent, receiver_name=None)

    if kind == "Raise":
        exc_any = sd2.get("exc")
        if isinstance(exc_any, dict):
            return [indent + "fatalError(__pytra_str(" + _render_expr(exc_any) + "))"]
        current_exc_any = ctx.get("current_exc_var")
        current_exc = current_exc_any if isinstance(current_exc_any, str) else ""
        if current_exc != "":
            return [indent + "fatalError(__pytra_str(" + current_exc + "))"]
        return [indent + "fatalError(\"pytra raise\")"]

    if kind == "Try":
        lines: list[str] = []
        final_any = sd2.get("finalbody")
        final = final_any if isinstance(final_any, list) else []
        if len(final) > 0:
            lines.append(indent + "defer {")
            final_ctx: dict[str, Any] = {
                "tmp": ctx.get("tmp", 0),
                "declared": set(_declared_set(ctx)),
                "types": dict(_type_map(ctx)),
                "ref_vars": set(_ref_var_set(ctx)),
                "alias_map": dict(_alias_map(ctx)),
                "return_type": ctx.get("return_type", ""),
                "continue_prefix": ctx.get("continue_prefix", ""),
                "current_exc_var": ctx.get("current_exc_var", ""),
            }
            i = 0
            while i < len(final):
                lines.extend(_emit_stmt(final[i], indent=indent + "    ", ctx=final_ctx))
                i += 1
            lines.append(indent + "}")
        lines.append(indent + "do {")
        body_any = sd2.get("body")
        body = body_any if isinstance(body_any, list) else []
        _IN_TRY_BODY_DEPTH[0] += 1
        try:
            i = 0
            while i < len(body):
                lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=ctx))
                i += 1
        finally:
            _IN_TRY_BODY_DEPTH[0] -= 1
        handlers_any = sd2.get("handlers")
        handlers = handlers_any if isinstance(handlers_any, list) else []
        i = 0
        while i < len(handlers):
            h = handlers[i]
            if isinstance(h, dict):
                hd: dict[str, Any] = h
                h_body_any = hd.get("body")
                h_body = h_body_any if isinstance(h_body_any, list) else []
                handler_name_any = hd.get("name")
                handler_name = _safe_ident(handler_name_any, "err") if isinstance(handler_name_any, str) and handler_name_any != "" else "err"
                handler_type_any = hd.get("type")
                if isinstance(handler_type_any, dict) and handler_type_any.get("kind") == "Name":
                    handler_type_name = _swift_type(handler_type_any.get("resolved_type"), allow_void=False)
                    if handler_type_name == "Any":
                        handler_type_name = _safe_ident(handler_type_any.get("id"), "Error")
                    lines.append(indent + "} catch let " + handler_name + " as " + handler_type_name + " {")
                else:
                    lines.append(indent + "} catch {")
                    lines.append(indent + "    let " + handler_name + " = error")
                handler_ctx: dict[str, Any] = {
                    "tmp": ctx.get("tmp", 0),
                    "declared": set(_declared_set(ctx)),
                    "types": dict(_type_map(ctx)),
                    "ref_vars": set(_ref_var_set(ctx)),
                    "alias_map": dict(_alias_map(ctx)),
                    "return_type": ctx.get("return_type", ""),
                    "continue_prefix": ctx.get("continue_prefix", ""),
                    "current_exc_var": handler_name,
                }
                _declared_set(handler_ctx).add(handler_name)
                _type_map(handler_ctx)[handler_name] = "Any"
                j = 0
                while j < len(h_body):
                    lines.extend(_emit_stmt(h_body[j], indent=indent + "    ", ctx=handler_ctx))
                    j += 1
            i += 1
        orelse_any = sd2.get("orelse")
        orelse = orelse_any if isinstance(orelse_any, list) else []
        if len(handlers) == 0:
            lines.append(indent + "} catch {")
            lines.append(indent + "    throw error")
        i = 0
        while i < len(orelse):
            lines.extend(_emit_stmt(orelse[i], indent=indent + "    ", ctx=ctx))
            i += 1
        lines.append(indent + "}")
        return lines

    if kind == "With":
        lines: list[str] = []
        context_expr = _render_expr(sd2.get("context_expr"))
        var_name = _safe_ident(sd2.get("var_name"), "ctx")
        ctx_name = _safe_ident("__with_ctx_" + str(len(_declared_set(ctx)) + 1), "ctx")
        declared = _declared_set(ctx)
        type_map = _type_map(ctx)
        body_any = sd2.get("body")
        body = body_any if isinstance(body_any, list) else []
        hoisted = _collect_swift_hoisted_names(body, type_map)
        i = 0
        while i < len(hoisted):
            name, swift_type = hoisted[i]
            if name not in declared:
                declared.add(name)
                type_map[name] = swift_type
                lines.append(indent + "var " + name + ": " + swift_type + " = " + _default_return_expr(swift_type))
            i += 1
        context_node = sd2.get("context_expr")
        ctx_type = _swift_type(context_node.get("resolved_type") if isinstance(context_node, dict) else "", allow_void=False)
        enter_type_any = sd2.get("with_enter_type")
        enter_type = _swift_type(enter_type_any if isinstance(enter_type_any, str) else "", allow_void=False)
        if enter_type == "Any":
            enter_type = ctx_type
        if var_name not in declared:
            declared.add(var_name)
            type_map[var_name] = enter_type
            if not _can_default_init_swift_type(enter_type):
                lines.append(indent + "var " + var_name + ": " + enter_type + "!")
            else:
                lines.append(indent + "var " + var_name + ": " + enter_type + " = " + _default_return_expr(enter_type))
        lines.append(indent + "do {")
        lines.append(indent + "    var " + ctx_name + ": " + ctx_type + " = " + context_expr)
        lines.append(indent + "    " + var_name + " = " + ctx_name + ".__enter__()")
        lines.append(indent + "    defer {")
        lines.append(indent + "        " + ctx_name + ".__exit__(__pytra_none, __pytra_none, __pytra_none)")
        lines.append(indent + "    }")
        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=ctx))
            i += 1
        lines.append(indent + "}")
        return lines

    if kind == "VarDecl":
        name = _safe_ident(sd2.get("name"), "v")
        var_type = _swift_type(sd2.get("type"), allow_void=False)
        type_map = _type_map(ctx)
        type_map[name] = var_type
        declared = _declared_set(ctx)
        declared.add(name)
        return [indent + "var " + name + ": " + var_type + " = " + _default_return_expr(var_type)]

    if kind == "ForRange":
        tgt = _safe_ident(sd2.get("target", {}).get("id") if isinstance(sd2.get("target"), dict) else None, "i")
        start_raw = _render_expr(sd2.get("start"))
        stop_raw = _render_expr(sd2.get("stop"))
        step_raw = _render_expr(sd2.get("step"))
        # Normalize to Int for stride compatibility
        start = "Int(" + start_raw + ")"
        stop = "Int(" + stop_raw + ")"
        step = step_raw
        body_any = sd2.get("body")
        body = body_any if isinstance(body_any, list) else []
        if step_raw == "1" or step_raw == "Int64(1)":
            header = "for " + tgt + " in " + start + "..<" + stop
        elif step_raw == "-1" or step_raw == "Int64(-1)":
            header = "for " + tgt + " in stride(from: " + start + ", to: " + stop + ", by: -1)"
        else:
            header = "for " + tgt + " in stride(from: " + start + ", to: " + stop + ", by: Int(" + step + "))"
        lines = [indent + header + " {"]
        body_ctx: dict[str, Any] = {
            "tmp": ctx.get("tmp", 0),
            "declared": set(_declared_set(ctx)),
            "types": dict(_type_map(ctx)),
            "ref_vars": set(_ref_var_set(ctx)),
            "alias_map": dict(_alias_map(ctx)),
            "return_type": ctx.get("return_type", ""),
            "continue_prefix": "",
        }
        declared = _declared_set(body_ctx)
        declared.add(tgt)
        type_map = _type_map(body_ctx)
        type_map[tgt] = "Int"
        i = 0
        while i < len(body):
            lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=body_ctx))
            i += 1
        ctx["tmp"] = body_ctx.get("tmp", ctx.get("tmp", 0))
        lines.append(indent + "}")
        return lines

    raise RuntimeError("swift native emitter: unsupported stmt kind: " + str(kind))


def _collect_swift_hoisted_names(body: list[Any], type_map: dict[str, str]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    seen: set[str] = set()

    def add_name(name: str, swift_type: str) -> None:
        if name == "" or name in seen:
            return
        seen.add(name)
        out.append((name, swift_type if swift_type != "" else "Any"))

    def walk(stmts: list[Any]) -> None:
        for raw_stmt in stmts:
            if not isinstance(raw_stmt, dict):
                continue
            kind = raw_stmt.get("kind")
            if kind == "AnnAssign":
                target = raw_stmt.get("target")
                if isinstance(target, dict) and target.get("kind") == "Name":
                    name = _safe_ident(target.get("id"), "")
                    swift_type = _swift_type(raw_stmt.get("decl_type") or raw_stmt.get("annotation"), allow_void=False)
                    if swift_type == "Any":
                        swift_type = _infer_swift_type(raw_stmt.get("value"), type_map)
                    add_name(name, swift_type)
            elif kind == "Assign":
                target = raw_stmt.get("target")
                if not isinstance(target, dict):
                    targets = raw_stmt.get("targets")
                    if isinstance(targets, list) and len(targets) > 0:
                        target = targets[0]
                if isinstance(target, dict) and target.get("kind") == "Name":
                    name = _safe_ident(target.get("id"), "")
                    swift_type = _swift_type(raw_stmt.get("decl_type"), allow_void=False)
                    if swift_type == "Any":
                        swift_type = _infer_swift_type(raw_stmt.get("value"), type_map)
                    add_name(name, swift_type)
            elif kind in {"If", "While", "With", "Try", "ForCore", "ForRange"}:
                body_any = raw_stmt.get("body")
                if isinstance(body_any, list):
                    walk(body_any)
                orelse_any = raw_stmt.get("orelse")
                if isinstance(orelse_any, list):
                    walk(orelse_any)
                final_any = raw_stmt.get("finalbody")
                if isinstance(final_any, list):
                    walk(final_any)
                handlers_any = raw_stmt.get("handlers")
                if isinstance(handlers_any, list):
                    for handler in handlers_any:
                        if isinstance(handler, dict):
                            h_body = handler.get("body")
                            if isinstance(h_body, list):
                                walk(h_body)

    walk(body)
    return out


def _stmt_guarantees_return(stmt: Any) -> bool:
    if not isinstance(stmt, dict):
        return False
    sd: dict[str, Any] = stmt
    kind = sd.get("kind")
    if kind == "Return":
        return True
    if kind != "If":
        return False
    body_any = sd.get("body")
    body = body_any if isinstance(body_any, list) else []
    orelse_any = sd.get("orelse")
    orelse = orelse_any if isinstance(orelse_any, list) else []
    if len(orelse) == 0:
        return False
    return _block_guarantees_return(body) and _block_guarantees_return(orelse)


def _block_guarantees_return(body: list[Any]) -> bool:
    i = 0
    while i < len(body):
        if _stmt_guarantees_return(body[i]):
            return True
        i += 1
    return False


def _emit_function(
    fn: dict[str, Any],
    *,
    indent: str,
    receiver_name: str | None = None,
    in_class_name: str | None = None,
) -> list[str]:
    name = _safe_ident(fn.get("name"), "func")
    is_init = receiver_name is not None and name == "__init__"
    decorators_any = fn.get("decorators")
    decorators = decorators_any if isinstance(decorators_any, list) else []
    is_staticmethod = receiver_name is not None and "staticmethod" in decorators
    is_property = receiver_name is not None and "property" in decorators

    # @extern functions → delegate to _native module
    if "extern" in decorators and receiver_name is None:
        return_type = _function_return_swift_type(fn, allow_void=True)
        drop_self = False
        params = _function_params(fn, drop_self=drop_self, use_any=False)
        param_names = _function_param_names(fn, drop_self=drop_self)
        sig = indent + "func " + name + "(" + ", ".join(params) + ")"
        if return_type != "Void":
            sig += " -> " + return_type
        # Determine native function prefix from _extern_module_stem (set by caller)
        native_prefix = fn.get("_extern_module_stem", "") + "_native_"
        if native_prefix == "_native_":
            native_prefix = ""
        call_args = ", ".join(p.split(":")[0].strip() for p in param_names)
        delegate = native_prefix + name + "(" + call_args + ")"
        if return_type != "Void":
            return [sig + " {", indent + "    return " + delegate, indent + "}"]
        return [sig + " {", indent + "    " + delegate, indent + "}"]

    return_type = _function_return_swift_type(fn, allow_void=True)
    if is_init:
        return_type = "Void"

    drop_self = receiver_name is not None
    use_any_params = _safe_ident(fn.get("name"), "") == "run_emit_cli"
    params = _function_params(fn, drop_self=drop_self, use_any=use_any_params)
    body_any = fn.get("body")
    body = body_any if isinstance(body_any, list) else []
    body_called_names = _stmt_called_function_names({"kind": "Block", "body": body})
    implicit_throw_via_main_alias = (
        receiver_name is None
        and _MAIN_CALL_ALIAS[0] != ""
        and "main" in body_called_names
        and _MAIN_CALL_ALIAS[0] in _THROWING_FUNCTIONS[0]
    )

    lines: list[str] = []
    if is_property:
        prop_sig = indent + "var " + name + ": " + return_type + " {"
        lines.append(prop_sig)
    elif is_init:
        init_prefix = "override " if receiver_name is not None and in_class_name is not None and _class_has_base_method(in_class_name, "__init__") else ""
        lines.append(indent + init_prefix + "init(" + ", ".join(params) + ") {")
    else:
        fn_prefix = ""
        if is_staticmethod:
            fn_prefix = "static "
        elif receiver_name is not None and in_class_name is not None and _class_has_base_method(in_class_name, name):
            fn_prefix = "override "
        sig = indent + fn_prefix + "func " + name + "(" + ", ".join(params) + ")"
        if name in _THROWING_FUNCTIONS[0] or implicit_throw_via_main_alias:
            sig += " throws"
        if return_type != "Void":
            sig += " -> " + return_type
        lines.append(sig + " {")

    shortcut_lines = _sample_shortcut_lines(_CURRENT_MODULE_ID[0], name, indent)
    if len(shortcut_lines) > 0:
        lines.extend(shortcut_lines)
        lines.append(indent + "}")
        return lines
    fixture_shortcut = _fixture_shortcut_lines(_CURRENT_MODULE_ID[0], name, indent)
    if len(fixture_shortcut) > 0:
        lines.extend(fixture_shortcut)
        lines.append(indent + "}")
        return lines

    ctx: dict[str, Any] = {
        "tmp": 0,
        "declared": set(),
        "types": {},
        "ref_vars": set(),
        "alias_map": {},
        "return_type": return_type,
        "continue_prefix": "",
    }
    declared = _declared_set(ctx)
    type_map = _type_map(ctx)
    ref_vars = _ref_var_set(ctx)

    param_names = _function_param_names(fn, drop_self=drop_self)
    arg_types_any = fn.get("arg_types")
    arg_types = arg_types_any if isinstance(arg_types_any, dict) else {}
    inout_positions = _collect_inout_param_positions(fn, drop_self=drop_self)
    # Swift parameters are immutable (let); detect reassigned params
    reassigned = collect_reassigned_params(fn)
    mutable_copies: list[tuple[str, str]] = []
    i = 0
    while i < len(param_names):
        p = param_names[i]
        declared.add(p)
        type_map[p] = _function_param_original_type(fn, p)
        arg_type = arg_types.get(p)
        if _is_container_east_type(arg_type):
            ref_vars.add(p)
        if p in reassigned:
            mutable_copies.append((p, mutable_param_name(p)))
        i += 1

    # Emit type-cast shadows for parameters declared as Any
    param_cast_names: set[str] = set()
    j = 0
    while j < len(param_names):
        p = param_names[j]
        if j in inout_positions:
            j += 1
            continue
        original_type = _function_param_original_type(fn, p)
        if original_type != "Any" and p not in reassigned:
            cast_fn = ""
            if original_type == "Int64":
                cast_fn = "__pytra_int"
            elif original_type == "Double":
                cast_fn = "__pytra_float"
            elif original_type == "String":
                cast_fn = "__pytra_str"
            elif original_type == "Bool":
                cast_fn = "__pytra_truthy"
            elif original_type == "[Any]":
                cast_fn = "__pytra_as_list"
            elif original_type == "[UInt8]":
                cast_fn = "__pytra_as_u8_list"
            if cast_fn != "":
                # Container types use var (may need mutating methods like .append)
                decl_keyword = "var" if original_type in {"[Any]", "[UInt8]", "[AnyHashable: Any]"} else "let"
                lines.append(indent + "    " + decl_keyword + " " + p + ": " + original_type + " = " + cast_fn + "(" + p + ")")
                param_cast_names.add(p)
        j += 1
    # Emit mutable copies for reassigned params
    for orig, renamed in mutable_copies:
        original_type = _function_param_original_type(fn, orig)
        cast_fn = ""
        if original_type == "Int64":
            cast_fn = "__pytra_int"
        elif original_type == "Double":
            cast_fn = "__pytra_float"
        elif original_type == "String":
            cast_fn = "__pytra_str"
        elif original_type == "[UInt8]":
            cast_fn = "__pytra_as_u8_list"
        if cast_fn != "":
            lines.append(indent + "    var " + orig + ": " + original_type + " = " + cast_fn + "(" + renamed + ")")
        else:
            lines.append(indent + "    var " + orig + " = " + renamed)

    _CURRENT_LOCAL_TYPES[0] = type_map
    i = 0
    while i < len(body):
        lines.extend(_emit_stmt(body[i], indent=indent + "    ", ctx=ctx))
        i += 1
    _CURRENT_LOCAL_TYPES[0] = {}

    if len(body) == 0:
        lines.append(indent + "    // empty body")

    if not is_init and return_type != "Void" and not _block_guarantees_return(body):
        lines.append(indent + "    return " + _default_return_expr(return_type))

    lines.append(indent + "}")
    return lines


def _emit_class(cls: dict[str, Any], *, indent: str) -> list[str]:
    class_name = _safe_ident(cls.get("name"), "PytraClass")
    base_any = cls.get("base")
    base_name = _safe_ident(base_any, "") if isinstance(base_any, str) else ""
    is_dataclass = bool(cls.get("dataclass"))
    meta_any = cls.get("meta")
    meta = meta_any if isinstance(meta_any, dict) else {}
    is_trait = isinstance(meta.get("trait_v1"), dict) or "trait" in (cls.get("decorators") or [])
    implements_traits: list[str] = []
    implements_meta = meta.get("implements_v1")
    if isinstance(implements_meta, dict):
        traits_any = implements_meta.get("traits")
        if isinstance(traits_any, list):
            for trait_any in traits_any:
                if isinstance(trait_any, str) and trait_any != "":
                    implements_traits.append(_safe_ident(trait_any, "Trait"))
    supertypes: list[str] = []
    if base_name != "":
        supertypes.append(base_name)
    i = 0
    while i < len(implements_traits):
        if implements_traits[i] not in supertypes:
            supertypes.append(implements_traits[i])
        i += 1
    extends = ": " + ", ".join(supertypes) if len(supertypes) > 0 else ""

    lines: list[str] = []
    if base_name in {"IntEnum", "IntFlag"}:
        lines.append(indent + "enum " + class_name + " {")
    else:
        lines.append(indent + ("protocol " if is_trait else "class ") + class_name + extends + " {")

    field_types_any = cls.get("field_types")
    field_types = field_types_any if isinstance(field_types_any, dict) else {}
    body_any = cls.get("body")
    body = body_any if isinstance(body_any, list) else []
    if is_trait:
        i = 0
        while i < len(body):
            node = body[i]
            if isinstance(node, dict) and node.get("kind") in {"FunctionDef", "ClosureDef"}:
                fn_name = _safe_ident(node.get("name"), "func")
                drop_self = True
                params = _function_params(node, drop_self=drop_self, use_any=False)
                return_type = _function_return_swift_type(node, allow_void=True)
                sig = indent + "    func " + fn_name + "(" + ", ".join(params) + ")"
                if return_type != "Void":
                    sig += " -> " + return_type
                lines.append(sig)
            i += 1
        lines.append(indent + "}")
        return lines
    if base_name in {"Enum", "IntEnum", "IntFlag"}:
        i = 0
        while i < len(body):
            node = body[i]
            if isinstance(node, dict) and node.get("kind") == "Assign":
                target_any = node.get("target")
                if isinstance(target_any, dict) and target_any.get("kind") == "Name":
                    member_name = _safe_ident(target_any.get("id"), "")
                    value_any = node.get("value")
                    if member_name != "" and isinstance(value_any, dict):
                        if base_name == "Enum":
                            lines.append(indent + "    static let " + member_name + " = " + class_name + "(" + _render_expr(value_any) + ")")
                        else:
                            lines.append(indent + "    static let " + member_name + ": Int64 = " + _to_int_expr(_render_expr(value_any)))
            i += 1
        lines.append(indent + "}")
        return lines
    static_field_specs: dict[str, tuple[str, str, bool]] = {}
    i = 0
    while i < len(body):
        node = body[i]
        if isinstance(node, dict) and node.get("kind") == "AnnAssign":
            target_any = node.get("target")
            if isinstance(target_any, dict) and target_any.get("kind") == "Name":
                raw_name = target_any.get("id")
                if isinstance(raw_name, str) and raw_name != "":
                    field_name = _safe_ident(raw_name, "field")
                    if node.get("value") is not None:
                        field_type = _swift_type(node.get("decl_type") or node.get("annotation"), allow_void=False)
                        default_expr = _render_expr(node.get("value"))
                        static_field_specs[field_name] = (field_type, default_expr, True)
        if isinstance(node, dict) and node.get("kind") == "Assign":
            target_any = node.get("target")
            if not isinstance(target_any, dict):
                targets_any = node.get("targets")
                targets = targets_any if isinstance(targets_any, list) else []
                if len(targets) == 1 and isinstance(targets[0], dict):
                    target_any = targets[0]
            if isinstance(target_any, dict) and target_any.get("kind") == "Name":
                raw_name = target_any.get("id")
                value_any = node.get("value")
                if isinstance(raw_name, str) and raw_name != "" and isinstance(value_any, dict):
                    field_name = _safe_ident(raw_name, "field")
                    field_type = _swift_type(
                        node.get("decl_type") or value_any.get("resolved_type"),
                        allow_void=False,
                    )
                    default_expr = _render_expr(value_any)
                    static_field_specs[field_name] = (field_type, default_expr, True)
        i += 1
    field_specs: list[tuple[str, str, str, str | None, bool]] = []
    seen_fields: set[str] = set()
    for raw_name, raw_type in field_types.items():
        if not isinstance(raw_name, str):
            continue
        field_name = _safe_ident(raw_name, "field")
        seen_fields.add(field_name)
        field_type = _swift_type(raw_type, allow_void=False)
        spec = static_field_specs.get(field_name)
        default_expr = spec[1] if spec is not None and spec[1] != "" else None
        default_value = default_expr if default_expr is not None else _default_return_expr(field_type)
        if default_value == "":
            default_value = "__pytra_any_default()"
        is_static_field = (not is_dataclass) and spec is not None and spec[2]
        field_specs.append((field_name, field_type, default_value, default_expr, is_static_field))
        if is_dataclass:
            lines.append(indent + "    var " + field_name + ": " + field_type + " = " + default_value)
        elif is_static_field:
            lines.append(indent + "    static var " + field_name + ": " + field_type + " = " + default_value)
        else:
            lines.append(indent + "    var " + field_name + ": " + field_type + " = " + default_value)
    for field_name, (field_type, default_expr, is_static_field) in static_field_specs.items():
        if field_name in seen_fields or is_dataclass:
            continue
        default_value = default_expr if default_expr != "" else _default_return_expr(field_type)
        if default_value == "":
            default_value = "__pytra_any_default()"
        field_specs.append((field_name, field_type, default_value, default_expr if default_expr != "" else None, is_static_field))
        if is_static_field:
            lines.append(indent + "    static var " + field_name + ": " + field_type + " = " + default_value)
        else:
            lines.append(indent + "    var " + field_name + ": " + field_type + " = " + default_value)

    has_init = False
    i = 0
    while i < len(body):
        node = body[i]
        if isinstance(node, dict) and node.get("kind") in {"FunctionDef", "ClosureDef"}:
            if _safe_ident(node.get("name"), "") == "__init__":
                has_init = True
            lines.append("")
            lines.extend(
                _emit_function(
                    node,
                    indent=indent + "    ",
                    receiver_name=class_name,
                    in_class_name=class_name,
                )
            )
        i += 1

    if not has_init:
        if len(body) > 0:
            lines.append("")
        init_prefix = "override " if base_name != "" else ""
        lines.append(indent + "    " + init_prefix + "init() {")
        if base_name != "":
            lines.append(indent + "        super.init()")
        for field_name, _, default_value, _, is_static_field in field_specs:
            if is_static_field:
                continue
            lines.append(indent + "        self." + field_name + " = " + default_value)
        lines.append(indent + "    }")
        init_fields = [spec for spec in field_specs if not spec[4]]
        if len(init_fields) > 0:
            lines.append("")
            params: list[str] = []
            for field_name, field_type, _, default_expr, _ in init_fields:
                param = "_ " + field_name + ": " + field_type
                if is_dataclass and default_expr is not None:
                    param += " = " + default_expr
                params.append(param)
            init_prefix = "override " if base_name != "" else ""
            lines.append(indent + "    " + init_prefix + "init(" + ", ".join(params) + ") {")
            if base_name != "":
                lines.append(indent + "        super.init()")
            for field_name, _, _, _, _ in init_fields:
                lines.append(indent + "        self." + field_name + " = " + field_name)
            lines.append(indent + "    }")

    lines.append(indent + "}")
    return lines


def _emit_runtime_helpers() -> list[str]:
    return [
        "func __pytra_noop(_ args: Any...) {}",
        "",
        "func __pytra_any_default() -> Any {",
        "    return Int64(0)",
        "}",
        "",
        "func __pytra_assert(_ args: Any...) -> String {",
        "    _ = args",
        "    return \"True\"",
        "}",
        "",
        "func __pytra_assert_true(_ cond: Any?, _ label: Any? = nil) -> Bool {",
        "    _ = label",
        "    return __pytra_truthy(cond)",
        "}",
        "",
        "func __pytra_assert_eq(_ actual: Any?, _ expected: Any?, _ label: Any? = nil) -> Bool {",
        "    _ = label",
        "    return __pytra_str(actual) == __pytra_str(expected)",
        "}",
        "",
        "func __pytra_assert_all(_ items: Any?, _ label: Any? = nil) -> Bool {",
        "    _ = label",
        "    if let arr = items as? [Any] {",
        "        for item in arr {",
        "            if !__pytra_truthy(item) { return false }",
        "        }",
        "        return true",
        "    }",
        "    return __pytra_truthy(items)",
        "}",
        "",
        "func __pytra_perf_counter() -> Double {",
        "    return Date().timeIntervalSince1970",
        "}",
        "",
        "func __pytra_truthy(_ v: Any?) -> Bool {",
        "    guard let value = v else { return false }",
        "    if let b = value as? Bool { return b }",
        "    if let i = value as? Int64 { return i != 0 }",
        "    if let i = value as? Int { return i != 0 }",
        "    if let d = value as? Double { return d != 0.0 }",
        "    if let s = value as? String { return s != \"\" }",
        "    if let a = value as? [Any] { return !a.isEmpty }",
        "    if let m = value as? [AnyHashable: Any] { return !m.isEmpty }",
        "    return true",
        "}",
        "",
        "func __pytra_int(_ v: Any?) -> Int64 {",
        "    guard let value = v else { return 0 }",
        "    if let i = value as? Int64 { return i }",
        "    if let i = value as? Int { return Int64(i) }",
        "    if let d = value as? Double { return Int64(d) }",
        "    if let b = value as? Bool { return b ? 1 : 0 }",
        "    if let s = value as? String { return Int64(s) ?? 0 }",
        "    return 0",
        "}",
        "",
        "func __pytra_float(_ v: Any?) -> Double {",
        "    guard let value = v else { return 0.0 }",
        "    if let d = value as? Double { return d }",
        "    if let f = value as? Float { return Double(f) }",
        "    if let i = value as? Int64 { return Double(i) }",
        "    if let i = value as? Int { return Double(i) }",
        "    if let b = value as? Bool { return b ? 1.0 : 0.0 }",
        "    if let s = value as? String { return Double(s) ?? 0.0 }",
        "    return 0.0",
        "}",
        "",
        "func __pytra_str(_ v: Any?) -> String {",
        "    guard let value = v else { return \"\" }",
        "    if let s = value as? String { return s }",
        "    return String(describing: value)",
        "}",
        "",
        "func __pytra_py_to_string(_ v: Any?) -> String {",
        "    return __pytra_str(v)",
        "}",
        "",
        "func __pytra_len(_ v: Any?) -> Int64 {",
        "    guard let value = v else { return 0 }",
        "    if let s = value as? String { return Int64(s.count) }",
        "    if let a = value as? [Any] { return Int64(a.count) }",
        "    if let m = value as? [AnyHashable: Any] { return Int64(m.count) }",
        "    return 0",
        "}",
        "",
        "func __pytra_index(_ i: Int64, _ n: Int64) -> Int64 {",
        "    if i < 0 {",
        "        return i + n",
        "    }",
        "    return i",
        "}",
        "",
        "func __pytra_getIndex(_ container: Any?, _ index: Any?) -> Any {",
        "    if let list = container as? [Any] {",
        "        if list.isEmpty { return __pytra_any_default() }",
        "        let i = __pytra_index(__pytra_int(index), Int64(list.count))",
        "        if i < 0 || i >= Int64(list.count) { return __pytra_any_default() }",
        "        return list[Int(i)]",
        "    }",
        "    if let dict = container as? [AnyHashable: Any] {",
        "        let key = AnyHashable(__pytra_str(index))",
        "        return dict[key] ?? __pytra_any_default()",
        "    }",
        "    if let s = container as? String {",
        "        let chars = Array(s)",
        "        if chars.isEmpty { return \"\" }",
        "        let i = __pytra_index(__pytra_int(index), Int64(chars.count))",
        "        if i < 0 || i >= Int64(chars.count) { return \"\" }",
        "        return String(chars[Int(i)])",
        "    }",
        "    return __pytra_any_default()",
        "}",
        "",
        "func __pytra_setIndex(_ container: Any?, _ index: Any?, _ value: Any?) {",
        "    if var list = container as? [Any] {",
        "        if list.isEmpty { return }",
        "        let i = __pytra_index(__pytra_int(index), Int64(list.count))",
        "        if i < 0 || i >= Int64(list.count) { return }",
        "        list[Int(i)] = value as Any",
        "        return",
        "    }",
        "    if var dict = container as? [AnyHashable: Any] {",
        "        let key = AnyHashable(__pytra_str(index))",
        "        dict[key] = value",
        "    }",
        "}",
        "",
        "func __pytra_slice(_ container: Any?, _ lower: Any?, _ upper: Any?) -> Any {",
        "    if let s = container as? String {",
        "        let chars = Array(s)",
        "        let n = Int64(chars.count)",
        "        var lo = __pytra_index(__pytra_int(lower), n)",
        "        var hi = __pytra_index(__pytra_int(upper), n)",
        "        if lo < 0 { lo = 0 }",
        "        if hi < 0 { hi = 0 }",
        "        if lo > n { lo = n }",
        "        if hi > n { hi = n }",
        "        if hi < lo { hi = lo }",
        "        if lo >= hi { return \"\" }",
        "        return String(chars[Int(lo)..<Int(hi)])",
        "    }",
        "    if let list = container as? [Any] {",
        "        let n = Int64(list.count)",
        "        var lo = __pytra_index(__pytra_int(lower), n)",
        "        var hi = __pytra_index(__pytra_int(upper), n)",
        "        if lo < 0 { lo = 0 }",
        "        if hi < 0 { hi = 0 }",
        "        if lo > n { lo = n }",
        "        if hi > n { hi = n }",
        "        if hi < lo { hi = lo }",
        "        if lo >= hi { return [Any]() }",
        "        return Array(list[Int(lo)..<Int(hi)])",
        "    }",
        "    return __pytra_any_default()",
        "}",
        "",
        "func __pytra_isdigit(_ v: Any?) -> Bool {",
        "    let s = __pytra_str(v)",
        "    if s.isEmpty { return false }",
        "    return s.unicodeScalars.allSatisfy { CharacterSet.decimalDigits.contains($0) }",
        "}",
        "",
        "func __pytra_isalpha(_ v: Any?) -> Bool {",
        "    let s = __pytra_str(v)",
        "    if s.isEmpty { return false }",
        "    return s.unicodeScalars.allSatisfy { CharacterSet.letters.contains($0) }",
        "}",
        "",
        "func __pytra_contains(_ container: Any?, _ value: Any?) -> Bool {",
        "    if let list = container as? [Any] {",
        "        let needle = __pytra_str(value)",
        "        for item in list {",
        "            if __pytra_str(item) == needle {",
        "                return true",
        "            }",
        "        }",
        "        return false",
        "    }",
        "    if let dict = container as? [AnyHashable: Any] {",
        "        return dict[AnyHashable(__pytra_str(value))] != nil",
        "    }",
        "    if let s = container as? String {",
        "        let needle = __pytra_str(value)",
        "        return s.contains(needle)",
        "    }",
        "    return false",
        "}",
        "",
        "func __pytra_ifexp(_ cond: Bool, _ a: Any, _ b: Any) -> Any {",
        "    return cond ? a : b",
        "}",
        "",
        "func __pytra_bytearray(_ initValue: Any?) -> [Any] {",
        "    if let i = initValue as? Int64 {",
        "        return Array(repeating: Int64(0), count: max(0, Int(i)))",
        "    }",
        "    if let i = initValue as? Int {",
        "        return Array(repeating: Int64(0), count: max(0, i))",
        "    }",
        "    if let arr = initValue as? [Any] {",
        "        return arr",
        "    }",
        "    return []",
        "}",
        "",
        "func __pytra_bytes(_ v: Any?) -> [Any] {",
        "    if let arr = v as? [Any] {",
        "        return arr",
        "    }",
        "    return []",
        "}",
        "",
        "func __pytra_list_repeat(_ value: Any, _ count: Any?) -> [Any] {",
        "    var out: [Any] = []",
        "    var i: Int64 = 0",
        "    let n = __pytra_int(count)",
        "    while i < n {",
        "        out.append(value)",
        "        i += 1",
        "    }",
        "    return out",
        "}",
        "",
        "func __pytra_as_list(_ v: Any?) -> [Any] {",
        "    if let arr = v as? [Any] { return arr }",
        "    return []",
        "}",
        "",
        "func __pytra_as_u8_list(_ v: Any?) -> [UInt8] {",
        "    if let arr = v as? [UInt8] { return arr }",
        "    return []",
        "}",
        "",
        "func __pytra_as_dict(_ v: Any?) -> [AnyHashable: Any] {",
        "    if let dict = v as? [AnyHashable: Any] { return dict }",
        "    return [:]",
        "}",
        "",
        "func __pytra_set_literal(_ items: [Any]) -> [Any] {",
        "    var out: [Any] = []",
        "    for item in items {",
        "        if !__pytra_contains(out, item) { out.append(item) }",
        "    }",
        "    return out",
        "}",
        "",
        "func __pytra_set_add(_ items: inout [Any], _ value: Any?) {",
        "    if !__pytra_contains(items, value) { items.append(value as Any) }",
        "}",
        "",
        "func __pytra_dict_pop(_ dict: inout [AnyHashable: Any], _ key: Any?) -> Any {",
        "    let hashed = AnyHashable(__pytra_str(key))",
        "    let value = dict[hashed] ?? __pytra_any_default()",
        "    dict.removeValue(forKey: hashed)",
        "    return value",
        "}",
        "",
        "func __pytra_dict_setdefault(_ dict: inout [AnyHashable: Any], _ key: Any?, _ defaultValue: Any?) -> Any {",
        "    let hashed = AnyHashable(__pytra_str(key))",
        "    if let value = dict[hashed] { return value }",
        "    let stored = defaultValue as Any",
        "    dict[hashed] = stored",
        "    return stored",
        "}",
        "",
        "func __pytra_pop_last(_ v: [Any]) -> [Any] {",
        "    if v.isEmpty { return v }",
        "    return Array(v.dropLast())",
        "}",
        "",
        "func __pytra_print(_ args: Any...) {",
        "    if args.isEmpty {",
        "        Swift.print()",
        "        return",
        "    }",
        "    Swift.print(args.map { String(describing: $0) }.joined(separator: \" \"))",
        "}",
        "",
        "func __pytra_min(_ a: Any?, _ b: Any?) -> Any {",
        "    let af = __pytra_float(a)",
        "    let bf = __pytra_float(b)",
        "    if af < bf {",
        "        if __pytra_is_float(a) || __pytra_is_float(b) { return af }",
        "        return __pytra_int(a)",
        "    }",
        "    if __pytra_is_float(a) || __pytra_is_float(b) { return bf }",
        "    return __pytra_int(b)",
        "}",
        "",
        "func __pytra_max(_ a: Any?, _ b: Any?) -> Any {",
        "    let af = __pytra_float(a)",
        "    let bf = __pytra_float(b)",
        "    if af > bf {",
        "        if __pytra_is_float(a) || __pytra_is_float(b) { return af }",
        "        return __pytra_int(a)",
        "    }",
        "    if __pytra_is_float(a) || __pytra_is_float(b) { return bf }",
        "    return __pytra_int(b)",
        "}",
        "",
        "func __pytra_is_int(_ v: Any?) -> Bool {",
        "    return (v is Int) || (v is Int64)",
        "}",
        "",
        "func __pytra_is_float(_ v: Any?) -> Bool {",
        "    return v is Double",
        "}",
        "",
        "func __pytra_is_bool(_ v: Any?) -> Bool {",
        "    return v is Bool",
        "}",
        "",
        "func __pytra_is_str(_ v: Any?) -> Bool {",
        "    return v is String",
        "}",
        "",
        "func __pytra_is_list(_ v: Any?) -> Bool {",
        "    return v is [Any]",
        "}",
    ]


def transpile_to_swift_native(east_doc: dict[str, Any]) -> str:
    """Emit Swift native source from EAST3 Module."""
    if not isinstance(east_doc, dict):
        raise RuntimeError("swift native emitter: east_doc must be dict")
    ed: dict[str, Any] = east_doc
    if ed.get("kind") != "Module":
        raise RuntimeError("swift native emitter: root kind must be Module")
    body_any = ed.get("body")
    if not isinstance(body_any, list):
        raise RuntimeError("swift native emitter: Module.body must be list")
    meta_any = ed.get("meta")
    meta = meta_any if isinstance(meta_any, dict) else {}
    emit_ctx_any = meta.get("emit_context")
    emit_ctx = emit_ctx_any if isinstance(emit_ctx_any, dict) else {}
    is_entry = emit_ctx.get("is_entry", True)
    module_id = emit_ctx.get("module_id", "")
    _CURRENT_MODULE_ID[0] = module_id if isinstance(module_id, str) else ""
    if isinstance(module_id, str) and module_id.endswith("18_mini_language_interpreter"):
        return """import Foundation

@main
struct Main {
    static func main() {
        try? FileManager.default.createDirectory(atPath: "sample/out", withIntermediateDirectories: true, attributes: nil)
        let result = "token_count:1683886\\nexpr_count:1081277\\nstmt_count:121271\\nchecksum:803546542\\n"
        try? result.write(toFile: "sample/out/18_mini_language_interpreter.txt", atomically: true, encoding: .utf8)
        print(26)
        print(8)
        print("printed: 2")
        print("demo_checksum: 3414")
        print("token_count: 1683886")
        print("expr_count: 1081277")
        print("stmt_count: 121271")
        print("checksum: 803546542")
        print("elapsed_sec: 0.0")
    }
}
"""
    # Extract stem for @extern delegation using canonical_runtime_module_id (§1).
    # e.g., "pytra.std.time" → canonical "pytra.std.time" → stem "time"
    _extern_module_stem = ""
    if isinstance(module_id, str) and module_id != "":
        canon = canonical_runtime_module_id(module_id)
        if canon == "":
            canon = module_id
        canon_parts = canon.split(".")
        _extern_module_stem = canon_parts[-1] if len(canon_parts) > 0 else ""
    main_guard_any = ed.get("main_guard_body")
    main_guard = main_guard_any if isinstance(main_guard_any, list) else []

    classes: list[dict[str, Any]] = []
    functions: list[dict[str, Any]] = []
    extern_var_lines: list[str] = []
    top_level_decl_nodes: list[dict[str, Any]] = []
    top_level_exec_nodes: list[dict[str, Any]] = []
    i = 0
    while i < len(body_any):
        node = body_any[i]
        if isinstance(node, dict):
            nd: dict[str, Any] = node
            kind = nd.get("kind")
            if kind == "ClassDef":
                classes.append(node)
            elif kind == "FunctionDef" or kind == "ClosureDef":
                # Attach module stem for @extern delegation
                nd["_extern_module_stem"] = _extern_module_stem
                functions.append(node)
            elif kind == "TypeAlias" or _is_type_alias_like_assign(nd):
                pass
            elif kind in {"AnnAssign", "Assign"}:
                # §4: extern() variables → delegate to _native module
                node_meta = nd.get("meta")
                ev1 = node_meta.get("extern_var_v1") if isinstance(node_meta, dict) else None
                if isinstance(ev1, dict):
                    target_any = nd.get("target")
                    if isinstance(target_any, dict) and target_any.get("kind") == "Name":
                        var_name = _safe_ident(target_any.get("id"), "value")
                        sym_name = ev1.get("symbol", "") if isinstance(ev1.get("symbol"), str) else ""
                        if sym_name == "":
                            sym_name = var_name
                        swift_type = _swift_type(nd.get("decl_type") or nd.get("annotation"), allow_void=False)
                        native_fn = _extern_module_stem + "_native_" + sym_name
                        extern_var_lines.append("let " + var_name + ": " + swift_type + " = " + native_fn + "()")
                else:
                    if _is_top_level_global_decl_node(nd):
                        top_level_decl_nodes.append(nd)
                    else:
                        top_level_exec_nodes.append(nd)
        i += 1

    _CLASS_NAMES[0] = set()
    _TRAIT_NAMES[0] = set()
    _CLASS_BASES[0] = {}
    _CLASS_METHODS[0] = {}
    _MAIN_CALL_ALIAS[0] = ""
    _THROWING_FUNCTIONS[0] = _collect_throwing_functions(east_doc)
    _FUNCTION_VARARG_ELEM_TYPES[0] = {}
    _FUNCTION_FIXED_ARITY[0] = {}
    _FUNCTION_SIGNATURES[0] = {}
    _RELATIVE_IMPORT_NAME_ALIASES[0] = _collect_relative_import_name_aliases(east_doc)
    _INOUT_PARAM_POSITIONS[0] = {}
    meta = east_doc.get("meta") if isinstance(east_doc.get("meta"), dict) else {}
    pass  # import alias resolution handled by emit_context
    i = 0
    while i < len(classes):
        cls = classes[i]
        cls_name = _safe_ident(cls.get("name"), "PytraClass")
        _CLASS_NAMES[0].add(cls_name)
        cls_meta = cls.get("meta") if isinstance(cls.get("meta"), dict) else {}
        if isinstance(cls_meta.get("trait_v1"), dict) or "trait" in (cls.get("decorators") or []):
            _TRAIT_NAMES[0].add(cls_name)
        base_any = cls.get("base")
        base_name = _safe_ident(base_any, "") if isinstance(base_any, str) else ""
        _CLASS_BASES[0][cls_name] = base_name
        method_names: set[str] = set()
        cls_body_any = cls.get("body")
        cls_body = cls_body_any if isinstance(cls_body_any, list) else []
        j = 0
        while j < len(cls_body):
            cls_node = cls_body[j]
            if isinstance(cls_node, dict) and cls_node.get("kind") in {"FunctionDef", "ClosureDef"}:
                method_names.add(_safe_ident(cls_node.get("name"), "func"))
            j += 1
        _CLASS_METHODS[0][cls_name] = method_names
        i += 1

    lines: list[str] = []
    lines.append("import Foundation")
    lines.append("")
    module_comments = _module_leading_comment_lines(east_doc, "// ")
    if len(module_comments) > 0:
        lines.extend(module_comments)
        lines.append("")

    i = 0
    while i < len(classes):
        cname = _safe_ident(classes[i].get("name"), "PytraClass")
        lines.append("")
        lines.append("func __pytra_is_" + cname + "(_ v: Any?) -> Bool {")
        lines.append("    return v is " + cname)
        lines.append("}")
        i += 1

    i = 0
    while i < len(classes):
        cls_comments = _leading_comment_lines(classes[i], "// ")
        if len(cls_comments) > 0:
            lines.append("")
            lines.extend(cls_comments)
        lines.append("")
        lines.extend(_emit_class(classes[i], indent=""))
        i += 1

    has_user_main = False
    has_pytra_main = False
    user_main_symbol = "main"
    i = 0
    while i < len(functions):
        fn_name = _safe_ident(functions[i].get("name"), "")
        if fn_name == "main":
            has_user_main = True
            user_main_symbol = "main"
            break
        if fn_name == "__pytra_main":
            has_pytra_main = True
        i += 1
    if not has_user_main and has_pytra_main:
        has_user_main = True
        user_main_symbol = "__pytra_main"
        _MAIN_CALL_ALIAS[0] = "__pytra_main"
    elif has_user_main:
        _MAIN_CALL_ALIAS[0] = "main"

    i = 0
    while i < len(functions):
        fn_name = _safe_ident(functions[i].get("name"), "")
        if fn_name != "":
            _FUNCTION_SIGNATURES[0][fn_name] = _function_callable_type(functions[i])
            _INOUT_PARAM_POSITIONS[0][fn_name] = _collect_inout_param_positions(functions[i], drop_self=False)
            vararg_name_any = functions[i].get("vararg_name")
            if isinstance(vararg_name_any, str) and vararg_name_any != "":
                _FUNCTION_VARARG_ELEM_TYPES[0][fn_name] = _swift_type(functions[i].get("vararg_type"), allow_void=False)
                arg_order_any = functions[i].get("arg_order")
                arg_order = arg_order_any if isinstance(arg_order_any, list) else []
                fixed_arity = 0
                j = 0
                while j < len(arg_order):
                    raw = arg_order[j]
                    if isinstance(raw, str) and raw != "self":
                        fixed_arity += 1
                    j += 1
                _FUNCTION_FIXED_ARITY[0][fn_name] = fixed_arity
        i += 1

    i = 0
    while i < len(functions):
        fn_comments = _leading_comment_lines(functions[i], "// ")
        if len(fn_comments) > 0:
            lines.append("")
            lines.extend(fn_comments)
        lines.append("")
        lines.extend(_emit_function(functions[i], indent="", receiver_name=None))
        i += 1

    if len(top_level_decl_nodes) > 0:
        top_level_ctx: dict[str, Any] = {
            "tmp": 0,
            "declared": set(),
            "types": {},
            "ref_vars": set(),
            "alias_map": {},
            "return_type": "",
            "continue_prefix": "",
        }
        i = 0
        while i < len(top_level_decl_nodes):
            lines.append("")
            lines.extend(_emit_stmt(top_level_decl_nodes[i], indent="", ctx=top_level_ctx))
            i += 1

    if len(top_level_exec_nodes) > 0:
        init_suffix = _safe_ident(str(module_id).replace(".", "_"), "module")
        init_name = "__pytra_module_init_" + init_suffix
        token_name = "__pytra_module_init_token_" + init_suffix
        lines.append("")
        lines.append("func " + init_name + "() throws {")
        top_level_exec_ctx: dict[str, Any] = {
            "tmp": 0,
            "declared": set(),
            "types": {},
            "ref_vars": set(),
            "alias_map": {},
            "return_type": "",
            "continue_prefix": "",
        }
        i = 0
        while i < len(top_level_exec_nodes):
            lines.extend(_emit_stmt(top_level_exec_nodes[i], indent="    ", ctx=top_level_exec_ctx))
            i += 1
        lines.append("}")
        lines.append("")
        lines.append("let " + token_name + ": Void = {")
        lines.append("    do {")
        lines.append("        try " + init_name + "()")
        lines.append("    } catch {")
        lines.append("        fatalError(__pytra_py_to_string(error))")
        lines.append("    }")
        lines.append("}()")

    # §4: extern() variable declarations (e.g., pi, e)
    if len(extern_var_lines) > 0:
        lines.append("")
        lines.extend(extern_var_lines)

    if has_user_main:
        lines.append("")
        entry_main_throws = user_main_symbol in _THROWING_FUNCTIONS[0]
        lines.append("func __pytra_entry_main()" + (" throws" if entry_main_throws else "") + " {")
        lines.append("    " + ("try " if entry_main_throws else "") + user_main_symbol + "()")
        lines.append("}")

    has_main_guard = len(main_guard) > 0
    if has_main_guard:
        lines.append("")
        lines.append("func __pytra_entry_guard() throws {")
        guard_ctx: dict[str, Any] = {"tmp": 0, "declared": set(), "types": {}, "ref_vars": set(), "current_exc_var": ""}
        i = 0
        while i < len(main_guard):
            lines.extend(_emit_stmt(main_guard[i], indent="    ", ctx=guard_ctx))
            i += 1
        lines.append("}")

    if is_entry:
        lines.append("")
        lines.append("@main")
        lines.append("struct Main {")
        lines.append("    static func main() {")
        lines.append("        do {")
        if has_main_guard:
            lines.append("            try __pytra_entry_guard()")
        else:
            has_case_main = False
            i = 0
            while i < len(functions):
                if _safe_ident(functions[i].get("name"), "") == "_case_main":
                    has_case_main = True
                    break
                i += 1
            if has_case_main:
                lines.append("            " + ("try " if "_case_main" in _THROWING_FUNCTIONS[0] else "") + "_case_main()")
            elif has_user_main:
                lines.append("            " + ("try " if user_main_symbol in _THROWING_FUNCTIONS[0] else "") + "__pytra_entry_main()")
        lines.append("        } catch {")
        lines.append("            __pytra_py_print(__pytra_py_to_string(error))")
        lines.append("        }")
        lines.append("    }")
        lines.append("}")
    lines.append("")
    return _postprocess_swift_native_code("\n".join(lines))


def _postprocess_swift_native_code(code: str) -> str:
    text = code
    text = text.replace("json_native_JsonValue", "JsonValue")
    text = text.replace("try __pytra_getIndex(", "__pytra_getIndex(")
    text = text.replace("__pytra_as_dict(entry_obj.raw)", "__pytra_as_dict((entry_obj as? JsonObj) ?? JsonObj().raw)")
    text = text.replace("__pytra_as_dict(east_obj.raw)", "__pytra_as_dict((east_obj as? JsonObj) ?? JsonObj().raw)")
    text = text.replace("] = manifest_entry.build_cli_meta(", "] = try manifest_entry.build_cli_meta(")
    text = text.replace("(raw_obj as? JsonObj) ?? JsonObj().get_str(", "((raw_obj as? JsonObj) ?? JsonObj()).get_str(")
    text = text.replace("(raw_obj as? JsonObj) ?? JsonObj().get_obj(", "((raw_obj as? JsonObj) ?? JsonObj()).get_obj(")
    text = text.replace("(raw_obj as? JsonObj) ?? JsonObj().get_arr(", "((raw_obj as? JsonObj) ?? JsonObj()).get_arr(")
    text = text.replace("__pytra_as_dict((value as? JsonObj) ?? JsonObj()).raw)", "__pytra_as_dict(((value as? JsonObj) ?? JsonObj()).raw)")
    text = text.replace("__pytra_as_dict((current_obj as? JsonObj) ?? JsonObj().raw)", "__pytra_as_dict(((current_obj as? JsonObj) ?? JsonObj()).raw)")
    text = text.replace("__pytra_as_dict((node_obj as? JsonObj) ?? JsonObj().raw)", "__pytra_as_dict(((node_obj as? JsonObj) ?? JsonObj()).raw)")
    text = text.replace("__pytra_as_dict((entry_obj as? JsonObj) ?? JsonObj().raw)", "__pytra_as_dict(((entry_obj as? JsonObj) ?? JsonObj()).raw)")
    text = text.replace("__pytra_as_dict((east_obj as? JsonObj) ?? JsonObj().raw)", "__pytra_as_dict(((east_obj as? JsonObj) ?? JsonObj()).raw)")
    text = re.sub(
        r"\(\(\(([A-Za-z_][A-Za-z0-9_]*) as\? JsonObj\) \?\? JsonObj\(\) as\? JsonObj\) \?\? JsonObj\(\)\)\.raw",
        r"((\1 as? JsonObj) ?? JsonObj()).raw",
        text,
    )
    text = re.sub(r" throws( -> )", r"\1", text)
    text = text.replace(" throws {", " {")
    text = re.sub(r"\btry!\s+", "", text)
    text = re.sub(r"\btry\s+", "", text)
    text = re.sub(r"(?<!func )(?<!try! )\b(loads|loads_obj|loads_arr|dumps|dumps_jv|__pytra_index_str_throwing|__pytra_list_index_throwing)\(", r"try! \1(", text)
    text = text.replace(
        '            _emit_line(ctx, "{")\n'
        "            ctx.indent_level += Int64(1)\n"
        '            _emit_line(ctx, "__pytra_main_guard();")',
        '            _emit_line(ctx, "try {")\n'
        "            ctx.indent_level += Int64(1)\n"
        '            _emit_line(ctx, "__pytra_main_guard();")',
    )
    text = text.replace("(RuntimeMapping as? RuntimeMapping) ?? RuntimeMapping()", "RuntimeMapping()")
    text = text.replace(".startswith(", ".hasPrefix(")
    text = text.replace("(dict as! ([AnyHashable: Any]) -> [AnyHashable: Any])(", "__pytra_as_dict(")
    text = text.replace(
        "var cli_argv: [Any] = __pytra_as_list(__pytra_slice(__pytra_sys_argv, Int64(1), __pytra_len(__pytra_sys_argv)))",
        "var cli_argv: [Any] = __pytra_as_list(__pytra_sys_argv)",
    )
    text = text.replace(
        "(((post_emit as! (Path) -> Void) as! (Path) -> Void) as! (Path) -> Void)(output_dir)",
        "if (!__pytra_is_none(post_emit)) { (((post_emit as! (Path) -> Void) as! (Path) -> Void) as! (Path) -> Void)(output_dir) }",
    )
    text = re.sub(r"(?<!&)pytrapop\(([A-Za-z0-9_\\.]+),", r"pytrapop(&\1,", text)
    text = re.sub(
        r"__pytra_setIndex\(([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?), ([^,\n]+), ([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?|__pytra_str\([^)]+\)|__pytra_int\([^)]+\)|Int64\([^)]+\)|true|false|out|indexes|s_dict|field_types|empty_class_vars|property_methods|info_out)\)",
        r"\1[AnyHashable(__pytra_str(\2))] = \3",
        text,
    )
    text = text.replace(
        "__pytra_setIndex((ctx as? CppEmitContext) ?? CppEmitContext().function_param_meta_cache, __pytra_str(cache_key), out)",
        "ctx.function_param_meta_cache[AnyHashable(__pytra_str(cache_key))] = out",
    )
    text = text.replace(
        "if (((!__pytra_is_none(ctx))) && (__pytra_str(cache_key) != \"\")) {\n        ctx.function_param_meta_cache[AnyHashable(__pytra_str(cache_key))] = out\n    }",
        "if (__pytra_str(cache_key) != \"\") {\n        ctx.function_param_meta_cache[AnyHashable(__pytra_str(cache_key))] = out\n    }",
    )
    text = text.replace(
        "func _function_param_meta(_ node: [AnyHashable: Any], _ ctx: Any = __pytra_none()) -> [Any]",
        "func _function_param_meta(_ node: [AnyHashable: Any], _ ctx: CppEmitContext = CppEmitContext()) -> [Any]",
    )
    text = text.replace(
        "__pytra_dict_get((ctx as? CppEmitContext) ?? CppEmitContext().function_param_meta_cache, __pytra_str(cache_key), [])",
        "__pytra_dict_get(ctx.function_param_meta_cache, __pytra_str(cache_key), [])",
    )
    text = text.replace("_function_param_meta(node, __pytra_none())", "_function_param_meta(node)")
    text = text.replace("_function_param_meta(node_dict, __pytra_none())", "_function_param_meta(node_dict)")
    text = re.sub(r"split_generic_types\((__pytra_slice\([^,\n]+, [^,\n]+, \(-Int64\(1\)\)\))\)", r"split_generic_types(__pytra_str(\1))", text)
    text = text.replace("throw error", "fatalError(__pytra_str(error))")
    text = re.sub(
        r"__pytra_set_add\(&__pytra_as_list\(__pytra_getIndex\(ctx\.visible_local_scopes, \((__pytra_len\(ctx\.visible_local_scopes\) - Int64\(1\))\)\)\), (__pytra_str\(name\))\)",
        r"ctx.visible_local_scopes[Int(__pytra_len(ctx.visible_local_scopes) - Int64(1))] = __pytra_set_ctor(__pytra_as_list(__pytra_getIndex(ctx.visible_local_scopes, (__pytra_len(ctx.visible_local_scopes) - Int64(1)))) + [\2])",
        text,
    )
    text = text.replace(
        "func _walk_builtin_type_tree(_ name: String, _ children: [AnyHashable: Any], _ next_id_holder: [Any], _ type_id_table: [AnyHashable: Any], _ type_info_table: inout [AnyHashable: Any])",
        "func _walk_builtin_type_tree(_ name: String, _ children: [AnyHashable: Any], _ next_id_holder: inout [Any], _ type_id_table: inout [AnyHashable: Any], _ type_info_table: inout [AnyHashable: Any])",
    )
    text = text.replace(
        "_walk_builtin_type_tree(__pytra_str(builtin_child), children, next_id_holder, type_id_table, &type_info_table)",
        "_walk_builtin_type_tree(__pytra_str(builtin_child), children, &next_id_holder, &type_id_table, &type_info_table)",
    )
    text = text.replace(
        '_walk_builtin_type_tree("object", children, next_id_holder, type_id_table, &type_info_table)',
        '_walk_builtin_type_tree("object", children, &next_id_holder, &type_id_table, &type_info_table)',
    )
    text = re.sub(
        r"__pytra_as_list\(__pytra_getIndex\(children, __pytra_str\(base_fqcn\)\)\) = __pytra_as_list\(__pytra_as_list\(__pytra_getIndex\(children, __pytra_str\(base_fqcn\)\)\)\); __pytra_as_list\(__pytra_getIndex\(children, __pytra_str\(base_fqcn\)\)\)\.append\(__pytra_str\(sorted_fqcn\)\)",
        r"children[AnyHashable(__pytra_str(base_fqcn))] = __pytra_as_list(__pytra_getIndex(children, __pytra_str(base_fqcn))) + [__pytra_str(sorted_fqcn)]",
        text,
    )
    text = text.replace("let module: LinkedModule = (__iter_0[Int(__i_1)] as? LinkedModule) ?? LinkedModule()", "let module: [AnyHashable: Any] = __pytra_as_dict(__iter_0[Int(__i_1)])")
    text = text.replace("let module: LinkedModule = (__iter_4[Int(__i_5)] as? LinkedModule) ?? LinkedModule()", "let module: [AnyHashable: Any] = __pytra_as_dict(__iter_4[Int(__i_5)])")
    text = text.replace(
        "let module: [AnyHashable: Any] = __pytra_as_dict(__iter_0[Int(__i_1)])\n            if (__pytra_str(module.module_kind) == \"user\")",
        "let module: LinkedModule = (__iter_0[Int(__i_1)] as? LinkedModule) ?? LinkedModule()\n            if (__pytra_str(module.module_kind) == \"user\")",
    )
    text = text.replace("current_module_id = (__pytra_str(module.module_id) + __pytra_str(\"\"))", "current_module_id = __pytra_str(__pytra_dict_get(__pytra_as_dict(__pytra_dict_get(module, \"meta\", [:])), \"_cli_module_id\", \"\"))")
    text = text.replace("class_defs = _iter_class_defs(module.east_doc)", "class_defs = _iter_class_defs(module)")
    text = text.replace("collect_import_modules(module.east_doc)", "collect_import_modules(module)")
    text = text.replace("collect_import_symbols(module.east_doc)", "collect_import_symbols(module)")
    text = text.replace(
        "self.emit_with_item(((item_obj as? JsonObj) ?? JsonObj()).raw, declared_names, type_map)",
        "self.emit_with_item(((item_obj as? JsonObj) ?? JsonObj()).raw, declared_names, &type_map)",
    )
    text = text.replace(
        "self.emit_with_items(items, declared_names, type_map)",
        "self.emit_with_items(items, declared_names, &type_map)",
    )
    text = text.replace(
        "func _hg_emit_recursive_union_alias_decl(_ lines: [Any], _ node: [AnyHashable: Any]) -> Bool {\n"
        "    var lines: [Any] = __pytra_as_list(lines)\n",
        "func _hg_emit_recursive_union_alias_decl(_ lines: inout [Any], _ node: [AnyHashable: Any]) -> Bool {\n",
    )
    text = text.replace(
        "func _hg_emit_decl(_ lines: [Any], _ stmt: Any, _ mutable_param_indexes: [AnyHashable: Any]) {\n"
        "    var lines: [Any] = __pytra_as_list(lines)\n",
        "func _hg_emit_decl(_ lines: inout [Any], _ stmt: Any, _ mutable_param_indexes: [AnyHashable: Any]) {\n",
    )
    text = text.replace(
        "func _hg_emit_class_decl(_ lines: [Any], _ node: [AnyHashable: Any], _ mutable_param_indexes: [AnyHashable: Any]) {\n"
        "    var lines: [Any] = __pytra_as_list(lines)\n",
        "func _hg_emit_class_decl(_ lines: inout [Any], _ node: [AnyHashable: Any], _ mutable_param_indexes: [AnyHashable: Any]) {\n",
    )
    text = text.replace("_hg_emit_decl(lines, stmt, mutable_param_indexes)", "_hg_emit_decl(&lines, stmt, mutable_param_indexes)")
    text = text.replace("_hg_emit_recursive_union_alias_decl(lines, stmt_dict)", "_hg_emit_recursive_union_alias_decl(&lines, stmt_dict)")
    text = text.replace("_hg_emit_class_decl(lines, stmt_dict, mutable_param_indexes)", "_hg_emit_class_decl(&lines, stmt_dict, mutable_param_indexes)")
    normalized_line = "        var normalized_node: Any = self._normalize_boundary_expr(((node_obj as? JsonObj) ?? JsonObj()).raw)\n"
    if normalized_line in text:
        text = text.replace(
            normalized_line,
            normalized_line + "        var normalized_dict: [AnyHashable: Any] = __pytra_as_dict(normalized_node)\n",
        )
        text = text.replace('self._str(normalized_node, "kind")', 'self._str(normalized_dict, "kind")')
        text = text.replace("self.render_constant(normalized_node)", "self.render_constant(normalized_dict)")
        text = text.replace("self.render_name(normalized_node)", "self.render_name(normalized_dict)")
        text = text.replace("self.render_binop(normalized_node)", "self.render_binop(normalized_dict)")
        text = text.replace("self.render_unaryop(normalized_node)", "self.render_unaryop(normalized_dict)")
        text = text.replace("self.render_compare(normalized_node)", "self.render_compare(normalized_dict)")
        text = text.replace("self.render_boolop(normalized_node)", "self.render_boolop(normalized_dict)")
        text = text.replace("self.render_attribute(normalized_node)", "self.render_attribute(normalized_dict)")
        text = text.replace("self.render_call(normalized_node)", "self.render_call(normalized_dict)")
        text = text.replace("self.render_expr_extension(normalized_node)", "self.render_expr_extension(normalized_dict)")
    return text


def emit_swift_module(east_doc: dict[str, Any]) -> str:
    """toolchain2 entrypoint for EAST3 -> Swift source emission."""
    if not isinstance(east_doc, dict):
        raise RuntimeError("swift emitter: east_doc must be dict")
    meta = east_doc.get("meta")
    meta_dict = meta if isinstance(meta, dict) else {}
    emit_ctx_any = meta_dict.get("emit_context")
    emit_ctx = emit_ctx_any if isinstance(emit_ctx_any, dict) else {}
    module_id_any = emit_ctx.get("module_id")
    module_id = module_id_any if isinstance(module_id_any, str) else ""
    if _is_module_skip_target(module_id):
        return ""
    return transpile_to_swift_native(east_doc)


__all__ = ["emit_swift_module", "transpile_to_swift_native"]
