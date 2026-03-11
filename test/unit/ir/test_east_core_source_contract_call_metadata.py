"""Source-contract regressions for EAST core call metadata clusters."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import CORE_CALL_ANNOTATION_SOURCE_PATH
from _east_core_test_support import CORE_RUNTIME_CALL_SEMANTICS_SOURCE_PATH
from _east_core_test_support import CORE_SOURCE_PATH


class EastCoreSourceContractCallMetadataTest(unittest.TestCase):
    def test_core_source_routes_method_call_metadata_through_shared_helper(self) -> None:
        text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        runtime_text = CORE_RUNTIME_CALL_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = runtime_text.split("def _sh_annotate_runtime_method_call_expr", 1)[1].split(
            "def _sh_annotate_enumerate_call_expr",
            1,
        )[0]
        runtime_apply_text = text.split("def _apply_runtime_method_call_expr_annotation", 1)[1].split(
            "def _apply_attr_call_expr_annotation",
            1,
        )[0]
        apply_text = text.split("def _apply_attr_call_expr_annotation", 1)[1].split(
            "def _resolve_attr_expr_annotation",
            1,
        )[0]
        attr_call_text = annotation_text.split("def _annotate_attr_call_expr", 1)[1].split(
            "def _resolve_attr_expr_annotation",
            1,
        )[0]
        postfix_text = core_text.split("def _parse_postfix", 1)[1].split("def _parse_primary", 1)[0]

        self.assertIn('lookup_owner_method_semantic_tag(owner_type, attr)', helper_text)
        self.assertIn('lookup_stdlib_method_runtime_call(owner_type, attr)', helper_text)
        self.assertIn('_sh_annotate_runtime_call_expr(', helper_text)
        self.assertIn('_sh_annotate_runtime_method_call_expr(', runtime_apply_text)
        self.assertIn("self._apply_runtime_method_call_expr_annotation(", apply_text)
        self.assertIn("return self._apply_attr_call_expr_annotation(", attr_call_text)
        self.assertNotIn('owner_method_semantic_tag = lookup_owner_method_semantic_tag(owner_t, attr)', postfix_text)
        self.assertNotIn('payload["semantic_tag"] = owner_method_semantic_tag', postfix_text)
        self.assertNotIn('rc = lookup_stdlib_method_runtime_call(owner_t, attr)', postfix_text)

    def test_core_source_routes_enumerate_metadata_through_shared_helper(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        runtime_text = CORE_RUNTIME_CALL_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = runtime_text.split("def _sh_annotate_enumerate_call_expr", 1)[1].split(
            "def _sh_annotate_stdlib_function_call_expr",
            1,
        )[0]
        named_call_text = annotation_text.split("def _annotate_named_call_expr", 1)[1].split(
            "def _annotate_builtin_named_call_expr",
            1,
        )[0]
        postfix_text = text.split("def _parse_postfix", 1)[1].split("def _parse_primary", 1)[0]

        self.assertIn('_sh_annotate_runtime_call_expr(', helper_text)
        self.assertIn('payload["iterable_trait"] = "yes" if iter_element_type != "unknown" else "unknown"', helper_text)
        self.assertIn('payload["iter_protocol"] = "static_range"', helper_text)
        self.assertIn('payload["resolved_type"] = f"list[tuple[int64, {iter_element_type}]]"', helper_text)
        self.assertIn("return self._apply_named_call_dispatch(", named_call_text)
        self.assertNotIn('payload["iterable_trait"] = "yes" if elem_t != "unknown" else "unknown"', postfix_text)
        self.assertNotIn('payload["iter_protocol"] = "static_range"', postfix_text)
        self.assertNotIn('payload["iter_element_type"] = elem_t', postfix_text)

    def test_core_source_routes_stdlib_function_metadata_through_shared_helper(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        runtime_text = CORE_RUNTIME_CALL_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = runtime_text.split("def _sh_annotate_stdlib_function_call_expr", 1)[1].split(
            "def _sh_annotate_stdlib_symbol_call_expr",
            1,
        )[0]
        named_call_text = annotation_text.split("def _annotate_named_call_expr", 1)[1].split(
            "def _annotate_builtin_named_call_expr",
            1,
        )[0]
        postfix_text = text.split("def _parse_postfix", 1)[1].split("def _parse_primary", 1)[0]

        self.assertIn("lookup_stdlib_function_runtime_binding(fn_name)", helper_text)
        self.assertIn("lookup_stdlib_function_return_type(fn_name)", helper_text)
        self.assertIn('_sh_annotate_runtime_call_expr(', helper_text)
        self.assertIn("return self._apply_named_call_dispatch(", named_call_text)
        self.assertNotIn("mod_id, runtime_symbol = lookup_stdlib_function_runtime_binding(fn_name)", postfix_text)
        self.assertNotIn("sig_ret = lookup_stdlib_function_return_type(fn_name)", postfix_text)
        self.assertNotIn('payload["resolved_type"] = sig_ret', postfix_text)

    def test_core_source_routes_stdlib_symbol_metadata_through_shared_helper(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        runtime_text = CORE_RUNTIME_CALL_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = runtime_text.split("def _sh_annotate_stdlib_symbol_call_expr", 1)[1].split(
            "def _sh_annotate_noncpp_symbol_call_expr",
            1,
        )[0]
        named_call_text = annotation_text.split("def _annotate_named_call_expr", 1)[1].split(
            "def _annotate_builtin_named_call_expr",
            1,
        )[0]
        postfix_text = text.split("def _parse_postfix", 1)[1].split("def _parse_primary", 1)[0]

        self.assertIn("lookup_stdlib_imported_symbol_runtime_binding(fn_name, import_symbols)", helper_text)
        self.assertIn('_sh_annotate_runtime_call_expr(', helper_text)
        self.assertIn("return self._apply_named_call_dispatch(", named_call_text)
        self.assertNotIn(
            "mod_id, runtime_symbol = lookup_stdlib_imported_symbol_runtime_binding(fn_name, _SH_IMPORT_SYMBOLS)",
            postfix_text,
        )

    def test_core_source_routes_noncpp_symbol_metadata_through_shared_helper(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        runtime_text = CORE_RUNTIME_CALL_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = runtime_text.split("def _sh_annotate_noncpp_symbol_call_expr", 1)[1].split(
            "def _sh_lookup_noncpp_attr_runtime_call",
            1,
        )[0]
        named_call_text = annotation_text.split("def _annotate_named_call_expr", 1)[1].split(
            "def _annotate_builtin_named_call_expr",
            1,
        )[0]
        postfix_text = text.split("def _parse_postfix", 1)[1].split("def _parse_primary", 1)[0]

        self.assertIn("binding = import_symbols.get(fn_name)", helper_text)
        self.assertIn("lookup_runtime_binding_semantic_tag(mod_id, runtime_symbol)", helper_text)
        self.assertIn('_sh_annotate_resolved_runtime_expr(', helper_text)
        self.assertIn("return self._apply_named_call_dispatch(", named_call_text)
        self.assertNotIn("binding = import_symbols.get(fn_name)", postfix_text)
        self.assertNotIn("binding_semantic_tag = lookup_runtime_binding_semantic_tag(mod_id, runtime_symbol)", postfix_text)

    def test_core_source_centralizes_noncpp_attr_runtime_lookup(self) -> None:
        text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        runtime_text = CORE_RUNTIME_CALL_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = runtime_text.split("def _sh_lookup_noncpp_attr_runtime_call", 1)[1].split(
            "def _sh_annotate_noncpp_attr_call_expr",
            1,
        )[0]
        noncpp_apply_text = text.split("def _apply_noncpp_attr_call_expr_annotation", 1)[1].split(
            "def _apply_runtime_method_call_expr_annotation",
            1,
        )[0]
        apply_text = text.split("def _apply_attr_call_expr_annotation", 1)[1].split(
            "def _resolve_attr_expr_annotation",
            1,
        )[0]
        attr_call_text = annotation_text.split("def _annotate_attr_call_expr", 1)[1].split(
            "def _resolve_attr_expr_annotation",
            1,
        )[0]
        postfix_text = core_text.split("def _parse_postfix", 1)[1].split("def _parse_primary", 1)[0]

        self.assertIn("def _sh_lookup_noncpp_attr_runtime_call(", runtime_text)
        self.assertIn("if owner_name in import_modules:", helper_text)
        self.assertIn("if owner_name in import_symbols:", helper_text)
        self.assertEqual(postfix_text.count("_sh_lookup_noncpp_attr_runtime_call("), 0)
        self.assertIn("_sh_annotate_noncpp_attr_call_expr(", noncpp_apply_text)
        self.assertIn("self._apply_noncpp_attr_call_expr_annotation(", apply_text)
        self.assertIn("return self._apply_attr_call_expr_annotation(", attr_call_text)
        self.assertNotIn("if isinstance(owner_expr, dict) and owner_expr.get(\"kind\") == \"Name\":", postfix_text)
        self.assertNotIn("if isinstance(owner, dict) and owner.get(\"kind\") == \"Name\":", postfix_text)

    def test_core_source_routes_noncpp_attr_call_annotations_through_shared_helper(self) -> None:
        text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        runtime_text = CORE_RUNTIME_CALL_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = runtime_text.split("def _sh_annotate_noncpp_attr_call_expr", 1)[1].split(
            "def _sh_annotate_scalar_ctor_call_expr",
            1,
        )[0]
        noncpp_apply_text = text.split("def _apply_noncpp_attr_call_expr_annotation", 1)[1].split(
            "def _apply_runtime_method_call_expr_annotation",
            1,
        )[0]
        attr_call_apply_text = text.split("def _apply_attr_call_expr_annotation", 1)[1].split(
            "def _resolve_attr_expr_annotation",
            1,
        )[0]
        attr_call_text = annotation_text.split("def _annotate_attr_call_expr", 1)[1].split(
            "def _resolve_attr_expr_annotation",
            1,
        )[0]
        postfix_text = core_text.split("def _parse_postfix", 1)[1].split("def _parse_primary", 1)[0]

        self.assertIn("_sh_lookup_noncpp_attr_runtime_call(", helper_text)
        self.assertIn("import_modules=import_modules", helper_text)
        self.assertIn("import_symbols=import_symbols", helper_text)
        self.assertIn("_sh_annotate_resolved_runtime_expr(", helper_text)
        self.assertIn('payload["resolved_type"] = std_module_attr_ret', helper_text)
        self.assertIn("_sh_annotate_noncpp_attr_call_expr(", noncpp_apply_text)
        self.assertIn("self._apply_noncpp_attr_call_expr_annotation(", attr_call_apply_text)
        self.assertIn("return self._apply_attr_call_expr_annotation(", attr_call_text)
        self.assertNotIn("std_module_attr_ret = lookup_stdlib_function_return_type(attr)", postfix_text)
        self.assertNotIn('payload["resolved_type"] = std_module_attr_ret', postfix_text)

    def test_core_source_routes_attr_call_annotations_through_parser_helper(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("class _ShExprCallAnnotationMixin:", annotation_text)
        self.assertIn("def _apply_attr_callee_call_annotation(", annotation_text)
        self.assertIn("def _apply_callee_call_annotation(", annotation_text)
        self.assertIn("def _resolve_callee_call_annotation_kind(", annotation_text)
        self.assertIn("def _resolve_callee_call_annotation_state(", annotation_text)
        self.assertIn("def _annotate_callee_call_expr(", annotation_text)
        self.assertIn("def _apply_call_expr_annotation(", annotation_text)
        self.assertIn("def _annotate_call_expr(", annotation_text)
        self.assertIn("return self._annotate_attr_call_expr(", annotation_text)
        self.assertIn("return self._apply_callee_call_annotation(", annotation_text)
        self.assertIn("return self._annotate_callee_call_expr(", annotation_text)
        self.assertIn("from toolchain.ir.core_expr_call_annotation import _ShExprCallAnnotationMixin", core_text)
        self.assertIn("_ShExprCallAnnotationMixin", core_text)
        self.assertIn("def _resolve_attr_call_annotation_state(", annotation_text)
        self.assertIn("def _apply_attr_call_expr_annotation(", annotation_text)
        self.assertIn("def _annotate_attr_call_expr(", annotation_text)
        self.assertNotIn("def _apply_attr_callee_call_annotation(", core_text)
        self.assertNotIn("def _apply_callee_call_annotation(", core_text)
        self.assertNotIn("def _resolve_callee_call_annotation_kind(", core_text)
        self.assertNotIn("def _annotate_callee_call_expr(", core_text)
        self.assertNotIn("def _annotate_call_expr(", core_text)
        self.assertNotIn("def _apply_attr_call_expr_annotation(", core_text)

    def test_core_source_routes_scalar_ctor_metadata_through_shared_helper(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        runtime_text = CORE_RUNTIME_CALL_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = runtime_text.split("def _sh_annotate_scalar_ctor_call_expr", 1)[1].split(
            "def _sh_annotate_minmax_call_expr",
            1,
        )[0]
        named_call_text = annotation_text.split("def _annotate_named_call_expr", 1)[1].split(
            "def _annotate_builtin_named_call_expr",
            1,
        )[0]
        postfix_text = text.split("def _parse_postfix", 1)[1].split("def _parse_primary", 1)[0]

        self.assertIn('runtime_call = "static_cast"', helper_text)
        self.assertIn('if fn_name == "int" and arg_count == 2:', helper_text)
        self.assertIn('runtime_call = "py_to_int64_base"', helper_text)
        self.assertIn('elif fn_name == "bool" and arg_count == 1 and use_truthy_runtime:', helper_text)
        self.assertIn('runtime_call = "py_to_bool"', helper_text)
        self.assertIn('_sh_annotate_runtime_call_expr(', helper_text)
        self.assertIn("return self._apply_named_call_dispatch(", named_call_text)
        self.assertNotIn('runtime_call = "static_cast"', postfix_text)
        self.assertNotIn('runtime_call = "py_to_int64_base"', postfix_text)
        self.assertNotIn('runtime_call = "py_to_bool"', postfix_text)
        self.assertNotIn('runtime_module_id = "pytra.core.py_runtime"', postfix_text)
        self.assertNotIn('runtime_symbol = "py_to_int64_base"', postfix_text)

    def test_core_source_routes_minmax_metadata_through_shared_helper(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        runtime_text = CORE_RUNTIME_CALL_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = runtime_text.split("def _sh_annotate_minmax_call_expr", 1)[1].split(
            "def _sh_annotate_collection_ctor_call_expr",
            1,
        )[0]
        named_call_text = annotation_text.split("def _annotate_named_call_expr", 1)[1].split(
            "def _annotate_builtin_named_call_expr",
            1,
        )[0]
        postfix_text = text.split("def _parse_postfix", 1)[1].split("def _parse_primary", 1)[0]

        self.assertIn('_sh_annotate_runtime_call_expr(', helper_text)
        self.assertIn('runtime_call="py_min" if fn_name == "min" else "py_max"', helper_text)
        self.assertIn('module_id="pytra.core.py_runtime"', helper_text)
        self.assertIn("return self._apply_named_call_dispatch(", named_call_text)
        self.assertNotIn('elif fn_name in {"min", "max"}:\n                    _sh_annotate_runtime_call_expr(', postfix_text)
        self.assertNotIn('runtime_call="py_min" if fn_name == "min" else "py_max"', postfix_text)
