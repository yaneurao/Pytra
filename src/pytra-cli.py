#!/usr/bin/env python3
"""pytra-cli: 新パイプライン CLI (parse / resolve / compile / optimize / emit).

設計文書: docs/ja/plans/plan-pipeline-redesign.md

パイプライン:
  -parse      .py → .py.east1         Python 構文解析
  -resolve    *.py.east1 → *.east2    型解決 + 正規化 (言語固有→言語非依存)
  -compile    *.east2 → *.east3       core lowering (言語非依存)
  -optimize   *.east3 → *.east3       whole-program 最適化
  -link       *.east3 → manifest.json multi-module 結合
  -emit       *.east3 → *.cpp 等      target コード生成
  -build      .py → target            一括実行

selfhost 対象 (§5.7): toolchain/ + pytra.std.* のみ使用。
golden file 生成は tools/gen/generate_golden.py に分離。
"""

from __future__ import annotations

from pytra.std import sys
from pytra.std import json
from pytra.types import int64
from pytra.std import subprocess as py_subprocess
from pytra.std.json import JsonVal
from pytra.std.pathlib import Path
from pytra.typing import cast
from toolchain.common.jv import deep_copy_json
from toolchain.compile.lower import lower_east2_to_east3
from toolchain.link.linker import LinkResult
from toolchain.link.linker import link_modules
from toolchain.link.shared_types import LinkedModule
from toolchain.link.shared_types import linked_module_id
from toolchain.link.shared_types import linked_module_is_entry
from toolchain.link.shared_types import linked_module_mark_non_entry
from toolchain.link.shared_types import linked_module_source_path
from toolchain.optimize.optimizer import optimize_east3_doc_only
from toolchain.optimize.optimizer import resolve_bounds_check_mode
from toolchain.optimize.optimizer import resolve_negative_index_mode
from toolchain.parse.py.parse_python import parse_python_file
from toolchain.resolve.py.builtin_registry import load_builtin_registry
from toolchain.resolve.py.resolver import east2_output_path_from_east1
from toolchain.resolve.py.resolver import resolve_east1_to_east2
from toolchain.resolve.py.resolver import resolve_file


def _repo_root() -> Path:
    """Return repository root from the current working directory.

    Selfhost binaries may run from /workspace, so fall back to ./Pytra when present.
    """
    cwd = Path.cwd()
    if cwd.joinpath("src").exists():
        return cwd
    if cwd.joinpath("Pytra").joinpath("src").exists():
        return cwd.joinpath("Pytra")
    return cwd


def _unsupported_target_attr(module_name: str, attr_name: str) -> None:
    raise RuntimeError("selfhost-safe dynamic load is unavailable for " + module_name + "." + attr_name)


def _src_dir() -> Path:
    return _repo_root().joinpath("src")


def _python() -> str:
    return "python3"


def _subprocess_env() -> dict[str, str]:
    env: dict[str, str] = {}
    env["PYTHONPATH"] = str(_src_dir())
    return env


def _run_subprocess(cmd: list[str]) -> int:
    result = py_subprocess.run(cmd, "", False, _subprocess_env())
    return result.returncode


def _emit_target_subprocess(target: str, manifest_path: Path, output_dir: Path) -> int:
    """Emit via subprocess: python3 -m toolchain.emit.<target>.cli manifest -o dir."""
    cmd = [_python(), "-m", "toolchain.emit." + target + ".cli", str(manifest_path), "--output-dir", str(output_dir)]
    return _run_subprocess(cmd)



def _emit_rs_module(_east_doc: dict[str, JsonVal], package_mode: bool = False) -> str:
    _ = package_mode
    _unsupported_target_attr("toolchain.emit.rs.emitter", "emit_rs_module")
    return ""


def _emit_nim_module(_east_doc: dict[str, JsonVal]) -> str:
    _unsupported_target_attr("toolchain.emit.nim.emitter", "emit_nim_module")
    return ""


def _emit_ts_module(_east_doc: dict[str, JsonVal], strip_types: bool = False) -> str:
    _ = strip_types
    _unsupported_target_attr("toolchain.emit.ts.emitter", "emit_ts_module")
    return ""



def _builtin_registry_paths() -> tuple[Path, Path, Path, Path]:
    """Return absolute builtins/containers/containers source/stdlib registry inputs."""
    root = _repo_root()
    east1_root = root.joinpath("test").joinpath("include").joinpath("east1").joinpath("py")
    return (
        east1_root.joinpath("built_in").joinpath("builtins.py.east1"),
        east1_root.joinpath("built_in").joinpath("containers.py.east1"),
        root.joinpath("src").joinpath("pytra").joinpath("built_in").joinpath("containers.py"),
        east1_root.joinpath("std"),
    )


def _copy_go_runtime_files(output_dir: Path) -> int:
    """Copy native Go runtime files into the flat emit directory."""
    runtime_root = _repo_root().joinpath("src").joinpath("runtime").joinpath("go")
    copied = 0
    for bucket in ["built_in", "std"]:
        for go_file in runtime_root.joinpath(bucket).glob("*.go"):
            dst = output_dir.joinpath(_path_text_name(go_file))
            dst.write_text(go_file.read_text(encoding="utf-8"), encoding="utf-8")
            copied += 1
    output_dir.joinpath("go.mod").write_text(
        "module pytra_selfhost_go\n\ngo 1.22\n",
        encoding="utf-8",
    )
    return copied



