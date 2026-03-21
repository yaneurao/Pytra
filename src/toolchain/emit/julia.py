#!/usr/bin/env python3
"""Julia backend: link-output.json → Julia multi-file output.

Usage:
    python3 -m toolchain.emit.julia LINK_OUTPUT.json --output-dir out/julia/
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from toolchain.emit.julia.emitter import transpile_to_julia_native
from toolchain.emit.loader import emit_all_modules, load_linked_modules

_RUNTIME_EAST_ROOT = Path(__file__).resolve().parents[2] / "runtime" / "east"
_RUNTIME_MODULE_BUCKETS = {
    "pytra.built_in.": "built_in",
    "pytra.std.": "std",
    "pytra.utils.": "utils",
}


def _resolve_runtime_east_path(module_id: str) -> Path | None:
    for prefix, bucket in _RUNTIME_MODULE_BUCKETS.items():
        if module_id.startswith(prefix):
            name = module_id[len(prefix):]
            east_path = _RUNTIME_EAST_ROOT / bucket / (name + ".east")
            if east_path.exists():
                return east_path
    return None


def _collect_missing_runtime_module_ids(modules: list[dict]) -> list[str]:
    """Scan linked modules for runtime imports not already in the module list."""
    known_ids = {m["module_id"] for m in modules}
    missing: list[str] = []
    seen: set[str] = set()

    for mod in modules:
        east_doc = mod.get("east_doc")
        if not isinstance(east_doc, dict):
            continue
        body = east_doc.get("body")
        if not isinstance(body, list):
            continue
        for stmt in body:
            if not isinstance(stmt, dict):
                continue
            kind = stmt.get("kind")
            if kind == "ImportFrom":
                module_name = stmt.get("module")
                if not isinstance(module_name, str):
                    continue
                names = stmt.get("names")
                if isinstance(names, list):
                    for ent in names:
                        if isinstance(ent, dict):
                            sym = ent.get("name")
                            if isinstance(sym, str) and sym != "" and sym != "*":
                                candidate = module_name + "." + sym
                                if candidate not in known_ids and candidate not in seen:
                                    if _resolve_runtime_east_path(candidate) is not None:
                                        missing.append(candidate)
                                        seen.add(candidate)
                if module_name not in known_ids and module_name not in seen:
                    if _resolve_runtime_east_path(module_name) is not None:
                        missing.append(module_name)
                        seen.add(module_name)
            elif kind == "Import":
                names = stmt.get("names")
                if isinstance(names, list):
                    for ent in names:
                        if isinstance(ent, dict):
                            name = ent.get("name")
                            if isinstance(name, str) and name not in known_ids and name not in seen:
                                if _resolve_runtime_east_path(name) is not None:
                                    missing.append(name)
                                    seen.add(name)
    return missing


def _emit_runtime_modules(output_dir: str, runtime_module_ids: list[str]) -> None:
    """Transpile runtime .east modules and write them to output_dir."""
    out = Path(output_dir)
    for mod_id in runtime_module_ids:
        east_path = _resolve_runtime_east_path(mod_id)
        if east_path is None:
            continue
        east_doc = json.loads(east_path.read_text(encoding="utf-8"))
        # Ensure east_stage is set
        if east_doc.get("east_stage") is None:
            east_doc["east_stage"] = 3
        try:
            source = transpile_to_julia_native(east_doc)
        except Exception as exc:
            print(f"warning: failed to transpile runtime module {mod_id}: {exc}", file=sys.stderr)
            continue
        # Map module_id to file path
        for prefix, bucket in _RUNTIME_MODULE_BUCKETS.items():
            if mod_id.startswith(prefix):
                name = mod_id[len(prefix):]
                rel_path = bucket + "/" + name + ".jl"
                break
        else:
            rel_path = mod_id.replace(".", "/") + ".jl"
        out_path = out / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(source, encoding="utf-8")
        print("generated: " + str(out_path))


def _copy_runtime(output_dir: str) -> None:
    """Copy py_runtime.jl to each directory containing generated .jl files."""
    src_dir = Path(__file__).resolve().parents[2]
    runtime_src = src_dir / "runtime" / "julia" / "built_in" / "py_runtime.jl"
    if not runtime_src.exists():
        return
    out = Path(output_dir)
    dirs_seen: set[str] = set()
    for jl_file in out.rglob("*.jl"):
        parent = str(jl_file.parent)
        if parent not in dirs_seen:
            dirs_seen.add(parent)
            dest = jl_file.parent / "py_runtime.jl"
            if not dest.exists():
                shutil.copy2(str(runtime_src), str(dest))


def main() -> int:
    argv = sys.argv[1:]
    if len(argv) == 0 or argv[0] in ("-h", "--help"):
        print("usage: toolchain.emit.julia LINK_OUTPUT.json --output-dir DIR")
        return 0

    input_path = ""
    output_dir = "out/julia"
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
        print("error: input link-output.json is required", file=sys.stderr)
        return 1

    # Load linked modules to scan for missing runtime deps
    modules, _ = load_linked_modules(input_path)
    missing_runtime = _collect_missing_runtime_module_ids(modules)

    rc = emit_all_modules(input_path, output_dir, ".jl", transpile_to_julia_native)
    if rc != 0:
        return rc

    # Emit missing runtime modules (png, gif, etc.)
    if len(missing_runtime) > 0:
        _emit_runtime_modules(output_dir, missing_runtime)

    _copy_runtime(output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
