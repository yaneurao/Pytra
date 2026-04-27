"""Helpers for emitting C++ runtime headers/sources from linked EAST3 docs."""

from __future__ import annotations

from dataclasses import dataclass

import pytra.std.json as json
from pytra.std.json import JsonVal
from pytra.std.pathlib import Path

from toolchain.emit.cpp.emitter import emit_cpp_module
from toolchain.emit.cpp.header_gen import build_cpp_header_from_east3
from toolchain.emit.cpp.runtime_paths import (
    cpp_user_header_for_module,
    runtime_rel_tail_for_module,
    native_companion_header_path,
    native_companion_source_path,
)
from toolchain.emit.cpp.types import collect_cpp_type_vars


_rb_RUNTIME_CPP_ROOT = Path("src").joinpath("runtime").joinpath("cpp")


@dataclass
class RuntimeModuleArtifactDraft:
    header_path: str = ""
    source_path: str = ""

    def as_tuple(self) -> tuple[str, str]:
        return self.header_path, self.source_path

    def emitted_count(self) -> int:
        count = 0
        if self.header_path != "":
            count += 1
        if self.source_path != "":
            count += 1
        return count


def _rb_is_extern_decorator_name(name: str) -> bool:
    n = name.strip()
    return n == "extern" or n.endswith(".extern")


def _rb_is_extern_function_decl(stmt: dict[str, JsonVal]) -> bool:
    if _rb_str(stmt, "kind") != "FunctionDef":
        return False
    decorators = stmt.get("decorators")
    decorators_arr = json.JsonValue(decorators).as_arr()
    if decorators_arr is not None:
        for decorator in decorators_arr.raw:
            decorator_text = _rb_json_str_value(decorator)
            if decorator_text != "" and _rb_is_extern_decorator_name(decorator_text):
                return True
    meta = stmt.get("meta")
    meta_obj = json.JsonValue(meta).as_obj()
    if meta_obj is not None and json.JsonValue(meta_obj.raw.get("extern_v1")).as_obj() is not None:
            return True
    return False


def _rb_is_extern_call_expr(expr: JsonVal) -> bool:
    expr_obj = json.JsonValue(expr).as_obj()
    if expr_obj is None:
        return False
    expr_dict = expr_obj.raw
    if _rb_str(expr_dict, "kind") != "Call":
        return False
    func_obj = json.JsonValue(expr_dict.get("func")).as_obj()
    if func_obj is None:
        return False
    func = func_obj.raw
    if _rb_str(func, "kind") == "Name":
        func_id = _rb_str(func, "id")
        return func_id != "" and _rb_is_extern_decorator_name(func_id)
    if _rb_str(func, "kind") == "Attribute":
        return _rb_str(func, "attr") == "extern"
    return False


def _rb_is_extern_variable_decl(stmt: dict[str, JsonVal]) -> bool:
    kind = _rb_str(stmt, "kind")
    if kind not in ("Assign", "AnnAssign"):
        return False
    return _rb_is_extern_call_expr(stmt.get("value"))


def _rb_strip_extern_decls_from_stmt(stmt: JsonVal) -> JsonVal:
    stmt_obj = json.JsonValue(stmt).as_obj()
    if stmt_obj is None:
        return stmt
    stmt_dict = stmt_obj.raw
    if _rb_is_extern_function_decl(stmt_dict) or _rb_is_extern_variable_decl(stmt_dict):
        return None
    kind = _rb_str(stmt_dict, "kind")
    copied: dict[str, JsonVal] = {}
    for key, value in stmt_dict.items():
        copied[key] = value
    if kind == "ClassDef":
        body = copied.get("body")
        body_arr = json.JsonValue(body).as_arr()
        items: list[JsonVal] = []
        if body_arr is not None:
            items = body_arr.raw
        new_body: list[JsonVal] = []
        for child in items:
            kept = _rb_strip_extern_decls_from_stmt(child)
            if kept is not None:
                new_body.append(kept)
        copied["body"] = new_body
    return copied


def _rb_build_emit_doc_without_extern_decls(east_doc: dict[str, JsonVal]) -> dict[str, JsonVal]:
    copied: dict[str, JsonVal] = {}
    for key, value in east_doc.items():
        copied[key] = value
    body = copied.get("body")
    body_arr = json.JsonValue(body).as_arr()
    items: list[JsonVal] = []
    if body_arr is not None:
        items = body_arr.raw
    new_body: list[JsonVal] = []
    for stmt in items:
        kept = _rb_strip_extern_decls_from_stmt(stmt)
        if kept is not None:
            new_body.append(kept)
    copied["body"] = new_body
    return copied


