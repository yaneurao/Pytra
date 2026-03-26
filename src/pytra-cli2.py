#!/usr/bin/env python3
"""pytra-cli2: 新パイプライン CLI (parse / resolve / compile / optimize / emit).

設計文書: docs/ja/plans/plan-pipeline-redesign.md

パイプライン:
  -parse      .py → .py.east1         Python 構文解析
  -resolve    *.py.east1 → *.east2    型解決 + 正規化 (言語固有→言語非依存)
  -compile    *.east2 → *.east3       core lowering (言語非依存)
  -optimize   *.east3 → *.east3       whole-program 最適化
  -link       *.east3 → manifest.json multi-module 結合
  -emit       *.east3 → *.cpp 等      target コード生成
  -build      .py → target            一括実行

selfhost 対象 (§5.7): toolchain2/ + pytra.std.* のみ使用。
golden file 生成は tools/generate_golden.py に分離。
"""

from __future__ import annotations

from pytra.std import sys
from pytra.std import json
from pytra.std.pathlib import Path


def _repo_root() -> Path:
    """Return repository root from this script path."""
    return Path(__file__).resolve().parent.parent


def _builtin_registry_paths() -> tuple[Path, Path, Path]:
    """Return absolute builtins/containers/stdlib registry inputs."""
    root = _repo_root()
    return (
        root / "test" / "include" / "east1" / "py" / "built_in" / "builtins.py.east1",
        root / "test" / "include" / "east1" / "py" / "built_in" / "containers.py.east1",
        root / "test" / "include" / "east1" / "py" / "std",
    )


# ---------------------------------------------------------------------------
# parse: .py → .py.east1
# ---------------------------------------------------------------------------

def _default_east1_output_path(input_path: Path) -> Path:
    """a.py → a.py.east1 (同一ディレクトリ)"""
    return input_path.parent / (input_path.name + ".east1")


