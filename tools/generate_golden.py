#!/usr/bin/env python3
"""golden file 生成ツール: 現行 toolchain/ を使って各段の golden file を生成する。

pytra-cli2.py (selfhost 対象) とは分離された開発支援ツール。
toolchain/ に依存するため selfhost 非対象。

使い方:
  # sample (デフォルト)
  python3 tools/generate_golden.py --stage=east1
  python3 tools/generate_golden.py --stage=east2
  python3 tools/generate_golden.py --stage=east3
  python3 tools/generate_golden.py --stage=east3-opt

  # fixture
  python3 tools/generate_golden.py --case-root=fixture --stage=east1
  python3 tools/generate_golden.py --case-root=fixture --stage=east2

  # 出力先を明示
  python3 tools/generate_golden.py --stage=east1 -o test/sample/east1/py/

設計文書: docs/ja/plans/plan-pipeline-redesign.md §6.1
"""

from __future__ import annotations

import sys
import json
from pathlib import Path

_GOLDEN_STAGES = ("east1", "east2", "east3", "east3-opt")
_CASE_ROOTS = ("sample", "fixture")

_SAMPLE_SOURCE_DIR = "sample/py"
_FIXTURE_SOURCE_DIR = "test/fixture/source/py"

_SAMPLE_DEFAULT_OUTPUT: dict[str, str] = {
    "east1": "test/sample/east1/py",
    "east2": "test/sample/east2",
    "east3": "test/sample/east3",
    "east3-opt": "test/sample/east3-opt",
}

_FIXTURE_DEFAULT_OUTPUT: dict[str, str] = {
    "east1": "test/fixture/east1/py",
    "east2": "test/fixture/east2",
    "east3": "test/fixture/east3",
    "east3-opt": "test/fixture/east3-opt",
}


def _golden_output_ext(stage: str) -> str:
    if stage == "east1":
        return ".py.east1"
    if stage == "east2":
        return ".east2"
    if stage == "east3" or stage == "east3-opt":
        return ".east3"
    return "." + stage


def _generate_east1(input_path: Path) -> dict[str, object]:
    from toolchain.compile.core_entrypoints import convert_path
    from toolchain.compile.east1 import normalize_east1_root_document

    raw = convert_path(input_path, parser_backend="self_hosted")
    return normalize_east1_root_document(raw)


def _generate_east2(input_path: Path) -> dict[str, object]:
    from toolchain.frontends.transpile_cli import load_east_document

    return load_east_document(input_path, parser_backend="self_hosted")


def _generate_east3(input_path: Path, opt_level: int) -> dict[str, object]:
    from toolchain.frontends.transpile_cli import load_east3_document

    return load_east3_document(
        input_path,
        parser_backend="self_hosted",
        object_dispatch_mode="native",
        east3_opt_level=opt_level,
    )


def _generate_golden(input_path: Path, stage: str) -> dict[str, object]:
    if stage == "east1":
        return _generate_east1(input_path)
    if stage == "east2":
        return _generate_east2(input_path)
    if stage == "east3":
        return _generate_east3(input_path, opt_level=0)
    if stage == "east3-opt":
        return _generate_east3(input_path, opt_level=1)
    raise ValueError(f"unknown stage: {stage}")


def _collect_sources(source_dir: Path) -> list[tuple[Path, str]]:
    """ソースファイルを収集し、(path, relative_stem) のリストを返す。

    サブディレクトリ構造を維持する。例:
      source_dir/collections/add.py → ("collections/add")
      source_dir/01_mandelbrot.py → ("01_mandelbrot")
    """
    sources: list[tuple[Path, str]] = []
    for py_file in sorted(source_dir.rglob("*.py")):
        rel = py_file.relative_to(source_dir)
        stem = str(rel.with_suffix(""))  # "collections/add" or "01_mandelbrot"
        # ng_ prefix はネガティブテスト（parse 失敗を期待）なのでスキップ
        if py_file.stem.startswith("ng_"):
            continue
        sources.append((py_file, stem))
    return sources


def main() -> int:
    stage = ""
    output_dir_text = ""
    case_root = "sample"

    i = 0
    args = sys.argv[1:]
    while i < len(args):
        tok = args[i]
        if tok == "--stage":
            if i + 1 >= len(args):
                print(f"error: missing value for {tok}", file=sys.stderr)
                return 1
            stage = args[i + 1]
            i += 2
            continue
        if tok.startswith("--stage="):
            stage = tok[len("--stage="):]
            i += 1
            continue
        if tok == "--case-root":
            if i + 1 >= len(args):
                print(f"error: missing value for {tok}", file=sys.stderr)
                return 1
            case_root = args[i + 1]
            i += 2
            continue
        if tok.startswith("--case-root="):
            case_root = tok[len("--case-root="):]
            i += 1
            continue
        if tok == "-o" or tok == "--output":
            if i + 1 >= len(args):
                print(f"error: missing value for {tok}", file=sys.stderr)
                return 1
            output_dir_text = args[i + 1]
            i += 2
            continue
        if tok == "--from":
            if i + 1 >= len(args):
                i += 1
                continue
            i += 2
            continue
        if tok.startswith("--from="):
            i += 1
            continue
        if tok == "-h" or tok == "--help":
            print("usage: generate_golden.py --stage=STAGE [--case-root=sample|fixture] [-o DIR]")
            print()
            print("stages: " + ", ".join(_GOLDEN_STAGES))
            print("case roots: " + ", ".join(_CASE_ROOTS))
            print()
            print("examples (sample):")
            print("  generate_golden.py --stage=east1")
            print("  generate_golden.py --stage=east3-opt")
            print()
            print("examples (fixture):")
            print("  generate_golden.py --case-root=fixture --stage=east1")
            print("  generate_golden.py --case-root=fixture --stage=east2")
            return 0
        i += 1

    if stage == "":
        print("error: --stage is required", file=sys.stderr)
        return 1
    if stage not in _GOLDEN_STAGES:
        print(f"error: unknown stage: {stage} (available: {', '.join(_GOLDEN_STAGES)})", file=sys.stderr)
        return 1
    if case_root not in _CASE_ROOTS:
        print(f"error: unknown case-root: {case_root} (available: {', '.join(_CASE_ROOTS)})", file=sys.stderr)
        return 1

    if case_root == "fixture":
        source_dir = Path(_FIXTURE_SOURCE_DIR)
        default_output = _FIXTURE_DEFAULT_OUTPUT
    else:
        source_dir = Path(_SAMPLE_SOURCE_DIR)
        default_output = _SAMPLE_DEFAULT_OUTPUT

    if output_dir_text == "":
        output_dir_text = default_output[stage]
    output_dir = Path(output_dir_text)

    sources = _collect_sources(source_dir)
    if len(sources) == 0:
        print(f"error: no .py files found in {source_dir}", file=sys.stderr)
        return 1

    ext = _golden_output_ext(stage)
    print(f"golden: case_root={case_root}, stage={stage}, sources={len(sources)}, output={output_dir}")
    exit_code = 0
    ok_count = 0
    fail_count = 0
    for src_path, rel_stem in sources:
        out_path = output_dir / (rel_stem + ext)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            doc = _generate_golden(src_path, stage)
            out_path.write_text(
                json.dumps(doc, ensure_ascii=False, indent=2, default=str) + "\n",
                encoding="utf-8",
            )
            print(f"  ok: {out_path}")
            ok_count += 1
        except Exception as e:
            print(f"  FAIL: {src_path}: {e}", file=sys.stderr)
            fail_count += 1
            exit_code = 1

    print(f"golden: {ok_count} ok, {fail_count} failed")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
