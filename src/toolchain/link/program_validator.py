"""Validation helpers for linked-program manifests."""

from __future__ import annotations

from typing import Any

from toolchain.link.program_model import DISPATCH_MODES
from toolchain.link.program_model import LINK_INPUT_SCHEMA
from toolchain.link.program_model import LINK_OUTPUT_SCHEMA
from toolchain.link.program_model import LinkInputModuleEntry
from toolchain.link.program_model import LinkOutputModuleEntry
from toolchain.link.program_model import normalize_writer_options


def _require_dict(doc: object, label: str) -> dict[str, object]:
    if not isinstance(doc, dict):
        raise RuntimeError(label + " must be an object")
    out: dict[str, object] = {}
    for key, value in doc.items():
        if isinstance(key, str):
            out[key] = value
    return out


def _require_str(doc: dict[str, object], key: str, label: str) -> str:
    value = doc.get(key)
    if not isinstance(value, str) or value.strip() == "":
        raise RuntimeError(label + "." + key + " must be a non-empty string")
    return value.strip()


def _require_bool(doc: dict[str, object], key: str, label: str) -> bool:
    value = doc.get(key)
    if not isinstance(value, bool):
        raise RuntimeError(label + "." + key + " must be a bool")
    return bool(value)


def _require_str_list(doc: dict[str, object], key: str, label: str) -> tuple[str, ...]:
    raw = doc.get(key)
    if not isinstance(raw, list):
        raise RuntimeError(label + "." + key + " must be a list")
    out: list[str] = []
    for item in raw:
        if not isinstance(item, str) or item.strip() == "":
            raise RuntimeError(label + "." + key + " items must be non-empty strings")
        out.append(item.strip())
    return tuple(out)


def validate_link_input_doc(doc_any: object) -> dict[str, object]:
    doc = _require_dict(doc_any, "link-input")
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

    raw_modules = doc.get("modules")
    if not isinstance(raw_modules, list) or len(raw_modules) == 0:
        raise RuntimeError("link-input.modules must be a non-empty list")

    module_entries: list[LinkInputModuleEntry] = []
    seen_module_ids: set[str] = set()
    for idx, item_any in enumerate(raw_modules):
        label = "link-input.modules[" + str(idx) + "]"
        item = _require_dict(item_any, label)
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
        "options": normalize_writer_options(doc.get("options")),
    }


def validate_raw_east3_doc(
    east_any: object,
    *,
    expected_dispatch_mode: str,
    module_id: str,
) -> dict[str, object]:
    east = _require_dict(east_any, "raw EAST3")
    if east.get("kind") != "Module":
        raise RuntimeError("raw EAST3 kind must be Module: " + module_id)
    stage = east.get("east_stage")
    if not isinstance(stage, int) or stage != 3:
        raise RuntimeError("raw EAST3 east_stage must be 3: " + module_id)
    body = east.get("body")
    if not isinstance(body, list):
        raise RuntimeError("raw EAST3 body must be a list: " + module_id)
    schema_version = east.get("schema_version")
    if schema_version is not None and (not isinstance(schema_version, int) or schema_version < 1):
        raise RuntimeError("raw EAST3 schema_version must be int >= 1: " + module_id)
    meta_any = east.get("meta", {})
    meta = _require_dict(meta_any, "raw EAST3.meta")
    dispatch_mode = meta.get("dispatch_mode")
    if not isinstance(dispatch_mode, str) or dispatch_mode not in DISPATCH_MODES:
        raise RuntimeError("raw EAST3.meta.dispatch_mode must be native|type_id: " + module_id)
    if dispatch_mode != expected_dispatch_mode:
        raise RuntimeError(
            "dispatch_mode mismatch for " + module_id + ": " + dispatch_mode + " != " + expected_dispatch_mode
        )
    if "linked_program_v1" in meta:
        raise RuntimeError("raw EAST3 must not contain meta.linked_program_v1: " + module_id)
    return east


def validate_link_output_doc(doc_any: object) -> dict[str, object]:
    doc = _require_dict(doc_any, "link-output")
    schema = _require_str(doc, "schema", "link-output")
    if schema != LINK_OUTPUT_SCHEMA:
        raise RuntimeError("link-output.schema must be " + LINK_OUTPUT_SCHEMA)
    _require_str(doc, "target", "link-output")
    dispatch_mode = _require_str(doc, "dispatch_mode", "link-output")
    if dispatch_mode not in DISPATCH_MODES:
        raise RuntimeError("link-output.dispatch_mode must be one of: native, type_id")
    entry_modules = _require_str_list(doc, "entry_modules", "link-output")
    modules_any = doc.get("modules")
    if not isinstance(modules_any, list):
        raise RuntimeError("link-output.modules must be a list")
    module_entries: list[LinkOutputModuleEntry] = []
    seen_module_ids: set[str] = set()
    for idx, item_any in enumerate(modules_any):
        label = "link-output.modules[" + str(idx) + "]"
        item = _require_dict(item_any, label)
        module_id = _require_str(item, "module_id", label)
        if module_id in seen_module_ids:
            raise RuntimeError("duplicate link-output module_id: " + module_id)
        seen_module_ids.add(module_id)
        module_entries.append(
            LinkOutputModuleEntry(
                module_id=module_id,
                input=_require_str(item, "input", label),
                output=_require_str(item, "output", label),
                source_path=_require_str(item, "source_path", label),
                is_entry=_require_bool(item, "is_entry", label),
            )
        )
    module_id_set = {item.module_id for item in module_entries}
    for module_id in entry_modules:
        if module_id not in module_id_set:
            raise RuntimeError("missing link-output entry module: " + module_id)
    for item in module_entries:
        if item.is_entry and item.module_id not in entry_modules:
            raise RuntimeError("link-output module marked is_entry but not present in entry_modules: " + item.module_id)
    global_any = doc.get("global")
    global_doc = _require_dict(global_any, "link-output.global")
    for key in (
        "type_id_table",
        "call_graph",
        "sccs",
        "non_escape_summary",
        "container_ownership_hints_v1",
    ):
        if key not in global_doc:
            raise RuntimeError("link-output.global." + key + " is required")
    diagnostics_any = doc.get("diagnostics")
    diagnostics = _require_dict(diagnostics_any, "link-output.diagnostics")
    for key in ("warnings", "errors"):
        if not isinstance(diagnostics.get(key), list):
            raise RuntimeError("link-output.diagnostics." + key + " must be a list")
    return {
        "schema": schema,
        "target": doc["target"],
        "dispatch_mode": dispatch_mode,
        "entry_modules": entry_modules,
        "modules": sorted(module_entries, key=lambda item: item.module_id),
        "global": global_doc,
        "diagnostics": diagnostics,
    }
