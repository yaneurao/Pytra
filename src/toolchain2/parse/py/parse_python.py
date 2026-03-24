"""Python frontend: .py → .py.east1

自前パーサーで Python ソースを EAST1 (east_stage=1) に変換する。
toolchain/ には依存しない。
"""

from __future__ import annotations

from toolchain2.parse.py.nodes import Module, JsonVal
from toolchain2.parse.py.parser import parse_python_source


def parse_python_file_to_module(input_path: str) -> Module:
    """ファイルを読み込み、EAST1 Module ノードを返す。"""
    with open(input_path, encoding="utf-8") as f:
        source = f.read()
    return parse_python_source(source, input_path)


def parse_python_file(input_path: str) -> dict[str, JsonVal]:
    """ファイルを読み込み、EAST1 ドキュメント (dict) を返す。"""
    module = parse_python_file_to_module(input_path)
    return module.to_jv()
