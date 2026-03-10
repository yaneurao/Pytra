"""Validation helpers for linked-program manifests."""

from __future__ import annotations

from pytra.std import json

from toolchain.frontends.type_expr import sync_type_expr_mirrors
from toolchain.json_adapters import coerce_json_object_doc
from toolchain.json_adapters import export_json_object_dict
from toolchain.json_adapters import export_json_value_raw
from toolchain.json_adapters import json_array_length
from toolchain.json_adapters import json_value_as_object_doc_or_empty
from toolchain.link.program_model import DISPATCH_MODES
from toolchain.link.program_model import LINK_INPUT_SCHEMA
from toolchain.link.program_model import LINK_OUTPUT_SCHEMA
from toolchain.link.program_model import LinkInputModuleEntry
from toolchain.link.program_model import LinkOutputModuleEntry
from toolchain.link.program_model import MODULE_KINDS
from toolchain.link.program_model import normalize_writer_options


def _iter_object_tree(value: object, path: str) -> object:
    if isinstance(value, dict):
        yield (path, value)
        for key, child in value.items():
            yield from _iter_object_tree(child, path + "." + str(key))
        return
    if isinstance(value, list):
        for idx, child in enumerate(value):
            yield from _iter_object_tree(child, path + "[" + str(idx) + "]")


def _validate_source_span_shape(span_any: object, label: str) -> None:
    if not isinstance(span_any, dict):
        raise RuntimeError(label + " must be an object")
    for key in ("lineno", "end_lineno", "col_offset", "end_col_offset"):
        value = span_any.get(key)
        if type(value) is not int:
            raise RuntimeError(label + "." + key + " must be int")
    start_line = int(span_any["lineno"])
    end_line = int(span_any["end_lineno"])
    start_col = int(span_any["col_offset"])
    end_col = int(span_any["end_col_offset"])
    if end_line < start_line or (end_line == start_line and end_col < start_col):
        raise RuntimeError(label + " must not encode reversed range")


def _validate_raw_east3_invariants(
    raw_doc: dict[str, object],
    *,
    expected_dispatch_mode: str,
    module_id: str,
) -> None:
    for path, obj in _iter_object_tree(raw_doc, "$"):
        if not isinstance(obj, dict):
            continue
        kind = obj.get("kind")
        if kind is not None and (not isinstance(kind, str) or kind.strip() == ""):
            raise RuntimeError("raw EAST3 " + path + ".kind must be non-empty string: " + module_id)
        repr_value = obj.get("repr")
        if repr_value is not None and not isinstance(repr_value, str):
            raise RuntimeError("raw EAST3 " + path + ".repr must be string: " + module_id)
        source_span = obj.get("source_span")
        meta = obj.get("meta")
        generated_by = meta.get("generated_by") if isinstance(meta, dict) else None
        if kind is not None and kind != "Module" and source_span is None and not isinstance(generated_by, str):
            raise RuntimeError("raw EAST3 " + path + ".source_span is required: " + module_id)
        if source_span is not None:
            _validate_source_span_shape(source_span, "raw EAST3 " + path + ".source_span")
        if meta is None:
            continue
        if not isinstance(meta, dict):
            raise RuntimeError("raw EAST3 " + path + ".meta must be an object: " + module_id)
        node_dispatch_mode = meta.get("dispatch_mode")
        if node_dispatch_mode is None:
            continue
        if not isinstance(node_dispatch_mode, str):
            raise RuntimeError("raw EAST3 " + path + ".meta.dispatch_mode must be string: " + module_id)
        if node_dispatch_mode != expected_dispatch_mode:
            raise RuntimeError(
                "raw EAST3 " + path + ".meta.dispatch_mode mismatch: "
                + node_dispatch_mode
                + " != "
                + expected_dispatch_mode
                + ": "
                + module_id
            )


def _require_str(doc: json.JsonObj, key: str, label: str) -> str:
    value = doc.get_str(key)
    if value is None or value.strip() == "":
        raise RuntimeError(label + "." + key + " must be a non-empty string")
    return value.strip()


def _require_bool(doc: json.JsonObj, key: str, label: str) -> bool:
    value = doc.get_bool(key)
    if value is None:
        raise RuntimeError(label + "." + key + " must be a bool")
    return value


def _require_obj_field(doc: json.JsonObj, key: str, label: str) -> json.JsonObj:
    value = doc.get_obj(key)
    if value is None:
        raise RuntimeError(label + "." + key + " must be an object")
    return value


def _str_or_empty(doc: json.JsonObj, key: str) -> str:
    value = doc.get_str(key)
    if value is None:
        return ""
    return value


def _require_list_field(doc: json.JsonObj, key: str, label: str) -> json.JsonArr:
    value = doc.get_arr(key)
    if value is None:
        raise RuntimeError(label + "." + key + " must be a list")
    return value


def _require_str_list(doc: json.JsonObj, key: str, label: str) -> tuple[str, ...]:
    raw = _require_list_field(doc, key, label)
    out: list[str] = []
    for index in range(json_array_length(raw)):
        item = raw.get_str(index)
        if item is None or item.strip() == "":
            raise RuntimeError(label + "." + key + " items must be non-empty strings")
        out.append(item.strip())
    return tuple(out)


