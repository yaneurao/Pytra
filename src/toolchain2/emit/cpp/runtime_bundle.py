"""Helpers for emitting C++ runtime headers/sources from linked EAST3 docs."""

from __future__ import annotations

from pytra.std.json import JsonVal
from pytra.std.pathlib import Path

from toolchain2.emit.cpp.emitter import emit_cpp_module
from toolchain2.emit.cpp.header_gen import build_cpp_header_from_east3
from toolchain2.emit.cpp.runtime_paths import (
    runtime_rel_tail_for_module,
    native_companion_header_path,
    native_companion_source_path,
)
from toolchain2.emit.cpp.types import collect_cpp_type_vars


_RUNTIME_CPP_ROOT = Path(__file__).resolve().parents[3] / "runtime" / "cpp"


def _is_extern_decorator_name(name: str) -> bool:
    n = name.strip()
    return n == "extern" or n.endswith(".extern")


def _is_extern_function_decl(stmt: dict[str, JsonVal]) -> bool:
    if stmt.get("kind") != "FunctionDef":
        return False
    decorators = stmt.get("decorators")
    if not isinstance(decorators, list):
        return False
    for decorator in decorators:
        if isinstance(decorator, str) and _is_extern_decorator_name(decorator):
            return True
    meta = stmt.get("meta")
    if isinstance(meta, dict) and isinstance(meta.get("extern_v1"), dict):
        return True
    return False


def _is_extern_call_expr(expr: JsonVal) -> bool:
    if not isinstance(expr, dict):
        return False
    if expr.get("kind") != "Call":
        return False
    func = expr.get("func")
    if not isinstance(func, dict):
        return False
    if func.get("kind") == "Name":
        func_id = func.get("id")
        return isinstance(func_id, str) and _is_extern_decorator_name(func_id)
    if func.get("kind") == "Attribute":
        attr = func.get("attr")
        return isinstance(attr, str) and attr == "extern"
    return False


def _is_extern_variable_decl(stmt: dict[str, JsonVal]) -> bool:
    kind = stmt.get("kind")
    if kind not in ("Assign", "AnnAssign"):
        return False
    return _is_extern_call_expr(stmt.get("value"))


def _strip_extern_decls_from_stmt(stmt: JsonVal) -> JsonVal:
    if not isinstance(stmt, dict):
        return stmt
    if _is_extern_function_decl(stmt) or _is_extern_variable_decl(stmt):
        return None
    kind = stmt.get("kind")
    copied = dict(stmt)
    if kind == "ClassDef":
        body = copied.get("body")
        items = body if isinstance(body, list) else []
        new_body: list[JsonVal] = []
        for child in items:
            kept = _strip_extern_decls_from_stmt(child)
            if kept is not None:
                new_body.append(kept)
        copied["body"] = new_body
    return copied


def _build_emit_doc_without_extern_decls(east_doc: dict[str, JsonVal]) -> dict[str, JsonVal]:
    copied = dict(east_doc)
    body = copied.get("body")
    items = body if isinstance(body, list) else []
    new_body: list[JsonVal] = []
    for stmt in items:
        kept = _strip_extern_decls_from_stmt(stmt)
        if kept is not None:
            new_body.append(kept)
    copied["body"] = new_body
    return copied


def _has_cpp_emit_definitions(east_doc: dict[str, JsonVal]) -> bool:
    body = east_doc.get("body")
    items = body if isinstance(body, list) else []
    for stmt in items:
        if not isinstance(stmt, dict):
            continue
        kind = stmt.get("kind")
        if kind in ("Import", "ImportFrom", "Pass"):
            continue
        if kind == "Expr":
            value = stmt.get("value")
            if isinstance(value, dict) and value.get("kind") == "Constant" and isinstance(value.get("value"), str):
                continue
        return True
    return False


def _is_template_function_stmt(stmt: dict[str, JsonVal]) -> bool:
    if stmt.get("kind") not in ("FunctionDef", "ClosureDef"):
        return False
    arg_types = stmt.get("arg_types")
    if isinstance(arg_types, dict):
        for arg_type in arg_types.values():
            if isinstance(arg_type, str) and len(collect_cpp_type_vars(arg_type)) > 0:
                return True
    return len(collect_cpp_type_vars(_return_type(stmt))) > 0


def _runtime_module_is_header_only_template_lane(east_doc: dict[str, JsonVal]) -> bool:
    body = east_doc.get("body")
    items = body if isinstance(body, list) else []
    saw_template_fn = False
    for stmt in items:
        if not isinstance(stmt, dict):
            continue
        kind = stmt.get("kind")
        if kind in ("Import", "ImportFrom", "Pass", "TypeAlias"):
            continue
        if kind == "Expr":
            value = stmt.get("value")
            if isinstance(value, dict) and value.get("kind") == "Constant" and isinstance(value.get("value"), str):
                continue
        if not _is_template_function_stmt(stmt):
            return False
        saw_template_fn = True
    return saw_template_fn