def _copy_java_runtime_files(output_dir: Path) -> int:
    """Copy Java runtime files into the flat emit directory."""
    runtime_root = _repo_root().joinpath("src").joinpath("runtime").joinpath("java")
    copied = 0
    if not runtime_root.exists():
        return copied
    for bucket in ["built_in", "std"]:
        bucket_dir = runtime_root.joinpath(bucket)
        if not bucket_dir.exists():
            continue
        for java_file in bucket_dir.glob("*.java"):
            dst = output_dir.joinpath(_path_text_name(java_file))
            dst.write_text(java_file.read_text(encoding="utf-8"), encoding="utf-8")
            copied += 1
    return copied



def _path_text_name(path: Path) -> str:
    text = str(path)
    slash = text.rfind("/")
    if slash >= 0:
        return text[slash + 1:]
    return text


def _path_text_stem(path: Path) -> str:
    name = _path_text_name(path)
    dot = name.rfind(".")
    if dot > 0:
        return name[:dot]
    return name


def _ensure_parent_dir(path: Path) -> None:
    text = str(path)
    slash = text.rfind("/")
    if slash < 0:
        return
    parent_text = text[:slash]
    if parent_text == "":
        return
    Path(parent_text).mkdir(parents=True, exist_ok=True)


def _module_source_path(module_id: str) -> Path:
    """Resolve a user module_id like toolchain.parse.py.parse_python to src path."""
    src_root = _repo_root().joinpath("src")
    module_path = src_root.joinpath(module_id.replace(".", "/") + ".py")
    if module_path.exists():
        return module_path
    package_init = src_root.joinpath(module_id.replace(".", "/")).joinpath("__init__.py")
    if package_init.exists():
        return package_init
    return Path("")


def _copy_json_doc(doc: dict[str, JsonVal]) -> dict[str, JsonVal]:
    _copied_raw = deep_copy_json(doc)
    _ = _copied_raw
    return doc


def _dump_json_doc(doc: JsonVal, indent: int64 | None = None) -> str:
    key_sep = ":" if indent is None else ": "
    return json._dump_json_value(doc, True, indent, ",", key_sep, 0)


def _module_stem_from_source_path(source_path: str, fallback_input: str) -> str:
    if source_path != "" and "/src/toolchain/" in source_path:
        idx = source_path.index("/src/toolchain/")
        rel = source_path[idx + len("/src/"):]
        if rel.endswith(".py"):
            rel = rel[:-3]
        return rel.replace("/", ".")
    if source_path.startswith("src/toolchain/"):
        rel = source_path[len("src/"):]
        if rel.endswith(".py"):
            rel = rel[:-3]
        return rel.replace("/", ".")
    return _path_text_stem(Path(fallback_input))


def _lower_cpp_doc(east2_doc: dict[str, JsonVal]) -> dict[str, JsonVal]:
    lowered_doc: dict[str, JsonVal] = lower_east2_to_east3(east2_doc, target_language="cpp")
    return lowered_doc


def _optimize_cpp_doc(east3_doc: dict[str, JsonVal]) -> dict[str, JsonVal]:
    optimized_doc: dict[str, JsonVal] = optimize_east3_doc_only(
        east3_doc,
        1,
        "",
        "",
        _optimizer_debug_flags(1, "", ""),
    )
    return optimized_doc


def _optimizer_debug_flags(
    opt_level: int,
    negative_index_mode: str,
    bounds_check_mode: str,
) -> dict[str, JsonVal]:
    return {
        "negative_index_mode": resolve_negative_index_mode(negative_index_mode, opt_level),
        "bounds_check_mode": resolve_bounds_check_mode(bounds_check_mode, opt_level),
    }


def _optimize_linked_runtime_modules(
    linked_modules: list[LinkedModule],
    *,
    opt_level: int,
    debug_flags: dict[str, JsonVal],
) -> None:
    for module in linked_modules:
        if module.module_kind not in ("runtime", "helper"):
            continue
        module.east_doc = optimize_east3_doc_only(
            module.east_doc,
            opt_level,
            "",
            "",
            debug_flags,
        )


def _demote_non_entry_module(module: LinkedModule, entry_abs: str) -> None:
    source_path: str = linked_module_source_path(module)
    sp_abs = str(Path(source_path).resolve()) if source_path != "" else ""
    if not linked_module_is_entry(module) or sp_abs == entry_abs:
        return
    module.is_entry = False
    linked_module_mark_non_entry(module)


def _linked_module_entry_path(module: LinkedModule) -> Path:
    source_path: str = linked_module_source_path(module)
    if source_path != "":
        return Path(source_path)
    return Path(linked_module_id(module) + ".py")


