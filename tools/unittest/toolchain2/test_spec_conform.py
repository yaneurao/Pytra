from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))


from toolchain2.common.jv import deep_copy_json
from toolchain2.compile.jv import CompileContext
from toolchain2.compile.lower import lower_east2_to_east3
from toolchain2.compile.passes import apply_guard_narrowing
from toolchain2.emit.common.code_emitter import (
    RuntimeMapping,
    build_runtime_import_map,
    resolve_runtime_symbol_name,
)
from toolchain2.link.linker import link_modules
from toolchain2.optimize.optimizer import optimize_east3_document
from toolchain2.optimize.optimizer import make_pass_context
from toolchain2.optimize.optimizer import resolve_bounds_check_mode
from toolchain2.optimize.optimizer import resolve_negative_index_mode
from toolchain2.optimize.passes.subscript_access_annotation import SubscriptAccessAnnotationPass
from toolchain2.optimize.passes.typed_enumerate_normalization import TypedEnumerateNormalizationPass
from toolchain2.optimize.passes.typed_repeat_materialization import TypedRepeatMaterializationPass
from toolchain2.parse.py.parser import parse_python_source
from toolchain2.parse.py.parse_python import parse_python_file
from toolchain2.resolve.py.builtin_registry import BuiltinRegistry, load_builtin_registry
from toolchain2.resolve.py.resolver import resolve_east1_to_east2
from toolchain2.resolve.py.validate_east2 import validate_east2


def _walk(node: object) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    if isinstance(node, dict):
        out.append(node)
        for value in node.values():
            out.extend(_walk(value))
    elif isinstance(node, list):
        for item in node:
            out.extend(_walk(item))
    return out


def _load_registry() -> BuiltinRegistry:
    return load_builtin_registry(
        ROOT / "test" / "include" / "east1" / "py" / "built_in" / "builtins.py.east1",
        ROOT / "test" / "include" / "east1" / "py" / "built_in" / "containers.py.east1",
        ROOT / "test" / "include" / "east1" / "py" / "std",
    )


