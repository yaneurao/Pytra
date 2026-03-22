"""Linked-program loader."""

from __future__ import annotations

import os
from pytra.std import json
from pytra.std.pathlib import Path
from typing import Any

from toolchain.json_adapters import coerce_json_object_dict
from toolchain.link.link_manifest_io import load_link_input_doc
from toolchain.link.program_model import LinkedProgram
from toolchain.link.program_model import LinkedProgramModule
from toolchain.link.program_model import LINK_INPUT_SCHEMA
from toolchain.link.program_validator import validate_raw_east3_doc

_RUNTIME_EAST_ROOT = Path(__file__).resolve().parents[2] / "runtime" / "east"

_RUNTIME_MODULE_BUCKETS: dict[str, str] = {
    "pytra.built_in.": "built_in",
    "pytra.std.": "std",
    "pytra.utils.": "utils",
}


def _resolve_runtime_east_path(module_id: str) -> Path | None:
    """Resolve a runtime module ID to its .east file path, or None."""
    for prefix, bucket in _RUNTIME_MODULE_BUCKETS.items():
        if module_id.startswith(prefix):
            name = module_id[len(prefix):]
            east_path = _RUNTIME_EAST_ROOT / bucket / (name + ".east")
            if east_path.exists():
                return east_path
    # Fallback: bare module name → try pytra.std.X
    # e.g. "pathlib" → std/pathlib.east, "json" → std/json.east
    bare_path = _RUNTIME_EAST_ROOT / "std" / (module_id + ".east")
    if bare_path.exists():
        return bare_path
    return None


