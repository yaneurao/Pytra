"""Shared helpers for host/static backend registries."""

from __future__ import annotations

from typing import Any

from pytra.std.pathlib import Path
from toolchain.compiler.typed_boundary import coerce_ir_document


def registry_src_root(module_file: str) -> Path:
    return Path(module_file).resolve().parents[2]


def identity_ir(doc: object) -> dict[str, object]:
    return coerce_ir_document(doc)


def empty_emit(_ir: object, _output_path: Path, _emitter_options: object = None) -> str:
    return ""


def default_output_path_for(input_path: Path, ext: str) -> Path:
    stem = str(input_path)
    if stem.endswith(".py"):
        stem = stem[:-3]
    elif stem.endswith(".json"):
        stem = stem[:-5]
    return Path(stem + ext)


def copy_runtime_file(src_root: Path, src_rel: str, output_path: Path, dst_name: str) -> None:
    src = src_root / src_rel
    if not src.exists():
        raise RuntimeError("runtime source not found: " + str(src))
    dst = output_path.parent / dst_name
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def copy_runtime_files(src_root: Path, file_specs: list[object], output_path: Path) -> None:
    for item in file_specs:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise RuntimeError("invalid runtime file descriptor")
        src_rel = item[0]
        dst_name = item[1]
        if not isinstance(src_rel, str) or not isinstance(dst_name, str):
            raise RuntimeError("invalid runtime file descriptor")
        copy_runtime_file(src_root, src_rel, output_path, dst_name)


def copy_php_runtime_files(src_root: Path, file_specs: list[object], output_path: Path) -> None:
    php_src_root = src_root / "runtime" / "php"
    if not php_src_root.exists():
        raise RuntimeError("php runtime source root not found: " + str(php_src_root))
    dst_root = output_path.parent / "pytra"
    for item in file_specs:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise RuntimeError("invalid php runtime file descriptor")
        src_rel = item[0]
        dst_rel = item[1]
        if not isinstance(src_rel, str) or not isinstance(dst_rel, str):
            raise RuntimeError("invalid php runtime file descriptor")
        src = php_src_root / src_rel
        if not src.exists():
            raise RuntimeError("php runtime source missing: " + str(src))
        dst = dst_root / dst_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def runtime_none(_output_path: Path) -> None:
    return


def build_runtime_hook_from_descriptor(
    runtime_key: str,
    descriptor: dict[str, object],
    *,
    none_hook: Any,
    js_shims_hook: Any,
    copy_files_factory: Any,
    php_runtime_factory: Any,
) -> Any:
    kind = str(descriptor.get("kind", ""))
    files_any = descriptor.get("files", [])
    files = files_any if isinstance(files_any, list) else []
    if kind == "none":
        return none_hook
    if kind == "js_shims":
        return js_shims_hook
    if kind == "copy_files":
        return copy_files_factory(files)
    if kind == "php_runtime":
        return php_runtime_factory(files)
    raise RuntimeError("unsupported runtime hook kind: " + runtime_key)