def _require_non_empty_str_items(arr: json.JsonArr, label: str) -> None:
    for index in range(json_array_length(arr)):
        item = arr.get_str(index)
        if item is None or item.strip() == "":
            raise RuntimeError(label + "[" + str(index) + "] must be a non-empty string")


def _validate_link_output_diagnostic_items(arr: json.JsonArr, label: str) -> None:
    for index in range(json_array_length(arr)):
        item_label = label + "[" + str(index) + "]"
        item_obj = arr.get_obj(index)
        if item_obj is not None:
            category = item_obj.get_str("category")
            if category is None or category.strip() == "":
                raise RuntimeError(item_label + ".category must be a non-empty string")
            message = item_obj.get_str("message")
            if message is None or message.strip() == "":
                raise RuntimeError(item_label + ".message must be a non-empty string")
            span = item_obj.get("source_span")
            if span is None:
                continue
            span_obj = item_obj.get_obj("source_span")
            if span_obj is None:
                raise RuntimeError(item_label + ".source_span must be an object")
            _validate_source_span_shape(export_json_object_dict(span_obj), item_label + ".source_span")
            continue
        item = arr.get_str(index)
        if item is None or item.strip() == "":
            raise RuntimeError(item_label + " must be a non-empty string or object")


def _validate_link_output_global_shape(global_doc: json.JsonObj) -> None:
    _require_obj_field(global_doc, "type_id_table", "link-output.global")
    _require_obj_field(global_doc, "call_graph", "link-output.global")
    _require_list_field(global_doc, "sccs", "link-output.global")
    _require_obj_field(global_doc, "non_escape_summary", "link-output.global")
    _require_obj_field(global_doc, "container_ownership_hints_v1", "link-output.global")


def validate_link_input_doc(doc_any: object) -> dict[str, object]:
    doc = coerce_json_object_doc(doc_any, label="link-input")
    schema = _require_str(doc, "schema", "link-input")
    if schema != LINK_INPUT_SCHEMA:
        raise RuntimeError("link-input.schema must be " + LINK_INPUT_SCHEMA)

    target = _require_str(doc, "target", "link-input")
    dispatch_mode = _require_str(doc, "dispatch_mode", "link-input")
    if dispatch_mode not in DISPATCH_MODES:
        raise RuntimeError("link-input.dispatch_mode must be one of: native, type_id")

    entry_modules = _require_str_list(doc, "entry_modules", "link-input")
    if len(set(entry_modules)) != len(entry_modules):
        raise RuntimeError("link-input.entry_modules must be unique")

    raw_modules = _require_list_field(doc, "modules", "link-input")
    if json_array_length(raw_modules) == 0:
        raise RuntimeError("link-input.modules must be a non-empty list")

    module_entries: list[LinkInputModuleEntry] = []
    seen_module_ids: set[str] = set()
    for idx in range(json_array_length(raw_modules)):
        label = "link-input.modules[" + str(idx) + "]"
        item = raw_modules.get_obj(idx)
        if item is None:
            raise RuntimeError(label + " must be an object")
        module_id = _require_str(item, "module_id", label)
        if module_id in seen_module_ids:
            raise RuntimeError("duplicate module_id: " + module_id)
        seen_module_ids.add(module_id)
        entry = LinkInputModuleEntry(
            module_id=module_id,
            path=_require_str(item, "path", label),
            source_path=_require_str(item, "source_path", label),
            is_entry=_require_bool(item, "is_entry", label),
        )
        module_entries.append(entry)

    module_id_set = {item.module_id for item in module_entries}
    for module_id in entry_modules:
        if module_id not in module_id_set:
            raise RuntimeError("missing entry module: " + module_id)

    for item in module_entries:
        if item.is_entry and item.module_id not in entry_modules:
            raise RuntimeError("module marked is_entry but not present in entry_modules: " + item.module_id)

    return {
        "schema": schema,
        "target": target,
        "dispatch_mode": dispatch_mode,
        "entry_modules": tuple(sorted(entry_modules)),
        "modules": sorted(module_entries, key=lambda item: item.module_id),
        "options": normalize_writer_options(export_json_value_raw(doc.get("options"))),
    }


