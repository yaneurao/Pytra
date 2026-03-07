"""Linked-program loader."""

from __future__ import annotations

from pytra.std import json
from pytra.std.pathlib import Path

from toolchain.link.link_manifest_io import load_link_input_doc
from toolchain.link.program_model import LinkedProgram
from toolchain.link.program_model import LinkedProgramModule
from toolchain.link.program_validator import validate_raw_east3_doc


def _load_raw_east3(path: Path) -> dict[str, object]:
    try:
        payload_any = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError("failed to parse raw EAST3: " + str(path) + ": " + str(exc)) from exc
    if not isinstance(payload_any, dict):
        raise RuntimeError("raw EAST3 root must be an object: " + str(path))
    east_doc: dict[str, object] = {}
    for key, value in payload_any.items():
        if isinstance(key, str):
            east_doc[key] = value
    return east_doc


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
                path=module_path.resolve(),
                source_path=item.source_path,
                is_entry=item.is_entry,
                east_doc=east_doc,
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
