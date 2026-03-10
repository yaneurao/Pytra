"""Unit regression tests for the self_hosted EAST converter."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import CORE_ATTR_SUBSCRIPT_ANNOTATION_SOURCE_PATH
from _east_core_test_support import CORE_ATTR_SUBSCRIPT_SUFFIX_SOURCE_PATH
from _east_core_test_support import CORE_CALL_ANNOTATION_SOURCE_PATH
from _east_core_test_support import CORE_CALL_ARG_SOURCE_PATH
from _east_core_test_support import CORE_CALL_SUFFIX_SOURCE_PATH
from _east_core_test_support import CORE_SOURCE_PATH
from _east_core_test_support import _walk
from src.toolchain.compiler.east import convert_source_to_east_with_backend
from src.toolchain.compiler.east import EastBuildError


class EastCoreTest(unittest.TestCase):
    def test_core_source_routes_collection_ctor_metadata_through_shared_helper(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = text.split("def _sh_annotate_collection_ctor_call_expr", 1)[1].split(
            "def _sh_annotate_anyall_call_expr",
            1,
        )[0]
        named_call_text = annotation_text.split("def _annotate_named_call_expr", 1)[1].split(
            "def _annotate_builtin_named_call_expr",
            1,
        )[0]
        postfix_text = text.split("def _parse_postfix", 1)[1].split("def _parse_primary", 1)[0]

        self.assertIn('runtime_call = fn_name + "_ctor"', helper_text)
        self.assertIn('if fn_name == "bytes":', helper_text)
        self.assertIn('runtime_call = "bytes_ctor"', helper_text)
        self.assertIn('elif fn_name == "bytearray":', helper_text)
        self.assertIn('runtime_call = "bytearray_ctor"', helper_text)
        self.assertIn('_sh_annotate_runtime_call_expr(', helper_text)
        self.assertIn("return self._apply_named_call_dispatch(", named_call_text)
        self.assertNotIn(
            'elif fn_name in {"bytes", "bytearray"}:\n                    _sh_annotate_runtime_call_expr(',
            postfix_text,
        )
        self.assertNotIn(
            'elif fn_name in {"list", "set", "dict"}:\n                    _sh_annotate_runtime_call_expr(',
            postfix_text,
        )
        self.assertNotIn('runtime_call="bytes_ctor" if fn_name == "bytes" else "bytearray_ctor"', postfix_text)
        self.assertNotIn('runtime_call=fn_name + "_ctor"', postfix_text)

    def test_core_source_routes_anyall_metadata_through_shared_helper(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = text.split("def _sh_annotate_anyall_call_expr", 1)[1].split(
            "def _sh_annotate_ordchr_call_expr",
            1,
        )[0]
        named_call_text = annotation_text.split("def _annotate_named_call_expr", 1)[1].split(
            "def _annotate_builtin_named_call_expr",
            1,
        )[0]
        postfix_text = text.split("def _parse_postfix", 1)[1].split("def _parse_primary", 1)[0]

        self.assertIn('_sh_annotate_runtime_call_expr(', helper_text)
        self.assertIn('runtime_call="py_any" if fn_name == "any" else "py_all"', helper_text)
        self.assertIn('module_id="pytra.built_in.predicates"', helper_text)
        self.assertIn("return self._apply_named_call_dispatch(", named_call_text)
        self.assertNotIn('elif fn_name == "any":\n                    _sh_annotate_runtime_call_expr(', postfix_text)
        self.assertNotIn('elif fn_name == "all":\n                    _sh_annotate_runtime_call_expr(', postfix_text)
        self.assertNotIn('runtime_call="py_any" if fn_name == "any" else "py_all"', postfix_text)

    def test_core_source_routes_ordchr_metadata_through_shared_helper(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = text.split("def _sh_annotate_ordchr_call_expr", 1)[1].split(
            "def _sh_annotate_iterator_builtin_call_expr",
            1,
        )[0]
        named_call_text = annotation_text.split("def _annotate_named_call_expr", 1)[1].split(
            "def _annotate_builtin_named_call_expr",
            1,
        )[0]
        postfix_text = text.split("def _parse_postfix", 1)[1].split("def _parse_primary", 1)[0]

        self.assertIn('_sh_annotate_runtime_call_expr(', helper_text)
        self.assertIn('runtime_call="py_ord" if fn_name == "ord" else "py_chr"', helper_text)
        self.assertIn('runtime_symbol="py_ord" if fn_name == "ord" else "py_chr"', helper_text)
        self.assertIn('module_id="pytra.built_in.scalar_ops"', helper_text)
        self.assertIn("return self._apply_named_call_dispatch(", named_call_text)
        self.assertNotIn('elif fn_name == "ord":\n                    _sh_annotate_runtime_call_expr(', postfix_text)
        self.assertNotIn('elif fn_name == "chr":\n                    _sh_annotate_runtime_call_expr(', postfix_text)
        self.assertNotIn('runtime_call="py_ord" if fn_name == "ord" else "py_chr"', postfix_text)

    def test_core_source_routes_iterator_builtin_metadata_through_shared_helper(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = text.split("def _sh_annotate_iterator_builtin_call_expr", 1)[1].split(
            "def _sh_annotate_open_call_expr",
            1,
        )[0]
        named_call_text = annotation_text.split("def _annotate_named_call_expr", 1)[1].split(
            "def _annotate_builtin_named_call_expr",
            1,
        )[0]
        postfix_text = text.split("def _parse_postfix", 1)[1].split("def _parse_primary", 1)[0]

        self.assertIn('runtime_call = "py_iter_or_raise"', helper_text)
        self.assertIn('if fn_name == "next":', helper_text)
        self.assertIn('runtime_call = "py_next_or_stop"', helper_text)
        self.assertIn('elif fn_name == "reversed":', helper_text)
        self.assertIn('runtime_call = "py_reversed"', helper_text)
        self.assertIn('module_id = "pytra.core.py_runtime"', helper_text)
        self.assertIn('module_id = "pytra.built_in.iter_ops"', helper_text)
        self.assertIn('_sh_annotate_runtime_call_expr(', helper_text)
        self.assertIn("return self._apply_named_call_dispatch(", named_call_text)
        self.assertNotIn('elif fn_name == "iter":\n                    _sh_annotate_runtime_call_expr(', postfix_text)
        self.assertNotIn('elif fn_name == "next":\n                    _sh_annotate_runtime_call_expr(', postfix_text)
        self.assertNotIn('elif fn_name == "reversed":\n                    _sh_annotate_runtime_call_expr(', postfix_text)
        self.assertNotIn('runtime_call="py_iter_or_raise"', postfix_text)
        self.assertNotIn('runtime_call="py_next_or_stop"', postfix_text)
        self.assertNotIn('runtime_call="py_reversed"', postfix_text)

    def test_core_source_routes_open_metadata_through_shared_helper(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = text.split("def _sh_annotate_open_call_expr", 1)[1].split(
            "def _sh_annotate_exception_ctor_call_expr",
            1,
        )[0]
        named_call_text = annotation_text.split("def _annotate_named_call_expr", 1)[1].split(
            "def _annotate_builtin_named_call_expr",
            1,
        )[0]
        postfix_text = text.split("def _parse_postfix", 1)[1].split("def _parse_primary", 1)[0]

        self.assertIn('_sh_annotate_runtime_call_expr(', helper_text)
        self.assertIn('builtin_name="open"', helper_text)
        self.assertIn('runtime_call="open"', helper_text)
        self.assertIn('module_id="pytra.core.py_runtime"', helper_text)
        self.assertIn('runtime_symbol="open"', helper_text)
        self.assertIn("return self._apply_named_call_dispatch(", named_call_text)
        self.assertNotIn('elif fn_name == "open":\n                    _sh_annotate_runtime_call_expr(', postfix_text)
        self.assertNotIn('runtime_call="open"', postfix_text)

    def test_core_source_routes_exception_ctor_metadata_through_shared_helper(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = text.split("def _sh_annotate_exception_ctor_call_expr", 1)[1].split(
            "def _sh_annotate_type_predicate_call_expr",
            1,
        )[0]
        named_call_text = annotation_text.split("def _annotate_named_call_expr", 1)[1].split(
            "def _annotate_builtin_named_call_expr",
            1,
        )[0]
        postfix_text = text.split("def _parse_postfix", 1)[1].split("def _parse_primary", 1)[0]

        self.assertIn('_sh_annotate_runtime_call_expr(', helper_text)
        self.assertIn('builtin_name=fn_name', helper_text)
        self.assertIn('runtime_call="std::runtime_error"', helper_text)
        self.assertIn('module_id="pytra.core.py_runtime"', helper_text)
        self.assertIn('runtime_symbol=fn_name', helper_text)
        self.assertIn("return self._apply_named_call_dispatch(", named_call_text)
        self.assertNotIn('elif fn_name in {"Exception", "RuntimeError"}:\n                    _sh_annotate_runtime_call_expr(', postfix_text)
        self.assertNotIn('runtime_call="std::runtime_error"', postfix_text)

    def test_core_source_routes_type_predicate_metadata_through_shared_helper(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = text.split("def _sh_annotate_type_predicate_call_expr", 1)[1].split(
            "def _sh_annotate_fixed_runtime_builtin_call_expr",
            1,
        )[0]
        named_call_text = annotation_text.split("def _annotate_named_call_expr", 1)[1].split(
            "def _subscript_result_type",
            1,
        )[0]
        postfix_text = text.split("def _parse_postfix", 1)[1].split("def _parse_primary", 1)[0]

        self.assertIn('_sh_annotate_runtime_call_expr(', helper_text)
        self.assertIn('lowered_kind="TypePredicateCall"', helper_text)
        self.assertIn('builtin_name=fn_name', helper_text)
        self.assertIn("return self._apply_named_call_dispatch(", named_call_text)
        self.assertNotIn('elif fn_name == "isinstance":\n                    _sh_annotate_runtime_call_expr(', postfix_text)
        self.assertNotIn('elif fn_name == "issubclass":\n                    _sh_annotate_runtime_call_expr(', postfix_text)
        self.assertNotIn('lowered_kind="TypePredicateCall"', postfix_text)

    def test_core_source_routes_fixed_runtime_builtin_metadata_through_shared_helper(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = text.split("def _sh_annotate_fixed_runtime_builtin_call_expr", 1)[1].split(
            "def _sh_lookup_named_call_dispatch",
            1,
        )[0]
        named_call_text = annotation_text.split("def _annotate_named_call_expr", 1)[1].split(
            "def _subscript_result_type",
            1,
        )[0]
        postfix_text = text.split("def _parse_postfix", 1)[1].split("def _parse_primary", 1)[0]

        self.assertIn('runtime_call = "py_to_string"', helper_text)
        self.assertIn('if fn_name == "print":', helper_text)
        self.assertIn('runtime_call = "py_print"', helper_text)
        self.assertIn('module_id = "pytra.built_in.io_ops"', helper_text)
        self.assertIn('runtime_symbol = "py_print"', helper_text)
        self.assertIn('elif fn_name == "len":', helper_text)
        self.assertIn('runtime_call = "py_len"', helper_text)
        self.assertIn('elif fn_name == "range":', helper_text)
        self.assertIn('runtime_call = "py_range"', helper_text)
        self.assertIn('elif fn_name == "zip":', helper_text)
        self.assertIn('runtime_call = "zip"', helper_text)
        self.assertIn('_sh_annotate_runtime_call_expr(', helper_text)
        self.assertIn("return self._apply_named_call_dispatch(", named_call_text)
        self.assertNotIn('if fn_name == "print":\n                    _sh_annotate_runtime_call_expr(', postfix_text)
        self.assertNotIn('elif fn_name == "len":\n                    _sh_annotate_runtime_call_expr(', postfix_text)
        self.assertNotIn('elif fn_name == "range":\n                    _sh_annotate_runtime_call_expr(', postfix_text)
        self.assertNotIn('elif fn_name == "zip":\n                    _sh_annotate_runtime_call_expr(', postfix_text)
        self.assertNotIn('elif fn_name == "str":\n                    _sh_annotate_runtime_call_expr(', postfix_text)
        self.assertNotIn('runtime_call = "py_to_string"', postfix_text)
        self.assertNotIn('runtime_call = "py_print"', postfix_text)

    def test_core_source_routes_named_call_lookup_through_shared_helper(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = text.split("def _sh_lookup_named_call_dispatch", 1)[1].split(
            "def _sh_infer_known_name_call_return_type",
            1,
        )[0]
        call_helper_text = annotation_text.split("def _annotate_call_expr", 1)[1].split(
            "def _resolve_named_call_dispatch",
            1,
        )[0]
        postfix_text = text.split("def _parse_postfix", 1)[1].split("def _parse_primary", 1)[0]

        self.assertIn('return {\n            "builtin_semantic_tag": "",', helper_text)
        self.assertIn('lookup_builtin_semantic_tag(fn_name)', helper_text)
        self.assertIn('lookup_stdlib_function_runtime_call(fn_name)', helper_text)
        self.assertIn('lookup_stdlib_function_semantic_tag(fn_name)', helper_text)
        self.assertIn('lookup_stdlib_imported_symbol_runtime_call(fn_name, _SH_IMPORT_SYMBOLS)', helper_text)
        self.assertIn('lookup_stdlib_symbol_semantic_tag(fn_name)', helper_text)
        self.assertIn('lookup_noncpp_imported_symbol_runtime_call(fn_name, _SH_IMPORT_SYMBOLS)', helper_text)
        self.assertNotIn('_sh_lookup_named_call_dispatch(fn_name)', call_helper_text)
        self.assertNotIn('lookup_stdlib_function_runtime_call(fn_name) if fn_name != "" else ""', postfix_text)
        self.assertNotIn('lookup_builtin_semantic_tag(fn_name) if fn_name != "" else ""', postfix_text)
        self.assertNotIn('_sh_lookup_named_call_dispatch(fn_name)', postfix_text)
        self.assertNotIn(
            'lookup_stdlib_imported_symbol_runtime_call(fn_name, _SH_IMPORT_SYMBOLS)',
            postfix_text,
        )
        self.assertNotIn(
            'lookup_noncpp_imported_symbol_runtime_call(fn_name, _SH_IMPORT_SYMBOLS)',
            postfix_text,
        )

    def test_core_source_routes_named_call_annotations_through_parser_helper(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("class _ShExprCallAnnotationMixin:", annotation_text)
        self.assertIn("def _apply_named_callee_call_annotation(", annotation_text)
        self.assertIn("def _apply_callee_call_annotation(", annotation_text)
        self.assertIn("def _resolve_callee_call_annotation_kind(", annotation_text)
        self.assertIn("def _resolve_callee_call_annotation_state(", annotation_text)
        self.assertIn("def _annotate_callee_call_expr(", annotation_text)
        self.assertIn("def _resolve_call_expr_annotation_state(", annotation_text)
        self.assertIn("def _annotate_call_expr(", annotation_text)
        self.assertIn("return self._annotate_named_call_expr(", annotation_text)
        self.assertIn("return self._apply_named_callee_call_annotation(", annotation_text)
        self.assertIn("return self._apply_attr_callee_call_annotation(", annotation_text)
        self.assertIn("return self._apply_call_expr_annotation(", annotation_text)
        self.assertIn("from toolchain.ir.core_expr_call_annotation import _ShExprCallAnnotationMixin", core_text)
        self.assertIn("_ShExprCallAnnotationMixin", core_text)
        self.assertIn("def _resolve_named_call_dispatch(", core_text)
        self.assertIn("def _annotate_named_call_expr(", annotation_text)
        self.assertIn("def _annotate_builtin_named_call_expr(", annotation_text)
        self.assertIn("def _annotate_runtime_named_call_expr(", annotation_text)
        self.assertNotIn("def _apply_named_callee_call_annotation(", core_text)
        self.assertNotIn("def _apply_callee_call_annotation(", core_text)
        self.assertNotIn("def _resolve_callee_call_annotation_kind(", core_text)
        self.assertNotIn("def _resolve_call_expr_annotation_state(", core_text)
        self.assertNotIn("def _annotate_call_expr(", core_text)

    def test_self_hosted_parser_rejects_object_receiver_method_call(self) -> None:
        src = """