def _rb_has_cpp_emit_definitions(east_doc: dict[str, JsonVal]) -> bool:
    body = east_doc.get("body")
    body_arr = json.JsonValue(body).as_arr()
    items: list[JsonVal] = []
    if body_arr is not None:
        items = body_arr.raw
    for stmt in items:
        stmt_obj = json.JsonValue(stmt).as_obj()
        if stmt_obj is None:
            continue
        stmt_dict = stmt_obj.raw
        kind = _rb_str(stmt_dict, "kind")
        if kind in ("Import", "ImportFrom", "Pass"):
            continue
        if kind == "Expr":
            value_obj = json.JsonValue(stmt_dict.get("value")).as_obj()
            if value_obj is not None and _rb_str(value_obj.raw, "kind") == "Constant" and json.JsonValue(value_obj.raw.get("value")).as_str() is not None:
                continue
        return True
    return False


def _rb_is_template_function_stmt(stmt: dict[str, JsonVal]) -> bool:
    if _rb_str(stmt, "kind") not in ("FunctionDef", "ClosureDef"):
        return False
    arg_types = _rb_dict(stmt, "arg_types")
    for arg_type in arg_types.values():
        arg_type_text = _rb_json_str_value(arg_type)
        if arg_type_text != "":
            if len(collect_cpp_type_vars(arg_type_text)) > 0:
                return True
    return len(collect_cpp_type_vars(_rb_return_type(stmt))) > 0


def _rb_runtime_module_is_header_only_template_lane(east_doc: dict[str, JsonVal]) -> bool:
    body = east_doc.get("body")
    body_arr = json.JsonValue(body).as_arr()
    items: list[JsonVal] = []
    if body_arr is not None:
        items = body_arr.raw
    saw_template_fn = False
    for stmt in items:
        stmt_obj = json.JsonValue(stmt).as_obj()
        if stmt_obj is None:
            continue
        stmt_dict = stmt_obj.raw
        kind = _rb_str(stmt_dict, "kind")
        if kind in ("Import", "ImportFrom", "Pass", "TypeAlias"):
            continue
        if kind == "Expr":
            value_obj = json.JsonValue(stmt_dict.get("value")).as_obj()
            if value_obj is not None and _rb_str(value_obj.raw, "kind") == "Constant" and json.JsonValue(value_obj.raw.get("value")).as_str() is not None:
                continue
        if not _rb_is_template_function_stmt(stmt_dict):
            return False
        saw_template_fn = True
    return saw_template_fn


def _rb_return_type(node: dict[str, JsonVal]) -> str:
    return_type = _rb_json_str_value(node.get("return_type"))
    if return_type != "":
        return return_type
    returns = _rb_json_str_value(node.get("returns"))
    if returns != "":
        return returns
    return "None"


def _rb_cpp_impl_body(cpp_text: str) -> str:
    marker = "// Generated by toolchain2/emit/cpp"
    idx = cpp_text.find(marker)
    if idx < 0:
        return cpp_text.strip()
    body = cpp_text[idx + len(marker):].strip()
    return body


def _rb_append_header_only_impls(header_text: str, cpp_text: str) -> str:
    impl_body = _rb_cpp_impl_body(cpp_text)
    if impl_body == "":
        return header_text
    lines = header_text.splitlines()
    insert_at = len(lines)
    i = 0
    for line in lines:
        if line.startswith("#endif"):
            insert_at = i
            break
        i += 1
    impl_lines = ["", impl_body, ""]
    new_lines: list[str] = []
    i = 0
    for line in lines:
        if i == insert_at:
            new_lines.extend(impl_lines)
        new_lines.append(line)
        i += 1
    if insert_at == len(lines):
        new_lines.extend(impl_lines)
    return "\n".join(new_lines) + "\n"


