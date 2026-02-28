from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.pytra.compiler.east_parts.east3_opt_passes.non_escape_interprocedural_pass import NonEscapeInterproceduralPass
from src.pytra.compiler.east_parts.east3_optimizer import PassContext


def _name(id_text: str) -> dict[str, object]:
    return {"kind": "Name", "id": id_text}


def _call_name(id_text: str, args: list[dict[str, object]]) -> dict[str, object]:
    return {"kind": "Call", "func": _name(id_text), "args": args, "keywords": []}


def _ret(value: dict[str, object]) -> dict[str, object]:
    return {"kind": "Return", "value": value}


def _expr(value: dict[str, object]) -> dict[str, object]:
    return {"kind": "Expr", "value": value}


def _fn(name: str, args: list[str], body: list[dict[str, object]]) -> dict[str, object]:
    return {"kind": "FunctionDef", "name": name, "arg_order": args, "body": body}


def _sym(name: str) -> str:
    return "__module__::" + name


class East3NonEscapeInterproceduralPassTest(unittest.TestCase):
    def test_pass_propagates_arg_escape_through_known_calls(self) -> None:
        sink_call = _call_name("unknown_sink", [_name("x")])
        wrap_call = _call_name("sink", [_name("y")])
        doc: dict[str, object] = {
            "kind": "Module",
            "east_stage": 3,
            "meta": {},
            "body": [
                _fn("sink", ["x"], [_expr(sink_call)]),
                _fn("wrap", ["y"], [_expr(wrap_call)]),
            ],
        }
        result = NonEscapeInterproceduralPass().run(doc, PassContext(opt_level=1))
        self.assertTrue(result.changed)
        summary = doc.get("meta", {}).get("non_escape_summary", {})
        self.assertTrue(summary[_sym("sink")]["arg_escape"][0])
        self.assertTrue(summary[_sym("wrap")]["arg_escape"][0])
        body = doc.get("body", [])
        sink_fn = body[0] if isinstance(body, list) and len(body) > 0 else {}
        wrap_fn = body[1] if isinstance(body, list) and len(body) > 1 else {}
        self.assertTrue(sink_fn.get("meta", {}).get("escape_summary", {}).get("arg_escape", [False])[0])
        self.assertTrue(wrap_fn.get("meta", {}).get("escape_summary", {}).get("arg_escape", [False])[0])
        sink_call_meta = sink_call.get("meta", {}).get("non_escape_callsite", {})
        wrap_call_meta = wrap_call.get("meta", {}).get("non_escape_callsite", {})
        self.assertFalse(sink_call_meta.get("resolved", True))
        self.assertTrue(wrap_call_meta.get("resolved", False))
        self.assertEqual(wrap_call_meta.get("callee"), _sym("sink"))
        self.assertEqual(wrap_call_meta.get("arg_sources"), [[0]])

    def test_pass_propagates_return_from_args(self) -> None:
        doc: dict[str, object] = {
            "kind": "Module",
            "east_stage": 3,
            "meta": {},
            "body": [
                _fn("identity", ["x"], [_ret(_name("x"))]),
                _fn("wrap", ["y"], [_ret(_call_name("identity", [_name("y")]))]),
                _fn("wrap2", ["z"], [_ret(_call_name("wrap", [_name("z")]))]),
            ],
        }
        _ = NonEscapeInterproceduralPass().run(doc, PassContext(opt_level=1))
        summary = doc.get("meta", {}).get("non_escape_summary", {})
        self.assertTrue(summary[_sym("identity")]["return_from_args"][0])
        self.assertTrue(summary[_sym("wrap")]["return_from_args"][0])
        self.assertTrue(summary[_sym("wrap2")]["return_from_args"][0])
        self.assertTrue(summary[_sym("wrap2")]["return_escape"])

    def test_unknown_call_policy_can_disable_direct_arg_escape(self) -> None:
        doc: dict[str, object] = {
            "kind": "Module",
            "east_stage": 3,
            "meta": {},
            "body": [
                _fn("sink", ["x"], [_expr(_call_name("unknown_sink", [_name("x")]))]),
            ],
        }
        _ = NonEscapeInterproceduralPass().run(
            doc,
            PassContext(
                opt_level=1,
                non_escape_policy={"unknown_call_escape": False},
            ),
        )
        summary = doc.get("meta", {}).get("non_escape_summary", {})
        self.assertFalse(summary[_sym("sink")]["arg_escape"][0])
        self.assertFalse(summary[_sym("sink")]["return_escape"])

    def test_pass_handles_mutual_recursion_with_unknown_calls(self) -> None:
        call_a_to_b = _call_name("b", [_name("x")])
        call_b_to_unknown = _call_name("unknown_sink", [_name("y")])
        call_b_to_a = _call_name("a", [_name("y")])
        doc: dict[str, object] = {
            "kind": "Module",
            "east_stage": 3,
            "meta": {},
            "body": [
                _fn("a", ["x"], [_ret(call_a_to_b)]),
                _fn("b", ["y"], [_expr(call_b_to_unknown), _ret(call_b_to_a)]),
            ],
        }
        _ = NonEscapeInterproceduralPass().run(doc, PassContext(opt_level=1))
        summary = doc.get("meta", {}).get("non_escape_summary", {})
        self.assertTrue(summary[_sym("a")]["arg_escape"][0])
        self.assertTrue(summary[_sym("b")]["arg_escape"][0])
        self.assertTrue(summary[_sym("a")]["return_from_args"][0])
        self.assertTrue(summary[_sym("b")]["return_from_args"][0])
        self.assertTrue(summary[_sym("a")]["return_escape"])
        self.assertTrue(summary[_sym("b")]["return_escape"])
        self.assertTrue(call_a_to_b.get("meta", {}).get("non_escape_callsite", {}).get("resolved", False))
        self.assertFalse(call_b_to_unknown.get("meta", {}).get("non_escape_callsite", {}).get("resolved", True))
        self.assertTrue(call_b_to_a.get("meta", {}).get("non_escape_callsite", {}).get("resolved", False))
        self.assertEqual(call_a_to_b.get("meta", {}).get("non_escape_callsite", {}).get("callee"), _sym("b"))
        self.assertEqual(call_b_to_a.get("meta", {}).get("non_escape_callsite", {}).get("callee"), _sym("a"))

    def test_pass_is_deterministic_after_convergence(self) -> None:
        call_a_to_b = _call_name("b", [_name("x")])
        call_b_to_unknown = _call_name("unknown_sink", [_name("y")])
        doc: dict[str, object] = {
            "kind": "Module",
            "east_stage": 3,
            "meta": {},
            "body": [
                _fn("a", ["x"], [_ret(call_a_to_b)]),
                _fn("b", ["y"], [_expr(call_b_to_unknown)]),
            ],
        }
        pass_obj = NonEscapeInterproceduralPass()
        result1 = pass_obj.run(doc, PassContext(opt_level=1))
        summary1 = doc.get("meta", {}).get("non_escape_summary", {})
        result2 = pass_obj.run(doc, PassContext(opt_level=1))
        summary2 = doc.get("meta", {}).get("non_escape_summary", {})
        self.assertTrue(result1.changed)
        self.assertFalse(result2.changed)
        self.assertEqual(result2.change_count, 0)
        self.assertEqual(summary1, summary2)

    def test_imported_symbol_call_keeps_module_qualified_callee_candidate(self) -> None:
        imported_call = _call_name("save_gif", [_name("frames")])
        doc: dict[str, object] = {
            "kind": "Module",
            "east_stage": 3,
            "meta": {
                "import_bindings": [
                    {
                        "module_id": "pytra.std.image",
                        "export_name": "save_gif",
                        "local_name": "save_gif",
                        "binding_kind": "symbol",
                    }
                ]
            },
            "body": [
                _fn("main", ["frames"], [_expr(imported_call)]),
            ],
        }
        _ = NonEscapeInterproceduralPass().run(doc, PassContext(opt_level=1))
        callsite = imported_call.get("meta", {}).get("non_escape_callsite", {})
        self.assertEqual(callsite.get("callee"), "pytra.std.image::save_gif")
        self.assertFalse(callsite.get("resolved", True))

    def test_cross_module_closure_propagates_summary_to_root(self) -> None:
        callee_unknown = _call_name("unknown_sink", [_name("p")])
        imported_doc: dict[str, object] = {
            "kind": "Module",
            "east_stage": 3,
            "meta": {"module_id": "pkg.b"},
            "body": [
                _fn("sink", ["p"], [_expr(callee_unknown)]),
            ],
        }
        root_call = _call_name("sink", [_name("x")])
        root_doc: dict[str, object] = {
            "kind": "Module",
            "east_stage": 3,
            "meta": {
                "module_id": "pkg.a",
                "import_bindings": [
                    {
                        "module_id": "pkg.b",
                        "export_name": "sink",
                        "local_name": "sink",
                        "binding_kind": "symbol",
                    }
                ],
                "non_escape_import_closure": {"pkg.b": imported_doc},
            },
            "body": [
                _fn("main", ["x"], [_expr(root_call)]),
            ],
        }
        result1 = NonEscapeInterproceduralPass().run(root_doc, PassContext(opt_level=1))
        summary1 = root_doc.get("meta", {}).get("non_escape_summary", {})
        self.assertTrue(result1.changed)
        self.assertTrue(summary1["pkg.b::sink"]["arg_escape"][0])
        self.assertTrue(summary1["pkg.a::main"]["arg_escape"][0])
        callsite = root_call.get("meta", {}).get("non_escape_callsite", {})
        self.assertEqual(callsite.get("callee"), "pkg.b::sink")
        self.assertTrue(callsite.get("resolved", False))
        result2 = NonEscapeInterproceduralPass().run(root_doc, PassContext(opt_level=1))
        summary2 = root_doc.get("meta", {}).get("non_escape_summary", {})
        self.assertFalse(result2.changed)
        self.assertEqual(summary1, summary2)

    def test_unresolved_builtin_len_gets_non_escape_arg_annotation(self) -> None:
        len_call = _call_name("len", [_name("xs")])
        doc: dict[str, object] = {
            "kind": "Module",
            "east_stage": 3,
            "meta": {},
            "body": [
                _fn("f", ["xs"], [_ret(len_call)]),
            ],
        }
        _ = NonEscapeInterproceduralPass().run(doc, PassContext(opt_level=1))
        callsite = len_call.get("meta", {}).get("non_escape_callsite", {})
        self.assertFalse(callsite.get("resolved", True))
        self.assertEqual(callsite.get("callee_arg_escape"), [False])

    def test_auto_import_closure_loads_module_from_source_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root_dir = Path(tmpdir)
            dep_py = root_dir / "b.py"
            dep_py.write_text(
                "def sink(xs):\n"
                "    print(xs)\n"
                "    return 0\n",
                encoding="utf-8",
            )
            src_py = root_dir / "a.py"
            src_py.write_text(
                "from b import sink\n"
                "def main(x):\n"
                "    return sink(x)\n",
                encoding="utf-8",
            )

            call_sink = _call_name("sink", [_name("x")])
            root_doc: dict[str, object] = {
                "kind": "Module",
                "east_stage": 3,
                "source_path": str(src_py),
                "meta": {
                    "import_bindings": [
                        {
                            "module_id": "b",
                            "export_name": "sink",
                            "local_name": "sink",
                            "binding_kind": "symbol",
                        }
                    ]
                },
                "body": [_fn("main", ["x"], [_ret(call_sink)])],
            }

            _ = NonEscapeInterproceduralPass().run(root_doc, PassContext(opt_level=1))
            summary = root_doc.get("meta", {}).get("non_escape_summary", {})
            self.assertTrue("b::sink" in summary)
            self.assertTrue(summary["b::sink"]["arg_escape"][0])
            root_keys = [k for k in summary.keys() if isinstance(k, str) and k.endswith("::main")]
            self.assertEqual(len(root_keys), 1)
            self.assertTrue(summary[root_keys[0]]["arg_escape"][0])
            callsite = call_sink.get("meta", {}).get("non_escape_callsite", {})
            self.assertEqual(callsite.get("callee"), "b::sink")
            self.assertTrue(callsite.get("resolved", False))

    def test_reexport_module_alias_is_resolved_to_real_callee(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root_dir = Path(tmpdir)
            pkg_dir = root_dir / "pkg"
            pkg_dir.mkdir(parents=True, exist_ok=True)
            runtime_py = pkg_dir / "runtime.py"
            runtime_py.write_text(
                "from .util import sink\n",
                encoding="utf-8",
            )
            util_py = pkg_dir / "util.py"
            util_py.write_text(
                "def sink(xs):\n"
                "    print(xs)\n"
                "    return 0\n",
                encoding="utf-8",
            )
            src_py = pkg_dir / "main.py"
            src_py.write_text(
                "from pkg.runtime import sink\n"
                "def main(x):\n"
                "    return sink(x)\n",
                encoding="utf-8",
            )

            call_sink = _call_name("sink", [_name("x")])
            root_doc: dict[str, object] = {
                "kind": "Module",
                "east_stage": 3,
                "source_path": str(src_py),
                "meta": {
                    "module_id": "pkg.main",
                    "import_bindings": [
                        {
                            "module_id": "pkg.runtime",
                            "export_name": "sink",
                            "local_name": "sink",
                            "binding_kind": "symbol",
                        }
                    ]
                },
                "body": [_fn("main", ["x"], [_ret(call_sink)])],
            }

            _ = NonEscapeInterproceduralPass().run(root_doc, PassContext(opt_level=1))
            summary = root_doc.get("meta", {}).get("non_escape_summary", {})
            self.assertTrue("pkg.util::sink" in summary)
            self.assertTrue(summary["pkg.util::sink"]["arg_escape"][0])
            self.assertTrue(summary["pkg.main::main"]["arg_escape"][0])
            callsite = call_sink.get("meta", {}).get("non_escape_callsite", {})
            self.assertEqual(callsite.get("callee"), "pkg.util::sink")
            self.assertTrue(callsite.get("resolved", False))

    def test_unresolved_import_is_fail_closed_and_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root_dir = Path(tmpdir)
            src_py = root_dir / "a.py"
            src_py.write_text(
                "from missing_mod import sink\n"
                "def main(x):\n"
                "    return sink(x)\n",
                encoding="utf-8",
            )
            call_sink = _call_name("sink", [_name("x")])
            root_doc: dict[str, object] = {
                "kind": "Module",
                "east_stage": 3,
                "source_path": str(src_py),
                "meta": {
                    "module_id": "a",
                    "import_bindings": [
                        {
                            "module_id": "missing_mod",
                            "export_name": "sink",
                            "local_name": "sink",
                            "binding_kind": "symbol",
                        }
                    ],
                },
                "body": [_fn("main", ["x"], [_ret(call_sink)])],
            }

            pass_obj = NonEscapeInterproceduralPass()
            result1 = pass_obj.run(root_doc, PassContext(opt_level=1))
            summary1 = root_doc.get("meta", {}).get("non_escape_summary", {})
            self.assertTrue(result1.changed)
            self.assertTrue("missing_mod::sink" not in summary1)
            self.assertTrue(summary1["a::main"]["arg_escape"][0])
            callsite = call_sink.get("meta", {}).get("non_escape_callsite", {})
            self.assertEqual(callsite.get("callee"), "missing_mod::sink")
            self.assertFalse(callsite.get("resolved", True))

            result2 = pass_obj.run(root_doc, PassContext(opt_level=1))
            summary2 = root_doc.get("meta", {}).get("non_escape_summary", {})
            self.assertFalse(result2.changed)
            self.assertEqual(summary1, summary2)

    def test_recursive_import_closure_converges(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root_dir = Path(tmpdir)
            mod_a = root_dir / "a.py"
            mod_b = root_dir / "b.py"
            mod_a.write_text(
                "from b import g\n"
                "def f(x):\n"
                "    return g(x)\n",
                encoding="utf-8",
            )
            mod_b.write_text(
                "from a import f\n"
                "def g(y):\n"
                "    return f(y)\n",
                encoding="utf-8",
            )

            call_g = _call_name("g", [_name("x")])
            root_doc: dict[str, object] = {
                "kind": "Module",
                "east_stage": 3,
                "source_path": str(mod_a),
                "meta": {
                    "module_id": "a",
                    "import_bindings": [
                        {
                            "module_id": "b",
                            "export_name": "g",
                            "local_name": "g",
                            "binding_kind": "symbol",
                        }
                    ],
                },
                "body": [_fn("f", ["x"], [_ret(call_g)])],
            }

            pass_obj = NonEscapeInterproceduralPass()
            result1 = pass_obj.run(root_doc, PassContext(opt_level=1))
            summary1 = root_doc.get("meta", {}).get("non_escape_summary", {})
            self.assertTrue(result1.changed)
            self.assertTrue("a::f" in summary1)
            self.assertTrue("b::g" in summary1)
            callsite = call_g.get("meta", {}).get("non_escape_callsite", {})
            self.assertEqual(callsite.get("callee"), "b::g")
            self.assertTrue(callsite.get("resolved", False))

            result2 = pass_obj.run(root_doc, PassContext(opt_level=1))
            summary2 = root_doc.get("meta", {}).get("non_escape_summary", {})
            self.assertFalse(result2.changed)
            self.assertEqual(summary1, summary2)


if __name__ == "__main__":
    unittest.main()
