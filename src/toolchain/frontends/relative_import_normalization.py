"""Relative import normalization helpers for frontend and import-graph lanes."""

from __future__ import annotations

from pytra.std.pathlib import Path


def _path_key_for_graph(path_obj: Path) -> str:
    """Return the graph-internal string key for a path."""
    return str(path_obj)


def _path_parent_text(path_obj: Path) -> str:
    """Return the parent directory text for a path."""
    path_txt = str(path_obj)
    if path_txt == "":
        return "."
    last_sep = -1
    for i, ch in enumerate(path_txt):
        if ch == "/" or ch == "\\":
            last_sep = i
    if last_sep <= 0:
        return "."
    return path_txt[:last_sep]


def _module_name_from_path_for_graph(root: Path, module_path: Path) -> str:
    """Resolve a fallback module id from a file path."""
    root_txt = str(root)
    path_txt = str(module_path)
    in_root = False
    if root_txt != "" and not root_txt.endswith("/"):
        root_txt += "/"
    rel = path_txt
    if root_txt != "" and path_txt.startswith(root_txt):
        rel = path_txt[len(root_txt) :]
        in_root = True
    if rel.endswith(".py"):
        rel = rel[:-3]
    rel = rel.replace("/", ".")
    if rel.endswith(".__init__"):
        rel = rel[:-9]
    if not in_root:
        stem = module_path.stem
        stem = module_path.parent.name if stem == "__init__" else stem
        rel = stem
    return rel


def _dict_any_get_str(src: dict[str, object], key: str, default_value: str = "") -> str:
    """Return a string value from a generic dict."""
    if key in src:
        value = src[key]
        if isinstance(value, str):
            return str(value)
    return default_value


def relative_module_level(raw_name: str) -> int:
    """Return the number of leading dots in a relative import."""
    level = 0
    for ch in raw_name:
        if ch != ".":
            break
        level += 1
    return level


def relative_module_tail(raw_name: str) -> str:
    """Return a relative import without its leading dots."""
    return raw_name[relative_module_level(raw_name) :]


def _path_is_under_root_for_graph(path_obj: Path, root: Path) -> bool:
    """Return True when a path lives under the entry root."""
    path_txt = _path_key_for_graph(path_obj)
    root_txt = _path_key_for_graph(root)
    if path_txt == root_txt:
        return True
    root_prefix = root_txt if root_txt.endswith("/") else root_txt + "/"
    return path_txt.startswith(root_prefix)


def resolve_import_graph_entry_root(entry_path: Path) -> Path:
    """Infer the package root from the `__init__.py` chain above the entry file."""
    cur_dir = Path(_path_parent_text(entry_path))
    while (cur_dir / "__init__.py").exists():
        parent_txt = _path_parent_text(cur_dir)
        cur_txt = _path_key_for_graph(cur_dir)
        if parent_txt == cur_txt:
            break
        parent_dir = Path(parent_txt if parent_txt != "" else ".")
        if not (parent_dir / "__init__.py").exists():
            break
        cur_dir = parent_dir
    return cur_dir


def resolve_relative_module_anchor_dir(raw_name: str, entry_root: Path, importer_path: Path) -> dict[str, str]:
    """Resolve the anchor directory for a relative import under the entry root."""
    level = relative_module_level(raw_name)
    tail = relative_module_tail(raw_name)
    cur_dir = Path(_path_parent_text(importer_path))
    root_key = _path_key_for_graph(entry_root)
    for _ in range(level - 1):
        if _path_key_for_graph(cur_dir) == root_key:
            return {"status": "relative", "anchor": "", "tail": tail}
        parent_dir = _path_parent_text(cur_dir)
        if parent_dir == _path_key_for_graph(cur_dir):
            return {"status": "relative", "anchor": "", "tail": tail}
        cur_dir = Path(parent_dir if parent_dir != "" else ".")
    if not _path_is_under_root_for_graph(cur_dir, entry_root):
        return {"status": "relative", "anchor": "", "tail": tail}
    return {
        "status": "anchor",
        "anchor": _path_key_for_graph(cur_dir),
        "tail": tail,
    }


def relative_module_id_from_anchor(anchor_dir: Path, tail: str, entry_root: Path) -> str:
    """Build a normalized absolute module id from an anchor dir and module tail."""
    anchor_txt = _path_key_for_graph(anchor_dir)
    root_txt = _path_key_for_graph(entry_root)
    rel = ""
    if anchor_txt == root_txt:
        rel = ""
    else:
        root_prefix = root_txt if root_txt.endswith("/") else root_txt + "/"
        if not anchor_txt.startswith(root_prefix):
            return ""
        rel = anchor_txt[len(root_prefix) :]
    parts: list[str] = []
    for part in rel.split("/"):
        if part != "":
            parts.append(part)
    if tail != "":
        for part in tail.split("."):
            if part != "":
                parts.append(part)
    out = ""
    for part in parts:
        out = part if out == "" else out + "." + part
    return out


