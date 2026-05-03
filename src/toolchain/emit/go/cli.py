"""Go backend CLI: manifest.json -> Go multi-file output.

selfhost-safe: does not depend on typing.Callable. The C++ selfhost path
cannot currently compile the shared cli_runner Callable aliases.
"""
from __future__ import annotations

from pytra.std import json
from pytra.std.json import JsonVal
from pytra.std.pathlib import Path

from toolchain.emit.go.emitter import emit_go_module


def _jv_obj(value: JsonVal) -> dict[str, JsonVal]:
    if isinstance(value, dict):
        obj: dict[str, JsonVal] = value
        return obj
    return {}


def _jv_list(value: JsonVal) -> list[JsonVal]:
    if isinstance(value, list):
        items: list[JsonVal] = value
        return items
    return []


def _jv_str(value: JsonVal) -> str:
    if isinstance(value, str):
        text: str = value
        return text
    return ""


def _jv_bool(value: JsonVal) -> bool:
    if isinstance(value, bool):
        flag: bool = value
        return flag
    return False


def _parse_args(argv: list[str]) -> tuple[str, str, str, str]:
    input_text: str = ""
    output_dir_text: str = ""
    file_ext: str = ""
    target_text: str = "go"
    i: int = 0
    while i < len(argv):
        tok: str = argv[i]
        if tok == "-emit":
            i += 1
            continue
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
        if tok == "--target" or tok.startswith("--target="):
            if "=" in tok:
                target_text = tok.split("=", 1)[1]
                i += 1
            else:
                if i + 1 >= len(argv):
                    raise RuntimeError("missing value for --target")
                target_text = argv[i + 1]
                i += 2
            continue
        if tok == "-h" or tok == "--help":
            print("usage: python3 -m toolchain.emit.go.cli [-emit] MANIFEST_DIR_OR_EAST3_JSON [-o OUTPUT_DIR] [--target go] [--ext .EXT]")
            raise SystemExit(0)
        if not tok.startswith("-") and input_text == "":
            input_text = tok
        i += 1
    return input_text, output_dir_text, file_ext, target_text


def _load_linked_modules(manifest_path: Path) -> list[dict[str, JsonVal]]:
    manifest_text: str = manifest_path.read_text(encoding="utf-8")
    manifest_doc: JsonVal = json.loads(manifest_text).raw
    typed_manifest = _jv_obj(manifest_doc)
    if len(typed_manifest) == 0:
        raise RuntimeError("manifest root must be object: " + str(manifest_path))
    modules = _jv_list(typed_manifest.get("modules"))
    if len(modules) == 0:
        raise RuntimeError("manifest.modules must be list")
    manifest_dir: Path = manifest_path.parent
    result: list[dict[str, JsonVal]] = []
    for index, entry in enumerate(modules):
        typed_entry = _jv_obj(entry)
        if len(typed_entry) == 0:
            raise RuntimeError("manifest.modules[" + str(index) + "] must be object")
        output_rel = _jv_str(typed_entry.get("output"))
        if output_rel == "":
            raise RuntimeError("manifest.modules[" + str(index) + "].output must be non-empty string")
        east_path: Path = manifest_dir.joinpath(output_rel)
        east_text: str = east_path.read_text(encoding="utf-8")
        east_doc: JsonVal = json.loads(east_text).raw
        typed_east = _jv_obj(east_doc)
        if len(typed_east) == 0:
            raise RuntimeError("linked EAST root must be object: " + str(east_path))
        typed_meta = _jv_obj(typed_east.get("meta"))
        if len(typed_meta) == 0:
            empty_meta: dict[str, JsonVal] = {}
            typed_meta = empty_meta
            typed_east["meta"] = typed_meta
        module_id = _jv_str(typed_entry.get("module_id"))
        if module_id != "":
            typed_meta["_cli_module_id"] = module_id
        module_kind = _jv_str(typed_entry.get("module_kind"))
        if module_kind != "":
            typed_meta["_cli_module_kind"] = module_kind
        is_entry = _jv_bool(typed_entry.get("is_entry"))
        if is_entry:
            typed_meta["_cli_is_entry"] = is_entry
        source_path = _jv_str(typed_entry.get("source_path"))
        if source_path != "":
            typed_meta["_cli_source_path"] = source_path
        result.append(typed_east)
    return result