def validate_raw_east3_doc(
    east_any: object,
    *,
    expected_dispatch_mode: str,
    module_id: str,
) -> dict[str, object]:
    east = coerce_json_object_doc(east_any, label="raw EAST3")
    if east.get_str("kind") != "Module":
        raise RuntimeError("raw EAST3 kind must be Module: " + module_id)
    stage = east.get_int("east_stage")
    if stage != 3:
        raise RuntimeError("raw EAST3 east_stage must be 3: " + module_id)
    body = _require_list_field(east, "body", "raw EAST3")
    for idx in range(json_array_length(body)):
        if body.get_obj(idx) is None:
            raise RuntimeError("raw EAST3.body[" + str(idx) + "] must be an object: " + module_id)
    schema_version_value = east.get("schema_version")
    schema_version = schema_version_value.as_int() if schema_version_value is not None else None
    if schema_version_value is not None and (schema_version is None or schema_version < 1):
        raise RuntimeError("raw EAST3 schema_version must be int >= 1: " + module_id)
    meta_value = east.get("meta")
    meta = json_value_as_object_doc_or_empty(meta_value)
    dispatch_mode = meta.get_str("dispatch_mode")
    if dispatch_mode is None or dispatch_mode not in DISPATCH_MODES:
        raise RuntimeError("raw EAST3.meta.dispatch_mode must be native|type_id: " + module_id)
    if dispatch_mode != expected_dispatch_mode:
        raise RuntimeError(
            "dispatch_mode mismatch for " + module_id + ": " + dispatch_mode + " != " + expected_dispatch_mode
        )
    if meta.get("linked_program_v1") is not None:
        raise RuntimeError("raw EAST3 must not contain meta.linked_program_v1: " + module_id)
    raw_doc = export_json_object_dict(east)
    sync_type_expr_mirrors(raw_doc)
    _validate_raw_east3_invariants(raw_doc, expected_dispatch_mode=expected_dispatch_mode, module_id=module_id)
    return raw_doc


def validate_link_output_doc(doc_any: object) -> dict[str, object]:
    doc = coerce_json_object_doc(doc_any, label="link-output")
    schema = _require_str(doc, "schema", "link-output")
    if schema != LINK_OUTPUT_SCHEMA:
        raise RuntimeError("link-output.schema must be " + LINK_OUTPUT_SCHEMA)
    _require_str(doc, "target", "link-output")
    dispatch_mode = _require_str(doc, "dispatch_mode", "link-output")
    if dispatch_mode not in DISPATCH_MODES:
        raise RuntimeError("link-output.dispatch_mode must be one of: native, type_id")
    entry_modules = _require_str_list(doc, "entry_modules", "link-output")
    modules_any = _require_list_field(doc, "modules", "link-output")
    module_entries: list[LinkOutputModuleEntry] = []
    seen_module_ids: set[str] = set()
    for idx in range(json_array_length(modules_any)):
        label = "link-output.modules[" + str(idx) + "]"
        item = modules_any.get_obj(idx)
        if item is None:
            raise RuntimeError(label + " must be an object")
        module_id = _require_str(item, "module_id", label)
        if module_id in seen_module_ids:
            raise RuntimeError("duplicate link-output module_id: " + module_id)
        seen_module_ids.add(module_id)
        module_kind = _str_or_empty(item, "module_kind")
        if module_kind == "":
            module_kind = "user"
        if module_kind not in MODULE_KINDS:
            raise RuntimeError(label + ".module_kind must be one of: user, runtime, helper")
        helper_id = _str_or_empty(item, "helper_id")
        owner_module_id = _str_or_empty(item, "owner_module_id")
        generated_by = _str_or_empty(item, "generated_by")
        source_path = _str_or_empty(item, "source_path")
        if module_kind == "helper":
            if helper_id == "":
                raise RuntimeError(label + ".helper_id is required for helper module")
            if owner_module_id == "":
                raise RuntimeError(label + ".owner_module_id is required for helper module")
            if generated_by != "linked_optimizer":
                raise RuntimeError(label + ".generated_by must be linked_optimizer for helper module")
        else:
            if helper_id != "" or owner_module_id != "" or generated_by != "":
                raise RuntimeError(label + " must not carry helper metadata unless module_kind=helper")
            source_path = _require_str(item, "source_path", label)
        module_entries.append(
            LinkOutputModuleEntry(
                module_id=module_id,
                input=_require_str(item, "input", label),
                output=_require_str(item, "output", label),
                source_path=source_path,
                is_entry=_require_bool(item, "is_entry", label),
                module_kind=module_kind,
                helper_id=helper_id,
                owner_module_id=owner_module_id,
                generated_by=generated_by,
            )
        )
    module_id_set = {item.module_id for item in module_entries}
    for module_id in entry_modules:
        if module_id not in module_id_set:
            raise RuntimeError("missing link-output entry module: " + module_id)
    for item in module_entries:
        if item.is_entry and item.module_id not in entry_modules:
            raise RuntimeError("link-output module marked is_entry but not present in entry_modules: " + item.module_id)
    global_doc = _require_obj_field(doc, "global", "link-output")
    _validate_link_output_global_shape(global_doc)
    diagnostics = _require_obj_field(doc, "diagnostics", "link-output")
    for key in ("warnings", "errors"):
        arr = diagnostics.get_arr(key)
        if arr is None:
            raise RuntimeError("link-output.diagnostics." + key + " must be a list")
        _validate_link_output_diagnostic_items(arr, "link-output.diagnostics." + key)
    return {
        "schema": schema,
        "target": _require_str(doc, "target", "link-output"),
        "dispatch_mode": dispatch_mode,
        "entry_modules": entry_modules,
        "modules": sorted(module_entries, key=lambda item: item.module_id),
        "global": export_json_object_dict(global_doc),
        "diagnostics": export_json_object_dict(diagnostics),
    }
