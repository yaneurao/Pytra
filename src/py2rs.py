#!/usr/bin/env python3
# Python -> Rust の変換器（最小実装）。
# 生成される Rust は Python スクリプト本体を埋め込み、Python 実行環境で実行します。

from __future__ import annotations

import argparse
from pathlib import Path
import sys


def _rust_raw_string_literal(text: str) -> str:
    """任意テキストを Rust の raw string literal へ変換する。"""
    for n in range(1, 32):
        fence = "#" * n
        end_seq = f'"{fence}'
        if end_seq not in text:
            return f'r{fence}"{text}"{fence}'
    # ほぼ起こらない保険。通常文字列へエスケープする。
    escaped = (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    return f'"{escaped}"'


def transpile_file(input_path: Path, output_path: Path) -> None:
    source = input_path.read_text(encoding="utf-8")
    source_literal = _rust_raw_string_literal(source)
    input_name = input_path.name

    rust = f"""// このファイルは自動生成です。編集しないでください。
// 入力 Python: {input_name}

use std::env;
use std::process::Command;

fn run_with(interpreter: &str, source: &str) -> Option<i32> {{
    let mut cmd = Command::new(interpreter);
    cmd.arg("-c").arg(source);

    // sample/py が `from py_module ...` を使うため `PYTHONPATH=src` を付与する。
    let py_path = match env::var("PYTHONPATH") {{
        Ok(v) if !v.is_empty() => format!("src:{{}}", v),
        _ => "src".to_string(),
    }};
    cmd.env("PYTHONPATH", py_path);

    // 親プロセスの標準入出力をそのまま使う。
    let status = cmd.status().ok()?;
    Some(status.code().unwrap_or(1))
}}

fn main() {{
    let source: &str = {source_literal};

    // python3 を優先し、無ければ python を試す。
    if let Some(code) = run_with("python3", source) {{
        std::process::exit(code);
    }}
    if let Some(code) = run_with("python", source) {{
        std::process::exit(code);
    }}

    eprintln!("error: python interpreter not found (python3/python)");
    std::process::exit(1);
}}
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rust, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Transpile Python to Rust")
    parser.add_argument("input", help="input Python file")
    parser.add_argument("output", help="output Rust file")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    try:
        transpile_file(input_path, output_path)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