def _return_type(node: dict[str, JsonVal]) -> str:
    return_type = node.get("return_type")
    if isinstance(return_type, str) and return_type != "":
        return return_type
    returns = node.get("returns")
    if isinstance(returns, str) and returns != "":
        return returns
    return "None"


def _cpp_impl_body(cpp_text: str) -> str:
    marker = "// Generated by toolchain2/emit/cpp"
    idx = cpp_text.find(marker)
    if idx < 0:
        return cpp_text.strip()
    body = cpp_text[idx + len(marker):].strip()
    return body


def _append_header_only_impls(header_text: str, cpp_text: str) -> str:
    impl_body = _cpp_impl_body(cpp_text)
    if impl_body == "":
        return header_text
    lines = header_text.splitlines()
    insert_at = len(lines)
    for i, line in enumerate(lines):
        if line.startswith("#endif"):
            insert_at = i
            break
    impl_lines = ["", impl_body, ""]
    new_lines = lines[:insert_at] + impl_lines + lines[insert_at:]
    return "\n".join(new_lines) + "\n"


def _inject_runtime_native_companion_include(header_text: str, module_id: str) -> str:
    native_hdr = native_companion_header_path(module_id)
    if not native_hdr.exists():
        return header_text
    rel = str(native_hdr.relative_to(_RUNTIME_CPP_ROOT)).replace("\\", "/")
    include_line = '#include "' + rel + '"'
    if include_line in header_text:
        return header_text
    lines = header_text.splitlines()
    insert_at = len(lines)
    for i, line in enumerate(lines):
        if line.startswith("#endif"):
            insert_at = i
            break
    lines.insert(insert_at, include_line)
    if insert_at > 0 and lines[insert_at - 1] != "":
        lines.insert(insert_at, "")
        insert_at += 1
    if insert_at + 1 < len(lines) and lines[insert_at + 1] != "":
        lines.insert(insert_at + 1, "")
    return "\n".join(lines) + "\n"


def emit_runtime_module_artifacts(
    module_id: str,
    east_doc: dict[str, JsonVal],
    *,
    output_dir: Path,
    source_path: str = "",
) -> tuple[str, str]:
    """Emit runtime module header/source into output_dir.

    Returns `(header_path, source_path)` as strings; `source_path` may be empty
    for header-only modules.
    """
    rel = runtime_rel_tail_for_module(module_id)
    if rel == "":
        return "", ""

    header_path = output_dir / (rel + ".h")
    header_path.parent.mkdir(parents=True, exist_ok=True)

    emit_doc = _build_emit_doc_without_extern_decls(east_doc)
    if "meta" not in emit_doc or not isinstance(emit_doc["meta"], dict):
        emit_doc["meta"] = {}
    meta = emit_doc["meta"]
    assert isinstance(meta, dict)
    linked = meta.get("linked_program_v1")
    if not isinstance(linked, dict):
        linked = {"module_id": module_id}
        meta["linked_program_v1"] = linked
    elif not isinstance(linked.get("module_id"), str) or linked.get("module_id") == "":
        linked["module_id"] = module_id

    cpp_text = ""
    source_out = ""
    has_native_companion = native_companion_header_path(module_id).exists() or native_companion_source_path(module_id).exists()
    header_only_templates = _runtime_module_is_header_only_template_lane(emit_doc)
    if (not has_native_companion) and _has_cpp_emit_definitions(emit_doc):
        cpp_text = emit_cpp_module(
            emit_doc,
            allow_runtime_module=True,
            self_header=rel + ".h",
        )
        if cpp_text.strip() != "" and not header_only_templates:
            source_path_out = output_dir / (rel + ".cpp")
            source_path_out.parent.mkdir(parents=True, exist_ok=True)
            source_path_out.write_text(cpp_text, encoding="utf-8")
            source_out = str(source_path_out)

    native_include = ""
    native_header = native_companion_header_path(module_id)
    if native_header.exists():
        # Use path relative to src/ so the generated #include resolves via -I src_dir
        # rather than self-shadowing via -I emit_dir (which takes search precedence).
        _src_root = _RUNTIME_CPP_ROOT.parents[1]  # .../src
        native_include = str(native_header.relative_to(_src_root)).replace("\\", "/")
    header_text = build_cpp_header_from_east3(
        module_id,
        east_doc,
        rel_header_path=rel + ".h",
        native_header_include=native_include,
        prefer_native_header=native_include != "",
    )
    if header_only_templates and cpp_text.strip() != "":
        header_text = _append_header_only_impls(header_text, cpp_text)
    header_path.write_text(header_text, encoding="utf-8")
    return str(header_path), source_out