x: object = 1
x.bit_length()
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("object receiver attribute/method access is forbidden", str(cm.exception))
        self.assertNotIn('if fn_name in {"print", "len", "range", "zip", "str"}:', postfix_text)
        self.assertNotIn('if fn_name == "bool" and len(args) == 1:', postfix_text)
        self.assertNotIn("payload = self._annotate_named_call_expr(", postfix_text)
        self.assertNotIn("elem_t = _sh_infer_enumerate_item_type(args)", postfix_text)

    def test_core_source_routes_builtin_named_call_annotations_through_parser_helper(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        named_call_text = annotation_text.split("def _annotate_named_call_expr", 1)[1].split(
            "def _should_use_truthy_runtime_for_bool_ctor",
            1,
        )[0]
        named_apply_text = text.split("def _apply_named_call_dispatch", 1)[1].split(
            "def _coalesce_optional_annotation_payload",
            1,
        )[0]
        truthy_helper_text = text.split("def _should_use_truthy_runtime_for_bool_ctor", 1)[1].split(
            "def _resolve_builtin_named_call_semantic_tag",
            1,
        )[0]
        resolve_text = text.split("def _resolve_builtin_named_call_semantic_tag", 1)[1].split(
            "def _resolve_builtin_named_call_kind",
            1,
        )[0]
        kind_text = text.split("def _resolve_builtin_named_call_kind", 1)[1].split(
            "def _resolve_builtin_named_call_dispatch",
            1,
        )[0]
        dispatch_text = text.split("def _resolve_builtin_named_call_dispatch", 1)[1].split(
            "def _resolve_builtin_named_call_annotation_state",
            1,
        )[0]
        state_text = text.split("def _resolve_builtin_named_call_annotation_state", 1)[1].split(
            "def _resolve_builtin_named_call_truthy_state",
            1,
        )[0]
        truthy_state_text = text.split("def _resolve_builtin_named_call_truthy_state", 1)[1].split(
            "def _resolve_builtin_named_call_iter_element_type",
            1,
        )[0]
        iter_state_text = text.split("def _resolve_builtin_named_call_iter_element_type", 1)[1].split(
            "def _apply_fixed_runtime_builtin_named_call_annotation",
            1,
        )[0]
        fixed_apply_text = text.split("def _apply_fixed_runtime_builtin_named_call_annotation", 1)[1].split(
            "def _apply_scalar_ctor_builtin_named_call_annotation",
            1,
        )[0]
        scalar_apply_text = text.split("def _apply_scalar_ctor_builtin_named_call_annotation", 1)[1].split(
            "def _apply_minmax_builtin_named_call_annotation",
            1,
        )[0]
        enumerate_apply_text = text.split("def _apply_enumerate_builtin_named_call_annotation", 1)[1].split(
            "def _apply_anyall_builtin_named_call_annotation",
            1,
        )[0]
        apply_text = text.split("def _apply_builtin_named_call_dispatch", 1)[1].split(
            "def _annotate_builtin_named_call_expr",
            1,
        )[0]
        helper_text = annotation_text.split("def _annotate_builtin_named_call_expr", 1)[1].split(
            "def _resolve_runtime_named_call_dispatch",
            1,
        )[0]
        postfix_text = text.split("def _parse_postfix", 1)[1].split("def _parse_primary", 1)[0]

        self.assertIn("if len(args) != 1:", truthy_helper_text)
        self.assertIn('arg0_t = str(arg0.get("resolved_type", "unknown"))', truthy_helper_text)
        self.assertIn("return self._is_forbidden_object_receiver_type(arg0_t)", truthy_helper_text)
        self.assertIn('return str(call_dispatch.get("builtin_semantic_tag", ""))', resolve_text)
        self.assertIn('if fn_name in {"print", "len", "range", "zip", "str"}:', kind_text)
        self.assertIn("semantic_tag = self._resolve_builtin_named_call_semantic_tag(", dispatch_text)
        self.assertIn("dispatch_kind = self._resolve_builtin_named_call_kind(", dispatch_text)
        self.assertIn("semantic_tag, dispatch_kind = self._resolve_builtin_named_call_dispatch(", state_text)
        self.assertIn("use_truthy_runtime = self._resolve_builtin_named_call_truthy_state(", state_text)
        self.assertIn("iter_element_type = self._resolve_builtin_named_call_iter_element_type(", state_text)
        self.assertIn('dispatch_kind == "scalar_ctor"', truthy_state_text)
        self.assertIn('fn_name == "bool"', truthy_state_text)
        self.assertIn("self._should_use_truthy_runtime_for_bool_ctor(args=args)", truthy_state_text)
        self.assertIn('if dispatch_kind == "enumerate":', iter_state_text)
        self.assertIn("return _sh_infer_enumerate_item_type(args)", iter_state_text)
        self.assertIn("return _sh_annotate_fixed_runtime_builtin_call_expr(", fixed_apply_text)
        self.assertIn("return _sh_annotate_scalar_ctor_call_expr(", scalar_apply_text)
        self.assertIn("return _sh_annotate_enumerate_call_expr(", enumerate_apply_text)
        self.assertIn('if dispatch_kind == "fixed_runtime":', apply_text)
        self.assertIn("return self._apply_fixed_runtime_builtin_named_call_annotation(", apply_text)
        self.assertIn("return self._apply_scalar_ctor_builtin_named_call_annotation(", apply_text)
        self.assertIn("return self._apply_enumerate_builtin_named_call_annotation(", apply_text)
        self.assertIn("_resolve_builtin_named_call_annotation_state(", helper_text)
        self.assertNotIn('semantic_tag = str(call_dispatch.get("builtin_semantic_tag", ""))', helper_text)
        self.assertNotIn('if fn_name in {"print", "len", "range", "zip", "str"}:', helper_text)
        self.assertNotIn("semantic_tag = self._resolve_builtin_named_call_semantic_tag(", helper_text)
        self.assertNotIn("dispatch_kind = self._resolve_builtin_named_call_kind(", helper_text)
        self.assertNotIn("semantic_tag, dispatch_kind = self._resolve_builtin_named_call_dispatch(", helper_text)
        self.assertIn("return self._apply_builtin_named_call_dispatch(", helper_text)
        self.assertIn("use_truthy_runtime=use_truthy_runtime", apply_text)
        self.assertIn("iter_element_type=iter_element_type", apply_text)
        self.assertNotIn('fn_name == "bool" and self._should_use_truthy_runtime_for_bool_ctor(', apply_text)
        self.assertNotIn("_sh_infer_enumerate_item_type(args)", apply_text)
        self.assertNotIn("return _sh_annotate_fixed_runtime_builtin_call_expr(", apply_text)
        self.assertNotIn("return _sh_annotate_scalar_ctor_call_expr(", apply_text)
        self.assertNotIn("return _sh_annotate_enumerate_call_expr(", apply_text)
        self.assertNotIn('dispatch_kind == "scalar_ctor"', state_text)
        self.assertNotIn('dispatch_kind == "enumerate"', state_text)
        self.assertIn("return None", apply_text)
        self.assertIn("return self._apply_named_call_dispatch(", named_call_text)
        self.assertIn('if dispatch_kind == "builtin":', named_apply_text)
        self.assertNotIn('if fn_name in {"print", "len", "range", "zip", "str"}:', postfix_text)
        self.assertNotIn('if fn_name == "bool" and len(args) == 1:', postfix_text)
        self.assertNotIn("elem_t = _sh_infer_enumerate_item_type(args)", postfix_text)

    def test_core_source_routes_runtime_named_call_annotations_through_parser_helper(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        named_call_text = annotation_text.split("def _annotate_named_call_expr", 1)[1].split(
            "def _should_use_truthy_runtime_for_bool_ctor",
            1,
        )[0]
        named_apply_text = text.split("def _apply_named_call_dispatch", 1)[1].split(
            "def _coalesce_optional_annotation_payload",
            1,
        )[0]
        resolve_text = annotation_text.split("def _resolve_runtime_named_call_dispatch", 1)[1].split(
            "def _resolve_runtime_named_call_kind",
            1,
        )[0]
        kind_text = annotation_text.split("def _resolve_runtime_named_call_kind", 1)[1].split(
            "def _resolve_runtime_named_call_annotation",
            1,
        )[0]
        resolve_apply_text = annotation_text.split("def _resolve_runtime_named_call_apply_state", 1)[1].split(
            "def _apply_stdlib_function_named_call_annotation",
            1,
        )[0]
        stdlib_fn_apply_text = text.split("def _apply_stdlib_function_named_call_annotation", 1)[1].split(
            "def _apply_stdlib_symbol_named_call_annotation",
            1,
        )[0]
        stdlib_symbol_apply_text = text.split("def _apply_stdlib_symbol_named_call_annotation", 1)[1].split(
            "def _apply_noncpp_symbol_named_call_annotation",
            1,
        )[0]
        noncpp_symbol_apply_text = text.split("def _apply_noncpp_symbol_named_call_annotation", 1)[1].split(
            "def _apply_runtime_named_call_dispatch",
            1,
        )[0]
        apply_text = text.split("def _apply_runtime_named_call_dispatch", 1)[1].split(
            "def _annotate_runtime_named_call_expr",
            1,
        )[0]
        helper_text = annotation_text.split("def _annotate_runtime_named_call_expr", 1)[1].split(
            "def _owner_expr_resolved_type",
            1,
        )[0]
        postfix_text = text.split("def _parse_postfix", 1)[1].split("def _parse_primary", 1)[0]

        self.assertIn('stdlib_fn_runtime_call = str(call_dispatch.get("stdlib_fn_runtime_call", ""))', resolve_text)
        self.assertIn('stdlib_symbol_runtime_call = str(call_dispatch.get("stdlib_symbol_runtime_call", ""))', resolve_text)
        self.assertIn('noncpp_symbol_runtime_call = str(call_dispatch.get("noncpp_symbol_runtime_call", ""))', resolve_text)
        self.assertIn("return (", resolve_text)
        self.assertIn('if stdlib_fn_runtime_call != "":', kind_text)
        self.assertIn(") = self._resolve_runtime_named_call_annotation(", resolve_apply_text)
        self.assertIn('if dispatch_kind == "stdlib_function":', resolve_apply_text)
        self.assertIn('if dispatch_kind == "stdlib_symbol":', resolve_apply_text)
        self.assertIn('if dispatch_kind == "noncpp_symbol":', resolve_apply_text)
        self.assertIn("return _sh_annotate_stdlib_function_call_expr(", stdlib_fn_apply_text)
        self.assertIn("return _sh_annotate_stdlib_symbol_call_expr(", stdlib_symbol_apply_text)
        self.assertIn("return _sh_annotate_noncpp_symbol_call_expr(", noncpp_symbol_apply_text)
        self.assertIn('if dispatch_kind == "stdlib_function":', apply_text)
        self.assertIn('if dispatch_kind == "stdlib_symbol":', apply_text)
        self.assertIn('if dispatch_kind == "noncpp_symbol":', apply_text)
        self.assertIn("return self._apply_stdlib_function_named_call_annotation(", apply_text)
        self.assertIn("return self._apply_stdlib_symbol_named_call_annotation(", apply_text)
        self.assertIn("return self._apply_noncpp_symbol_named_call_annotation(", apply_text)
        self.assertIn("dispatch_kind, runtime_call, semantic_tag = self._resolve_runtime_named_call_apply_state(", helper_text)
        self.assertIn("return self._apply_runtime_named_call_dispatch(", helper_text)
        self.assertNotIn('stdlib_fn_runtime_call = str(call_dispatch.get("stdlib_fn_runtime_call", ""))', helper_text)
        self.assertNotIn('stdlib_symbol_runtime_call = str(call_dispatch.get("stdlib_symbol_runtime_call", ""))', helper_text)
        self.assertNotIn('noncpp_symbol_runtime_call = str(call_dispatch.get("noncpp_symbol_runtime_call", ""))', helper_text)
        self.assertNotIn('if stdlib_fn_runtime_call != "":', helper_text)
        self.assertNotIn("dispatch_kind = self._resolve_runtime_named_call_kind(", helper_text)
        self.assertNotIn(") = self._resolve_runtime_named_call_annotation(", helper_text)
        self.assertNotIn("return _sh_annotate_stdlib_function_call_expr(", apply_text)
        self.assertNotIn("return _sh_annotate_stdlib_symbol_call_expr(", apply_text)
        self.assertNotIn("return _sh_annotate_noncpp_symbol_call_expr(", apply_text)
        self.assertIn("return None", apply_text)
        self.assertIn("return self._apply_named_call_dispatch(", named_call_text)
        self.assertIn('if dispatch_kind == "runtime":', named_apply_text)
        self.assertNotIn('_sh_lookup_named_call_dispatch(fn_name)', postfix_text)
        self.assertNotIn('if dispatch_kind == "stdlib_function":', postfix_text)
        self.assertNotIn('if dispatch_kind == "stdlib_symbol":', postfix_text)
        self.assertNotIn('if dispatch_kind == "noncpp_symbol":', postfix_text)

    def test_core_source_routes_known_name_call_returns_through_shared_helper(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = text.split("def _sh_infer_known_name_call_return_type", 1)[1].split(
            "def _sh_infer_enumerate_item_type",
            1,
        )[0]
        postfix_text = text.split("def _parse_postfix", 1)[1].split("def _parse_primary", 1)[0]

        self.assertIn('if fn_name == "print":', helper_text)
        self.assertIn('if stdlib_imported_ret != "":', helper_text)
        self.assertIn('if fn_name == "open":', helper_text)
        self.assertIn('if fn_name == "zip":', helper_text)
        self.assertIn("zip_item_types.append(_sh_infer_item_type(arg_node))", helper_text)
        self.assertIn('return "dict[unknown,unknown]"', helper_text)
        self.assertNotIn("_sh_infer_known_name_call_return_type(", postfix_text)
        self.assertNotIn('if fn_name == "print":\n                        call_ret = "None"', postfix_text)
        self.assertNotIn('elif fn_name == "open":\n                        call_ret = "PyFile"', postfix_text)
        self.assertNotIn('elif fn_name == "zip":', postfix_text)
        self.assertNotIn('call_ret = "dict[unknown,unknown]"', postfix_text)

    def test_core_source_routes_enumerate_item_type_through_shared_helper(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        self.assertEqual(text.count("def _sh_infer_enumerate_item_type"), 1)
        helper_text = text.split("def _sh_infer_enumerate_item_type", 1)[1].split(
            "def _sh_set_parse_context",
            1,
        )[0]
        state_text = text.split("def _resolve_builtin_named_call_annotation_state", 1)[1].split(
            "def _apply_builtin_named_call_dispatch",
            1,
        )[0]
        postfix_text = text.split("def _parse_postfix", 1)[1].split("def _parse_primary", 1)[0]

        self.assertIn("if len(args) < 1:", helper_text)
        self.assertIn("arg0 = args[0]", helper_text)
        self.assertIn("return _sh_infer_item_type(arg0)", helper_text)
        self.assertIn("_sh_infer_enumerate_item_type(args)", state_text)
        self.assertNotIn('if len(args) >= 1 and isinstance(args[0], dict):', postfix_text)
        self.assertNotIn('elem_t = self._iter_item_type(args[0])', postfix_text)

    def test_core_source_routes_attr_call_returns_through_shared_helper(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = annotation_text.split("def _infer_attr_call_return_type", 1)[1].split(
            "def _infer_call_expr_return_type",
            1,
        )[0]
        postfix_text = text.split("def _parse_postfix", 1)[1].split("def _parse_primary", 1)[0]

        self.assertIn("owner_t = self._owner_expr_resolved_type(owner)", helper_text)
        self.assertIn('if owner_t == "PyFile" and attr in {"close", "write"}:', helper_text)
        self.assertIn('call_ret = self._lookup_method_return(owner_t, attr)', helper_text)
        self.assertIn('stdlib_method_ret = lookup_stdlib_method_return_type(owner_t, attr)', helper_text)
        self.assertNotIn('owner_t = str(owner.get("resolved_type", "unknown"))', helper_text)
        self.assertNotIn('owner_t = self.name_types.get(str(owner.get("id", "")), owner_t)', helper_text)
        self.assertNotIn('call_ret = self._lookup_method_return(owner_t, attr)', postfix_text)
        self.assertNotIn('call_ret = self._lookup_builtin_method_return(owner_t, attr)', postfix_text)
        self.assertNotIn('stdlib_method_ret = lookup_stdlib_method_return_type(owner_t, attr)', postfix_text)
        self.assertNotIn('if owner_t == "PyFile":', postfix_text)

    def test_core_source_routes_call_expr_returns_through_shared_helper(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        named_decl_text = text.split("def _resolve_named_call_declared_return_type", 1)[1].split(
            "def _resolve_named_call_return_state",
            1,
        )[0]
        named_state_text = text.split("def _resolve_named_call_return_state", 1)[1].split(
            "def _infer_named_call_return_type",
            1,
        )[0]
        named_helper_text = text.split("def _infer_named_call_return_type", 1)[1].split(
            "def _infer_call_expr_return_type",
            1,
        )[0]
        helper_text = annotation_text.split("def _infer_call_expr_return_type", 1)[1].split(
            "def _apply_named_callee_call_annotation",
            1,
        )[0]
        build_text = text.split("def _build_call_expr_payload", 1)[1].split(
            "def _apply_named_call_dispatch",
            1,
        )[0]
        state_text = annotation_text.split("def _resolve_call_expr_annotation_state", 1)[1].split(
            "def _apply_call_expr_annotation",
            1,
        )[0]
        apply_text = annotation_text.split("def _apply_call_expr_annotation", 1)[1].split(
            "def _annotate_call_expr",
            1,
        )[0]
        call_helper_text = annotation_text.split("def _annotate_call_expr", 1)[1].split(
            "def _apply_named_call_dispatch",
            1,
        )[0]
        postfix_text = text.split("def _parse_postfix", 1)[1].split("def _parse_primary", 1)[0]

        self.assertIn('kind = str(callee.get("kind", ""))', helper_text)
        self.assertIn("_sh_infer_known_name_call_return_type(", named_state_text)
        self.assertIn("lookup_stdlib_imported_symbol_return_type(fn_name, _SH_IMPORT_SYMBOLS)", named_state_text)
        self.assertIn("if fn_name in self.fn_return_types:", named_decl_text)
        self.assertIn("if fn_name in self.class_method_return_types:", named_decl_text)
        self.assertIn('return self._callable_return_type(str(self.name_types.get(fn_name, "unknown")))', named_decl_text)
        self.assertIn("call_ret, declared_ret = self._resolve_named_call_return_state(", named_helper_text)
        self.assertIn('if call_ret != "":', named_helper_text)
        self.assertIn("self._infer_attr_call_return_type(", helper_text)
        self.assertIn('if kind == "Lambda":', helper_text)
        self.assertIn("return self._infer_named_call_return_type(fn_name=fn_name, args=args), fn_name", helper_text)
        self.assertIn("call_ret, fn_name = self._infer_call_expr_return_type(callee, args)", state_text)
        self.assertIn("self._guard_named_call_args(", state_text)
        self.assertIn("return _sh_make_call_expr(", build_text)
        self.assertIn("payload = self._build_call_expr_payload(", apply_text)
        self.assertIn("return self._annotate_callee_call_expr(", apply_text)
        self.assertIn("call_ret, fn_name = self._resolve_call_expr_annotation_state(", call_helper_text)
        self.assertIn("return self._apply_call_expr_annotation(", call_helper_text)
        self.assertIn("from toolchain.ir.core_expr_call_annotation import _ShExprCallAnnotationMixin", text)
        self.assertNotIn("def _resolve_call_expr_annotation_state(", text)
        self.assertNotIn("def _apply_call_expr_annotation(", text)
        self.assertNotIn("def _annotate_call_expr(", text)
        self.assertNotIn("_sh_infer_known_name_call_return_type(", helper_text)
        self.assertNotIn("stdlib_imported_ret = (", postfix_text)
        self.assertNotIn("call_ret = self.fn_return_types[fn_name]", postfix_text)
        self.assertNotIn('call_ret = self._callable_return_type(str(self.name_types.get(fn_name, "unknown")))', postfix_text)
        self.assertNotIn("lookup_stdlib_imported_symbol_return_type(fn_name, _SH_IMPORT_SYMBOLS)", named_helper_text)
        self.assertNotIn("if fn_name in self.fn_return_types:", named_helper_text)
        self.assertNotIn("call_ret = self._infer_attr_call_return_type(", postfix_text)
        self.assertNotIn('call_ret = str(node.get("return_type", "unknown"))', postfix_text)
        self.assertNotIn("call_ret, fn_name = self._infer_call_expr_return_type(", postfix_text)
        self.assertNotIn("payload = self._build_call_expr_payload(", call_helper_text)
        self.assertNotIn("payload = _sh_make_call_expr(", call_helper_text)
        self.assertNotIn("self._guard_named_call_args(", call_helper_text)

    def test_core_source_routes_call_arg_parsing_through_parser_helper(self) -> None:
        text = CORE_CALL_ARG_SOURCE_PATH.read_text(encoding="utf-8")
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        postfix_text = core_text.split("def _parse_postfix", 1)[1].split("def _parse_comp_target", 1)[0]

        self.assertIn("class _ShExprCallArgParserMixin:", text)
        self.assertIn("def _parse_call_args(", text)
        self.assertIn("def _consume_call_arg_entries(", text)
        self.assertIn("def _consume_call_arg_entries_loop(", text)
        self.assertIn("def _consume_call_arg_loop_entry(", text)
        self.assertIn("def _resolve_call_args_empty_state(", text)
        self.assertIn("def _apply_call_arg_entries_result_state(", text)
        self.assertIn("def _advance_call_arg_loop(", core_text)
        self.assertIn("if self._resolve_call_args_empty_state():", text)
        self.assertIn("return self._consume_call_arg_entries(", text)
        self.assertIn("arg_entry, keyword_entry = self._resolve_call_arg_loop_entry_state()", text)
        self.assertIn("return self._apply_call_arg_loop_entry_state(", text)
        self.assertIn("from toolchain.ir.core_expr_call_args import _ShExprCallArgParserMixin", core_text)
        self.assertIn("from toolchain.ir.core_expr_call_suffix import _ShExprCallSuffixParserMixin", core_text)
        self.assertIn(
            "from toolchain.ir.core_expr_attr_subscript_suffix import _ShExprAttrSubscriptSuffixParserMixin",
            core_text,
        )
        self.assertIn(
            "class _ShExprParser(",
            core_text,
        )
        self.assertIn("next_node = self._parse_postfix_suffix(owner_expr=node)", postfix_text)
        self.assertNotIn("def _parse_call_args(", core_text)
        self.assertNotIn("def _consume_call_arg_entries(", core_text)
        self.assertNotIn("def _consume_call_arg_entries_loop(", core_text)
        self.assertNotIn("def _consume_call_arg_loop_entry(", core_text)

    def test_core_source_routes_call_suffix_through_parser_helper(self) -> None:
        text = CORE_CALL_SUFFIX_SOURCE_PATH.read_text(encoding="utf-8")
        suffix_text = CORE_ATTR_SUBSCRIPT_SUFFIX_SOURCE_PATH.read_text(encoding="utf-8")
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        postfix_suffix_apply_text = suffix_text.split("def _apply_postfix_suffix_kind", 1)[1].split(
            "def _parse_postfix_suffix",
            1,
        )[0]
        postfix_text = core_text.split("def _parse_postfix", 1)[1].split("def _parse_comp_target", 1)[0]

        self.assertIn("def _resolve_call_suffix_state(", text)
        self.assertIn("def _resolve_call_suffix_token_state(", text)
        self.assertIn("def _consume_call_suffix_tokens(", text)
        self.assertIn("def _consume_call_suffix_open_token(", text)
        self.assertIn("def _consume_call_suffix_close_token(", text)
        self.assertIn("def _parse_call_suffix(", text)
        self.assertIn("args, keywords, rtok = self._resolve_call_suffix_token_state()", text)
        self.assertIn("return self._apply_call_suffix_token_state(", text)
        self.assertIn("self._consume_call_suffix_open_token()", text)
        self.assertIn("return self._apply_call_suffix_open_token_state()", text)
        self.assertIn("return self._annotate_call_expr(", text)
        self.assertIn("from toolchain.ir.core_expr_call_suffix import _ShExprCallSuffixParserMixin", core_text)
        self.assertIn(
            "from toolchain.ir.core_expr_attr_subscript_suffix import _ShExprAttrSubscriptSuffixParserMixin",
            core_text,
        )
        self.assertIn(
            "class _ShExprParser(",
            core_text,
        )
        self.assertIn('if tok_kind == "(":', postfix_suffix_apply_text)
        self.assertIn("return self._parse_call_suffix(callee=owner_expr)", postfix_suffix_apply_text)
        self.assertIn("next_node = self._parse_postfix_suffix(owner_expr=node)", postfix_text)
        self.assertNotIn("def _resolve_call_suffix_state(", core_text)
        self.assertNotIn("def _consume_call_suffix_tokens(", core_text)
        self.assertNotIn("def _parse_call_suffix(", core_text)

    def test_core_source_routes_postfix_suffix_dispatch_through_parser_helper(self) -> None:
        text = CORE_ATTR_SUBSCRIPT_SUFFIX_SOURCE_PATH.read_text(encoding="utf-8")
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = text.split("def _apply_postfix_suffix_kind", 1)[1].split(
            "def _parse_postfix_suffix",
            1,
        )[0]
        postfix_text = core_text.split("def _parse_postfix", 1)[1].split("def _parse_comp_target", 1)[0]

        self.assertIn('if tok_kind == ".":', helper_text)
        self.assertIn('if tok_kind == "(":', helper_text)
        self.assertIn('if tok_kind == "[":', helper_text)
        self.assertIn("return None", helper_text)
        self.assertIn('tok_kind = str(self._cur()["k"])', text.split("def _parse_postfix_suffix", 1)[1].split("def _apply_postfix_suffix_kind", 1)[0])
        self.assertIn("return self._apply_postfix_suffix_kind(", text.split("def _parse_postfix_suffix", 1)[1].split("def _apply_postfix_suffix_kind", 1)[0])
        self.assertIn("next_node = self._parse_postfix_suffix(owner_expr=node)", postfix_text)
        self.assertIn("if next_node is None:", postfix_text)
        self.assertNotIn('tok = self._cur()', postfix_text)
        self.assertNotIn('if tok["k"] == "."', postfix_text)
        self.assertNotIn('if tok["k"] == "("', postfix_text)
        self.assertNotIn('if tok["k"] == "["', postfix_text)

    def test_core_source_uses_builder_helpers_for_tuple_destructuring_clusters(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        stmt_text = text.split("def _sh_parse_stmt_block_mutable", 1)[1].split(
            "def _sh_build_module_root",
            1,
        )[0]

        self.assertIn("def _sh_make_tuple_destructure_assign_stmt(", text)
        self.assertIn("_sh_make_tuple_destructure_assign_stmt(", stmt_text)
        self.assertIn('resolved_type=name_types.get(n1, "unknown")', stmt_text)
        self.assertIn('resolved_type=name_types.get(n2, "unknown")', stmt_text)
        self.assertNotIn("target_expr = _sh_make_tuple_expr(", stmt_text)
        self.assertNotIn('target_expr = {"kind": "Tuple"', stmt_text)
        self.assertNotIn('pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, dict<str, object>{{"kind", make_object("Assign")}', stmt_text)

    def test_core_source_known_inline_kind_residual_set_is_helper_only(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        raw_kinds = re.findall(r'\{"kind": "([^"]+)"', text)
        inline_kinds = {kind for kind in raw_kinds if kind != "" and kind[0].isupper()}
        trivia_kinds = {kind for kind in raw_kinds if kind != "" and kind[0].islower()}
        multiline_kind_literals = set(
            re.findall(r'(?:return|node:\s*dict\[str, Any\]\s*=)\s*\{\s*"kind":\s*"([^"]+)"', text, re.S)
        )

        self.assertIn('node = _sh_make_stmt_node("Expr", source_span)', text)
        self.assertIn('return _sh_make_node("Slice", lower=lower, upper=upper, step=step)', text)
        self.assertIn('return _sh_make_node("blank", count=count)', text)
        self.assertIn('return _sh_make_node("comment", text=text)', text)
        self.assertNotIn('return {"kind": "Expr", "source_span": source_span, "value": value}', text)
        self.assertNotIn('return {"kind": "Slice", "lower": lower, "upper": upper, "step": step}', text)
        self.assertNotIn('return {"kind": "blank", "count": count}', text)
        self.assertNotIn('return {"kind": "comment", "text": text}', text)
        self.assertEqual(inline_kinds, set())
        self.assertEqual(trivia_kinds, set())
        self.assertEqual(multiline_kind_literals, set())
        self.assertTrue(
            {
                "If",
                "While",
                "ExceptHandler",
                "Try",
                "For",
                "ForRange",
                "Raise",
                "Pass",
                "Return",
                "AugAssign",
                "Swap",
                "RangeExpr",
                "ListComp",
                "DictComp",
                "SetComp",
                "FormattedValue",
                "JoinedStr",
                "Subscript",
                "BoolOp",
                "UnaryOp",
                "Compare",
                "BinOp",
                "Lambda",
                "Call",
                "Dict",
                "Tuple",
                "Name",
                "Module",
                "Assign",
                "AnnAssign",
                "FormattedValue",
            }.isdisjoint(inline_kinds)
        )

    def test_top_level_extern_decorator_is_preserved(self) -> None:
        src = """
from pytra.std import extern

@extern
def f(x: float) -> float:
    return x
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "f"
        ]
        self.assertEqual(len(funcs), 1)
        self.assertEqual(funcs[0].get("decorators"), ["extern"])

    def test_top_level_annassign_extern_same_name_sets_ambient_global_metadata(self) -> None:
        src = """
from pytra.std import extern

document: Any = extern()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        ann_assigns = [
            n for n in east.get("body", []) if isinstance(n, dict) and n.get("kind") == "AnnAssign"
        ]
        self.assertEqual(len(ann_assigns), 1)
        self.assertEqual(
            ann_assigns[0].get("meta", {}).get("extern_var_v1"),
            {
                "schema_version": 1,
                "symbol": "document",
                "same_name": 1,
            },
        )

    def test_top_level_annassign_extern_alias_sets_ambient_global_metadata(self) -> None:
        src = """
from pytra.std import extern

doc: Any = extern("document")
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        ann_assigns = [
            n for n in east.get("body", []) if isinstance(n, dict) and n.get("kind") == "AnnAssign"
        ]
        self.assertEqual(len(ann_assigns), 1)
        self.assertEqual(
            ann_assigns[0].get("meta", {}).get("extern_var_v1"),
            {
                "schema_version": 1,
                "symbol": "document",
                "same_name": 0,
            },
        )

    def test_top_level_abi_decorator_sets_runtime_abi_metadata(self) -> None:
        src = """
from pytra.std import abi

@abi(args={"parts": "value"}, ret="value")
def py_join(sep: str, parts: list[str]) -> str:
    return sep
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "py_join"
        ]
        self.assertEqual(len(funcs), 1)
        fn = funcs[0]
        self.assertEqual(
            fn.get("decorators"),
            ['abi(args={"parts": "value"}, ret="value")'],
        )
        self.assertEqual(
            fn.get("meta", {}).get("runtime_abi_v1"),
            {
                "schema_version": 1,
                "args": {"parts": "value"},
                "ret": "value",
            },
        )

    def test_legacy_value_readonly_alias_is_normalized_to_value(self) -> None:
        src = """
from pytra.std import abi

@abi(args={"parts": "value_readonly"}, ret="value")
def py_join(sep: str, parts: list[str]) -> str:
    return sep
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "py_join"
        ]
        self.assertEqual(len(funcs), 1)
        fn = funcs[0]
        self.assertEqual(
            fn.get("decorators"),
            ['abi(args={"parts": "value_readonly"}, ret="value")'],
        )
        self.assertEqual(
            fn.get("meta", {}).get("runtime_abi_v1"),
            {
                "schema_version": 1,
                "args": {"parts": "value"},
                "ret": "value",
            },
        )

    def test_top_level_extern_and_abi_decorators_can_coexist(self) -> None:
        src = """
from pytra.std import extern, abi

@extern
@abi(args={"xs": "value"}, ret="value")
def clone(xs: list[int]) -> list[int]:
    return xs
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "clone"
        ]
        self.assertEqual(len(funcs), 1)
        fn = funcs[0]
        self.assertEqual(
            fn.get("decorators"),
            ["extern", 'abi(args={"xs": "value"}, ret="value")'],
        )
        self.assertEqual(
            fn.get("meta", {}).get("runtime_abi_v1"),
            {
                "schema_version": 1,
                "args": {"xs": "value"},
                "ret": "value",
            },
        )

    def test_top_level_abi_decorator_accepts_value_mut_arg(self) -> None:
        src = """
from pytra.std import abi

@abi(args={"xs": "value_mut"})
def sort_inplace(xs: list[int]) -> None:
    return None
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "sort_inplace"
        ]
        self.assertEqual(len(funcs), 1)
        self.assertEqual(
            funcs[0].get("meta", {}).get("runtime_abi_v1"),
            {
                "schema_version": 1,
                "args": {"xs": "value_mut"},
                "ret": "default",
            },
        )

    def test_top_level_template_decorator_sets_template_metadata(self) -> None:
        src = """
from pytra.std.template import template

@template("T", "U")
def py_zip(lhs: list[T], rhs: list[U]) -> list[tuple[T, U]]:
    return []
"""
        east = convert_source_to_east_with_backend(
            src,
            "src/pytra/built_in/template_ops.py",
            parser_backend="self_hosted",
        )
        funcs = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "py_zip"
        ]
        self.assertEqual(len(funcs), 1)
        fn = funcs[0]
        self.assertEqual(fn.get("decorators"), ['template("T", "U")'])
        self.assertEqual(
            fn.get("meta", {}).get("template_v1"),
            {
                "schema_version": 1,
                "params": ["T", "U"],
                "scope": "runtime_helper",
                "instantiation_mode": "linked_implicit",
            },
        )

    def test_top_level_template_and_abi_decorators_can_coexist(self) -> None:
        src = """
from pytra.std import abi
from pytra.std.template import template

@template("T")
@abi(args={"xs": "value"}, ret="value")
def clone(xs: list[T]) -> list[T]:
    return xs
"""
        east = convert_source_to_east_with_backend(
            src,
            "src/pytra/built_in/template_ops.py",
            parser_backend="self_hosted",
        )
        funcs = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "clone"
        ]
        self.assertEqual(len(funcs), 1)
        fn = funcs[0]
        self.assertEqual(
            fn.get("meta", {}),
            {
                "template_v1": {
                    "schema_version": 1,
                    "params": ["T"],
                    "scope": "runtime_helper",
                    "instantiation_mode": "linked_implicit",
                },
                "runtime_abi_v1": {
                    "schema_version": 1,
                    "args": {"xs": "value"},
                    "ret": "value",
                },
            },
        )

    def test_method_level_template_decorator_is_rejected(self) -> None:
        src = """
from pytra.std.template import template

class Box:
    @template("T")
    def f(self, xs: list[int]) -> list[int]:
        return xs
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("@template is not supported on methods", str(cm.exception))

    def test_template_decorator_rejects_duplicate_params(self) -> None:
        src = """
from pytra.std.template import template

@template("T", "T")
def f(xs: list[int]) -> list[int]:
    return xs
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("duplicate template parameter", str(cm.exception))

    def test_template_decorator_rejects_keyword_form(self) -> None:
        src = """
from pytra.std.template import template

@template(name="T")
def f(xs: list[int]) -> list[int]:
    return xs
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("template decorator accepts positional string literal parameters only", str(cm.exception))

    def test_self_hosted_parser_rejects_object_receiver_method_call(self) -> None:
        src = """
def bad_attr(x: object) -> int:
    return x.bit_length()
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("object receiver attribute/method access is forbidden", str(cm.exception))

    def test_template_decorator_is_rejected_outside_runtime_helper_modules(self) -> None:
        src = """
from pytra.std.template import template

@template("T")
def f(xs: list[T]) -> list[T]:
    return xs
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(
                src,
                "sample/py/template_demo.py",
                parser_backend="self_hosted",
            )
        self.assertIn("@template is supported on runtime helper modules only", str(cm.exception))

    def test_method_level_abi_decorator_is_rejected(self) -> None:
        src = """
from pytra.std import abi

class Box:
    @abi(args={"xs": "value"})
    def f(self, xs: list[int]) -> list[int]:
        return xs
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("@abi is not supported on methods", str(cm.exception))

    def test_positional_abi_decorator_is_rejected(self) -> None:
        src = """
from pytra.std import abi

@abi("value")
def f(xs: list[int]) -> list[int]:
    return xs
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("abi decorator accepts keyword arguments only", str(cm.exception))

    def test_value_mut_is_rejected_for_return_mode(self) -> None:
        src = """
from pytra.std import abi

@abi(ret="value_mut")
def f(xs: list[int]) -> list[int]:
    return xs
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("unsupported abi mode for abi ret", str(cm.exception))

    def test_value_abi_rejects_mutating_append(self) -> None:
        src = """
from pytra.std import abi

@abi(args={"parts": "value"})
def py_join(parts: list[str]) -> str:
    parts.append("x")
    return ""
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("value parameter mutated", str(cm.exception))
        self.assertIn("parts", str(cm.exception))

    def test_sum_on_json_object_is_rejected_by_decode_first_guard(self) -> None:
        src = """
from pytra.std import json

def f(text: str) -> int:
    value = json.loads(text)
    return sum(value)
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("sum() does not accept object/Any values", str(cm.exception))

    def test_zip_on_json_values_is_rejected_by_decode_first_guard(self) -> None:
        src = """
from pytra.std import json

def f(lhs_text: str, rhs_text: str) -> None:
    lhs = json.loads(lhs_text)
    rhs = json.loads(rhs_text)
    _ = zip(lhs, rhs)
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("zip() does not accept object/Any values", str(cm.exception))

    def test_dict_keys_on_json_object_is_rejected_by_decode_first_guard(self) -> None:
        src = """
from pytra.std import json

def f(text: str) -> None:
    value = json.loads(text)
    _ = value.keys()
"""
        with self.assertRaises(RuntimeError) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("keys() does not accept object/Any receivers", str(cm.exception))

    def test_quoted_type_annotation_is_normalized(self) -> None:
        src = """
def f(p: "Path", xs: "list[int]") -> "Path":
    return p
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "f"]
        self.assertEqual(len(funcs), 1)
        fn = funcs[0]
        arg_types = fn.get("arg_types", {})
        self.assertEqual(arg_types.get("p"), "Path")
        self.assertEqual(arg_types.get("xs"), "list[int64]")
        self.assertEqual(fn.get("return_type"), "Path")
        arg_type_exprs = fn.get("arg_type_exprs", {})
        self.assertEqual(arg_type_exprs.get("p"), {"kind": "NamedType", "name": "Path"})
        self.assertEqual(
            arg_type_exprs.get("xs"),
            {
                "kind": "GenericType",
                "base": "list",
                "args": [{"kind": "NamedType", "name": "int64"}],
            },
        )
        self.assertEqual(fn.get("return_type_expr"), {"kind": "NamedType", "name": "Path"})

    def test_type_expr_is_emitted_for_union_optional_and_nested_generic_annotations(self) -> None:
        src = """
from pytra.std.json import JsonValue

def f(x: int | bool, ys: list[int | bool], payload: JsonValue | None) -> dict[str, int | bool]:
    local: list[int | bool] = []
    return {"a": 1}
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        fn = next(
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "f"
        )
        self.assertEqual(fn.get("arg_types", {}).get("x"), "int64|bool")
        self.assertEqual(fn.get("arg_types", {}).get("ys"), "list[int64|bool]")
        self.assertEqual(fn.get("arg_types", {}).get("payload"), "JsonValue | None")
        self.assertEqual(fn.get("return_type"), "dict[str,int64|bool]")

        arg_type_exprs = fn.get("arg_type_exprs", {})
        self.assertEqual(
            arg_type_exprs.get("x"),
            {
                "kind": "UnionType",
                "union_mode": "general",
                "options": [
                    {"kind": "NamedType", "name": "int64"},
                    {"kind": "NamedType", "name": "bool"},
                ],
            },
        )
        self.assertEqual(
            arg_type_exprs.get("ys"),
            {
                "kind": "GenericType",
                "base": "list",
                "args": [
                    {
                        "kind": "UnionType",
                        "union_mode": "general",
                        "options": [
                            {"kind": "NamedType", "name": "int64"},
                            {"kind": "NamedType", "name": "bool"},
                        ],
                    }
                ],
            },
        )
        self.assertEqual(
            arg_type_exprs.get("payload"),
            {
                "kind": "OptionalType",
                "inner": {
                    "kind": "NominalAdtType",
                    "name": "JsonValue",
                    "adt_family": "json",
                    "variant_domain": "closed",
                },
            },
        )
        self.assertEqual(
            fn.get("return_type_expr"),
            {
                "kind": "GenericType",
                "base": "dict",
                "args": [
                    {"kind": "NamedType", "name": "str"},
                    {
                        "kind": "UnionType",
                        "union_mode": "general",
                        "options": [
                            {"kind": "NamedType", "name": "int64"},
                            {"kind": "NamedType", "name": "bool"},
                        ],
                    },
                ],
            },
        )

        ann_assign = next(
            st for st in fn.get("body", []) if isinstance(st, dict) and st.get("kind") == "AnnAssign"
        )
        self.assertEqual(ann_assign.get("annotation"), "list[int64|bool]")
        self.assertEqual(
            ann_assign.get("annotation_type_expr"),
            {
                "kind": "GenericType",
                "base": "list",
                "args": [
                    {
                        "kind": "UnionType",
                        "union_mode": "general",
                        "options": [
                            {"kind": "NamedType", "name": "int64"},
                            {"kind": "NamedType", "name": "bool"},
                        ],
                    }
                ],
            },
        )

    def test_type_expr_is_built_for_union_optional_and_nominal_annotations(self) -> None:
        src = """
from pytra.std.json import JsonObj, JsonValue

def f(x: int | bool, xs: list[int | bool], payload: JsonValue | None) -> JsonObj | None:
    local: dict[str, int | bool] = {}
    return None
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        fn = next(
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "f"
        )
        arg_type_exprs = fn.get("arg_type_exprs", {})
        self.assertEqual(
            arg_type_exprs.get("x"),
            {
                "kind": "UnionType",
                "union_mode": "general",
                "options": [
                    {"kind": "NamedType", "name": "int64"},
                    {"kind": "NamedType", "name": "bool"},
                ],
            },
        )
        self.assertEqual(
            arg_type_exprs.get("xs"),
            {
                "kind": "GenericType",
                "base": "list",
                "args": [
                    {
                        "kind": "UnionType",
                        "union_mode": "general",
                        "options": [
                            {"kind": "NamedType", "name": "int64"},
                            {"kind": "NamedType", "name": "bool"},
                        ],
                    }
                ],
            },
        )
        self.assertEqual(
            arg_type_exprs.get("payload"),
            {
                "kind": "OptionalType",
                "inner": {
                    "kind": "NominalAdtType",
                    "name": "JsonValue",
                    "adt_family": "json",
                    "variant_domain": "closed",
                },
            },
        )
        self.assertEqual(
            fn.get("return_type_expr"),
            {
                "kind": "OptionalType",
                "inner": {
                    "kind": "NominalAdtType",
                    "name": "JsonObj",
                    "adt_family": "json",
                    "variant_domain": "closed",
                },
            },
        )
        ann_assign = next(
            n
            for n in fn.get("body", [])
            if isinstance(n, dict) and n.get("kind") == "AnnAssign"
        )
        expected_decl = {
            "kind": "GenericType",
            "base": "dict",
            "args": [
                {"kind": "NamedType", "name": "str"},
                {
                    "kind": "UnionType",
                    "union_mode": "general",
                    "options": [
                        {"kind": "NamedType", "name": "int64"},
                        {"kind": "NamedType", "name": "bool"},
                    ],
                },
            ],
        }
        self.assertEqual(ann_assign.get("annotation_type_expr"), expected_decl)
        self.assertEqual(ann_assign.get("decl_type_expr"), expected_decl)
        self.assertEqual(ann_assign.get("target", {}).get("type_expr"), expected_decl)

    def test_dict_set_comprehension_infers_target_type(self) -> None:
        src = """
def main() -> None:
    xs: list[int] = [1, 2, 3, 4]
    ys: set[int] = {x * x for x in xs if x % 2 == 1}
    ds: dict[int, int] = {x: x * x for x in xs if x % 2 == 0}
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        dict_comps = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "DictComp"]
        set_comps = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "SetComp"]
        self.assertEqual(len(dict_comps), 1)
        self.assertEqual(len(set_comps), 1)
        dc = dict_comps[0]
        sc = set_comps[0]
        self.assertEqual(dc.get("resolved_type"), "dict[int64,int64]")
        self.assertEqual(sc.get("resolved_type"), "set[int64]")
        self.assertEqual(dc.get("key", {}).get("resolved_type"), "int64")
        self.assertEqual(dc.get("value", {}).get("resolved_type"), "int64")
        self.assertEqual(sc.get("elt", {}).get("resolved_type"), "int64")
        d_ifs = dc.get("generators", [{}])[0].get("ifs", [])
        s_ifs = sc.get("generators", [{}])[0].get("ifs", [])
        self.assertEqual(len(d_ifs), 1)
        self.assertEqual(len(s_ifs), 1)

    def test_list_comprehension_over_range_uses_range_expr(self) -> None:
        src = """
def main() -> list[int]:
    return [x for x in range(3)]
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        list_comps = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "ListComp"]
        self.assertEqual(len(list_comps), 1)
        generators = list_comps[0].get("generators", [])
        self.assertEqual(len(generators), 1)
        iter_node = generators[0].get("iter", {})
        self.assertEqual(iter_node.get("kind"), "RangeExpr")
        self.assertEqual(iter_node.get("range_mode"), "ascending")
        self.assertEqual(iter_node.get("start", {}).get("value"), 0)
        self.assertEqual(iter_node.get("stop", {}).get("value"), 3)
        self.assertEqual(iter_node.get("step", {}).get("value"), 1)

    def test_lambda_expression_builds_lambda_node(self) -> None:
        src = """
def main() -> None:
    fn = lambda x: x + 1
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        lambdas = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Lambda"]
        self.assertEqual(len(lambdas), 1)
        lam = lambdas[0]
        self.assertEqual([arg.get("arg") for arg in lam.get("args", [])], ["x"])
        self.assertEqual(lam.get("body", {}).get("kind"), "BinOp")

    def test_fstring_builds_joinedstr_and_formatted_value_nodes(self) -> None:
        src = """
def main(name: str) -> str:
    return f"hello {name}"
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        joined = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "JoinedStr"]
        self.assertEqual(len(joined), 1)
        values = joined[0].get("values", [])
        formatted = [v for v in values if isinstance(v, dict) and v.get("kind") == "FormattedValue"]
        self.assertEqual(len(formatted), 1)
        self.assertEqual(formatted[0].get("value", {}).get("kind"), "Name")
        self.assertEqual(formatted[0].get("value", {}).get("id"), "name")

    def test_except_without_as_is_supported(self) -> None:
        src = """
def f(x: str) -> bool:
    try:
        _ = int(x)
        return True
    except ValueError:
        return False

def main() -> None:
    print(f("12"))

if __name__ == "__main__":
    main()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        try_nodes = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Try"]
        self.assertEqual(len(try_nodes), 1)
        handlers = try_nodes[0].get("handlers", [])
        self.assertEqual(len(handlers), 1)
        self.assertIsNone(handlers[0].get("name"))

    def test_builtin_call_lowering_for_common_methods(self) -> None:
        src = """
from pathlib import Path

def main() -> None:
    s: str = "  abc  "
    t: str = s.strip()
    u: str = s.lstrip()
    p0: int = s.find("a")
    p1: int = s.rfind("a")
    blob: bytes = bytes()
    ba: bytearray = bytearray(blob)
    xs: list[int] = []
    xs.append(1)
    zp = zip(xs, xs)
    n: int = int("10", 16)
    o: object = xs
    b: bool = bool(o)
    it = iter(xs)
    first = next(it)
    ri = reversed(xs)
    en = enumerate(xs, 1)
    has_any: bool = any(xs)
    has_all: bool = all(xs)
    ch: str = chr(65)
    ocode: int = ord("A")
    r = range(3)
    ys: list[int] = list(xs)
    zs: set[int] = set(xs)
    d: dict[str, int] = {"a": 1}
    d2: dict[str, int] = dict(d)
    v: int = d.get("a", 0)
    p: Path = Path("tmp")
    ok: bool = p.exists()
    print(len(xs), t, u, p0, p1, len(ba), n, b, first, ri, en, zp, has_any, has_all, ch, ocode, len(ys), len(zs), len(d2), v, ok)

if __name__ == "__main__":
    main()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        calls = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Call"]
        runtime_calls = {str(n.get("runtime_call")) for n in calls if n.get("lowered_kind") == "BuiltinCall"}
        semantic_tags = {str(n.get("semantic_tag")) for n in calls if n.get("lowered_kind") == "BuiltinCall"}
        self.assertIn("py_strip", runtime_calls)
        self.assertIn("py_lstrip", runtime_calls)
        self.assertIn("py_find", runtime_calls)
        self.assertIn("py_rfind", runtime_calls)
        self.assertIn("bytes_ctor", runtime_calls)
        self.assertIn("bytearray_ctor", runtime_calls)
        self.assertIn("py_iter_or_raise", runtime_calls)
        self.assertIn("py_next_or_stop", runtime_calls)
        self.assertIn("py_reversed", runtime_calls)
        self.assertIn("py_enumerate", runtime_calls)
        self.assertIn("zip", runtime_calls)
        self.assertIn("py_any", runtime_calls)
        self.assertIn("py_all", runtime_calls)
        self.assertIn("py_ord", runtime_calls)
        self.assertIn("py_chr", runtime_calls)
        self.assertIn("py_range", runtime_calls)
        self.assertIn("list_ctor", runtime_calls)
        self.assertIn("set_ctor", runtime_calls)
        self.assertIn("dict_ctor", runtime_calls)
        self.assertIn("py_to_bool", runtime_calls)
        self.assertIn("py_to_int64_base", runtime_calls)
        self.assertIn("list.append", runtime_calls)
        self.assertIn("dict.get", runtime_calls)
        self.assertIn("std::filesystem::exists", runtime_calls)
        self.assertIn("py_len", runtime_calls)
        self.assertIn("py_print", runtime_calls)
        self.assertIn("core.len", semantic_tags)
        self.assertIn("core.print", semantic_tags)
        self.assertIn("cast.bool", semantic_tags)
        self.assertIn("cast.int", semantic_tags)
        self.assertIn("iter.init", semantic_tags)
        self.assertIn("iter.next", semantic_tags)
        self.assertIn("logic.any", semantic_tags)
        self.assertIn("logic.all", semantic_tags)
        runtime_bindings = {
            str(n.get("runtime_call")): (str(n.get("runtime_module_id", "")), str(n.get("runtime_symbol", "")))
            for n in calls
            if n.get("lowered_kind") == "BuiltinCall" and isinstance(n.get("runtime_call"), str)
        }
        self.assertEqual(runtime_bindings.get("py_enumerate"), ("pytra.built_in.iter_ops", "enumerate"))
        self.assertEqual(runtime_bindings.get("py_any"), ("pytra.built_in.predicates", "any"))
        self.assertEqual(runtime_bindings.get("py_print"), ("pytra.built_in.io_ops", "py_print"))
        self.assertEqual(runtime_bindings.get("py_to_int64_base"), ("pytra.built_in.scalar_ops", "py_to_int64_base"))
        self.assertEqual(runtime_bindings.get("py_ord"), ("pytra.built_in.scalar_ops", "py_ord"))
        self.assertEqual(runtime_bindings.get("py_chr"), ("pytra.built_in.scalar_ops", "py_chr"))
        self.assertEqual(runtime_bindings.get("dict.get"), ("pytra.core.dict", "dict.get"))
        self.assertEqual(runtime_bindings.get("std::filesystem::exists"), ("pytra.std.pathlib", "Path.exists"))

    def test_perf_counter_resolved_type_comes_from_stdlib_signature(self) -> None:
        src = """
from pytra.std.time import perf_counter

def main() -> float:
    t0: float = perf_counter()
    return t0
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        calls = [
            n
            for n in _walk(east)
            if isinstance(n, dict)
            and n.get("kind") == "Call"
            and n.get("lowered_kind") == "BuiltinCall"
            and n.get("runtime_call") == "perf_counter"
        ]
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].get("resolved_type"), "float64")
        self.assertEqual(calls[0].get("runtime_module_id"), "pytra.std.time")
        self.assertEqual(calls[0].get("runtime_symbol"), "perf_counter")

    def test_noncpp_runtime_call_annotations_for_import_symbol_and_module_attr(self) -> None:
        src = """
from pytra.std import json
from pytra.utils import png, gif
from pytra.utils.assertions import py_assert_stdout
import math

def main() -> None:
    obj = json.loads("{\\"ok\\": true}")
    txt = json.dumps(obj)
    pixels: bytes = bytes([0, 0, 0])
    wave = math.sin(math.pi)
    png.write_rgb_png("x.png", 1, 1, pixels)
    palette = gif.grayscale_palette()
    gif.save_gif("x.gif", 1, 1, [pixels], palette, delay_cs=1, loop=0)
    py_assert_stdout("ok", txt + str(wave))
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        calls = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Call"]
        resolved_runtime_calls = {
            str(n.get("resolved_runtime_call"))
            for n in calls
            if isinstance(n.get("resolved_runtime_call"), str)
            and str(n.get("resolved_runtime_call")) != ""
        }
        self.assertIn("json.loads", resolved_runtime_calls)
        self.assertIn("json.dumps", resolved_runtime_calls)
        self.assertIn("write_rgb_png", resolved_runtime_calls)
        self.assertIn("save_gif", resolved_runtime_calls)
        self.assertIn("grayscale_palette", resolved_runtime_calls)
        self.assertIn("py_assert_stdout", resolved_runtime_calls)
        self.assertIn("math.sin", resolved_runtime_calls)
        math_sin_calls = [
            n for n in calls if isinstance(n.get("resolved_runtime_call"), str) and n.get("resolved_runtime_call") == "math.sin"
        ]
        self.assertEqual(len(math_sin_calls), 1)
        self.assertEqual(math_sin_calls[0].get("resolved_type"), "float64")
        self.assertEqual(math_sin_calls[0].get("runtime_module_id"), "math")
        self.assertEqual(math_sin_calls[0].get("runtime_symbol"), "sin")
        json_loads_calls = [
            n for n in calls if isinstance(n.get("resolved_runtime_call"), str) and n.get("resolved_runtime_call") == "json.loads"
        ]
        self.assertEqual(len(json_loads_calls), 1)
        self.assertEqual(json_loads_calls[0].get("runtime_module_id"), "pytra.std.json")
        self.assertEqual(json_loads_calls[0].get("runtime_symbol"), "loads")
        png_calls = [
            n for n in calls if isinstance(n.get("resolved_runtime_call"), str) and n.get("resolved_runtime_call") == "write_rgb_png"
        ]
        self.assertEqual(len(png_calls), 1)
        self.assertEqual(png_calls[0].get("runtime_module_id"), "pytra.utils.png")
        self.assertEqual(png_calls[0].get("runtime_symbol"), "write_rgb_png")
        attrs = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Attribute"]
        resolved_runtime_attrs = {
            str(n.get("resolved_runtime_call"))
            for n in attrs
            if isinstance(n.get("resolved_runtime_call"), str)
            and str(n.get("resolved_runtime_call")) != ""
        }
        self.assertIn("math.pi", resolved_runtime_attrs)
        math_pi_attrs = [
            n for n in attrs if isinstance(n.get("resolved_runtime_call"), str) and n.get("resolved_runtime_call") == "math.pi"
        ]
        self.assertEqual(len(math_pi_attrs), 1)
        self.assertEqual(math_pi_attrs[0].get("runtime_module_id"), "math")
        self.assertEqual(math_pi_attrs[0].get("runtime_symbol"), "pi")

    def test_json_decode_helpers_receive_json_semantic_tags(self) -> None:
        src = """
from pytra.std import json
from pytra.std.json import JsonArr, JsonObj, JsonValue

def main(text: str, value: JsonValue, obj: JsonObj, arr: JsonArr) -> None:
    root = json.loads(text)
    obj0 = json.loads_obj(text)
    arr0 = json.loads_arr(text)
    a = value.as_obj()
    b = value.as_int()
    c = obj.get_arr("items")
    d = arr.get_bool(0)
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        calls = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "Call" and isinstance(n.get("repr"), str)
        ]
        by_repr = {str(n.get("repr")): n for n in calls}
        self.assertEqual(by_repr["json.loads(text)"].get("semantic_tag"), "json.loads")
        self.assertEqual(by_repr["json.loads_obj(text)"].get("semantic_tag"), "json.loads_obj")
        self.assertEqual(by_repr["json.loads_arr(text)"].get("semantic_tag"), "json.loads_arr")
        self.assertEqual(by_repr["value.as_obj()"].get("semantic_tag"), "json.value.as_obj")
        self.assertEqual(by_repr["value.as_int()"].get("semantic_tag"), "json.value.as_int")
        self.assertEqual(by_repr['obj.get_arr("items")'].get("semantic_tag"), "json.obj.get_arr")
        self.assertEqual(by_repr["arr.get_bool(0)"].get("semantic_tag"), "json.arr.get_bool")

    def test_core_does_not_reintroduce_perf_counter_direct_branch(self) -> None:
        src = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        self.assertNotIn('fn_name == "perf_counter"', src)
        self.assertNotIn("fn_name == 'perf_counter'", src)

    def test_core_does_not_reintroduce_path_direct_branches(self) -> None:
        src = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        self.assertNotIn('fn_name == "Path"', src)
        self.assertNotIn("fn_name == 'Path'", src)
        self.assertNotIn('owner_t == "Path"', src)
        self.assertNotIn("owner_t == 'Path'", src)

    def test_core_semantic_tag_mapping_is_adapter_driven(self) -> None:
        src = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("lookup_builtin_semantic_tag", src)
        self.assertIn("lookup_stdlib_function_semantic_tag", src)
        self.assertIn("lookup_stdlib_symbol_semantic_tag", src)
        self.assertIn("lookup_stdlib_method_semantic_tag", src)
        self.assertNotIn('payload["semantic_tag"] = "', src)

    def test_path_constructor_is_resolved_via_import_binding(self) -> None:
        src = """
from pathlib import Path as P
from pytra.std.pathlib import Path as PP

def main() -> None:
    p = P("out")
    q = PP("tmp")
    r = p / "a.txt"
    print(q, r)
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        calls = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Call"]
        path_ctor_calls = [
            n
            for n in calls
            if n.get("lowered_kind") == "BuiltinCall" and n.get("runtime_call") == "Path"
        ]
        self.assertEqual(len(path_ctor_calls), 2)
        for call in path_ctor_calls:
            self.assertEqual(call.get("resolved_type"), "Path")
            self.assertEqual(call.get("runtime_module_id"), "pytra.std.pathlib")
            self.assertEqual(call.get("runtime_symbol"), "Path")

        path_div_binops = [
            n
            for n in _walk(east)
            if isinstance(n, dict)
            and n.get("kind") == "BinOp"
            and n.get("op") == "Div"
            and n.get("resolved_type") == "Path"
        ]
        self.assertEqual(len(path_div_binops), 1)

    def test_path_mkdir_keywords_are_kept(self) -> None:
        src = """
from pathlib import Path

def main() -> None:
    p: Path = Path("out")
    p.mkdir(parents=True, exist_ok=True)
    print(True)

if __name__ == "__main__":
    main()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        mkdir_calls = [
            n
            for n in _walk(east)
            if isinstance(n, dict)
            and n.get("kind") == "Call"
            and n.get("runtime_call") == "std::filesystem::create_directories"
        ]
        self.assertEqual(len(mkdir_calls), 1)
        kws = mkdir_calls[0].get("keywords", [])
        names = [k.get("arg") for k in kws if isinstance(k, dict)]
        self.assertIn("parents", names)
        self.assertIn("exist_ok", names)

    def test_path_property_attributes_are_lowered_with_runtime_call(self) -> None:
        src = """
from pathlib import Path

def main() -> None:
    p: Path = Path("out/a.txt")
    parent = p.parent
    name = p.name
    stem = p.stem
    print(parent, name, stem)
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        attrs = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Attribute"]
        path_attrs = [n for n in attrs if str(n.get("attr")) in {"parent", "name", "stem"}]
        self.assertEqual(len(path_attrs), 3)
        runtime_calls = {str(n.get("runtime_call")) for n in path_attrs}
        self.assertEqual(runtime_calls, {"path_parent", "path_name", "path_stem"})
        lowered_kinds = {str(n.get("lowered_kind")) for n in path_attrs}
        self.assertEqual(lowered_kinds, {"BuiltinAttr"})
        semantic_tags = {str(n.get("semantic_tag")) for n in path_attrs}
        self.assertEqual(
            semantic_tags,
            {"stdlib.method.parent", "stdlib.method.name", "stdlib.method.stem"},
        )

    def test_range_keywords_are_kept_for_builtin_call(self) -> None:
        src = """
def main() -> None:
    r = range(start=1, stop=5, step=2)
    print(r)
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        range_calls = [
            n
            for n in _walk(east)
            if isinstance(n, dict)
            and n.get("kind") == "Call"
            and n.get("lowered_kind") == "BuiltinCall"
            and n.get("runtime_call") == "py_range"
        ]
        self.assertEqual(len(range_calls), 1)
        kws = range_calls[0].get("keywords", [])
        names = [k.get("arg") for k in kws if isinstance(k, dict)]
        self.assertEqual(names, ["start", "stop", "step"])

    def test_numeric_literal_prefixes_are_parsed(self) -> None:
        src = """
def main() -> int:
    a: int = 0xFF
    b: int = 0X10
    return a + b
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        constants = [n.get("value") for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Constant"]
        self.assertIn(255, constants)
        self.assertIn(16, constants)

    def test_identifier_prefixed_with_import_is_not_import_stmt(self) -> None:
        src = """
def f() -> None:
    import_modules: dict[str, str] = {}
    print(import_modules)

if __name__ == "__main__":
    f()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "f"]
        self.assertEqual(len(funcs), 1)
        body = funcs[0].get("body", [])
        ann = [n for n in body if isinstance(n, dict) and n.get("kind") == "AnnAssign"]
        self.assertEqual(len(ann), 1)
        target = ann[0].get("target")
        self.assertIsInstance(target, dict)
        self.assertEqual(target.get("id"), "import_modules")

    def test_future_annotations_is_not_emitted_to_east_imports(self) -> None:
        src = """
from __future__ import annotations
from pytra.std import json

def main() -> int:
    x: "int" = 1
    _ = json.dumps({"x": x})
    return x
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        import_from_nodes = [
            n
            for n in _walk(east)
            if isinstance(n, dict)
            and n.get("kind") == "ImportFrom"
        ]
        future_nodes = [n for n in import_from_nodes if n.get("module") == "__future__"]
        self.assertEqual(future_nodes, [])
        meta = east.get("meta", {})
        import_bindings = meta.get("import_bindings", [])
        self.assertIsInstance(import_bindings, list)
        for ent in import_bindings:
            if isinstance(ent, dict):
                self.assertNotEqual(ent.get("module_id"), "__future__")

    def test_typing_imports_are_annotation_only_noop(self) -> None:
        src = """
