#!/usr/bin/env python3
"""pytra-cli2: 新パイプライン CLI (parse / resolve / compile / optimize / emit).

設計文書: docs/ja/plans/plan-pipeline-redesign.md

パイプライン:
  -parse      .py → .py.east1         Python 構文解析
  -resolve    *.py.east1 → *.east2    型解決 + 正規化 (言語固有→言語非依存)
  -compile    *.east2 → *.east3       core lowering (言語非依存)
  -optimize   *.east3 → *.east3       whole-program 最適化
  -emit       *.east3 → *.cpp 等      target コード生成
  -build      .py → target            一括実行

selfhost 対象 (§5.7): toolchain2/ + pytra.std.* のみ使用。
golden file 生成は tools/generate_golden.py に分離。
"""

from __future__ import annotations

from pytra.std import sys
from pytra.std import json
from pytra.std.pathlib import Path

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

    # TODO: toolchain2/parse/py/ の自前パーサーに切り替える。
    # 暫定で toolchain/ を使用（selfhost 移行完了まで）。
    from toolchain.compile.core_entrypoints import convert_path
    from toolchain.compile.east1 import normalize_east1_root_document

    try:
        raw_east = convert_path(input_path, parser_backend="self_hosted")
        east1_doc = normalize_east1_root_document(raw_east)
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

    if not input_path.exists():
        print("error: file not found: " + str(input_path))
        return 1

    try:
        result = resolve_file(input_path)
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
# compile: *.east2 → *.east3 (未実装)
# ---------------------------------------------------------------------------

def cmd_compile(args: list[str]) -> int:
    print("error: -compile is not yet implemented")
    return 1


# ---------------------------------------------------------------------------
# optimize: *.east3 → *.east3 (未実装)
# ---------------------------------------------------------------------------

def cmd_optimize(args: list[str]) -> int:
    print("error: -optimize is not yet implemented")
    return 1


# ---------------------------------------------------------------------------
# emit: *.east3 → target (未実装)
# ---------------------------------------------------------------------------

def cmd_emit(args: list[str]) -> int:
    print("error: -emit is not yet implemented")
    return 1


# ---------------------------------------------------------------------------
# build: .py → target (一括実行, 未実装)
# ---------------------------------------------------------------------------

def cmd_build(args: list[str]) -> int:
    print("error: -build is not yet implemented")
    return 1


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

_COMMANDS = {
    "-parse": cmd_parse,
    "-resolve": cmd_resolve,
    "-compile": cmd_compile,
    "-optimize": cmd_optimize,
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
