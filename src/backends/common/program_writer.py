"""Shared backend program-writer helpers."""

from __future__ import annotations

from typing import Any

from pytra.std.pathlib import Path


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _modules(program_artifact: dict[str, Any]) -> list[dict[str, Any]]:
    modules_any = program_artifact.get("modules", [])
    out: list[dict[str, Any]] = []
    if isinstance(modules_any, list):
        for item in modules_any:
            if isinstance(item, dict):
                out.append(item)
    return out


def _select_primary_module(modules: list[dict[str, Any]]) -> dict[str, Any]:
    primary_modules: list[dict[str, Any]] = []
    for module in modules:
        kind_any = module.get("kind", "user")
        kind = kind_any if isinstance(kind_any, str) else "user"
        if kind == "helper":
            continue
        primary_modules.append(module)
    if len(primary_modules) != 1:
        raise RuntimeError("SingleFileProgramWriter requires exactly one non-helper module artifact")
    return primary_modules[0]


def _resolve_output_path(output_root: Path, module_artifact: dict[str, Any]) -> Path:
    if output_root.suffix != "":
        return output_root
    label = module_artifact.get("label", "")
    if not isinstance(label, str) or label == "":
        label = "module"
    ext = module_artifact.get("extension", "")
    if not isinstance(ext, str):
        ext = ""
    return output_root / (label + ext)


def write_single_file_program(
    program_artifact: dict[str, Any],
    output_root: Path,
    options: dict[str, object] | None = None,
) -> dict[str, object]:
    _ = options
    artifact = _dict(program_artifact)
    modules = _modules(artifact)
    primary_module = _select_primary_module(modules)
    text = primary_module.get("text", "")
    if not isinstance(text, str):
        text = ""
    output_path = _resolve_output_path(output_root, primary_module)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    module_id = primary_module.get("module_id", "")
    return {
        "layout_mode": "single_file",
        "primary_output": str(output_path),
        "output_files": [str(output_path)],
        "entry_modules": list(artifact.get("entry_modules", [])) if isinstance(artifact.get("entry_modules"), list) else [],
        "program_id": artifact.get("program_id", module_id if isinstance(module_id, str) else ""),
    }