import typing
from typing import Any as A, List as L
from pytra.std import json

def main(xs: L[int]) -> A:
    _ = json.dumps({"n": len(xs)})
    return xs
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        import_nodes = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") in {"Import", "ImportFrom"}
        ]
        self.assertEqual(len(import_nodes), 1)
        self.assertEqual(import_nodes[0].get("kind"), "ImportFrom")
        self.assertEqual(import_nodes[0].get("module"), "pytra.std")

        meta = east.get("meta", {})
        import_bindings = meta.get("import_bindings", [])
        self.assertIsInstance(import_bindings, list)
        module_ids = [
            str(ent.get("module_id"))
            for ent in import_bindings
            if isinstance(ent, dict) and isinstance(ent.get("module_id"), str)
        ]
        self.assertNotIn("typing", module_ids)
        self.assertIn("pytra.std", module_ids)

    def test_typing_alias_is_resolved_without_runtime_import(self) -> None:
        src = """
from typing import List as L

def main() -> None:
    ys: L[int] = []
    print(ys)
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        fn = next(
            n
            for n in east.get("body", [])
            if isinstance(n, dict)
            and n.get("kind") == "FunctionDef"
            and (n.get("original_name") == "main" or n.get("name") == "main")
        )
        ann_assigns = [
            st for st in fn.get("body", []) if isinstance(st, dict) and st.get("kind") == "AnnAssign"
        ]
        self.assertEqual(len(ann_assigns), 1)
        self.assertEqual(ann_assigns[0].get("annotation"), "list[int64]")
        self.assertEqual(ann_assigns[0].get("value", {}).get("resolved_type"), "list[unknown]")

        import_bindings = east.get("meta", {}).get("import_bindings", [])
        self.assertEqual(import_bindings, [])

    def test_future_non_annotations_is_rejected(self) -> None:
        src = """
