from __future__ import annotations

from pytra.std.pathlib import Path
from pytra.std.typing import Any

from hooks.cpp.runtime_emit.cpp_runtime_emit import (
    RUNTIME_BUILT_IN_SOURCE_ROOT,
    RUNTIME_COMPILER_SOURCE_ROOT,
    RUNTIME_CPP_COMPAT_ROOT,
    RUNTIME_CPP_GEN_ROOT,
    RUNTIME_STD_SOURCE_ROOT,
    RUNTIME_UTILS_SOURCE_ROOT,
    join_runtime_path as _join_runtime_path_impl,
    module_tail_to_cpp_header_path as _module_tail_to_cpp_header_path_impl,
    module_name_to_cpp_include as _module_name_to_cpp_include_impl,
    prepend_generated_cpp_banner as _prepend_generated_cpp_banner_impl,
    runtime_cpp_header_exists_for_module as _runtime_cpp_header_exists_for_module_impl,
    runtime_module_tail_from_source_path as _runtime_module_tail_from_source_path_impl,
    is_runtime_emit_input_path as _is_runtime_emit_input_path_impl,
    runtime_output_rel_tail as _runtime_output_rel_tail_impl,
    runtime_namespace_for_tail as _runtime_namespace_for_tail_impl,
)

_join_runtime_path = _join_runtime_path_impl
_module_tail_to_cpp_header_path = _module_tail_to_cpp_header_path_impl
_module_name_to_cpp_include = _module_name_to_cpp_include_impl
_prepend_generated_cpp_banner = _prepend_generated_cpp_banner_impl
_runtime_cpp_header_exists_for_module = _runtime_cpp_header_exists_for_module_impl
_runtime_module_tail_from_source_path = _runtime_module_tail_from_source_path_impl
_is_runtime_emit_input_path = _is_runtime_emit_input_path_impl
_runtime_output_rel_tail = _runtime_output_rel_tail_impl
_runtime_namespace_for_tail = _runtime_namespace_for_tail_impl

__all__ = [
    "RUNTIME_CPP_COMPAT_ROOT",
    "RUNTIME_CPP_GEN_ROOT",
    "RUNTIME_STD_SOURCE_ROOT",
    "RUNTIME_UTILS_SOURCE_ROOT",
    "RUNTIME_COMPILER_SOURCE_ROOT",
    "RUNTIME_BUILT_IN_SOURCE_ROOT",
    "join_runtime_path",
    "module_tail_to_cpp_header_path",
    "module_name_to_cpp_include",
    "prepend_generated_cpp_banner",
    "runtime_cpp_header_exists_for_module",
    "runtime_module_tail_from_source_path",
    "is_runtime_emit_input_path",
    "runtime_output_rel_tail",
    "runtime_namespace_for_tail",
    "_join_runtime_path",
    "_module_tail_to_cpp_header_path",
    "_module_name_to_cpp_include",
    "_prepend_generated_cpp_banner",
    "_runtime_cpp_header_exists_for_module",
    "_runtime_module_tail_from_source_path",
    "_is_runtime_emit_input_path",
    "_runtime_output_rel_tail",
    "_runtime_namespace_for_tail",
]


def module_tail_to_cpp_header_path(*args: Any, **kwargs: Any) -> str:
    """Delegate to concrete runtime emit implementation."""
    return _module_tail_to_cpp_header_path_impl(*args, **kwargs)  # type: ignore[no-any-return]


def join_runtime_path(*args: Any, **kwargs: Any) -> Path:
    """Delegate to concrete runtime emit implementation."""
    return _join_runtime_path_impl(*args, **kwargs)  # type: ignore[no-any-return]


def module_name_to_cpp_include(*args: Any, **kwargs: Any) -> str:
    """Delegate to concrete runtime emit implementation."""
    return _module_name_to_cpp_include_impl(*args, **kwargs)  # type: ignore[no-any-return]


def prepend_generated_cpp_banner(*args: Any, **kwargs: Any) -> str:
    """Delegate to concrete runtime emit implementation."""
    return _prepend_generated_cpp_banner_impl(*args, **kwargs)  # type: ignore[no-any-return]


def runtime_cpp_header_exists_for_module(*args: Any, **kwargs: Any) -> bool:
    """Delegate to concrete runtime emit implementation."""
    return _runtime_cpp_header_exists_for_module_impl(*args, **kwargs)  # type: ignore[no-any-return]


def runtime_module_tail_from_source_path(*args: Any, **kwargs: Any) -> str:
    """Delegate to concrete runtime emit implementation."""
    return _runtime_module_tail_from_source_path_impl(*args, **kwargs)  # type: ignore[no-any-return]


def is_runtime_emit_input_path(*args: Any, **kwargs: Any) -> bool:
    """Delegate to concrete runtime emit implementation."""
    return _is_runtime_emit_input_path_impl(*args, **kwargs)  # type: ignore[no-any-return]


def runtime_output_rel_tail(*args: Any, **kwargs: Any) -> str:
    """Delegate to concrete runtime emit implementation."""
    return _runtime_output_rel_tail_impl(*args, **kwargs)  # type: ignore[no-any-return]


def runtime_namespace_for_tail(*args: Any, **kwargs: Any) -> str:
    """Delegate to concrete runtime emit implementation."""
    return _runtime_namespace_for_tail_impl(*args, **kwargs)  # type: ignore[no-any-return]
