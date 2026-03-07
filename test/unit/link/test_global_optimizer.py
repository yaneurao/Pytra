import tempfile
import unittest

from pytra.std.pathlib import Path

from toolchain.link import build_linked_program_from_module_map
from toolchain.link import optimize_linked_program
from toolchain.link import validate_link_output_doc


def _name(id_text: str) -> dict[str, object]:
    return {"kind": "Name", "id": id_text}


def _constant(value: object) -> dict[str, object]:
    return {"kind": "Constant", "value": value}


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
            cpp_hints = global_hints["cpp_value_list_locals_v1"]
            self.assertEqual(cpp_hints["pkg.main::main"]["locals"], ["xs"])

            linked_meta = result.linked_program.modules[0].east_doc["meta"]["linked_program_v1"]
            local_hints = linked_meta["container_ownership_hints_v1"]["cpp_value_list_locals_v1"]
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
            self.assertNotIn("cpp_value_list_locals_v1", fn_meta)


if __name__ == "__main__":
    unittest.main()
