"""C++ program-writer helpers."""

from __future__ import annotations

from typing import Any

from pytra.std import json
from pytra.std.pathlib import Path

from backends.common.program_writer import write_single_file_program
from toolchain.compiler.transpile_cli import (
    check_guard_limit,
    count_text_lines,
    mkdirs_for_cli,
    write_text_file,
)


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _dict_list(value: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                out.append(item)
    return out


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _bool(value: Any) -> bool:
    return bool(value)


def _prelude_header_text() -> str:
    return (
        "// AUTO-GENERATED FILE. DO NOT EDIT.\n"
        "#ifndef PYTRA_MULTI_PRELUDE_H\n"
        "#define PYTRA_MULTI_PRELUDE_H\n\n"
        '#include "runtime/cpp/core/py_runtime.h"\n\n'
        '#include "runtime/cpp/core/process_runtime.h"\n\n'
        '#include "runtime/cpp/core/scope_exit.h"\n\n'
        "#endif  // PYTRA_MULTI_PRELUDE_H\n"
    )


def _normalize_rendered_modules(rendered_modules: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in _dict_list(rendered_modules):
        label = _text(item.get("label"))
        header_text = _text(item.get("header_text"))
        source_text = _text(item.get("source_text"))
        if label == "" or header_text == "" or source_text == "":
            raise RuntimeError("CppProgramWriter requires label/header_text/source_text for each rendered module")
        out.append(
            {
                "module": _text(item.get("module")),
                "kind": _text(item.get("kind")) if _text(item.get("kind")) != "" else "user",
                "label": label,
                "header_text": header_text,
                "source_text": source_text,
                "is_entry": _bool(item.get("is_entry")),
                "helper_id": _text(item.get("helper_id")),
                "owner_module_id": _text(item.get("owner_module_id")),
            }
        )
    if len(out) == 0:
        raise RuntimeError("CppProgramWriter requires at least one rendered module")
    return out


def _check_generated_limit(total: int, limit: int, context: str) -> None:
    if limit <= 0:
        return
    check_guard_limit(
        "emit",
        "max_generated_lines",
        total,
        {"max_generated_lines": limit},
        context,
    )


def write_cpp_rendered_program(
    output_root: Path,
    rendered_modules: list[dict[str, Any]] | Any,
    *,
    entry: str,
    entry_modules: list[str] | None = None,
    program_id: str = "",
    max_generated_lines: int = 0,
) -> dict[str, object]:
    modules = _normalize_rendered_modules(rendered_modules)
    include_dir = output_root / "include"
    src_dir = output_root / "src"
    mkdirs_for_cli(str(include_dir))
    mkdirs_for_cli(str(src_dir))

    generated_lines_total = 0
    output_files: list[str] = []
    prelude_hdr = include_dir / "pytra_multi_prelude.h"
    prelude_txt = _prelude_header_text()
    generated_lines_total += count_text_lines(prelude_txt)
    _check_generated_limit(generated_lines_total, max_generated_lines, entry)
    write_text_file(prelude_hdr, prelude_txt)
    output_files.append(str(prelude_hdr))

    manifest_modules: list[dict[str, Any]] = []
    for item in modules:
        label = _text(item.get("label"))
        module_key = _text(item.get("module"))
        header_text = _text(item.get("header_text"))
        source_text = _text(item.get("source_text"))
        is_entry = _bool(item.get("is_entry"))
        hdr_path = include_dir / (label + ".h")
        cpp_path = src_dir / (label + ".cpp")
        generated_lines_total += count_text_lines(header_text) + count_text_lines(source_text)
        _check_generated_limit(generated_lines_total, max_generated_lines, module_key if module_key != "" else label)
        write_text_file(hdr_path, header_text)
        write_text_file(cpp_path, source_text)
        output_files.append(str(hdr_path))
        output_files.append(str(cpp_path))
        manifest_modules.append(
            {
                "module": module_key,
                "kind": _text(item.get("kind")) if _text(item.get("kind")) != "" else "user",
                "label": label,
                "header": str(hdr_path),
                "source": str(cpp_path),
                "is_entry": is_entry,
                "helper_id": _text(item.get("helper_id")),
                "owner_module_id": _text(item.get("owner_module_id")),
            }
        )

    manifest_for_dump: dict[str, Any] = {
        "entry": entry,
        "include_dir": str(include_dir),
        "src_dir": str(src_dir),
        "modules": manifest_modules,
    }
    manifest_path = output_root / "manifest.json"
    manifest_txt = json.dumps(manifest_for_dump, ensure_ascii=False, indent=2)
    generated_lines_total += count_text_lines(manifest_txt)
    _check_generated_limit(generated_lines_total, max_generated_lines, entry)
    write_text_file(manifest_path, manifest_txt)
    output_files.append(str(manifest_path))

    program_name = program_id
    if program_name == "" and entry_modules is not None and len(entry_modules) > 0:
        first_entry = entry_modules[0]
        if isinstance(first_entry, str):
            program_name = first_entry

    return {
        "layout_mode": "multi_file",
        "primary_output": str(manifest_path),
        "output_files": output_files,
        "entry_modules": list(entry_modules) if isinstance(entry_modules, list) else [],
        "program_id": program_name,
        "entry": entry,
        "include_dir": str(include_dir),
        "src_dir": str(src_dir),
        "modules": manifest_modules,
        "manifest": str(manifest_path),
        "generated_lines_total": generated_lines_total,
    }


def _rendered_modules_from_program_artifact(program_artifact: dict[str, Any]) -> list[dict[str, Any]]:
    rendered_modules: list[dict[str, Any]] = []
    for module_artifact in _dict_list(program_artifact.get("modules")):
        metadata = _dict(module_artifact.get("metadata"))
        header_text = _text(metadata.get("header_text"))
        source_text = _text(metadata.get("source_text"))
        if source_text == "":
            source_text = _text(module_artifact.get("text"))
        if header_text == "" or source_text == "":
            return []
        module_key = _text(metadata.get("source_path"))
        if module_key == "":
            module_key = _text(module_artifact.get("module_id"))
        rendered_modules.append(
            {
                "module": module_key,
                "kind": _text(module_artifact.get("kind")) if _text(module_artifact.get("kind")) != "" else "user",
                "label": _text(module_artifact.get("label")),
                "header_text": header_text,
                "source_text": source_text,
                "is_entry": _bool(module_artifact.get("is_entry")),
                "helper_id": _text(metadata.get("helper_id")),
                "owner_module_id": _text(metadata.get("owner_module_id")),
            }
        )
    return rendered_modules


def write_cpp_program(
    program_artifact: dict[str, Any],
    output_root: Path,
    options: dict[str, object] | None = None,
) -> dict[str, object]:
    opts = options if isinstance(options, dict) else {}
    artifact = _dict(program_artifact)
    rendered_modules = _rendered_modules_from_program_artifact(artifact)
    if len(rendered_modules) == 0:
        return write_single_file_program(artifact, output_root, opts)
    entry_modules_any = artifact.get("entry_modules")
    entry_modules: list[str] = []
    if isinstance(entry_modules_any, list):
        for item in entry_modules_any:
            if isinstance(item, str):
                entry_modules.append(item)
    entry_key = _text(artifact.get("entry"))
    if entry_key == "" and len(rendered_modules) > 0:
        for item in rendered_modules:
            if _bool(item.get("is_entry")):
                entry_key = _text(item.get("module"))
                if entry_key != "":
                    break
        if entry_key == "":
            entry_key = _text(rendered_modules[0].get("module"))
    max_generated_lines_any = opts.get("max_generated_lines", 0)
    max_generated_lines = int(max_generated_lines_any) if isinstance(max_generated_lines_any, int) else 0
    return write_cpp_rendered_program(
        output_root,
        rendered_modules,
        entry=entry_key,
        entry_modules=entry_modules,
        program_id=_text(artifact.get("program_id")),
        max_generated_lines=max_generated_lines,
    )
