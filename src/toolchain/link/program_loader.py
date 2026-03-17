"""Linked-program loader."""

from __future__ import annotations

from pytra.std import json
from pytra.std.pathlib import Path
from typing import Any

from toolchain.json_adapters import coerce_json_object_dict
from toolchain.link.link_manifest_io import load_link_input_doc
from toolchain.link.program_model import LinkedProgram
from toolchain.link.program_model import LinkedProgramModule
from toolchain.link.program_model import LINK_INPUT_SCHEMA
from toolchain.link.program_validator import validate_raw_east3_doc


def _load_raw_east3(path: Path) -> dict[str, object]:
    obj = json.loads_obj(path.read_text(encoding="utf-8"))
    if obj is None:
        raise RuntimeError("raw EAST3 root must be an object: " + str(path))
    return coerce_json_object_dict(obj, label="raw EAST3")


def _module_id_from_east_or_path(east_doc: dict[str, object], source_path: Path) -> str:
    meta_any = east_doc.get("meta", {})
    if isinstance(meta_any, dict):
        module_id_any = meta_any.get("module_id")
        if isinstance(module_id_any, str) and module_id_any.strip() != "":
            return module_id_any.strip()

    file_name = source_path.name
    for suffix in (".east3.json", ".json", ".py"):
        if file_name.endswith(suffix):
            file_name = file_name[: -len(suffix)]
            break
    file_name = file_name.replace("-", "_").strip()
    if file_name == "":
        raise RuntimeError("failed to infer module_id from path: " + str(source_path))
    return file_name


def build_linked_program_from_module_map(
    entry_path: Path,
    module_east_map: dict[str, dict[str, Any]],
    *,
    target: str,
    dispatch_mode: str,
    options: dict[str, object] | None = None,
) -> LinkedProgram:
    if len(module_east_map) == 0:
        raise RuntimeError("module_east_map must not be empty")

    entry_resolved = str(entry_path.resolve())
    modules: list[LinkedProgramModule] = []
    seen_module_ids: set[str] = set()
    entry_modules: list[str] = []
    module_items: list[tuple[Path, dict[str, object]]] = []
    for path_txt, east_any in module_east_map.items():
        if not isinstance(path_txt, str) or path_txt.strip() == "":
            raise RuntimeError("module_east_map keys must be non-empty paths")
        module_path = Path(path_txt).resolve()
        east_doc = coerce_json_object_dict(east_any, label="module_east_map[" + path_txt + "]")
        module_items.append((module_path, east_doc))

    for module_path, raw_east_doc in sorted(module_items, key=lambda item: str(item[0])):
        module_id = _module_id_from_east_or_path(raw_east_doc, module_path)
        if module_id in seen_module_ids:
            raise RuntimeError("duplicate module_id in module_east_map: " + module_id)
        seen_module_ids.add(module_id)
        east_doc = validate_raw_east3_doc(
            raw_east_doc,
            expected_dispatch_mode=dispatch_mode,
            module_id=module_id,
        )
        is_entry = str(module_path) == entry_resolved
        if is_entry:
            entry_modules.append(module_id)
        modules.append(
            LinkedProgramModule(
                module_id=module_id,
                source_path=str(module_path),
                is_entry=is_entry,
                east_doc=east_doc,
            )
        )

    if len(entry_modules) == 0:
        raise RuntimeError("entry module not found in module_east_map: " + entry_resolved)

    return LinkedProgram(
        schema=LINK_INPUT_SCHEMA,
        manifest_path=None,
        target=target,
        dispatch_mode=dispatch_mode,
        entry_modules=tuple(sorted(entry_modules)),
        modules=tuple(sorted(modules, key=lambda item: item.module_id)),
        options=dict(options) if isinstance(options, dict) else {},
    )


def load_linked_program(manifest_path: Path) -> LinkedProgram:
    manifest_doc = load_link_input_doc(manifest_path)
    manifest_dir = manifest_path.parent
    dispatch_mode = str(manifest_doc["dispatch_mode"])

    modules: list[LinkedProgramModule] = []
    for item_any in manifest_doc["modules"]:
        item = item_any
        module_path = manifest_dir / item.path
        raw_east_doc = _load_raw_east3(module_path)
        east_doc = validate_raw_east3_doc(
            raw_east_doc,
            expected_dispatch_mode=dispatch_mode,
            module_id=item.module_id,
        )
        modules.append(
            LinkedProgramModule(
                module_id=item.module_id,
                source_path=item.source_path,
                is_entry=item.is_entry,
                east_doc=east_doc,
                artifact_path=module_path.resolve(),
            )
        )

    return LinkedProgram(
        schema=str(manifest_doc["schema"]),
        manifest_path=manifest_path.resolve(),
        target=str(manifest_doc["target"]),
        dispatch_mode=dispatch_mode,
        entry_modules=tuple(manifest_doc["entry_modules"]),
        modules=tuple(modules),
        options=dict(manifest_doc["options"]),
    )
