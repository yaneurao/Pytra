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
CORE_CALLEE_CALL_ANNOTATION_SOURCE_PATH = (
    ROOT / "src" / "toolchain" / "ir" / "core_expr_callee_call_annotation.py"
)
CORE_EXPR_SHELL_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_expr_shell.py"
CORE_EXPR_PARSER_BASE_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_expr_parser_base.py"
CORE_EXPR_LOWERED_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_expr_lowered.py"
CORE_EXPR_PRIMARY_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_expr_primary.py"
CORE_EXPR_RESOLUTION_SEMANTICS_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_expr_resolution_semantics.py"
CORE_ENTRYPOINTS_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_entrypoints.py"
CORE_EXPR_PRECEDENCE_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_expr_precedence.py"
CORE_CALL_SUFFIX_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_expr_call_suffix.py"
CORE_NAMED_CALL_ANNOTATION_SOURCE_PATH = (
    ROOT / "src" / "toolchain" / "ir" / "core_expr_named_call_annotation.py"
)
CORE_ATTR_CALL_ANNOTATION_SOURCE_PATH = (
    ROOT / "src" / "toolchain" / "ir" / "core_expr_attr_call_annotation.py"
)
CORE_CALLEE_CALL_ANNOTATION_SOURCE_PATH = (
    ROOT / "src" / "toolchain" / "ir" / "core_expr_callee_call_annotation.py"
)
CORE_ATTR_SUFFIX_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_expr_attr_suffix.py"
CORE_SUBSCRIPT_SUFFIX_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_expr_subscript_suffix.py"
CORE_CLASS_SEMANTICS_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_class_semantics.py"
CORE_DECORATOR_SEMANTICS_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_decorator_semantics.py"
CORE_DATACLASS_FIELD_SEMANTICS_SOURCE_PATH = (
    ROOT / "src" / "toolchain" / "ir" / "core_dataclass_field_semantics.py"
)
CORE_EXTERN_SEMANTICS_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_extern_semantics.py"
CORE_IMPORT_SEMANTICS_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_import_semantics.py"
CORE_IMPORT_MODULE_BUILDERS_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_import_module_builders.py"
CORE_MODULE_PARSER_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_module_parser.py"
CORE_PARSE_CONTEXT_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_parse_context.py"
CORE_STMT_ANALYSIS_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_stmt_analysis.py"
CORE_STMT_IF_SEMANTICS_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_stmt_if_semantics.py"
CORE_STMT_PARSER_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "core_stmt_parser.py"
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
EAST23_LOWERING_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "east2_to_east3_lowering.py"
EAST23_CALL_METADATA_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "east2_to_east3_call_metadata.py"
EAST23_DISPATCH_ORCHESTRATION_SOURCE_PATH = (
    ROOT / "src" / "toolchain" / "ir" / "east2_to_east3_dispatch_orchestration.py"
)
EAST23_STMT_LOWERING_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "east2_to_east3_stmt_lowering.py"
EAST23_NOMINAL_ADT_META_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "east2_to_east3_nominal_adt_meta.py"
EAST23_TYPE_ID_PREDICATE_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "east2_to_east3_type_id_predicate.py"
EAST23_TYPE_SUMMARY_SOURCE_PATH = ROOT / "src" / "toolchain" / "ir" / "east2_to_east3_type_summary.py"


def _walk(node: Any):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for it in node:
            yield from _walk(it)
