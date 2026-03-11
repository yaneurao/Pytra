"""Source-contract regressions for EAST core expression suffix and annotation clusters."""

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
from _east_core_test_support import CORE_AST_BUILDERS_SOURCE_PATH
from _east_core_test_support import CORE_BUILDER_BASE_SOURCE_PATH
from _east_core_test_support import CORE_CALL_ANNOTATION_SOURCE_PATH
from _east_core_test_support import CORE_EXPR_RESOLUTION_SEMANTICS_SOURCE_PATH
from _east_core_test_support import CORE_RUNTIME_CALL_SEMANTICS_SOURCE_PATH
from _east_core_test_support import CORE_SOURCE_PATH


class EastCoreSourceContractExprSuffixTest(unittest.TestCase):
    def test_core_source_uses_builder_helpers_for_lowered_residual_call_dict_tuple_clusters(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        builder_text = CORE_AST_BUILDERS_SOURCE_PATH.read_text(encoding="utf-8")
        lowered_text = text.split("def _sh_parse_expr_lowered", 1)[1].split(
            "def _sh_parse_stmt_block_mutable",
            1,
        )[0]

        self.assertIn("def _sh_make_builtin_listcomp_call_expr(", builder_text)
        self.assertIn("_sh_make_builtin_listcomp_call_expr(", lowered_text)
        self.assertIn("return _sh_make_dict_expr(", lowered_text)
        self.assertIn("return _sh_make_tuple_expr(", lowered_text)

        self.assertNotIn('return {"kind": "Call"', lowered_text)
        self.assertNotIn('return {"kind": "Dict"', lowered_text)
        self.assertNotIn('return {"kind": "Tuple"', lowered_text)

    def test_core_source_uses_builder_helpers_for_lowered_any_all_and_simple_listcomp_clusters(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        builder_text = CORE_AST_BUILDERS_SOURCE_PATH.read_text(encoding="utf-8")
        lowered_text = text.split("def _sh_parse_expr_lowered", 1)[1].split(
            "def _sh_parse_stmt_block_mutable",
            1,
        )[0]

        self.assertIn("def _sh_make_builtin_listcomp_call_expr(", builder_text)
        self.assertIn("_sh_make_builtin_listcomp_call_expr(", lowered_text)
        self.assertIn("payload = _sh_make_call_expr(", builder_text)
        self.assertIn('_sh_make_name_expr(', builder_text)
        self.assertIn("def _sh_make_simple_name_list_comp_expr(", builder_text)
        self.assertIn("_sh_make_simple_name_list_comp_expr(", lowered_text)
        self.assertIn("def _sh_make_simple_name_comp_generator(", builder_text)
        self.assertIn("_sh_make_simple_name_comp_generator(", builder_text)
        self.assertIn("elt_node = _sh_make_name_expr(", builder_text)
        self.assertNotIn("target_node = _sh_make_name_expr(", text)
        self.assertIn('resolved_type=f"list[{elem_type}]"', builder_text)
        self.assertNotIn('return dict<str, object>{{"kind", make_object("Call")}', lowered_text)
        self.assertNotIn('dict<str, object>{{"kind", make_object("Name")}', lowered_text)

    def test_core_source_routes_runtime_call_metadata_through_shared_helper(self) -> None:
        runtime_text = CORE_RUNTIME_CALL_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")
        text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = runtime_text.split("def _sh_annotate_runtime_call_expr", 1)[1].split(
            "def _sh_annotate_resolved_runtime_expr",
            1,
        )[0]
        named_call_text = annotation_text.split("def _annotate_named_call_expr", 1)[1].split(
            "def _annotate_builtin_named_call_expr",
            1,
        )[0]
        runtime_method_apply_text = text.split("def _apply_runtime_method_call_expr_annotation", 1)[1].split(
            "def _apply_attr_call_expr_annotation",
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

        self.assertIn('_set_runtime_binding_fields(payload, module_id, runtime_symbol)', helper_text)
        self.assertIn('payload["runtime_owner"] = runtime_owner', helper_text)
        self.assertIn("return self._apply_named_call_dispatch(", named_call_text)
        self.assertIn("_sh_annotate_runtime_method_call_expr(", runtime_method_apply_text)
        self.assertIn("self._apply_runtime_method_call_expr_annotation(", attr_call_apply_text)
        self.assertIn("return self._apply_attr_call_expr_annotation(", attr_call_text)
        self.assertIn("def _annotate_builtin_named_call_expr(", annotation_text)
        self.assertNotIn('payload["lowered_kind"] = "BuiltinCall"', postfix_text)
        self.assertNotIn('payload["lowered_kind"] = "TypePredicateCall"', postfix_text)
        self.assertNotIn('payload["builtin_name"] = "print"', postfix_text)
        self.assertNotIn('payload["runtime_call"] = "py_print"', postfix_text)
        self.assertNotIn('payload["runtime_call"] = "py_range"', postfix_text)
        self.assertNotIn("def _apply_runtime_method_call_expr_annotation(", core_text)
        self.assertNotIn("def _apply_attr_call_expr_annotation(", core_text)

    def test_core_source_routes_resolved_runtime_annotations_through_shared_helper(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        runtime_text = CORE_RUNTIME_CALL_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")
        attr_annotation_text = CORE_ATTR_SUBSCRIPT_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = runtime_text.split("def _sh_annotate_resolved_runtime_expr", 1)[1].split(
            "def _sh_annotate_runtime_attr_expr",
            1,
        )[0]
        noncpp_apply_text = attr_annotation_text.split("def _apply_noncpp_attr_expr_annotation", 1)[1].split(
            "def _resolve_subscript_expr_annotation_state",
            1,
        )[0]
        apply_text = attr_annotation_text.split("def _apply_attr_expr_annotation", 1)[1].split(
            "def _annotate_attr_expr",
            1,
        )[0]
        attr_expr_text = attr_annotation_text.split("def _annotate_attr_expr", 1)[1].split(
            "def _resolve_attr_expr_annotation",
            1,
        )[0]
        postfix_text = core_text.split("def _parse_postfix", 1)[1].split("def _parse_primary", 1)[0]

        self.assertIn('_set_runtime_binding_fields(payload, module_id, runtime_symbol)', helper_text)
        self.assertIn('_sh_annotate_resolved_runtime_expr(', noncpp_apply_text)
        self.assertIn("self._apply_noncpp_attr_expr_annotation(", apply_text)
        self.assertIn("return self._apply_attr_expr_annotation(", attr_expr_text)
        self.assertNotIn('payload["resolved_runtime_call"] = noncpp_symbol_runtime_call', postfix_text)
        self.assertNotIn('payload["resolved_runtime_source"] = "import_symbol"', postfix_text)
        self.assertNotIn('payload["resolved_runtime_call"] = noncpp_module_runtime_call', postfix_text)
        self.assertNotIn('payload["resolved_runtime_source"] = "module_attr"', postfix_text)
        self.assertNotIn('node["resolved_runtime_call"] = noncpp_module_attr_runtime_call', postfix_text)
        self.assertNotIn('node["resolved_runtime_source"] = "module_attr"', postfix_text)

    def test_core_source_routes_builtin_attr_metadata_through_shared_helper(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        runtime_text = CORE_RUNTIME_CALL_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")
        attr_annotation_text = CORE_ATTR_SUBSCRIPT_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = runtime_text.split("def _sh_annotate_runtime_attr_expr", 1)[1].split(
            "def _sh_annotate_runtime_method_call_expr",
            1,
        )[0]
        runtime_apply_text = attr_annotation_text.split("def _apply_runtime_attr_expr_annotation", 1)[1].split(
            "def _apply_runtime_call_attr_expr_annotation",
            1,
        )[0]
        apply_text = attr_annotation_text.split("def _apply_attr_expr_annotation", 1)[1].split(
            "def _annotate_attr_expr",
            1,
        )[0]
        attr_expr_text = attr_annotation_text.split("def _annotate_attr_expr", 1)[1].split(
            "def _resolve_attr_expr_annotation",
            1,
        )[0]
        postfix_text = core_text.split("def _parse_postfix", 1)[1].split("def _parse_primary", 1)[0]

        self.assertIn('_set_runtime_binding_fields(payload, module_id, runtime_symbol)', helper_text)
        self.assertIn('payload["runtime_owner"] = runtime_owner', helper_text)
        self.assertIn("if self._apply_runtime_call_attr_expr_annotation(", runtime_apply_text)
        self.assertIn("self._apply_runtime_semantic_attr_expr_annotation(", runtime_apply_text)
        self.assertIn("self._apply_runtime_attr_expr_annotation(", apply_text)
        self.assertIn("return self._apply_attr_expr_annotation(", attr_expr_text)
        self.assertNotIn('node["lowered_kind"] = "BuiltinAttr"', postfix_text)
        self.assertNotIn('node["runtime_call"] = attr_runtime_call', postfix_text)

    def test_core_source_routes_attr_lookup_through_shared_helper(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        suffix_text = CORE_ATTR_SUBSCRIPT_SUFFIX_SOURCE_PATH.read_text(encoding="utf-8")
        attr_annotation_text = CORE_ATTR_SUBSCRIPT_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        resolution_text = CORE_EXPR_RESOLUTION_SEMANTICS_SOURCE_PATH.read_text(encoding="utf-8")
        helper_text = resolution_text.split("def _lookup_attr_expr_metadata", 1)[1].split(
            "def _split_generic_types",
            1,
        )[0]
        postfix_suffix_text = suffix_text.split("def _parse_postfix_suffix", 1)[1].split(
            "def _apply_postfix_suffix_kind",
            1,
        )[0]
        postfix_suffix_apply_text = suffix_text.split("def _apply_postfix_suffix_kind", 1)[1].split(
            "def _parse_postfix_suffix",
            1,
        )[0]
        attr_suffix_text = suffix_text.split("def _parse_attr_suffix", 1)[1].split(
            "def _apply_attr_suffix_state",
            1,
        )[0]
        attr_expr_text = attr_annotation_text.split("def _annotate_attr_expr", 1)[1].split(
            "def _resolve_attr_expr_annotation",
            1,
        )[0]
        postfix_text = core_text.split("def _parse_postfix", 1)[1].split("def _parse_comp_target", 1)[0]

        self.assertIn('std_attr_t = lookup_stdlib_attribute_type(owner_type, attr_name)', helper_text)
        self.assertIn('runtime_call = lookup_stdlib_method_runtime_call(owner_type, attr_name)', helper_text)
        self.assertIn('module_id, runtime_symbol = lookup_stdlib_method_runtime_binding(owner_type, attr_name)', helper_text)
        self.assertIn('_sh_lookup_noncpp_attr_runtime_call(', helper_text)
        self.assertIn('import_modules=_SH_IMPORT_MODULES', helper_text)
        self.assertIn('import_symbols=_SH_IMPORT_SYMBOLS', helper_text)
        self.assertIn("self._resolve_attr_expr_annotation_state(", attr_expr_text)
        self.assertNotIn("self._resolve_attr_expr_metadata(", attr_expr_text)
        self.assertNotIn("attr_meta = self._lookup_attr_expr_metadata(", attr_expr_text)
        self.assertIn("return self._apply_attr_suffix_state(", attr_suffix_text)
        self.assertIn("return self._apply_postfix_suffix_kind(", postfix_suffix_text)
        self.assertIn("return self._parse_attr_suffix(owner_expr=owner_expr)", postfix_suffix_apply_text)
        self.assertIn("next_node = self._parse_postfix_suffix(owner_expr=node)", postfix_text)
        self.assertNotIn('std_attr_t = lookup_stdlib_attribute_type(owner_t, attr_name)', postfix_text)
        self.assertNotIn('attr_runtime_call = lookup_stdlib_method_runtime_call(owner_t, attr_name)', postfix_text)
        self.assertNotIn('mod_id, runtime_symbol = lookup_stdlib_method_runtime_binding(owner_t, attr_name)', postfix_text)
        self.assertNotIn('_sh_lookup_noncpp_attr_runtime_call(owner_expr, attr_name)', postfix_text)

    def test_core_source_routes_attr_annotations_through_parser_helper(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        attr_annotation_text = CORE_ATTR_SUBSCRIPT_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        suffix_text = CORE_ATTR_SUBSCRIPT_SUFFIX_SOURCE_PATH.read_text(encoding="utf-8")
        owner_type_text = annotation_text.split("def _owner_expr_resolved_type", 1)[1].split(
            "def _resolve_attr_callee_attr_name",
            1,
        )[0]
        owner_state_text = annotation_text.split("def _resolve_attr_expr_owner_state", 1)[1].split(
            "def _resolve_attr_callee",
            1,
        )[0]
        resolve_text = attr_annotation_text.split("def _resolve_attr_expr_annotation", 1)[1].split(
            "def _resolve_attr_expr_metadata",
            1,
        )[0]
        metadata_text = attr_annotation_text.split("def _resolve_attr_expr_metadata", 1)[1].split(
            "def _resolve_attr_expr_annotation_state",
            1,
        )[0]
        state_text = attr_annotation_text.split("def _resolve_attr_expr_annotation_state", 1)[1].split(
            "def _resolve_subscript_expr_annotation_state",
            1,
        )[0]
        build_text = attr_annotation_text.split("def _build_attr_expr_payload", 1)[1].split(
            "def _apply_runtime_attr_expr_annotation",
            1,
        )[0]
        runtime_apply_text = attr_annotation_text.split("def _apply_runtime_attr_expr_annotation", 1)[1].split(
            "def _apply_runtime_call_attr_expr_annotation",
            1,
        )[0]
        runtime_call_apply_text = attr_annotation_text.split("def _apply_runtime_call_attr_expr_annotation", 1)[1].split(
            "def _apply_runtime_semantic_attr_expr_annotation",
            1,
        )[0]
        runtime_semantic_apply_text = attr_annotation_text.split("def _apply_runtime_semantic_attr_expr_annotation", 1)[1].split(
            "def _apply_noncpp_attr_expr_annotation",
            1,
        )[0]
        noncpp_apply_text = attr_annotation_text.split("def _apply_noncpp_attr_expr_annotation", 1)[1].split(
            "def _apply_attr_expr_annotation",
            1,
        )[0]
        apply_text = attr_annotation_text.split("def _apply_attr_expr_annotation", 1)[1].split(
            "def _annotate_attr_expr",
            1,
        )[0]
        helper_text = attr_annotation_text.split("def _annotate_attr_expr", 1)[1].split(
            "def _resolve_attr_expr_annotation",
            1,
        )[0]
        postfix_suffix_text = suffix_text.split("def _parse_postfix_suffix", 1)[1].split(
            "def _apply_postfix_suffix_kind",
            1,
        )[0]
        postfix_suffix_apply_text = suffix_text.split("def _apply_postfix_suffix_kind", 1)[1].split(
            "def _parse_postfix_suffix",
            1,
        )[0]
        postfix_text = text.split("def _parse_postfix", 1)[1].split("def _parse_comp_target", 1)[0]

        self.assertIn('resolved_type = str(attr_meta.get("resolved_type", "unknown"))', resolve_text)
        self.assertIn('attr_runtime_call = str(attr_meta.get("runtime_call", ""))', resolve_text)
        self.assertIn('attr_semantic_tag = str(attr_meta.get("semantic_tag", ""))', resolve_text)
        self.assertIn('attr_module_id = str(attr_meta.get("module_id", ""))', resolve_text)
        self.assertIn('attr_runtime_symbol = str(attr_meta.get("runtime_symbol", ""))', resolve_text)
        self.assertIn('noncpp_module_attr_runtime_call = str(attr_meta.get("noncpp_runtime_call", ""))', resolve_text)
        self.assertIn('noncpp_module_id = str(attr_meta.get("noncpp_module_id", ""))', resolve_text)
        self.assertIn('owner_t = str(owner_expr.get("resolved_type", "unknown"))', owner_type_text)
        self.assertIn('owner_t = self.name_types.get(str(owner_expr.get("id", "")), owner_t)', owner_type_text)
        self.assertIn("return owner_t", owner_type_text)
        self.assertIn("owner_t = self._owner_expr_resolved_type(owner_expr)", owner_state_text)
        self.assertIn("self._guard_dynamic_helper_receiver(", owner_state_text)
        self.assertIn("if self._is_forbidden_object_receiver_type(owner_t):", owner_state_text)
        self.assertIn("attr_meta = self._lookup_attr_expr_metadata(owner_expr, owner_t, attr_name)", metadata_text)
        self.assertIn("return self._resolve_attr_expr_annotation(", metadata_text)
        self.assertIn("owner_t = self._resolve_attr_expr_owner_state(", state_text)
        self.assertIn(") = self._resolve_attr_expr_metadata(", state_text)
        self.assertNotIn("return (\n            owner_t,", state_text)
        self.assertIn(
            "from toolchain.ir.core_expr_attr_subscript_annotation import _ShExprAttrSubscriptAnnotationMixin",
            text,
        )
        self.assertIn("node = _sh_make_attribute_expr(", build_text)
        self.assertIn("return node", build_text)
        self.assertIn("if self._apply_runtime_call_attr_expr_annotation(", runtime_apply_text)
        self.assertIn("self._apply_runtime_semantic_attr_expr_annotation(", runtime_apply_text)
        self.assertIn('if attr_runtime_call == "":', runtime_call_apply_text)
        self.assertIn('_sh_annotate_runtime_attr_expr(', runtime_call_apply_text)
        self.assertIn("return True", runtime_call_apply_text)
        self.assertIn('if attr_semantic_tag != "":', runtime_semantic_apply_text)
        self.assertIn('node["semantic_tag"] = attr_semantic_tag', runtime_semantic_apply_text)
        self.assertIn('_sh_annotate_resolved_runtime_expr(', noncpp_apply_text)
        self.assertIn("self._apply_runtime_attr_expr_annotation(", apply_text)
        self.assertIn("self._apply_noncpp_attr_expr_annotation(", apply_text)
        self.assertIn(") = self._resolve_attr_expr_annotation_state(", helper_text)
        self.assertNotIn("owner_t,", helper_text)
        self.assertIn("node = self._build_attr_expr_payload(", helper_text)
        self.assertIn("return self._apply_attr_expr_annotation(", helper_text)
        self.assertNotIn("owner_t = self._resolve_attr_expr_owner_state(", helper_text)
        self.assertNotIn("self._resolve_attr_expr_metadata(", helper_text)
        self.assertNotIn("_sh_make_attribute_expr(", helper_text)
        self.assertNotIn("def _resolve_attr_expr_annotation(", text)
        self.assertNotIn("def _resolve_attr_expr_metadata(", text)
        self.assertNotIn("def _resolve_attr_expr_annotation_state(", text)
        self.assertNotIn("def _build_attr_expr_payload(", text)
        self.assertNotIn("def _apply_runtime_attr_expr_annotation(", text)
        self.assertNotIn("def _apply_runtime_call_attr_expr_annotation(", text)
        self.assertNotIn("def _apply_runtime_semantic_attr_expr_annotation(", text)
        self.assertNotIn("def _apply_noncpp_attr_expr_annotation(", text)
        self.assertNotIn("def _apply_attr_expr_annotation(", text)
        self.assertNotIn("def _annotate_attr_expr(", text)
        self.assertNotIn('_sh_annotate_runtime_attr_expr(', apply_text)
        self.assertNotIn('_sh_annotate_resolved_runtime_expr(', apply_text)
        self.assertNotIn('_sh_annotate_runtime_attr_expr(', helper_text)
        self.assertNotIn('_sh_annotate_runtime_attr_expr(', runtime_apply_text)
        self.assertNotIn('node["semantic_tag"] = attr_semantic_tag', runtime_apply_text)
        self.assertNotIn('_sh_annotate_resolved_runtime_expr(', helper_text)
        self.assertIn("return self._apply_postfix_suffix_kind(", postfix_suffix_text)
        self.assertIn("return self._parse_attr_suffix(owner_expr=owner_expr)", postfix_suffix_apply_text)
        self.assertIn("next_node = self._parse_postfix_suffix(owner_expr=node)", postfix_text)
        self.assertNotIn('owner_t = str(node.get("resolved_type", "unknown"))', postfix_text)
        self.assertNotIn("attr_meta = self._lookup_attr_expr_metadata(", postfix_text)
        self.assertNotIn("_sh_make_attribute_expr(", postfix_text)
        self.assertNotIn('_sh_annotate_runtime_attr_expr(', postfix_text)
        self.assertNotIn('_sh_annotate_resolved_runtime_expr(', postfix_text)

    def test_core_source_routes_attr_suffix_through_parser_helper(self) -> None:
        text = CORE_ATTR_SUBSCRIPT_SUFFIX_SOURCE_PATH.read_text(encoding="utf-8")
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        postfix_suffix_apply_text = text.split("def _apply_postfix_suffix_kind", 1)[1].split(
            "def _parse_postfix_suffix",
            1,
        )[0]
        postfix_text = core_text.split("def _parse_postfix", 1)[1].split("def _parse_comp_target", 1)[0]

        self.assertIn("class _ShExprAttrSubscriptSuffixParserMixin:", text)
        self.assertIn("def _parse_attr_suffix(", text)
        self.assertIn("def _resolve_attr_suffix_state(", text)
        self.assertIn("def _resolve_attr_suffix_name_token(", text)
        self.assertIn("def _resolve_attr_suffix_name_state(", text)
        self.assertIn("def _resolve_attr_suffix_token_state(", text)
        self.assertIn("def _resolve_attr_suffix_span_repr(", text)
        self.assertIn("return self._annotate_attr_expr(", text)
        self.assertIn("return self._resolve_postfix_span_repr(", text)
        self.assertIn(
            "from toolchain.ir.core_expr_attr_subscript_suffix import _ShExprAttrSubscriptSuffixParserMixin",
            core_text,
        )
        self.assertIn(
            "class _ShExprParser(",
            core_text,
        )
        self.assertIn("return self._parse_attr_suffix(owner_expr=owner_expr)", postfix_suffix_apply_text)
        self.assertIn("next_node = self._parse_postfix_suffix(owner_expr=node)", postfix_text)
        self.assertNotIn("def _parse_attr_suffix(", core_text)
        self.assertNotIn("def _resolve_attr_suffix_state(", core_text)
        self.assertNotIn("def _resolve_attr_suffix_name_token(", core_text)
        self.assertNotIn("def _resolve_attr_suffix_span_repr(", core_text)

    def test_core_source_routes_subscript_annotations_through_parser_helper(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        annotation_text = CORE_CALL_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        attr_annotation_text = CORE_ATTR_SUBSCRIPT_ANNOTATION_SOURCE_PATH.read_text(encoding="utf-8")
        suffix_text = CORE_ATTR_SUBSCRIPT_SUFFIX_SOURCE_PATH.read_text(encoding="utf-8")
        owner_type_text = annotation_text.split("def _owner_expr_resolved_type", 1)[1].split(
            "def _resolve_attr_callee_attr_name",
            1,
        )[0]
        slice_build_text = attr_annotation_text.split("def _build_slice_subscript_expr", 1)[1].split(
            "def _build_index_subscript_expr",
            1,
        )[0]
        index_build_text = attr_annotation_text.split("def _build_index_subscript_expr", 1)[1].split(
            "def _resolve_subscript_expr_annotation_state",
            1,
        )[0]
        state_text = attr_annotation_text.split("def _resolve_subscript_expr_annotation_state", 1)[1].split(
            "def _resolve_subscript_expr_build_kind",
            1,
        )[0]
        build_kind_text = attr_annotation_text.split("def _resolve_subscript_expr_build_kind", 1)[1].split(
            "def _resolve_subscript_expr_apply_state",
            1,
        )[0]
        apply_state_text = attr_annotation_text.split("def _resolve_subscript_expr_apply_state", 1)[1].split(
            "def _apply_slice_subscript_expr_build",
            1,
        )[0]
        slice_apply_text = attr_annotation_text.split("def _apply_slice_subscript_expr_build", 1)[1].split(
            "def _apply_index_subscript_expr_build",
            1,
        )[0]
        index_apply_text = attr_annotation_text.split("def _apply_index_subscript_expr_build", 1)[1].split(
            "def _apply_subscript_expr_build",
            1,
        )[0]
        apply_text = attr_annotation_text.split("def _apply_subscript_expr_build", 1)[1].split(
            "def _subscript_result_type",
            1,
        )[0]
        helper_text = attr_annotation_text.split("def _annotate_subscript_expr", 1)[1].split(
            "def _subscript_result_type",
            1,
        )[0]
        postfix_suffix_text = suffix_text.split("def _parse_postfix_suffix", 1)[1].split(
            "def _apply_postfix_suffix_kind",
            1,
        )[0]
        postfix_suffix_apply_text = suffix_text.split("def _apply_postfix_suffix_kind", 1)[1].split(
            "def _parse_postfix_suffix",
            1,
        )[0]
        postfix_text = text.split("def _parse_postfix", 1)[1].split("def _parse_comp_target", 1)[0]

        self.assertIn('owner_t = str(owner_expr.get("resolved_type", "unknown"))', owner_type_text)
        self.assertIn('owner_t = self.name_types.get(str(owner_expr.get("id", "")), owner_t)', owner_type_text)
        self.assertIn("return owner_t", owner_type_text)
        self.assertIn("_sh_make_slice_node(lower, upper)", slice_build_text)
        self.assertIn("_sh_make_subscript_expr(", slice_build_text)
        self.assertIn('lowered_kind="SliceExpr"', slice_build_text)
        self.assertIn("_sh_make_subscript_expr(", index_build_text)
        self.assertIn("resolved_type=self._subscript_result_type(owner_t)", index_build_text)
        self.assertIn("return self._owner_expr_resolved_type(owner_expr)", state_text)
        self.assertIn("if index_expr is None or lower is not None or upper is not None:", build_kind_text)
        self.assertIn('return "slice"', build_kind_text)
        self.assertIn('return "index"', build_kind_text)
        self.assertIn("owner_t = self._resolve_subscript_expr_annotation_state(", apply_state_text)
        self.assertIn("build_kind = self._resolve_subscript_expr_build_kind(", apply_state_text)
        self.assertIn("return owner_t, build_kind", apply_state_text)
        self.assertIn("return self._build_slice_subscript_expr(", slice_apply_text)
        self.assertIn("return self._build_index_subscript_expr(", index_apply_text)
        self.assertIn('if build_kind == "slice":', apply_text)
        self.assertIn("return self._apply_slice_subscript_expr_build(", apply_text)
        self.assertIn("return self._apply_index_subscript_expr_build(", apply_text)
        self.assertIn("owner_t, build_kind = self._resolve_subscript_expr_apply_state(", helper_text)
        self.assertIn("return self._apply_subscript_expr_build(", helper_text)
        self.assertIn("return self._apply_postfix_suffix_kind(", postfix_suffix_text)
        self.assertIn("return self._parse_subscript_suffix(owner_expr=owner_expr)", postfix_suffix_apply_text)
        self.assertIn("next_node = self._parse_postfix_suffix(owner_expr=node)", postfix_text)
        self.assertIn(
            "from toolchain.ir.core_expr_attr_subscript_annotation import _ShExprAttrSubscriptAnnotationMixin",
            text,
        )
        self.assertNotIn("_sh_make_slice_node(lower, upper)", helper_text)
        self.assertNotIn("_sh_make_subscript_expr(", helper_text)
        self.assertNotIn("owner_t = self._owner_expr_resolved_type(owner_expr)", helper_text)
        self.assertNotIn("owner_t = self._resolve_subscript_expr_annotation_state(", helper_text)
        self.assertNotIn("build_kind = self._resolve_subscript_expr_build_kind(", helper_text)
        self.assertNotIn('if build_kind == "slice":', helper_text)
        self.assertNotIn("return self._build_slice_subscript_expr(", apply_text)
        self.assertNotIn("return self._build_index_subscript_expr(", apply_text)
        self.assertNotIn("def _resolve_subscript_expr_annotation_state(", text)
        self.assertNotIn("def _resolve_subscript_expr_build_kind(", text)
        self.assertNotIn("def _resolve_subscript_expr_apply_state(", text)
        self.assertNotIn("def _build_slice_subscript_expr(", text)
        self.assertNotIn("def _build_index_subscript_expr(", text)
        self.assertNotIn("def _apply_slice_subscript_expr_build(", text)
        self.assertNotIn("def _apply_index_subscript_expr_build(", text)
        self.assertNotIn("def _apply_subscript_expr_build(", text)
        self.assertNotIn("def _annotate_subscript_expr(", text)
        self.assertNotIn("node = _sh_make_subscript_expr(", postfix_text)
        self.assertNotIn("_sh_make_slice_node(", postfix_text)
        self.assertNotIn("out_t = self._subscript_result_type(", postfix_text)

    def test_core_source_routes_subscript_suffix_through_parser_helper(self) -> None:
        text = CORE_ATTR_SUBSCRIPT_SUFFIX_SOURCE_PATH.read_text(encoding="utf-8")
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        slice_tail_text = text.split("def _parse_subscript_slice_tail", 1)[1].split(
            "def _apply_subscript_slice_tail_parse_state",
            1,
        )[0]
        slice_tail_apply_text = text.split("def _apply_subscript_slice_tail_parse_state", 1)[1].split(
            "def _resolve_subscript_slice_tail_state",
            1,
        )[0]
        tail_state_text = text.split("def _resolve_subscript_slice_tail_state", 1)[1].split(
            "def _resolve_subscript_slice_tail_token_state",
            1,
        )[0]
        tail_token_state_text = text.split("def _resolve_subscript_slice_tail_token_state", 1)[1].split(
            "def _apply_subscript_slice_tail_state",
            1,
        )[0]
        tail_state_apply_text = text.split("def _apply_subscript_slice_tail_state", 1)[1].split(
            "def _apply_subscript_slice_tail_state_result",
            1,
        )[0]
        tail_state_result_apply_text = text.split("def _apply_subscript_slice_tail_state_result", 1)[1].split(
            "def _resolve_subscript_slice_upper_expr_state",
            1,
        )[0]
        upper_state_text = text.split("def _resolve_subscript_slice_upper_expr_state", 1)[1].split(
            "def _resolve_subscript_slice_upper_expr_kind",
            1,
        )[0]
        upper_kind_text = text.split("def _resolve_subscript_slice_upper_expr_kind", 1)[1].split(
            "def _parse_subscript_slice_upper_expr",
            1,
        )[0]
        upper_expr_text = text.split("def _parse_subscript_slice_upper_expr", 1)[1].split(
            "def _apply_subscript_slice_upper_expr_state",
            1,
        )[0]
        upper_apply_text = text.split("def _apply_subscript_slice_upper_expr_state", 1)[1].split(
            "def _consume_subscript_slice_tail_colon_token",
            1,
        )[0]
        tail_colon_text = text.split("def _consume_subscript_slice_tail_colon_token", 1)[1].split(
            "def _resolve_subscript_slice_tail_colon_token_state",
            1,
        )[0]
        tail_colon_token_state_text = text.split(
            "def _resolve_subscript_slice_tail_colon_token_state",
            1,
        )[1].split(
            "def _consume_subscript_slice_tail_close_token",
            1,
        )[0]
        tail_close_text = text.split("def _consume_subscript_slice_tail_close_token", 1)[1].split(
            "def _consume_subscript_slice_tail_tokens",
            1,
        )[0]
        tail_token_text = text.split("def _consume_subscript_slice_tail_tokens", 1)[1].split(
            "def _apply_subscript_slice_tail_colon_token_state",
            1,
        )[0]
        tail_colon_token_apply_text = text.split(
            "def _apply_subscript_slice_tail_colon_token_state",
            1,
        )[1].split(
            "def _apply_subscript_slice_tail_colon_state",
            1,
        )[0]
        tail_colon_apply_text = text.split("def _apply_subscript_slice_tail_colon_state", 1)[1].split(
            "def _resolve_subscript_slice_tail_colon_state",
            1,
        )[0]
        tail_colon_state_text = text.split("def _resolve_subscript_slice_tail_colon_state", 1)[1].split(
            "def _apply_subscript_slice_tail_colon_state_result",
            1,
        )[0]
        tail_colon_state_result_text = text.split(
            "def _apply_subscript_slice_tail_colon_state_result", 1
        )[1].split(
            "def _resolve_subscript_slice_tail_upper_state",
            1,
        )[0]
        tail_upper_state_text = text.split("def _resolve_subscript_slice_tail_upper_state", 1)[1].split(
            "def _apply_subscript_slice_tail_upper_state_result",
            1,
        )[0]
        tail_upper_result_apply_text = text.split(
            "def _apply_subscript_slice_tail_upper_state_result", 1
        )[1].split(
            "def _apply_subscript_slice_tail_upper_state",
            1,
        )[0]
        tail_upper_apply_text = text.split("def _apply_subscript_slice_tail_upper_state", 1)[1].split(
            "def _apply_subscript_slice_tail_close_state",
            1,
        )[0]
        tail_close_apply_text = text.split("def _apply_subscript_slice_tail_close_state", 1)[1].split(
            "def _apply_subscript_slice_tail_close_state_result",
            1,
        )[0]
        tail_close_result_apply_text = text.split(
            "def _apply_subscript_slice_tail_close_state_result", 1
        )[1].split(
            "def _resolve_subscript_slice_tail_close_token_state",
            1,
        )[0]
        tail_close_token_state_text = text.split(
            "def _resolve_subscript_slice_tail_close_token_state", 1
        )[1].split(
            "def _apply_subscript_slice_tail_close_token_state",
            1,
        )[0]
        tail_close_token_apply_text = text.split(
            "def _apply_subscript_slice_tail_close_token_state", 1
        )[1].split(
            "def _apply_subscript_slice_tail_close_token_state_result",
            1,
        )[0]
        tail_close_token_result_apply_text = text.split(
            "def _apply_subscript_slice_tail_close_token_state_result", 1
        )[1].split(
            "def _parse_subscript_suffix_components",
            1,
        )[0]
        tail_close_state_text = text.split("def _resolve_subscript_slice_tail_close_state", 1)[1].split(
            "def _resolve_subscript_slice_tail_close_token_state",
            1,
        )[0]
        component_text = text.split("def _parse_subscript_suffix_components", 1)[1].split(
            "def _resolve_subscript_suffix_component_state",
            1,
        )[0]
        component_state_text = text.split("def _resolve_subscript_suffix_component_state", 1)[1].split(
            "def _apply_subscript_suffix_component_state",
            1,
        )[0]
        component_apply_text = text.split("def _apply_subscript_suffix_component_state", 1)[1].split(
            "def _parse_subscript_suffix_first_component",
            1,
        )[0]
        first_component_text = text.split("def _parse_subscript_suffix_first_component", 1)[1].split(
            "def _resolve_subscript_suffix_first_component_state",
            1,
        )[0]
        first_component_state_text = text.split(
            "def _resolve_subscript_suffix_first_component_state", 1
        )[1].split(
            "def _apply_subscript_suffix_first_component_kind_state",
            1,
        )[0]
        first_component_kind_apply_text = text.split(
            "def _apply_subscript_suffix_first_component_kind_state", 1
        )[1].split(
            "def _resolve_subscript_suffix_first_component_kind",
            1,
        )[0]
        first_component_kind_text = text.split(
            "def _resolve_subscript_suffix_first_component_kind", 1
        )[1].split(
            "def _apply_subscript_suffix_first_component_state",
            1,
        )[0]
        first_component_apply_text = text.split(
            "def _apply_subscript_suffix_first_component_state", 1
        )[1].split(
            "def _apply_subscript_slice_first_component",
            1,
        )[0]
        first_component_slice_apply_text = text.split(
            "def _apply_subscript_slice_first_component", 1
        )[1].split(
            "def _apply_subscript_index_first_component",
            1,
        )[0]
        first_component_index_apply_text = text.split(
            "def _apply_subscript_index_first_component", 1
        )[1].split(
            "def _parse_subscript_index_tail",
            1,
        )[0]
        index_tail_text = text.split("def _parse_subscript_index_tail", 1)[1].split(
            "def _resolve_subscript_index_tail_state",
            1,
        )[0]
        index_tail_state_text = text.split("def _resolve_subscript_index_tail_state", 1)[1].split(
            "def _consume_subscript_index_tail_close_token",
            1,
        )[0]
        index_tail_close_text = text.split("def _consume_subscript_index_tail_close_token", 1)[1].split(
            "def _resolve_subscript_suffix_state",
            1,
        )[0]
        state_text = text.split("def _resolve_subscript_suffix_state", 1)[1].split(
            "def _apply_subscript_suffix_token_state",
            1,
        )[0]
        state_apply_text = text.split("def _apply_subscript_suffix_token_state", 1)[1].split(
            "def _apply_subscript_suffix_span_repr_state",
            1,
        )[0]
        subscript_span_apply_text = text.split("def _apply_subscript_suffix_span_repr_state", 1)[1].split(
            "def _resolve_subscript_suffix_span_repr",
            1,
        )[0]
        subscript_span_text = text.split("def _resolve_subscript_suffix_span_repr", 1)[1].split(
            "def _consume_subscript_suffix_open_token",
            1,
        )[0]
        open_token_text = text.split("def _consume_subscript_suffix_open_token", 1)[1].split(
            "def _apply_subscript_suffix_open_token_state",
            1,
        )[0]
        open_state_text = text.split("def _apply_subscript_suffix_open_token_state", 1)[1].split(
            "def _consume_subscript_suffix_tokens",
            1,
        )[0]
        token_text = text.split("def _consume_subscript_suffix_tokens", 1)[1].split(
            "def _resolve_subscript_suffix_token_state",
            1,
        )[0]
        token_state_text = text.split("def _resolve_subscript_suffix_token_state", 1)[1].split(
            "def _parse_subscript_suffix(",
            1,
        )[0]
        helper_text = text.split("def _parse_subscript_suffix(", 1)[1].split(
            "def _apply_subscript_suffix_state",
            1,
        )[0]
        helper_apply_text = text.split("def _apply_subscript_suffix_state", 1)[1].split(
            "def _parse_postfix_suffix",
            1,
        )[0]
        postfix_suffix_text = text.split("def _parse_postfix_suffix", 1)[1].split(
            "def _apply_postfix_suffix_kind",
            1,
        )[0]
        postfix_suffix_apply_text = text.split("def _apply_postfix_suffix_kind", 1)[1].split(
            "def _parse_postfix_suffix",
            1,
        )[0]
        postfix_text = core_text.split("def _parse_postfix", 1)[1].split("def _parse_comp_target", 1)[0]

        self.assertIn("upper, rtok = self._resolve_subscript_slice_tail_state()", slice_tail_text)
        self.assertIn(
            "return self._apply_subscript_slice_tail_parse_state(lower=lower, upper=upper, rtok=rtok)",
            slice_tail_text,
        )
        self.assertIn("return None, lower, upper, rtok", slice_tail_apply_text)
        self.assertIn("upper, rtok = self._resolve_subscript_slice_tail_token_state()", tail_state_text)
        self.assertIn("return self._apply_subscript_slice_tail_state(upper=upper, rtok=rtok)", tail_state_text)
        self.assertIn("return self._consume_subscript_slice_tail_tokens()", tail_token_state_text)
        self.assertIn("return self._apply_subscript_slice_tail_state_result(upper=upper, rtok=rtok)", tail_state_apply_text)
        self.assertIn("return upper, rtok", tail_state_result_apply_text)
        self.assertIn("return self._resolve_subscript_slice_upper_expr_kind()", upper_state_text)
        self.assertIn('return self._cur()["k"] == "]"', upper_kind_text)
        self.assertIn("is_empty = self._resolve_subscript_slice_upper_expr_state()", upper_expr_text)
        self.assertIn("return self._apply_subscript_slice_upper_expr_state(is_empty=is_empty)", upper_expr_text)
        self.assertIn("if is_empty:", upper_apply_text)
        self.assertIn("return None", upper_apply_text)
        self.assertIn("return self._parse_ifexp()", upper_apply_text)
        self.assertIn('return self._eat(":")', tail_colon_text)
        self.assertIn("return self._consume_subscript_slice_tail_colon_token()", tail_colon_token_state_text)
        self.assertIn('return self._eat("]")', tail_close_text)
        self.assertIn("ctok = self._resolve_subscript_slice_tail_colon_token_state()", tail_token_text)
        self.assertIn(
            "return self._apply_subscript_slice_tail_colon_token_state(ctok=ctok)",
            tail_token_text,
        )
        self.assertIn("_ = ctok", tail_colon_token_apply_text)
        self.assertIn("return self._apply_subscript_slice_tail_colon_state()", tail_colon_token_apply_text)
        self.assertIn("upper = self._resolve_subscript_slice_tail_colon_state()", tail_colon_apply_text)
        self.assertIn("return self._apply_subscript_slice_tail_upper_state(upper=upper)", tail_colon_apply_text)
        self.assertIn("upper = self._resolve_subscript_slice_tail_upper_state()", tail_colon_state_text)
        self.assertIn(
            "return self._apply_subscript_slice_tail_colon_state_result(upper=upper)",
            tail_colon_state_text,
        )
        self.assertIn("return upper", tail_colon_state_result_text)
        self.assertIn("upper = self._parse_subscript_slice_upper_expr()", tail_upper_state_text)
        self.assertIn(
            "return self._apply_subscript_slice_tail_upper_state_result(upper=upper)",
            tail_upper_state_text,
        )
        self.assertIn("return upper", tail_upper_result_apply_text)
        self.assertIn("rtok = self._resolve_subscript_slice_tail_close_state()", tail_upper_apply_text)
        self.assertIn("return self._apply_subscript_slice_tail_close_state(upper=upper, rtok=rtok)", tail_upper_apply_text)
        self.assertIn(
            "return self._apply_subscript_slice_tail_close_state_result(upper=upper, rtok=rtok)",
            tail_close_apply_text,
        )
        self.assertIn("return upper, rtok", tail_close_result_apply_text)
        self.assertIn("return self._consume_subscript_slice_tail_close_token()", tail_close_token_state_text)
        self.assertIn(
            "return self._apply_subscript_slice_tail_close_token_state_result(rtok=rtok)",
            tail_close_token_apply_text,
        )
        self.assertIn("return rtok", tail_close_token_result_apply_text)
        self.assertIn("rtok = self._resolve_subscript_slice_tail_close_token_state()", tail_close_state_text)
        self.assertIn("return self._apply_subscript_slice_tail_close_token_state(rtok=rtok)", tail_close_state_text)
        self.assertIn("starts_with_slice = self._resolve_subscript_suffix_component_state()", component_text)
        self.assertIn("return self._apply_subscript_suffix_component_state(", component_text)
        self.assertIn('return self._cur()["k"] == ":"', component_state_text)
        self.assertIn("if starts_with_slice:", component_apply_text)
        self.assertIn("return self._parse_subscript_slice_tail(lower=None)", component_apply_text)
        self.assertIn("return self._parse_subscript_suffix_first_component()", component_apply_text)
        self.assertIn("first, is_slice = self._resolve_subscript_suffix_first_component_state()", first_component_text)
        self.assertIn("return self._apply_subscript_suffix_first_component_state(", first_component_text)
        self.assertIn("first = self._parse_ifexp()", first_component_state_text)
        self.assertIn(
            "return self._apply_subscript_suffix_first_component_kind_state(first=first)",
            first_component_state_text,
        )
        self.assertIn(
            "return first, self._resolve_subscript_suffix_first_component_kind()",
            first_component_kind_apply_text,
        )
        self.assertIn('return self._cur()["k"] == ":"', first_component_kind_text)
        self.assertIn("if is_slice:", first_component_apply_text)
        self.assertIn("return self._apply_subscript_slice_first_component(first=first)", first_component_apply_text)
        self.assertIn("return self._apply_subscript_index_first_component(first=first)", first_component_apply_text)
        self.assertIn(
            "return self._parse_subscript_slice_tail(lower=first)",
            first_component_slice_apply_text,
        )
        self.assertIn(
            "return self._parse_subscript_index_tail(index_expr=first)",
            first_component_index_apply_text,
        )
        self.assertIn("rtok = self._resolve_subscript_index_tail_state()", index_tail_text)
        self.assertIn("return index_expr, None, None, rtok", index_tail_text)
        self.assertIn("return self._consume_subscript_index_tail_close_token()", index_tail_state_text)
        self.assertIn('return self._eat("]")', index_tail_close_text)
        self.assertIn("index_expr, lower, upper, rtok = self._resolve_subscript_suffix_token_state()", state_text)
        self.assertIn("return self._apply_subscript_suffix_token_state(", state_text)
        self.assertIn("source_span, repr_text = self._resolve_subscript_suffix_span_repr(", state_apply_text)
        self.assertIn("return self._apply_subscript_suffix_span_repr_state(", state_apply_text)
        self.assertIn("return index_expr, lower, upper, source_span, repr_text", subscript_span_apply_text)
        self.assertIn("return self._resolve_postfix_span_repr(", subscript_span_text)
        self.assertIn('return self._eat("[")', open_token_text)
        self.assertIn("return self._parse_subscript_suffix_components()", open_state_text)
        self.assertIn("self._consume_subscript_suffix_open_token()", token_text)
        self.assertIn("return self._apply_subscript_suffix_open_token_state()", token_text)
        self.assertIn("return self._consume_subscript_suffix_tokens()", token_state_text)
        self.assertIn(
            "index_expr, lower, upper, source_span, repr_text = self._resolve_subscript_suffix_state(",
            helper_text,
        )
        self.assertIn("return self._apply_subscript_suffix_state(", helper_text)
        self.assertIn("owner_expr=owner_expr,", helper_text)
        self.assertIn("index_expr=index_expr,", helper_text)
        self.assertIn("lower=lower,", helper_text)
        self.assertIn("upper=upper,", helper_text)
        self.assertIn("source_span=source_span,", helper_text)
        self.assertIn("repr_text=repr_text,", helper_text)
        self.assertIn("return self._annotate_subscript_expr(", helper_apply_text)
        self.assertIn("index_expr=index_expr,", helper_apply_text)
        self.assertIn("lower=lower,", helper_apply_text)
        self.assertIn("upper=upper,", helper_apply_text)
        self.assertNotIn('self._eat("[")', state_text)
        self.assertNotIn("index_expr, lower, upper, rtok = self._consume_subscript_suffix_tokens()", state_text)
        self.assertNotIn("source_span, repr_text = self._resolve_postfix_span_repr(", state_text)
        self.assertNotIn("return index_expr, lower, upper, source_span, repr_text", state_text)
        self.assertNotIn("return index_expr, lower, upper, source_span, repr_text", state_apply_text)
        self.assertNotIn("source_span, repr_text = self._resolve_postfix_span_repr(", helper_text)
        self.assertNotIn("return self._annotate_subscript_expr(", helper_text)
        self.assertNotIn('self._eat("[")', token_text)
        self.assertNotIn("return self._parse_subscript_suffix_components()", token_text)
        self.assertNotIn("return self._parse_subscript_suffix_components()", token_state_text)
        self.assertNotIn("return self._consume_subscript_slice_tail_tokens()", slice_tail_text)
        self.assertNotIn('self._eat(":")', slice_tail_text)
        self.assertNotIn('rtok = self._eat("]")', slice_tail_text)
        self.assertNotIn("return None, lower, upper, rtok", slice_tail_text)
        self.assertNotIn("return self._consume_subscript_slice_tail_tokens()", tail_state_text)
        self.assertNotIn("upper, rtok = self._consume_subscript_slice_tail_tokens()", tail_state_text)
        self.assertNotIn("return upper, rtok", tail_state_text)
        self.assertNotIn("return upper, rtok", tail_state_apply_text)
        self.assertNotIn("upper = self._parse_subscript_slice_upper_expr()", tail_state_text)
        self.assertNotIn('if self._cur()["k"] == "]":', upper_expr_text)
        self.assertNotIn('self._cur()["k"] == "]"', upper_state_text)
        self.assertNotIn("if is_empty:", upper_expr_text)
        self.assertNotIn("return self._parse_ifexp()", upper_expr_text)
        self.assertNotIn('self._eat(":")', tail_token_text)
        self.assertNotIn("self._consume_subscript_slice_tail_colon_token()", tail_token_text)
        self.assertNotIn("upper = self._resolve_subscript_slice_tail_upper_state()", tail_token_text)
        self.assertNotIn("upper = self._resolve_subscript_slice_tail_upper_state()", tail_colon_apply_text)
        self.assertNotIn("return self._resolve_subscript_slice_tail_upper_state()", tail_colon_state_text)
        self.assertNotIn("rtok = self._resolve_subscript_slice_tail_close_state()", tail_token_text)
        self.assertNotIn("return upper, rtok", tail_token_text)
        self.assertNotIn("return upper, rtok", tail_upper_apply_text)
        self.assertNotIn("return upper, rtok", tail_close_apply_text)
        self.assertNotIn("return self._consume_subscript_slice_tail_close_token()", tail_close_state_text)
        self.assertNotIn("return rtok", tail_close_token_apply_text)
        self.assertNotIn("return self._parse_subscript_slice_upper_expr()", tail_upper_state_text)
        self.assertNotIn('if self._cur()["k"] == ":":', component_text)
        self.assertNotIn("if starts_with_slice:", component_text)
        self.assertNotIn("return self._parse_subscript_slice_tail(lower=None)", component_text)
        self.assertNotIn("return self._parse_subscript_suffix_first_component()", component_text)
        self.assertNotIn("first = self._parse_ifexp()", component_text)
        self.assertNotIn("return self._parse_subscript_slice_tail(lower=first)", component_text)
        self.assertNotIn("return first, None, None, rtok", component_text)
        self.assertNotIn("first = self._parse_ifexp()", first_component_text)
        self.assertNotIn("if is_slice:", first_component_text)
        self.assertNotIn("return self._parse_subscript_slice_tail(lower=first)", first_component_text)
        self.assertNotIn("return first, None, None, rtok", first_component_text)
        self.assertNotIn('self._cur()["k"] == ":"', first_component_text)
        self.assertNotIn('self._cur()["k"] == ":"', first_component_state_text)
        self.assertNotIn(
            "return first, self._resolve_subscript_suffix_first_component_kind()",
            first_component_state_text,
        )
        self.assertNotIn('rtok = self._eat("]")', first_component_apply_text)
        self.assertNotIn("return self._parse_subscript_slice_tail(lower=first)", first_component_apply_text)
        self.assertNotIn("return self._parse_subscript_index_tail(index_expr=first)", first_component_apply_text)
        self.assertNotIn("rtok = self._consume_subscript_index_tail_close_token()", index_tail_text)
        self.assertNotIn('rtok = self._eat("]")', index_tail_text)
        self.assertIn("return self._apply_postfix_suffix_kind(", postfix_suffix_text)
        self.assertIn('if tok_kind == "[":', postfix_suffix_apply_text)
        self.assertIn("return self._parse_subscript_suffix(owner_expr=owner_expr)", postfix_suffix_apply_text)
        self.assertIn("next_node = self._parse_postfix_suffix(owner_expr=node)", postfix_text)
        self.assertNotIn('if self._cur()["k"] == ":":', helper_text)
        self.assertNotIn("first = self._parse_ifexp()", helper_text)
        self.assertNotIn('if self._cur()["k"] == ":":', postfix_text)
        self.assertNotIn("first = self._parse_ifexp()", postfix_text)
        self.assertNotIn("node = self._annotate_subscript_expr(", postfix_text)

    def test_core_source_known_inline_kind_residual_set_is_helper_only(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        builder_base_text = CORE_BUILDER_BASE_SOURCE_PATH.read_text(encoding="utf-8")
        ast_builder_text = CORE_AST_BUILDERS_SOURCE_PATH.read_text(encoding="utf-8")
        raw_kinds = re.findall(r'\{"kind": "([^"]+)"', text)
        inline_kinds = {kind for kind in raw_kinds if kind != "" and kind[0].isupper()}
        trivia_kinds = {kind for kind in raw_kinds if kind != "" and kind[0].islower()}
        multiline_kind_literals = set(
            re.findall(r'(?:return|node:\s*dict\[str, Any\]\s*=)\s*\{\s*"kind":\s*"([^"]+)"', text, re.S)
        )

        self.assertIn('node = _sh_make_stmt_node("Expr", source_span)', builder_base_text)
        self.assertIn('return _sh_make_node("Slice", lower=lower, upper=upper, step=step)', ast_builder_text)
        self.assertIn('return _sh_make_node("blank", count=count)', builder_base_text)
        self.assertIn('return _sh_make_node("comment", text=text)', builder_base_text)
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
