"""Source-contract regressions for EAST core call dispatch and suffix clusters."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import CORE_ATTR_SUBSCRIPT_SUFFIX_SOURCE_PATH
from _east_core_test_support import CORE_ATTR_CALL_ANNOTATION_SOURCE_PATH
from _east_core_test_support import CORE_CALLEE_CALL_ANNOTATION_SOURCE_PATH
from _east_core_test_support import CORE_CALL_ANNOTATION_SOURCE_PATH
from _east_core_test_support import CORE_CALL_ARG_SOURCE_PATH
from _east_core_test_support import CORE_EXPR_SHELL_SOURCE_PATH
from _east_core_test_support import CORE_CALL_SUFFIX_SOURCE_PATH
from _east_core_test_support import CORE_EXPR_RESOLUTION_SEMANTICS_SOURCE_PATH
from _east_core_test_support import CORE_NAMED_CALL_ANNOTATION_SOURCE_PATH
from _east_core_test_support import CORE_RUNTIME_CALL_SEMANTICS_SOURCE_PATH
from _east_core_test_support import CORE_SOURCE_PATH


class EastCoreSourceContractCallDispatchTest(unittest.TestCase):
    def test_core_source_routes_named_call_lookup_through_shared_helper(self) -> None:
        runtime_text = CORE_RUNTIME_CALL_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")
        shell_text = CORE_EXPR_SHELL_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = runtime_text.split("def _sh_lookup_named_call_dispatch", 1)[1].split(
            "def _sh_infer_known_name_call_return_type",
            1,
        )[0]
        call_helper_text = annotation_text.split("def _annotate_call_expr", 1)[1]
        postfix_text = shell_text.split("def _parse_postfix", 1)[1].split("def _make_bin", 1)[0]

        self.assertIn('return {\n            "builtin_semantic_tag": "",', helper_text)
        self.assertIn('lookup_builtin_semantic_tag(fn_name)', helper_text)
        self.assertIn('lookup_stdlib_function_runtime_call(fn_name)', helper_text)
        self.assertIn('lookup_stdlib_function_semantic_tag(fn_name)', helper_text)
        self.assertIn('lookup_stdlib_imported_symbol_runtime_call(fn_name, import_symbols)', helper_text)
        self.assertIn('lookup_stdlib_symbol_semantic_tag(fn_name)', helper_text)
        self.assertIn('lookup_noncpp_imported_symbol_runtime_call(fn_name, import_symbols)', helper_text)
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
        shell_text = CORE_EXPR_SHELL_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        named_text = CORE_NAMED_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        attr_text = CORE_ATTR_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        callee_text = CORE_CALLEE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn(
            "class _ShExprCallAnnotationMixin(\n    _ShExprNamedCallAnnotationMixin,\n    _ShExprAttrCallAnnotationMixin,\n    _ShExprCalleeCallAnnotationMixin,\n):",
            annotation_text,
        )
        self.assertIn("class _ShExprCalleeCallAnnotationMixin:", callee_text)
        self.assertIn("def _apply_named_callee_call_annotation(", callee_text)
        self.assertIn("def _apply_callee_call_annotation(", callee_text)
        self.assertIn("def _resolve_callee_call_annotation_kind(", callee_text)
        self.assertIn("def _resolve_callee_call_annotation_state(", callee_text)
        self.assertIn("def _annotate_callee_call_expr(", callee_text)
        self.assertIn("def _resolve_call_expr_annotation_state(", annotation_text)
        self.assertIn("def _annotate_call_expr(", annotation_text)
        self.assertIn("return self._annotate_named_call_expr(", callee_text)
        self.assertIn("return self._apply_named_callee_call_annotation(", callee_text)
        self.assertIn("return self._apply_attr_callee_call_annotation(", callee_text)
        self.assertIn("return self._apply_call_expr_annotation(", annotation_text)
        self.assertIn("from toolchain.compile.core_expr_call_annotation import _ShExprCallAnnotationMixin", shell_text)
        self.assertIn("_ShExprCallAnnotationMixin", shell_text)
        self.assertIn(
            "from toolchain.compile.core_expr_named_call_annotation import _ShExprNamedCallAnnotationMixin",
            annotation_text,
        )
        self.assertIn(
            "from toolchain.compile.core_expr_attr_call_annotation import _ShExprAttrCallAnnotationMixin",
            annotation_text,
        )
        self.assertIn(
            "from toolchain.compile.core_expr_callee_call_annotation import _ShExprCalleeCallAnnotationMixin",
            annotation_text,
        )
        self.assertIn("class _ShExprNamedCallAnnotationMixin:", named_text)
        self.assertIn("def _resolve_named_call_dispatch(", named_text)
        self.assertIn("def _annotate_named_call_expr(", named_text)
        self.assertIn("def _annotate_builtin_named_call_expr(", named_text)
        self.assertIn("def _annotate_runtime_named_call_expr(", named_text)
        self.assertIn("class _ShExprAttrCallAnnotationMixin:", attr_text)
        self.assertNotIn("def _apply_named_callee_call_annotation(", core_text)
        self.assertNotIn("def _apply_callee_call_annotation(", core_text)
        self.assertNotIn("def _resolve_callee_call_annotation_kind(", core_text)
        self.assertNotIn("def _resolve_call_expr_annotation_state(", core_text)
        self.assertNotIn("def _annotate_call_expr(", core_text)

    def test_core_source_routes_builtin_named_call_annotations_through_parser_helper(self) -> None:
        text = CORE_NAMED_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        shell_text = CORE_EXPR_SHELL_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_NAMED_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
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
        postfix_text = shell_text.split("def _parse_postfix", 1)[1].split("def _make_bin", 1)[0]

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
        self.assertIn("return _sh_infer_enumerate_item_type(", iter_state_text)
        self.assertIn("infer_item_type=_sh_infer_item_type", iter_state_text)
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
        self.assertNotIn("def _apply_named_call_dispatch(", core_text)
        self.assertNotIn('if fn_name in {"print", "len", "range", "zip", "str"}:', postfix_text)
        self.assertNotIn('if fn_name == "bool" and len(args) == 1:', postfix_text)
        self.assertNotIn("elem_t = _sh_infer_enumerate_item_type(args)", postfix_text)

    def test_core_source_routes_runtime_named_call_annotations_through_parser_helper(self) -> None:
        text = CORE_NAMED_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        shell_text = CORE_EXPR_SHELL_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_NAMED_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
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
        postfix_text = shell_text.split("def _parse_postfix", 1)[1].split("def _make_bin", 1)[0]

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
        self.assertNotIn("def _apply_runtime_named_call_dispatch(", core_text)
        self.assertNotIn('_sh_lookup_named_call_dispatch(fn_name)', postfix_text)
        self.assertNotIn('if dispatch_kind == "stdlib_function":', postfix_text)
        self.assertNotIn('if dispatch_kind == "stdlib_symbol":', postfix_text)
        self.assertNotIn('if dispatch_kind == "noncpp_symbol":', postfix_text)

    def test_core_source_routes_known_name_call_returns_through_shared_helper(self) -> None:
        runtime_text = CORE_RUNTIME_CALL_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")
        shell_text = CORE_EXPR_SHELL_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = runtime_text.split("def _sh_infer_known_name_call_return_type", 1)[1].split(
            "def _sh_infer_enumerate_item_type",
            1,
        )[0]
        postfix_text = shell_text.split("def _parse_postfix", 1)[1].split("def _make_bin", 1)[0]

        self.assertIn('if fn_name == "print":', helper_text)
        self.assertIn('if stdlib_imported_ret != "":', helper_text)
        self.assertIn('if fn_name == "open":', helper_text)
        self.assertIn('if fn_name == "zip":', helper_text)
        self.assertIn("zip_item_types.append(infer_item_type(arg_node))", helper_text)
        self.assertIn('return "dict[unknown,unknown]"', helper_text)
        self.assertNotIn("_sh_infer_known_name_call_return_type(", postfix_text)
        self.assertNotIn('if fn_name == "print":\n                        call_ret = "None"', postfix_text)
        self.assertNotIn('elif fn_name == "open":\n                        call_ret = "PyFile"', postfix_text)
        self.assertNotIn('elif fn_name == "zip":', postfix_text)
        self.assertNotIn('call_ret = "dict[unknown,unknown]"', postfix_text)

    def test_core_source_routes_enumerate_item_type_through_shared_helper(self) -> None:
        runtime_text = CORE_RUNTIME_CALL_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")
        text = CORE_NAMED_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        shell_text = CORE_EXPR_SHELL_SOURCE_PATH.read_text(encoding="utf-8")
        self.assertEqual(runtime_text.count("def _sh_infer_enumerate_item_type"), 1)
        helper_text = runtime_text.split("def _sh_infer_enumerate_item_type", 1)[1]
        state_text = text.split("def _resolve_builtin_named_call_annotation_state", 1)[1].split(
            "def _apply_builtin_named_call_dispatch",
            1,
        )[0]
        postfix_text = shell_text.split("def _parse_postfix", 1)[1].split("def _make_bin", 1)[0]

        self.assertIn("if len(args) < 1:", helper_text)
        self.assertIn("arg0 = args[0]", helper_text)
        self.assertIn("return infer_item_type(arg0)", helper_text)
        self.assertIn("return _sh_infer_enumerate_item_type(", state_text)
        self.assertIn("infer_item_type=_sh_infer_item_type", state_text)
        self.assertNotIn('if len(args) >= 1 and isinstance(args[0], dict):', postfix_text)
        self.assertNotIn('elem_t = self._iter_item_type(args[0])', postfix_text)

    def test_core_source_routes_attr_call_returns_through_shared_helper(self) -> None:
        shell_text = CORE_EXPR_SHELL_SOURCE_PATH.read_text(encoding="utf-8")
        callee_text = CORE_CALLEE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = callee_text.split("def _infer_attr_call_return_type", 1)[1].split(
            "def _infer_call_expr_return_type",
            1,
        )[0]
        postfix_text = shell_text.split("def _parse_postfix", 1)[1].split("def _make_bin", 1)[0]

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
        text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        shell_text = CORE_EXPR_SHELL_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        callee_text = CORE_CALLEE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        resolution_text = CORE_EXPR_RESOLUTION_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")
        named_decl_text = resolution_text.split("def _resolve_named_call_declared_return_type", 1)[1].split(
            "def _resolve_named_call_return_state",
            1,
        )[0]
        named_state_text = resolution_text.split("def _resolve_named_call_return_state", 1)[1].split(
            "def _infer_named_call_return_type",
            1,
        )[0]
        named_helper_text = resolution_text.split("def _infer_named_call_return_type", 1)[1].split(
            "def _lookup_attr_expr_metadata",
            1,
        )[0]
        helper_text = callee_text.split("def _infer_call_expr_return_type", 1)[1].split(
            "def _apply_named_callee_call_annotation",
            1,
        )[0]
        build_text = text.split("def _build_call_expr_payload", 1)[1].split(
            "def _apply_call_expr_annotation",
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
        call_helper_text = annotation_text.split("def _annotate_call_expr", 1)[1]
        postfix_text = shell_text.split("def _parse_postfix", 1)[1].split("def _make_bin", 1)[0]

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
        self.assertIn("from toolchain.compile.core_expr_call_annotation import _ShExprCallAnnotationMixin", shell_text)
        self.assertIn("class _ShExprCalleeCallAnnotationMixin:", callee_text)
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
        shell_text = CORE_EXPR_SHELL_SOURCE_PATH.read_text(encoding="utf-8")
        postfix_text = shell_text.split("def _parse_postfix", 1)[1].split("def _make_bin", 1)[0]

        self.assertIn("class _ShExprCallArgParserMixin:", text)
        self.assertIn("def _dict_stmt_list(", text)
        self.assertIn("def _node_kind_from_dict(", text)
        self.assertIn("def _iter_item_type(", text)
        self.assertIn("def _parse_name_comp_target(", text)
        self.assertIn("def _parse_tuple_comp_target(", text)
        self.assertIn("def _parse_comp_target(", text)
        self.assertIn("def _parse_call_arg_expr(", text)
        self.assertIn("def _collect_and_bind_comp_target_types(", text)
        self.assertIn("def _restore_comp_target_types(", text)
        self.assertIn("def _parse_call_args(", text)
        self.assertIn("def _consume_call_arg_entries(", text)
        self.assertIn("def _consume_call_arg_entries_loop(", text)
        self.assertIn("def _consume_call_arg_loop_entry(", text)
        self.assertIn("def _parse_call_arg_entry(", text)
        self.assertIn("def _resolve_call_arg_entry_state(", text)
        self.assertIn("def _apply_call_arg_entry_state(", text)
        self.assertIn("def _apply_call_arg_entry(", text)
        self.assertIn("def _advance_call_arg_loop(", text)
        self.assertIn("def _resolve_call_args_empty_state(", text)
        self.assertIn("def _apply_call_arg_entries_result_state(", text)
        self.assertIn("if self._resolve_call_args_empty_state():", text)
        self.assertIn("return self._consume_call_arg_entries(", text)
        self.assertIn("arg_entry, keyword_entry = self._resolve_call_arg_loop_entry_state()", text)
        self.assertIn("return self._apply_call_arg_loop_entry_state(", text)
        self.assertIn("from toolchain.compile.core_expr_call_args import _ShExprCallArgParserMixin", shell_text)
        self.assertIn("from toolchain.compile.core_expr_call_suffix import _ShExprCallSuffixParserMixin", shell_text)
        self.assertIn(
            "from toolchain.compile.core_expr_attr_subscript_suffix import _ShExprPostfixSuffixParserMixin",
            shell_text,
        )
        self.assertIn(
            "from toolchain.compile.core_expr_attr_suffix import _ShExprAttrSuffixParserMixin",
            shell_text,
        )
        self.assertIn(
            "from toolchain.compile.core_expr_subscript_suffix import _ShExprSubscriptSuffixParserMixin",
            shell_text,
        )
        self.assertIn("class _ShExprParser(", shell_text)
        self.assertIn("next_node = self._parse_postfix_suffix(owner_expr=node)", postfix_text)
        self.assertNotIn("def _parse_call_args(", core_text)
        self.assertNotIn("def _consume_call_arg_entries(", core_text)
        self.assertNotIn("def _consume_call_arg_entries_loop(", core_text)
        self.assertNotIn("def _consume_call_arg_loop_entry(", core_text)
        self.assertNotIn("def _parse_call_arg_entry(", core_text)
        self.assertNotIn("def _resolve_call_arg_entry_state(", core_text)
        self.assertNotIn("def _apply_call_arg_entry_state(", core_text)
        self.assertNotIn("def _apply_call_arg_entry(", core_text)
        self.assertNotIn("def _advance_call_arg_loop(", core_text)
        self.assertNotIn("def _dict_stmt_list(", core_text)
        self.assertNotIn("def _node_kind_from_dict(", core_text)
        self.assertNotIn("def _iter_item_type(", core_text)
        self.assertNotIn("def _parse_name_comp_target(", core_text)
        self.assertNotIn("def _parse_tuple_comp_target(", core_text)
        self.assertNotIn("def _parse_comp_target(", core_text)
        self.assertNotIn("def _parse_call_arg_expr(", core_text)
        self.assertNotIn("def _collect_and_bind_comp_target_types(", core_text)
        self.assertNotIn("def _restore_comp_target_types(", core_text)

    def test_core_source_routes_call_suffix_through_parser_helper(self) -> None:
        text = CORE_CALL_SUFFIX_SOURCE_PATH.read_text(encoding="utf-8")
        suffix_text = CORE_ATTR_SUBSCRIPT_SUFFIX_SOURCE_PATH.read_text(encoding="utf-8")
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        shell_text = CORE_EXPR_SHELL_SOURCE_PATH.read_text(encoding="utf-8")
        postfix_suffix_apply_text = suffix_text.split("def _apply_postfix_suffix_kind", 1)[1].split(
            "def _parse_postfix_suffix",
            1,
        )[0]
        postfix_text = shell_text.split("def _parse_postfix", 1)[1].split("def _make_bin", 1)[0]

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
        self.assertIn("from toolchain.compile.core_expr_call_suffix import _ShExprCallSuffixParserMixin", shell_text)
        self.assertIn(
            "from toolchain.compile.core_expr_attr_subscript_suffix import _ShExprPostfixSuffixParserMixin",
            shell_text,
        )
        self.assertIn(
            "from toolchain.compile.core_expr_attr_suffix import _ShExprAttrSuffixParserMixin",
            shell_text,
        )
        self.assertIn(
            "from toolchain.compile.core_expr_subscript_suffix import _ShExprSubscriptSuffixParserMixin",
            shell_text,
        )
        self.assertIn("class _ShExprParser(", shell_text)
        self.assertIn('if tok_kind == "(":', postfix_suffix_apply_text)
        self.assertIn("return self._parse_call_suffix(callee=owner_expr)", postfix_suffix_apply_text)
        self.assertIn("next_node = self._parse_postfix_suffix(owner_expr=node)", postfix_text)
        self.assertNotIn("def _resolve_call_suffix_state(", core_text)
        self.assertNotIn("def _consume_call_suffix_tokens(", core_text)
        self.assertNotIn("def _parse_call_suffix(", core_text)

    def test_core_source_routes_postfix_suffix_dispatch_through_parser_helper(self) -> None:
        text = CORE_ATTR_SUBSCRIPT_SUFFIX_SOURCE_PATH.read_text(encoding="utf-8")
        shell_text = CORE_EXPR_SHELL_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = text.split("def _apply_postfix_suffix_kind", 1)[1].split(
            "def _parse_postfix_suffix",
            1,
        )[0]
        postfix_text = shell_text.split("def _parse_postfix", 1)[1].split("def _make_bin", 1)[0]

        self.assertIn('if tok_kind == ".":', helper_text)
        self.assertIn('if tok_kind == "(":', helper_text)
        self.assertIn('if tok_kind == "[":', helper_text)
        self.assertIn("class _ShExprPostfixSuffixParserMixin:", text)
        self.assertIn("return None", helper_text)
        self.assertIn('tok_kind = str(self._cur()["k"])', text.split("def _parse_postfix_suffix", 1)[1].split("def _apply_postfix_suffix_kind", 1)[0])
        self.assertIn("return self._apply_postfix_suffix_kind(", text.split("def _parse_postfix_suffix", 1)[1].split("def _apply_postfix_suffix_kind", 1)[0])
        self.assertIn("next_node = self._parse_postfix_suffix(owner_expr=node)", postfix_text)
        self.assertIn("if next_node is None:", postfix_text)
        self.assertNotIn('tok = self._cur()', postfix_text)
        self.assertNotIn('if tok["k"] == "."', postfix_text)
        self.assertNotIn('if tok["k"] == "("', postfix_text)
        self.assertNotIn('if tok["k"] == "["', postfix_text)