from __future__ import generator_stop
"""
        with self.assertRaises((EastBuildError, RuntimeError)) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("__future__", str(cm.exception))

    def test_builtin_call_nodes_always_have_runtime_call(self) -> None:
        src = """
from pathlib import Path

def main(xs: list[int], s: str, p: Path) -> None:
    _ = print(len(xs), str(1), int("10", 16), bool(xs), range(3), zip(xs, xs))
    _ = s.strip()
    _ = s.find("x")
    _ = p.exists()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        builtin_calls = [
            n
            for n in _walk(east)
            if isinstance(n, dict)
            and n.get("kind") == "Call"
            and n.get("lowered_kind") == "BuiltinCall"
        ]
        self.assertGreater(len(builtin_calls), 0)
        missing_runtime = [
            n
            for n in builtin_calls
            if not isinstance(n.get("runtime_call"), str) or str(n.get("runtime_call")) == ""
        ]
        self.assertEqual(missing_runtime, [])

    def test_builtin_method_calls_keep_runtime_owner(self) -> None:
        src = """
from pathlib import Path

def main(xs: list[int], d: dict[str, int], s: str, n: int, p: Path) -> None:
    xs.append(1)
    _ = d.get("a", 0)
    _ = s.strip()
    _ = n.to_bytes(2, "little")
    _ = p.exists()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        calls = [
            n
            for n in _walk(east)
            if isinstance(n, dict)
            and n.get("kind") == "Call"
            and n.get("lowered_kind") == "BuiltinCall"
        ]
        target_runtime_calls = {"list.append", "dict.get", "py_strip", "py_int_to_bytes", "std::filesystem::exists"}
        targets = [c for c in calls if str(c.get("runtime_call")) in target_runtime_calls]
        self.assertEqual(len(targets), 5)
        for c in targets:
            owner = c.get("runtime_owner")
            self.assertIsInstance(owner, dict)
            self.assertNotEqual(owner.get("kind"), "")

    def test_raw_range_call_is_lowered_out(self) -> None:
        src = """