class Toolchain2SpecConformTests(unittest.TestCase):
    def test_optimizer_mode_normalizers_accept_defaults_and_reject_invalid(self) -> None:
        self.assertEqual(resolve_negative_index_mode(""), "const_only")
        self.assertEqual(resolve_negative_index_mode("always"), "always")
        self.assertEqual(resolve_bounds_check_mode(""), "off")
        self.assertEqual(resolve_bounds_check_mode("debug"), "debug")
        with self.assertRaisesRegex(ValueError, "invalid --negative-index-mode"):
            resolve_negative_index_mode("maybe")
        with self.assertRaisesRegex(ValueError, "invalid --bounds-check-mode"):
            resolve_bounds_check_mode("fast")

    def test_subscript_access_annotation_marks_range_index_fastpath(self) -> None:
        subscript = {
            "kind": "Subscript",
            "value": {"kind": "Name", "id": "xs", "resolved_type": "list[int64]"},
            "slice": {"kind": "Name", "id": "i", "resolved_type": "int64"},
            "resolved_type": "int64",
        }
        doc = {
            "kind": "Module",
            "east_stage": 3,
            "body": [
                {
                    "kind": "ForCore",
                    "iter_mode": "static_fastpath",
                    "iter_plan": {
                        "kind": "StaticRangeForPlan",
                        "start": {"kind": "Constant", "value": 0},
                        "stop": {"kind": "Name", "id": "n", "resolved_type": "int64"},
                        "step": {"kind": "Constant", "value": 1},
                        "range_mode": "ascending",
                    },
                    "target_plan": {"kind": "NameTarget", "id": "i", "target_type": "int64"},
                    "body": [{"kind": "Expr", "value": subscript}],
                    "orelse": [],
                }
            ],
        }

        result = SubscriptAccessAnnotationPass().run(doc, make_pass_context(opt_level=1))

        self.assertTrue(result.changed)
        hint = subscript.get("meta", {}).get("subscript_access_v1")
        self.assertEqual(
            hint,
            {
                "schema_version": "subscript_access_v1",
                "negative_index": "skip",
                "bounds_check": "off",
                "reason": "for_range_index",
            },
        )

    def test_subscript_access_annotation_respects_negative_literal_and_default_modes(self) -> None:
        negative = {
            "kind": "Subscript",
            "value": {"kind": "Name", "id": "xs", "resolved_type": "list[int64]"},
            "slice": {"kind": "UnaryOp", "op": "USub", "operand": {"kind": "Constant", "value": 1}},
            "resolved_type": "int64",
        }
        dynamic = {
            "kind": "Subscript",
            "value": {"kind": "Name", "id": "buf", "resolved_type": "bytes"},
            "slice": {"kind": "Name", "id": "j", "resolved_type": "int64"},
            "resolved_type": "uint8",
        }
        doc = {
            "kind": "Module",
            "east_stage": 3,
            "body": [{"kind": "Expr", "value": negative}, {"kind": "Expr", "value": dynamic}],
        }

        result = SubscriptAccessAnnotationPass().run(
            doc,
            make_pass_context(
                opt_level=1,
                debug_flags={"negative_index_mode": "always", "bounds_check_mode": "debug"},
            ),
        )

        self.assertTrue(result.changed)
        self.assertEqual(
            negative.get("meta", {}).get("subscript_access_v1"),
            {
                "schema_version": "subscript_access_v1",
                "negative_index": "normalize",
                "bounds_check": "full",
                "reason": "negative_literal",
            },
        )
        self.assertEqual(
            dynamic.get("meta", {}).get("subscript_access_v1"),
            {
                "schema_version": "subscript_access_v1",
                "negative_index": "normalize",
                "bounds_check": "full",
                "reason": "optimizer_default",
            },
        )

    def test_subscript_access_annotation_marks_monotonic_while_index_fastpath(self) -> None:
        subscript = {
            "kind": "Subscript",
            "value": {"kind": "Name", "id": "raw", "resolved_type": "bytes"},
            "slice": {"kind": "Name", "id": "i", "resolved_type": "int64"},
            "resolved_type": "uint8",
        }
        doc = {
            "kind": "Module",
            "east_stage": 3,
            "body": [
                {
                    "kind": "Assign",
                    "target": {"kind": "Name", "id": "i"},
                    "value": {"kind": "Constant", "value": 0, "resolved_type": "int64"},
                },
                {
                    "kind": "While",
                    "test": {
                        "kind": "Compare",
                        "left": {"kind": "Name", "id": "i", "resolved_type": "int64"},
                        "ops": ["Lt"],
                        "comparators": [{"kind": "Name", "id": "n", "resolved_type": "int64"}],
                    },
                    "body": [
                        {"kind": "Expr", "value": subscript},
                        {
                            "kind": "AugAssign",
                            "target": {"kind": "Name", "id": "i"},
                            "op": "Add",
                            "value": {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                        },
                    ],
                    "orelse": [],
                },
            ],
        }

        result = SubscriptAccessAnnotationPass().run(doc, make_pass_context(opt_level=1))

        self.assertTrue(result.changed)
        self.assertEqual(
            subscript.get("meta", {}).get("subscript_access_v1"),
            {
                "schema_version": "subscript_access_v1",
                "negative_index": "skip",
                "bounds_check": "off",
                "reason": "for_range_index",
            },
        )

    def test_subscript_access_annotation_tracks_non_negative_alias_assignment(self) -> None:
        subscript = {
            "kind": "Subscript",
            "value": {"kind": "Name", "id": "raw", "resolved_type": "bytes"},
            "slice": {"kind": "Name", "id": "j", "resolved_type": "int64"},
            "resolved_type": "uint8",
        }
        doc = {
            "kind": "Module",
            "east_stage": 3,
            "body": [
                {
                    "kind": "Assign",
                    "target": {"kind": "Name", "id": "i"},
                    "value": {"kind": "Constant", "value": 0, "resolved_type": "int64"},
                },
                {
                    "kind": "Assign",
                    "target": {"kind": "Name", "id": "j"},
                    "value": {"kind": "Name", "id": "i", "resolved_type": "int64"},
                },
                {
                    "kind": "While",
                    "test": {
                        "kind": "Compare",
                        "left": {"kind": "Name", "id": "j", "resolved_type": "int64"},
                        "ops": ["Lt"],
                        "comparators": [{"kind": "Name", "id": "n", "resolved_type": "int64"}],
                    },
                    "body": [
                        {"kind": "Expr", "value": subscript},
                        {
                            "kind": "AugAssign",
                            "target": {"kind": "Name", "id": "j"},
                            "op": "Add",
                            "value": {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                        },
                    ],
                    "orelse": [],
                },
            ],
        }

        result = SubscriptAccessAnnotationPass().run(doc, make_pass_context(opt_level=1))

        self.assertTrue(result.changed)
        self.assertEqual(
            subscript.get("meta", {}).get("subscript_access_v1", {}).get("bounds_check"),
            "off",
        )

    def test_optimize_east3_document_registers_subscript_access_annotation_pass(self) -> None:
        subscript = {
            "kind": "Subscript",
            "value": {"kind": "Name", "id": "xs", "resolved_type": "list[int64]"},
            "slice": {"kind": "Constant", "value": 0, "resolved_type": "int64"},
            "resolved_type": "int64",
        }
        doc = {"kind": "Module", "east_stage": 3, "schema_version": 1, "meta": {}, "body": [{"kind": "Expr", "value": subscript}]}

        out_doc, report = optimize_east3_document(
            deep_copy_json(doc),
            opt_level=1,
            debug_flags={"negative_index_mode": "const_only", "bounds_check_mode": "off"},
        )

        self.assertIsInstance(out_doc.get("body"), list)
        hint = out_doc["body"][0]["value"].get("meta", {}).get("subscript_access_v1")
        self.assertEqual(hint.get("reason"), "non_negative_constant")
        trace = report.get("trace", [])
        self.assertTrue(any(item.get("name") == "SubscriptAccessAnnotationPass" for item in trace if isinstance(item, dict)))

    def test_common_emitter_resolves_runtime_symbol_names_from_mapping_first(self) -> None:
        mapping = RuntimeMapping(
            builtin_prefix="rt_",
            calls={"math.sin": "rt_sin", "argv": "rt_argv"},
            skip_module_prefixes=["runtime."],
        )

        self.assertEqual(
            resolve_runtime_symbol_name(
                "sin",
                mapping,
                resolved_runtime_call="math.sin",
                runtime_call="sin",
            ),
            "rt_sin",
        )
        self.assertEqual(resolve_runtime_symbol_name("argv", mapping), "rt_argv")
        self.assertEqual(resolve_runtime_symbol_name("helper", mapping), "rt_helper")
        self.assertEqual(resolve_runtime_symbol_name("rt_helper", mapping), "rt_helper")

    def test_common_emitter_builds_runtime_import_map_from_binding_metadata(self) -> None:
        mapping = RuntimeMapping(
            builtin_prefix="rt_",
            calls={"math.sin": "rt_sin"},
            skip_module_prefixes=["runtime.", "pytra.std."],
        )
        meta = {
            "import_bindings": [
                {
                    "module_id": "runtime.custom",
                    "export_name": "helper",
                    "local_name": "helper",
                    "binding_kind": "symbol",
                },
                {
                    "module_id": "pytra.std",
                    "export_name": "math",
                    "local_name": "math_alias",
                    "binding_kind": "symbol",
                },
                {
                    "module_id": "math",
                    "runtime_module_id": "pytra.std.math",
                    "export_name": "sqrt",
                    "local_name": "msqrt",
                    "binding_kind": "symbol",
                    "runtime_symbol": "sqrt",
                },
                {
                    "module_id": "time",
                    "runtime_module_id": "pytra.std.time",
                    "export_name": "perf_counter",
                    "local_name": "perf_counter",
                    "binding_kind": "symbol",
                    "runtime_symbol": "perf_counter",
                },
                {
                    "module_id": "app.local",
                    "export_name": "helper",
                    "local_name": "local_helper",
                    "binding_kind": "symbol",
                },
            ]
        }

        runtime_imports = build_runtime_import_map(meta, mapping)

        self.assertEqual(runtime_imports["helper"], "rt_helper")
        self.assertEqual(runtime_imports["math_alias"], "math")
        self.assertEqual(runtime_imports["msqrt"], "sqrt")
        self.assertEqual(runtime_imports["perf_counter"], "perf_counter")
        self.assertNotIn("local_helper", runtime_imports)

    def test_typed_repeat_materialization_keeps_resolved_type_and_sets_hints(self) -> None:
        repeat_elt = {
            "kind": "BinOp",
            "op": "Mult",
            "resolved_type": "unknown",
            "left": {"kind": "List", "resolved_type": "list[int64]", "elements": [{"kind": "Constant", "value": 0}]},
            "right": {"kind": "Name", "id": "w", "resolved_type": "int64"},
            "casts": [],
        }
        list_comp = {
            "kind": "ListComp",
            "resolved_type": "list[unknown]",
            "elt": repeat_elt,
            "generators": [],
            "casts": [],
        }
        doc = {"kind": "Module", "body": [{"kind": "Expr", "value": list_comp}]}

        result = TypedRepeatMaterializationPass().run(doc, make_pass_context(opt_level=1))

        self.assertTrue(result.changed)
        self.assertEqual(repeat_elt.get("resolved_type"), "unknown")
        self.assertEqual(repeat_elt.get("repeat_result_type_hint"), "list[int64]")
        self.assertEqual(list_comp.get("resolved_type"), "list[unknown]")
        self.assertEqual(list_comp.get("list_comp_result_type_hint"), "list[list[int64]]")

    def test_typed_enumerate_normalization_keeps_resolved_type_and_sets_iter_metadata(self) -> None:
        iter_expr = {
            "kind": "Call",
            "resolved_type": "unknown",
            "func": {"kind": "Name", "id": "enumerate", "resolved_type": "unknown"},
            "args": [{"kind": "Name", "id": "lines", "resolved_type": "list[str]"}],
            "keywords": [],
            "lowered_kind": "BuiltinCall",
            "builtin_name": "enumerate",
            "runtime_call": "py_enumerate",
        }
        for_stmt = {
            "kind": "ForCore",
            "iter_mode": "runtime_protocol",
            "iter_plan": {
                "kind": "RuntimeIterForPlan",
                "iter_expr": iter_expr,
                "dispatch_mode": "native",
                "init_op": "ObjIterInit",
                "next_op": "ObjIterNext",
            },
            "target_plan": {
                "kind": "TupleTarget",
                "elements": [
                    {"kind": "NameTarget", "id": "line_index", "target_type": "unknown"},
                    {"kind": "NameTarget", "id": "source", "target_type": "unknown"},
                ],
            },
            "body": [{"kind": "Pass"}],
            "orelse": [],
        }
        doc = {"kind": "Module", "body": [for_stmt]}

        result = TypedEnumerateNormalizationPass().run(doc, make_pass_context(opt_level=1))

        self.assertTrue(result.changed)
        self.assertEqual(iter_expr.get("resolved_type"), "unknown")
        self.assertEqual(iter_expr.get("iter_element_type"), "tuple[int64, str]")
        self.assertEqual(iter_expr.get("iterable_trait"), "yes")
        self.assertEqual(iter_expr.get("iter_protocol"), "static_range")
        self.assertEqual(for_stmt.get("iter_plan", {}).get("iter_item_type"), "tuple[int64, str]")
        self.assertEqual(for_stmt.get("target_plan", {}).get("target_type"), "tuple[int64, str]")

    def test_parser_preserves_typing_prefix_until_resolve(self) -> None:
        source = """
import typing

def f(xs: typing.List[int], *rest: typing.Tuple[str, int]) -> "typing.List[int]":
    return xs
"""
        east1 = parse_python_source(source, "<mem>").to_jv()
        fn = next(node for node in _walk(east1) if node.get("kind") == "FunctionDef" and node.get("name") == "f")

        self.assertEqual(fn.get("arg_types", {}).get("xs"), "typing.List[int]")
        self.assertEqual(fn.get("vararg_type"), "typing.Tuple[str, int]")
        self.assertEqual(fn.get("return_type"), '"typing.List[int]"')

        east2 = deep_copy_json(east1)
        self.assertIsInstance(east2, dict)
        resolve_east1_to_east2(east2, registry=_load_registry())
        fn2 = next(node for node in _walk(east2) if node.get("kind") == "FunctionDef" and node.get("name") == "f")

        self.assertEqual(fn2.get("arg_types", {}).get("xs"), "list[int64]")
        self.assertEqual(fn2.get("vararg_type"), "tuple[str,int64]")
        self.assertEqual(fn2.get("return_type"), "list[int64]")
        self.assertEqual(
            fn2.get("vararg_type_expr"),
            {
                "kind": "GenericType",
                "base": "tuple",
                "args": [
                    {"kind": "NamedType", "name": "str"},
                    {"kind": "NamedType", "name": "int64"},
                ],
            },
        )

    def test_parser_preserves_type_alias_value_in_east1(self) -> None:
        source = """
type Scalar = int | float
"""
        east1 = parse_python_source(source, "<mem>").to_jv()

        type_alias = next(node for node in _walk(east1) if node.get("kind") == "TypeAlias")
        self.assertEqual(type_alias.get("name"), "Scalar")
        self.assertEqual(type_alias.get("value"), "int | float")

    def test_parse_python_file_accepts_stdlib_json_current_source(self) -> None:
        east1 = parse_python_file(str(ROOT / "src" / "pytra" / "std" / "json.py"))
        self.assertEqual(east1.get("kind"), "Module")
        self.assertTrue(any(node.get("kind") == "ClassDef" and node.get("name") == "JsonValue" for node in _walk(east1)))

    def test_parse_python_file_accepts_selfhost_toolchain2_source_with_typing_aliases(self) -> None:
        east1 = parse_python_file(str(ROOT / "src" / "toolchain2" / "common" / "jv.py"))
        self.assertEqual(east1.get("kind"), "Module")
        self.assertTrue(any(node.get("kind") == "TypeAlias" for node in _walk(east1)))

    def test_parser_keeps_trait_and_implements_class_decorators(self) -> None:
        source = """
@trait
class Drawable:
    def draw(self) -> None: ...

@implements(Drawable)
class Circle:
    def draw(self) -> None:
        pass
"""
        east1 = parse_python_source(source, "<mem>").to_jv()
        classes = [node for node in _walk(east1) if node.get("kind") == "ClassDef"]
        drawable = next(node for node in classes if node.get("name") == "Drawable")
        circle = next(node for node in classes if node.get("name") == "Circle")

        self.assertEqual(drawable.get("decorators"), ["trait"])
        self.assertEqual(circle.get("decorators"), ["implements(Drawable)"])

    def test_parser_derives_runtime_class_and_method_extern_metadata(self) -> None:
        source = """
from pytra.std import runtime

@runtime("pytra.core")
class list:
    def __len__(self) -> int: ...
    def append(self, x: int) -> None: ...
"""
        east1 = parse_python_source(source, "<mem>").to_jv()
        cls = next(
            node for node in _walk(east1)
            if node.get("kind") == "ClassDef" and node.get("name") == "list"
        )
        methods = {
            node.get("name"): node
            for node in _walk(cls)
            if node.get("kind") == "FunctionDef"
        }

        self.assertEqual(cls.get("meta", {}).get("runtime_v1"), {"schema_version": 1, "namespace": "pytra.core"})
        self.assertEqual(
            cls.get("meta", {}).get("extern_v2"),
            {"module": "pytra.core.list", "symbol": "list", "tag": "container.list"},
        )
        self.assertEqual(
            methods["__len__"].get("meta", {}).get("extern_v2"),
            {
                "module": "pytra.core.list",
                "symbol": "list.__len__",
                "tag": "dunder.len",
                "kind": "method",
            },
        )
        self.assertEqual(
            methods["append"].get("meta", {}).get("extern_v2"),
            {
                "module": "pytra.core.list",
                "symbol": "list.append",
                "tag": "stdlib.method.append",
                "kind": "method",
            },
        )

    def test_parser_rejects_extern_method_decorator(self) -> None:
        source = """
from pytra.std import extern_method

class Path:
    @extern_method(module="pytra.std.pathlib", symbol="pathlib.read_text", tag="stdlib.method.read_text")
    def read_text(self) -> str: ...
"""
        with self.assertRaisesRegex(RuntimeError, "extern_method is removed"):
            parse_python_source(source, "<mem>").to_jv()

    def test_parser_rejects_abi_decorator(self) -> None:
        source = """
from pytra.std import abi

@abi(ret="value")
def f() -> int:
    return 1
"""
        with self.assertRaisesRegex(RuntimeError, "abi decorator is removed"):
            parse_python_source(source, "<mem>").to_jv()

    def test_resolver_adds_trait_metadata_and_trait_impl_markers(self) -> None:
        source = """
@trait
class Drawable:
    def draw(self) -> None: ...

@trait
class Serializable:
    def draw(self) -> None: ...
    def serialize(self) -> str: ...

@implements(Drawable, Serializable)
class Circle:
    def draw(self) -> None:
        pass

    def serialize(self) -> str:
        return "circle"
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())

        drawable = next(
            node for node in _walk(east2)
            if node.get("kind") == "ClassDef" and node.get("name") == "Drawable"
        )
        circle = next(
            node for node in _walk(east2)
            if node.get("kind") == "ClassDef" and node.get("name") == "Circle"
        )
        draw_impl = next(
            node for node in _walk(circle)
            if node.get("kind") == "FunctionDef" and node.get("name") == "draw"
        )
        serialize_impl = next(
            node for node in _walk(circle)
            if node.get("kind") == "FunctionDef" and node.get("name") == "serialize"
        )

        trait_meta = drawable.get("meta", {}).get("trait_v1")
        impl_meta = circle.get("meta", {}).get("implements_v1")
        self.assertIsInstance(trait_meta, dict)
        self.assertEqual(trait_meta.get("extends_traits"), [])
        self.assertEqual([row.get("name") for row in trait_meta.get("methods", [])], ["draw"])
        self.assertEqual(impl_meta, {"schema_version": 1, "traits": ["Drawable", "Serializable"]})
        self.assertEqual(
            draw_impl.get("meta", {}).get("trait_impl_v1"),
            [
                {"schema_version": 1, "trait_name": "Drawable", "method_name": "draw"},
                {"schema_version": 1, "trait_name": "Serializable", "method_name": "draw"},
            ],
        )
        self.assertEqual(
            serialize_impl.get("meta", {}).get("trait_impl_v1"),
            {"schema_version": 1, "trait_name": "Serializable", "method_name": "serialize"},
        )

        east3 = lower_east2_to_east3(deep_copy_json(east2))
        drawable3 = next(
            node for node in _walk(east3)
            if node.get("kind") == "ClassDef" and node.get("name") == "Drawable"
        )
        circle3 = next(
            node for node in _walk(east3)
            if node.get("kind") == "ClassDef" and node.get("name") == "Circle"
        )
        self.assertIn("trait_v1", drawable3.get("meta", {}))
        self.assertIn("implements_v1", circle3.get("meta", {}))

    def test_resolver_rejects_missing_trait_method(self) -> None:
        source = """
@trait
class Drawable:
    def draw(self) -> None: ...

@implements(Drawable)
class Circle:
    def area(self) -> int:
        return 1
"""
        east2 = parse_python_source(source, "<mem>").to_jv()

        with self.assertRaisesRegex(RuntimeError, "missing trait method implementation"):
            resolve_east1_to_east2(east2, registry=_load_registry())

    def test_resolver_rejects_non_stub_trait_method_body(self) -> None:
        source = """
@trait
class Drawable:
    def draw(self) -> None:
        pass
"""
        east2 = parse_python_source(source, "<mem>").to_jv()

        with self.assertRaisesRegex(RuntimeError, "trait method body must be ellipsis-only"):
            resolve_east1_to_east2(east2, registry=_load_registry())

    def test_stdlib_json_current_source_flows_through_full_pipeline(self) -> None:
        east1 = parse_python_file(str(ROOT / "src" / "pytra" / "std" / "json.py"))

        east2 = deep_copy_json(east1)
        self.assertIsInstance(east2, dict)
        resolve_east1_to_east2(east2, registry=_load_registry())
        validate_east2(east2)

        east3 = lower_east2_to_east3(deep_copy_json(east2))
        self.assertEqual(east3.get("kind"), "Module")

        east3_opt, _report = optimize_east3_document(deep_copy_json(east3), opt_level=1)
        self.assertEqual(east3_opt.get("kind"), "Module")

        with tempfile.TemporaryDirectory() as tmp:
            east3_path = Path(tmp) / "json.east3"
            east3_path.write_text(json.dumps(east3_opt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            linked = link_modules([str(east3_path)], target="go", dispatch_mode="native")

        self.assertEqual(linked.manifest.get("schema"), "pytra.link_output.v1")
        self.assertIn("json", [module.module_id for module in linked.linked_modules])
        self.assertTrue(any(module.is_entry and module.module_id == "json" for module in linked.linked_modules))

    def test_parser_accepts_keyword_unpack_in_call(self) -> None:
        source = """
def f(kwargs: dict[str, object]) -> None:
    run(["echo"], **kwargs)
"""
        east1 = parse_python_source(source, "<mem>").to_jv()

        call = next(node for node in _walk(east1) if node.get("kind") == "Call")
        keywords = call.get("keywords", [])

        self.assertEqual(len(keywords), 1)
        self.assertIsNone(keywords[0].get("arg"))
        self.assertEqual(keywords[0].get("value", {}).get("kind"), "Name")
        self.assertEqual(keywords[0].get("value", {}).get("id"), "kwargs")

    def test_parse_python_file_keeps_multiline_function_docstring_as_docstring(self) -> None:
        source = '''\
def run() -> None:
    """Run a command.

    Args:
        cwd: Working directory.
    """
    value = 1
'''
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "doc.py"
            path.write_text(source, encoding="utf-8")
            east1 = parse_python_file(str(path))

        fn = next(node for node in _walk(east1) if node.get("kind") == "FunctionDef" and node.get("name") == "run")
        body = fn.get("body", [])

        self.assertEqual(fn.get("docstring"), "Run a command.\n\n    Args:\n        cwd: Working directory.\n    ")
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0].get("kind"), "Assign")

    def test_resolver_expands_type_aliases_by_east2(self) -> None:
        source = """
type Scalar = int | float

def identity(value: Scalar) -> Scalar:
    return value
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())

        type_alias = next(node for node in _walk(east2) if node.get("kind") == "TypeAlias")
        fn = next(node for node in _walk(east2) if node.get("kind") == "FunctionDef" and node.get("name") == "identity")
        ret_name = next(
            node for node in _walk(fn)
            if node.get("kind") == "Name" and node.get("id") == "value" and node.get("resolved_type") != "callable"
        )

        self.assertEqual(type_alias.get("value"), "int64 | float64")
        self.assertEqual(fn.get("arg_types", {}).get("value"), "int64 | float64")
        self.assertEqual(fn.get("return_type"), "int64 | float64")
        self.assertEqual(ret_name.get("resolved_type"), "int64 | float64")

    def test_resolver_preserves_existing_tuple_target_types_under_optional_tuple_reassign(self) -> None:
        source = """
def f(separators: tuple[str, str] | None) -> str:
    item_sep = ","
    key_sep = ":"
    if separators is not None:
        item_sep, key_sep = separators
    return item_sep + key_sep
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())

        names = [
            node for node in _walk(east2)
            if node.get("kind") == "Name" and node.get("id") in {"item_sep", "key_sep"}
        ]
        return_names = [
            node for node in names
            if node.get("repr") in {"item_sep", "key_sep"} and node.get("borrow_kind") == "readonly_ref"
        ]

        self.assertTrue(return_names)
        self.assertTrue(all(node.get("resolved_type") == "str" for node in return_names))

    def test_resolver_supports_block_import_aliases(self) -> None:
        source = """
def f() -> str:
    import os as _os
    return _os.sep
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())

        fn = next(node for node in _walk(east2) if node.get("kind") == "FunctionDef" and node.get("name") == "f")
        body = fn.get("body", [])
        os_ref = next(
            node
            for node in _walk(fn)
            if node.get("kind") == "Name" and node.get("id") == "_os" and node.get("repr") == "_os"
        )

        self.assertEqual(body[0].get("kind"), "Import")
        self.assertEqual(os_ref.get("resolved_type"), "module")

    def test_resolver_treats_function_value_refs_as_callable(self) -> None:
        source = """
from pytra.typing import Callable  # type:ignore

def takes_cb(cb: Callable) -> bool:
    return cb is not None

def main() -> None:
    print(takes_cb(main))
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())

        main_ref = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "Name"
            and node.get("id") == "main"
            and node.get("call_arg_type") == "Callable"
        )

        self.assertEqual(main_ref.get("resolved_type"), "Callable")

    def test_resolver_resolves_class_object_fields_staticmethods_and_enum_members(self) -> None:
        source = """
