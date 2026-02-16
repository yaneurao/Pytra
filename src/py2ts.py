#!/usr/bin/env python3
"""Python -> TypeScript 変換 CLI。"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

try:
    from common.node_embedded_python_transpiler import (
        NodeEmbeddedPythonTranspiler,
        NodeEmbeddedTranspileConfig,
    )
except ModuleNotFoundError:
    from src.common.node_embedded_python_transpiler import (
        NodeEmbeddedPythonTranspiler,
        NodeEmbeddedTranspileConfig,
    )


def transpile(input_path: str, output_path: str) -> None:
    """入力 Python ファイルを TypeScript へ変換する。"""
    in_path = Path(input_path)
    out_path = Path(output_path)
    transpiler = NodeEmbeddedPythonTranspiler(
        NodeEmbeddedTranspileConfig(
            language_name="TypeScript",
            file_header="// このファイルは自動生成です（Python -> TypeScript）。",
            use_typescript=True,
        )
    )
    code = transpiler.transpile_path(in_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(code, encoding="utf-8")


def main() -> int:
    """CLI エントリポイント。"""
    parser = argparse.ArgumentParser(description="Transpile Python subset to TypeScript")
    parser.add_argument("input", help="Input Python file")
    parser.add_argument("output", help="Output TypeScript file")
    args = parser.parse_args()

    try:
        transpile(args.input, args.output)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