def main() -> None:
    s: int = 0
    for i in range(3):
        s += i
    print(s)

if __name__ == "__main__":
    main()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        calls = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Call"]
        has_raw_range = any(
            isinstance(c.get("func"), dict)
            and c.get("func", {}).get("kind") == "Name"
            and c.get("func", {}).get("id") == "range"
            for c in calls
        )
        self.assertFalse(has_raw_range)
        has_for_range = any(
            isinstance(n, dict) and n.get("kind") == "ForRange"
            for n in _walk(east)
        )
        self.assertTrue(has_for_range)

    def test_for_iter_mode_and_iterable_traits_are_annotated(self) -> None:
        src = """
def f(xs: list[int], d: dict[str, int], x: object) -> None:
    for a in xs:
        pass
    for k in d:
        pass
    for v in x:
        pass
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "f"]
        self.assertEqual(len(funcs), 1)
        body = funcs[0].get("body", [])
        for_nodes = [n for n in body if isinstance(n, dict) and n.get("kind") == "For"]
        self.assertEqual(len(for_nodes), 3)

        list_for = for_nodes[0]
        self.assertEqual(list_for.get("iter_mode"), "static_fastpath")
        self.assertEqual(list_for.get("iter_element_type"), "int64")
        self.assertEqual(list_for.get("iter", {}).get("iterable_trait"), "yes")
        self.assertEqual(list_for.get("iter", {}).get("iter_protocol"), "static_range")

        dict_for = for_nodes[1]
        self.assertEqual(dict_for.get("iter_mode"), "static_fastpath")
        self.assertEqual(dict_for.get("iter_element_type"), "str")
        self.assertEqual(dict_for.get("iter", {}).get("iterable_trait"), "yes")
        self.assertEqual(dict_for.get("iter", {}).get("iter_protocol"), "static_range")

        obj_for = for_nodes[2]
        self.assertEqual(obj_for.get("iter_mode"), "runtime_protocol")
        self.assertEqual(obj_for.get("iter_source_type"), "object")
        self.assertEqual(obj_for.get("iter", {}).get("iterable_trait"), "unknown")
        self.assertEqual(obj_for.get("iter", {}).get("iter_protocol"), "runtime_protocol")

    def test_super_call_is_parsed(self) -> None:
        src = """
