#!/usr/bin/env python3
"""Python -> Swift 変換 CLI。"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

try:
    from common.swift_kotlin_node_transpiler import SwiftKotlinNodeConfig, SwiftKotlinNodeTranspiler
except ModuleNotFoundError:
    from src.common.swift_kotlin_node_transpiler import SwiftKotlinNodeConfig, SwiftKotlinNodeTranspiler


def transpile(input_path: str, output_path: str) -> None:
    """Python ファイルを Swift コードへ変換する。"""
    in_path = Path(input_path)
    out_path = Path(output_path)
    this_dir = Path(__file__).resolve().parent
    transpiler = SwiftKotlinNodeTranspiler(
        SwiftKotlinNodeConfig(
            language_name="Swift",
            file_header="// このファイルは自動生成です（Python -> Swift node-backed mode）。",
            target="swift",  # Swift コードを生成し、実行時は Node.js で処理する。
            runtime_template_path=this_dir / "swift_module" / "py_runtime.swift",
        )
    )
    code = transpiler.transpile_path(in_path, out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(code, encoding="utf-8")


def main() -> int:
    """CLI エントリポイント。"""
    parser = argparse.ArgumentParser(description="Transpile Python source to Swift")
    parser.add_argument("input", help="Input Python file")
    parser.add_argument("output", help="Output Swift file")
    args = parser.parse_args()

    try:
        transpile(args.input, args.output)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