def _collect_build_sources(inputs: list[str]) -> list[tuple[str, dict[str, JsonVal]]]:
    """Parse entry inputs plus local user-module dependencies recursively."""
    pending: list[Path] = []
    for inp in inputs:
        pending.append(Path(inp).resolve())

    ordered: list[tuple[str, dict[str, JsonVal]]] = []
    seen: set[str] = set()

    while len(pending) > 0:
        current = pending.pop(0)
        current_key = str(current)
        if current_key in seen:
            continue
        if not current.exists():
            raise RuntimeError("file not found: " + current_key)
        east1_doc = parse_python_file(current_key)
        ordered.append((current_key, east1_doc))
        seen.add(current_key)

        meta = json.JsonObj(east1_doc).get_obj("meta")
        if meta is None:
            continue
        import_resolution = meta.get_obj("import_resolution")
        if import_resolution is None:
            continue
        bindings = import_resolution.get_arr("bindings")
        if bindings is None:
            continue
        for binding in bindings.raw:
            binding_node = json.JsonValue(binding).as_obj()
            if binding_node is None:
                continue
            module_id_text_opt = binding_node.get_str("module_id")
            if module_id_text_opt is None:
                continue
            module_id_text = cast(str, module_id_text_opt)
            if module_id_text == "" or module_id_text.startswith("pytra."):
                continue
            dep_path = _module_source_path(module_id_text)
            dep_key = str(dep_path.resolve()) if str(dep_path) != "" else ""
            if dep_key != "" and dep_key not in seen:
                pending.append(dep_path.resolve())

    return ordered


# ---------------------------------------------------------------------------
# parse: .py → .py.east1
# ---------------------------------------------------------------------------

def _default_east1_output_path(input_path: Path) -> Path:
    """a.py → work/tmp/east1/a.py.east1"""
    return Path("work").joinpath("tmp").joinpath("east1").joinpath(_path_text_name(input_path) + ".east1")


def _parse_one(input_path: Path, output_text: str, pretty: bool) -> int:
    """1 ファイルを parse して .py.east1 を生成する。"""
    if not input_path.exists():
        print("error: file not found: " + str(input_path))
        return 1

    east1_doc = parse_python_file(str(input_path))
    out_path = Path(output_text) if output_text != "" else _default_east1_output_path(input_path)

    _ensure_parent_dir(out_path)
    indent = 2 if pretty else None
    payload: JsonVal = east1_doc
    out_path.write_text(
        _dump_json_doc(east1_doc, indent) + "\n",
        encoding="utf-8",
    )
    print("parsed: " + str(out_path))
    return 0


def cmd_parse(args: list[str]) -> int:
    """parse サブコマンド: .py → .py.east1"""
    inputs: list[str] = []
    output_text = ""
    pretty = False

    i = 0
    while i < len(args):
        tok = args[i]
        if tok == "-o" or tok == "--output":
            if i + 1 >= len(args):
                print("error: missing value for " + tok)
                return 1
            output_text = args[i + 1]
            i += 2
            continue
        if tok == "--pretty":
            pretty = True
            i += 1
            continue
        if tok == "-h" or tok == "--help":
            print("usage: pytra-cli -parse INPUT.py [-o OUTPUT.py.east1] [--pretty]")
            print("       pytra-cli -parse INPUT1.py INPUT2.py ...  (multiple files)")
            return 0
        if not tok.startswith("-"):
            inputs.append(tok)
        i += 1

    if len(inputs) == 0:
        print("error: at least one input file is required")
        return 1

    if output_text != "" and len(inputs) > 1:
        print("error: -o cannot be used with multiple input files")
        return 1

    exit_code = 0
    for inp in inputs:
        input_path = Path(inp)
        rc = _parse_one(input_path, output_text, pretty)
        if rc != 0:
            exit_code = rc
    return exit_code


# ---------------------------------------------------------------------------
# resolve: *.py.east1 → *.east2
# ---------------------------------------------------------------------------

def _resolve_one(input_path: Path, output_text: str, pretty: bool) -> int:
    """1 ファイルを resolve して .east2 を生成する。"""
    if not input_path.exists():
        print("error: file not found: " + str(input_path))
        return 1

    # Load builtin registry
    builtins_path, containers_path, containers_source_path, stdlib_dir = _builtin_registry_paths()
    registry = load_builtin_registry(builtins_path, containers_path, stdlib_dir, containers_source_path, None)

    result = resolve_file(input_path, registry=registry)
    if output_text != "":
        out_path = Path(output_text)
    else:
        name = _path_text_name(input_path)
        if name.endswith(".py.east1"):
            base = name[:len(name) - len(".py.east1")]
        elif name.endswith(".east1"):
            base = name[:len(name) - len(".east1")]
        else:
            base = name
        out_path = Path("work").joinpath("tmp").joinpath("east2").joinpath(base + ".east2")

    _ensure_parent_dir(out_path)
    indent = 2 if pretty else None
    payload: JsonVal = result.east2_doc
    out_path.write_text(
        _dump_json_doc(result.east2_doc, indent) + "\n",
        encoding="utf-8",
    )
    print("resolved: " + str(out_path))
    return 0


