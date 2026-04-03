from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from toolchain.misc.transpile_cli import load_east3_document
from toolchain2.emit.julia.bootstrap import JuliaBootstrapRewriter
from toolchain2.emit.julia.bootstrap import module_id_from_doc
from toolchain2.emit.julia.bootstrap import prepare_module_for_emit
from toolchain2.emit.julia.emitter import JuliaRenderer
from toolchain2.emit.julia.emitter import transpile_to_julia_native
from toolchain2.emit.julia.subset import JuliaSubsetRenderer
from toolchain2.emit.julia.subset import can_render_module_natively


def _fixture_path(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixture" / "source" / "py").rglob(stem + ".py"))
    if not matches:
        raise FileNotFoundError(stem)
    return matches[0]


def _load_east3_for_julia(stem: str) -> dict[str, object]:
    doc = load_east3_document(
        _fixture_path(stem),
        parser_backend="self_hosted",
        object_dispatch_mode="native",
        east3_opt_level="1",
        target_lang="julia",
    )
    if not isinstance(doc, dict):
        raise AssertionError("expected dict EAST3 document")
    meta = doc.setdefault("meta", {})
    if not isinstance(meta, dict):
        raise AssertionError("expected meta dict")
    emit_context = meta.setdefault("emit_context", {})
    if not isinstance(emit_context, dict):
        raise AssertionError("expected emit_context dict")
    emit_context["is_entry"] = True
    return doc


class JuliaEmitterBootstrapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.renderer = JuliaRenderer()
        self.rewriter = JuliaBootstrapRewriter()

    def test_rewrite_closure_def_to_function_def(self) -> None:
        doc: dict[str, object] = {
            "kind": "Module",
            "body": [
                {
                    "kind": "ClosureDef",
                    "name": "inner",
                    "args": [],
                    "body": [{"kind": "Return", "value": {"kind": "Constant", "value": 1}}],
                }
            ],
        }
        rewritten = self.rewriter.rewrite_document(doc)
        body = rewritten.get("body")
        self.assertIsInstance(body, list)
        self.assertEqual(body[0].get("kind"), "FunctionDef")

    def test_rewrite_preserves_typed_vararg_when_body_uses_it(self) -> None:
        doc: dict[str, object] = {
            "kind": "Module",
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "merge",
                    "args": [{"name": "target"}],
                    "vararg_name": "states",
                    "vararg_type": "ControllerState",
                    "body": [
                        {
                            "kind": "For",
                            "target": {"kind": "Name", "id": "state"},
                            "iter": {"kind": "Name", "id": "states"},
                            "body": [],
                        }
                    ],
                }
            ],
        }
        rewritten = self.rewriter.rewrite_document(doc)
        fn = rewritten["body"][0]
        self.assertEqual(fn.get("vararg_name"), "states")
        self.assertEqual(fn.get("vararg_type"), "ControllerState")

    def test_rewrite_lifts_class_static_assign_and_rewrites_attribute_access(self) -> None:
        doc: dict[str, object] = {
            "kind": "Module",
            "body": [
                {
                    "kind": "ClassDef",
                    "name": "Config",
                    "body": [
                        {
                            "kind": "Assign",
                            "target": {"kind": "Name", "id": "DEFAULT_PORT"},
                            "value": {"kind": "Constant", "value": 8080},
                        }
                    ],
                },
                {
                    "kind": "Return",
                    "value": {
                        "kind": "Attribute",
                        "value": {"kind": "Name", "id": "Config"},
                        "attr": "DEFAULT_PORT",
                    },
                },
            ],
        }
        rewritten = self.rewriter.rewrite_document(doc)
        body = rewritten["body"]
        self.assertEqual(body[0]["kind"], "ClassDef")
        self.assertEqual(body[0]["body"], [])
        self.assertEqual(body[1]["kind"], "Assign")
        self.assertEqual(body[1]["target"]["id"], "__pytra_cls_Config_DEFAULT_PORT")
        self.assertEqual(body[2]["value"]["kind"], "Name")
        self.assertEqual(body[2]["value"]["id"], "__pytra_cls_Config_DEFAULT_PORT")

    def test_rewrite_folds_trait_isinstance_for_concrete_resolved_type(self) -> None:
        doc: dict[str, object] = {
            "kind": "Module",
            "body": [
                {"kind": "ClassDef", "name": "Drawable", "decorators": ["trait"], "body": []},
                {
                    "kind": "ClassDef",
                    "name": "Circle",
                    "decorators": ["implements(Drawable)"],
                    "body": [],
                },
                {
                    "kind": "ExprStmt",
                    "value": {
                        "kind": "IsInstance",
                        "value": {"kind": "Name", "id": "c", "resolved_type": "Circle"},
                        "expected_type_name": "Drawable",
                    },
                },
            ],
        }
        rewritten = self.rewriter.rewrite_document(doc)
        expr = rewritten["body"][2]["value"]
        self.assertEqual(expr.get("kind"), "Constant")
        self.assertEqual(expr.get("value"), True)

    def test_module_id_from_doc_prefers_emit_context_then_meta(self) -> None:
        doc: dict[str, object] = {
            "kind": "Module",
            "meta": {
                "module_id": "meta.module",
                "emit_context": {"module_id": "emit.module"},
            },
        }
        self.assertEqual(module_id_from_doc(doc), "emit.module")

    def test_prepare_module_for_emit_deepcopies_before_default_expansion(self) -> None:
        doc: dict[str, object] = {
            "kind": "Module",
            "east_stage": 3,
            "meta": {"module_id": "sample.defaults"},
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "foo",
                    "arg_order": ["x"],
                    "arg_defaults": {
                        "x": {"kind": "Constant", "value": 7, "resolved_type": "int", "repr": "7"}
                    },
                    "body": [{"kind": "Return", "value": {"kind": "Name", "id": "x"}}],
                },
                {
                    "kind": "Assign",
                    "target": {"kind": "Name", "id": "y"},
                    "value": {
                        "kind": "Call",
                        "func": {"kind": "Name", "id": "foo"},
                        "args": [],
                    },
                },
            ],
        }
        original = copy.deepcopy(doc)
        module_id, prepared = prepare_module_for_emit(doc)
        self.assertEqual(module_id, "sample.defaults")
        self.assertEqual(doc, original)
        call_args = prepared["body"][1]["value"]["args"]
        self.assertEqual(len(call_args), 1)
        self.assertEqual(call_args[0]["value"], 7)

    def test_subset_accepts_simple_fixture_module(self) -> None:
        doc = _load_east3_for_julia("add")
        _module_id, prepared = prepare_module_for_emit(doc)
        self.assertEqual(can_render_module_natively(prepared), True)

    def test_subset_renders_simple_fixture_module(self) -> None:
        doc = _load_east3_for_julia("add")
        _module_id, prepared = prepare_module_for_emit(doc)
        source = JuliaSubsetRenderer().render_module(prepared)
        self.assertIn("function add(a, b)", source)
        self.assertIn("__pytra_print(py_assert_stdout([\"7\"], _case_main))", source)

    def test_subset_accepts_for_range_fixture(self) -> None:
        doc = _load_east3_for_julia("for_range")
        _module_id, prepared = prepare_module_for_emit(doc)
        self.assertEqual(can_render_module_natively(prepared), True)

    def test_subset_accepts_loop_fixture(self) -> None:
        doc = _load_east3_for_julia("loop")
        _module_id, prepared = prepare_module_for_emit(doc)
        self.assertEqual(can_render_module_natively(prepared), True)

    def test_subset_accepts_ifexp_bool_fixture(self) -> None:
        doc = _load_east3_for_julia("ifexp_bool")
        _module_id, prepared = prepare_module_for_emit(doc)
        self.assertEqual(can_render_module_natively(prepared), True)

    def test_subset_accepts_dict_in_fixture(self) -> None:
        doc = _load_east3_for_julia("dict_in")
        _module_id, prepared = prepare_module_for_emit(doc)
        self.assertEqual(can_render_module_natively(prepared), True)

    def test_subset_accepts_negative_index_fixture(self) -> None:
        doc = _load_east3_for_julia("negative_index")
        _module_id, prepared = prepare_module_for_emit(doc)
        self.assertEqual(can_render_module_natively(prepared), True)

    def test_subset_accepts_slice_basic_fixture(self) -> None:
        doc = _load_east3_for_julia("slice_basic")
        _module_id, prepared = prepare_module_for_emit(doc)
        self.assertEqual(can_render_module_natively(prepared), True)

    def test_subset_accepts_list_repeat_fixture(self) -> None:
        doc = _load_east3_for_julia("list_repeat")
        _module_id, prepared = prepare_module_for_emit(doc)
        self.assertEqual(can_render_module_natively(prepared), True)

    def test_subset_accepts_dict_literal_entries_fixture(self) -> None:
        doc = _load_east3_for_julia("dict_literal_entries")
        _module_id, prepared = prepare_module_for_emit(doc)
        self.assertEqual(can_render_module_natively(prepared), True)

    def test_subset_accepts_tuple_assign_fixture(self) -> None:
        doc = _load_east3_for_julia("tuple_assign")
        _module_id, prepared = prepare_module_for_emit(doc)
        self.assertEqual(can_render_module_natively(prepared), True)

    def test_subset_accepts_str_join_method_fixture(self) -> None:
        doc = _load_east3_for_julia("str_join_method")
        _module_id, prepared = prepare_module_for_emit(doc)
        self.assertEqual(can_render_module_natively(prepared), True)

    def test_subset_accepts_lambda_basic_fixture(self) -> None:
        doc = _load_east3_for_julia("lambda_basic")
        _module_id, prepared = prepare_module_for_emit(doc)
        self.assertEqual(can_render_module_natively(prepared), True)

    def test_subset_accepts_lambda_immediate_fixture(self) -> None:
        doc = _load_east3_for_julia("lambda_immediate")
        _module_id, prepared = prepare_module_for_emit(doc)
        self.assertEqual(can_render_module_natively(prepared), True)

    def test_subset_accepts_lambda_ifexp_fixture(self) -> None:
        doc = _load_east3_for_julia("lambda_ifexp")
        _module_id, prepared = prepare_module_for_emit(doc)
        self.assertEqual(can_render_module_natively(prepared), True)

    def test_subset_accepts_lambda_as_arg_fixture(self) -> None:
        doc = _load_east3_for_julia("lambda_as_arg")
        _module_id, prepared = prepare_module_for_emit(doc)
        self.assertEqual(can_render_module_natively(prepared), True)

    def test_subset_accepts_lambda_capture_multiargs_fixture(self) -> None:
        doc = _load_east3_for_julia("lambda_capture_multiargs")
        _module_id, prepared = prepare_module_for_emit(doc)
        self.assertEqual(can_render_module_natively(prepared), True)

    def test_subset_accepts_lambda_local_state_fixture(self) -> None:
        doc = _load_east3_for_julia("lambda_local_state")
        _module_id, prepared = prepare_module_for_emit(doc)
        self.assertEqual(can_render_module_natively(prepared), True)

    def test_subset_accepts_rewritten_class_tuple_assign_fixture(self) -> None:
        doc = _load_east3_for_julia("class_tuple_assign")
        _module_id, prepared = prepare_module_for_emit(doc)
        rewritten = self.rewriter.rewrite_document(prepared)
        self.assertEqual(can_render_module_natively(rewritten), True)

    def test_subset_accepts_class_body_pass_fixture(self) -> None:
        doc = _load_east3_for_julia("class_body_pass")
        _module_id, prepared = prepare_module_for_emit(doc)
        self.assertEqual(can_render_module_natively(prepared), True)

    def test_subset_accepts_rewritten_obj_attr_space_fixture(self) -> None:
        doc = _load_east3_for_julia("obj_attr_space")
        _module_id, prepared = prepare_module_for_emit(doc)
        rewritten = self.rewriter.rewrite_document(prepared)
        self.assertEqual(can_render_module_natively(rewritten), True)

    def test_renderer_uses_subset_for_range_fixture(self) -> None:
        source = self.renderer.render_module(_load_east3_for_julia("for_range"))
        self.assertIn("for i in 0:(n - 1)", source)

    def test_renderer_uses_subset_for_loop_fixture(self) -> None:
        source = self.renderer.render_module(_load_east3_for_julia("loop"))
        self.assertIn("for v in values", source)
        self.assertIn("if __pytra_truthy(((v % 2) == 0))", source)

    def test_renderer_uses_subset_for_ifexp_bool_fixture(self) -> None:
        source = self.renderer.render_module(_load_east3_for_julia("ifexp_bool"))
        self.assertIn("__pytra_truthy((begin __pytra_boolop_", source)
        self.assertIn("? a : b", source)

    def test_renderer_uses_subset_for_dict_in_fixture(self) -> None:
        source = self.renderer.render_module(_load_east3_for_julia("dict_in"))
        self.assertIn("haskey(d, k)", source)

    def test_renderer_uses_subset_for_negative_index_fixture(self) -> None:
        source = self.renderer.render_module(_load_east3_for_julia("negative_index"))
        self.assertIn("__pytra_idx((-1), length(stack))", source)

    def test_renderer_uses_subset_for_slice_basic_fixture(self) -> None:
        source = self.renderer.render_module(_load_east3_for_julia("slice_basic"))
        self.assertIn("nums[(1 + 1):4]", source)
        self.assertIn("__pytra_str_slice(text, 2, 5)", source)

    def test_renderer_uses_subset_for_list_repeat_fixture(self) -> None:
        source = self.renderer.render_module(_load_east3_for_julia("list_repeat"))
        self.assertIn("repeat([0], 8)", source)
        self.assertIn("repeat([1, 2], 4)", source)

    def test_renderer_uses_subset_for_dict_literal_entries_fixture(self) -> None:
        source = self.renderer.render_module(_load_east3_for_julia("dict_literal_entries"))
        self.assertIn('token_tags = Dict("+" => 1, "=" => 7)', source)
        self.assertIn('get(token_tags, "=", 0)', source)

    def test_renderer_uses_subset_for_tuple_assign_fixture(self) -> None:
        source = self.renderer.render_module(_load_east3_for_julia("tuple_assign"))
        self.assertIn("x, y = y, x", source)

    def test_renderer_uses_subset_for_str_join_method_fixture(self) -> None:
        source = self.renderer.render_module(_load_east3_for_julia("str_join_method"))
        self.assertIn('return join(items, sep)', source)

    def test_renderer_uses_subset_for_lambda_basic_fixture(self) -> None:
        source = self.renderer.render_module(_load_east3_for_julia("lambda_basic"))
        self.assertIn("add_base = ((x) -> (x + base))", source)
        self.assertIn("always_true = (() -> true)", source)

    def test_renderer_uses_subset_for_lambda_immediate_fixture(self) -> None:
        source = self.renderer.render_module(_load_east3_for_julia("lambda_immediate"))
        self.assertIn("a = ((x) -> (x + 1))(3)", source)
        self.assertIn("b = ((x, y) -> (x + y))(4, 5)", source)

    def test_renderer_uses_subset_for_lambda_ifexp_fixture(self) -> None:
        source = self.renderer.render_module(_load_east3_for_julia("lambda_ifexp"))
        self.assertIn('choose = ((x) -> (__pytra_truthy((x > 0)) ? "pos" : "non-pos"))', source)

    def test_renderer_uses_subset_for_lambda_as_arg_fixture(self) -> None:
        source = self.renderer.render_module(_load_east3_for_julia("lambda_as_arg"))
        self.assertIn("inc = ((z) -> (z + 1))", source)
        self.assertIn("out = apply_once(inc, 41)", source)

    def test_renderer_uses_subset_for_lambda_capture_multiargs_fixture(self) -> None:
        source = self.renderer.render_module(_load_east3_for_julia("lambda_capture_multiargs"))
        self.assertIn("mix = ((a, b) -> ((a + b) + base))", source)

    def test_renderer_uses_subset_for_lambda_local_state_fixture(self) -> None:
        source = self.renderer.render_module(_load_east3_for_julia("lambda_local_state"))
        self.assertIn("scale = ((x) -> (x * factor))", source)

    def test_renderer_uses_subset_for_rewritten_class_tuple_assign_fixture(self) -> None:
        source = self.renderer.render_module(_load_east3_for_julia("class_tuple_assign"))
        self.assertIn("__pytra_cls_Holder_X = (0,)", source)
        self.assertIn("__pytra_print((__pytra_cls_Holder_X[__pytra_idx(0, length(__pytra_cls_Holder_X))] == 0))", source)
        self.assertIn("__pytra_main()", source)

    def test_renderer_uses_subset_for_class_body_pass_fixture(self) -> None:
        source = self.renderer.render_module(_load_east3_for_julia("class_body_pass"))
        self.assertIn("mutable struct Marker", source)
        self.assertIn("function __pytra_new_Marker()", source)
        self.assertIn("m = __pytra_new_Marker()", source)
        self.assertIn("__pytra_print((m !== nothing))", source)

    def test_renderer_uses_subset_for_rewritten_obj_attr_space_fixture(self) -> None:
        source = self.renderer.render_module(_load_east3_for_julia("obj_attr_space"))
        self.assertIn("mutable struct Obj", source)
        self.assertIn("value", source)
        self.assertIn("self.value = 7", source)
        self.assertIn("o = __pytra_new_Obj()", source)
        self.assertIn("__pytra_print((o.value == 7))", source)

    def test_emit_nested_closure_fixture_through_toolchain2_entrypoint(self) -> None:
        source = transpile_to_julia_native(_load_east3_for_julia("nested_closure_def"))
        self.assertIn("function inner(y)", source)
        self.assertIn("function rec(n)", source)

    def test_emit_typed_varargs_fixture_through_toolchain2_entrypoint(self) -> None:
        source = transpile_to_julia_native(_load_east3_for_julia("ok_typed_varargs_representative"))
        self.assertIn("function merge_controller_states(target, states)", source)
        self.assertIn("merge_controller_states(target, [lhs, rhs])", source)

    def test_render_module_expands_defaults_without_mutating_input(self) -> None:
        doc: dict[str, object] = {
            "kind": "Module",
            "east_stage": 3,
            "meta": {"module_id": "sample.defaults"},
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "foo",
                    "arg_order": ["x"],
                    "arg_defaults": {
                        "x": {"kind": "Constant", "value": 7, "resolved_type": "int", "repr": "7"}
                    },
                    "body": [
                        {"kind": "Return", "value": {"kind": "Name", "id": "x"}},
                    ],
                },
                {
                    "kind": "Assign",
                    "target": {"kind": "Name", "id": "y"},
                    "value": {
                        "kind": "Call",
                        "func": {"kind": "Name", "id": "foo"},
                        "args": [],
                    },
                },
            ],
        }
        original = copy.deepcopy(doc)
        source = self.renderer.render_module(doc)
        self.assertIn("y = foo(7)", source)
        self.assertEqual(doc, original)

    def test_renderer_uses_subset_for_simple_fixture(self) -> None:
        source = self.renderer.render_module(_load_east3_for_julia("add"))
        self.assertIn("function add(a, b)", source)
        self.assertNotIn("__pytra_print(py_assert_stdout([\"7\"], _case_main));", source)


if __name__ == "__main__":
    unittest.main()
