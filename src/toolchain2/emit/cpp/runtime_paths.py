"""Shared runtime path helpers for toolchain2 C++ emit/build."""

from __future__ import annotations

from pytra.std.json import JsonVal
from pytra.std.pathlib import Path

from toolchain2.link.dependencies import is_type_only_dependency_module_id
from toolchain2.link.runtime_discovery import is_runtime_internal_helper_module
from toolchain2.link.runtime_discovery import is_runtime_namespace_module
from toolchain2.link.runtime_discovery import resolve_runtime_module_rel_tail


_RUNTIME_CPP_ROOT = Path(__file__).resolve().parents[3] / "runtime" / "cpp"


def runtime_rel_tail_for_module(module_id: str) -> str:
    return resolve_runtime_module_rel_tail(module_id)


def cpp_include_for_module(module_id: str) -> str:
    if is_runtime_namespace_module(module_id) or is_type_only_dependency_module_id(module_id):
        return ""
    rel = resolve_runtime_module_rel_tail(module_id)
    if rel != "":
        return rel + ".h"
    if is_runtime_internal_helper_module(module_id):
        return ""
    if module_id != "":
        return module_id.replace(".", "/") + ".h"
    return ""


def collect_cpp_dependency_module_ids(module_id: str, meta: dict[str, JsonVal]) -> list[str]:
    """Collect C++ include dependencies from linker/runtime metadata.

    Prefer link-stage `resolved_dependencies_v1` when present. Runtime EAST
    fixtures often lack it, so fall back to `import_bindings` while filtering
    host-only Python modules like `os.path`.
    """
    linked = meta.get("linked_program_v1")
    dep_ids: list[str] = []
    if isinstance(linked, dict):
        deps = linked.get("resolved_dependencies_v1")
        if isinstance(deps, list):
            for dep in deps:
                if isinstance(dep, str) and dep != "":
                    dep_ids.append(dep)
    bindings = meta.get("import_bindings")
    if isinstance(bindings, list):
        for binding in bindings:
            dep_id = _binding_cpp_dependency_module_id(binding)
            if dep_id != "":
                dep_ids.append(dep_id)
    import_resolution = meta.get("import_resolution")
    if isinstance(import_resolution, dict):
        bindings = import_resolution.get("bindings")
        if isinstance(bindings, list):
            for binding in bindings:
                dep_id = _binding_cpp_dependency_module_id(binding)
                if dep_id != "":
                    dep_ids.append(dep_id)

    out: list[str] = []
    seen: set[str] = set()
    for dep_id in dep_ids:
        if dep_id == "" or dep_id == module_id or dep_id in seen:
            continue
        if cpp_include_for_module(dep_id) == "":
            continue
        seen.add(dep_id)
        out.append(dep_id)
    return out


def _binding_cpp_dependency_module_id(binding: JsonVal) -> str:
    if not isinstance(binding, dict):
        return ""
    runtime_module_id = binding.get("runtime_module_id")
    runtime_group = binding.get("runtime_group")
    module_id = binding.get("module_id")
    host_only = binding.get("host_only") is True

    if isinstance(runtime_module_id, str) and runtime_module_id != "":
        if host_only:
            return ""
        if isinstance(runtime_group, str) and runtime_group != "":
            return runtime_module_id
        if not host_only:
            return runtime_module_id
        return ""

    if isinstance(module_id, str) and module_id != "":
        if module_id.startswith("pytra.") or not host_only:
            return module_id
    return ""


def native_companion_header_path(module_id: str) -> Path:
    rel = runtime_rel_tail_for_module(module_id)
    if rel == "":
        return Path("")
    p = _RUNTIME_CPP_ROOT / (rel + ".h")
    return p if p.exists() else Path("")


def native_companion_source_path(module_id: str) -> Path:
    rel = runtime_rel_tail_for_module(module_id)
    if rel == "":
        return Path("")
    p = _RUNTIME_CPP_ROOT / (rel + ".cpp")
    return p if p.exists() else Path("")
