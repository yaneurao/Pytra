"""Shared assertions for comment-fidelity smoke tests."""

from __future__ import annotations

from typing import Iterable
from unittest import TestCase


_FORBIDDEN_COMMENT_SNIPPETS: tuple[str, ...] = (
    "Auto-generated",
    "Runtime helpers are provided",
    "TypeScript プレビュー出力",
    "TODO: unsupported",
    "unsupported stmt",
    "__main__ guard",
    "// pass",
    "# pass",
    "-- pass",
    "/* pass */",
)


def assert_no_generated_comments(tc: TestCase, code: str) -> None:
    """Emitter 固有の固定コメントが混入していないことを確認する。"""
    for snippet in _FORBIDDEN_COMMENT_SNIPPETS:
        tc.assertNotIn(snippet, code)


def assert_sample01_module_comments(tc: TestCase, code: str, *, prefix: str) -> None:
    """sample/py/01 の先頭コメントが出力へ伝播していることを確認する。"""
    expected_lines: Iterable[str] = (
        f"{prefix} 01: Sample that outputs the Mandelbrot set as a PNG image.",
        f"{prefix} Syntax is kept straightforward with future transpilation in mind.",
    )
    for line in expected_lines:
        tc.assertIn(line, code)