class Base:
    def __init__(self) -> None:
        self.x: int = 1

class Child(Base):
    def __init__(self) -> None:
        super().__init__()
        self.x += 1

def main() -> None:
    c: Child = Child()
    print(c.x)

if __name__ == "__main__":
    main()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        calls = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Call"]
        has_super = any(
            isinstance(c.get("func"), dict)
            and c.get("func", {}).get("kind") == "Attribute"
            and isinstance(c.get("func", {}).get("value"), dict)
            and c.get("func", {}).get("value", {}).get("kind") == "Call"
            and isinstance(c.get("func", {}).get("value", {}).get("func"), dict)
            and c.get("func", {}).get("value", {}).get("func", {}).get("kind") == "Name"
            and c.get("func", {}).get("value", {}).get("func", {}).get("id") == "super"
            for c in calls
        )
        self.assertTrue(has_super)

    def test_object_receiver_access_is_rejected(self) -> None:
        src = """
def f(x: object) -> int:
    return x.bit_length()

def main() -> None:
    print(f(1))

if __name__ == "__main__":
    main()
"""
        with self.assertRaises((EastBuildError, RuntimeError)):
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")

    def test_bare_return_is_parsed_as_return_stmt(self) -> None:
        src = """
def f(flag: bool) -> None:
    if flag:
        return
    print(1)

def main() -> None:
    f(True)
    print(True)

if __name__ == "__main__":
    main()
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        returns = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Return"]
        self.assertGreaterEqual(len(returns), 1)
        bare = [r for r in returns if r.get("value") is None]
        self.assertGreaterEqual(len(bare), 1)

    def test_class_storage_hint_override_is_supported(self) -> None:
        src = """
