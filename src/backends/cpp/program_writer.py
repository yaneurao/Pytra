"""C++ program-writer helpers."""

from __future__ import annotations

import os
import shutil
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
from toolchain.json_adapters import dumps_object as _json_dumps_object


_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_RUNTIME_CPP_ROOT = _PROJECT_ROOT / "src" / "runtime" / "cpp"
_RUNTIME_EAST_ROOT = _PROJECT_ROOT / "src" / "runtime" / "generated"


def _copy_native_runtime_to_output(output_root: Path) -> list[str]:
    """Copy native C++ runtime headers/sources to output directory.

    Preserves namespace folder structure (core/, built_in/, std/).
    Returns list of copied file paths.
    """
    copied: list[str] = []
    src_root_str = str(_RUNTIME_CPP_ROOT)
    if not os.path.isdir(src_root_str):
        return copied
    for subdir in ("core", "built_in", "std"):
        src_dir_str = os.path.join(src_root_str, subdir)
        if not os.path.isdir(src_dir_str):
            continue
        dst_dir = output_root / subdir
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst_dir_str = str(dst_dir)
        for name in sorted(os.listdir(src_dir_str)):
            if name.endswith(".h") or name.endswith(".cpp"):
                src_file = os.path.join(src_dir_str, name)
                if os.path.isfile(src_file):
                    dst_file = os.path.join(dst_dir_str, name)
                    shutil.copy2(src_file, dst_file)
                    copied.append(dst_file)
    return copied


def _generate_declarations_only_header(cpp_text: str, guard: str, bucket: str, name: str) -> str:
    """Generate a header with only function forward declarations (no bodies).

    Used for @extern modules where native .cpp provides the implementation.
    """
    import re as _re
    _func_re = _re.compile(
        r"^((?:static\s+inline\s+|inline\s+|static\s+)?)"
        r"([:A-Za-z_][\w:*&<>, ]*\S)\s+"
        r"([A-Za-z_]\w*)\s*"
        r"(\([^)]*\))"
        r"\s*\{"
    )
    # Also capture global variable declarations: Type name = ...;
    _var_re = _re.compile(r"^([A-Za-z_][\w:*&<>, ]*\S)\s+([A-Za-z_]\w*)\s*=")

    lines = cpp_text.splitlines()
    decls: list[str] = []
    seen: set[str] = set()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#include ") or stripped.startswith("//") or stripped == "":
            continue
        m = _func_re.match(stripped)
        if m and m.group(3) not in seen:
            seen.add(m.group(3))
            quals = m.group(1).strip()
            parts = ([quals] if quals else []) + [m.group(2).strip()]
            decls.append(" ".join(parts) + " " + m.group(3) + m.group(4) + ";")
            continue
        vm = _var_re.match(stripped)
        if vm and vm.group(2) not in seen:
            seen.add(vm.group(2))
            decls.append("extern " + vm.group(1) + " " + vm.group(2) + ";")

    # Derive namespace from bucket/name for @extern runtime modules.
    # e.g. std/os_path → pytra::std::os_path
    stem_name = name[:-5] if name.endswith(".east") else name
    if bucket == "std":
        ns = "pytra::std::" + stem_name
    elif bucket == "utils":
        ns = "pytra::utils::" + stem_name
    else:
        ns = ""

    body = "\n".join(decls)
    if ns != "":
        body = "namespace " + ns + " {\n" + body + "\n}  // namespace " + ns

    return (
        "// AUTO-GENERATED declarations from " + bucket + "/" + name + "\n"
        "#ifndef " + guard + "\n"
        "#define " + guard + "\n\n"
        + body + "\n\n"
        "#endif  // " + guard + "\n"
    )


