#!/usr/bin/env python3
"""Shared EAST core helpers for import binding normalization and registration."""

from __future__ import annotations

from typing import Any
from typing import Callable

from toolchain.frontends.runtime_symbol_index import resolve_import_binding_doc


def _sh_append_import_binding(
    *,
    import_bindings: list[dict[str, Any]],
    import_binding_names: set[str],
    module_id: str,
    export_name: str,
    local_name: str,
    binding_kind: str,
    source_file: str,
    source_line: int,
    make_east_build_error: Callable[..., Exception],
    make_import_build_error: Callable[..., Exception],
    make_span: Callable[..., dict[str, int]],
    make_import_binding: Callable[..., dict[str, Any]],
) -> None:
    """import 情報の正本 `ImportBinding` を追加する。"""
    if local_name in import_binding_names:
        raise make_import_build_error(
            code="duplicate_binding",
            message=f"duplicate import binding: {local_name}",
            source_span=make_span(source_line, 0, 0),
            hint="Rename alias to avoid duplicate imported names.",
            local_name=local_name,
        )
    import_binding_names.add(local_name)
    import_bindings.append(
        make_import_binding(
            module_id=module_id,
            export_name=export_name,
            local_name=local_name,
            binding_kind=binding_kind,
            source_file=source_file,
            source_line=source_line,
        )
    )


def _sh_import_binding_fields(binding: dict[str, Any]) -> tuple[str, str, str, str, str, int]:
    """import binding raw dict から共通 field を取り出す。"""
    module_id_obj = binding.get("module_id")
    export_name_obj = binding.get("export_name")
    local_name_obj = binding.get("local_name")
    binding_kind_obj = binding.get("binding_kind")
    source_file_obj = binding.get("source_file")
    source_line_obj = binding.get("source_line")
    module_id = module_id_obj if isinstance(module_id_obj, str) else ""
    export_name = export_name_obj if isinstance(export_name_obj, str) else ""
    local_name = local_name_obj if isinstance(local_name_obj, str) else ""
    binding_kind = binding_kind_obj if isinstance(binding_kind_obj, str) else ""
    source_file = source_file_obj if isinstance(source_file_obj, str) else ""
    source_line = source_line_obj if isinstance(source_line_obj, int) else 0
    return module_id, export_name, local_name, binding_kind, source_file, source_line


def _sh_make_import_resolution_binding(
    binding: dict[str, Any],
    *,
    make_import_binding: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    module_id, export_name, local_name, binding_kind, source_file, source_line = _sh_import_binding_fields(binding)
    out = make_import_binding(
        module_id=module_id,
        export_name=export_name,
        local_name=local_name,
        binding_kind=binding_kind,
        source_file=source_file,
        source_line=source_line,
    )
    resolution = resolve_import_binding_doc(
        module_id,
        export_name,
        binding_kind,
    )
    for key in (
        "source_module_id",
        "source_export_name",
        "source_binding_kind",
        "runtime_module_id",
        "runtime_group",
        "resolved_binding_kind",
        "runtime_symbol",
        "runtime_symbol_kind",
        "runtime_symbol_dispatch",
        "runtime_semantic_tag",
        "runtime_call_adapter_kind",
    ):
        value = resolution.get(key)
        if isinstance(value, str) and value != "":
            out[key] = value
    return out


def _sh_is_host_only_alias(local_name: str) -> bool:
    """`__name` 形式の host-only import alias か判定する。"""
    local = local_name.strip()
    return local.startswith("__") and local != ""


def _sh_register_import_symbol(
    import_symbols: dict[str, dict[str, str]],
    local_name: str,
    module_id: str,
    export_name: str,
    *,
    make_import_symbol_binding: Callable[[str, str], dict[str, str]],
) -> None:
    """from-import で導入されたシンボル解決情報を式パーサ共有コンテキストへ反映する。"""
    local = local_name.strip()
    module = module_id.strip()
    export = export_name.strip()
    if local == "" or module == "" or export == "":
        return
    import_symbols[local] = make_import_symbol_binding(module, export)


def _sh_register_import_module(import_modules: dict[str, str], local_name: str, module_id: str) -> None:
    """import で導入されたモジュール別名を式パーサ共有コンテキストへ反映する。"""
    local = local_name.strip()
    module = module_id.strip()
    if local == "" or module == "":
        return
    import_modules[local] = module