def resolve_relative_module_name_for_graph(
    raw_name: str,
    entry_root: Path,
    importer_path: Path,
) -> dict[str, str]:
    """Normalize a relative import to an absolute module/path under the entry root."""
    anchor_state = resolve_relative_module_anchor_dir(raw_name, entry_root, importer_path)
    if _dict_any_get_str(anchor_state, "status") != "anchor":
        return {"status": "relative", "module_id": raw_name, "path": ""}
    anchor_dir = Path(_dict_any_get_str(anchor_state, "anchor"))
    tail = _dict_any_get_str(anchor_state, "tail")
    module_id = relative_module_id_from_anchor(anchor_dir, tail, entry_root)
    if module_id == "":
        return {"status": "relative", "module_id": raw_name, "path": ""}
    if tail == "":
        init_path = anchor_dir / "__init__.py"
        if init_path.exists():
            return {
                "status": "user",
                "module_id": _module_name_from_path_for_graph(entry_root, init_path),
                "path": _path_key_for_graph(init_path),
            }
        return {"status": "missing", "module_id": module_id, "path": ""}
    rel = tail.replace(".", "/")
    parts = tail.split(".")
    leaf = parts[len(parts) - 1] if len(parts) > 0 else ""
    cand_init = anchor_dir / rel / "__init__.py"
    cand_named = anchor_dir / rel / (leaf + ".py") if leaf != "" else Path("")
    cand_flat = anchor_dir / (rel + ".py")
    candidates: list[Path] = [cand_init]
    if str(cand_named) != "." and _path_key_for_graph(cand_named) != "":
        candidates.append(cand_named)
    candidates.append(cand_flat)
    for dep_file in candidates:
        if dep_file.exists():
            return {
                "status": "user",
                "module_id": _module_name_from_path_for_graph(entry_root, dep_file),
                "path": _path_key_for_graph(dep_file),
            }
    return {"status": "missing", "module_id": module_id, "path": ""}


def normalize_relative_module_id(
    raw_name: str,
    entry_root: Path,
    importer_path: Path,
) -> str:
    """Convert relative module text to a normalized absolute module id."""
    if not raw_name.startswith("."):
        return raw_name
    resolved = resolve_relative_module_name_for_graph(raw_name, entry_root, importer_path)
    module_id = _dict_any_get_str(resolved, "module_id")
    return module_id if module_id != "" else raw_name


def rewrite_relative_imports_in_east_doc(
    east_doc: dict[str, object],
    *,
    entry_root: Path,
    importer_path: Path,
) -> dict[str, object]:
    """Rewrite relative import metadata/body inside one EAST module document."""
    body_any = east_doc.get("body")
    if isinstance(body_any, list):
        for stmt_any in body_any:
            if not isinstance(stmt_any, dict):
                continue
            kind_any = stmt_any.get("kind")
            if not isinstance(kind_any, str) or kind_any != "ImportFrom":
                continue
            mod_any = stmt_any.get("module")
            if isinstance(mod_any, str) and mod_any.startswith("."):
                stmt_any["module"] = normalize_relative_module_id(mod_any, entry_root, importer_path)
    meta_any = east_doc.get("meta")
    if isinstance(meta_any, dict):
        import_bindings_any = meta_any.get("import_bindings")
        if isinstance(import_bindings_any, list):
            for binding_any in import_bindings_any:
                if not isinstance(binding_any, dict):
                    continue
                mod_any = binding_any.get("module_id")
                if isinstance(mod_any, str) and mod_any.startswith("."):
                    binding_any["module_id"] = normalize_relative_module_id(mod_any, entry_root, importer_path)
        import_symbols_any = meta_any.get("import_symbols")
        if isinstance(import_symbols_any, dict):
            for local_name_any, binding_any in import_symbols_any.items():
                if not isinstance(local_name_any, str) or not isinstance(binding_any, dict):
                    continue
                mod_any = binding_any.get("module")
                if isinstance(mod_any, str) and mod_any.startswith("."):
                    binding_any["module"] = normalize_relative_module_id(mod_any, entry_root, importer_path)
        qualified_refs_any = meta_any.get("qualified_symbol_refs")
        if isinstance(qualified_refs_any, list):
            for ref_any in qualified_refs_any:
                if not isinstance(ref_any, dict):
                    continue
                mod_any = ref_any.get("module_id")
                if isinstance(mod_any, str) and mod_any.startswith("."):
                    ref_any["module_id"] = normalize_relative_module_id(mod_any, entry_root, importer_path)
        import_resolution_any = meta_any.get("import_resolution")
        if isinstance(import_resolution_any, dict):
            bindings_any = import_resolution_any.get("bindings")
            if isinstance(bindings_any, list):
                for binding_any in bindings_any:
                    if not isinstance(binding_any, dict):
                        continue
                    for key in ("module_id", "source_module_id"):
                        mod_any = binding_any.get(key)
                        if isinstance(mod_any, str) and mod_any.startswith("."):
                            binding_any[key] = normalize_relative_module_id(mod_any, entry_root, importer_path)
            qualified_any = import_resolution_any.get("qualified_refs")
            if isinstance(qualified_any, list):
                for ref_any in qualified_any:
                    if not isinstance(ref_any, dict):
                        continue
                    mod_any = ref_any.get("module_id")
                    if isinstance(mod_any, str) and mod_any.startswith("."):
                        ref_any["module_id"] = normalize_relative_module_id(mod_any, entry_root, importer_path)
    return east_doc


def rewrite_relative_imports_in_module_east_map(
    entry_path: Path,
    module_east_map: dict[str, dict[str, object]],
) -> dict[str, dict[str, object]]:
    """Rewrite relative import metadata across a whole module EAST map."""
    entry_root = resolve_import_graph_entry_root(entry_path)
    for mod_key, east_doc in module_east_map.items():
        rewrite_relative_imports_in_east_doc(
            east_doc,
            entry_root=entry_root,
            importer_path=Path(mod_key),
        )
        module_east_map[mod_key] = east_doc
    return module_east_map
