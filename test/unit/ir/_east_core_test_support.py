"""Shared support for EAST core regression tests."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

CORE_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core.py"
CORE_CALL_ARG_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_expr_call_args.py"
CORE_CALL_SUFFIX_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_expr_call_suffix.py"
CORE_CLASS_SEMANTICS_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_class_semantics.py"
CORE_CALL_ANNOTATION_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_expr_call_annotation.py"
CORE_ATTR_SUBSCRIPT_ANNOTATION_SOURCE_PATH = (
    ROOT / "src" / "toolchain" / "ir" / "core_expr_attr_subscript_annotation.py"
)
CORE_ATTR_SUBSCRIPT_SUFFIX_SOURCE_PATH = (
    ROOT / "src" / "toolchain" / "ir" / "core_expr_attr_subscript_suffix.py"
)


def _walk(node: Any):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for it in node:
            yield from _walk(it)
