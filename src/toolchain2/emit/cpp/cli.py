#!/usr/bin/env python3
"""CLI helpers for toolchain2 C++ emit from linked manifest output."""

from __future__ import annotations

from pytra.std import json
from pytra.std.json import JsonVal
from pytra.std.pathlib import Path

from toolchain2.emit.cpp.runtime_bundle import write_helper_module_artifacts
from toolchain2.emit.cpp.runtime_bundle import write_runtime_module_artifacts
from toolchain2.emit.cpp.runtime_bundle import write_user_module_artifacts
from toolchain2.link.shared_types import LinkedModule
from toolchain2.link.shared_types import linked_module_east_doc
from toolchain2.link.shared_types import linked_module_id
from toolchain2.link.shared_types import linked_module_kind
from toolchain2.link.shared_types import linked_module_source_path


def _helper_cpp_rel_path(module_id: str) -> str:
    if module_id.startswith("pytra."):
        return module_id[len("pytra."):].replace(".", "/")
    return module_id.replace(".", "/")


def load_cpp_linked_modules(manifest_path: Path) -> list[LinkedModule]:
    manifest_text = manifest_path.read_text(encoding="utf-8")
    manifest_doc = json.loads(manifest_text).raw
    if not isinstance(manifest_doc, dict):
        raise RuntimeError("manifest root must be object: " + str(manifest_path))
    typed_manifest_doc: dict[str, JsonVal] = manifest_doc
    if "modules" not in typed_manifest_doc:
        raise RuntimeError("manifest.modules must be list")
    modules_raw_val: JsonVal = typed_manifest_doc["modules"]
    if not isinstance(modules_raw_val, list):
        raise RuntimeError("manifest.modules must be list")
    modules_raw: list[JsonVal] = modules_raw_val
    manifest_dir = manifest_path.parent
    linked_modules: list[LinkedModule] = []
    for index, entry in enumerate(modules_raw):
        if not isinstance(entry, dict):
            raise RuntimeError("manifest.modules[" + str(index) + "] must be object")
        typed_entry: dict[str, JsonVal] = entry
        module_id = typed_entry.get("module_id")
        input_path_val = typed_entry.get("input")
        output_rel = typed_entry.get("output")
        source_path = typed_entry.get("source_path")
        is_entry = typed_entry.get("is_entry")
        module_kind = typed_entry.get("module_kind")
        if not isinstance(module_id, str) or module_id == "":
            raise RuntimeError("manifest.modules[" + str(index) + "].module_id must be non-empty string")
        if not isinstance(input_path_val, str) or input_path_val == "":
            raise RuntimeError("manifest.modules[" + str(index) + "].input must be non-empty string")
        if not isinstance(output_rel, str) or output_rel == "":
            raise RuntimeError("manifest.modules[" + str(index) + "].output must be non-empty string")
        if not isinstance(source_path, str):
            raise RuntimeError("manifest.modules[" + str(index) + "].source_path must be string")
        if not isinstance(is_entry, bool):
            raise RuntimeError("manifest.modules[" + str(index) + "].is_entry must be bool")
        if not isinstance(module_kind, str) or module_kind == "":
            raise RuntimeError("manifest.modules[" + str(index) + "].module_kind must be non-empty string")
        east_path = manifest_dir.joinpath(output_rel)
        east_text = east_path.read_text(encoding="utf-8")
        east_doc = json.loads(east_text).raw
        if not isinstance(east_doc, dict):
            raise RuntimeError("linked EAST root must be object: " + str(east_path))
        typed_east_doc: dict[str, JsonVal] = east_doc
        linked_modules.append(
            LinkedModule(
                module_id=module_id,
                input_path=input_path_val,
                source_path=source_path,
                is_entry=is_entry,
                east_doc=typed_east_doc,
                module_kind=module_kind,
            )
        )
    return linked_modules


def emit_cpp_linked_module(module: LinkedModule, output_dir: Path) -> int:
    module_id: str = linked_module_id(module)
    east_doc: dict[str, JsonVal] = linked_module_east_doc(module)
    module_kind: str = linked_module_kind(module)
    source_path: str = linked_module_source_path(module)
    if module_kind == "runtime":
        return write_runtime_module_artifacts(
            module_id,
            east_doc,
            output_dir=output_dir,
            source_path=source_path,
        )
    if module_kind == "helper":
        rel_header_path = _helper_cpp_rel_path(module_id) + ".h"
        return write_helper_module_artifacts(
            module_id,
            east_doc,
            output_dir=output_dir,
            rel_header_path=rel_header_path,
        )
    return write_user_module_artifacts(
        module_id,
        east_doc,
        output_dir=output_dir,
    )


def emit_cpp_from_manifest(manifest_path: Path, output_dir: Path) -> int:
    linked_modules = load_cpp_linked_modules(manifest_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    for module in linked_modules:
        written += emit_cpp_linked_module(module, output_dir)
    print("emitted: " + str(output_dir) + " (" + str(written) + " C++ files)")
    return 0


def main(argv: list[str]) -> int:
    input_text = ""
    output_dir_text = ""
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok == "-o" or tok == "--output-dir":
            if i + 1 >= len(argv):
                print("error: missing value for " + tok)
                return 1
            output_dir_text = argv[i + 1]
            i += 2
            continue
        if tok == "-h" or tok == "--help":
            print("usage: python3 src/toolchain2/emit/cpp/cli.py MANIFEST.json [-o OUTPUT_DIR]")
            return 0
        if not tok.startswith("-") and input_text == "":
            input_text = tok
        i += 1

    if input_text == "":
        print("error: manifest.json path is required")
        return 1

    manifest_path = Path(input_text)
    if manifest_path.name != "manifest.json":
        manifest_path = manifest_path.joinpath("manifest.json")
    if not manifest_path.exists():
        print("error: manifest.json not found: " + str(manifest_path))
        return 1

    if output_dir_text == "":
        output_dir_text = str(Path("work").joinpath("tmp").joinpath("emit").joinpath("cpp"))
    return emit_cpp_from_manifest(manifest_path, Path(output_dir_text))


if __name__ == "__main__":
    import sys as _stdlib_sys

    raise SystemExit(main(_stdlib_sys.argv[1:]))