from pytra.enum import IntEnum

class Counter:
    value: int = 0

    def inc(self) -> int:
        Counter.value += 1
        return Counter.value

class MathUtil:
    @staticmethod
    def double(x: int) -> int:
        return x * 2

class Status(IntEnum):
    OK = 0
    ERROR = 1

def run() -> int:
    return Counter().inc() + MathUtil.double(2) + int(Status.ERROR)
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())

        counter_attrs = [
            node
            for node in _walk(east2)
            if node.get("kind") == "Attribute"
            and node.get("attr") == "value"
            and isinstance(node.get("value"), dict)
            and node["value"].get("kind") == "Name"
            and node["value"].get("id") == "Counter"
        ]
        static_call = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "Call"
            and node.get("repr") == "MathUtil.double(2)"
        )
        enum_attr = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "Attribute"
            and node.get("attr") == "ERROR"
            and isinstance(node.get("value"), dict)
            and node["value"].get("id") == "Status"
        )

        self.assertEqual([node.get("resolved_type") for node in counter_attrs], ["int64", "int64"])
        self.assertEqual(static_call.get("resolved_type"), "int64")
        self.assertEqual(static_call.get("call_dispatch_kind"), "static_method")
        self.assertEqual(enum_attr.get("resolved_type"), "Status")

    def test_resolver_preserves_property_getters_across_inherited_fields(self) -> None:
        source = """
class Base:
    def __init__(self) -> None:
        self.value: int = 1

class Child(Base):
    @property
    def prop(self) -> int:
        return self.value

    def total(self) -> int:
        return self.prop + self.value
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())

        prop_attr = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "Attribute"
            and node.get("attr") == "prop"
            and isinstance(node.get("value"), dict)
            and node["value"].get("id") == "self"
        )
        self_attrs = [
            node
            for node in _walk(east2)
            if node.get("kind") == "Attribute"
            and node.get("attr") == "value"
            and isinstance(node.get("value"), dict)
            and node["value"].get("id") == "self"
        ]

        self.assertEqual(prop_attr.get("resolved_type"), "int64")
        self.assertTrue(self_attrs)
        self.assertTrue(all(node.get("resolved_type") == "int64" for node in self_attrs))

    def test_resolver_does_not_materialize_inherited_init_fields_on_child(self) -> None:
        source = """