def _rb_inject_runtime_native_companion_include(header_text: str, module_id: str) -> str:
    native_hdr = native_companion_header_path(module_id)
    if not native_hdr.exists():
        return header_text
    rel = str(native_hdr).replace("\\", "/")
    if rel.startswith("src/"):
        rel = rel[4:]
    include_line = '#include "' + rel + '"'
    if include_line in header_text:
        return header_text
    lines = header_text.splitlines()
    insert_at = len(lines)
    i = 0
    for line in lines:
        if line.startswith("#endif"):
            insert_at = i
            break
        i += 1
    new_lines: list[str] = []
    i = 0
    for line in lines:
        if i == insert_at:
            if len(new_lines) > 0 and new_lines[-1] != "":
                new_lines.append("")
            new_lines.append(include_line)
            if line != "":
                new_lines.append("")
        new_lines.append(line)
        i += 1
    if insert_at == len(lines):
        if len(new_lines) > 0 and new_lines[-1] != "":
            new_lines.append("")
        new_lines.append(include_line)
    return "\n".join(new_lines) + "\n"


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

    header_path = output_dir.joinpath(rel + ".h")
    header_path.parent.mkdir(parents=True, exist_ok=True)

    emit_doc = _rb_build_emit_doc_without_extern_decls(east_doc)
    meta_obj = json.JsonValue(emit_doc.get("meta")).as_obj()
    meta: dict[str, JsonVal] = {}
    if meta_obj is None:
        meta = {}
    else:
        meta = meta_obj.raw
    linked = meta.get("linked_program_v1")
    linked_obj = json.JsonValue(linked).as_obj()
    if linked_obj is None:
        linked_dict: dict[str, JsonVal] = {}
        linked_dict["module_id"] = module_id
    else:
        linked_dict = linked_obj.raw
        if _rb_json_str_value(linked_dict.get("module_id")) == "":
            linked_dict["module_id"] = module_id

    cpp_text = ""
    source_out = ""
    has_native_companion = native_companion_header_path(module_id).exists() or native_companion_source_path(module_id).exists()
    header_only_templates = _rb_runtime_module_is_header_only_template_lane(emit_doc)
    if (not has_native_companion) and _rb_has_cpp_emit_definitions(emit_doc):
        cpp_text = emit_cpp_module(
            emit_doc,
            allow_runtime_module=True,
            self_header=rel + ".h",
        ) + ""
        if cpp_text.strip() != "" and not header_only_templates:
            source_path_out = output_dir.joinpath(rel + ".cpp")
            source_path_out.parent.mkdir(parents=True, exist_ok=True)
            source_path_out.write_text(cpp_text, encoding="utf-8")
            source_out = str(source_path_out)

    native_include = ""
    native_header = native_companion_header_path(module_id)
    if native_header.exists():
        # Use path relative to src/ so the generated #include resolves via -I src_dir
        # rather than self-shadowing via -I emit_dir (which takes search precedence).
        native_include = str(native_header).replace("\\", "/")
        if native_include.startswith("src/"):
            native_include = native_include[4:]
    header_text = build_cpp_header_from_east3(
        module_id,
        east_doc,
        rel_header_path=rel + ".h",
        native_header_include=native_include,
        prefer_native_header=native_include != "",
    )
    if header_only_templates and cpp_text.strip() != "":
        header_text = _rb_append_header_only_impls(header_text, cpp_text)
    header_path.write_text(header_text, encoding="utf-8")
    return RuntimeModuleArtifactDraft(header_path=str(header_path), source_path=source_out).as_tuple()


def write_runtime_module_artifacts(
    module_id: str,
    east_doc: dict[str, JsonVal],
    *,
    output_dir: Path,
    source_path: str = "",
) -> int:
    """Selfhost-safe wrapper that returns emitted file count."""
    header_path, source_out = emit_runtime_module_artifacts(
        module_id,
        east_doc,
        output_dir=output_dir,
        source_path=source_path,
    )
    return RuntimeModuleArtifactDraft(header_path=header_path, source_path=source_out).emitted_count()


def write_helper_module_artifacts(
    module_id: str,
    east_doc: dict[str, JsonVal],
    *,
    output_dir: Path,
    rel_header_path: str,
) -> int:
    """Write helper module source/header and return emitted file count."""
    cpp_path = output_dir.joinpath(rel_header_path[:-2] + ".cpp")
    header_path = output_dir.joinpath(rel_header_path)
    cpp_path.parent.mkdir(parents=True, exist_ok=True)
    header_path.parent.mkdir(parents=True, exist_ok=True)
    cpp_text = emit_cpp_module(east_doc, False, rel_header_path)
    header_text = build_cpp_header_from_east3(
        module_id,
        east_doc,
        rel_header_path=rel_header_path,
    )
    cpp_path.write_text(cpp_text, encoding="utf-8")
    header_path.write_text(header_text, encoding="utf-8")
    return 2


def write_user_module_artifacts(
    module_id: str,
    east_doc: dict[str, JsonVal],
    *,
    output_dir: Path,
) -> int:
    """Write user module source/header and return emitted file count."""
    rel_header_path = cpp_user_header_for_module(module_id)
    cpp_text = emit_cpp_module(east_doc, False, rel_header_path)
    if cpp_text.strip() == "":
        return 0
    cpp_path = output_dir.joinpath(module_id.replace(".", "_") + ".cpp")
    header_path = output_dir.joinpath(rel_header_path)
    header_path.parent.mkdir(parents=True, exist_ok=True)
    header_text = build_cpp_header_from_east3(
        module_id,
        east_doc,
        rel_header_path=rel_header_path,
    )
    cpp_path.write_text(cpp_text, encoding="utf-8")
    header_path.write_text(header_text, encoding="utf-8")
    return 2


def _rb_str(node: dict[str, JsonVal], key: str) -> str:
    raw = json.JsonValue(node.get(key)).as_str()
    if raw is not None:
        return raw
    return ""


def _rb_json_str_value(value: JsonVal) -> str:
    raw = json.JsonValue(value).as_str()
    if raw is not None:
        return raw
    return ""


def _rb_dict(node: dict[str, JsonVal], key: str) -> dict[str, JsonVal]:
    raw = json.JsonValue(node.get(key)).as_obj()
    if raw is not None:
        return raw.raw
    return {}