def cmd_resolve(args: list[str]) -> int:
    """resolve サブコマンド: *.py.east1 → *.east2"""
    inputs: list[str] = []
    output_text = ""
    pretty = False

    i = 0
    while i < len(args):
        tok = args[i]
        if tok == "-o" or tok == "--output":
            if i + 1 >= len(args):
                print("error: missing value for " + tok)
                return 1
            output_text = args[i + 1]
            i += 2
            continue
        if tok == "--pretty":
            pretty = True
            i += 1
            continue
        if tok == "-h" or tok == "--help":
            print("usage: pytra-cli -resolve INPUT.py.east1 [-o OUTPUT.east2] [--pretty]")
            print("       pytra-cli -resolve INPUT1.py.east1 INPUT2.py.east1 ...  (multiple files)")
            return 0
        if tok == "--from" or tok.startswith("--from="):
            # --from=python は現時点では Python のみサポート (無視)
            if tok == "--from":
                i += 1
            i += 1
            continue
        if not tok.startswith("-"):
            inputs.append(tok)
        i += 1

    if len(inputs) == 0:
        print("error: at least one input file is required")
        return 1

    if output_text != "" and len(inputs) > 1:
        print("error: -o cannot be used with multiple input files")
        return 1

    exit_code = 0
    for inp in inputs:
        input_path = Path(inp)
        rc = _resolve_one(input_path, output_text, pretty)
        if rc != 0:
            exit_code = rc
    return exit_code


# ---------------------------------------------------------------------------
# compile: *.east2 → *.east3
# ---------------------------------------------------------------------------

def _default_east3_output_path(input_path: Path) -> Path:
    """a.east2 → work/tmp/east3/a.east3"""
    name = _path_text_name(input_path)
    if name.endswith(".east2"):
        name = name[:-6] + ".east3"
    else:
        name = name + ".east3"
    return Path("work").joinpath("tmp").joinpath("east3").joinpath(name)


def _compile_one(input_path: Path, output_text: str, pretty: bool) -> int:
    """1 ファイルを compile して .east3 を生成する。"""
    if not input_path.exists():
        print("error: file not found: " + str(input_path))
        return 1

    east2_text = input_path.read_text(encoding="utf-8")
    east2_obj = json.loads_obj(east2_text)
    if east2_obj is None:
        print("error: invalid east2 document: " + str(input_path))
        return 1

    typed_east2_doc: dict[str, JsonVal] = east2_obj.raw
    east3_doc = lower_east2_to_east3(typed_east2_doc, target_language="cpp")
    out_path = Path(output_text) if output_text != "" else _default_east3_output_path(input_path)

    _ensure_parent_dir(out_path)
    indent = 2 if pretty else None
    payload: JsonVal = east3_doc
    out_path.write_text(
        _dump_json_doc(east3_doc, indent) + "\n",
        encoding="utf-8",
    )
    print("compiled: " + str(out_path))
    return 0


def cmd_compile(args: list[str]) -> int:
    """compile サブコマンド: *.east2 → *.east3"""
    inputs: list[str] = []
    output_text = ""
    pretty = False

    i = 0
    while i < len(args):
        tok = args[i]
        if tok == "-o" or tok == "--output":
            if i + 1 >= len(args):
                print("error: missing value for " + tok)
                return 1
            output_text = args[i + 1]
            i += 2
            continue
        if tok == "--pretty":
            pretty = True
            i += 1
            continue
        if tok == "-h" or tok == "--help":
            print("usage: pytra-cli -compile INPUT.east2 [-o OUTPUT.east3] [--pretty]")
            print("       pytra-cli -compile INPUT1.east2 INPUT2.east2 ...  (multiple files)")
            return 0
        if not tok.startswith("-"):
            inputs.append(tok)
        i += 1

    if len(inputs) == 0:
        print("error: at least one input file is required")
        return 1

    if output_text != "" and len(inputs) > 1:
        print("error: -o cannot be used with multiple input files")
        return 1

    exit_code = 0
    for inp in inputs:
        input_path = Path(inp)
        rc = _compile_one(input_path, output_text, pretty)
        if rc != 0:
            exit_code = rc
    return exit_code


# ---------------------------------------------------------------------------
# optimize: *.east3 → *.east3
# ---------------------------------------------------------------------------

def _optimize_one(
    input_path: Path,
    output_text: str,
    pretty: bool,
    opt_level: int,
    negative_index_mode: str,
    bounds_check_mode: str,
) -> int:
    """1 ファイルを optimize して .east3 を生成する。"""
    if not input_path.exists():
        print("error: file not found: " + str(input_path))
        return 1

    east3_text = input_path.read_text(encoding="utf-8")
    east3_obj = json.loads_obj(east3_text)
    if east3_obj is None:
        print("error: invalid east3 document: " + str(input_path))
        return 1

    typed_east3_doc: dict[str, JsonVal] = east3_obj.raw
    optimized_doc = optimize_east3_doc_only(
        typed_east3_doc,
        opt_level,
        "",
        "",
        _optimizer_debug_flags(opt_level, negative_index_mode, bounds_check_mode),
    )
    if output_text != "":
        out_path = Path(output_text)
    else:
        out_path = Path("work").joinpath("tmp").joinpath("east3-opt").joinpath(_path_text_name(input_path))

    _ensure_parent_dir(out_path)
    indent = 2 if pretty else None
    payload: JsonVal = optimized_doc
    out_path.write_text(
        _dump_json_doc(optimized_doc, indent) + "\n",
        encoding="utf-8",
    )
    print("optimized: " + str(out_path))
    return 0


