"""Linked-program manifest data models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pytra.std.pathlib import Path


LINK_INPUT_SCHEMA = "pytra.link_input.v1"
LINK_OUTPUT_SCHEMA = "pytra.link_output.v1"
DISPATCH_MODES = ("native", "type_id")
MODULE_KINDS = ("user", "runtime", "helper")


@dataclass(frozen=True)
class LinkInputModuleEntry:
    """Raw `link-input.v1` module entry."""

    module_id: str
    path: str
    source_path: str
    is_entry: bool


@dataclass(frozen=True)
class LinkOutputModuleEntry:
    """Raw `link-output.v1` module entry."""

    module_id: str
    input: str
    output: str
    source_path: str
    is_entry: bool
    module_kind: str = "user"
    helper_id: str = ""
    owner_module_id: str = ""
    generated_by: str = ""


@dataclass(frozen=True)
class LinkedProgramModule:
    """Validated module loaded from `link-input.v1`."""

    module_id: str
    source_path: str
    is_entry: bool
    east_doc: dict[str, object]
    artifact_path: Path | None = None
    module_kind: str = "user"
    helper_id: str = ""
    owner_module_id: str = ""
    generated_by: str = ""

    @property
    def path(self) -> Path:
        if self.artifact_path is not None:
            return self.artifact_path
        return Path(self.source_path).resolve()


@dataclass(frozen=True)
class LinkedProgram:
    """Deterministic program unit for linker/global optimizer input."""

    schema: str
    manifest_path: Path | None
    target: str
    dispatch_mode: str
    entry_modules: tuple[str, ...]
    modules: tuple[LinkedProgramModule, ...]
    options: dict[str, object]

    @property
    def manifest_dir(self) -> Path:
        if self.manifest_path is None:
            raise RuntimeError("manifest_dir is unavailable for in-memory LinkedProgram")
        return self.manifest_path.parent

    def to_link_input_dict(self) -> dict[str, object]:
        if self.manifest_path is None:
            raise RuntimeError("in-memory LinkedProgram cannot be serialized without manifest_path")
        modules: list[dict[str, object]] = []
        for item in self.modules:
            artifact_path = item.artifact_path
            if artifact_path is None:
                raise RuntimeError("LinkedProgramModule.artifact_path is required for serialization")
            rel_path = artifact_path.relative_to(self.manifest_dir).as_posix()
            modules.append(
                {
                    "module_id": item.module_id,
                    "path": rel_path,
                    "source_path": item.source_path,
                    "is_entry": item.is_entry,
                }
            )
        return {
            "schema": self.schema,
            "target": self.target,
            "dispatch_mode": self.dispatch_mode,
            "entry_modules": list(self.entry_modules),
            "modules": modules,
            "options": dict(self.options),
        }


def normalize_writer_options(raw: object) -> dict[str, object]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, object] = {}
    for key, value in raw.items():
        if isinstance(key, str):
            out[key] = value
    return out
