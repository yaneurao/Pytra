import tempfile
import unittest
from unittest.mock import patch

from pytra.std.pathlib import Path

from toolchain.link import LinkedProgram
from toolchain.link import LinkedProgramModule
from toolchain.link import build_linked_program_from_module_map
from toolchain.link import optimize_linked_program
from toolchain.link import validate_link_output_doc


def _name(id_text: str) -> dict[str, object]:
    return {"kind": "Name", "id": id_text}


def _constant(value: object) -> dict[str, object]:
    return {"kind": "Constant", "value": value}


def _typed_name(id_text: str, resolved_type: str) -> dict[str, object]:
    return {"kind": "Name", "id": id_text, "resolved_type": resolved_type}


def _call_name(id_text: str, args: list[dict[str, object]] | None = None) -> dict[str, object]:
    return {"kind": "Call", "func": _name(id_text), "args": list(args or []), "keywords": []}


def _call_attr(owner: str, attr: str, args: list[dict[str, object]] | None = None) -> dict[str, object]:
    return {
        "kind": "Call",
        "func": {"kind": "Attribute", "value": _name(owner), "attr": attr},
        "args": list(args or []),
        "keywords": [],
    }


def _expr(value: dict[str, object]) -> dict[str, object]:
    return {"kind": "Expr", "value": value}


def _ret(value: dict[str, object]) -> dict[str, object]:
    return {"kind": "Return", "value": value}


def _fn(name: str, body: list[dict[str, object]], args: list[str] | None = None) -> dict[str, object]:
    return {"kind": "FunctionDef", "name": name, "arg_order": list(args or []), "body": body}