def cmd_optimize(args: list[str]) -> int:
    """optimize サブコマンド: *.east3 → *.east3"""
    inputs: list[str] = []
    output_text = ""
    pretty = False
    opt_level = 1
    negative_index_mode = ""
    bounds_check_mode = ""

    i = 0
    while i < len(args):
        tok = args[i]
        if tok == "-o" or tok == "--output":
            if i + 1 >= len(args):
                print("error: missing value for " + tok)
                return 1
            output_text = args[i + 1]
            i += 2
            continue
        if tok == "--pretty":
            pretty = True
            i += 1
            continue
        if tok == "--opt-level":
            if i + 1 >= len(args):
                print("error: missing value for --opt-level")
                return 1
            try:
                opt_level = int(args[i + 1])
            except ValueError:
                print("error: invalid --opt-level: " + args[i + 1])
                return 1
            if opt_level not in (0, 1, 2):
                print("error: invalid --opt-level: " + str(opt_level))
                return 1
            i += 2
            continue
        if tok == "--negative-index-mode":
            if i + 1 >= len(args):
                print("error: missing value for --negative-index-mode")
                return 1
            negative_index_mode = args[i + 1]
            i += 2
            continue
        if tok == "--bounds-check-mode":
            if i + 1 >= len(args):
                print("error: missing value for --bounds-check-mode")
                return 1
            bounds_check_mode = args[i + 1]
            i += 2
            continue
        if tok == "-h" or tok == "--help":
            print("usage: pytra-cli -optimize INPUT.east3 [-o OUTPUT.east3] [--pretty] [--opt-level {0,1,2}] [--negative-index-mode MODE] [--bounds-check-mode MODE]")
            print("       pytra-cli -optimize INPUT1.east3 INPUT2.east3 ...  (multiple files)")
            return 0
        if not tok.startswith("-"):
            inputs.append(tok)
        i += 1

    if len(inputs) == 0:
        print("error: at least one input file is required")
        return 1

    if output_text != "" and len(inputs) > 1:
        print("error: -o cannot be used with multiple input files")
        return 1

    exit_code = 0
    for inp in inputs:
        input_path = Path(inp)
        rc = _optimize_one(input_path, output_text, pretty, opt_level, negative_index_mode, bounds_check_mode)
        if rc != 0:
            exit_code = rc
    return exit_code


# ---------------------------------------------------------------------------
# link: *.east3 → manifest.json + linked east3 群
# ---------------------------------------------------------------------------