class Base:
    def __init__(self) -> None:
        self.value: int = 1

class Child(Base):
    def __init__(self) -> None:
        super().__init__()
        self.value += 1
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())

        child_cls = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "ClassDef" and node.get("name") == "Child"
        )

        self.assertEqual(child_cls.get("field_types"), {})

    def test_pytra_typing_cast_is_kept_as_value_import_and_resolves_target_type(self) -> None:
        source = """
from pytra.typing import Any, cast
from pytra.std.pathlib import Path

def f(value: str | Path, raw: Any) -> str:
    text = cast(str, value)
    path_obj = cast(Path, value)
    return text
"""
        east1 = parse_python_source(source, "<mem>").to_jv()
        meta1 = east1.get("meta", {})
        self.assertIsInstance(meta1, dict)
        import_symbols1 = meta1.get("import_symbols", {})
        self.assertIsInstance(import_symbols1, dict)
        self.assertEqual(import_symbols1.get("cast"), {"module": "pytra.typing", "name": "cast"})
        self.assertNotIn("Any", import_symbols1)

        east2 = deep_copy_json(east1)
        self.assertIsInstance(east2, dict)
        resolve_east1_to_east2(east2, registry=_load_registry())

        cast_calls = [
            node
            for node in _walk(east2)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Name"
            and node["func"].get("id") == "cast"
        ]
        self.assertEqual([node.get("resolved_type") for node in cast_calls], ["str", "Path"])

        east3 = lower_east2_to_east3(deep_copy_json(east2))
        text_assign = next(
            node for node in _walk(east3)
            if node.get("kind") == "Assign"
            and isinstance(node.get("target"), dict)
            and node["target"].get("id") == "text"
        )
        path_assign = next(
            node for node in _walk(east3)
            if node.get("kind") == "Assign"
            and isinstance(node.get("target"), dict)
            and node["target"].get("id") == "path_obj"
        )
        self.assertEqual(text_assign.get("decl_type"), "str")
        self.assertEqual(path_assign.get("decl_type"), "Path")

    def test_registry_driven_resolution_covers_builtins_stdlib_and_forrange(self) -> None:
        source = """
from pytra.std import json, random
from pytra.std.pathlib import Path

def f(xs: list[int], ys: list[str], text: str) -> None:
    a = sorted(xs)
    b = zip(xs, ys)
    c = json.loads(text)
    d = random.randint(1, 2)
    p = Path("x")
    for i in range(3):
        pass
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())

        sorted_call = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Name"
            and node["func"].get("id") == "sorted"
        )
        zip_call = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Name"
            and node["func"].get("id") == "zip"
        )
        json_call = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Attribute"
            and isinstance(node["func"].get("value"), dict)
            and node["func"]["value"].get("kind") == "Name"
            and node["func"]["value"].get("id") == "json"
            and node["func"].get("attr") == "loads"
        )
        randint_call = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Attribute"
            and isinstance(node["func"].get("value"), dict)
            and node["func"]["value"].get("kind") == "Name"
            and node["func"]["value"].get("id") == "random"
            and node["func"].get("attr") == "randint"
        )
        path_call = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Name"
            and node["func"].get("id") == "Path"
        )
        for_range = next(node for node in _walk(east2) if node.get("kind") == "ForRange")

        self.assertEqual(sorted_call.get("resolved_type"), "list[int64]")
        self.assertEqual(zip_call.get("resolved_type"), "list[tuple[int64,str]]")
        self.assertEqual(json_call.get("resolved_type"), "JsonValue")
        self.assertEqual(json_call.get("runtime_module_id"), "pytra.std.json")
        self.assertEqual(randint_call.get("resolved_type"), "int64")
        self.assertEqual(randint_call.get("runtime_module_id"), "pytra.std.random")
        self.assertEqual(path_call.get("resolved_type"), "Path")
        self.assertEqual(for_range.get("target_type"), "int64")
        self.assertEqual(for_range.get("target", {}).get("resolved_type"), "int64")

    def test_resolver_annotates_module_attr_runtime_metadata_for_extern_values(self) -> None:
        source = """
from pytra.std import math

def f() -> float:
    return math.pi
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())

        math_pi = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "Attribute"
            and node.get("attr") == "pi"
            and isinstance(node.get("value"), dict)
            and node["value"].get("kind") == "Name"
            and node["value"].get("id") == "math"
        )

        self.assertEqual(math_pi.get("resolved_type"), "float64")
        self.assertEqual(math_pi.get("runtime_module_id"), "pytra.std.math")
        self.assertEqual(math_pi.get("runtime_symbol"), "pi")
        self.assertEqual(math_pi.get("runtime_symbol_dispatch"), "value")

    def test_resolver_propagates_extern_call_argument_type(self) -> None:
        source = """
import sys
from pytra.std import extern

stdout = extern(sys.stdout)
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(deep_copy_json(east2))

        stdout_assign = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "Assign"
            and isinstance(node.get("target"), dict)
            and node["target"].get("id") == "stdout"
        )

        self.assertEqual(stdout_assign.get("decl_type"), "str")
        self.assertEqual(stdout_assign.get("value", {}).get("resolved_type"), "str")

    def test_bound_method_call_keeps_only_explicit_args_even_with_same_named_free_function(self) -> None:
        source = """
class C:
    def group(self, idx: int = 0) -> int:
        return idx

