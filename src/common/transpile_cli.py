"""トランスパイラ CLI の共通引数定義。"""

from __future__ import annotations

import argparse
from pylib.typing import Iterable


def add_common_transpile_args(
    parser: argparse.ArgumentParser,
    *,
    enable_negative_index_mode: bool = False,
    parser_backends: Iterable[str] | None = None,
) -> None:
    """各トランスパイラで共通利用する CLI 引数を追加する。"""
    parser.add_argument("input", help="Input .py or EAST .json")
    parser.add_argument("-o", "--output", help="Output file path")
    if enable_negative_index_mode:
        parser.add_argument(
            "--negative-index-mode",
            choices=["always", "const_only", "off"],
            help="Policy for Python-style negative indexing on list/str subscripts",
        )
    if parser_backends is not None:
        choices = list(parser_backends)
        parser.add_argument(
            "--parser-backend",
            choices=choices,
            help="EAST parser backend for .py input",
        )


def normalize_common_transpile_args(
    args: argparse.Namespace,
    *,
    default_negative_index_mode: str | None = None,
    default_parser_backend: str | None = None,
) -> argparse.Namespace:
    """共通引数の既定値を埋める。"""
    if default_negative_index_mode is not None:
        cur = getattr(args, "negative_index_mode", None)
        if not cur:
            setattr(args, "negative_index_mode", default_negative_index_mode)
    if default_parser_backend is not None:
        cur = getattr(args, "parser_backend", None)
        if not cur:
            setattr(args, "parser_backend", default_parser_backend)
    return args