def add_runtime_east_to_module_map(
    module_map: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Scan module_map for runtime imports and add their .east files.

    Iterates until no new runtime dependencies are found (transitive closure).
    """
    result = dict(module_map)
    seen_paths: set[str] = set(result.keys())

    changed = True
    while changed:
        changed = False
        new_deps: list[tuple[str, Path]] = []
        for east_doc in list(result.values()):
            if not isinstance(east_doc, dict):
                continue
            meta = east_doc.get("meta")
            if not isinstance(meta, dict):
                continue
            bindings = meta.get("import_bindings")
            if isinstance(bindings, list):
                for binding in bindings:
                    if not isinstance(binding, dict):
                        continue
                    mod_id = binding.get("module_id")
                    if isinstance(mod_id, str) and mod_id != "":
                        east_path = _resolve_runtime_east_path(mod_id)
                        if east_path is not None and str(east_path) not in seen_paths:
                            new_deps.append((str(east_path), east_path))
            # Also scan body for Import/ImportFrom
            body = east_doc.get("body")
            if isinstance(body, list):
                for stmt in body:
                    if not isinstance(stmt, dict):
                        continue
                    kind = stmt.get("kind")
                    if kind == "ImportFrom":
                        mod = stmt.get("module")
                        if isinstance(mod, str) and mod != "":
                            east_path = _resolve_runtime_east_path(mod)
                            if east_path is not None and str(east_path) not in seen_paths:
                                new_deps.append((str(east_path), east_path))
                            # Also try {module}.{name} for sub-module imports
                            # e.g. from pytra.utils import png → pytra.utils.png
                            names = stmt.get("names")
                            if isinstance(names, list):
                                for ent in names:
                                    if isinstance(ent, dict):
                                        sym = ent.get("name")
                                        if isinstance(sym, str) and sym != "":
                                            sub_mod = mod + "." + sym
                                            sub_path = _resolve_runtime_east_path(sub_mod)
                                            if sub_path is not None and str(sub_path) not in seen_paths:
                                                new_deps.append((str(sub_path), sub_path))
                    elif kind == "Import":
                        names = stmt.get("names")
                        if isinstance(names, list):
                            for ent in names:
                                if isinstance(ent, dict):
                                    name = ent.get("name")
                                    if isinstance(name, str):
                                        east_path = _resolve_runtime_east_path(name)
                                        if east_path is not None and str(east_path) not in seen_paths:
                                            new_deps.append((str(east_path), east_path))
            # Detect implicit format_value dependency from f-string format_spec
            _scan_format_spec_dep(east_doc, seen_paths, new_deps)

        for path_str, east_path in new_deps:
            if path_str in seen_paths:
                continue
            seen_paths.add(path_str)
            try:
                east_doc = _load_raw_east3(east_path)
                result[path_str] = east_doc
                changed = True
            except Exception:
                pass
    return result


def _has_format_spec(node: object) -> bool:
    """EAST ノードツリーに format_spec を持つ FormattedValue が含まれるか再帰検査する。"""
    if isinstance(node, dict):
        if node.get("kind") == "FormattedValue":
            fs = node.get("format_spec")
            if isinstance(fs, str) and fs != "":
                return True
        for v in node.values():
            if _has_format_spec(v):
                return True
    elif isinstance(node, list):
        for item in node:
            if _has_format_spec(item):
                return True
    return False


def _scan_format_spec_dep(
    east_doc: dict[str, object],
    seen_paths: set[str],
    new_deps: list[tuple[str, Path]],
) -> None:
    """f-string format_spec が存在すれば pytra.built_in.format_value を暗黙依存に追加する。"""
    if _has_format_spec(east_doc):
        ep = _resolve_runtime_east_path("pytra.built_in.format_value")
        if ep is not None and str(ep) not in seen_paths:
            new_deps.append((str(ep), ep))


def _load_raw_east3(path: Path) -> dict[str, object]:
    obj = json.loads_obj(path.read_text(encoding="utf-8"))
    if obj is None:
        raise RuntimeError("raw EAST3 root must be an object: " + str(path))
    return coerce_json_object_dict(obj, label="raw EAST3")


def _module_id_from_east_or_path(east_doc: dict[str, object], source_path: Path) -> str:
    meta_any = east_doc.get("meta", {})
    if isinstance(meta_any, dict):
        module_id_any = meta_any.get("module_id")
        if isinstance(module_id_any, str) and module_id_any.strip() != "":
            return module_id_any.strip()

    # For runtime .east files, derive module_id from path relative to _RUNTIME_EAST_ROOT.
    # e.g. src/runtime/east/std/time.east → pytra.std.time
    resolved = source_path.resolve()
    east_root = _RUNTIME_EAST_ROOT.resolve()
    try:
        rel = resolved.relative_to(east_root)
        rel_str = str(rel).replace("\\", "/")
        # Strip .east extension
        if rel_str.endswith(".east"):
            rel_str = rel_str[:-5]
        # Convert path separators to dots: std/time → std.time
        module_id = "pytra." + rel_str.replace("/", ".")
        if module_id != "":
            return module_id
    except ValueError:
        pass

    file_name = source_path.name
    for suffix in (".east3.json", ".json", ".py"):
        if file_name.endswith(suffix):
            file_name = file_name[: -len(suffix)]
            break
    file_name = file_name.replace("-", "_").strip()
    if file_name == "":
        raise RuntimeError("failed to infer module_id from path: " + str(source_path))
    return file_name


def build_linked_program_from_module_map(
    entry_path: Path,
    module_east_map: dict[str, dict[str, Any]],
    *,
    target: str,
    dispatch_mode: str,
    options: dict[str, object] | None = None,
) -> LinkedProgram:
    if len(module_east_map) == 0:
        raise RuntimeError("module_east_map must not be empty")

    entry_resolved = str(entry_path.resolve())
    modules: list[LinkedProgramModule] = []
    seen_module_ids: set[str] = set()
    entry_modules: list[str] = []
    module_items: list[tuple[Path, dict[str, object]]] = []
    for path_txt, east_any in module_east_map.items():
        if not isinstance(path_txt, str) or path_txt.strip() == "":
            raise RuntimeError("module_east_map keys must be non-empty paths")
        module_path = Path(path_txt).resolve()
        east_doc = coerce_json_object_dict(east_any, label="module_east_map[" + path_txt + "]")
        module_items.append((module_path, east_doc))

    for module_path, raw_east_doc in sorted(module_items, key=lambda item: str(item[0])):
        module_id = _module_id_from_east_or_path(raw_east_doc, module_path)
        if module_id in seen_module_ids:
            raise RuntimeError("duplicate module_id in module_east_map: " + module_id)
        seen_module_ids.add(module_id)
        east_doc = validate_raw_east3_doc(
            raw_east_doc,
            expected_dispatch_mode=dispatch_mode,
            module_id=module_id,
        )
        is_entry = str(module_path) == entry_resolved
        if is_entry:
            entry_modules.append(module_id)
        modules.append(
            LinkedProgramModule(
                module_id=module_id,
                source_path=str(module_path),
                is_entry=is_entry,
                east_doc=east_doc,
            )
        )

    if len(entry_modules) == 0:
        raise RuntimeError("entry module not found in module_east_map: " + entry_resolved)

    return LinkedProgram(
        schema=LINK_INPUT_SCHEMA,
        manifest_path=None,
        target=target,
        dispatch_mode=dispatch_mode,
        entry_modules=tuple(sorted(entry_modules)),
        modules=tuple(sorted(modules, key=lambda item: item.module_id)),
        options=dict(options) if isinstance(options, dict) else {},
    )


def load_linked_program(manifest_path: Path) -> LinkedProgram:
    manifest_doc = load_link_input_doc(manifest_path)
    manifest_dir = manifest_path.parent
    dispatch_mode = str(manifest_doc["dispatch_mode"])

    modules: list[LinkedProgramModule] = []
    for item_any in manifest_doc["modules"]:
        item = item_any
        module_path = manifest_dir / item.path
        raw_east_doc = _load_raw_east3(module_path)
        east_doc = validate_raw_east3_doc(
            raw_east_doc,
            expected_dispatch_mode=dispatch_mode,
            module_id=item.module_id,
        )
        modules.append(
            LinkedProgramModule(
                module_id=item.module_id,
                source_path=item.source_path,
                is_entry=item.is_entry,
                east_doc=east_doc,
                artifact_path=module_path.resolve(),
            )
        )

    return LinkedProgram(
        schema=str(manifest_doc["schema"]),
        manifest_path=manifest_path.resolve(),
        target=str(manifest_doc["target"]),
        dispatch_mode=dispatch_mode,
        entry_modules=tuple(manifest_doc["entry_modules"]),
        modules=tuple(modules),
        options=dict(manifest_doc["options"]),
    )
