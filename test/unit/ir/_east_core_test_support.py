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
CORE_AST_BUILDERS_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_ast_builders.py"
CORE_BUILDER_BASE_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_builder_base.py"
CORE_CALL_ARG_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_expr_call_args.py"
CORE_EXPR_PARSER_BASE_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_expr_parser_base.py"
CORE_ENTRYPOINTS_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_entrypoints.py"
CORE_EXPR_PRECEDENCE_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_expr_precedence.py"
CORE_CALL_SUFFIX_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_expr_call_suffix.py"
CORE_CLASS_SEMANTICS_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_class_semantics.py"
CORE_DECORATOR_SEMANTICS_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_decorator_semantics.py"
CORE_EXTERN_SEMANTICS_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_extern_semantics.py"
CORE_IMPORT_SEMANTICS_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_import_semantics.py"
CORE_IMPORT_MODULE_BUILDERS_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_import_module_builders.py"
CORE_STMT_ANALYSIS_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_stmt_analysis.py"
CORE_STRING_SEMANTICS_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_string_semantics.py"
CORE_STMT_TEXT_SEMANTICS_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_stmt_text_semantics.py"
CORE_TEXT_SEMANTICS_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_text_semantics.py"
CORE_TYPE_SEMANTICS_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_type_semantics.py"
CORE_RUNTIME_CALL_SEMANTICS_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_runtime_call_semantics.py"
CORE_RUNTIME_DECL_SEMANTICS_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_runtime_decl_semantics.py"
CORE_SIGNATURE_SEMANTICS_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_signature_semantics.py"
CORE_STMT_BUILDERS_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_stmt_builders.py"
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