class Box:
    __pytra_class_storage_hint__ = "value"

    def __init__(self, x: int) -> None:
        self.x = x
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        classes = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "ClassDef" and n.get("name") == "Box"]
        self.assertEqual(len(classes), 1)
        cls = classes[0]
        self.assertEqual(cls.get("class_storage_hint"), "value")
        names = []
        for st in cls.get("body", []):
            if isinstance(st, dict) and st.get("kind") == "Assign":
                tgt = st.get("target")
                if isinstance(tgt, dict) and tgt.get("kind") == "Name":
                    names.append(tgt.get("id"))
        self.assertNotIn("__pytra_class_storage_hint__", names)

    def test_dataclass_scalar_fields_are_value_candidates(self) -> None:
        src = """
from dataclasses import dataclass

@dataclass
class Token:
    kind: str
    text: str
    pos: int
    number_value: int
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        classes = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "ClassDef" and n.get("name") == "Token"]
        self.assertEqual(len(classes), 1)
        self.assertEqual(classes[0].get("class_storage_hint"), "value")

    def test_dataclass_container_field_falls_back_to_ref(self) -> None:
        src = """
from dataclasses import dataclass

@dataclass
class Box:
    items: list[int]
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        classes = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "ClassDef" and n.get("name") == "Box"]
        self.assertEqual(len(classes), 1)
        self.assertEqual(classes[0].get("class_storage_hint"), "ref")

    def test_std_dataclasses_imports_are_noop_and_decorator_resolves(self) -> None:
        src = """
import dataclasses as dc
from dataclasses import dataclass as d

@dc.dataclass(eq=False)
class A:
    x: int

@d(init=False, frozen=True)
class B:
    y: int
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")

        import_nodes = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") in {"Import", "ImportFrom"}
        ]
        self.assertEqual(import_nodes, [])

        import_bindings = east.get("meta", {}).get("import_bindings", [])
        self.assertIsInstance(import_bindings, list)
        for ent in import_bindings:
            if isinstance(ent, dict):
                self.assertNotEqual(ent.get("module_id"), "dataclasses")

        classes = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "ClassDef" and n.get("name") in {"A", "B"}
        ]
        self.assertEqual(len(classes), 2)
        by_name = {str(c.get("name")): c for c in classes}
        self.assertTrue(bool(by_name["A"].get("dataclass")))
        self.assertTrue(bool(by_name["B"].get("dataclass")))
        opts_a = by_name["A"].get("dataclass_options", {})
        opts_b = by_name["B"].get("dataclass_options", {})
        self.assertIsInstance(opts_a, dict)
        self.assertIsInstance(opts_b, dict)
        self.assertEqual(opts_a.get("eq"), False)
        self.assertEqual(opts_b.get("init"), False)
        self.assertEqual(opts_b.get("frozen"), True)

    def test_nominal_adt_family_and_variants_are_parsed(self) -> None:
        src = """