def _write_link_output(result: LinkResult, output_dir: Path, pretty: bool) -> int:
    """Write manifest.json and linked east3 files to output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    indent = 2 if pretty else None

    # Write manifest.json
    manifest_path = output_dir.joinpath("manifest.json")
    manifest_payload: JsonVal = result.manifest
    manifest_path.write_text(
        _dump_json_doc(result.manifest, indent) + "\n",
        encoding="utf-8",
    )

    # Write linked east3 files
    for module in result.linked_modules:
        rel_path = module.module_id.replace(".", "/") + ".east3.json"
        out_path = output_dir.joinpath("east3").joinpath(rel_path)
        _ensure_parent_dir(out_path)
        module_payload: JsonVal = module.east_doc
        out_path.write_text(
            _dump_json_doc(module.east_doc, indent) + "\n",
            encoding="utf-8",
        )

    print("linked: " + str(manifest_path) + " (" + str(len(result.linked_modules)) + " modules)")
    return 0


def cmd_link(args: list[str]) -> int:
    """link サブコマンド: *.east3 → manifest.json + linked east3 群"""
    inputs: list[str] = []
    output_text = ""
    target = "cpp"
    dispatch_mode = "native"
    pretty = True  # default to pretty for linked output

    i = 0
    while i < len(args):
        tok = args[i]
        if tok == "-o" or tok == "--output":
            if i + 1 >= len(args):
                print("error: missing value for " + tok)
                return 1
            output_text = args[i + 1]
            i += 2
            continue
        if tok == "--target":
            if i + 1 >= len(args):
                print("error: missing value for --target")
                return 1
            target = args[i + 1]
            i += 2
            continue
        if tok == "--dispatch-mode":
            if i + 1 >= len(args):
                print("error: missing value for --dispatch-mode")
                return 1
            dispatch_mode = args[i + 1]
            i += 2
            continue
        if tok == "--pretty":
            pretty = True
            i += 1
            continue
        if tok == "--compact":
            pretty = False
            i += 1
            continue
        if tok == "-h" or tok == "--help":
            print("usage: pytra-cli -link INPUT1.east3 [INPUT2.east3 ...] [-o OUTPUT_DIR] [--target TARGET] [--dispatch-mode MODE]")
            return 0
        if not tok.startswith("-"):
            inputs.append(tok)
        i += 1

    if len(inputs) == 0:
        print("error: at least one input file is required")
        return 1

    result = link_modules(inputs, target=target, dispatch_mode=dispatch_mode)

    if output_text == "":
        # Default: output to work/tmp/linked/
        output_dir = Path("work").joinpath("tmp").joinpath("linked")
    else:
        output_dir = Path(output_text)

    return _write_link_output(result, output_dir, pretty)


# ---------------------------------------------------------------------------
# emit: linked → target
# ---------------------------------------------------------------------------

_SUBPROCESS_EMIT_TARGETS: list[str] = [
    "go", "cs", "java", "scala", "kotlin", "zig",
    "dart", "lua", "php", "ruby", "nim", "swift", "julia", "powershell",
]


def cmd_emit(args: list[str]) -> int:
    """emit サブコマンド: linked output → target code (暫定: 現行 toolchain/emit/ への橋渡し)"""
    input_text = ""
    output_dir_text = ""
    target = "cpp"
    emitter_options: dict[str, str] = {}

    i = 0
    while i < len(args):
        tok = args[i]
        if tok == "-o" or tok == "--output-dir":
            if i + 1 >= len(args):
                print("error: missing value for " + tok)
                return 1
            output_dir_text = args[i + 1]
            i += 2
            continue
        if tok == "--target" or tok.startswith("--target="):
            if "=" in tok:
                target = tok.split("=", 1)[1]
                i += 1
            else:
                if i + 1 >= len(args):
                    print("error: missing value for --target")
                    return 1
                target = args[i + 1]
                i += 2
            continue
        if tok == "--emitter-option":
            if i + 1 >= len(args):
                print("error: missing value for --emitter-option")
                return 1
            eq = args[i + 1].find("=")
            if eq > 0:
                emitter_options[args[i + 1][:eq]] = args[i + 1][eq + 1:]
            i += 2
            continue
        if tok == "-h" or tok == "--help":
            print("usage: pytra-cli -emit MANIFEST_DIR [-o OUTPUT_DIR] [--target TARGET] [--emitter-option key=value]")
            print("  MANIFEST_DIR: directory containing manifest.json + east3/ (output of -link)")
            return 0
        if not tok.startswith("-") and input_text == "":
            input_text = tok
        i += 1

    if input_text == "":
        print("error: input directory (containing manifest.json) is required")
        return 1

    manifest_path = Path(input_text).joinpath("manifest.json")
    if not manifest_path.exists():
        # Maybe the input IS the manifest.json directly
        if _path_text_name(Path(input_text)) == "manifest.json" and Path(input_text).exists():
            manifest_path = Path(input_text)
        else:
            print("error: manifest.json not found in: " + input_text)
            return 1

    if output_dir_text == "":
        output_dir_text = str(Path("work").joinpath("tmp").joinpath("emit").joinpath(target))

    if target == "cpp":
        return _emit_cpp(manifest_path, Path(output_dir_text))

    if target == "rs":
        return _emit_rs(manifest_path, Path(output_dir_text))

    if target == "ts" or target == "js":
        return _emit_ts(manifest_path, Path(output_dir_text), strip_types=(target == "js"))

    if target in _SUBPROCESS_EMIT_TARGETS:
        return _emit_target_subprocess(target, manifest_path, Path(output_dir_text))

    print("error: unsupported target: " + target)
    return 1


def _emit_rs(manifest_path: Path, output_dir: Path, *, package_mode: bool = False) -> int:
    """Rust emit: linked output → subprocess delegated Rust emitter."""
    cmd = [_python(), "-m", "toolchain.emit.rs.cli", str(manifest_path), "--output-dir", str(output_dir)]
    if package_mode:
        cmd.append("--package")
    return _run_subprocess(cmd)


def _copy_nim_runtime_files(output_dir: Path) -> int:
    """Copy native Nim runtime files into the flat emit directory."""
    runtime_root = _repo_root().joinpath("src").joinpath("runtime").joinpath("nim")
    copied = 0
    for bucket in ["built_in", "std"]:
        bucket_dir = runtime_root.joinpath(bucket)
        if not bucket_dir.exists():
            continue
        for nim_file in bucket_dir.glob("*.nim"):
            dst = output_dir.joinpath(_path_text_name(nim_file))
            dst.write_text(nim_file.read_text(encoding="utf-8"), encoding="utf-8")
            copied += 1
    return copied


def _emit_nim(manifest_path: Path, output_dir: Path) -> int:
    """Nim emit: linked output -> Nim source files via subprocess + runtime copy."""
    status = _emit_target_subprocess("nim", manifest_path, output_dir)
    if status != 0:
        return status
    _copy_nim_runtime_files(output_dir)
    return 0


def _emit_go(manifest_path: Path, output_dir: Path) -> int:
    """Go emit: linked output → subprocess delegated Go emitter + runtime copy."""
    status = _emit_target_subprocess("go", manifest_path, output_dir)
    if status != 0:
        return status
    _copy_go_runtime_files(output_dir)
    return 0


def _copy_ts_runtime_files(output_dir: Path) -> int:
    """Copy TypeScript/JavaScript runtime files into the flat emit directory."""
    runtime_root = _repo_root().joinpath("src").joinpath("runtime").joinpath("ts")
    copied: int = 0
    for bucket in ["built_in", "std"]:
        bucket_dir = runtime_root.joinpath(bucket)
        if not bucket_dir.exists():
            continue
        for ts_file in bucket_dir.glob("*.ts"):
            dst = output_dir.joinpath(_path_text_name(ts_file))
            dst.write_text(ts_file.read_text(encoding="utf-8"), encoding="utf-8")
            copied += 1
    return copied


def _emit_ts(manifest_path: Path, output_dir: Path, *, strip_types: bool = False) -> int:
    """TypeScript/JavaScript emit: linked output → TS/JS source files via subprocess."""
    ext = ".js" if strip_types else ".ts"
    cmd = [_python(), "-m", "toolchain.emit.ts.cli",
           str(manifest_path), "--output-dir", str(output_dir), "--ext", ext]
    status = _run_subprocess(cmd)
    if status != 0:
        return status
    _copy_ts_runtime_files(output_dir)
    return 0


def _emit_cpp(manifest_path: Path, output_dir: Path) -> int:
    """C++ emit: linked output → subprocess delegated C++ emitter."""
    cmd = [_python(), "-m", "toolchain.emit.cpp.cli", str(manifest_path), "--output-dir", str(output_dir)]
    return _run_subprocess(cmd)


# ---------------------------------------------------------------------------
# build: .py → target (一括実行, 未実装)
# ---------------------------------------------------------------------------

def cmd_build(args: list[str]) -> int:
    """build サブコマンド: .py → target (parse→resolve→compile→optimize→link→emit 一括実行)"""
    inputs: list[str] = []
    output_dir_text = ""
    target = "cpp"
    opt_level = 1
    rs_package = False
    negative_index_mode = ""
    bounds_check_mode = ""

    i = 0
    while i < len(args):
        tok = args[i]
        if tok == "-o" or tok == "--output-dir":
            if i + 1 >= len(args):
                print("error: missing value for " + tok)
                return 1
            output_dir_text = args[i + 1]
            i += 2
            continue
        if tok == "--target":
            if i + 1 >= len(args):
                print("error: missing value for --target")
                return 1
            target = args[i + 1]
            i += 2
            continue
        if tok == "--rs-package":
            rs_package = True
            i += 1
            continue
        if tok == "--opt-level":
            if i + 1 >= len(args):
                print("error: missing value for --opt-level")
                return 1
            try:
                opt_level = int(args[i + 1])
            except ValueError:
                print("error: invalid --opt-level: " + args[i + 1])
                return 1
            if opt_level not in (0, 1, 2):
                print("error: invalid --opt-level: " + str(opt_level))
                return 1
            i += 2
            continue
        if tok == "--negative-index-mode":
            if i + 1 >= len(args):
                print("error: missing value for --negative-index-mode")
                return 1
            negative_index_mode = args[i + 1]
            i += 2
            continue
        if tok == "--bounds-check-mode":
            if i + 1 >= len(args):
                print("error: missing value for --bounds-check-mode")
                return 1
            bounds_check_mode = args[i + 1]
            i += 2
            continue
        if tok == "-h" or tok == "--help":
            print("usage: pytra-cli -build INPUT.py [-o OUTPUT_DIR] [--target TARGET] [--rs-package] [--opt-level {0,1,2}] [--negative-index-mode MODE] [--bounds-check-mode MODE]")
            return 0
        if not tok.startswith("-"):
            inputs.append(tok)
        i += 1

    if len(inputs) == 0:
        print("error: at least one input .py file is required")
        return 1

    if target not in ["cpp", "go", "rs", "cs", "java", "scala", "kotlin", "ts", "js", "nim", "swift", "julia", "powershell", "ps1"]:
        print("error: unsupported target: " + target + " (available: cpp, go, rs, cs, java, scala, kotlin, ts, js, nim, swift, julia, powershell, zig)")
        return 1

    try:
        return _build_pipeline(
            inputs,
            output_dir_text,
            target,
            opt_level=opt_level,
            rs_package=rs_package,
            negative_index_mode=negative_index_mode,
            bounds_check_mode=bounds_check_mode,
        )
    except Exception as exc:
        print("error: build failed: " + str(exc))
        return 1


def _build_pipeline(
    inputs: list[str],
    output_dir_text: str,
    target: str,
    *,
    opt_level: int = 1,
    rs_package: bool = False,
    negative_index_mode: str = "",
    bounds_check_mode: str = "",
) -> int:
    """Run the full build pipeline in-memory."""
    lowering_target = "ts" if target == "js" else target

    # 1. Parse
    east1_docs = _collect_build_sources(inputs)
    print("build: parsed " + str(len(east1_docs)) + " files")

    # 2. Resolve
    builtins_path, containers_path, containers_source_path, stdlib_dir = _builtin_registry_paths()
    registry = load_builtin_registry(builtins_path, containers_path, stdlib_dir, containers_source_path, None)

    east2_docs: list[tuple[str, dict[str, JsonVal]]] = []
    for inp, east1_doc in east1_docs:
        typed_east2_doc = _copy_json_doc(east1_doc)
        resolve_east1_to_east2(typed_east2_doc, registry=registry)
        east2_docs.append((inp, typed_east2_doc))
    print("build: resolved " + str(len(east2_docs)) + " files")

    # 3. Compile
    east3_docs: list[tuple[str, dict[str, JsonVal]]] = []
    for inp, east2_doc in east2_docs:
        compiled_doc = lower_east2_to_east3(east2_doc, target_language=lowering_target)
        east3_docs.append((inp, compiled_doc))
    print("build: compiled " + str(len(east3_docs)) + " files")

    # 4. Optimize
    east3_opt_docs: list[tuple[str, dict[str, JsonVal]]] = []
    optimizer_debug_flags = _optimizer_debug_flags(opt_level, negative_index_mode, bounds_check_mode)
    for inp, east3_doc in east3_docs:
        optimized_doc = optimize_east3_doc_only(east3_doc, opt_level, "", "", optimizer_debug_flags)
        east3_opt_docs.append((
            inp,
            optimized_doc,
        ))
    print("build: optimized " + str(len(east3_opt_docs)) + " files")

    # 5. Link — write east3-opt to temp files for link_modules
    work_dir = Path("work").joinpath("tmp").joinpath("build_" + _path_text_stem(Path(inputs[0]))).resolve()
    east3_opt_dir = work_dir.joinpath("east3-opt")
    east3_opt_dir.mkdir(parents=True, exist_ok=True)

    east3_opt_paths: list[str] = []
    for inp, east3_opt_doc in east3_opt_docs:
        # Use source_path-derived name to avoid collisions (e.g. two types.py in different dirs)
        source_path_text_opt = json.JsonObj(east3_opt_doc).get_str("source_path")
        if source_path_text_opt is None:
            source_path_text = ""
        else:
            source_path_text = cast(str, source_path_text_opt)
        stem = _module_stem_from_source_path(source_path_text, inp)
        out_path = east3_opt_dir.joinpath(stem + ".east3")
        east3_opt_payload: JsonVal = east3_opt_doc
        out_path.write_text(
            _dump_json_doc(east3_opt_doc, 2) + "\n",
            encoding="utf-8",
        )
        east3_opt_paths.append(str(out_path.resolve()))

    link_result = link_modules(east3_opt_paths, target=target, dispatch_mode="native")
    for module in link_result.linked_modules:
        if module.module_kind not in ("runtime", "helper"):
            continue
        module.east_doc = optimize_east3_doc_only(
            module.east_doc,
            opt_level,
            "",
            "",
            optimizer_debug_flags,
        )
    # Only the first input is the actual entry module; demote others
    if len(inputs) >= 1:
        entry_abs = str(Path(inputs[0]).resolve())
        for m in link_result.linked_modules:
            _demote_non_entry_module(m, entry_abs)
    print("build: linked " + str(len(link_result.linked_modules)) + " modules")

    # 6. Emit
    if output_dir_text == "":
        output_dir_text = str(work_dir.joinpath("emit").joinpath(target))
    output_dir = Path(output_dir_text).resolve()

    entry_path = Path("")
    for m in link_result.linked_modules:
        mp = _linked_module_entry_path(m)
        if m.is_entry:
            entry_path = mp

    if str(entry_path) == "":
        print("error: no entry module found")
        return 1

    linked_dir = work_dir.joinpath("linked").resolve()
    _write_link_output(link_result, linked_dir, False)
    if target == "rs":
        return _emit_rs(linked_dir.joinpath("manifest.json"), output_dir, package_mode=rs_package)
    if target == "go":
        return _emit_go(linked_dir.joinpath("manifest.json"), output_dir)
    if target == "cs":
        return _emit_target_subprocess("cs", linked_dir.joinpath("manifest.json"), output_dir)
    if target == "java":
        return _emit_target_subprocess("java", linked_dir.joinpath("manifest.json"), output_dir)
    if target == "scala":
        return _emit_target_subprocess("scala", linked_dir.joinpath("manifest.json"), output_dir)
    if target == "kotlin":
        return _emit_target_subprocess("kotlin", linked_dir.joinpath("manifest.json"), output_dir)
    if target == "ts" or target == "js":
        return _emit_ts(linked_dir.joinpath("manifest.json"), output_dir, strip_types=(target == "js"))
    if target == "nim":
        return _emit_nim(linked_dir.joinpath("manifest.json"), output_dir)
    if target == "powershell" or target == "ps1":
        return _emit_target_subprocess("powershell", linked_dir.joinpath("manifest.json"), output_dir)
    if target == "swift" or target == "julia":
        return _emit_target_subprocess(target, linked_dir.joinpath("manifest.json"), output_dir)
    return _emit_cpp(linked_dir.joinpath("manifest.json"), output_dir)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def cli_main() -> int:
    cli_argv: list[str] = []
    index = 0
    for arg in sys.argv:
        if index > 0:
            cli_argv.append(arg)
        index += 1
    if len(cli_argv) == 0 or cli_argv[0] == "-h" or cli_argv[0] == "--help":
        print("usage: pytra-cli <command> [options]")
        print("")
        print("commands:")
        print("  -parse      .py -> .py.east1         (Python parse)")
        print("  -resolve    *.py.east1 -> *.east2    (type resolve + normalize)")
        print("  -compile    *.east2 -> *.east3       (core lowering)")
        print("  -optimize   *.east3 -> *.east3       (whole-program optimization)")
        print("  -link       *.east3 -> manifest.json  (multi-module linking)")
        print("  -emit       *.east3 -> target         (code generation)")
        print("  -build      .py -> target             (all-in-one)")
        print("")
        print("golden file generation: python3 tools/gen/generate_golden.py --help")
        return 0

    cmd_name = cli_argv[0]
    args: list[str] = []
    index = 0
    for arg in cli_argv:
        if index > 0:
            args.append(arg)
        index += 1
    if cmd_name == "-parse":
        return cmd_parse(args)
    if cmd_name == "-resolve":
        return cmd_resolve(args)
    if cmd_name == "-compile":
        return cmd_compile(args)
    if cmd_name == "-optimize":
        return cmd_optimize(args)
    if cmd_name == "-link":
        return cmd_link(args)
    if cmd_name == "-emit":
        return cmd_emit(args)
    if cmd_name == "-build":
        return cmd_build(args)
    else:
        print("error: unknown command: " + cmd_name)
        print("run 'pytra-cli --help' for available commands")
        return 1


if __name__ == "__main__":
    sys.exit(cli_main())
