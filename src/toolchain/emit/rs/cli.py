#!/usr/bin/env python3
"""Rust backend CLI: manifest.json -> Rust multi-file output."""

from __future__ import annotations

from pytra.std.json import JsonVal
from pytra.std import json
from pytra.std.pathlib import Path

from toolchain.emit.common.cli_runner import run_emit_cli
from toolchain.emit.rs.emitter import emit_rs_module


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _copy_rs_runtime_files(dst_dir: Path) -> int:
    runtime_root = _repo_root().joinpath("src").joinpath("runtime").joinpath("rs")
    copied = 0
    sources = [
        runtime_root.joinpath("built_in").joinpath("py_runtime.rs"),
        runtime_root.joinpath("std").joinpath("time_native.rs"),
        runtime_root.joinpath("std").joinpath("math_native.rs"),
    ]
    for src in sources:
        if not src.exists():
            continue
        dst = dst_dir.joinpath(src.name)
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        copied += 1
    return copied


def _resolve_manifest_path(argv: list[str]) -> Path:
    input_text = ""
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok in ("-o", "--output-dir", "--ext"):
            i += 2
            continue
        if tok in ("-h", "--help", "--package"):
            i += 1
            continue
        if not tok.startswith("-") and input_text == "":
            input_text = tok
        i += 1
    if input_text == "":
        return Path("")
    manifest_path = Path(input_text)
    if manifest_path.name != "manifest.json":
        manifest_path = manifest_path.joinpath("manifest.json")
    return manifest_path


def _strip_package_flag(argv: list[str]) -> tuple[list[str], bool]:
    cleaned: list[str] = []
    package_mode = False
    for tok in argv:
        if tok == "--package":
            package_mode = True
            continue
        cleaned.append(tok)
    return cleaned, package_mode


def _write_rs_package_files(output_dir: Path, manifest_path: Path) -> None:
    src_dir = output_dir.joinpath("src")
    src_dir.mkdir(parents=True, exist_ok=True)

    module_names: list[str] = []
    for mod_file in output_dir.glob("*.rs"):
        dst = src_dir.joinpath(mod_file.name)
        dst.write_text(mod_file.read_text(encoding="utf-8"), encoding="utf-8")
        module_name = mod_file.stem
        if module_name not in module_names:
            module_names.append(module_name)

    _copy_rs_runtime_files(src_dir)
    for runtime_mod in ["py_runtime", "time_native", "math_native"]:
        if runtime_mod not in module_names:
            module_names.append(runtime_mod)

    entry_mod = ""
    manifest_doc: JsonVal = json.loads(manifest_path.read_text(encoding="utf-8")).raw
    if isinstance(manifest_doc, dict):
        modules = manifest_doc.get("modules")
        if isinstance(modules, list):
            for module in modules:
                if not isinstance(module, dict):
                    continue
                is_entry = module.get("is_entry")
                if isinstance(is_entry, bool) and is_entry:
                    module_id_any = module.get("module_id")
                    module_id = module_id_any if isinstance(module_id_any, str) else ""
                    if module_id != "":
                        entry_mod = module_id.replace(".", "_")
                        break
    if entry_mod == "":
        raise RuntimeError("missing entry module for Rust package emit")

    lib_lines = ["pub mod " + mod_name + ";" for mod_name in sorted(set(module_names))]
    src_dir.joinpath("lib.rs").write_text("\n".join(lib_lines) + "\n", encoding="utf-8")

    main_src = "fn main() {\n"
    main_src += "    pytra_selfhost::" + entry_mod + "::main();\n"
    main_src += "}\n"
    src_dir.joinpath("main.rs").write_text(main_src, encoding="utf-8")

    cargo_src = "[package]\n"
    cargo_src += "name = \"pytra_selfhost\"\n"
    cargo_src += "version = \"0.1.0\"\n"
    cargo_src += "edition = \"2021\"\n\n"
    cargo_src += "[lib]\n"
    cargo_src += "name = \"pytra_selfhost\"\n"
    cargo_src += "path = \"src/lib.rs\"\n\n"
    cargo_src += "[[bin]]\n"
    cargo_src += "name = \"pytra_selfhost\"\n"
    cargo_src += "path = \"src/main.rs\"\n"
    output_dir.joinpath("Cargo.toml").write_text(cargo_src, encoding="utf-8")


def emit_rs_from_manifest(manifest_path: Path, output_dir: Path, *, package_mode: bool = False) -> int:
    argv = [str(manifest_path), "--output-dir", str(output_dir)]
    if package_mode:
        argv.append("--package")
    return main(argv)


def main(argv: list[str]) -> int:
    args: list[str] = []
    for item in argv:
        args.append(item)
    if "-h" in args or "--help" in args:
        print("usage: python3 -m toolchain.emit.rs.cli MANIFEST.json [-o OUTPUT_DIR] [--package]")
        return 0

    cleaned_argv, package_mode = _strip_package_flag(args)
    manifest_path = _resolve_manifest_path(cleaned_argv)

    def _emit_rs(east_doc: dict[str, JsonVal]) -> str:
        return emit_rs_module(east_doc, package_mode=package_mode)

    def _post_emit(output_dir: Path) -> None:
        if package_mode:
            _write_rs_package_files(output_dir, manifest_path)
            return
        _copy_rs_runtime_files(output_dir)

    return run_emit_cli(_emit_rs, cleaned_argv, default_ext=".rs", post_emit=_post_emit)


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
