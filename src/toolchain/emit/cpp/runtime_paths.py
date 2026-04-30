"""Shared runtime path helpers for toolchain2 C++ emit/build."""

from __future__ import annotations

import pytra.std.json as json
from pytra.std.json import JsonVal
from pytra.std.pathlib import Path

from toolchain.link.dependencies import is_type_only_dependency_module_id
from toolchain.link.runtime_discovery import is_runtime_internal_helper_module
from toolchain.link.runtime_discovery import is_runtime_namespace_module
from toolchain.link.runtime_discovery import resolve_runtime_module_rel_tail


def runtime_rel_tail_for_module(module_id: str) -> str:
    return resolve_runtime_module_rel_tail(module_id) + ""


def cpp_include_for_module(module_id: str) -> str:
    cpp_skip_module_ids: set[str] = {
        "abc",
        "readonly",
        "str",
    }
    if module_id in cpp_skip_module_ids:
        return ""
    if is_runtime_namespace_module(module_id) or is_type_only_dependency_module_id(module_id):
        return ""
    rel = runtime_rel_tail_for_module(module_id)
    if rel != "":
        return rel + ".h"
    if is_runtime_internal_helper_module(module_id):
        return ""
    if module_id != "":
        return cpp_user_header_for_module(module_id)
    return ""


def cpp_user_header_for_module(module_id: str) -> str:
    if module_id == "":
        return ""
    return "__pytra_user/" + module_id.replace(".", "/") + ".h"


def collect_cpp_dependency_module_ids(module_id: str, meta: dict[str, JsonVal]) -> list[str]:
    """Collect C++ include dependencies from linker/runtime metadata.

    Prefer link-stage `resolved_dependencies_v1` when present. Runtime EAST
    fixtures often lack it, so fall back to `import_bindings` while filtering
    host-only Python modules like `os.path`.
    """
    dep_ids: list[str] = []
    linked = _rp_dict(meta, "linked_program_v1")
    deps = _rp_list(linked, "resolved_dependencies_v1")
    for dep in deps:
        dep_text = _rp_json_str_value(dep)
        if dep_text != "":
            dep_ids.append(dep_text)
    bindings = _rp_list(meta, "import_bindings")
    for binding in bindings:
        dep_id = _rp_binding_cpp_dependency_module_id(binding)
        if dep_id != "":
            dep_ids.append(dep_id)
    import_resolution = _rp_dict(meta, "import_resolution")
    resolution_bindings = _rp_list(import_resolution, "bindings")
    for binding in resolution_bindings:
        dep_id = _rp_binding_cpp_dependency_module_id(binding)
        if dep_id != "":
            dep_ids.append(dep_id)

    out: list[str] = []
    seen: set[str] = set()
    for dep_id in dep_ids:
        dep_text = str(dep_id)
        if dep_id == "" or dep_text == "None" or dep_text == "undefined" or dep_id == module_id or dep_id in seen:
            continue
        include_path = cpp_include_for_module(dep_id)
        include_text = str(include_path)
        if include_path == "" or include_text == "None" or include_text == "undefined":
            continue
        seen.add(dep_id)
        out.append(dep_id)
    return out


def _rp_binding_cpp_dependency_module_id(binding: JsonVal) -> str:
    binding_obj = json.JsonValue(binding).as_obj()
    if binding_obj is None:
        return ""
    binding_dict = binding_obj.raw
    module_id = _rp_str(binding_dict, "module_id")
    export_name = _rp_str(binding_dict, "export_name")
    _ = export_name
    runtime_module_id = _rp_str(binding_dict, "runtime_module_id")
    runtime_group = _rp_str(binding_dict, "runtime_group")
    host_only = _rp_bool(binding_dict, "host_only")

    if runtime_module_id != "":
        if host_only:
            return ""
        if runtime_group != "":
            return runtime_module_id
        if not host_only:
            return runtime_module_id
        return ""

    if module_id != "":
        if module_id.startswith("pytra.") or not host_only:
            return module_id
    return ""


def native_companion_header_path(module_id: str) -> Path:
    rel = runtime_rel_tail_for_module(module_id)
    if rel == "":
        return Path("")
    p = Path("src").joinpath("runtime").joinpath("cpp").joinpath(rel + ".h")
    return p if p.exists() else Path("")


def native_companion_source_path(module_id: str) -> Path:
    rel = runtime_rel_tail_for_module(module_id)
    if rel == "":
        return Path("")
    p = Path("src").joinpath("runtime").joinpath("cpp").joinpath(rel + ".cpp")
    return p if p.exists() else Path("")


def _rp_str(node: dict[str, JsonVal], key: str) -> str:
    raw = json.JsonValue(node.get(key)).as_str()
    if raw is not None:
        return raw
    return ""


def _rp_bool(node: dict[str, JsonVal], key: str) -> bool:
    raw = json.JsonValue(node.get(key)).as_bool()
    if raw is not None:
        return raw
    return False


def _rp_json_str_value(value: JsonVal) -> str:
    raw = json.JsonValue(value).as_str()
    if raw is not None:
        return raw
    return ""


def _rp_list(node: dict[str, JsonVal], key: str) -> list[JsonVal]:
    raw = json.JsonValue(node.get(key)).as_arr()
    if raw is not None:
        return raw.raw
    return []


def _rp_dict(node: dict[str, JsonVal], key: str) -> dict[str, JsonVal]:
    raw = json.JsonValue(node.get(key)).as_obj()
    if raw is not None:
        return raw.raw
    return {}
