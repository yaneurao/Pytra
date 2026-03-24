#!/usr/bin/env python3
"""Scala backend: manifest.json → Scala single-file output.

All linked modules are merged into a single .scala file to avoid
top-level definition collisions in Scala 3.

Usage:
    python3 -m toolchain.emit.scala MANIFEST.json --output-dir work/tmp/scala/
"""

from __future__ import annotations

import sys
from pathlib import Path

from toolchain.emit.scala.emitter.scala_native_emitter import transpile_to_scala_native
from toolchain.emit.loader import emit_all_modules


def _transpile_scala(east_doc: dict) -> str:
    """Wrapper to adapt transpile_to_scala_native to the standard (dict) -> str signature."""
    meta = east_doc.get("meta", {})
    emit_ctx = meta.get("emit_context", {}) if isinstance(meta, dict) else {}
    is_entry = emit_ctx.get("is_entry", False) if isinstance(emit_ctx, dict) else False
    return transpile_to_scala_native(east_doc, emit_main=is_entry)


def main() -> int:
    argv = sys.argv[1:]
    if len(argv) == 0 or argv[0] in ("-h", "--help"):
        print("usage: toolchain.emit.scala MANIFEST.json --output-dir DIR")
        return 0

    input_path = ""
    output_dir = "work/tmp/scala"
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok == "--output-dir" and i + 1 < len(argv):
            output_dir = argv[i + 1]
            i += 2
            continue
        if not tok.startswith("-") and input_path == "":
            input_path = tok
        i += 1

    if input_path == "":
        print("error: input manifest.json is required", file=sys.stderr)
        return 1

    # Scala merges all modules into a single file (spec §5 exception).
    # Use emit_all_modules for per-module transpilation, then merge the results.
    # We collect per-module outputs by using a capturing transpile function.
    per_module_results: list[tuple[str, str, bool]] = []  # (module_id, source, is_entry)

    def _capture_scala(east_doc: dict) -> str:
        meta = east_doc.get("meta", {})
        emit_ctx = meta.get("emit_context", {}) if isinstance(meta, dict) else {}
        is_entry = emit_ctx.get("is_entry", False) if isinstance(emit_ctx, dict) else False
        module_id = emit_ctx.get("module_id", "") if isinstance(emit_ctx, dict) else ""
        source = transpile_to_scala_native(east_doc, emit_main=is_entry)
        per_module_results.append((module_id, source, is_entry))
        return source

    # emit_all_modules writes per-module files and copies native runtime
    rc = emit_all_modules(input_path, output_dir, ".scala", _capture_scala, lang="scala")
    if rc != 0:
        return rc

    # Now merge all per-module files into a single .scala file
    if not per_module_results:
        return 0

    submodule_sources: list[str] = []
    entry_source = ""
    entry_stem = ""

    for module_id, source, is_entry in per_module_results:
        if is_entry:
            entry_source = source
            entry_stem = module_id
        else:
            submodule_sources.append("// --- module: " + module_id + " ---\n" + source)

    # Collect unique import lines from all sources
    all_imports: set[str] = set()
    all_body_lines: list[str] = []

    for src in submodule_sources + [entry_source]:
        for line in src.split("\n"):
            stripped = line.strip()
            if stripped.startswith("import "):
                all_imports.add(stripped)
            else:
                all_body_lines.append(line)

    merged_parts: list[str] = []
    merged_parts.extend(sorted(all_imports))
    merged_parts.append("")
    merged_parts.extend(all_body_lines)

    merged = "\n".join(merged_parts)

    if entry_stem == "":
        entry_stem = "main"
    out = Path(output_dir)
    out_path = out / (entry_stem + ".scala")
    out_path.write_text(merged, encoding="utf-8")
    # Suppress merged message to avoid polluting stdout during parity check.
    # print("merged: " + str(out_path), file=sys.stderr)

    # Remove per-module files that were merged into the single output.
    # Keep built_in/ and std/*_native.scala (hand-written runtime).
    for module_id, _source, _is_entry in per_module_results:
        if module_id.startswith("pytra."):
            rel = module_id[len("pytra."):]
        else:
            rel = module_id
        mod_file = out / (rel.replace(".", "/") + ".scala")
        if mod_file.exists() and mod_file != out_path:
            mod_file.unlink()
    # Clean up empty subdirectories left after removal
    for sub in sorted(out.rglob("*"), reverse=True):
        if sub.is_dir() and sub != out:
            try:
                sub.rmdir()  # only removes if empty
            except OSError:
                pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
