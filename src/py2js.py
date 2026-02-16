#!/usr/bin/env python3
"""Python -> JavaScript 変換 CLI。"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

try:
    from common.js_ts_native_transpiler import JsTsConfig, JsTsNativeTranspiler
except ModuleNotFoundError:
    from src.common.js_ts_native_transpiler import JsTsConfig, JsTsNativeTranspiler


def transpile(input_path: str, output_path: str) -> None:
    in_path = Path(input_path)
    out_path = Path(output_path)
    transpiler = JsTsNativeTranspiler(
        JsTsConfig(
            language_name="JavaScript",
            file_header="// このファイルは自動生成です（Python -> JavaScript native mode）。",
            runtime_ext="js",
        )
    )
    code = transpiler.transpile_path(in_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(code, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Transpile Python subset to JavaScript")
    parser.add_argument("input", help="Input Python file")
    parser.add_argument("output", help="Output JavaScript file")
    args = parser.parse_args()

    try:
        transpile(args.input, args.output)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
