"""JSON I/O helpers for linked-program manifests."""

from __future__ import annotations

from typing import Any

from pytra.std import json
from pytra.std.pathlib import Path

from toolchain.json_adapters import export_json_object_dict
from toolchain.json_adapters import load_json_object_doc
from toolchain.link.program_validator import validate_link_input_doc
from toolchain.link.program_validator import validate_link_output_doc


def _load_json_doc(path: Path, label: str) -> dict[str, object]:
    return export_json_object_dict(load_json_object_doc(path, label=label))


def load_link_input_doc(path: Path) -> dict[str, object]:
    return validate_link_input_doc(_load_json_doc(path, "link-input"))


def load_link_output_doc(path: Path) -> dict[str, object]:
    return validate_link_output_doc(_load_json_doc(path, "link-output"))


def save_manifest_doc(path: Path, doc: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
