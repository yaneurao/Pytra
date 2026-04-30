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

from dataclasses import dataclass
from typing import Callable

from pytra.std import json
from pytra.std.json import JsonVal
from pytra.std.pathlib import Path


type EmitFn = Callable[[dict[str, JsonVal]], str]
type DirectEmitFn = Callable[[dict[str, JsonVal], Path], int]
type PostEmitFn = Callable[[Path], None]


def _jv_get(node: dict[str, JsonVal], key: str) -> JsonVal:
    return node.get(key)


@dataclass
class ManifestModuleEntryDraft:
    module_id: str = ""
    output: str = ""
    module_kind: str = ""
    is_entry: bool = False
    source_path: str = ""

    @staticmethod
    def from_jv(entry: dict[str, JsonVal], index: int) -> ManifestModuleEntryDraft:
        output_raw = json.JsonValue(_jv_get(entry, "output")).as_str()
        if output_raw is None:
            return ManifestModuleEntryDraft()
        output: str = output_raw
        if output == "":
            return ManifestModuleEntryDraft()
        module_id = ""
        module_id_raw = json.JsonValue(_jv_get(entry, "module_id")).as_str()
        if module_id_raw is not None:
            module_id = module_id_raw
        module_kind = ""
        module_kind_raw = json.JsonValue(_jv_get(entry, "module_kind")).as_str()
        if module_kind_raw is not None:
            module_kind = module_kind_raw
        is_entry = False
        is_entry_raw = json.JsonValue(_jv_get(entry, "is_entry")).as_bool()
        if is_entry_raw is not None:
            is_entry = is_entry_raw
        source_path = ""
        source_path_raw = json.JsonValue(_jv_get(entry, "source_path")).as_str()
        if source_path_raw is not None:
            source_path = source_path_raw
        return ManifestModuleEntryDraft(
            module_id,
            output,
            module_kind,
            is_entry,
            source_path,
        )

    def build_cli_meta(self, east_doc: dict[str, JsonVal]) -> dict[str, JsonVal]:
        meta_val: JsonVal = _jv_get(east_doc, "meta")
        typed_meta: dict[str, JsonVal] = {}
        meta_obj = json.JsonValue(meta_val).as_obj()
        if meta_obj is not None:
            typed_meta = meta_obj.raw
        if self.module_id != "":
            typed_meta["_cli_module_id"] = self.module_id
        if self.module_kind != "":
            typed_meta["_cli_module_kind"] = self.module_kind
        typed_meta["_cli_is_entry"] = self.is_entry
        if self.source_path != "":
            typed_meta["_cli_source_path"] = self.source_path
        return typed_meta


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
                return "", "", "__pytra_error__:missing value for " + tok
            output_dir_text = argv[i + 1]
            i += 2
            continue
        if tok == "--ext":
            if i + 1 >= len(argv):
                return "", "", "__pytra_error__:missing value for --ext"
            file_ext = argv[i + 1]
            i += 2
            continue
        if tok == "-h" or tok == "--help":
            print("usage: python3 -m toolchain.emit.<lang>.cli MANIFEST_DIR_OR_FILE [-o OUTPUT_DIR] [--ext .EXT]")
            return "", "", "__pytra_help__"
        if not tok.startswith("-") and input_text == "":
            input_text = tok
        i += 1
    return input_text, output_dir_text, file_ext


def _path_name(path: Path) -> str:
    text: str = str(path)
    last: int = -1
    i: int = 0
    while i < len(text):
        if text[i] == "/":
            last = i
        i += 1
    return text[last + 1 :]


def _path_parent(path: Path) -> Path:
    text: str = str(path)
    last: int = -1
    i: int = 0
    while i < len(text):
        if text[i] == "/":
            last = i
        i += 1
    if last <= 0:
        return Path(".")
    return Path(text[:last])


def _load_linked_modules(manifest_path: Path) -> list[dict[str, JsonVal]]:
    """Load linked modules from a manifest.json file."""
    manifest_text: str = manifest_path.read_text(encoding="utf-8")
    manifest_doc: JsonVal = json.loads(manifest_text).raw
    manifest_obj = json.JsonValue(manifest_doc).as_obj()
    if manifest_obj is None:
        return []
    typed_manifest: dict[str, JsonVal] = manifest_obj.raw
    modules_raw: JsonVal = _jv_get(typed_manifest, "modules")
    modules_arr = json.JsonValue(modules_raw).as_arr()
    if modules_arr is None:
        return []
    manifest_dir: Path = _path_parent(manifest_path)
    result: list[dict[str, JsonVal]] = []
    index: int = 0
    while index < len(modules_arr.raw):
        entry: JsonVal = modules_arr.raw[index]
        entry_obj = json.JsonValue(entry).as_obj()
        if entry_obj is None:
            index += 1
            continue
        typed_entry: dict[str, JsonVal] = entry_obj.raw
        manifest_entry = ManifestModuleEntryDraft.from_jv(typed_entry, index)
        east_path: Path = manifest_dir.joinpath(manifest_entry.output)
        east_text: str = east_path.read_text(encoding="utf-8")
        east_doc: JsonVal = json.loads(east_text).raw
        east_obj = json.JsonValue(east_doc).as_obj()
        if east_obj is None:
            index += 1
            continue
        typed_east: dict[str, JsonVal] = east_obj.raw
        typed_east["meta"] = manifest_entry.build_cli_meta(typed_east)
        result.append(typed_east)
        index += 1
    return result


def run_emit_cli(
    emit_fn: EmitFn | None = None,
    argv: list[str] = [],
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
    argv_list: list[str] = argv
    parsed_args: tuple[str, str, str] = _parse_args(argv_list)
    input_text = parsed_args[0]
    output_dir_text = parsed_args[1]
    file_ext = parsed_args[2]
    if file_ext == "__pytra_help__":
        return 0
    if file_ext.startswith("__pytra_error__:"):
        print("error: " + file_ext[len("__pytra_error__:") :])
        return 1

    use_direct = direct_emit_fn is not None
    if not use_direct:
        if emit_fn is None:
            print("error: either emit_fn or direct_emit_fn must be provided")
            return 1
        if file_ext == "":
            file_ext = default_ext
        if file_ext == "":
            print("error: file extension must be specified via --ext or default_ext")
            return 1

    if input_text == "":
        print("error: manifest.json path or directory is required")
        return 1

    manifest_path: Path = Path(input_text)
    if _path_name(manifest_path) != "manifest.json":
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
        active_direct_emit_fn = direct_emit_fn
        for east_doc in modules:
            written = written + active_direct_emit_fn(east_doc, output_dir)
    else:
        active_emit_fn = emit_fn
        for east_doc in modules:
            code: str = active_emit_fn(east_doc)
            if code.strip() == "":
                continue
            meta: JsonVal = _jv_get(east_doc, "meta")
            module_id: str = ""
            meta_obj = json.JsonValue(meta).as_obj()
            if meta_obj is not None:
                mid = json.JsonValue(_jv_get(meta_obj.raw, "_cli_module_id")).as_str()
                if mid is not None:
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
