"""Shared loader and multi-module emit helpers for emit entry points.

Handles link-output.json (linked program manifest) loading and
multi-module emit orchestration.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

LINK_OUTPUT_SCHEMA = "pytra.link_output.v1"


def load_linked_modules(input_path: str) -> tuple[list[dict[str, Any]], list[str]]:
    """Load linked modules from a link-output.json.

    Returns (modules, entry_module_ids) where each module is a dict with:
        - module_id: str
        - east_doc: dict (the EAST3 document)
        - source_path: str
        - is_entry: bool
    """
    p = Path(input_path)
    raw = json.loads(p.read_text(encoding="utf-8"))
    manifest_dir = p.parent

    schema = raw.get("schema", "")
    if schema != LINK_OUTPUT_SCHEMA:
        raise RuntimeError(
            f"link-output manifest required: expected schema={LINK_OUTPUT_SCHEMA!r}, "
            f"got {schema!r}. Raw EAST3 JSON is not accepted; run the linker first."
        )

    entry_modules_any = raw.get("entry_modules", [])
    entry_modules: list[str] = []
    if isinstance(entry_modules_any, (list, tuple)):
        for item in entry_modules_any:
            if isinstance(item, str) and item != "":
                entry_modules.append(item)

    modules_any = raw.get("modules", [])
    if not isinstance(modules_any, list):
        raise RuntimeError("link-output.json: modules must be a list")

    modules: list[dict[str, Any]] = []
    for item in modules_any:
        if isinstance(item, dict):
            module_id = item.get("module_id", "")
            output = item.get("output", "")
            source_path = item.get("source_path", "")
            is_entry = bool(item.get("is_entry", False))
        else:
            module_id = getattr(item, "module_id", "")
            output = getattr(item, "output", "")
            source_path = getattr(item, "source_path", "")
            is_entry = bool(getattr(item, "is_entry", False))

        if module_id == "" or output == "":
            continue

        artifact_path = manifest_dir / output
        east_doc = json.loads(artifact_path.read_text(encoding="utf-8"))
        modules.append({
            "module_id": module_id,
            "east_doc": east_doc,
            "source_path": source_path,
            "is_entry": is_entry,
        })

    return modules, entry_modules


def emit_all_modules(
    input_path: str,
    output_dir: str,
    ext: str,
    transpile_fn: Callable[[dict[str, Any]], str],
) -> int:
    """Load linked modules and emit all of them to output_dir.

    Before calling *transpile_fn*, each module's ``meta.emit_context`` is set
    with ``module_id``, ``root_rel_prefix``, and ``is_entry`` so that emitters
    can resolve sub-module import paths relative to the output root.
    See spec-runtime.md §0.6c for details.

    Args:
        input_path: Path to link-output.json.
        output_dir: Directory to write output files.
        ext: File extension (e.g. ".rs", ".lua").
        transpile_fn: Function that takes an EAST3 dict and returns source code string.

    Returns exit code (0 = success).
    """
    modules, entry_modules = load_linked_modules(input_path)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    for mod in modules:
        module_id = mod["module_id"]
        east_doc = mod["east_doc"]
        is_entry = mod.get("is_entry", False)
        # Use module_id as filename, replacing dots with path separators.
        # Strip "pytra." prefix for runtime modules (pytra.std.time → std/time).
        rel_module = module_id
        if rel_module.startswith("pytra."):
            rel_module = rel_module[len("pytra."):]
        rel_path = rel_module.replace(".", "/") + ext
        out_path = out / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        # Compute root-relative prefix for sub-module import path resolution.
        # e.g. "os/east" (depth 1) → "../", "a/b/c" (depth 2) → "../../"
        depth = rel_path.count("/")
        root_rel_prefix = "../" * depth if depth > 0 else "./"
        # Inject emit context into EAST3 meta for emitter use
        meta = east_doc.get("meta")
        if not isinstance(meta, dict):
            meta = {}
            east_doc["meta"] = meta
        meta["emit_context"] = {
            "module_id": module_id,
            "root_rel_prefix": root_rel_prefix,
            "is_entry": bool(is_entry),
        }
        source = transpile_fn(east_doc)
        out_path.write_text(source, encoding="utf-8")
        print("generated: " + str(out_path))

    return 0
