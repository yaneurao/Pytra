#!/usr/bin/env python3
"""Unified Pytra frontend: Python/EAST3 -> multi-target source."""

from __future__ import annotations

from typing import Any

from toolchain.compiler.typed_boundary import export_compiler_root_document
from toolchain.frontends.extern_var import validate_ambient_global_target_support
from toolchain.frontends import add_common_transpile_args
from toolchain.frontends import build_module_east_map
from toolchain.frontends import load_east3_document_typed
from toolchain.json_adapters import empty_json_object_doc
from toolchain.link import LINK_INPUT_SCHEMA
from toolchain.link import build_linked_program_from_module_map
from toolchain.link import LinkedProgram
from toolchain.link import load_linked_program
from toolchain.link import optimize_linked_program
from toolchain.link import write_link_input_bundle
from toolchain.link import write_link_output_bundle
from toolchain.link.program_loader import add_runtime_east_to_module_map
from pytra.std import argparse
from pytra.std import json
from pytra.std.pathlib import Path
from pytra.std import sys


_BACKEND_TARGETS = ["cpp", "rs", "cs", "js", "ts", "go", "java", "kotlin", "swift", "ruby", "lua", "scala", "php", "nim", "powershell"]

_TARGET_EXTENSIONS: dict[str, str] = {
    "cpp": ".cpp", "rs": ".rs", "cs": ".cs", "js": ".js", "ts": ".ts",
    "go": ".go", "java": ".java", "kotlin": ".kt", "swift": ".swift",
    "ruby": ".rb", "lua": ".lua", "scala": ".scala", "php": ".php",
    "nim": ".nim", "powershell": ".ps1",
}


def _default_output_path(input_path: Path, target: str) -> Path:
    ext = _TARGET_EXTENSIONS.get(target, "." + target)
    return Path("out") / (input_path.stem + ext)


def _arg_get_str(args: dict[str, Any], key: str, default_value: str = "") -> str:
    if key not in args:
        return default_value
    val = args[key]
    if isinstance(val, str):
        return val
    return default_value


def _fatal(msg: str) -> None:
    sys.write_stderr("error: " + msg + "\n")
    raise SystemExit(2)


def _print_help() -> None:
    print(
        "usage:\n"
        "  py2x.py compile INPUT.py [-o OUTPUT.east]                    Compile .py to .east (EAST3 JSON)\n"
        "  py2x.py link INPUT.east [INPUT2.east ...] --target TARGET [-o OUTPUT]  Link .east files to target language\n"
        "  py2x.py INPUT.py --target TARGET [-o OUTPUT]                 Legacy single-step mode\n"
        "\n"
        "options:\n"
        "  --target {cpp,rs,cs,js,ts,go,java,kotlin,swift,ruby,lua,scala,php,nim,powershell}\n"
        "  --east3-opt-level {0,1,2}  --east3-opt-pass SPEC\n"
        "  --dump-east3-dir DIR  --link-only  --from-link-output  --output-dir DIR\n"
        "  --lower-option key=value  --optimizer-option key=value  --emitter-option key=value\n"
        "\n"
        "note: for --target cpp, py2cpp compatibility flags are also accepted."
    )


def _extract_layer_options(argv: list[str]) -> tuple[list[str], dict[str, list[str]]]:
    cleaned: list[str] = []
    options: dict[str, list[str]] = {
        "lower": [],
        "optimizer": [],
        "emitter": [],
    }
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok == "--lower-option" or tok == "--optimizer-option" or tok == "--emitter-option":
            if i + 1 >= len(argv):
                _fatal("missing value for " + tok)
            val = argv[i + 1]
            if tok == "--lower-option":
                options["lower"].append(val)
            elif tok == "--optimizer-option":
                options["optimizer"].append(val)
            else:
                options["emitter"].append(val)
            i += 2
            continue
        cleaned.append(tok)
        i += 1
    return cleaned, options


def _peek_target(argv: list[str]) -> str:
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok == "--target":
            if i + 1 >= len(argv):
                _fatal("missing value for --target")
            return argv[i + 1]
        if tok.startswith("--target="):
            return tok[len("--target=") :]
        i += 1
    return ""



def _load_json_root(path: Path) -> json.JsonObj:
    try:
        payload = json.loads_obj(path.read_text(encoding="utf-8"))
    except Exception:
        return empty_json_object_doc()
    if payload is None:
        return empty_json_object_doc()
    return payload


def _write_generated_paths(paths: list[Path]) -> None:
    for path in paths:
        print("generated: " + str(path))


def _use_linked_program_route(target_hint: str, argv: list[str]) -> bool:
    # All targets now use the linked program route (compile -> link pipeline).
    _ = target_hint
    _ = argv
    return True




