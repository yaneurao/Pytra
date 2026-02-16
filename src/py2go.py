#!/usr/bin/env python3
"""Python -> Go 変換 CLI。"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

try:
    from common.go_java_native_transpiler import GoJavaConfig, GoJavaNativeTranspiler
except ModuleNotFoundError:
    from src.common.go_java_native_transpiler import GoJavaConfig, GoJavaNativeTranspiler


def transpile(input_path: str, output_path: str) -> None:
    """Python ファイルを Go コードへ変換する。"""
    in_path = Path(input_path)
    out_path = Path(output_path)
    this_dir = Path(__file__).resolve().parent
    transpiler = GoJavaNativeTranspiler(
        GoJavaConfig(
            language_name="Go",
            target="go",
            file_header="// このファイルは自動生成です（Python -> Go native mode）。",
            runtime_template_path=this_dir / "go_module" / "py_runtime.go",
        ),
    )
    code = transpiler.transpile_path(in_path, out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(code, encoding="utf-8")


def main() -> int:
    """CLI エントリポイント。"""
    parser = argparse.ArgumentParser(description="Transpile Python source to Go")
    parser.add_argument("input", help="Input Python file")
    parser.add_argument("output", help="Output Go file")
    args = parser.parse_args()

    try:
        transpile(args.input, args.output)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
