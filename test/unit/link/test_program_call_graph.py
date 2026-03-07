import tempfile
import unittest

from pytra.std.pathlib import Path

from toolchain.link import build_linked_program_call_graph
from toolchain.link import build_linked_program_from_module_map


def _name(id_text: str) -> dict[str, object]:
    return {"kind": "Name", "id": id_text}


def _call_name(id_text: str, args: list[dict[str, object]] | None = None) -> dict[str, object]:
    return {"kind": "Call", "func": _name(id_text), "args": list(args or []), "keywords": []}


def _expr(value: dict[str, object]) -> dict[str, object]:
    return {"kind": "Expr", "value": value}


def _ret(value: dict[str, object]) -> dict[str, object]:
    return {"kind": "Return", "value": value}


def _fn(name: str, body: list[dict[str, object]], args: list[str] | None = None) -> dict[str, object]:
    return {"kind": "FunctionDef", "name": name, "arg_order": list(args or []), "body": body}


class LinkedProgramCallGraphTests(unittest.TestCase):
    def test_builds_cross_module_call_graph_from_linked_program(self) -> None:
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
                        "body": [_fn("main", [_ret(_call_name("sink", [_name("x")]))], ["x"])],
                    },
                    str(dep_py): {
                        "kind": "Module",
                        "east_stage": 3,
                        "schema_version": 1,
                        "meta": {"dispatch_mode": "native", "module_id": "pkg.dep"},
                        "body": [_fn("sink", [], ["y"])],
                    },
                },
                target="cpp",
                dispatch_mode="native",
            )

            result = build_linked_program_call_graph(program)

            self.assertEqual(result.graph["pkg.main::main"], ("pkg.dep::sink",))
            self.assertEqual(result.graph["pkg.dep::sink"], ())
            self.assertEqual(result.unresolved_calls["pkg.main::main"], 0)
            self.assertEqual(result.symbol_module_ids["pkg.main::main"], "pkg.main")
            self.assertEqual(result.sccs, (("pkg.dep::sink",), ("pkg.main::main",)))

    def test_mutual_recursion_across_modules_forms_single_scc(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a_py = root / "a.py"
            b_py = root / "b.py"
            program = build_linked_program_from_module_map(
                a_py,
                {
                    str(a_py): {
                        "kind": "Module",
                        "east_stage": 3,
                        "schema_version": 1,
                        "meta": {
                            "dispatch_mode": "native",
                            "module_id": "pkg.a",
                            "import_bindings": [
                                {
                                    "module_id": "pkg.b",
                                    "export_name": "g",
                                    "local_name": "g",
                                    "binding_kind": "symbol",
                                }
                            ],
                        },
                        "body": [_fn("f", [_ret(_call_name("g", [_name("x")]))], ["x"])],
                    },
                    str(b_py): {
                        "kind": "Module",
                        "east_stage": 3,
                        "schema_version": 1,
                        "meta": {
                            "dispatch_mode": "native",
                            "module_id": "pkg.b",
                            "import_bindings": [
                                {
                                    "module_id": "pkg.a",
                                    "export_name": "f",
                                    "local_name": "f",
                                    "binding_kind": "symbol",
                                }
                            ],
                        },
                        "body": [_fn("g", [_ret(_call_name("f", [_name("y")]))], ["y"])],
                    },
                },
                target="cpp",
                dispatch_mode="native",
            )

            result = build_linked_program_call_graph(program)

            self.assertEqual(result.graph["pkg.a::f"], ("pkg.b::g",))
            self.assertEqual(result.graph["pkg.b::g"], ("pkg.a::f",))
            self.assertEqual(result.sccs, (("pkg.a::f", "pkg.b::g"),))

    def test_missing_callee_does_not_trigger_import_closure_loading(self) -> None:
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
                        "meta": {
                            "dispatch_mode": "native",
                            "module_id": "pkg.main",
                            "import_bindings": [
                                {
                                    "module_id": "missing.mod",
                                    "export_name": "sink",
                                    "local_name": "sink",
                                    "binding_kind": "symbol",
                                }
                            ],
                        },
                        "body": [_fn("main", [_expr(_call_name("sink", [_name("x")]))], ["x"])],
                    }
                },
                target="cpp",
                dispatch_mode="native",
            )

            result = build_linked_program_call_graph(program)

            self.assertEqual(result.graph["pkg.main::main"], ())
            self.assertEqual(result.unresolved_calls["pkg.main::main"], 1)
            self.assertEqual(result.sccs, (("pkg.main::main",),))


if __name__ == "__main__":
    unittest.main()