def _load_single_east3_module(east_path: Path) -> list[dict[str, JsonVal]]:
    east_text: str = east_path.read_text(encoding="utf-8")
    east_doc: JsonVal = json.loads(east_text).raw
    typed_east = _jv_obj(east_doc)
    if len(typed_east) == 0:
        raise RuntimeError("EAST3 root must be object: " + str(east_path))
    return [typed_east]


def _module_id_from_doc(east_doc: dict[str, JsonVal], fallback_index: int) -> str:
    meta = _jv_obj(east_doc.get("meta"))
    mid = _jv_str(meta.get("_cli_module_id"))
    if mid != "":
        return mid
    mid = _jv_str(meta.get("module_id"))
    if mid != "":
        return mid
    return "module_" + str(fallback_index)


def _repo_root() -> Path:
    cwd = Path.cwd()
    if cwd.joinpath("src").joinpath("runtime").joinpath("go").exists():
        return cwd
    nested = cwd.joinpath("Pytra")
    if nested.joinpath("src").joinpath("runtime").joinpath("go").exists():
        return nested
    return cwd


def _copy_go_runtime_files(output_dir: Path) -> int:
    runtime_root = _repo_root().joinpath("src").joinpath("runtime").joinpath("go")
    copied: int = 0
    for bucket in ["built_in", "std"]:
        bucket_dir = runtime_root.joinpath(bucket)
        if not bucket_dir.exists():
            continue
        for go_file in bucket_dir.glob("*.go"):
            dst = output_dir.joinpath(go_file.name)
            dst.write_text(go_file.read_text(encoding="utf-8"), encoding="utf-8")
            copied += 1
    output_dir.joinpath("go.mod").write_text(
        "module pytra_selfhost_go\n\ngo 1.22\n",
        encoding="utf-8",
    )
    return copied


def main(argv: list[str]) -> int:
    parsed_args = _parse_args(argv)
    input_text = parsed_args[0]
    output_dir_text = parsed_args[1]
    file_ext = parsed_args[2]
    target_text = parsed_args[3]
    if file_ext == "":
        file_ext = ".go"
    if input_text == "":
        print("error: manifest.json path or directory is required")
        return 1
    if target_text != "go":
        print("error: Go selfhost emitter only supports --target go")
        return 1
    if output_dir_text == "":
        output_dir_text = str(Path("work").joinpath("tmp").joinpath("emit"))
    output_dir: Path = Path(output_dir_text)
    output_dir.mkdir(parents=True, exist_ok=True)

    input_path: Path = Path(input_text)
    manifest_path: Path = input_path.joinpath("manifest.json")
    if manifest_path.exists():
        modules = _load_linked_modules(manifest_path)
    elif input_path.name == "manifest.json" and input_path.exists():
        modules = _load_linked_modules(input_path)
    elif input_path.exists():
        modules = _load_single_east3_module(input_path)
    else:
        print("error: manifest.json or EAST3 JSON not found: " + input_text)
        return 1

    written: int = 0
    for east_doc in modules:
        code = emit_go_module(east_doc)
        if code.strip() == "":
            continue
        module_id = _module_id_from_doc(east_doc, written)
        out_name = module_id.replace(".", "_") + file_ext
        output_dir.joinpath(out_name).write_text(code, encoding="utf-8")
        written += 1

    _copy_go_runtime_files(output_dir)
    print("emitted: " + str(output_dir) + " (" + str(written) + " files)")
    return 0


if __name__ == "__main__":
    import sys
    cli_argv: list[str] = []
    arg_index = 1
    while arg_index < len(sys.argv):
        cli_argv.append(sys.argv[arg_index])
        arg_index += 1
    exit_code = main(cli_argv)
    if exit_code != 0:
        raise SystemExit(exit_code)
