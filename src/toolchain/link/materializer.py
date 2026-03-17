"""Disk I/O helpers for linked-program input/output bundles."""

from __future__ import annotations

from typing import Any

from pytra.std import json
from pytra.std.pathlib import Path

from toolchain.json_adapters import export_json_object_dict
from toolchain.link.global_optimizer import LinkedProgramOptimizationResult
from toolchain.link.link_manifest_io import load_link_output_doc
from toolchain.link.link_manifest_io import save_manifest_doc
from toolchain.link.program_model import LINK_INPUT_SCHEMA
from toolchain.link.program_model import LinkedProgram
from toolchain.link.program_model import LinkedProgramModule


def _module_rel_path(module_id: str, *, prefix: str) -> str:
    stem = module_id.replace(".", "/")
    return prefix + "/" + stem + ".east3.json"


def _load_json_doc(path: Path, label: str) -> dict[str, object]:
    if not path.exists():
        raise RuntimeError(label + " not found: " + str(path))
    try:
        obj = json.loads_obj(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError("failed to parse " + label + ": " + str(path) + ": " + str(exc)) from exc
    if obj is None:
        raise RuntimeError(label + " root must be an object: " + str(path))
    return export_json_object_dict(obj)


def _load_linked_east3_doc(
    path: Path,
    *,
    module_id: str,
    module_kind: str = "user",
    helper_id: str = "",
    owner_module_id: str = "",
) -> dict[str, object]:
    doc = _load_json_doc(path, "linked EAST3")
    if doc.get("kind") != "Module":
        raise RuntimeError("linked EAST3 kind must be Module: " + module_id)
    stage = doc.get("east_stage")
    if not isinstance(stage, int) or stage != 3:
        raise RuntimeError("linked EAST3 east_stage must be 3: " + module_id)
    body = doc.get("body")
    if not isinstance(body, list):
        raise RuntimeError("linked EAST3 body must be a list: " + module_id)
    meta_any = doc.get("meta")
    if not isinstance(meta_any, dict):
        raise RuntimeError("linked EAST3 meta must be an object: " + module_id)
    linked_any = meta_any.get("linked_program_v1")
    if not isinstance(linked_any, dict):
        raise RuntimeError("linked EAST3 meta.linked_program_v1 is required: " + module_id)
    linked_module_id = linked_any.get("module_id")
    if not isinstance(linked_module_id, str) or linked_module_id != module_id:
        raise RuntimeError("linked EAST3 module_id mismatch: " + module_id)
    if module_kind == "helper":
        synthetic_any = meta_any.get("synthetic_helper_v1")
        if not isinstance(synthetic_any, dict):
            raise RuntimeError("linked helper meta.synthetic_helper_v1 is required: " + module_id)
        if synthetic_any.get("helper_id") != helper_id:
            raise RuntimeError("linked helper helper_id mismatch: " + module_id)
        if synthetic_any.get("owner_module_id") != owner_module_id:
            raise RuntimeError("linked helper owner_module_id mismatch: " + module_id)
    return doc


def build_link_input_doc_for_program(
    program: LinkedProgram,
    *,
    module_prefix: str = "raw",
) -> dict[str, object]:
    modules: list[dict[str, object]] = []
    for module in program.modules:
        modules.append(
            {
                "module_id": module.module_id,
                "path": _module_rel_path(module.module_id, prefix=module_prefix),
                "source_path": module.source_path,
                "is_entry": module.is_entry,
            }
        )
    return {
        "schema": LINK_INPUT_SCHEMA,
        "target": program.target,
        "dispatch_mode": program.dispatch_mode,
        "entry_modules": list(program.entry_modules),
        "modules": modules,
        "options": dict(program.options),
    }


def write_link_input_bundle(
    output_dir: Path,
    program: LinkedProgram,
    *,
    module_prefix: str = "raw",
) -> tuple[Path, list[Path]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for module in program.modules:
        output_path = output_dir / _module_rel_path(module.module_id, prefix=module_prefix)
        save_manifest_doc(output_path, module.east_doc)
        written.append(output_path)
    manifest_doc = build_link_input_doc_for_program(program, module_prefix=module_prefix)
    manifest_path = output_dir / "link-input.json"
    save_manifest_doc(manifest_path, manifest_doc)
    return manifest_path, written


def _module_output_map(link_output_doc: dict[str, object]) -> dict[str, str]:
    modules_any = link_output_doc.get("modules", [])
    out: dict[str, str] = {}
    if not isinstance(modules_any, list):
        return out
    for item in modules_any:
        if not isinstance(item, dict):
            continue
        module_id = item.get("module_id")
        output = item.get("output")
        if isinstance(module_id, str) and module_id != "" and isinstance(output, str) and output != "":
            out[module_id] = output
    return out


def write_link_output_bundle(
    output_dir: Path,
    result: LinkedProgramOptimizationResult,
) -> tuple[Path, list[Path]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    link_output_doc = result.link_output_doc
    link_output_path = output_dir / "link-output.json"
    save_manifest_doc(link_output_path, link_output_doc)

    output_map = _module_output_map(link_output_doc)
    written: list[Path] = []
    for module in result.linked_program.modules:
        rel_path = output_map.get(module.module_id, _module_rel_path(module.module_id, prefix="linked"))
        output_path = output_dir / rel_path
        save_manifest_doc(output_path, module.east_doc)
        written.append(output_path)
    return link_output_path, written


def load_linked_output_bundle(
    manifest_path: Path,
) -> tuple[dict[str, object], tuple[LinkedProgramModule, ...]]:
    manifest_doc = load_link_output_doc(manifest_path)
    manifest_dir = manifest_path.parent
    modules_any = manifest_doc.get("modules", [])
    modules: list[LinkedProgramModule] = []
    if not isinstance(modules_any, list):
        raise RuntimeError("link-output.modules must be a list")
    for index, item in enumerate(modules_any):
        module_id = getattr(item, "module_id", "")
        output = getattr(item, "output", "")
        source_path = getattr(item, "source_path", "")
        is_entry = bool(getattr(item, "is_entry", False))
        if not isinstance(module_id, str) or module_id == "":
            raise RuntimeError("link-output.modules[" + str(index) + "].module_id must be non-empty string")
        if not isinstance(output, str) or output == "":
            raise RuntimeError("link-output.modules[" + str(index) + "].output must be non-empty string")
        artifact_path = (manifest_dir / output).resolve()
        east_doc = _load_linked_east3_doc(
            artifact_path,
            module_id=module_id,
            module_kind=item.module_kind,
            helper_id=item.helper_id,
            owner_module_id=item.owner_module_id,
        )
        modules.append(
            LinkedProgramModule(
                module_id=module_id,
                source_path=source_path if isinstance(source_path, str) else "",
                is_entry=is_entry,
                east_doc=east_doc,
                artifact_path=artifact_path,
                module_kind=item.module_kind,
                helper_id=item.helper_id,
                owner_module_id=item.owner_module_id,
                generated_by=item.generated_by,
            )
        )
    modules.sort(key=lambda item: item.module_id)
    return manifest_doc, tuple(modules)