def group(m: C | None, idx: int = 0) -> int:
    if m is None:
        return 0
    mm: C = m
    return mm.group(idx)
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(deep_copy_json(east2))

        bound_call = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "Call" and node.get("repr") == "mm.group(idx)"
        )

        self.assertEqual(len(bound_call.get("args", [])), 1)

    def test_class_constructor_hints_empty_list_literals_from_signature(self) -> None:
        source = """
class Match:
    def __init__(self, text: str, groups: list[str]) -> None:
        self.text = text
        self.groups = groups

def f(text: str) -> Match:
    return Match(text, [])
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(deep_copy_json(east2))

        ctor_call = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "Call" and node.get("repr") == "Match(text, [])"
        )
        list_arg = ctor_call.get("args", [])[1]

        self.assertIsInstance(list_arg, dict)
        self.assertEqual(list_arg.get("resolved_type"), "list[str]")

    def test_resolver_recognizes_builtin_type_objects_in_value_position(self) -> None:
        source = """
int8 = int
float64 = float
Obj = object
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(deep_copy_json(east2))

        assigns = {
            node["target"]["id"]: node
            for node in _walk(east3)
            if node.get("kind") == "Assign"
            and isinstance(node.get("target"), dict)
            and isinstance(node["target"].get("id"), str)
        }

        self.assertEqual(assigns["int8"].get("decl_type"), "type")
        self.assertEqual(assigns["int8"].get("value", {}).get("resolved_type"), "type")
        self.assertEqual(assigns["float64"].get("decl_type"), "type")
        self.assertEqual(assigns["Obj"].get("decl_type"), "type")

    def test_registry_loads_runtime_builtins_and_tuple_target_comprehensions(self) -> None:
        registry = _load_registry()
        sum_sig = registry.lookup_function("sum")

        self.assertIsNotNone(sum_sig)
        self.assertEqual(sum_sig.return_type, "T")

        source = """
def linear(x: list[float], w: list[list[float]]) -> list[float]:
    return [sum(wi * xi for wi, xi in zip(wo, x)) for wo in w]
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=registry)

        linear_fn = next(
            node for node in _walk(east2)
            if node.get("kind") == "FunctionDef" and node.get("name") == "linear"
        )
        sum_call = next(
            node
            for node in _walk(linear_fn)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Name"
            and node["func"].get("id") == "sum"
        )
        wi_nodes = [
            node for node in _walk(linear_fn)
            if node.get("kind") == "Name" and node.get("id") == "wi"
        ]
        xi_nodes = [
            node for node in _walk(linear_fn)
            if node.get("kind") == "Name" and node.get("id") == "xi"
        ]

        self.assertEqual(linear_fn.get("return_type"), "list[float64]")
        self.assertEqual(sum_call.get("lowered_kind"), "BuiltinCall")
        self.assertEqual(sum_call.get("resolved_type"), "float64")
        self.assertTrue(wi_nodes)
        self.assertTrue(xi_nodes)
        self.assertTrue(all(node.get("resolved_type") == "float64" for node in wi_nodes))
        self.assertTrue(all(node.get("resolved_type") == "float64" for node in xi_nodes))

    def test_resolve_requires_registry(self) -> None:
        east1 = parse_python_source("def f() -> None:\n    pass\n", "<mem>").to_jv()
        with self.assertRaisesRegex(ValueError, "registry is required"):
            resolve_east1_to_east2(east1, registry=None)

    def test_resolver_keeps_pathlib_methods_transpilable_and_resolves_with_body(self) -> None:
        source = """
from pytra.std.pathlib import Path

def f(p: Path) -> str:
    p.write_text("42")
    with open("out.bin", "wb") as fh:
        fh.write(bytes(bytearray([1, 2, 3])))
    return p.read_text()
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())

        write_call = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Attribute"
            and node["func"].get("attr") == "write_text"
        )
        read_call = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Attribute"
            and node["func"].get("attr") == "read_text"
        )
        with_node = next(node for node in _walk(east2) if node.get("kind") == "With")
        with_body_call = with_node["body"][0]["value"]
        file_name = with_body_call["func"]["value"]

        self.assertNotEqual(write_call.get("lowered_kind"), "BuiltinCall")
        self.assertNotEqual(read_call.get("lowered_kind"), "BuiltinCall")
        self.assertEqual(with_node.get("context_expr", {}).get("kind"), "Call")
        self.assertEqual(with_node.get("context_expr", {}).get("resolved_type"), "PyFile")
        self.assertEqual(with_node.get("context_expr", {}).get("args", [])[0].get("resolved_type"), "str")
        self.assertEqual(file_name.get("resolved_type"), "PyFile")
        self.assertEqual(with_body_call.get("resolved_type"), "int64")
        self.assertEqual(with_body_call.get("args", [])[0].get("resolved_type"), "bytes")

    def test_resolver_keeps_builtin_calls_lowered_when_registry_also_has_runtime_helpers(self) -> None:
        source = """
def py_find_window(s: str) -> int:
    return len(s)

def run(s: str) -> int:
    return py_find_window(s)
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())

        len_call = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Name"
            and node["func"].get("id") == "len"
        )
        helper_call = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Name"
            and node["func"].get("id") == "py_find_window"
        )

        self.assertEqual(len_call.get("lowered_kind"), "BuiltinCall")
        self.assertEqual(len_call.get("builtin_name"), "len")
        self.assertEqual(len_call.get("runtime_call"), "len")
        self.assertEqual(len_call.get("runtime_module_id"), "pytra.core.py_runtime")
        self.assertNotEqual(helper_call.get("lowered_kind"), "BuiltinCall")
        self.assertEqual(helper_call.get("resolved_type"), "int64")

    def test_resolver_lowers_builtin_str_before_registry_class_ctor_path(self) -> None:
        source = """
from pytra.std.pathlib import Path

def stringify(p: Path) -> str:
    return str(p)
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())

        str_call = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Name"
            and node["func"].get("id") == "str"
        )

        self.assertEqual(str_call.get("lowered_kind"), "BuiltinCall")
        self.assertEqual(str_call.get("builtin_name"), "str")
        self.assertEqual(str_call.get("runtime_call"), "py_to_string")
        self.assertEqual(str_call.get("runtime_module_id"), "pytra.core.py_runtime")
        self.assertEqual(str_call.get("runtime_call_adapter_kind"), "builtin")

    def test_resolver_marks_in_place_mutation_params_as_reassigned(self) -> None:
        source = """
def append_all(dst: bytearray, src: bytearray) -> None:
    i = 0
    while i < len(src):
        dst.append(src[i])
        i += 1
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())

        fn = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "FunctionDef" and node.get("name") == "append_all"
        )

        self.assertEqual(fn.get("arg_usage", {}).get("dst"), "reassigned")
        self.assertEqual(fn.get("arg_usage", {}).get("src"), "readonly")

    def test_resolver_attaches_runtime_metadata_for_stdlib_class_methods(self) -> None:
        source = """
from pytra.std.pathlib import Path

def exists_here(p: Path) -> bool:
    return p.exists()
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())

        exists_call = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "Call"
            and node.get("repr") == "p.exists()"
        )

        self.assertEqual(exists_call.get("resolved_runtime_call"), "Path.exists")
        self.assertEqual(exists_call.get("runtime_call"), "Path.exists")
        self.assertEqual(exists_call.get("runtime_module_id"), "pytra.std.pathlib")
        self.assertEqual(exists_call.get("runtime_symbol"), "Path.exists")

    def test_boolop_value_select_preserves_operand_type(self) -> None:
        source = """
def f() -> None:
    x: str = ""
    y: str = "fallback"
    z: str = x or y
    n: int = 0
    m: int = 9
    t: int = n or m
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())

        boolops = [node for node in _walk(east2) if node.get("kind") == "BoolOp"]
        self.assertEqual(len(boolops), 2)
        self.assertEqual(boolops[0].get("resolved_type"), "str")
        self.assertEqual(boolops[1].get("resolved_type"), "int64")

    def test_ann_assign_does_not_rewrite_any_annotated_value_type(self) -> None:
        source = """
from pytra.typing import Any

def f() -> None:
    values: list[Any] = [1, 2]
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())

        ann_assign = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "AnnAssign"
            and isinstance(node.get("target"), dict)
            and node["target"].get("id") == "values"
        )

        self.assertEqual(ann_assign.get("decl_type"), "list[Any]")
        self.assertEqual(ann_assign.get("value", {}).get("resolved_type"), "list[int64]")

        east3 = lower_east2_to_east3(east2)
        ann_assign3 = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "AnnAssign"
            and isinstance(node.get("target"), dict)
            and node["target"].get("id") == "values"
        )
        self.assertEqual(ann_assign3.get("value", {}).get("kind"), "Box")
        self.assertEqual(ann_assign3.get("value", {}).get("target"), "list[Any]")

    def test_compile_uses_dynamic_target_resolved_type_for_cpp_box(self) -> None:
        source = """
from pytra.typing import Any

def f() -> None:
    values: list[Any] = [1, 2]
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(east2, target_language="cpp")

        ann_assign3 = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "AnnAssign"
            and isinstance(node.get("target"), dict)
            and node["target"].get("id") == "values"
        )
        boxed = ann_assign3.get("value", {})

        self.assertEqual(boxed.get("kind"), "Box")
        self.assertEqual(boxed.get("target"), "list[Any]")
        self.assertEqual(boxed.get("resolved_type"), "list[Any]")

    def test_compile_inserts_unbox_for_yields_dynamic_assignment_targets(self) -> None:
        source = """
