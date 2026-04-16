"""Common CLI runner for language-specific emit cli.py modules.

Each language's cli.py delegates to this runner:

    from toolchain.emit.common.cli_runner import run_emit_cli
    from toolchain.emit.<lang>.emitter import emit_<lang>_module

    if __name__ == "__main__":
        import sys
        raise SystemExit(run_emit_cli(emit_<lang>_module, sys.argv[1:]))

The runner handles manifest loading, module iteration, argument parsing,
and file writing. The language-specific emit function only needs to
accept an EAST3 document and return a code string.
"""

from __future__ import annotations

from typing import Callable

from pytra.std import json
from pytra.std.json import JsonVal
from pytra.std.pathlib import Path


type EmitFn = Callable[[dict[str, JsonVal]], str]
type DirectEmitFn = Callable[[dict[str, JsonVal], Path], int]
type PostEmitFn = Callable[[Path], None]


def _parse_args(argv: list[str]) -> tuple[str, str, str]:
    """Parse CLI arguments. Returns (input_path, output_dir, file_ext)."""
    input_text: str = ""
    output_dir_text: str = ""
    file_ext: str = ""
    i: int = 0
    while i < len(argv):
        tok: str = argv[i]
        if tok == "-o" or tok == "--output-dir":
            if i + 1 >= len(argv):
                raise RuntimeError("missing value for " + tok)
            output_dir_text = argv[i + 1]
            i += 2
            continue
        if tok == "--ext":
            if i + 1 >= len(argv):
                raise RuntimeError("missing value for --ext")
            file_ext = argv[i + 1]
            i += 2
            continue
        if tok == "-h" or tok == "--help":
            print("usage: python3 -m toolchain.emit.<lang>.cli MANIFEST_DIR_OR_FILE [-o OUTPUT_DIR] [--ext .EXT]")
            raise SystemExit(0)
        if not tok.startswith("-") and input_text == "":
            input_text = tok
        i += 1
    return input_text, output_dir_text, file_ext


def _load_linked_modules(manifest_path: Path) -> list[dict[str, JsonVal]]:
    """Load linked modules from a manifest.json file."""
    manifest_text: str = manifest_path.read_text(encoding="utf-8")
    manifest_doc: JsonVal = json.loads(manifest_text).raw
    if not isinstance(manifest_doc, dict):
        raise RuntimeError("manifest root must be object: " + str(manifest_path))
    typed_manifest: dict[str, JsonVal] = manifest_doc
    modules_raw: JsonVal = typed_manifest.get("modules", [])
    if not isinstance(modules_raw, list):
        raise RuntimeError("manifest.modules must be list")
    manifest_dir: Path = manifest_path.parent
    result: list[dict[str, JsonVal]] = []
    for index, entry in enumerate(modules_raw):
        if not isinstance(entry, dict):
            raise RuntimeError("manifest.modules[" + str(index) + "] must be object")
        typed_entry: dict[str, JsonVal] = entry
        output_rel: JsonVal = typed_entry.get("output")
        if not isinstance(output_rel, str) or output_rel == "":
            raise RuntimeError("manifest.modules[" + str(index) + "].output must be non-empty string")
        east_path: Path = manifest_dir.joinpath(output_rel)
        east_text: str = east_path.read_text(encoding="utf-8")
        east_doc: JsonVal = json.loads(east_text).raw
        if not isinstance(east_doc, dict):
            raise RuntimeError("linked EAST root must be object: " + str(east_path))
        typed_east: dict[str, JsonVal] = east_doc
        # Inject module metadata from manifest entry into east_doc meta
        meta_val: JsonVal = typed_east.get("meta")
        typed_meta: dict[str, JsonVal] = {}
        if isinstance(meta_val, dict):
            typed_meta = meta_val
        else:
            typed_east["meta"] = typed_meta
        module_id: JsonVal = typed_entry.get("module_id")
        if isinstance(module_id, str):
            typed_meta["_cli_module_id"] = module_id
        module_kind: JsonVal = typed_entry.get("module_kind")
        if isinstance(module_kind, str):
            typed_meta["_cli_module_kind"] = module_kind
        is_entry: JsonVal = typed_entry.get("is_entry")
        if isinstance(is_entry, bool):
            typed_meta["_cli_is_entry"] = is_entry
        source_path: JsonVal = typed_entry.get("source_path")
        if isinstance(source_path, str):
            typed_meta["_cli_source_path"] = source_path
        result.append(typed_east)
    return result


def run_emit_cli(
    emit_fn: EmitFn | None = None,
    argv: list[str] | None = None,
    *,
    default_ext: str = "",
    post_emit: PostEmitFn | None = None,
    direct_emit_fn: DirectEmitFn | None = None,
) -> int:
    """Run the emit CLI with the given language-specific emit function.

    Args:
        emit_fn: Language-specific emit function (east_doc -> code string).
                 Mutually exclusive with direct_emit_fn.
        argv: Command-line arguments (excluding program name).
        post_emit: Optional callback called after all modules are emitted,
                   receives output_dir. Use for runtime file copying etc.
        direct_emit_fn: Alternative emit function that writes files directly
                        (east_doc, output_dir -> written_count). Used by C++ etc.
                        When set, emit_fn and default_ext are ignored.
        default_ext: Default file extension (e.g. ".rs", ".go"). If empty,
                     must be provided via --ext.
    Returns:
        Exit code (0 on success).
    """
    if argv is None:
        argv = []
    input_text, output_dir_text, file_ext = _parse_args(argv)

    use_direct = direct_emit_fn is not None
    if not use_direct:
        if emit_fn is None:
            raise RuntimeError("either emit_fn or direct_emit_fn must be provided")
        if file_ext == "":
            file_ext = default_ext
        if file_ext == "":
            raise RuntimeError("file extension must be specified via --ext or default_ext")

    if input_text == "":
        print("error: manifest.json path or directory is required")
        return 1

    manifest_path: Path = Path(input_text)
    if manifest_path.name != "manifest.json":
        manifest_path = manifest_path.joinpath("manifest.json")
    if not manifest_path.exists():
        print("error: manifest.json not found: " + str(manifest_path))
        return 1

    if output_dir_text == "":
        output_dir_text = str(Path("work").joinpath("tmp").joinpath("emit"))
    output_dir: Path = Path(output_dir_text)
    output_dir.mkdir(parents=True, exist_ok=True)

    modules: list[dict[str, JsonVal]] = _load_linked_modules(manifest_path)
    written: int = 0

    if use_direct and direct_emit_fn is not None:
        for east_doc in modules:
            written += direct_emit_fn(east_doc, output_dir)
    elif emit_fn is not None:
        for east_doc in modules:
            code: str = emit_fn(east_doc)
            if code.strip() == "":
                continue
            meta: JsonVal = east_doc.get("meta")
            module_id: str = ""
            if isinstance(meta, dict):
                mid: JsonVal = meta.get("_cli_module_id")
                if isinstance(mid, str):
                    module_id = mid
            if module_id == "":
                module_id = "module_" + str(written)
            out_name: str = module_id.replace(".", "_") + file_ext
            output_dir.joinpath(out_name).write_text(code, encoding="utf-8")
            written += 1

    if post_emit is not None:
        post_emit(output_dir)

    print("emitted: " + str(output_dir) + " (" + str(written) + " files)")
    return 0
