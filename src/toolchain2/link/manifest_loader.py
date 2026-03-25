"""Load linked output bundle (manifest.json + east3/ files).

Replaces toolchain/link/materializer.load_linked_output_bundle
without depending on the old toolchain.

§5 準拠: Any/object 禁止, pytra.std.* のみ, selfhost 対象。
"""

from __future__ import annotations

from dataclasses import dataclass

from pytra.std.json import JsonVal
from pytra.std import json
from pytra.std.pathlib import Path


@dataclass
class LinkedModuleEntry:
    """A module loaded from a linked output bundle."""
    module_id: str
    source_path: str
    is_entry: bool
    east_doc: dict[str, JsonVal]
    module_kind: str = "user"


def load_linked_output(manifest_path: Path) -> tuple[dict[str, JsonVal], list[LinkedModuleEntry]]:
    """Load manifest.json and resolve linked east3 modules.

    Returns (manifest_doc, list of LinkedModuleEntry).
    """
    text = manifest_path.read_text(encoding="utf-8")
    raw = json.loads(text).raw
    if not isinstance(raw, dict):
        raise RuntimeError("manifest root must be object: " + str(manifest_path))

    manifest_dir = manifest_path.parent
    modules_raw = raw.get("modules")
    if not isinstance(modules_raw, list):
        raise RuntimeError("manifest.modules must be list")

    modules: list[LinkedModuleEntry] = []
    for entry in modules_raw:
        if not isinstance(entry, dict):
            continue
        mid = entry.get("module_id")
        if not isinstance(mid, str) or mid == "":
            continue
        output = entry.get("output")
        if not isinstance(output, str) or output == "":
            continue
        sp = entry.get("source_path")
        source_path = sp if isinstance(sp, str) else ""
        ie = entry.get("is_entry")
        is_entry = ie if isinstance(ie, bool) else False
        mk = entry.get("module_kind")
        module_kind = mk if isinstance(mk, str) else "user"

        east_path = manifest_dir / output
        if not east_path.exists():
            continue
        east_text = east_path.read_text(encoding="utf-8")
        east_raw = json.loads(east_text).raw
        if not isinstance(east_raw, dict):
            continue

        modules.append(LinkedModuleEntry(
            module_id=mid,
            source_path=source_path,
            is_entry=is_entry,
            east_doc=east_raw,
            module_kind=module_kind,
        ))

    modules.sort(key=lambda m: m.module_id)
    return raw, modules