def _generate_runtime_east_headers(output_root: Path) -> list[str]:
    """Transpile runtime .east files to C++ headers in output directory.

    Each .east → transpile_to_cpp → strip to header-only → write to namespace folder.
    """
    generated: list[str] = []
    east_root_str = str(_RUNTIME_EAST_ROOT)
    if not os.path.isdir(east_root_str):
        return generated
    from backends.cpp.emitter import transpile_to_cpp
    import json as _json
    for bucket in ("built_in", "std", "utils"):
        bucket_dir = os.path.join(east_root_str, bucket)
        if not os.path.isdir(bucket_dir):
            continue
        dst_dir = output_root / bucket
        dst_dir.mkdir(parents=True, exist_ok=True)
        for name in sorted(os.listdir(bucket_dir)):
            if not name.endswith(".east"):
                continue
            east_path = os.path.join(bucket_dir, name)
            stem = name[:-5]  # remove .east
            dst_h = str(dst_dir / (stem + ".h"))
            # Skip if native header already exists (native takes precedence).
            if os.path.isfile(dst_h):
                continue
            # If native .cpp exists, this is an @extern module.
            # Generate a declarations-only header (no function bodies).
            dst_cpp = str(dst_dir / (stem + ".cpp"))
            if os.path.isfile(dst_cpp):
                try:
                    east_text = open(east_path, "r", encoding="utf-8").read()
                    east_doc = _json.loads(east_text)
                    cpp_text = transpile_to_cpp(east_doc, emit_main=False)
                    guard = "PYTRA_GEN_" + bucket.upper() + "_" + stem.upper() + "_H"
                    decl_header = _generate_declarations_only_header(cpp_text, guard, bucket, name)
                    with open(dst_h, "w", encoding="utf-8") as fh:
                        fh.write(decl_header)
                    generated.append(dst_h)
                except Exception:
                    pass
                continue
            try:
                east_text = open(east_path, "r", encoding="utf-8").read()
                east_doc = _json.loads(east_text)
                cpp_text = transpile_to_cpp(east_doc, emit_main=False)
                # Strip only py_runtime.h / process_runtime.h includes (already in chain).
                # Keep other includes — generated headers may depend on other modules.
                _SKIP = {
                    '#include "core/py_runtime.h"',
                    '#include "core/process_runtime.h"',
                    '#include "core/scope_exit.h"',
                }
                lines = cpp_text.splitlines()
                body: list[str] = []
                for line in lines:
                    stripped = line.strip()
                    if stripped in _SKIP:
                        continue
                    body.append(line)
                # Trim blank prefix/suffix.
                while body and body[0].strip() == "":
                    body.pop(0)
                while body and body[-1].strip() == "":
                    body.pop()
                # Extract forward declarations for functions defined in this header.
                import re as _re
                _func_re = _re.compile(
                    r"^((?:static\s+inline\s+|inline\s+|static\s+)?)"
                    r"([A-Za-z_][\w:*&<>, ]*\S)\s+"
                    r"([A-Za-z_]\w*)\s*"
                    r"(\([^)]*\))"
                    r"\s*\{"
                )
                _struct_re = _re.compile(r"^struct\s+([A-Za-z_]\w*)\s*")
                fwd_decls: list[str] = []
                fwd_seen: set[str] = set()
                # Collect struct forward declarations first.
                for line in body:
                    sm = _struct_re.match(line)
                    if sm and sm.group(1) not in fwd_seen:
                        fwd_seen.add(sm.group(1))
                        fwd_decls.append("struct " + sm.group(1) + ";")
                # Then function forward declarations.
                for line in body:
                    m = _func_re.match(line)
                    if m and m.group(3) not in fwd_seen:
                        fwd_seen.add(m.group(3))
                        quals = m.group(1).strip()
                        parts = ([quals] if quals else []) + [m.group(2).strip()]
                        fwd_decls.append(" ".join(parts) + " " + m.group(3) + m.group(4) + ";")
                guard = "PYTRA_GEN_" + bucket.upper() + "_" + stem.upper() + "_H"
                fwd_block = ""
                if fwd_decls:
                    fwd_block = "// forward declarations\n" + "\n".join(fwd_decls) + "\n\n"
                header = (
                    "// AUTO-GENERATED from " + bucket + "/" + name + "\n"
                    "#ifndef " + guard + "\n"
                    "#define " + guard + "\n\n"
                    + fwd_block
                    + "\n".join(body) + "\n\n"
                    "#endif  // " + guard + "\n"
                )
                with open(dst_h, "w", encoding="utf-8") as fh:
                    fh.write(header)
                generated.append(dst_h)
            except Exception:
                pass  # Skip modules that fail to transpile.
    return generated


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
        '#include "core/py_runtime.h"\n\n'
        '#include "core/process_runtime.h"\n\n'
        '#include "core/scope_exit.h"\n\n'
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

    # Copy native runtime and generate C++ from .east for self-contained build.
    runtime_files = _copy_native_runtime_to_output(output_root)
    runtime_files.extend(_generate_runtime_east_headers(output_root))

    generated_lines_total = 0
    output_files: list[str] = list(runtime_files)
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
    manifest_txt = _json_dumps_object(manifest_for_dump, ensure_ascii=False, indent=2)
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
