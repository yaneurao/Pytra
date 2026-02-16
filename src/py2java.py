#!/usr/bin/env python3
"""Python -> Java 変換 CLI。"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

try:
    from common.embedded_python_transpiler import EmbeddedTranspileConfig, EmbeddedPythonTranspiler
except ModuleNotFoundError:
    from src.common.embedded_python_transpiler import EmbeddedTranspileConfig, EmbeddedPythonTranspiler


def transpile(input_path: str, output_path: str) -> None:
    """Python ファイルを Java コードへ変換する。"""
    in_path = Path(input_path)
    out_path = Path(output_path)
    this_dir = Path(__file__).resolve().parent
    transpiler = EmbeddedPythonTranspiler(
        EmbeddedTranspileConfig(
            language_name="Java",
            file_header="// このファイルは自動生成です（Python -> Java embedded mode）。",
            target="java",
            runtime_template_path=this_dir / "java_module" / "PyRuntime.java",
        )
    )
    code = transpiler.transpile_path(in_path, out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(code, encoding="utf-8")


def main() -> int:
    """CLI エントリポイント。"""
    parser = argparse.ArgumentParser(description="Transpile Python source to Java")
    parser.add_argument("input", help="Input Python file")
    parser.add_argument("output", help="Output Java file")
    args = parser.parse_args()

    try:
        transpile(args.input, args.output)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
