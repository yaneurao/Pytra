#!/usr/bin/env python3
"""CLI helpers for toolchain2 Kotlin emit from linked manifest output."""

from __future__ import annotations

from pytra.std import json
from pytra.std.json import JsonVal
from pytra.std.pathlib import Path

from toolchain2.emit.kotlin.emitter import emit_kotlin_module


def _copy_kotlin_runtime_files(output_dir: Path) -> int:
    runtime_root = Path(".").resolve().joinpath("src").joinpath("runtime").joinpath("kotlin")
    copied = 0
    if not runtime_root.exists():
        return copied
    for bucket in ["built_in", "std"]:
        bucket_dir = runtime_root.joinpath(bucket)
        if not bucket_dir.exists():
            continue
        for kt_file in bucket_dir.glob("*.kt"):
            dst = output_dir.joinpath(kt_file.name)
            dst.write_text(kt_file.read_text(encoding="utf-8"), encoding="utf-8")
            copied += 1
    return copied


def _inject_kotlin_emit_context(east_doc: dict[str, JsonVal], module_id: str, *, is_entry: bool) -> None:
    meta = east_doc.get("meta")
    if not isinstance(meta, dict):
        meta = {}
        east_doc["meta"] = meta
    emit_context = meta.get("emit_context")
    if not isinstance(emit_context, dict):
        emit_context = {}
        meta["emit_context"] = emit_context
    emit_context["module_id"] = module_id
    emit_context["is_entry"] = is_entry


def emit_kotlin_from_manifest(manifest_path: Path, output_dir: Path) -> int:
    manifest_doc = json.loads_obj(manifest_path.read_text(encoding="utf-8"))
    if manifest_doc is None:
        print("error: invalid manifest: " + str(manifest_path))
        return 1
    modules = manifest_doc.get_arr("modules")
    if modules is None:
        print("error: invalid manifest.modules: " + str(manifest_path))
        return 1
    output_dir.mkdir(parents=True, exist_ok=True)
    emitted = 0
    for item in modules.raw:
        item_obj = json.JsonValue(item).as_obj()
        if item_obj is None:
            continue
        module_id = item_obj.get_str("module_id")
        rel_output = item_obj.get_str("output")
        is_entry = item_obj.get_bool("is_entry")
        if module_id is None or module_id == "" or rel_output is None or rel_output == "":
            continue
        if module_id.startswith("pytra.built_in.") or module_id.startswith("pytra.core."):
            continue
        east_path = manifest_path.parent.joinpath(rel_output)
        if not east_path.exists():
            print("error: linked east3 missing: " + str(east_path))
            return 1
        east_doc_obj = json.loads_obj(east_path.read_text(encoding="utf-8"))
        if east_doc_obj is None:
            print("error: invalid east3 document: " + str(east_path))
            return 1
        _inject_kotlin_emit_context(east_doc_obj.raw, module_id, is_entry=(is_entry is True))
        code = emit_kotlin_module(east_doc_obj.raw)
        if code.strip() == "":
            continue
        out_path = output_dir.joinpath(module_id.replace(".", "_") + ".kt")
        out_path.write_text(code, encoding="utf-8")
        emitted += 1
    _copy_kotlin_runtime_files(output_dir)
    print("emitted: " + str(output_dir) + " (" + str(emitted) + " files)")
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
            print("usage: python3 src/toolchain2/emit/kotlin/cli.py MANIFEST.json [-o OUTPUT_DIR]")
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
        output_dir_text = str(Path("work").joinpath("tmp").joinpath("emit").joinpath("kotlin"))
    return emit_kotlin_from_manifest(manifest_path, Path(output_dir_text))


if __name__ == "__main__":
    import sys as _stdlib_sys

    raise SystemExit(main(_stdlib_sys.argv[1:]))
