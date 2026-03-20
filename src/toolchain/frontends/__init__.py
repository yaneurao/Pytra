"""Frontend bootstrap namespace (`src/toolchain/frontends`).

Keep package import side effects minimal to avoid cycles with
``toolchain.compiler.transpile_cli`` during staged migration.
"""

from __future__ import annotations

from typing import Any

from pytra.std.pathlib import Path


def add_common_transpile_args(
    parser: Any,
    *,
    enable_negative_index_mode: bool = False,
    enable_object_dispatch_mode: bool = False,
    parser_backends: Any = None,
) -> None:
    from .python_frontend import add_common_transpile_args as _impl

    _impl(
        parser,
        enable_negative_index_mode=enable_negative_index_mode,
        enable_object_dispatch_mode=enable_object_dispatch_mode,
        parser_backends=parser_backends,
    )


def normalize_common_transpile_args(
    args: Any,
    *,
    default_negative_index_mode: str | None = None,
    default_object_dispatch_mode: str | None = None,
    default_parser_backend: str | None = None,
) -> Any:
    from .python_frontend import normalize_common_transpile_args as _impl

    return _impl(
        args,
        default_negative_index_mode=default_negative_index_mode,
        default_object_dispatch_mode=default_object_dispatch_mode,
        default_parser_backend=default_parser_backend,
    )


def load_east3_document(
    input_path: Path,
    *,
    parser_backend: str = "self_hosted",
    object_dispatch_mode: str = "",
    east3_opt_level: str | int | object = 1,
    east3_opt_pass: str = "",
    dump_east3_before_opt: str = "",
    dump_east3_after_opt: str = "",
    dump_east3_opt_trace: str = "",
    target_lang: str = "",
) -> dict[str, object]:
    from .python_frontend import load_east3_document as _impl

    return _impl(
        input_path,
        parser_backend=parser_backend,
        object_dispatch_mode=object_dispatch_mode,
        east3_opt_level=east3_opt_level,
        east3_opt_pass=east3_opt_pass,
        dump_east3_before_opt=dump_east3_before_opt,
        dump_east3_after_opt=dump_east3_after_opt,
        dump_east3_opt_trace=dump_east3_opt_trace,
        target_lang=target_lang,
    )


def load_east3_document_typed(
    input_path: Path,
    *,
    parser_backend: str = "self_hosted",
    object_dispatch_mode: str = "",
    east3_opt_level: str | int | object = 1,
    east3_opt_pass: str = "",
    dump_east3_before_opt: str = "",
    dump_east3_after_opt: str = "",
    dump_east3_opt_trace: str = "",
    target_lang: str = "",
) -> Any:
    from .python_frontend import load_east3_document_typed as _impl

    return _impl(
        input_path,
        parser_backend=parser_backend,
        object_dispatch_mode=object_dispatch_mode,
        east3_opt_level=east3_opt_level,
        east3_opt_pass=east3_opt_pass,
        dump_east3_before_opt=dump_east3_before_opt,
        dump_east3_after_opt=dump_east3_after_opt,
        dump_east3_opt_trace=dump_east3_opt_trace,
        target_lang=target_lang,
    )


def build_module_east_map(
    entry_path: Path,
    load_east_fn: object,
    parser_backend: str = "self_hosted",
    east_stage: str = "2",
    object_dispatch_mode: str = "",
    runtime_std_source_root: Path = Path("src/pytra/std"),
    runtime_utils_source_root: Path = Path("src/pytra/utils"),
) -> dict[str, dict[str, object]]:
    from .python_frontend import build_module_east_map as _impl

    return _impl(
        entry_path,
        load_east_fn,
        parser_backend=parser_backend,
        east_stage=east_stage,
        object_dispatch_mode=object_dispatch_mode,
        runtime_std_source_root=runtime_std_source_root,
        runtime_utils_source_root=runtime_utils_source_root,
    )


__all__ = [
    "add_common_transpile_args",
    "normalize_common_transpile_args",
    "load_east3_document",
    "load_east3_document_typed",
    "build_module_east_map",
]