from pytra.typing import Any

def f(root: dict[str, Any]) -> int:
    meta: dict[str, Any] = root.get("meta", {})
    total: int = 0
    for _k, v in meta.items():
        total += v
    return total
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(east2)

        meta_assign = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "AnnAssign"
            and isinstance(node.get("target"), dict)
            and node["target"].get("id") == "meta"
        )
        total_aug = next(node for node in _walk(east3) if node.get("kind") == "AugAssign")

        self.assertEqual(meta_assign.get("value", {}).get("kind"), "Unbox")
        self.assertEqual(meta_assign.get("value", {}).get("target"), "dict[str,Any]")
        self.assertEqual(total_aug.get("value", {}).get("kind"), "Unbox")
        self.assertEqual(total_aug.get("value", {}).get("target"), "int64")

    def test_compile_keeps_optional_unbox_boundary_for_dict_get_without_default(self) -> None:
        source = """
def f(d: dict[str, int]) -> bool:
    g: int | None = d.get("x")
    return g is not None
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(east2)

        g_assign = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "AnnAssign"
            and isinstance(node.get("target"), dict)
            and node["target"].get("id") == "g"
        )

        self.assertEqual(g_assign.get("decl_type"), "int64 | None")
        self.assertEqual(g_assign.get("value", {}).get("kind"), "Unbox")
        self.assertEqual(g_assign.get("value", {}).get("target"), "int64 | None")
        self.assertTrue(g_assign.get("value", {}).get("value", {}).get("yields_dynamic"))

    def test_compile_inserts_static_cast_for_scalar_ann_assign(self) -> None:
        source = """
def f() -> float:
    n: int = 3
    x: float = n
    return x
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(east2)

        x_assign = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "AnnAssign"
            and isinstance(node.get("target"), dict)
            and node["target"].get("id") == "x"
        )
        cast_call = x_assign.get("value", {})

        self.assertEqual(cast_call.get("kind"), "Call")
        self.assertEqual(cast_call.get("lowered_kind"), "BuiltinCall")
        self.assertEqual(cast_call.get("runtime_call"), "static_cast")
        self.assertEqual(cast_call.get("resolved_type"), "float64")
        self.assertEqual(cast_call.get("args", [])[0].get("id"), "n")

    def test_compile_inserts_static_cast_for_local_call_args(self) -> None:
        source = """
def takes_float(x: float) -> float:
    return x

def f() -> float:
    n: int = 3
    return takes_float(n)
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(east2)

        local_call = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Name"
            and node["func"].get("id") == "takes_float"
        )
        cast_arg = local_call.get("args", [])[0]

        self.assertEqual(cast_arg.get("kind"), "Call")
        self.assertEqual(cast_arg.get("lowered_kind"), "BuiltinCall")
        self.assertEqual(cast_arg.get("runtime_call"), "static_cast")
        self.assertEqual(cast_arg.get("resolved_type"), "float64")
        self.assertEqual(cast_arg.get("args", [])[0].get("id"), "n")

    def test_compile_inserts_static_cast_for_scalar_aug_assign(self) -> None:
        source = """
def f() -> float:
    total: float = 0.0
    n: int = 3
    total += n
    return total
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(east2)

        aug_assign = next(node for node in _walk(east3) if node.get("kind") == "AugAssign")
        cast_value = aug_assign.get("value", {})

        self.assertEqual(cast_value.get("kind"), "Call")
        self.assertEqual(cast_value.get("lowered_kind"), "BuiltinCall")
        self.assertEqual(cast_value.get("runtime_call"), "static_cast")
        self.assertEqual(cast_value.get("resolved_type"), "float64")
        self.assertEqual(cast_value.get("args", [])[0].get("id"), "n")

    def test_compile_inserts_static_cast_for_dict_get_default(self) -> None:
        source = """
def f(d: dict[str, float]) -> float:
    return d.get("x", 0)
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(east2)

        dict_get = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "Call" and node.get("runtime_call") == "dict.get"
        )
        default_arg = dict_get.get("args", [])[1]

        self.assertEqual(default_arg.get("kind"), "Call")
        self.assertEqual(default_arg.get("lowered_kind"), "BuiltinCall")
        self.assertEqual(default_arg.get("runtime_call"), "static_cast")
        self.assertEqual(default_arg.get("resolved_type"), "float64")
        self.assertEqual(default_arg.get("args", [])[0].get("value"), 0)

    def test_compile_wraps_dict_literal_entries_for_return_type(self) -> None:
        source = """
def f() -> dict[str, float]:
    return {"x": 0}
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(east2)

        return_stmt = next(node for node in _walk(east3) if node.get("kind") == "Return")
        dict_value = return_stmt.get("value", {})
        entry_value = dict_value.get("entries", [])[0].get("value", {})

        self.assertEqual(dict_value.get("kind"), "Dict")
        self.assertEqual(dict_value.get("resolved_type"), "dict[str,float64]")
        self.assertEqual(entry_value.get("kind"), "Call")
        self.assertEqual(entry_value.get("lowered_kind"), "BuiltinCall")
        self.assertEqual(entry_value.get("runtime_call"), "static_cast")
        self.assertEqual(entry_value.get("resolved_type"), "float64")

    def test_compile_wraps_list_literal_elements_for_return_type(self) -> None:
        source = """
def f() -> list[float]:
    return [0]
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(east2)

        return_stmt = next(node for node in _walk(east3) if node.get("kind") == "Return")
        list_value = return_stmt.get("value", {})
        element_value = list_value.get("elements", [])[0]

        self.assertEqual(list_value.get("kind"), "List")
        self.assertEqual(list_value.get("resolved_type"), "list[float64]")
        self.assertEqual(element_value.get("kind"), "Call")
        self.assertEqual(element_value.get("lowered_kind"), "BuiltinCall")
        self.assertEqual(element_value.get("runtime_call"), "static_cast")
        self.assertEqual(element_value.get("resolved_type"), "float64")

    def test_compile_inserts_static_cast_for_optional_return_inner_type(self) -> None:
        source = """
def f(flag: bool) -> float | None:
    if flag:
        return 1
    return None
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(east2)

        cast_return = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "Return"
            and isinstance(node.get("value"), dict)
            and node["value"].get("kind") == "Call"
        )
        cast_value = cast_return.get("value", {})

        self.assertEqual(cast_value.get("lowered_kind"), "BuiltinCall")
        self.assertEqual(cast_value.get("runtime_call"), "static_cast")
        self.assertEqual(cast_value.get("resolved_type"), "float64")
        self.assertEqual(cast_value.get("args", [])[0].get("value"), 1)

    def test_compile_keeps_iter_boundary_for_core_target(self) -> None:
        east2 = {
            "kind": "Module",
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "f",
                    "arg_types": {"xs": "Any"},
                    "arg_order": ["xs"],
                    "arg_defaults": {},
                    "arg_usage": {"xs": "readonly"},
                    "return_type": "Any",
                    "body": [
                        {
                            "kind": "Return",
                            "value": {
                                "kind": "Call",
                                "lowered_kind": "BuiltinCall",
                                "runtime_call": "py_iter_or_raise",
                                "semantic_tag": "iter.init",
                                "resolved_type": "unknown",
                                "func": {"kind": "Name", "id": "iter", "resolved_type": "unknown"},
                                "args": [{"kind": "Name", "id": "xs", "resolved_type": "Any"}],
                                "keywords": [],
                            },
                        }
                    ],
                }
            ],
        }
        east3 = lower_east2_to_east3(east2, target_language="core")

        return_stmt = next(node for node in _walk(east3) if node.get("kind") == "Return")
        value = return_stmt.get("value", {})

        self.assertEqual(value.get("kind"), "ObjIterInit")
        self.assertEqual(value.get("resolved_type"), "object")

    def test_compile_skips_iter_boundary_for_cpp_target(self) -> None:
        east2 = {
            "kind": "Module",
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "f",
                    "arg_types": {"xs": "Any"},
                    "arg_order": ["xs"],
                    "arg_defaults": {},
                    "arg_usage": {"xs": "readonly"},
                    "return_type": "Any",
                    "body": [
                        {
                            "kind": "Return",
                            "value": {
                                "kind": "Call",
                                "lowered_kind": "BuiltinCall",
                                "runtime_call": "py_iter_or_raise",
                                "semantic_tag": "iter.init",
                                "resolved_type": "unknown",
                                "func": {"kind": "Name", "id": "iter", "resolved_type": "unknown"},
                                "args": [{"kind": "Name", "id": "xs", "resolved_type": "Any"}],
                                "keywords": [],
                            },
                        }
                    ],
                }
            ],
        }
        east3 = lower_east2_to_east3(east2, target_language="cpp")

        return_stmt = next(node for node in _walk(east3) if node.get("kind") == "Return")
        value = return_stmt.get("value", {})

        self.assertEqual(value.get("kind"), "Call")
        self.assertEqual(value.get("runtime_call"), "py_iter_or_raise")

    def test_compile_narrows_union_names_inside_isinstance_guard(self) -> None:
        source = """
type Scalar = int | float

def add_scalars(a: Scalar, b: Scalar) -> int:
    if isinstance(a, int) and isinstance(b, int):
        return a + b
    return 0
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(east2)

        guarded_return = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "Return"
            and isinstance(node.get("value"), dict)
            and node["value"].get("kind") == "BinOp"
        )
        binop = guarded_return["value"]
        left = binop.get("left", {})
        right = binop.get("right", {})

        self.assertEqual(left.get("kind"), "Name")
        self.assertEqual(left.get("resolved_type"), "int64")
        self.assertEqual(right.get("kind"), "Name")
        self.assertEqual(right.get("resolved_type"), "int64")
        self.assertEqual(binop.get("resolved_type"), "int64")

    def test_guard_narrowing_sees_through_unbox_wrapped_isinstance_subject(self) -> None:
        module = {
            "kind": "Module",
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "f",
                    "arg_types": {"v": "list[Any] | dict[str,Any]"},
                    "arg_order": ["v"],
                    "arg_defaults": {},
                    "arg_index": {"v": 0},
                    "return_type": "list[Any]",
                    "arg_usage": {"v": "readonly"},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "If",
                            "test": {
                                "kind": "IsInstance",
                                "value": {
                                    "kind": "Unbox",
                                    "value": {
                                        "kind": "Name",
                                        "id": "v",
                                        "resolved_type": "list[Any] | dict[str,Any]",
                                    },
                                    "resolved_type": "list[Any] | dict[str,Any]",
                                    "target": "list[Any] | dict[str,Any]",
                                },
                                "expected_type_id": {"kind": "Name", "id": "PYTRA_TID_LIST"},
                            },
                            "body": [
                                {
                                    "kind": "Return",
                                    "value": {
                                        "kind": "Name",
                                        "id": "v",
                                        "resolved_type": "list[Any] | dict[str,Any]",
                                    },
                                }
                            ],
                            "orelse": [],
                        }
                    ],
                }
            ],
            "main_guard_body": [],
        }

        apply_guard_narrowing(module, CompileContext())

        guarded_return = module["body"][0]["body"][0]["body"][0]["value"]
        self.assertEqual(guarded_return.get("kind"), "Unbox")

    def test_compile_lowers_pod_isinstance_to_exact_type_names(self) -> None:
        source = """