class LinkedProgramGlobalOptimizerTests(unittest.TestCase):
    def test_optimizer_validates_raw_east3_input_modules(self) -> None:
        program = LinkedProgram(
            schema="pytra.link_input.v1",
            manifest_path=None,
            target="cpp",
            dispatch_mode="native",
            entry_modules=("pkg.main",),
            modules=(
                LinkedProgramModule(
                    module_id="pkg.main",
                    source_path="main.py",
                    is_entry=True,
                    east_doc={
                        "kind": "Module",
                        "east_stage": 3,
                        "schema_version": 1,
                        "meta": {"dispatch_mode": "native", "module_id": "pkg.main"},
                        "body": [1],
                    },
                ),
            ),
            options={},
        )

        with self.assertRaisesRegex(RuntimeError, r"raw EAST3\.body\[0\] must be an object: pkg\.main"):
            optimize_linked_program(program)

    def test_optimizer_rejects_value_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main_py = root / "main.py"
            program = build_linked_program_from_module_map(
                main_py,
                {
                    str(main_py): {
                        "kind": "Module",
                        "east_stage": 3,
                        "schema_version": 1,
                        "meta": {"dispatch_mode": "native", "module_id": "pkg.main"},
                        "body": [
                            {
                                "kind": "FunctionDef",
                                "name": "py_join",
                                "arg_order": ["parts"],
                                "body": [_expr(_call_attr("parts", "append", [_constant("x")]))],
                                "meta": {
                                    "runtime_abi_v1": {
                                        "schema_version": 1,
                                        "args": {"parts": "value_readonly"},
                                        "ret": "default",
                                    }
                                },
                            }
                        ],
                    }
                },
                target="cpp",
                dispatch_mode="native",
            )

            with self.assertRaises(RuntimeError) as cm:
                optimize_linked_program(program)

        self.assertIn("value parameter mutated", str(cm.exception))
        self.assertIn("pkg.main::py_join", str(cm.exception))

    def test_optimizer_rejects_runtime_abi_for_unsupported_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main_py = root / "main.py"
            program = build_linked_program_from_module_map(
                main_py,
                {
                    str(main_py): {
                        "kind": "Module",
                        "east_stage": 3,
                        "schema_version": 1,
                        "meta": {"dispatch_mode": "native", "module_id": "pkg.main"},
                        "body": [
                            {
                                "kind": "FunctionDef",
                                "name": "py_join",
                                "arg_order": ["parts"],
                                "body": [_ret(_constant(""))],
                                "meta": {
                                    "runtime_abi_v1": {
                                        "schema_version": 1,
                                        "args": {"parts": "value_readonly"},
                                        "ret": "value",
                                    }
                                },
                            }
                        ],
                    }
                },
                target="rs",
                dispatch_mode="native",
            )

            with self.assertRaises(RuntimeError) as cm:
                optimize_linked_program(program)

        self.assertIn("@abi is not supported for target rs", str(cm.exception))
        self.assertIn("pkg.main::py_join", str(cm.exception))

    def test_optimizer_is_deterministic_for_reordered_module_map(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main_py = root / "main.py"
            dep_py = root / "dep.py"
            main_doc = {
                "kind": "Module",
                "east_stage": 3,
                "schema_version": 1,
                "meta": {
                    "dispatch_mode": "native",
                    "module_id": "pkg.main",
                    "import_bindings": [
                        {
                            "module_id": "pkg.dep",
                            "export_name": "sink",
                            "local_name": "sink",
                            "binding_kind": "symbol",
                        }
                    ],
                },
                "body": [_fn("main", [_expr(_call_name("sink", [_name("x")]))], ["x"])],
            }
            dep_doc = {
                "kind": "Module",
                "east_stage": 3,
                "schema_version": 1,
                "meta": {"dispatch_mode": "native", "module_id": "pkg.dep"},
                "body": [_fn("sink", [_ret(_constant(1))], ["p"])],
            }
            program_a = build_linked_program_from_module_map(
                main_py,
                {
                    str(main_py): dict(main_doc),
                    str(dep_py): dict(dep_doc),
                },
                target="cpp",
                dispatch_mode="native",
            )
            program_b = build_linked_program_from_module_map(
                main_py,
                {
                    str(dep_py): dict(dep_doc),
                    str(main_py): dict(main_doc),
                },
                target="cpp",
                dispatch_mode="native",
            )

            result_a = optimize_linked_program(program_a)
            result_b = optimize_linked_program(program_b)

            self.assertEqual(result_a.link_output_doc, result_b.link_output_doc)
            self.assertEqual(
                [item.module_id for item in result_a.linked_program.modules],
                [item.module_id for item in result_b.linked_program.modules],
            )

    def test_optimizer_materializes_non_escape_summary_and_linked_meta(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main_py = root / "main.py"
            dep_py = root / "dep.py"
            program = build_linked_program_from_module_map(
                main_py,
                {
                    str(main_py): {
                        "kind": "Module",
                        "east_stage": 3,
                        "schema_version": 1,
                        "meta": {
                            "dispatch_mode": "native",
                            "module_id": "pkg.main",
                            "import_bindings": [
                                {
                                    "module_id": "pkg.dep",
                                    "export_name": "sink",
                                    "local_name": "sink",
                                    "binding_kind": "symbol",
                                }
                            ],
                        },
                        "body": [_fn("main", [_expr(_call_name("sink", [_name("x")]))], ["x"])],
                    },
                    str(dep_py): {
                        "kind": "Module",
                        "east_stage": 3,
                        "schema_version": 1,
                        "meta": {"dispatch_mode": "native", "module_id": "pkg.dep"},
                        "body": [_fn("sink", [_expr(_call_name("unknown_sink", [_name("p")]))], ["p"])],
                    },
                },
                target="cpp",
                dispatch_mode="native",
            )

            result = optimize_linked_program(program)
            link_output = validate_link_output_doc(result.link_output_doc)

            self.assertEqual(link_output["global"]["call_graph"]["pkg.main::main"], ["pkg.dep::sink"])
            summary = link_output["global"]["non_escape_summary"]
            self.assertTrue(summary["pkg.dep::sink"]["arg_escape"][0])
            self.assertTrue(summary["pkg.main::main"]["arg_escape"][0])

            linked_main = result.linked_program.modules[1].east_doc
            main_meta = linked_main.get("meta", {})
            self.assertIn("linked_program_v1", main_meta)
            linked_payload = main_meta["linked_program_v1"]
            self.assertEqual(linked_payload["module_id"], "pkg.main")
            self.assertIn("pkg.dep::sink", linked_payload["non_escape_summary"])
            callsite = linked_main["body"][0]["body"][0]["value"]["meta"]["non_escape_callsite"]
            self.assertEqual(callsite["callee"], "pkg.dep::sink")
            self.assertTrue(callsite["resolved"])

    def test_optimizer_assigns_deterministic_type_ids_across_modules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base_py = root / "base.py"
            child_py = root / "child.py"
            program = build_linked_program_from_module_map(
                child_py,
                {
                    str(base_py): {
                        "kind": "Module",
                        "east_stage": 3,
                        "schema_version": 1,
                        "meta": {"dispatch_mode": "native", "module_id": "pkg.base"},
                        "body": [{"kind": "ClassDef", "name": "Base", "base": "", "body": []}],
                    },
                    str(child_py): {
                        "kind": "Module",
                        "east_stage": 3,
                        "schema_version": 1,
                        "meta": {
                            "dispatch_mode": "native",
                            "module_id": "pkg.child",
                            "import_bindings": [
                                {
                                    "module_id": "pkg.base",
                                    "export_name": "Base",
                                    "local_name": "Base",
                                    "binding_kind": "symbol",
                                }
                            ],
                        },
                        "body": [{"kind": "ClassDef", "name": "Child", "base": "Base", "body": []}],
                    },
                },
                target="cpp",
                dispatch_mode="native",
            )

            result = optimize_linked_program(program)
            type_id_table = result.link_output_doc["global"]["type_id_table"]

            self.assertEqual(type_id_table, {"pkg.base.Base": 1000, "pkg.child.Child": 1001})
            linked_child_meta = result.linked_program.modules[1].east_doc["meta"]["linked_program_v1"]
            self.assertEqual(linked_child_meta["type_id_resolved_v1"]["pkg.child.Child"], 1001)

    def test_optimizer_treats_enum_like_bases_as_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            enum_py = root / "enum_mod.py"
            intenum_py = root / "intenum_mod.py"
            intflag_py = root / "intflag_mod.py"
            program = build_linked_program_from_module_map(
                enum_py,
                {
                    str(enum_py): {
                        "kind": "Module",
                        "east_stage": 3,
                        "schema_version": 1,
                        "meta": {"dispatch_mode": "native", "module_id": "pkg.enum_mod"},
                        "body": [{"kind": "ClassDef", "name": "Color", "base": "Enum", "body": []}],
                    },
                    str(intenum_py): {
                        "kind": "Module",
                        "east_stage": 3,
                        "schema_version": 1,
                        "meta": {"dispatch_mode": "native", "module_id": "pkg.intenum_mod"},
                        "body": [{"kind": "ClassDef", "name": "Status", "base": "IntEnum", "body": []}],
                    },
                    str(intflag_py): {
                        "kind": "Module",
                        "east_stage": 3,
                        "schema_version": 1,
                        "meta": {"dispatch_mode": "native", "module_id": "pkg.intflag_mod"},
                        "body": [{"kind": "ClassDef", "name": "Perm", "base": "IntFlag", "body": []}],
                    },
                },
                target="cpp",
                dispatch_mode="native",
            )

            result = optimize_linked_program(program)
            self.assertEqual(
                result.link_output_doc["global"]["type_id_table"],
                {
                    "pkg.enum_mod.Color": 1000,
                    "pkg.intenum_mod.Status": 1001,
                    "pkg.intflag_mod.Perm": 1002,
                },
            )

    def test_optimizer_materializes_cpp_value_list_hints(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main_py = root / "main.py"
            program = build_linked_program_from_module_map(
                main_py,
                {
                    str(main_py): {
                        "kind": "Module",
                        "east_stage": 3,
                        "schema_version": 1,
                        "meta": {"dispatch_mode": "native", "module_id": "pkg.main"},
                        "body": [
                            _fn(
                                "main",
                                [
                                    {
                                        "kind": "AnnAssign",
                                        "target": _name("xs"),
                                        "annotation": "list[int]",
                                        "value": {"kind": "List", "elements": []},
                                    },
                                    _expr(_call_attr("xs", "append", [_constant(1)])),
                                    _ret(_call_name("len", [_name("xs")])),
                                ],
                            )
                        ],
                    }
                },
                target="cpp",
                dispatch_mode="native",
            )

            result = optimize_linked_program(program)
            global_hints = result.link_output_doc["global"]["container_ownership_hints_v1"]
            container_hints = global_hints["container_value_locals_v1"]
            self.assertEqual(container_hints["pkg.main::main"]["locals"], ["xs"])

            linked_meta = result.linked_program.modules[0].east_doc["meta"]["linked_program_v1"]
            local_hints = linked_meta["container_ownership_hints_v1"]["container_value_locals_v1"]
            self.assertEqual(local_hints["pkg.main::main"]["locals"], ["xs"])

    def test_optimizer_respects_opt_level_zero_for_global_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main_py = root / "main.py"
            program = build_linked_program_from_module_map(
                main_py,
                {
                    str(main_py): {
                        "kind": "Module",
                        "east_stage": 3,
                        "schema_version": 1,
                        "meta": {"dispatch_mode": "native", "module_id": "pkg.main"},
                        "body": [
                            _fn(
                                "main",
                                [
                                    {
                                        "kind": "AnnAssign",
                                        "target": _name("xs"),
                                        "annotation": "list[int]",
                                        "value": {"kind": "List", "elements": []},
                                    },
                                    _expr(_call_attr("xs", "append", [_constant(1)])),
                                    _ret(_call_name("len", [_name("xs")])),
                                ],
                            )
                        ],
                    }
                },
                target="cpp",
                dispatch_mode="native",
                options={"east3_opt_level": "0"},
            )

            result = optimize_linked_program(program)
            self.assertEqual(result.link_output_doc["global"]["non_escape_summary"], {})
            self.assertEqual(result.link_output_doc["global"]["container_ownership_hints_v1"], {})
            linked_main = result.linked_program.modules[0].east_doc
            self.assertNotIn("non_escape_summary", linked_main.get("meta", {}))
            fn_meta = linked_main["body"][0].get("meta", {})
            self.assertNotIn("escape_summary", fn_meta)
            self.assertNotIn("container_value_locals_v1", fn_meta)

    def test_optimizer_specializes_runtime_template_within_same_module(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            helper_py = root / "template_ops.py"
            program = build_linked_program_from_module_map(
                helper_py,
                {
                    str(helper_py): {
                        "kind": "Module",
                        "east_stage": 3,
                        "schema_version": 1,
                        "meta": {"dispatch_mode": "native", "module_id": "pytra.built_in.template_ops"},
                        "body": [
                            {
                                "kind": "FunctionDef",
                                "name": "py_echo",
                                "arg_order": ["x"],
                                "arg_types": {"x": "T"},
                                "return_type": "T",
                                "body": [_ret(_name("x"))],
                                "meta": {
                                    "template_v1": {
                                        "schema_version": 1,
                                        "params": ["T"],
                                        "scope": "runtime_helper",
                                        "instantiation_mode": "linked_implicit",
                                    }
                                },
                            },
                            {
                                "kind": "FunctionDef",
                                "name": "use_i64",
                                "arg_order": ["x"],
                                "arg_types": {"x": "int64"},
                                "return_type": "int64",
                                "body": [_ret(_call_name("py_echo", [_typed_name("x", "int64")]))],
                            },
                        ],
                    }
                },
                target="cpp",
                dispatch_mode="native",
            )

            result = optimize_linked_program(program)
            link_output = validate_link_output_doc(result.link_output_doc)

            helper_doc = result.linked_program.modules[0].east_doc
            fn_names = [item["name"] for item in helper_doc["body"] if item.get("kind") == "FunctionDef"]
            self.assertEqual(fn_names, ["py_echo__pytra_tmpl__int64", "use_i64"])
            specialized = helper_doc["body"][0]
            self.assertEqual(specialized["arg_types"], {"x": "int64"})
            self.assertEqual(specialized["return_type"], "int64")
            self.assertEqual(
                specialized["meta"]["template_specialization_v1"],
                {
                    "schema_version": 1,
                    "origin_symbol": "pytra.built_in.template_ops::py_echo",
                    "type_args": ["int64"],
                },
            )
            call_node = helper_doc["body"][1]["body"][0]["value"]
            self.assertEqual(call_node["func"]["id"], "py_echo__pytra_tmpl__int64")
            self.assertEqual(call_node["resolved_type"], "int64")
            summary = link_output["global"]["runtime_template_specializations_v1"]
            self.assertEqual(
                summary["pytra.built_in.template_ops::py_echo"],
                [{"export_name": "py_echo__pytra_tmpl__int64", "type_args": ["int64"]}],
            )

    def test_optimizer_specializes_runtime_template_annotations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            helper_py = root / "zip_ops.py"
            program = build_linked_program_from_module_map(
                helper_py,
                {
                    str(helper_py): {
                        "kind": "Module",
                        "east_stage": 3,
                        "schema_version": 1,
                        "meta": {"dispatch_mode": "native", "module_id": "pytra.built_in.zip_ops"},
                        "body": [
                            {
                                "kind": "FunctionDef",
                                "name": "zip",
                                "arg_order": ["lhs", "rhs"],
                                "arg_types": {"lhs": "list[A]", "rhs": "list[B]"},
                                "return_type": "list[tuple[A,B]]",
                                "body": [
                                    {
                                        "kind": "AnnAssign",
                                        "target": _name("out"),
                                        "annotation": "list[tuple[A,B]]",
                                        "value": {"kind": "List", "elements": [], "resolved_type": "list[tuple[A,B]]"},
                                    },
                                    _ret(_name("out")),
                                ],
                                "meta": {
                                    "template_v1": {
                                        "schema_version": 1,
                                        "params": ["A", "B"],
                                        "scope": "runtime_helper",
                                        "instantiation_mode": "linked_implicit",
                                    },
                                    "runtime_abi_v1": {
                                        "schema_version": 1,
                                        "args": {"lhs": "value", "rhs": "value"},
                                        "ret": "value",
                                    },
                                },
                            },
                            {
                                "kind": "FunctionDef",
                                "name": "use_pair",
                                "arg_order": ["lhs", "rhs"],
                                "arg_types": {"lhs": "list[int64]", "rhs": "list[str]"},
                                "return_type": "list[tuple[int64,str]]",
                                "body": [
                                    _ret(
                                        {
                                            "kind": "Call",
                                            "func": _name("zip"),
                                            "args": [
                                                _typed_name("lhs", "list[int64]"),
                                                _typed_name("rhs", "list[str]"),
                                            ],
                                            "keywords": [],
                                            "resolved_type": "list[tuple[int64,str]]",
                                        }
                                    )
                                ],
                            },
                        ],
                    }
                },
                target="cpp",
                dispatch_mode="native",
            )

            result = optimize_linked_program(program)
            helper_doc = result.linked_program.modules[0].east_doc
            specialized = helper_doc["body"][0]
            self.assertEqual(specialized["name"], "zip__pytra_tmpl__int64__str")
            self.assertEqual(specialized["arg_types"], {"lhs": "list[int64]", "rhs": "list[str]"})
            self.assertEqual(specialized["return_type"], "list[tuple[int64,str]]")
            ann_assign = specialized["body"][0]
            self.assertEqual(ann_assign["annotation"], "list[tuple[int64,str]]")
            self.assertEqual(ann_assign["value"]["resolved_type"], "list[tuple[int64,str]]")

    def test_optimizer_specializes_runtime_template_across_imported_module(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main_py = root / "main.py"
            helper_py = root / "template_ops.py"
            program = build_linked_program_from_module_map(
                main_py,
                {
                    str(main_py): {
                        "kind": "Module",
                        "east_stage": 3,
                        "schema_version": 1,
                        "meta": {
                            "dispatch_mode": "native",
                            "module_id": "pkg.main",
                            "import_bindings": [
                                {
                                    "module_id": "pytra.built_in.template_ops",
                                    "export_name": "py_echo",
                                    "local_name": "py_echo",
                                    "binding_kind": "symbol",
                                }
                            ],
                        },
                        "body": [
                            {
                                "kind": "ImportFrom",
                                "module": "pytra.built_in.template_ops",
                                "names": [{"name": "py_echo", "asname": None}],
                            },
                            {
                                "kind": "FunctionDef",
                                "name": "main",
                                "arg_order": ["xs"],
                                "arg_types": {"xs": "list[int64]"},
                                "return_type": "list[int64]",
                                "body": [_ret(_call_name("py_echo", [_typed_name("xs", "list[int64]")]))],
                            },
                        ],
                    },
                    str(helper_py): {
                        "kind": "Module",
                        "east_stage": 3,
                        "schema_version": 1,
                        "meta": {"dispatch_mode": "native", "module_id": "pytra.built_in.template_ops"},
                        "body": [
                            {
                                "kind": "FunctionDef",
                                "name": "py_echo",
                                "arg_order": ["xs"],
                                "arg_types": {"xs": "list[T]"},
                                "return_type": "list[T]",
                                "body": [_ret(_name("xs"))],
                                "meta": {
                                    "template_v1": {
                                        "schema_version": 1,
                                        "params": ["T"],
                                        "scope": "runtime_helper",
                                        "instantiation_mode": "linked_implicit",
                                    }
                                },
                            }
                        ],
                    },
                },
                target="cpp",
                dispatch_mode="native",
            )

            result = optimize_linked_program(program)
            link_output = validate_link_output_doc(result.link_output_doc)

            main_doc = next(item.east_doc for item in result.linked_program.modules if item.module_id == "pkg.main")
            import_binding = main_doc["meta"]["import_bindings"][0]
            self.assertEqual(import_binding["module_id"], "pytra.built_in.template_ops")
            self.assertEqual(import_binding["export_name"], "py_echo__pytra_tmpl__int64")
            self.assertEqual(import_binding["local_name"], "py_echo__pytra_tmpl__int64")
            import_stmt = main_doc["body"][0]
            self.assertEqual(import_stmt["names"], [{"name": "py_echo__pytra_tmpl__int64", "asname": None}])
            call_node = main_doc["body"][1]["body"][0]["value"]
            self.assertEqual(call_node["func"]["id"], "py_echo__pytra_tmpl__int64")
            self.assertEqual(call_node["resolved_type"], "list[int64]")
            summary = link_output["global"]["runtime_template_specializations_v1"]
            self.assertEqual(
                summary["pytra.built_in.template_ops::py_echo"],
                [{"export_name": "py_echo__pytra_tmpl__int64", "type_args": ["int64"]}],
            )

    def test_optimizer_preserves_helper_module_metadata(self) -> None:
        owner_doc = {
            "kind": "Module",
            "east_stage": 3,
            "schema_version": 1,
            "meta": {
                "dispatch_mode": "native",
                "module_id": "app.main",
            },
            "body": [],
        }
        helper_doc = {
            "kind": "Module",
            "east_stage": 3,
            "schema_version": 1,
            "meta": {
                "dispatch_mode": "native",
                "module_id": "__pytra_helper__.cpp.demo",
                "synthetic_helper_v1": {
                    "helper_id": "cpp.demo",
                    "owner_module_id": "app.main",
                    "generated_by": "linked_optimizer",
                },
            },
            "body": [],
        }
        program = LinkedProgram(
            schema="pytra.link_input.v1",
            manifest_path=None,
            target="cpp",
            dispatch_mode="native",
            entry_modules=("app.main",),
            modules=(
                LinkedProgramModule(
                    module_id="app.main",
                    source_path="app/main.py",
                    is_entry=True,
                    east_doc=owner_doc,
                    artifact_path=None,
                    module_kind="user",
                ),
                LinkedProgramModule(
                    module_id="__pytra_helper__.cpp.demo",
                    source_path="",
                    is_entry=False,
                    east_doc=helper_doc,
                    artifact_path=None,
                    module_kind="helper",
                    helper_id="cpp.demo",
                    owner_module_id="app.main",
                    generated_by="linked_optimizer",
                ),
            ),
            options={},
        )

        result = optimize_linked_program(program)

        helper_entry = next(
            item for item in result.link_output_doc["modules"] if item.get("module_id") == "__pytra_helper__.cpp.demo"
        )
        module_entry = helper_entry
        self.assertEqual(module_entry["module_kind"], "helper")
        self.assertEqual(module_entry["helper_id"], "cpp.demo")
        self.assertEqual(module_entry["owner_module_id"], "app.main")
        self.assertEqual(module_entry["generated_by"], "linked_optimizer")
        linked_module = next(item for item in result.linked_program.modules if item.module_id == "__pytra_helper__.cpp.demo")
        self.assertEqual(linked_module.module_kind, "helper")
        self.assertEqual(linked_module.helper_id, "cpp.demo")
        self.assertEqual(linked_module.owner_module_id, "app.main")
        self.assertEqual(linked_module.generated_by, "linked_optimizer")

    def test_optimizer_validates_link_output_before_return(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            main_py = root / "main.py"
            program = build_linked_program_from_module_map(
                main_py,
                {
                    str(main_py): {
                        "kind": "Module",
                        "east_stage": 3,
                        "schema_version": 1,
                        "meta": {"dispatch_mode": "native", "module_id": "pkg.main"},
                        "body": [],
                    }
                },
                target="cpp",
                dispatch_mode="native",
            )

            with patch("toolchain.link.global_optimizer._build_type_id_table", return_value={"pkg.main.Foo": "oops"}):
                with self.assertRaisesRegex(
                    RuntimeError,
                    r"link-output\.global\.type_id_table\.pkg\.main\.Foo must be int",
                ):
                    optimize_linked_program(program)


if __name__ == "__main__":
    unittest.main()
