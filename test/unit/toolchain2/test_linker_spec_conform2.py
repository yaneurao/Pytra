from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))


from toolchain2.link.linker import LinkedModule, link_modules
from toolchain2.link.expand_defaults import expand_cross_module_defaults
from toolchain2.link.manifest_loader import load_linked_output
from toolchain2.link.runtime_discovery import discover_runtime_modules
from toolchain2.link.type_id import build_type_id_table
from toolchain2.emit.go.emitter import emit_go_module
from toolchain2.emit.cpp.emitter import emit_cpp_module
from toolchain2.emit.common.code_emitter import RuntimeMapping


def _module_doc(
    module_id: str,
    *,
    source_path: str = "",
    body: list[dict[str, object]] | None = None,
    meta_extra: dict[str, object] | None = None,
) -> dict[str, object]:
    meta: dict[str, object] = {
        "module_id": module_id,
        "dispatch_mode": "native",
    }
    if meta_extra:
        meta.update(meta_extra)
    return {
        "kind": "Module",
        "east_stage": 3,
        "schema_version": 1,
        "source_path": source_path,
        "meta": meta,
        "body": body if body is not None else [],
    }


def _class_def(
    name: str,
    *,
    base: str | None = None,
    bases: list[str] | None = None,
) -> dict[str, object]:
    node: dict[str, object] = {
        "kind": "ClassDef",
        "name": name,
        "body": [],
    }
    if bases is not None:
        node["bases"] = bases
    else:
        node["base"] = base
    return node


def _linked_module(module_id: str, body: list[dict[str, object]]) -> LinkedModule:
    return LinkedModule(
        module_id=module_id,
        input_path=module_id.replace(".", "/") + ".east3.json",
        source_path=module_id.replace(".", "/") + ".py",
        is_entry=True,
        east_doc=_module_doc(module_id, body=body),
        module_kind="user",
    )


def _fixture_doc(relative_path: str) -> dict[str, object]:
    fixture_path = ROOT / relative_path
    return json.loads(fixture_path.read_text(encoding="utf-8"))