def f(x16: int16, x64: int64, f32: float32) -> None:
    print(isinstance(x16, int16))
    print(isinstance(x64, int))
    print(isinstance(f32, float32))
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(deep_copy_json(east2))

        expected_names: list[str] = []
        for node in _walk(east3):
            if node.get("kind") != "IsInstance":
                continue
            expected = node.get("expected_type_id")
            if isinstance(expected, dict):
                expected_name = expected.get("id")
                if isinstance(expected_name, str):
                    expected_names.append(expected_name)

        self.assertEqual(expected_names, ["int16", "int64", "float32"])

    def test_guard_narrowing_uses_exact_pod_names(self) -> None:
        module = {
            "kind": "Module",
            "body": [
                {
                    "kind": "If",
                    "test": {
                        "kind": "IsInstance",
                        "value": {"kind": "Name", "id": "x", "resolved_type": "int16 | int64"},
                        "expected_type_id": {"kind": "Name", "id": "int16"},
                        "resolved_type": "bool",
                    },
                    "body": [
                        {
                            "kind": "Return",
                            "value": {"kind": "Name", "id": "x", "resolved_type": "int16 | int64"},
                        }
                    ],
                    "orelse": [],
                }
            ],
        }

        apply_guard_narrowing(module, CompileContext())

        guarded_return = module["body"][0]["body"][0]["value"]
        self.assertEqual(guarded_return.get("resolved_type"), "int16")

    def test_compile_boxes_imported_stdlib_alias_arguments(self) -> None:
        source = """
from pytra.std.json import dumps

def f() -> str:
    return dumps(123)
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(east2)

        dumps_call = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Name"
            and node["func"].get("id") == "dumps"
        )
        boxed_arg = dumps_call.get("args", [])[0]

        self.assertEqual(boxed_arg.get("kind"), "Box")
        self.assertEqual(boxed_arg.get("target"), "bool|int64|float64|str|list[Any]|dict[str,Any]|None")
        self.assertEqual(boxed_arg.get("value", {}).get("resolved_type"), "int64")

    def test_compile_uses_union_target_resolved_type_for_cpp_box(self) -> None:
        source = """
from pytra.std.json import dumps

def f() -> str:
    return dumps(1)
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(east2, target_language="cpp")

        dumps_call = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Name"
            and node["func"].get("id") == "dumps"
        )
        boxed_arg = dumps_call.get("args", [])[0]

        self.assertEqual(boxed_arg.get("kind"), "Box")
        self.assertEqual(boxed_arg.get("target"), "bool|int64|float64|str|list[Any]|dict[str,Any]|None")
        self.assertEqual(boxed_arg.get("resolved_type"), "bool|int64|float64|str|list[Any]|dict[str,Any]|None")

    def test_compile_cpp_lowering_avoids_object_resolved_type_for_representative_dynamic_cases(self) -> None:
        east2 = {
            "kind": "Module",
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "f",
                    "arg_types": {"xs": "Any"},
                    "arg_order": ["xs"],
                    "arg_defaults": {},
                    "arg_usage": {"xs": "readonly"},
                    "return_type": "Any",
                    "body": [
                        {
                            "kind": "AnnAssign",
                            "target": {"kind": "Name", "id": "values"},
                            "decl_type": "list[Any]",
                            "value": {
                                "kind": "List",
                                "resolved_type": "list[int64]",
                                "elements": [
                                    {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                                    {"kind": "Constant", "value": 2, "resolved_type": "int64"},
                                ],
                            },
                            "resolved_type": "None",
                        },
                        {
                            "kind": "Return",
                            "value": {
                                "kind": "Call",
                                "lowered_kind": "BuiltinCall",
                                "runtime_call": "py_iter_or_raise",
                                "semantic_tag": "iter.init",
                                "resolved_type": "unknown",
                                "func": {"kind": "Name", "id": "iter", "resolved_type": "unknown"},
                                "args": [{"kind": "Name", "id": "xs", "resolved_type": "Any"}],
                                "keywords": [],
                            },
                        },
                    ],
                }
            ],
        }

        east3 = lower_east2_to_east3(east2, target_language="cpp")
        object_nodes = [
            node
            for node in _walk(east3)
            if isinstance(node, dict) and node.get("resolved_type") == "object"
        ]

        self.assertEqual(object_nodes, [])

    def test_compile_preserves_tuple_unpack_value_type_for_static_tuple_calls(self) -> None:
        source = """
def pair() -> tuple[int, int]:
    return 1, 2

def f() -> int:
    x, y = pair()
    return x + y
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(east2)

        tmp_assign = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "Assign"
            and isinstance(node.get("target"), dict)
            and node["target"].get("id") == "__tup_1"
        )
        x_assign = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "Assign"
            and isinstance(node.get("target"), dict)
            and node["target"].get("id") == "x"
        )

        self.assertEqual(tmp_assign.get("decl_type"), "tuple[int64,int64]")
        self.assertEqual(tmp_assign.get("value", {}).get("kind"), "Call")
        self.assertEqual(x_assign.get("decl_type"), "int64")
        self.assertEqual(x_assign.get("value", {}).get("resolved_type"), "int64")

    def test_compile_lowers_isinstance_object_to_true_without_type_id_object(self) -> None:
        source = """
def f(x: int) -> bool:
    return isinstance(x, object)
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(east2, target_language="cpp")

        return_nodes = [node for node in _walk(east3) if node.get("kind") == "Return"]
        self.assertEqual(len(return_nodes), 1)
        value = return_nodes[0].get("value")
        self.assertIsInstance(value, dict)
        self.assertEqual(value.get("kind"), "Constant")
        self.assertEqual(value.get("value"), True)
        self.assertFalse(any(node.get("id") == "PYTRA_TID_OBJECT" for node in _walk(east3)))

    def test_compile_lowers_issubclass_object_to_true_without_type_id_object(self) -> None:
        source = """
class A:
    pass

def f() -> bool:
    return issubclass(A, object)
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(east2, target_language="cpp")

        return_nodes = [node for node in _walk(east3) if node.get("kind") == "Return"]
        target = next(node for node in return_nodes if isinstance(node.get("value"), dict))
        value = target.get("value")
        self.assertIsInstance(value, dict)
        self.assertEqual(value.get("kind"), "Constant")
        self.assertEqual(value.get("value"), True)
        self.assertFalse(any(node.get("id") == "PYTRA_TID_OBJECT" for node in _walk(east3)))

    def test_compile_unboxes_optional_tuple_before_unpack(self) -> None:
        source = """