from dataclasses import dataclass

@sealed
class Maybe:
    pass

@dataclass
class Just(Maybe):
    value: int

class Nothing(Maybe):
    pass
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        classes = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "ClassDef" and n.get("name") in {"Maybe", "Just", "Nothing"}
        ]
        self.assertEqual(len(classes), 3)
        by_name = {str(c.get("name")): c for c in classes}

        maybe = by_name["Maybe"]
        maybe_meta = maybe.get("meta", {}).get("nominal_adt_v1", {})
        self.assertEqual(maybe.get("decorators"), ["sealed"])
        self.assertEqual(maybe_meta.get("role"), "family")
        self.assertEqual(maybe_meta.get("family_name"), "Maybe")
        self.assertEqual(maybe_meta.get("surface_phase"), "declaration_v1")
        self.assertEqual(maybe_meta.get("closed"), 1)

        just = by_name["Just"]
        just_meta = just.get("meta", {}).get("nominal_adt_v1", {})
        self.assertTrue(bool(just.get("dataclass")))
        self.assertEqual(just.get("base"), "Maybe")
        self.assertEqual(just_meta.get("role"), "variant")
        self.assertEqual(just_meta.get("family_name"), "Maybe")
        self.assertEqual(just_meta.get("variant_name"), "Just")
        self.assertEqual(just_meta.get("payload_style"), "dataclass")

        nothing = by_name["Nothing"]
        nothing_meta = nothing.get("meta", {}).get("nominal_adt_v1", {})
        self.assertEqual(nothing.get("base"), "Maybe")
        self.assertEqual(nothing_meta.get("role"), "variant")
        self.assertEqual(nothing_meta.get("family_name"), "Maybe")
        self.assertEqual(nothing_meta.get("variant_name"), "Nothing")
        self.assertEqual(nothing_meta.get("payload_style"), "unit")

    def test_nominal_adt_payload_variant_requires_dataclass(self) -> None:
        src = """
@sealed
class Maybe:
    pass

class Bad(Maybe):
    value: int
"""
        with self.assertRaisesRegex(RuntimeError, "payload variant 'Bad' must use @dataclass"):
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")

    def test_enum_members_are_parsed_in_class_body(self) -> None:
        src = """
from pytra.std.enum import Enum

class Color(Enum):
    RED = 1
    BLUE = 2
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        classes = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "ClassDef" and n.get("name") == "Color"]
        self.assertEqual(len(classes), 1)
        cls = classes[0]
        self.assertEqual(cls.get("base"), "Enum")
        self.assertEqual(cls.get("class_storage_hint"), "value")
        members: list[str] = []
        for st in cls.get("body", []):
            if isinstance(st, dict) and st.get("kind") == "Assign":
                tgt = st.get("target")
                if isinstance(tgt, dict) and tgt.get("kind") == "Name":
                    members.append(str(tgt.get("id", "")))
        self.assertIn("RED", members)
        self.assertIn("BLUE", members)

    def test_parser_accepts_bom_line_continuation_and_pow(self) -> None:
        src = """\ufefffrom pytra.std import math

def main() -> None:
    x: int = 1 + \\
        2
    y: float = math.sqrt(float(x ** 2))
    print(x, y)
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        binops = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "BinOp"]
        has_pow = any(b.get("op") == "Pow" for b in binops)
        self.assertTrue(has_pow)

    def test_parser_accepts_top_level_expr_class_pass_nested_def_and_tuple_trailing_comma(self) -> None:
        src = """
class E:
    X = 0,
    pass

def outer() -> int:
    def inner(x: int) -> int:
        return x + 1
    return inner(2)

print(outer())
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        classes = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "ClassDef" and n.get("name") == "E"]
        self.assertEqual(len(classes), 1)
        tuples = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Tuple"]
        self.assertGreaterEqual(len(tuples), 1)
        nested_fns = [
            n
            for n in _walk(east)
            if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "inner"
        ]
        self.assertEqual(len(nested_fns), 1)
        exprs = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "Expr"]
        self.assertGreaterEqual(len(exprs), 1)

    def test_yield_is_parsed_as_generator_function(self) -> None:
        src = """
def gen(n: int) -> int:
    i: int = 0
    while i < n:
        yield i
        i += 1
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "gen"]
        self.assertEqual(len(funcs), 1)
        fn = funcs[0]
        self.assertEqual(fn.get("is_generator"), 1)
        self.assertEqual(fn.get("return_type"), "list[int64]")
        yields = [n for n in _walk(fn.get("body", [])) if isinstance(n, dict) and n.get("kind") == "Yield"]
        self.assertGreaterEqual(len(yields), 1)

    def test_single_line_for_with_yield_is_parsed(self) -> None:
        src = """
def gen() -> int:
    for _ in range(3): yield 1
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "gen"]
        self.assertEqual(len(funcs), 1)
        fn = funcs[0]
        self.assertEqual(fn.get("is_generator"), 1)
        for_ranges = [n for n in _walk(fn.get("body", [])) if isinstance(n, dict) and n.get("kind") == "ForRange"]
        self.assertEqual(len(for_ranges), 1)
        yields = [n for n in _walk(for_ranges[0].get("body", [])) if isinstance(n, dict) and n.get("kind") == "Yield"]
        self.assertEqual(len(yields), 1)

    def test_arg_usage_tracks_reassigned_parameters(self) -> None:
        src = """
def f(x: int, y: int, z: int, w: int) -> int:
    x = x + 1
    for y in range(2):
        z += y
    return x + z + w
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        funcs = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "f"]
        self.assertEqual(len(funcs), 1)
        fn = funcs[0]
        arg_usage = fn.get("arg_usage", {})
        self.assertEqual(arg_usage.get("x"), "reassigned")
        self.assertEqual(arg_usage.get("y"), "reassigned")
        self.assertEqual(arg_usage.get("z"), "reassigned")
        self.assertEqual(arg_usage.get("w"), "readonly")

    def test_arg_usage_ignores_nested_scope_reassignment(self) -> None:
        src = """
def outer(a: int) -> int:
    def inner(a: int) -> int:
        a = a + 1
        return a
    return inner(a)
"""
        east = convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        outer_funcs = [n for n in _walk(east) if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "outer"]
        self.assertEqual(len(outer_funcs), 1)
        outer = outer_funcs[0]
        outer_usage = outer.get("arg_usage", {})
        self.assertEqual(outer_usage.get("a"), "readonly")

        inner_funcs = [n for n in _walk(outer.get("body", [])) if isinstance(n, dict) and n.get("kind") == "FunctionDef" and n.get("name") == "inner"]
        self.assertEqual(len(inner_funcs), 1)
        inner = inner_funcs[0]
        inner_usage = inner.get("arg_usage", {})
        self.assertEqual(inner_usage.get("a"), "reassigned")

    def test_trailing_semicolon_is_rejected(self) -> None:
        src = """
def main() -> None:
    x: int = 1;
    print(x)
"""
        with self.assertRaises((EastBuildError, RuntimeError)) as cm:
            convert_source_to_east_with_backend(src, "<mem>", parser_backend="self_hosted")
        self.assertIn("statement terminator", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
