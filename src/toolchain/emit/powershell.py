#!/usr/bin/env python3
"""Standalone PowerShell backend: linked EAST → PowerShell source.

This is the PowerShell backend entry point.  It reads a link-output.json
(produced by ``pytra-cli.py --link-only``) and emits PowerShell source files.

Usage:
    python3 -m toolchain.emit.powershell LINK_OUTPUT.json --output-dir out/ps/
    python3 -m toolchain.emit.powershell INPUT.east3.json -o out/output.ps1
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from toolchain.emit.powershell.emitter import transpile_to_powershell_native


def _is_link_output(doc: dict[str, object]) -> bool:
    return "manifest" in doc or "linked_modules" in doc or ("modules" in doc and "entry_modules" in doc)


def main() -> int:
    argv = sys.argv[1:]
    if len(argv) == 0 or argv[0] in ("-h", "--help"):
        print("usage: toolchain.emit.powershell LINK_OUTPUT.json --output-dir DIR")
        print("       toolchain.emit.powershell INPUT.east3.json -o OUTPUT.ps1")
        return 0

    input_path = ""
    output_path = ""
    output_dir = ""
    i = 0
    while i < len(argv):
        tok = argv[i]
        if (tok == "-o" or tok == "--output") and i + 1 < len(argv):
            output_path = argv[i + 1]
            i += 2
            continue
        if tok == "--output-dir" and i + 1 < len(argv):
            output_dir = argv[i + 1]
            i += 2
            continue
        # Skip options with values that we don't use (e.g. --target, --emitter-option)
        if tok in ("--target", "--emitter-option", "--lower-option", "--optimizer-option") and i + 1 < len(argv):
            i += 2
            continue
        if tok == "--no-runtime-hook":
            i += 1
            continue
        if not tok.startswith("-") and input_path == "":
            input_path = tok
        i += 1

    if input_path == "":
        print("error: input file is required", file=sys.stderr)
        return 1

    raw = json.loads(Path(input_path).read_text(encoding="utf-8"))

    # Linked program bundle (from pytra-cli.py --link-only)
    if isinstance(raw, dict) and _is_link_output(raw):
        from toolchain.link import load_linked_output_bundle

        manifest_doc, linked_modules = load_linked_output_bundle(Path(input_path))
        entry_modules_any = manifest_doc.get("entry_modules", [])
        entry_modules: list[str] = []
        if isinstance(entry_modules_any, (list, tuple)):
            for item in entry_modules_any:
                if isinstance(item, str) and item != "":
                    entry_modules.append(item)

        if output_dir == "":
            output_dir = "out/powershell"
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        # Copy runtime
        runtime_src = Path(__file__).resolve().parent.parent.parent / "runtime" / "powershell" / "built_in" / "py_runtime.ps1"
        if runtime_src.exists():
            (out_dir / "py_runtime.ps1").write_text(runtime_src.read_text(encoding="utf-8"), encoding="utf-8")

        entry_set = set(entry_modules)
        for module in linked_modules:
            east_doc = module.east_doc
            if not isinstance(east_doc, dict):
                continue
            if east_doc.get("kind") != "Module":
                continue
            if module.is_entry and module.module_id in entry_set:
                source = transpile_to_powershell_native(east_doc)
                stem = Path(module.source_path).stem if module.source_path != "" else module.module_id
                out_file = out_dir / (stem + ".ps1")
                out_file.write_text(source, encoding="utf-8")
                print("generated: " + str(out_file))

        return 0

    # Single EAST3 JSON (direct mode)
    if output_path == "":
        output_path = Path(input_path).stem + ".ps1"
    east_doc = raw
    source = transpile_to_powershell_native(east_doc)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(source, encoding="utf-8")
    print("generated: " + output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