def f(separators: tuple[str, str] | None) -> str:
    item_sep = ","
    key_sep = ":"
    if separators is not None:
        item_sep, key_sep = separators
    return item_sep + key_sep
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(deep_copy_json(east2))

        tmp_assign = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "Assign"
            and isinstance(node.get("target"), dict)
            and node["target"].get("id") == "__tup_1"
        )
        item_assign = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "Assign"
            and isinstance(node.get("target"), dict)
            and node["target"].get("id") == "item_sep"
            and node.get("decl_type") == "str"
            and isinstance(node.get("value"), dict)
            and node["value"].get("kind") == "Subscript"
        )
        key_assign = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "Assign"
            and isinstance(node.get("target"), dict)
            and node["target"].get("id") == "key_sep"
            and node.get("decl_type") == "str"
            and isinstance(node.get("value"), dict)
            and node["value"].get("kind") == "Subscript"
        )

        self.assertEqual(tmp_assign.get("value", {}).get("kind"), "Name")
        self.assertEqual(tmp_assign.get("value", {}).get("resolved_type"), "tuple[str,str]")
        self.assertEqual(item_assign.get("value", {}).get("resolved_type"), "str")
        self.assertEqual(key_assign.get("value", {}).get("resolved_type"), "str")

    def test_compile_casts_string_index_to_byte_target(self) -> None:
        source = """
def f(s: str, i: int) -> None:
    ch: byte = s[i]
    print(ch == 66)
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(deep_copy_json(east2))

        ch_assign = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "AnnAssign"
            and isinstance(node.get("target"), dict)
            and node["target"].get("id") == "ch"
        )
        value = ch_assign.get("value")

        self.assertEqual(ch_assign.get("decl_type"), "str")
        self.assertEqual(ch_assign.get("decl_type_expr"), {"kind": "NamedType", "name": "str"})
        self.assertIsInstance(ch_assign.get("target"), dict)
        self.assertEqual(ch_assign["target"].get("resolved_type"), "str")
        self.assertEqual(ch_assign["target"].get("type_expr"), {"kind": "NamedType", "name": "str"})
        self.assertIsInstance(value, dict)
        self.assertEqual(value.get("kind"), "Subscript")
        self.assertEqual(value.get("resolved_type"), "str")

    def test_resolver_sets_for_loop_target_types_for_strings_and_bytes(self) -> None:
        source = """
def f(b: bytes, ba: bytearray, s: str) -> None:
    for vb in b:
        print(vb)
    for vba in ba:
        print(vba)
    for ch in s:
        print(ch)
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())

        for_nodes = [node for node in _walk(east2) if node.get("kind") == "For"]
        self.assertEqual(len(for_nodes), 3)

        bytes_for = for_nodes[0]
        bytearray_for = for_nodes[1]
        str_for = for_nodes[2]

        self.assertEqual(bytes_for.get("target_type"), "int64")
        self.assertEqual(bytes_for.get("iter_element_type"), "int64")
        self.assertEqual(bytes_for.get("target", {}).get("resolved_type"), "int64")

        self.assertEqual(bytearray_for.get("target_type"), "int64")
        self.assertEqual(bytearray_for.get("iter_element_type"), "int64")
        self.assertEqual(bytearray_for.get("target", {}).get("resolved_type"), "int64")

        self.assertEqual(str_for.get("target_type"), "str")
        self.assertEqual(str_for.get("iter_element_type"), "str")
        self.assertEqual(str_for.get("target", {}).get("resolved_type"), "str")

    def test_resolver_refines_lambda_args_from_calls_and_defaults(self) -> None:
        source = """
def f() -> tuple[int, float]:
    direct: int = (lambda x, y: x + y)(4, 5)
    matrix = lambda nout, nin, std=0.08: nout + nin * std
    return direct, matrix(1, 2)
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())

        lambdas = [node for node in _walk(east2) if node.get("kind") == "Lambda"]
        direct_lambda = lambdas[0]
        named_lambda = lambdas[1]
        direct_call = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Lambda"
        )
        named_call = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Name"
            and node["func"].get("id") == "matrix"
        )

        self.assertEqual(direct_lambda.get("arg_types"), {"x": "int64", "y": "int64"})
        self.assertEqual(direct_lambda.get("return_type"), "int64")
        self.assertEqual(direct_call.get("resolved_type"), "int64")

        self.assertEqual(named_lambda.get("arg_types", {}).get("std"), "float64")
        self.assertEqual(named_lambda.get("return_type"), "float64")
        self.assertEqual(named_call.get("resolved_type"), "float64")

    def test_compile_expands_defaults_for_lambda_assigned_to_name(self) -> None:
        source = """
def f() -> None:
    matrix = lambda nout, nin, std=0.08: nout + nin * std
    print(matrix(1, 2))
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        validate_east2(east2)

        east3 = lower_east2_to_east3(deep_copy_json(east2))
        matrix_call = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Name"
            and node["func"].get("id") == "matrix"
        )

        self.assertEqual(len(matrix_call.get("args", [])), 3)
        self.assertEqual(matrix_call.get("args", [])[2].get("resolved_type"), "float64")

    def test_resolver_substitutes_container_method_arg_hints(self) -> None:
        source = """
def f() -> None:
    keys: list[list[int]] = []
    keys.append([])
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())

        append_call = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Attribute"
            and node["func"].get("attr") == "append"
        )
        append_arg = append_call.get("args", [])[0]

        self.assertEqual(append_arg.get("resolved_type"), "list[int64]")
        self.assertEqual(append_arg.get("call_arg_type"), "list[int64]")

    def test_resolver_loads_utils_registry_and_type_name_attribute(self) -> None:
        source = """
from pytra.utils.assertions import py_assert_eq

class Value:
    pass

def f(v: Value) -> bool:
    name = type(v).__name__
    return py_assert_eq(name, "Value", "type name")
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())

        type_name_attr = next(
            node for node in _walk(east2)
            if node.get("kind") == "Attribute" and node.get("attr") == "__name__"
        )
        assert_call = next(
            node
            for node in _walk(east2)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Name"
            and node["func"].get("id") == "py_assert_eq"
        )

        self.assertEqual(type_name_attr.get("resolved_type"), "str")
        self.assertEqual(assert_call.get("resolved_type"), "bool")

    def test_compile_preserves_nested_list_comp_element_type(self) -> None:
        source = """
def f(n_layer: int) -> list[list[int]]:
    keys: list[list[int]] = [[] for _ in range(n_layer)]
    return keys
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(deep_copy_json(east2))

        append_call = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "Call"
            and isinstance(node.get("func"), dict)
            and node["func"].get("kind") == "Attribute"
            and node["func"].get("attr") == "append"
        )
        append_arg = append_call.get("args", [])[0]

        self.assertEqual(append_arg.get("resolved_type"), "list[int64]")
        self.assertEqual(append_arg.get("call_arg_type"), "list[int64]")

    def test_compile_marks_closure_methods_that_mutate_self_transitively(self) -> None:
        source = """
class Parser:
    def __init__(self) -> None:
        self.pos: int = 0
        self.items: list[int] = []

    def match(self) -> bool:
        self.pos += 1
        return True

    def add(self, v: int) -> int:
        self.items.append(v)
        return len(self.items)

    def step(self, v: int) -> int:
        if self.match():
            return self.add(v)
        return 0
"""
        east2 = parse_python_source(source, "<mem>").to_jv()
        resolve_east1_to_east2(east2, registry=_load_registry())
        east3 = lower_east2_to_east3(deep_copy_json(east2))

        parser_class = next(
            node
            for node in _walk(east3)
            if node.get("kind") == "ClassDef" and node.get("name") == "Parser"
        )
        methods = {
            node.get("name"): node
            for node in parser_class.get("body", [])
            if isinstance(node, dict) and node.get("kind") == "ClosureDef"
        }

        self.assertTrue(methods["match"].get("mutates_self"))
        self.assertTrue(methods["add"].get("mutates_self"))
        self.assertTrue(methods["step"].get("mutates_self"))

    def test_validator_reports_unknown_missing_and_unnormalized_types(self) -> None:
        unknown_doc = {
            "kind": "Module",
            "east_stage": 2,
            "schema_version": 1,
            "source_path": "<unknown>",
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Name",
                        "id": "x",
                        "resolved_type": "unknown",
                    },
                }
            ],
        }
        missing_doc = {
            "kind": "Module",
            "east_stage": 2,
            "schema_version": 1,
            "source_path": "<missing>",
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Name",
                        "id": "x",
                    },
                }
            ],
        }
        range_doc = {
            "kind": "Module",
            "east_stage": 2,
            "schema_version": 1,
            "source_path": "<range>",
            "meta": {"dispatch_mode": "native"},
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "f",
                    "arg_types": {"x": "int"},
                    "arg_usage": {"x": "readonly"},
                    "arg_type_exprs": {"x": {"kind": "NamedType", "name": "int64"}},
                    "return_type": "float",
                    "return_type_expr": {"kind": "NamedType", "name": "float64"},
                    "body": [
                        {
                            "kind": "Expr",
                            "value": {
                                "kind": "RangeExpr",
                                "resolved_type": "list[int64]",
                                "start": {"kind": "Constant", "value": 0, "resolved_type": "int64"},
                                "stop": {"kind": "Constant", "value": 3, "resolved_type": "int64"},
                                "step": {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                            },
                        }
                    ],
                }
            ],
        }

        unknown_result = validate_east2(unknown_doc)
        missing_result = validate_east2(missing_doc)
        range_result = validate_east2(range_doc)

        self.assertTrue(any("resolved_type is unknown" in err for err in unknown_result.errors))
        self.assertTrue(any("missing resolved_type" in err for err in missing_result.errors))
        self.assertTrue(any("unnormalized type 'int'" in err for err in range_result.errors))
        self.assertTrue(any("unnormalized type 'float'" in err for err in range_result.errors))
        self.assertFalse(any("RangeExpr" in err for err in range_result.errors))


if __name__ == "__main__":
    unittest.main()
