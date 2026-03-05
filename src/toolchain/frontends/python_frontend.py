"""Python-input frontend bootstrap wrappers.

During 3-layer migration this module delegates to ``toolchain.frontends.transpile_cli``
and provides a stable future home under ``toolchain.frontends``.
"""

from __future__ import annotations

from typing import Any
from typing import Iterable

from toolchain.frontends.transpile_cli import add_common_transpile_args as _add_common_transpile_args
from toolchain.frontends.transpile_cli import load_east3_document as _load_east3_document
from toolchain.frontends.transpile_cli import normalize_common_transpile_args as _normalize_common_transpile_args
from pytra.std import argparse
from pytra.std.pathlib import Path


def add_common_transpile_args(
    parser: argparse.ArgumentParser,
    *,
    enable_negative_index_mode: bool = False,
    enable_object_dispatch_mode: bool = False,
    parser_backends: Iterable[str] | None = None,
) -> None:
    """Add common transpile CLI args for Python frontend inputs."""
    _add_common_transpile_args(
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
    """Fill default values for shared transpile CLI args."""
    return _normalize_common_transpile_args(
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
    """Load and normalize input into optimized EAST3 document."""
    return _load_east3_document(
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