def _invoke_east2x_main(argv: list[str]) -> int:
    from toolchain.emit.all import main as _emit_main

    return _emit_main(argv)




def _parse_layer_option_items(items: list[str], label: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items:
        pos = item.find("=")
        if pos <= 0:
            _fatal(label + " must be key=value: " + item)
        key = item[:pos]
        value = item[pos + 1 :]
        if key == "":
            _fatal(label + " key must not be empty")
        out[key] = value
    return out


def _build_linked_program_for_input(
    input_path: Path,
    *,
    parser_backend: str,
    object_dispatch_mode: str,
    east3_opt_level: str,
    east3_opt_pass: str,
    dump_east3_before_opt: str,
    dump_east3_after_opt: str,
    dump_east3_opt_trace: str,
    target_lang: str,
) -> LinkedProgram:
    def _load_for_program(
        module_path: Path,
        parser_backend: str = "self_hosted",
        east_stage: str = "3",
        object_dispatch_mode: str = "",
    ) -> dict[str, object]:
        _ = east_stage
        enable_dump = module_path.resolve() == input_path.resolve()
        return export_compiler_root_document(
            load_east3_document_typed(
                module_path,
                parser_backend=parser_backend,
                object_dispatch_mode=object_dispatch_mode,
                east3_opt_level=east3_opt_level,
                east3_opt_pass=east3_opt_pass,
                dump_east3_before_opt=dump_east3_before_opt if enable_dump else "",
                dump_east3_after_opt=dump_east3_after_opt if enable_dump else "",
                dump_east3_opt_trace=dump_east3_opt_trace if enable_dump else "",
                target_lang=target_lang,
            )
        )

    input_txt = str(input_path)
    module_map: dict[str, dict[str, object]] = {}
    if input_txt.endswith(".py"):
        module_map = build_module_east_map(
            input_path,
            _load_for_program,
            parser_backend=parser_backend,
            east_stage="3",
            object_dispatch_mode=object_dispatch_mode,
        )
    elif input_txt.endswith(".json"):
        root = _load_json_root(input_path)
        if root.get_str("schema") == LINK_INPUT_SCHEMA:
            return load_linked_program(input_path)
        module_map = {
            str(input_path.resolve()): _load_for_program(
                input_path,
                parser_backend=parser_backend,
                east_stage="3",
                object_dispatch_mode=object_dispatch_mode,
            )
        }
    else:
        module_map = {
            str(input_path.resolve()): _load_for_program(
                input_path,
                parser_backend=parser_backend,
                east_stage="3",
                object_dispatch_mode=object_dispatch_mode,
            )
        }

    # Add runtime .east files for imported runtime modules (transitive closure).
    module_map = add_runtime_east_to_module_map(module_map)

    return build_linked_program_from_module_map(
        input_path,
        module_map,
        target=target_lang,
        dispatch_mode=object_dispatch_mode,
        options={
            "east3_opt_level": east3_opt_level,
            "east3_opt_pass": east3_opt_pass,
        },
    )



def _entry_module_east_doc(program: LinkedProgram) -> dict[str, object]:
    entry_module_ids = set(program.entry_modules)
    for module in program.modules:
        if module.is_entry and module.module_id in entry_module_ids:
            return module.east_doc
    raise RuntimeError("linked program entry module not found")


def _compile_to_east(argv: list[str]) -> int:
    """pytra compile: .py → .east (EAST3 JSON)"""
    parser = argparse.ArgumentParser(description="Compile .py to .east (EAST3 JSON)")
    parser.add_argument("input", help="Input .py file")
    parser.add_argument("-o", "--output", default="", help="Output .east file (default: INPUT.east)")
    parser.add_argument("--east3-opt-level", default="1", help="EAST3 optimization level")
    parser.add_argument("--east3-opt-pass", default="", help="EAST3 optimization pass spec")
    args = parser.parse_args(argv)
    if not isinstance(args, dict):
        raise RuntimeError("argparse result must be dict")

    input_path = Path(_arg_get_str(args, "input"))
    output_text = _arg_get_str(args, "output")
    if output_text == "":
        output_text = str(input_path).removesuffix(".py") + ".east"
    output_path = Path(output_text)
    east3_opt_level = _arg_get_str(args, "east3_opt_level", "1")
    east3_opt_pass = _arg_get_str(args, "east3_opt_pass")

    east_doc = export_compiler_root_document(
        load_east3_document_typed(
            input_path,
            parser_backend="self_hosted",
            object_dispatch_mode="native",
            east3_opt_level=east3_opt_level,
            east3_opt_pass=east3_opt_pass,
            dump_east3_before_opt="",
            dump_east3_after_opt="",
            dump_east3_opt_trace="",
            target_lang="",
        )
    )
    import json as _json
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        _json.dumps(east_doc, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    print("compiled: " + str(output_path))
    return 0


def _link_east_files(argv: list[str]) -> int:
    """pytra link: .east 群 → ターゲット言語。
    .east ファイルから link-input bundle を構築し、既存の linked program 経路で emit する。
    """
    # 引数を手動パース（最初の .east ファイル群、--target、-o）
    input_paths: list[Path] = []
    target = "cpp"
    output_text = ""
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok == "--target" and i + 1 < len(argv):
            target = argv[i + 1]
            i += 2
            continue
        if tok == "-o" and i + 1 < len(argv):
            output_text = argv[i + 1]
            i += 2
            continue
        if tok.endswith(".east") or tok.endswith(".json"):
            input_paths.append(Path(tok))
        i += 1
    if len(input_paths) == 0:
        _fatal("no .east input files specified")

    # 各 .east を読み込んで module_map を構築
    import json as _json
    module_map: dict[str, dict[str, object]] = {}
    entry_source_path: str = ""
    for east_path in input_paths:
        east_text = east_path.read_text(encoding="utf-8")
        east_doc = _json.loads(east_text)
        source_path = east_doc.get("source_path", "")
        key = source_path if isinstance(source_path, str) and source_path != "" else str(east_path.resolve())
        module_map[key] = east_doc
        if entry_source_path == "":
            entry_source_path = key
    entry_path = Path(entry_source_path)

    program = build_linked_program_from_module_map(
        entry_path,
        module_map,
        target=target,
        dispatch_mode="native",
        options={},
    )

    # link-output を書き出し、east2x 経由で emit（C++ の場合）
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        link_output_dir = Path(tmpdir) / "linked"
        link_output_path, linked_paths = write_link_output_bundle(
            link_output_dir, optimize_linked_program(program),
        )
        # east2x に link-output.json を渡して emit
        forwarded = [str(link_output_path), "--target", target]
        if output_text != "":
            forwarded.extend(["-o", output_text])
        return _invoke_east2x_main(forwarded)


def main() -> int:
    argv = sys.argv[1:] if isinstance(sys.argv, list) else []
    for arg in argv:
        if arg == "-h" or arg == "--help":
            _print_help()
            return 0

    # サブコマンド: compile / link
    if len(argv) > 0 and argv[0] == "compile":
        return _compile_to_east(argv[1:])
    if len(argv) > 0 and argv[0] == "link":
        return _link_east_files(argv[1:])

    cleaned_argv, layer_option_items = _extract_layer_options(argv)
    target_hint = _peek_target(cleaned_argv)
    if _use_linked_program_route(target_hint, cleaned_argv) is False:
        return _run_cpp_compat(cleaned_argv, layer_option_items=layer_option_items)

    parser = argparse.ArgumentParser(description="Pytra unified transpiler frontend")
    add_common_transpile_args(
        parser,
        parser_backends=["self_hosted"],
        enable_object_dispatch_mode=True,
    )
    parser.add_argument("--target", choices=_BACKEND_TARGETS, help="Target backend language")
    parser.add_argument("--east-stage", choices=["2", "3"], help="EAST stage mode (default: 3)")
    parser.add_argument("--dump-east3-dir", help="Write raw EAST3 modules + link-input.json to DIR and exit")
    parser.add_argument("--link-only", action="store_true", help="Write link-output.json + linked modules to --output-dir and exit")
    parser.add_argument("--from-link-output", action="store_true", help="Treat INPUT.json as link-output.json and restart backend emit")
    parser.add_argument("--output-dir", help="Output directory for linked-program artifacts")
    args = parser.parse_args(cleaned_argv)
    if not isinstance(args, dict):
        raise RuntimeError("argparse result must be dict")

    target = _arg_get_str(args, "target")
    if target == "":
        _fatal("--target is required")

    input_path = Path(_arg_get_str(args, "input"))
    dump_east3_dir = _arg_get_str(args, "dump_east3_dir")
    link_only = bool(args.get("link_only", False))
    from_link_output = bool(args.get("from_link_output", False))
    output_dir_txt = _arg_get_str(args, "output_dir")
    if dump_east3_dir != "" and link_only:
        _fatal("--dump-east3-dir and --link-only cannot be combined")
    if from_link_output and (dump_east3_dir != "" or link_only):
        _fatal("--from-link-output cannot be combined with --dump-east3-dir or --link-only")
    output_text = _arg_get_str(args, "output")

    parser_backend = _arg_get_str(args, "parser_backend")
    if parser_backend == "":
        parser_backend = "self_hosted"

    east_stage = _arg_get_str(args, "east_stage")
    if east_stage == "":
        east_stage = "3"
    if east_stage == "2":
        _fatal("--east-stage 2 is no longer supported; use EAST3 (default).")

    object_dispatch_mode = _arg_get_str(args, "object_dispatch_mode")
    if object_dispatch_mode == "":
        object_dispatch_mode = "native"

    east3_opt_level = _arg_get_str(args, "east3_opt_level")
    if east3_opt_level == "":
        east3_opt_level = "1"
    east3_opt_pass = _arg_get_str(args, "east3_opt_pass")
    dump_east3_before_opt = _arg_get_str(args, "dump_east3_before_opt")
    dump_east3_after_opt = _arg_get_str(args, "dump_east3_after_opt")
    dump_east3_opt_trace = _arg_get_str(args, "dump_east3_opt_trace")
    if from_link_output:
        forwarded = [str(input_path), "--target", target]
        if output_text != "":
            forwarded.extend(["-o", output_text])
        if output_dir_txt != "":
            forwarded.extend(["--output-dir", output_dir_txt])
        for item in layer_option_items["lower"]:
            forwarded.extend(["--lower-option", item])
        for item in layer_option_items["optimizer"]:
            forwarded.extend(["--optimizer-option", item])
        for item in layer_option_items["emitter"]:
            forwarded.extend(["--emitter-option", item])
        return _invoke_east2x_main(forwarded)
    target_lang = target
    program = _build_linked_program_for_input(
        input_path,
        parser_backend=parser_backend,
        object_dispatch_mode=object_dispatch_mode,
        east3_opt_level=east3_opt_level,
        east3_opt_pass=east3_opt_pass,
        dump_east3_before_opt=dump_east3_before_opt,
        dump_east3_after_opt=dump_east3_after_opt,
        dump_east3_opt_trace=dump_east3_opt_trace,
        target_lang=target_lang,
    )
    for linked_module in program.modules:
        validate_ambient_global_target_support(linked_module.east_doc, target=target)
    if dump_east3_dir != "":
        manifest_path, module_paths = write_link_input_bundle(Path(dump_east3_dir), program)
        _write_generated_paths([manifest_path] + module_paths)
        return 0
    if link_only:
        output_dir = Path(output_dir_txt) if output_dir_txt != "" else Path("out/linked")
        link_output_path, linked_paths = write_link_output_bundle(output_dir, optimize_linked_program(program))
        _write_generated_paths([link_output_path] + linked_paths)
        return 0

    # compile → link → link-only output, then emit via subprocess (east2cpp / east2x).
    # This keeps py2x.py free of backend_registry dependencies.
    # compile → link → link-only output, then emit via subprocess (east2cpp / east2x).
    # This keeps py2x.py free of backend_registry dependencies.
    import subprocess as _subprocess
    import tempfile as _tempfile
    import sys as _stdlib_sys

    _python = _stdlib_sys.executable or "python3"
    _src_dir = str(Path(__file__).resolve().parent)

    opt_result = optimize_linked_program(program)
    with _tempfile.TemporaryDirectory() as tmpdir:
        link_output_dir = Path(tmpdir) / "linked"
        link_output_path, _ = write_link_output_bundle(link_output_dir, opt_result)

        output_path_txt = output_text if output_text != "" else str(_default_output_path(input_path, target))

        if target == "cpp":
            # C++ emit via toolchain/emit/cpp.py (imports only C++ backend)
            emit_cmd = [_python, _src_dir + "/toolchain/emit/cpp.py", str(link_output_path)]
            if output_dir_txt != "":
                emit_cmd.extend(["--output-dir", output_dir_txt])
            else:
                emit_cmd.extend(["--output-dir", str(Path(output_path_txt).parent)])
            for item in layer_option_items["emitter"]:
                emit_cmd.extend(["--emitter-option", item])
        else:
            # All other targets via toolchain/emit/all.py
            emit_cmd = [_python, _src_dir + "/toolchain/emit/all.py",
                        str(link_output_path), "--target", target]
            if output_path_txt != "":
                emit_cmd.extend(["-o", output_path_txt])
            if output_dir_txt != "":
                emit_cmd.extend(["--output-dir", output_dir_txt])
            for item in layer_option_items["lower"]:
                emit_cmd.extend(["--lower-option", item])
            for item in layer_option_items["optimizer"]:
                emit_cmd.extend(["--optimizer-option", item])
            for item in layer_option_items["emitter"]:
                emit_cmd.extend(["--emitter-option", item])

        import os as _os
        emit_env = dict(_os.environ)
        emit_env["PYTHONPATH"] = _src_dir + (_os.pathsep + emit_env.get("PYTHONPATH", "")) if emit_env.get("PYTHONPATH") else _src_dir
        proc = _subprocess.run(emit_cmd, text=True, env=emit_env)
        return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