def _parse_one(input_path: Path, output_path: Path | None, pretty: bool) -> int:
    """1 ファイルを parse して .py.east1 を生成する。"""
    if not input_path.exists():
        print("error: file not found: " + str(input_path))
        return 1

    from toolchain2.parse.py.parse_python import parse_python_file

    try:
        east1_doc = parse_python_file(str(input_path))
    except Exception as e:
        print("error: parse failed: " + str(input_path) + ": " + str(e))
        return 1

    if output_path is None:
        output_path = _default_east1_output_path(input_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    indent = 2 if pretty else None
    output_path.write_text(
        json.dumps(east1_doc, ensure_ascii=False, indent=indent) + "\n",
        encoding="utf-8",
    )
    print("parsed: " + str(output_path))
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
            print("usage: pytra-cli2 -parse INPUT.py [-o OUTPUT.py.east1] [--pretty]")
            print("       pytra-cli2 -parse INPUT1.py INPUT2.py ...  (multiple files)")
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
        out = Path(output_text) if output_text != "" else None
        rc = _parse_one(input_path, out, pretty)
        if rc != 0:
            exit_code = rc
    return exit_code


# ---------------------------------------------------------------------------
# resolve: *.py.east1 → *.east2
# ---------------------------------------------------------------------------

def _resolve_one(input_path: Path, output_path: Path | None, pretty: bool) -> int:
    """1 ファイルを resolve して .east2 を生成する。"""
    from toolchain2.resolve.py.resolver import resolve_file, east2_output_path_from_east1
    from toolchain2.resolve.py.builtin_registry import load_builtin_registry

    if not input_path.exists():
        print("error: file not found: " + str(input_path))
        return 1

    # Load builtin registry
    builtins_path, containers_path, stdlib_dir = _builtin_registry_paths()
    registry = load_builtin_registry(builtins_path, containers_path, stdlib_dir)

    try:
        result = resolve_file(input_path, registry=registry)
    except Exception as e:
        print("error: resolve failed: " + str(input_path) + ": " + str(e))
        return 1

    if output_path is None:
        output_path = east2_output_path_from_east1(input_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    indent = 2 if pretty else None
    output_path.write_text(
        json.dumps(result.east2_doc, ensure_ascii=False, indent=indent) + "\n",
        encoding="utf-8",
    )
    print("resolved: " + str(output_path))
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
            print("usage: pytra-cli2 -resolve INPUT.py.east1 [-o OUTPUT.east2] [--pretty]")
            print("       pytra-cli2 -resolve INPUT1.py.east1 INPUT2.py.east1 ...  (multiple files)")
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
        out = Path(output_text) if output_text != "" else None
        rc = _resolve_one(input_path, out, pretty)
        if rc != 0:
            exit_code = rc
    return exit_code


# ---------------------------------------------------------------------------
# compile: *.east2 → *.east3
# ---------------------------------------------------------------------------

def _default_east3_output_path(input_path: Path) -> Path:
    """a.east2 → a.east3 (同一ディレクトリ)"""
    name = input_path.name
    if name.endswith(".east2"):
        name = name[:-6] + ".east3"
    else:
        name = name + ".east3"
    return input_path.parent / name


def _compile_one(input_path: Path, output_path: Path | None, pretty: bool) -> int:
    """1 ファイルを compile して .east3 を生成する。"""
    if not input_path.exists():
        print("error: file not found: " + str(input_path))
        return 1

    from toolchain2.compile.lower import lower_east2_to_east3

    try:
        east2_text = input_path.read_text(encoding="utf-8")
        east2_doc = json.loads(east2_text).raw
        if not isinstance(east2_doc, dict):
            print("error: invalid east2 document: " + str(input_path))
            return 1
    except Exception as e:
        print("error: failed to read east2: " + str(input_path) + ": " + str(e))
        return 1

    try:
        east3_doc = lower_east2_to_east3(east2_doc)
    except Exception as e:
        print("error: compile failed: " + str(input_path) + ": " + str(e))
        return 1

    if output_path is None:
        output_path = _default_east3_output_path(input_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    indent = 2 if pretty else None
    output_path.write_text(
        json.dumps(east3_doc, ensure_ascii=False, indent=indent) + "\n",
        encoding="utf-8",
    )
    print("compiled: " + str(output_path))
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
            print("usage: pytra-cli2 -compile INPUT.east2 [-o OUTPUT.east3] [--pretty]")
            print("       pytra-cli2 -compile INPUT1.east2 INPUT2.east2 ...  (multiple files)")
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
        out = Path(output_text) if output_text != "" else None
        rc = _compile_one(input_path, out, pretty)
        if rc != 0:
            exit_code = rc
    return exit_code


# ---------------------------------------------------------------------------
# optimize: *.east3 → *.east3
# ---------------------------------------------------------------------------

def _optimize_one(input_path: Path, output_path: Path | None, pretty: bool) -> int:
    """1 ファイルを optimize して .east3 を生成する。"""
    if not input_path.exists():
        print("error: file not found: " + str(input_path))
        return 1

    from toolchain2.optimize.optimizer import optimize_east3_document

    try:
        east3_text = input_path.read_text(encoding="utf-8")
        east3_doc = json.loads(east3_text).raw
        if not isinstance(east3_doc, dict):
            print("error: invalid east3 document: " + str(input_path))
            return 1
    except Exception as e:
        print("error: failed to read east3: " + str(input_path) + ": " + str(e))
        return 1

    try:
        east3_doc, _report = optimize_east3_document(east3_doc, opt_level=1)
    except Exception as e:
        print("error: optimize failed: " + str(input_path) + ": " + str(e))
        return 1

    if output_path is None:
        output_path = input_path

    output_path.parent.mkdir(parents=True, exist_ok=True)
    indent = 2 if pretty else None
    output_path.write_text(
        json.dumps(east3_doc, ensure_ascii=False, indent=indent) + "\n",
        encoding="utf-8",
    )
    print("optimized: " + str(output_path))
    return 0


def cmd_optimize(args: list[str]) -> int:
    """optimize サブコマンド: *.east3 → *.east3"""
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
            print("usage: pytra-cli2 -optimize INPUT.east3 [-o OUTPUT.east3] [--pretty]")
            print("       pytra-cli2 -optimize INPUT1.east3 INPUT2.east3 ...  (multiple files)")
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
        out = Path(output_text) if output_text != "" else None
        rc = _optimize_one(input_path, out, pretty)
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
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(result.manifest, ensure_ascii=False, indent=indent) + "\n",
        encoding="utf-8",
    )

    # Write linked east3 files
    for module in result.linked_modules:
        rel_path = module.module_id.replace(".", "/") + ".east3.json"
        out_path = output_dir / "east3" / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(module.east_doc, ensure_ascii=False, indent=indent) + "\n",
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
            print("usage: pytra-cli2 -link INPUT1.east3 [INPUT2.east3 ...] [-o OUTPUT_DIR] [--target TARGET] [--dispatch-mode MODE]")
            return 0
        if not tok.startswith("-"):
            inputs.append(tok)
        i += 1

    if len(inputs) == 0:
        print("error: at least one input file is required")
        return 1

    from toolchain2.link.linker import link_modules as _link_modules
    from toolchain2.link.linker import LinkResult as _LinkResult

    try:
        result = _link_modules(inputs, target=target, dispatch_mode=dispatch_mode)
    except Exception as e:
        print("error: link failed: " + str(e))
        return 1

    if output_text == "":
        # Default: output to work/tmp/linked/
        output_dir = Path("work/tmp/linked")
    else:
        output_dir = Path(output_text)

    return _write_link_output(result, output_dir, pretty)


# ---------------------------------------------------------------------------
# emit: linked → target
# ---------------------------------------------------------------------------

def _emit_go(manifest_path: Path, output_dir: Path) -> int:
    """Go emit: linked output → Go source files."""
    from toolchain2.link.linker import link_modules as _lm
    from toolchain2.emit.go.emitter import emit_go_module
    from toolchain2.link.manifest_loader import load_linked_output

    manifest_doc, linked_modules = load_linked_output(manifest_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    written = 0
    for module in linked_modules:
        code = emit_go_module(module.east_doc)
        if code.strip() == "":
            continue
        # Flat layout: module_id → filename.go
        mid = module.module_id
        fname = mid.replace(".", "_") + ".go"
        out_path = output_dir / fname
        out_path.write_text(code, encoding="utf-8")
        written += 1

    print("emitted: " + str(output_dir) + " (" + str(written) + " Go files)")
    return 0


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
            print("usage: pytra-cli2 -emit MANIFEST_DIR [-o OUTPUT_DIR] [--target TARGET] [--emitter-option key=value]")
            print("  MANIFEST_DIR: directory containing manifest.json + east3/ (output of -link)")
            return 0
        if not tok.startswith("-") and input_text == "":
            input_text = tok
        i += 1

    if input_text == "":
        print("error: input directory (containing manifest.json) is required")
        return 1

    manifest_path = Path(input_text) / "manifest.json"
    if not manifest_path.exists():
        # Maybe the input IS the manifest.json directly
        if Path(input_text).name == "manifest.json" and Path(input_text).exists():
            manifest_path = Path(input_text)
        else:
            print("error: manifest.json not found in: " + input_text)
            return 1

    if output_dir_text == "":
        output_dir_text = "work/tmp/emit/" + target

    if target == "go":
        return _emit_go(manifest_path, Path(output_dir_text))

    if target == "cpp":
        return _emit_cpp(manifest_path, Path(output_dir_text))

    print("error: unsupported target: " + target + " (available: cpp, go)")
    return 1


def _emit_cpp(manifest_path: Path, output_dir: Path) -> int:
    """C++ emit: linked output → C++ source files (toolchain2 emitter)."""
    from toolchain2.link.manifest_loader import load_linked_output
    from toolchain2.emit.cpp.emitter import emit_cpp_module

    manifest_doc, linked_modules = load_linked_output(manifest_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    written = 0
    for module in linked_modules:
        code = emit_cpp_module(module.east_doc)
        if code.strip() == "":
            continue
        # Use module_id for filename
        mid = module.module_id
        fname = mid.replace(".", "_") + ".cpp"
        (output_dir / fname).write_text(code, encoding="utf-8")
        written += 1

    print("emitted: " + str(output_dir) + " (" + str(written) + " C++ files)")
    return 0


# ---------------------------------------------------------------------------
# build: .py → target (一括実行, 未実装)
# ---------------------------------------------------------------------------

def cmd_build(args: list[str]) -> int:
    """build サブコマンド: .py → target (parse→resolve→compile→optimize→link→emit 一括実行)"""
    inputs: list[str] = []
    output_dir_text = ""
    target = "cpp"

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
        if tok == "-h" or tok == "--help":
            print("usage: pytra-cli2 -build INPUT.py [-o OUTPUT_DIR] [--target TARGET]")
            return 0
        if not tok.startswith("-"):
            inputs.append(tok)
        i += 1

    if len(inputs) == 0:
        print("error: at least one input .py file is required")
        return 1

    if target not in ("cpp", "go"):
        print("error: unsupported target: " + target + " (available: cpp, go)")
        return 1

    try:
        return _build_pipeline(inputs, output_dir_text, target)
    except Exception as e:
        print("error: build failed: " + str(e))
        return 1


def _build_pipeline(inputs: list[str], output_dir_text: str, target: str) -> int:
    """Run the full build pipeline in-memory."""
    from toolchain2.parse.py.parse_python import parse_python_file
    from toolchain2.resolve.py.resolver import resolve_east1_to_east2
    from toolchain2.resolve.py.builtin_registry import load_builtin_registry
    from toolchain2.compile.lower import lower_east2_to_east3
    from toolchain2.optimize.optimizer import optimize_east3_document
    from toolchain2.link.linker import link_modules

    # 1. Parse
    east1_docs: list[tuple[str, dict]] = []
    for inp in inputs:
        p = Path(inp)
        if not p.exists():
            print("error: file not found: " + inp)
            return 1
        east1_doc = parse_python_file(str(p))
        if not isinstance(east1_doc, dict):
            print("error: parse failed: " + inp)
            return 1
        east1_docs.append((inp, east1_doc))
    print("build: parsed " + str(len(east1_docs)) + " files")

    # 2. Resolve
    builtins_path, containers_path, stdlib_dir = _builtin_registry_paths()
    registry = load_builtin_registry(builtins_path, containers_path, stdlib_dir)

    east2_docs: list[tuple[str, dict]] = []
    for inp, east1_doc in east1_docs:
        from toolchain2.common.jv import deep_copy_json
        east2_doc = deep_copy_json(east1_doc)
        if not isinstance(east2_doc, dict):
            print("error: invalid east1 document: " + inp)
            return 1
        resolve_east1_to_east2(east2_doc, registry=registry)
        east2_docs.append((inp, east2_doc))
    print("build: resolved " + str(len(east2_docs)) + " files")

    # 3. Compile
    east3_docs: list[tuple[str, dict]] = []
    for inp, east2_doc in east2_docs:
        east3_doc = lower_east2_to_east3(east2_doc)
        east3_docs.append((inp, east3_doc))
    print("build: compiled " + str(len(east3_docs)) + " files")

    # 4. Optimize
    east3_opt_docs: list[tuple[str, dict]] = []
    for inp, east3_doc in east3_docs:
        east3_opt, _report = optimize_east3_document(east3_doc, opt_level=1)
        east3_opt_docs.append((inp, east3_opt))
    print("build: optimized " + str(len(east3_opt_docs)) + " files")

    # 5. Link — write east3-opt to temp files for link_modules
    work_dir = Path("work/tmp/build_" + Path(inputs[0]).stem)
    east3_opt_dir = work_dir / "east3-opt"
    east3_opt_dir.mkdir(parents=True, exist_ok=True)

    east3_opt_paths: list[str] = []
    for inp, east3_opt_doc in east3_opt_docs:
        stem = Path(inp).stem
        out_path = east3_opt_dir / (stem + ".east3")
        out_path.write_text(
            json.dumps(east3_opt_doc, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        east3_opt_paths.append(str(out_path))

    link_result = link_modules(east3_opt_paths, target=target, dispatch_mode="native")
    print("build: linked " + str(len(link_result.linked_modules)) + " modules")

    # 6. Emit
    if output_dir_text == "":
        output_dir_text = str(work_dir / "emit" / target)
    output_dir = Path(output_dir_text)

    module_east_map: dict[str, dict] = {}
    entry_path = Path("")
    for m in link_result.linked_modules:
        mp = Path(m.source_path) if m.source_path != "" else Path(m.module_id + ".py")
        module_east_map[str(mp)] = m.east_doc
        if m.is_entry:
            entry_path = mp

    if str(entry_path) == "":
        print("error: no entry module found")
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    if target == "go":
        from toolchain2.emit.go.emitter import emit_go_module
        for m in link_result.linked_modules:
            code = emit_go_module(m.east_doc)
            if code.strip() == "": continue
            (output_dir / (m.module_id.replace(".", "_") + ".go")).write_text(code, encoding="utf-8")
            written += 1
    elif target == "cpp":
        from toolchain2.emit.cpp.emitter import emit_cpp_module
        for m in link_result.linked_modules:
            code = emit_cpp_module(m.east_doc)
            if code.strip() == "": continue
            (output_dir / (m.module_id.replace(".", "_") + ".cpp")).write_text(code, encoding="utf-8")
            written += 1
    print("build: emitted " + str(written) + " " + target + " files to " + str(output_dir))
    return 0


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

_COMMANDS = {
    "-parse": cmd_parse,
    "-resolve": cmd_resolve,
    "-compile": cmd_compile,
    "-optimize": cmd_optimize,
    "-link": cmd_link,
    "-emit": cmd_emit,
    "-build": cmd_build,
}


def main() -> int:
    argv = sys.argv[1:]
    if len(argv) == 0 or argv[0] == "-h" or argv[0] == "--help":
        print("usage: pytra-cli2 <command> [options]")
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
        print("golden file generation: python3 tools/generate_golden.py --help")
        return 0

    cmd_name = argv[0]
    cmd_fn = _COMMANDS.get(cmd_name)
    if cmd_fn is None:
        print("error: unknown command: " + cmd_name)
        print("run 'pytra-cli2 --help' for available commands")
        return 1

    return cmd_fn(argv[1:])


if __name__ == "__main__":
    sys.exit(main())