class Toolchain2LinkerSpecConform2Tests(unittest.TestCase):
    def test_type_id_builder_accepts_single_base_from_bases_array(self) -> None:
        modules = [
            _linked_module(
                "app.main",
                [
                    _class_def("Base"),
                    _class_def("Child", bases=["Base"]),
                ],
            )
        ]

        type_id_table, type_id_base_map, type_info_table = build_type_id_table(modules)

        self.assertIn("app.main.Base", type_id_table)
        self.assertIn("app.main.Child", type_id_table)
        self.assertEqual(type_id_base_map["app.main.Child"], type_id_table["app.main.Base"])
        self.assertEqual(type_info_table["app.main.Base"]["id"], type_id_table["app.main.Base"])

    def test_type_id_builder_rejects_multiple_inheritance(self) -> None:
        modules = [
            _linked_module(
                "app.main",
                [
                    _class_def("A"),
                    _class_def("B"),
                    _class_def("C", bases=["A", "B"]),
                ],
            )
        ]

        with self.assertRaisesRegex(RuntimeError, "multiple inheritance is not supported"):
            build_type_id_table(modules)

    def test_type_id_builder_rejects_undefined_base(self) -> None:
        modules = [
            _linked_module(
                "app.main",
                [
                    _class_def("Child", bases=["Missing"]),
                ],
            )
        ]

        with self.assertRaisesRegex(RuntimeError, "undefined base class"):
            build_type_id_table(modules)

    def test_type_id_builder_rejects_inheritance_cycle(self) -> None:
        modules = [
            _linked_module(
                "app.main",
                [
                    _class_def("A", bases=["B"]),
                    _class_def("B", bases=["A"]),
                ],
            )
        ]

        with self.assertRaisesRegex(RuntimeError, "inheritance cycle"):
            build_type_id_table(modules)

    def test_runtime_discovery_rejects_missing_explicit_runtime_module(self) -> None:
        module_map = {
            "/tmp/app.main.east3.json": _module_doc(
                "app.main",
                meta_extra={"import_bindings": [{"module_id": "pytra.std.missing"}]},
            )
        }

        with patch("toolchain2.link.runtime_discovery.resolve_runtime_east_path", return_value=""):
            with self.assertRaisesRegex(RuntimeError, "runtime EAST module not found"):
                discover_runtime_modules(module_map)

    def test_runtime_discovery_rejects_invalid_runtime_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad_runtime = Path(tmp) / "bad.east"
            bad_runtime.write_text("{bad json", encoding="utf-8")
            module_map = {
                "/tmp/app.main.east3.json": _module_doc(
                    "app.main",
                    meta_extra={"import_bindings": [{"module_id": "pytra.std.time"}]},
                )
            }

            with patch("toolchain2.link.runtime_discovery.resolve_runtime_east_path", return_value=str(bad_runtime)):
                with self.assertRaisesRegex(RuntimeError, "failed to parse runtime EAST"):
                    discover_runtime_modules(module_map)

    def test_runtime_discovery_allows_missing_speculative_runtime_submodule_probe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime_path = Path(tmp) / "assertions.east"
            runtime_path.write_text(
                json.dumps(
                    _module_doc("pytra.utils.assertions"),
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            module_map = {
                "/tmp/app.main.east3.json": _module_doc(
                    "app.main",
                    body=[
                        {
                            "kind": "ImportFrom",
                            "module": "pytra.utils.assertions",
                            "names": [{"name": "py_assert_all"}],
                        }
                    ],
                )
            }

            def _resolve(module_id: str) -> str:
                if module_id == "pytra.utils.assertions":
                    return str(runtime_path)
                if module_id == "pytra.utils.assertions.py_assert_all":
                    return ""
                return ""

            with patch("toolchain2.link.runtime_discovery.resolve_runtime_east_path", side_effect=_resolve):
                result = discover_runtime_modules(module_map)

            self.assertIn(str(runtime_path), result)

    def test_manifest_loader_rejects_invalid_module_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema": "pytra.link_output.v1",
                        "target": "cpp",
                        "dispatch_mode": "native",
                        "entry_modules": ["app.main"],
                        "modules": [
                            {
                                "module_id": "app.main",
                                "input": "raw/app.main.east3.json",
                                "source_path": "app/main.py",
                                "is_entry": True,
                                "module_kind": "user",
                            }
                        ],
                        "global": {
                            "type_id_table": {},
                            "type_id_base_map": {},
                            "call_graph": {},
                            "sccs": [],
                            "non_escape_summary": {},
                            "container_ownership_hints_v1": {},
                        },
                        "diagnostics": {"warnings": [], "errors": []},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RuntimeError, r"manifest\.modules\[0\]\.output must be non-empty string"):
                load_linked_output(manifest_path)

    def test_manifest_loader_rejects_missing_linked_east_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema": "pytra.link_output.v1",
                        "target": "cpp",
                        "dispatch_mode": "native",
                        "entry_modules": ["app.main"],
                        "modules": [
                            {
                                "module_id": "app.main",
                                "input": "raw/app.main.east3.json",
                                "output": "east3/app.main.east3.json",
                                "source_path": "app/main.py",
                                "is_entry": True,
                                "module_kind": "user",
                            }
                        ],
                        "global": {
                            "type_id_table": {},
                            "type_id_base_map": {},
                            "call_graph": {},
                            "sccs": [],
                            "non_escape_summary": {},
                            "container_ownership_hints_v1": {},
                        },
                        "diagnostics": {"warnings": [], "errors": []},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RuntimeError, "linked EAST file not found"):
                load_linked_output(manifest_path)

    def test_manifest_loader_rejects_invalid_linked_east_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            east_path = Path(tmp) / "east3" / "app.main.east3.json"
            east_path.parent.mkdir(parents=True, exist_ok=True)
            east_path.write_text("{bad json", encoding="utf-8")
            manifest_path = Path(tmp) / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema": "pytra.link_output.v1",
                        "target": "cpp",
                        "dispatch_mode": "native",
                        "entry_modules": ["app.main"],
                        "modules": [
                            {
                                "module_id": "app.main",
                                "input": "raw/app.main.east3.json",
                                "output": "east3/app.main.east3.json",
                                "source_path": "app/main.py",
                                "is_entry": True,
                                "module_kind": "user",
                            }
                        ],
                        "global": {
                            "type_id_table": {},
                            "type_id_base_map": {},
                            "call_graph": {},
                            "sccs": [],
                            "non_escape_summary": {},
                            "container_ownership_hints_v1": {},
                        },
                        "diagnostics": {"warnings": [], "errors": []},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RuntimeError, "failed to parse linked EAST file"):
                load_linked_output(manifest_path)

    def test_link_modules_manifest_input_points_to_raw_east3_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entry_path = Path(tmp) / "app.main.east3.json"
            entry_path.write_text(
                json.dumps(
                    _module_doc(
                        "app.main",
                        source_path="app/main.py",
                    ),
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = link_modules([str(entry_path)], target="cpp", dispatch_mode="native")

            modules = result.manifest.get("modules")
            self.assertIsInstance(modules, list)
            assert isinstance(modules, list)
            entry = next(item for item in modules if isinstance(item, dict) and item.get("module_id") == "app.main")
            self.assertEqual(entry.get("input"), str(entry_path.resolve()))
            self.assertEqual(entry.get("source_path"), "app/main.py")

    def test_expand_defaults_uses_same_module_qualified_name(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "foo",
                    "arg_order": ["x", "y"],
                    "arg_defaults": {
                        "y": {"kind": "Constant", "value": 2},
                    },
                    "body": [],
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "func": {"kind": "Name", "id": "foo"},
                        "args": [{"kind": "Constant", "value": 1}],
                    },
                },
            ],
        )

        expand_cross_module_defaults([doc])

        body = doc["body"]
        assert isinstance(body, list)
        call = body[1]["value"]
        self.assertEqual(len(call["args"]), 2)
        self.assertEqual(call["args"][1]["value"], 2)

    def test_expand_defaults_uses_imported_symbol_module_id(self) -> None:
        dep_doc = _module_doc(
            "pkg.dep",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "foo",
                    "arg_order": ["x", "y"],
                    "arg_defaults": {
                        "y": {"kind": "Constant", "value": 9},
                    },
                    "body": [],
                }
            ],
        )
        main_doc = _module_doc(
            "app.main",
            meta_extra={
                "import_symbols": {
                    "foo": {"module": "pkg.dep", "name": "foo"},
                }
            },
            body=[
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "func": {"kind": "Name", "id": "foo"},
                        "args": [{"kind": "Constant", "value": 1}],
                    },
                }
            ],
        )

        expand_cross_module_defaults([dep_doc, main_doc])

        body = main_doc["body"]
        assert isinstance(body, list)
        call = body[0]["value"]
        self.assertEqual(len(call["args"]), 2)
        self.assertEqual(call["args"][1]["value"], 9)

    def test_expand_defaults_does_not_expand_ambiguous_object_method_calls(self) -> None:
        doc_a = _module_doc(
            "pkg.a",
            body=[
                {
                    "kind": "ClassDef",
                    "name": "A",
                    "body": [
                        {
                            "kind": "FunctionDef",
                            "name": "run",
                            "arg_order": ["self", "x", "y"],
                            "arg_defaults": {
                                "y": {"kind": "Constant", "value": 1},
                            },
                            "body": [],
                        }
                    ],
                }
            ],
        )
        doc_b = _module_doc(
            "pkg.b",
            body=[
                {
                    "kind": "ClassDef",
                    "name": "B",
                    "body": [
                        {
                            "kind": "FunctionDef",
                            "name": "run",
                            "arg_order": ["self", "x", "y"],
                            "arg_defaults": {
                                "y": {"kind": "Constant", "value": 2},
                            },
                            "body": [],
                        }
                    ],
                }
            ],
        )
        main_doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "func": {
                            "kind": "Attribute",
                            "value": {"kind": "Name", "id": "obj"},
                            "attr": "run",
                        },
                        "args": [{"kind": "Constant", "value": 3}],
                    },
                }
            ],
        )

        expand_cross_module_defaults([doc_a, doc_b, main_doc])

        body = main_doc["body"]
        assert isinstance(body, list)
        call = body[0]["value"]
        self.assertEqual(len(call["args"]), 1)

    def test_emitters_consume_canonical_str_method_builtin_calls(self) -> None:
        doc = _fixture_doc("test/fixture/east3-opt/strings/str_methods.east3")

        go_code = emit_go_module(doc)
        cpp_code = emit_cpp_module(doc)

        self.assertIn("a := py_str_strip(s)", go_code)
        self.assertIn('j := py_str_join(":", parts)', go_code)
        self.assertIn("std::string a = py_str_strip(s);", cpp_code)
        self.assertIn('std::string j = py_str_join(std::string(":"), parts);', cpp_code)

    def test_go_emitter_handles_plain_set_constructor_without_link_normalization(self) -> None:
        doc = _fixture_doc("test/fixture/east3-opt/collections/nested_types.east3")

        go_code = emit_go_module(doc)

        self.assertIn("py_set()", go_code)

    def test_cpp_emitter_handles_plain_bytes_constructor_without_link_normalization(self) -> None:
        doc = _fixture_doc("test/fixture/east3-opt/typing/bytes_basic.east3")

        cpp_code = emit_cpp_module(doc)

        self.assertIn("std::vector<uint8_t>{uint8_t(1), uint8_t(2), uint8_t(3), uint8_t(255)}", cpp_code)
        self.assertNotIn("bytes(", cpp_code)

    def test_emitters_treat_runtime_call_int_as_cast_without_link_normalization(self) -> None:
        doc = _fixture_doc("test/fixture/east3-opt/typing/intenum_basic.east3")

        go_code = emit_go_module(doc)
        cpp_code = emit_cpp_module(doc)

        self.assertIn("int64(Status_ERROR)", go_code)
        self.assertNotIn("py_int(Status_ERROR)", go_code)
        self.assertIn("static_cast<int64_t>(Status.ERROR)", cpp_code)
        self.assertNotIn("py_int(Status.ERROR)", cpp_code)

    def test_go_emitter_runtime_symbol_prefix_uses_skip_modules_without_pytra_hardcode(self) -> None:
        doc = _module_doc(
            "app.main",
            meta_extra={
                "import_bindings": [
                    {
                        "module_id": "runtime.custom",
                        "local_name": "helper",
                        "binding_kind": "symbol",
                    }
                ]
            },
            body=[
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "func": {"kind": "Name", "id": "helper"},
                        "args": [],
                    },
                }
            ],
        )

        mapping = RuntimeMapping(
            builtin_prefix="rt_",
            calls={},
            skip_module_prefixes=["runtime."],
        )
        with patch("toolchain2.emit.go.emitter.load_runtime_mapping", return_value=mapping):
            go_code = emit_go_module(doc)

        self.assertIn("rt_helper()", go_code)

    def test_go_emitter_uses_runtime_metadata_for_skipped_module_values(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "run",
                    "arg_types": {},
                    "arg_order": [],
                    "arg_defaults": {},
                    "arg_index": {},
                    "return_type": "float64",
                    "arg_usage": {},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "Return",
                            "value": {
                                "kind": "Call",
                                "resolved_type": "float64",
                                "func": {
                                    "kind": "Attribute",
                                    "resolved_type": "callable",
                                    "value": {
                                        "kind": "Name",
                                        "id": "math",
                                        "resolved_type": "module",
                                    },
                                    "attr": "sin",
                                },
                                "args": [
                                    {
                                        "kind": "Attribute",
                                        "resolved_type": "float64",
                                        "value": {
                                            "kind": "Name",
                                            "id": "math",
                                            "resolved_type": "module",
                                        },
                                        "attr": "pi",
                                        "runtime_module_id": "pytra.std.math",
                                        "runtime_symbol": "pi",
                                        "runtime_symbol_dispatch": "value",
                                    }
                                ],
                                "keywords": [],
                                "resolved_runtime_call": "math.sin",
                                "runtime_module_id": "pytra.std.math",
                                "runtime_symbol": "sin",
                            },
                        }
                    ],
                }
            ],
        )

        go_code = emit_go_module(doc)

        self.assertIn("return py_sin(py_pi())", go_code)
        self.assertNotIn("math.Pi", go_code)

    def test_go_emitter_emits_pathlib_class_and_uses_native_os_path_helpers(self) -> None:
        doc = _fixture_doc("src/runtime/east/std/pathlib.east")
        meta = doc.setdefault("meta", {})
        assert isinstance(meta, dict)
        meta["linked_program_v1"] = {"module_id": "pytra.std.pathlib"}

        go_code = emit_go_module(doc)

        self.assertIn("type Path struct", go_code)
        self.assertIn("func NewPath(", go_code)
        self.assertIn("func (self *Path) joinpath(", go_code)
        self.assertIn("join(", go_code)
        self.assertIn("dirname(", go_code)
        self.assertNotIn("py_Path(", go_code)
        self.assertNotIn("py_pathlib_write_text", go_code)

    def test_go_emitter_keeps_comprehensions_as_iife_instead_of_placeholder(self) -> None:
        doc = _fixture_doc("test/fixture/east3-opt/collections/comprehension_dict_set.east3")

        go_code = emit_go_module(doc)

        self.assertIn("func() map[", go_code)
        self.assertIn("__comp_result := map[", go_code)
        self.assertNotIn("nil /*", go_code)

    def test_go_emitter_returns_mutated_bytearray_helpers(self) -> None:
        doc = _fixture_doc("test/pytra/east3-opt/utils/png.east3")

        go_code = emit_go_module(doc)

        self.assertIn("func _png_append(dst []byte, src []byte) []byte {", go_code)
        self.assertIn("return dst", go_code)
        self.assertIn("out = _png_append(out, []byte{byte(120), byte(1)})", go_code)

    def test_go_emitter_uses_marker_interfaces_for_user_class_isinstance(self) -> None:
        doc = _fixture_doc("test/fixture/east3-opt/oop/class_inherit_basic.east3")

        go_code = emit_go_module(doc)

        self.assertIn("func (_ Base) __pytra_is_Base() {}", go_code)
        self.assertIn("func (_ Child) __pytra_is_Child() {}", go_code)
        self.assertIn("interface{ __pytra_is_Base() }", go_code)
        self.assertNotIn("any(c).(*Base)", go_code)

    def test_go_emitter_lowers_class_vars_and_staticmethods_without_instance_fields(self) -> None:
        class_doc = _fixture_doc("test/fixture/east3-opt/oop/class_member.east3")
        static_doc = _fixture_doc("test/fixture/east3-opt/oop/staticmethod_basic.east3")

        class_go = emit_go_module(class_doc)
        static_go = emit_go_module(static_doc)

        self.assertIn("var Counter_value int64 = 0", class_go)
        self.assertIn("func NewCounter() *Counter {", class_go)
        self.assertIn("Counter_value += 1", class_go)
        self.assertNotIn("func NewCounter(value int64) *Counter {", class_go)
        self.assertIn("py_print(MathUtil_double(5))", static_go)
        self.assertIn("py_print(MathUtil_triple(4))", static_go)
        self.assertNotIn("MathUtil.double(5)", static_go)

    def test_go_emitter_lowers_super_calls_and_polymorphic_base_params(self) -> None:
        super_doc = _fixture_doc("test/fixture/east3-opt/oop/super_init.east3")
        dispatch_doc = _fixture_doc("test/fixture/east3-opt/oop/inheritance_virtual_dispatch_multilang.east3")

        super_go = emit_go_module(super_doc)
        dispatch_go = emit_go_module(dispatch_doc)

        self.assertIn("obj.Base = *NewBase()", super_go)
        self.assertIn("(\"loud-\" + self.Dog.speak())", dispatch_go)
        self.assertIn("type __pytra_iface_Animal interface {", dispatch_go)
        self.assertIn("func call_via_animal(a __pytra_iface_Animal) string {", dispatch_go)
        self.assertIn("func call_via_dog(d __pytra_iface_Dog) string {", dispatch_go)

    def test_go_emitter_turns_returning_try_into_return_iife(self) -> None:
        doc = _fixture_doc("test/pytra/east3-opt/utils/assertions.east3")

        go_code = emit_go_module(doc)

        self.assertIn("return func() bool {", go_code)
        self.assertIn("__try_result = (py_to_string(actual) == py_to_string(expected))", go_code)
        self.assertIn("__try_result = (actual == expected)", go_code)

    def test_go_emitter_uses_len_based_truthiness_for_bytes_ifexp(self) -> None:
        doc = _fixture_doc("test/fixture/east3-opt/typing/bytes_truthiness.east3")

        go_code = emit_go_module(doc)

        self.assertIn("if len(payload) > 0 {", go_code)
        self.assertIn("for len(payload) > 0 {", go_code)
        self.assertIn("return py_ternary_int(len(payload) > 0, 1, 0)", go_code)

    def test_go_emitter_keeps_tuple_star_args_as_backing_slice_indexes(self) -> None:
        doc = _fixture_doc("test/fixture/east3-opt/typing/starred_call_tuple_basic.east3")

        go_code = emit_go_module(doc)

        self.assertIn("rgb := []any{1, 2, 3}", go_code)
        self.assertIn("mix_rgb(py_to_int64(rgb[0]), py_to_int64(rgb[1]), py_to_int64(rgb[2]))", go_code)
        self.assertNotIn("rgb.([]any)", go_code)

    def test_go_emitter_wraps_optional_scalars_with_typed_temporaries(self) -> None:
        doc = _fixture_doc("test/fixture/east3-opt/typing/none_optional.east3")

        go_code = emit_go_module(doc)

        self.assertIn("func maybe_value(flag bool) *int64 {", go_code)
        self.assertIn("var __opt_1 int64 = 42", go_code)
        self.assertIn("var __opt_3 int64 = __dict_get_2", go_code)
        self.assertIn("var __opt_5 int64 = __dict_get_4", go_code)

    def test_go_emitter_lowers_enum_family_to_named_int_consts(self) -> None:
        enum_go = emit_go_module(_fixture_doc("test/fixture/east3-opt/typing/enum_basic.east3"))
        intenum_go = emit_go_module(_fixture_doc("test/fixture/east3-opt/typing/intenum_basic.east3"))
        intflag_go = emit_go_module(_fixture_doc("test/fixture/east3-opt/typing/intflag_basic.east3"))

        self.assertIn("type Color int64", enum_go)
        self.assertIn("Color_RED Color = 1", enum_go)
        self.assertIn("Color_BLUE Color = 2", enum_go)
        self.assertNotIn("Enum", enum_go)
        self.assertIn("type Status int64", intenum_go)
        self.assertIn("Status_ERROR Status = 1", intenum_go)
        self.assertNotIn("IntEnum", intenum_go)
        self.assertIn("type Perm int64", intflag_go)
        self.assertIn("Perm_READ Perm = 1", intflag_go)
        self.assertIn("Perm((Perm_READ | Perm_WRITE))", intflag_go)
        self.assertNotIn("IntFlag", intflag_go)

    def test_go_emitter_spreads_typed_varargs_and_keeps_plain_class_ctor_zero_arg(self) -> None:
        doc = _fixture_doc("test/fixture/east3-opt/signature/ok_typed_varargs_representative.east3")

        go_code = emit_go_module(doc)

        self.assertIn("func NewControllerState() *ControllerState {", go_code)
        self.assertIn("merge_controller_states(target, []*ControllerState{lhs, rhs}...)", go_code)

    def test_go_emitter_uses_range_target_type_from_east3(self) -> None:
        doc = _module_doc(
            "app.main",
            body=[
                {
                    "kind": "FunctionDef",
                    "name": "run",
                    "arg_types": {},
                    "arg_order": [],
                    "arg_defaults": {},
                    "arg_index": {},
                    "return_type": "None",
                    "arg_usage": {},
                    "renamed_symbols": {},
                    "docstring": None,
                    "body": [
                        {
                            "kind": "ForCore",
                            "iter_mode": "static_fastpath",
                            "iter_plan": {
                                "kind": "StaticRangeForPlan",
                                "start": {"kind": "Constant", "value": 0, "resolved_type": "int64"},
                                "stop": {"kind": "Constant", "value": 3, "resolved_type": "int64"},
                                "step": {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                            },
                            "target_plan": {
                                "kind": "NameTarget",
                                "id": "i",
                                "target_type": "int32",
                            },
                            "body": [],
                            "orelse": [],
                        }
                    ],
                }
            ],
        )

        go_code = emit_go_module(doc)

        self.assertIn("for i := int32(0); i < int32(3); i += int32(1) {", go_code)

    def test_cpp_emitter_runtime_symbol_prefix_uses_skip_modules_without_pytra_hardcode(self) -> None:
        doc = _module_doc(
            "app.main",
            meta_extra={
                "import_bindings": [
                    {
                        "module_id": "runtime.custom",
                        "local_name": "helper",
                        "binding_kind": "symbol",
                    }
                ]
            },
            body=[
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "func": {"kind": "Name", "id": "helper"},
                        "args": [],
                    },
                }
            ],
        )

        mapping = RuntimeMapping(
            builtin_prefix="rt_",
            calls={},
            skip_module_prefixes=["runtime."],
        )
        with patch("toolchain2.emit.cpp.emitter.load_runtime_mapping", return_value=mapping):
            cpp_code = emit_cpp_module(doc)

        self.assertIn("rt_helper();", cpp_code)


if __name__ == "__main__":
    unittest.main()
