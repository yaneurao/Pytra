"""Source-contract regressions for EAST core runtime builtin call clusters."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import CORE_CALL_ANNOTATION_SOURCE_PATH
from _east_core_test_support import CORE_EXPR_SHELL_SOURCE_PATH
from _east_core_test_support import CORE_NAMED_CALL_ANNOTATION_SOURCE_PATH
from _east_core_test_support import CORE_RUNTIME_CALL_SEMANTICS_SOURCE_PATH


class EastCoreSourceContractRuntimeBuiltinsTest(unittest.TestCase):
    def test_core_source_routes_collection_ctor_metadata_through_shared_helper(self) -> None:
        runtime_text = CORE_RUNTIME_CALL_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")
        shell_text = CORE_EXPR_SHELL_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_NAMED_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = runtime_text.split("def _sh_annotate_collection_ctor_call_expr", 1)[1].split(
            "def _sh_annotate_anyall_call_expr",
            1,
        )[0]
        named_call_text = annotation_text.split("def _annotate_named_call_expr", 1)[1].split(
            "def _annotate_builtin_named_call_expr",
            1,
        )[0]
        postfix_text = shell_text.split("def _parse_postfix", 1)[1].split("def _make_bin", 1)[0]

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
        runtime_text = CORE_RUNTIME_CALL_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")
        shell_text = CORE_EXPR_SHELL_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_NAMED_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = runtime_text.split("def _sh_annotate_anyall_call_expr", 1)[1].split(
            "def _sh_annotate_ordchr_call_expr",
            1,
        )[0]
        named_call_text = annotation_text.split("def _annotate_named_call_expr", 1)[1].split(
            "def _annotate_builtin_named_call_expr",
            1,
        )[0]
        postfix_text = shell_text.split("def _parse_postfix", 1)[1].split("def _make_bin", 1)[0]

        self.assertIn('_sh_annotate_runtime_call_expr(', helper_text)
        self.assertIn('runtime_call="py_any" if fn_name == "any" else "py_all"', helper_text)
        self.assertIn('module_id="pytra.built_in.predicates"', helper_text)
        self.assertIn("return self._apply_named_call_dispatch(", named_call_text)
        self.assertNotIn('elif fn_name == "any":\n                    _sh_annotate_runtime_call_expr(', postfix_text)
        self.assertNotIn('elif fn_name == "all":\n                    _sh_annotate_runtime_call_expr(', postfix_text)
        self.assertNotIn('runtime_call="py_any" if fn_name == "any" else "py_all"', postfix_text)

    def test_core_source_routes_ordchr_metadata_through_shared_helper(self) -> None:
        runtime_text = CORE_RUNTIME_CALL_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")
        shell_text = CORE_EXPR_SHELL_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_NAMED_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = runtime_text.split("def _sh_annotate_ordchr_call_expr", 1)[1].split(
            "def _sh_annotate_iterator_builtin_call_expr",
            1,
        )[0]
        named_call_text = annotation_text.split("def _annotate_named_call_expr", 1)[1].split(
            "def _annotate_builtin_named_call_expr",
            1,
        )[0]
        postfix_text = shell_text.split("def _parse_postfix", 1)[1].split("def _make_bin", 1)[0]

        self.assertIn('_sh_annotate_runtime_call_expr(', helper_text)
        self.assertIn('runtime_call="py_ord" if fn_name == "ord" else "py_chr"', helper_text)
        self.assertIn('runtime_symbol="py_ord" if fn_name == "ord" else "py_chr"', helper_text)
        self.assertIn('module_id="pytra.built_in.scalar_ops"', helper_text)
        self.assertIn("return self._apply_named_call_dispatch(", named_call_text)
        self.assertNotIn('elif fn_name == "ord":\n                    _sh_annotate_runtime_call_expr(', postfix_text)
        self.assertNotIn('elif fn_name == "chr":\n                    _sh_annotate_runtime_call_expr(', postfix_text)
        self.assertNotIn('runtime_call="py_ord" if fn_name == "ord" else "py_chr"', postfix_text)

    def test_core_source_routes_iterator_builtin_metadata_through_shared_helper(self) -> None:
        runtime_text = CORE_RUNTIME_CALL_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")
        shell_text = CORE_EXPR_SHELL_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_NAMED_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = runtime_text.split("def _sh_annotate_iterator_builtin_call_expr", 1)[1].split(
            "def _sh_annotate_open_call_expr",
            1,
        )[0]
        named_call_text = annotation_text.split("def _annotate_named_call_expr", 1)[1].split(
            "def _annotate_builtin_named_call_expr",
            1,
        )[0]
        postfix_text = shell_text.split("def _parse_postfix", 1)[1].split("def _make_bin", 1)[0]

        self.assertIn('runtime_call = "py_iter_or_raise"', helper_text)
        self.assertIn('if fn_name == "next":', helper_text)
        self.assertIn('runtime_call = "py_next_or_stop"', helper_text)
        self.assertIn('elif fn_name == "reversed":', helper_text)
        self.assertIn('runtime_call = "py_reversed"', helper_text)
        self.assertIn('module_id = "pytra.core.py_runtime"', helper_text)
        self.assertIn('module_id = "pytra.built_in.iter_ops"', helper_text)
        self.assertIn('_sh_annotate_runtime_call_expr(', helper_text)
        self.assertIn("return self._apply_named_call_dispatch(", named_call_text)
        self.assertNotIn('runtime_call="py_iter_or_raise"', postfix_text)
        self.assertNotIn('runtime_call="py_next_or_stop"', postfix_text)
        self.assertNotIn('runtime_call="py_reversed"', postfix_text)
        self.assertNotIn('runtime_call = "py_iter_or_raise"', postfix_text)
        self.assertNotIn('runtime_call = "py_next_or_stop"', postfix_text)
        self.assertNotIn('runtime_call = "py_reversed"', postfix_text)

    def test_core_source_routes_open_metadata_through_shared_helper(self) -> None:
        runtime_text = CORE_RUNTIME_CALL_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")
        shell_text = CORE_EXPR_SHELL_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_NAMED_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = runtime_text.split("def _sh_annotate_open_call_expr", 1)[1].split(
            "def _sh_annotate_exception_ctor_call_expr",
            1,
        )[0]
        named_call_text = annotation_text.split("def _annotate_named_call_expr", 1)[1].split(
            "def _annotate_builtin_named_call_expr",
            1,
        )[0]
        postfix_text = shell_text.split("def _parse_postfix", 1)[1].split("def _make_bin", 1)[0]

        self.assertIn('_sh_annotate_runtime_call_expr(', helper_text)
        self.assertIn('builtin_name="open"', helper_text)
        self.assertIn('runtime_call="open"', helper_text)
        self.assertIn('module_id="pytra.core.py_runtime"', helper_text)
        self.assertIn('runtime_symbol="open"', helper_text)
        self.assertIn("return self._apply_named_call_dispatch(", named_call_text)
        self.assertNotIn('elif fn_name == "open":\n                    _sh_annotate_runtime_call_expr(', postfix_text)
        self.assertNotIn('runtime_call="open"', postfix_text)

    def test_core_source_routes_exception_ctor_metadata_through_shared_helper(self) -> None:
        runtime_text = CORE_RUNTIME_CALL_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")
        shell_text = CORE_EXPR_SHELL_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_NAMED_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = runtime_text.split("def _sh_annotate_exception_ctor_call_expr", 1)[1].split(
            "def _sh_annotate_type_predicate_call_expr",
            1,
        )[0]
        named_call_text = annotation_text.split("def _annotate_named_call_expr", 1)[1].split(
            "def _annotate_builtin_named_call_expr",
            1,
        )[0]
        postfix_text = shell_text.split("def _parse_postfix", 1)[1].split("def _make_bin", 1)[0]

        self.assertIn('_sh_annotate_runtime_call_expr(', helper_text)
        self.assertIn('builtin_name=fn_name', helper_text)
        self.assertIn('runtime_call="std::runtime_error"', helper_text)
        self.assertIn('module_id="pytra.core.py_runtime"', helper_text)
        self.assertIn('runtime_symbol=fn_name', helper_text)
        self.assertIn("return self._apply_named_call_dispatch(", named_call_text)
        self.assertNotIn('elif fn_name in {"Exception", "RuntimeError"}:\n                    _sh_annotate_runtime_call_expr(', postfix_text)
        self.assertNotIn('runtime_call="std::runtime_error"', postfix_text)

    def test_core_source_routes_type_predicate_metadata_through_shared_helper(self) -> None:
        runtime_text = CORE_RUNTIME_CALL_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")
        shell_text = CORE_EXPR_SHELL_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_NAMED_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = runtime_text.split("def _sh_annotate_type_predicate_call_expr", 1)[1].split(
            "def _sh_annotate_fixed_runtime_builtin_call_expr",
            1,
        )[0]
        named_call_text = annotation_text.split("def _annotate_named_call_expr", 1)[1].split(
            "def _subscript_result_type",
            1,
        )[0]
        postfix_text = shell_text.split("def _parse_postfix", 1)[1].split("def _make_bin", 1)[0]

        self.assertIn('_sh_annotate_runtime_call_expr(', helper_text)
        self.assertIn('lowered_kind="TypePredicateCall"', helper_text)
        self.assertIn('builtin_name=fn_name', helper_text)
        self.assertIn("return self._apply_named_call_dispatch(", named_call_text)
        self.assertNotIn('elif fn_name == "isinstance":\n                    _sh_annotate_runtime_call_expr(', postfix_text)
        self.assertNotIn('elif fn_name == "issubclass":\n                    _sh_annotate_runtime_call_expr(', postfix_text)
        self.assertNotIn('lowered_kind="TypePredicateCall"', postfix_text)

    def test_core_source_routes_fixed_runtime_builtin_metadata_through_shared_helper(self) -> None:
        runtime_text = CORE_RUNTIME_CALL_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")
        shell_text = CORE_EXPR_SHELL_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_NAMED_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = runtime_text.split("def _sh_annotate_fixed_runtime_builtin_call_expr", 1)[1].split(
            "def _sh_lookup_named_call_dispatch",
            1,
        )[0]
        named_call_text = annotation_text.split("def _annotate_named_call_expr", 1)[1].split(
            "def _subscript_result_type",
            1,
        )[0]
        postfix_text = shell_text.split("def _parse_postfix", 1)[1].split("def _make_bin", 1)[0]

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
