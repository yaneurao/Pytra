"""py2rs (EAST based) smoke tests."""

# Language-specific smoke suite.
# Shared py2x target-parameterized checks live in test_py2x_smoke_common.py.

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from backends.rs.emitter.rs_emitter import load_rs_profile, transpile_to_rust
from toolchain.compiler.relative_import_firstwave_smoke_contract import (
    RELATIVE_IMPORT_FIRST_WAVE_SCENARIOS_V1,
)
from toolchain.compiler.transpile_cli import load_east3_document
from src.toolchain.ir.core_entrypoints import convert_path
from src.toolchain.frontends.type_expr import parse_type_expr_text
from backends.rs.emitter.rs_emitter import RustEmitter
from comment_fidelity import assert_no_generated_comments, assert_sample01_module_comments


def load_east(
    input_path: Path,
    parser_backend: str = "self_hosted",
    east_stage: str = "3",
    object_dispatch_mode: str = "native",
    east3_opt_level: str = "1",
    east3_opt_pass: str = "",
    dump_east3_before_opt: str = "",
    dump_east3_after_opt: str = "",
    dump_east3_opt_trace: str = "",
):
    if east_stage != "3":
        raise RuntimeError("unsupported east_stage: " + east_stage)
    doc3 = load_east3_document(
        input_path,
        parser_backend=parser_backend,
        object_dispatch_mode=object_dispatch_mode,
        east3_opt_level=east3_opt_level,
        east3_opt_pass=east3_opt_pass,
        dump_east3_before_opt=dump_east3_before_opt,
        dump_east3_after_opt=dump_east3_after_opt,
        dump_east3_opt_trace=dump_east3_opt_trace,
        target_lang="rs",
    )
    return doc3 if isinstance(doc3, dict) else {}


def find_fixture_case(stem: str) -> Path:
    matches = sorted((ROOT / "test" / "fixtures").rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(f"missing fixture: {stem}")
    return matches[0]


def _relative_import_firstwave_scenarios() -> dict[str, dict[str, object]]:
    return {
        str(entry["scenario_id"]): entry
        for entry in RELATIVE_IMPORT_FIRST_WAVE_SCENARIOS_V1
    }


def transpile_relative_import_project_to_rust(scenario_id: str) -> str:
    scenario = _relative_import_firstwave_scenarios()[scenario_id]
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        entry_path = td_path / str(scenario["entry_rel"])
        helper_path = td_path / str(scenario["helper_rel"])
        entry_path.parent.mkdir(parents=True, exist_ok=True)
        helper_path.parent.mkdir(parents=True, exist_ok=True)
        for pkg_dir in {helper_path.parent, entry_path.parent}:
            current = pkg_dir
            while current != td_path and current.is_relative_to(td_path):
                init_py = current / "__init__.py"
                if not init_py.exists():
                    init_py.write_text("", encoding="utf-8")
                current = current.parent
        helper_path.write_text("def f() -> int:\n    return 7\n", encoding="utf-8")
        entry_path.write_text(
            f"{scenario['import_form']}\nprint({scenario['representative_expr']})\n",
            encoding="utf-8",
        )
        out = td_path / "main.rs"
        proc = subprocess.run(
            ["python3", str(ROOT / "src" / "py2x.py"), str(entry_path), "--target", "rs", "-o", str(out)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            raise AssertionError(proc.stderr)
        return out.read_text(encoding="utf-8")


class Py2RsSmokeTest(unittest.TestCase):
    def test_load_rs_profile_contains_core_sections(self) -> None:
        profile = load_rs_profile()
        self.assertIn("types", profile)
        self.assertIn("operators", profile)
        self.assertIn("syntax", profile)
        self.assertIn("runtime_calls", profile)

    def test_bitwise_invert_basic_uses_rust_not_operator(self) -> None:
        fixture = find_fixture_case("bitwise_invert_basic")
        east = load_east(fixture, parser_backend="self_hosted")
        rust = transpile_to_rust(east)
        self.assertIn("!y", rust)

    def test_comment_fidelity_preserves_source_comments(self) -> None:
        sample = ROOT / "sample" / "py" / "01_mandelbrot.py"
        east = load_east(sample, parser_backend="self_hosted")
        rust = transpile_to_rust(east)
        assert_no_generated_comments(self, rust)
        assert_sample01_module_comments(self, rust, prefix="//")

    def test_bitwise_invert_fixture_uses_rust_not_operator(self) -> None:
        fixture = find_fixture_case("bitwise_invert_basic")
        east = load_east(fixture, parser_backend="self_hosted")
        rust = transpile_to_rust(east)
        self.assertIn("!y", rust)

    def test_cli_relative_import_firstwave_scenarios_transpile_for_rust(self) -> None:
        expectations = {
            "parent_module_alias": (
                "use crate::helper as h;",
                'println!("{}", helper::f());',
            ),
            "parent_symbol_alias": (
                "use crate::helper::f as g;",
                'println!("{}", g());',
            ),
        }
        for scenario_id, expected in expectations.items():
            with self.subTest(scenario_id=scenario_id):
                rust = transpile_relative_import_project_to_rust(scenario_id)
                for needle in expected:
                    self.assertIn(needle, rust)

    def test_transpile_for_range_fixture_lowers_to_for_fastpath(self) -> None:
        fixture = find_fixture_case("for_range")
        east = load_east(fixture, parser_backend="self_hosted")
        rust = transpile_to_rust(east)
        self.assertIn("for i in (0)..(n) {", rust)
        self.assertNotIn("for __for_i_", rust)
        self.assertNotIn("i = __for_i_", rust)
        self.assertNotIn("while i < n {", rust)

    def test_load_east_from_json_wrapper_payload(self) -> None:
        fixture = find_fixture_case("add")
        east = convert_path(fixture)
        with tempfile.TemporaryDirectory() as td:
            east_json = Path(td) / "case.wrapped.east.json"
            wrapped = {"ok": True, "east": east}
            east_json.write_text(json.dumps(wrapped), encoding="utf-8")
            loaded = load_east(east_json)
            rust = transpile_to_rust(loaded)
        self.assertIn("fn add(a: i64, b: i64)", rust)

    def test_for_core_static_range_plan_is_emitted(self) -> None:
        east = {
            "kind": "Module",
            "east_stage": 3,
            "body": [
                {
                    "kind": "ForCore",
                    "target_plan": {"kind": "NameTarget", "id": "i", "target_type": "int64"},
                    "iter_plan": {
                        "kind": "StaticRangeForPlan",
                        "start": {"kind": "Constant", "value": 0},
                        "stop": {"kind": "Constant", "value": 3},
                        "step": {"kind": "Constant", "value": 1},
                        "range_mode": "ascending",
                    },
                    "body": [
                        {
                            "kind": "Expr",
                            "value": {
                                "kind": "Call",
                                "func": {"kind": "Name", "id": "print"},
                                "args": [{"kind": "Name", "id": "i"}],
                                "keywords": [],
                            },
                        }
                    ],
                    "orelse": [],
                }
            ],
            "main_guard_body": [],
            "meta": {},
        }
        rust = transpile_to_rust(east)
        self.assertIn("for i in (0)..(3) {", rust)
        self.assertNotIn("for __for_i_", rust)
        self.assertNotIn("i = __for_i_", rust)
        self.assertNotIn("while i < 3 {", rust)

    def test_for_core_static_range_keeps_bridge_when_target_is_used_later(self) -> None:
        east = {
            "kind": "Module",
            "east_stage": 3,
            "body": [
                {
                    "kind": "ForCore",
                    "target_plan": {"kind": "NameTarget", "id": "i", "target_type": "int64"},
                    "iter_plan": {
                        "kind": "StaticRangeForPlan",
                        "start": {"kind": "Constant", "value": 0},
                        "stop": {"kind": "Constant", "value": 3},
                        "step": {"kind": "Constant", "value": 1},
                        "range_mode": "ascending",
                    },
                    "body": [{"kind": "Pass"}],
                    "orelse": [],
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "Call",
                        "func": {"kind": "Name", "id": "print"},
                        "args": [{"kind": "Name", "id": "i"}],
                        "keywords": [],
                    },
                },
            ],
            "main_guard_body": [],
            "meta": {},
        }
        rust = transpile_to_rust(east)
        self.assertIn("for __for_i_", rust)
        self.assertIn("i = __for_i_", rust)

    def test_for_core_static_range_prefers_normalized_condition_expr(self) -> None:
        east = {
            "kind": "Module",
            "east_stage": 3,
            "body": [
                {
                    "kind": "ForCore",
                    "normalized_expr_version": "east3_expr_v1",
                    "normalized_exprs": {
                        "for_cond_expr": {
                            "kind": "Compare",
                            "left": {"kind": "Name", "id": "i", "resolved_type": "int64"},
                            "ops": ["Gt"],
                            "comparators": [{"kind": "Constant", "value": 3, "resolved_type": "int64"}],
                            "resolved_type": "bool",
                        }
                    },
                    "target_plan": {"kind": "NameTarget", "id": "i", "target_type": "int64"},
                    "iter_plan": {
                        "kind": "StaticRangeForPlan",
                        "start": {"kind": "Constant", "value": 0, "resolved_type": "int64"},
                        "stop": {"kind": "Constant", "value": 3, "resolved_type": "int64"},
                        "step": {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                        "range_mode": "ascending",
                    },
                    "body": [{"kind": "Pass"}],
                    "orelse": [],
                }
            ],
            "main_guard_body": [],
            "meta": {},
        }
        rust = transpile_to_rust(east)
        self.assertIn("while i > 3 {", rust)
        self.assertNotIn("while i < 3 {", rust)

    def test_for_core_runtime_iter_tuple_target_is_emitted(self) -> None:
        east = {
            "kind": "Module",
            "east_stage": 3,
            "body": [
                {
                    "kind": "ForCore",
                    "target_plan": {
                        "kind": "TupleTarget",
                        "elements": [
                            {"kind": "NameTarget", "id": "k"},
                            {"kind": "NameTarget", "id": "v"},
                        ],
                        "target_type": "tuple[int64,int64]",
                    },
                    "iter_plan": {
                        "kind": "RuntimeIterForPlan",
                        "iter_expr": {"kind": "Name", "id": "pairs"},
                        "init_op": "ObjIterInit",
                        "next_op": "ObjIterNext",
                    },
                    "body": [
                        {
                            "kind": "Expr",
                            "value": {
                                "kind": "Call",
                                "func": {"kind": "Name", "id": "print"},
                                "args": [
                                    {"kind": "Name", "id": "k"},
                                    {"kind": "Name", "id": "v"},
                                ],
                                "keywords": [],
                            },
                        }
                    ],
                    "orelse": [],
                }
            ],
            "main_guard_body": [],
            "meta": {},
        }
        rust = transpile_to_rust(east)
        self.assertIn("for (k, v) in pairs {", rust)
        self.assertIn("println!(", rust)

    def test_rust_emitter_fail_closed_on_unresolved_stdlib_runtime_call(self) -> None:
        east = {
            "kind": "Module",
            "east_stage": 3,
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "_case_main",
                    "arg_order": [],
                    "arg_types": {},
                    "return_type": "None",
                    "body": [
                        {
                            "kind": "Expr",
                            "value": {
                                "kind": "Call",
                                "func": {"kind": "Name", "id": "save_gif"},
                                "args": [],
                                "keywords": [],
                                "semantic_tag": "stdlib.fn.save_gif",
                            },
                        }
                    ],
                }
            ],
            "main_guard_body": [],
            "meta": {},
        }
        with self.assertRaises(RuntimeError) as cm:
            transpile_to_rust(east)
        self.assertIn("unresolved stdlib runtime call", str(cm.exception))

    def test_runtime_import_resolution_uses_canonical_runtime_modules(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "runtime_imports.py"
            src_py.write_text(
                "import math as m\n"
                "from math import pi\n"
                "from pytra.utils import gif\n"
                "from pytra.utils.gif import save_gif\n"
                "\n"
                "def main() -> None:\n"
                "    x: float = m.sqrt(4.0)\n"
                "    y: float = pi\n"
                "    gif.save_gif('x.gif', 1, 1, [])\n"
                "    save_gif('x.gif', 1, 1, [])\n"
                "    print(x, y)\n",
                encoding="utf-8",
            )
            east = load_east(src_py, parser_backend="self_hosted")
            rust = transpile_to_rust(east)

        self.assertIn("use crate::pytra::std::math as m;", rust)
        self.assertIn("use crate::pytra::std::math::pi;", rust)
        self.assertIn("use crate::pytra::utils::gif;", rust)
        self.assertIn("use crate::pytra::utils::gif::save_gif;", rust)
        self.assertNotIn("use crate::math;", rust)
        self.assertIn("pytra::std::math::sqrt(4.0)", rust)
        self.assertIn('pytra::utils::gif::save_gif(&(("x.gif").to_string()), 1, 1, &(vec![]));', rust)
        self.assertIn('save_gif(&(("x.gif").to_string()), 1, 1, &(vec![]));', rust)

    def test_runtime_scaffold_exposes_pytra_std_time_and_math(self) -> None:
        runtime_src = (ROOT / "src" / "runtime" / "rs" / "pytra-core" / "built_in" / "py_runtime.rs").read_text(
            encoding="utf-8"
        )
        self.assertIn("pub mod pytra {", runtime_src)
        self.assertIn("pub mod std {", runtime_src)
        self.assertIn("pub use super::super::time;", runtime_src)
        self.assertIn("pub use super::super::math;", runtime_src)

    def test_runtime_import_resolution_skips_redundant_root_math_use(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            src_py = Path(td) / "runtime_imports_root_math.py"
            src_py.write_text(
                "import math\n"
                "\n"
                "def main() -> None:\n"
                "    print(math.sqrt(4.0))\n",
                encoding="utf-8",
            )
            east = load_east(src_py, parser_backend="self_hosted")
            rust = transpile_to_rust(east)

        self.assertNotIn("use crate::pytra::std::math;", rust)
        self.assertIn("pytra::std::math::sqrt(4.0)", rust)

    def test_for_core_downcount_range_uses_descending_condition(self) -> None:
        fixture = find_fixture_case("range_downcount_len_minus1")
        east = load_east(fixture, parser_backend="self_hosted")
        rust = transpile_to_rust(east)
        self.assertIn("((-1) < 0 && i > -1)", rust)
        self.assertNotIn("while i < -1 {", rust)

    def test_sample08_capture_return_avoids_clone_on_bytes_ctor_in_return(self) -> None:
        sample = ROOT / "sample" / "py" / "08_langtons_ant.py"
        east = load_east(sample, parser_backend="self_hosted")
        rust = transpile_to_rust(east)
        self.assertIn("return frame;", rust)
        self.assertNotIn("return (frame).clone();", rust)
        self.assertIn("grid[((y) as usize)][((x) as usize)]", rust)
        self.assertNotIn("grid.len() as i64 + ((y) as i64)", rust)
        self.assertIn("} else if d == 1 {", rust)
        self.assertIn("} else if d == 2 {", rust)
        self.assertIn("if i == __next_capture_", rust)
        self.assertNotIn("if i % capture_every == 0 {", rust)
        self.assertIn("frames.reserve((", rust)

    def test_sample18_list_ref_params_prefer_slice_signature(self) -> None:
        sample = ROOT / "sample" / "py" / "18_mini_language_interpreter.py"
        east = load_east(sample, parser_backend="self_hosted")
        rust = transpile_to_rust(east)
        self.assertIn("fn tokenize(lines: &[String]) -> Vec<Token> {", rust)
        self.assertIn("fn eval_expr(expr_index: i64, expr_nodes: &[ExprNode], env: &::std::collections::HashMap<String, i64>) -> i64 {", rust)
        self.assertIn("fn execute(stmts: &[StmtNode], expr_nodes: &[ExprNode], trace: bool) -> i64 {", rust)
        self.assertIn("let node: &ExprNode = &(expr_nodes[", rust)
        self.assertNotIn("let node: ExprNode = (expr_nodes[", rust)
        self.assertIn("single_char_token_kinds[((single_tag - 1) as usize)]", rust)
        self.assertNotIn("single_char_token_kinds[((if ((single_tag - 1) as i64) < 0", rust)
        self.assertIn("py_str_at_nonneg(&source, ((i) as usize))", rust)
        self.assertIn("match (ch).as_str()", rust)
        self.assertNotIn("single_char_token_tags.get(&ch)", rust)
        self.assertNotIn("format!(\"{}{}\", format!(\"{}{}\",", rust)
        self.assertIn("env: &::std::collections::HashMap<String, i64>", rust)
        self.assertIn("let mut env: ::std::collections::HashMap<String, i64> = ::std::collections::HashMap::from([]);", rust)
        self.assertNotIn("env: &::std::collections::BTreeMap<String, i64>", rust)
        self.assertNotIn("fn tokenize(lines: &Vec<String>) -> Vec<Token> {", rust)
        self.assertNotIn("fn eval_expr(expr_index: i64, expr_nodes: &Vec<ExprNode>", rust)
        self.assertNotIn("fn execute(stmts: &Vec<StmtNode>", rust)

    def test_object_boundary_nodes_are_lowered_without_legacy_bridge(self) -> None:
        east = {
            "kind": "Module",
            "east_stage": 3,
            "body": [
                {
                    "kind": "Expr",
                    "value": {"kind": "ObjBool", "value": {"kind": "Name", "id": "x", "resolved_type": "Any"}, "resolved_type": "bool"},
                },
                {
                    "kind": "Expr",
                    "value": {"kind": "ObjLen", "value": {"kind": "Name", "id": "x", "resolved_type": "Any"}, "resolved_type": "int64"},
                },
                {
                    "kind": "Expr",
                    "value": {"kind": "ObjStr", "value": {"kind": "Name", "id": "x", "resolved_type": "Any"}, "resolved_type": "str"},
                },
                {
                    "kind": "Expr",
                    "value": {"kind": "ObjTypeId", "value": {"kind": "Name", "id": "x", "resolved_type": "Any"}, "resolved_type": "int64"},
                },
                {
                    "kind": "Expr",
                    "value": {"kind": "ObjIterInit", "value": {"kind": "Name", "id": "x", "resolved_type": "Any"}, "resolved_type": "object"},
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "ObjIterNext",
                        "iter": {"kind": "ObjIterInit", "value": {"kind": "Name", "id": "x", "resolved_type": "Any"}, "resolved_type": "object"},
                        "resolved_type": "object",
                    },
                },
            ],
            "main_guard_body": [],
            "meta": {},
        }
        rust = transpile_to_rust(east)
        self.assertIn("py_any_to_bool(&x);", rust)
        self.assertIn("PyAny::Str(s) => s.len() as i64", rust)
        self.assertIn("py_any_to_string(&x);", rust)
        self.assertIn("py_runtime_value_type_id(&x);", rust)
        self.assertIn("iter(x);", rust)
        self.assertIn("next(iter(x));", rust)

    def test_type_predicate_nodes_are_lowered_without_legacy_bridge(self) -> None:
        east = {
            "kind": "Module",
            "east_stage": 3,
            "body": [
                {"kind": "ClassDef", "name": "Base", "base": "", "body": []},
                {"kind": "ClassDef", "name": "Child", "base": "Base", "body": []},
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "IsInstance",
                        "value": {"kind": "Name", "id": "x", "resolved_type": "Any"},
                        "expected_type_id": {"kind": "Name", "id": "PYTRA_TID_INT"},
                        "resolved_type": "bool",
                    },
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "IsInstance",
                        "value": {"kind": "Name", "id": "x", "resolved_type": "Any"},
                        "expected_type_id": {"kind": "Name", "id": "Base"},
                        "resolved_type": "bool",
                    },
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "IsSubtype",
                        "actual_type_id": {"kind": "Name", "id": "PYTRA_TID_BOOL"},
                        "expected_type_id": {"kind": "Name", "id": "PYTRA_TID_INT"},
                        "resolved_type": "bool",
                    },
                },
                {
                    "kind": "Expr",
                    "value": {
                        "kind": "IsSubclass",
                        "actual_type_id": {"kind": "Name", "id": "Child"},
                        "expected_type_id": {"kind": "Name", "id": "Base"},
                        "resolved_type": "bool",
                    },
                },
            ],
            "main_guard_body": [],
            "meta": {},
        }
        rust = transpile_to_rust(east)
        self.assertIn("py_register_generated_type_info(); py_runtime_value_isinstance(&x, PYTRA_TID_INT)", rust)
        self.assertIn("py_register_generated_type_info(); py_runtime_value_isinstance(&x, Base::PYTRA_TYPE_ID)", rust)
        self.assertIn("py_register_generated_type_info(); py_runtime_type_id_is_subtype(PYTRA_TID_BOOL, PYTRA_TID_INT)", rust)
        self.assertIn("py_register_generated_type_info(); py_runtime_type_id_issubclass(Child::PYTRA_TYPE_ID, Base::PYTRA_TYPE_ID)", rust)
        self.assertNotIn("fn py_runtime_type_id(actual_type_id:", rust)
        self.assertNotIn("fn py_is_subtype(", rust)
        self.assertNotIn("fn py_issubclass(", rust)
        self.assertNotIn("fn py_isinstance<", rust)

    def test_box_unbox_nodes_are_lowered_without_legacy_bridge(self) -> None:
        east = {
            "kind": "Module",
            "east_stage": 3,
            "body": [
                {
                    "kind": "Assign",
                    "targets": [{"kind": "Name", "id": "y"}],
                    "value": {
                        "kind": "Box",
                        "value": {"kind": "Constant", "value": 1, "resolved_type": "int64"},
                        "resolved_type": "Any",
                    },
                },
                {
                    "kind": "Assign",
                    "targets": [{"kind": "Name", "id": "z"}],
                    "value": {
                        "kind": "Unbox",
                        "value": {"kind": "Name", "id": "y", "resolved_type": "Any"},
                        "target": "int64",
                        "resolved_type": "int64",
                    },
                },
            ],
            "main_guard_body": [],
            "meta": {},
        }
        rust = transpile_to_rust(east)
        self.assertIn("PyAny::Int((1) as i64)", rust)
        self.assertIn("py_any_to_i64(&y)", rust)

    def test_imports_emit_use_lines(self) -> None:
        fixture = find_fixture_case("from_pytra_std_import_math")
        east = load_east(fixture, parser_backend="self_hosted")
        rust = transpile_to_rust(east)
        self.assertIn("use crate::pytra::std::math::floor;", rust)
        self.assertIn("use crate::pytra::std::math::sqrt as msqrt;", rust)

    def test_for_tuple_target_and_dict_items_quality(self) -> None:
        fixture = find_fixture_case("dict_get_items")
        east = load_east(fixture, parser_backend="self_hosted")
        rust = transpile_to_rust(east)
        self.assertIn("for (_k, v) in", rust)
        self.assertIn(".clone().into_iter()", rust)
        self.assertNotIn(".items()", rust)

    def test_class_struct_has_clone_debug_derive(self) -> None:
        fixture = find_fixture_case("class_instance")
        east = load_east(fixture, parser_backend="self_hosted")
        rust = transpile_to_rust(east)
        self.assertIn("#[derive(Clone, Debug)]", rust)
        self.assertIn("struct Box100 {", rust)

    def test_dict_entries_literal_is_not_dropped(self) -> None:
        fixture = find_fixture_case("any_dict_items")
        east = load_east(fixture, parser_backend="self_hosted")
        rust = transpile_to_rust(east)
        self.assertIn("BTreeMap::from([(", rust)
        self.assertIn("\"meta\"", rust)
        self.assertIn("use crate::py_runtime::*;", rust)
        self.assertIn("py_any_as_dict(", rust)
        self.assertIn("py_any_to_i64(&v)", rust)
        self.assertIn("py_any_to_string(&", rust)

    def test_reassigned_args_emit_mut_only_when_needed(self) -> None:
        src = """
def f(x: int, y: int) -> int:
    x = x + 1
    return x + y

def g(a: int, b: int) -> int:
    return a + b
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "arg_usage_case.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            rust = transpile_to_rust(east)

        self.assertIn("fn f(mut x: i64, y: i64) -> i64 {", rust)
        self.assertIn("fn g(a: i64, b: i64) -> i64 {", rust)
        self.assertNotIn("fn f(mut x: i64, mut y: i64) -> i64 {", rust)

    def test_ref_container_args_materialize_value_path_with_to_vec_or_clone(self) -> None:
        src = """
from typing import Any

def f(xs: list[int], ys: list[Any]) -> int:
    a: list[int] = xs
    b: list[Any] = ys
    return a[0] + int(b[0])
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "ref_container_args.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            rust = transpile_to_rust(east)

        self.assertIn("fn f(xs: &[i64], ys: &[PyAny]) -> i64 {", rust)
        self.assertIn("let a: Vec<i64> = (xs).to_vec();", rust)
        self.assertIn("let b: Vec<PyAny> = (ys).to_vec();", rust)
        self.assertNotIn("let a: Vec<i64> = xs;", rust)
        self.assertNotIn("let b: Vec<PyAny> = ys;", rust)

    def test_py2rs_does_not_import_src_common(self) -> None:
        src = (ROOT / "src" / "py2x.py").read_text(encoding="utf-8")
        self.assertNotIn("src.common", src)
        self.assertNotIn("from common.", src)

    def test_render_expr_kind_specific_hook_precedes_leaf_hook(self) -> None:
        emitter = RustEmitter({"kind": "Module", "body": [], "meta": {}})
        emitter.hooks["on_render_expr_name"] = (
            lambda _em, _kind, _expr_node: "specific_name_hook()"
        )
        emitter.hooks["on_render_expr_leaf"] = (
            lambda _em, _kind, _expr_node: "leaf_hook()"
        )
        rendered = emitter.render_expr({"kind": "Name", "id": "x"})
        self.assertEqual(rendered, "specific_name_hook()")

    def test_isinstance_lowering_for_any_uses_type_id_runtime_api(self) -> None:
        src = """
from typing import Any

def is_int(x: Any) -> bool:
    return isinstance(x, int)

def is_dict(x: Any) -> bool:
    return isinstance(x, dict)
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "isinstance_any.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            rust = transpile_to_rust(east)

        self.assertNotIn("return isinstance(", rust)
        self.assertIn("py_runtime_value_isinstance(&x, PYTRA_TID_INT)", rust)
        self.assertIn("py_runtime_value_isinstance(&x, PYTRA_TID_DICT)", rust)
        self.assertIn("fn py_register_generated_type_info() {", rust)

    def test_isinstance_lowering_for_static_builtin_type(self) -> None:
        src = """
def is_int(x: int) -> bool:
    return isinstance(x, int)

def is_float(x: int) -> bool:
    return isinstance(x, float)
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "isinstance_builtin.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            rust = transpile_to_rust(east)

        self.assertNotIn("return isinstance(", rust)
        self.assertIn("py_register_generated_type_info(); py_runtime_value_isinstance(&x, PYTRA_TID_INT)", rust)
        self.assertIn("py_register_generated_type_info(); py_runtime_value_isinstance(&x, PYTRA_TID_FLOAT)", rust)

    def test_isinstance_lowering_for_class_inheritance(self) -> None:
        src = """
class A:
    def __init__(self) -> None:
        pass

class B(A):
    def __init__(self) -> None:
        pass

def is_base(x: B) -> bool:
    return isinstance(x, A)

def is_child(x: A) -> bool:
    return isinstance(x, B)
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "isinstance_class.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            rust = transpile_to_rust(east)

        self.assertNotIn("return isinstance(", rust)
        self.assertIn("const PYTRA_TYPE_ID: i64 = 1000;", rust)
        self.assertIn("const PYTRA_TYPE_ID: i64 = 1001;", rust)
        self.assertIn("impl PyRuntimeTypeId for A {", rust)
        self.assertIn("impl PyRuntimeTypeId for B {", rust)
        self.assertIn("py_register_generated_type_info(); py_runtime_value_isinstance(&x, A::PYTRA_TYPE_ID)", rust)
        self.assertIn("py_register_generated_type_info(); py_runtime_value_isinstance(&x, B::PYTRA_TYPE_ID)", rust)
        self.assertIn("py_register_type_info(1000, 9, 9, 10);", rust)
        self.assertIn("py_register_type_info(1001, 10, 10, 10);", rust)

    def test_isinstance_sibling_classes_emit_non_overlapping_type_ranges(self) -> None:
        src = """
class A:
    def __init__(self) -> None:
        pass

class B:
    def __init__(self) -> None:
        pass

def is_a(x: B) -> bool:
    return isinstance(x, A)
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "isinstance_sibling_class.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            rust = transpile_to_rust(east)

        self.assertIn("py_register_generated_type_info(); py_runtime_value_isinstance(&x, A::PYTRA_TYPE_ID)", rust)
        self.assertIn("py_register_type_info(1000, 9, 9, 9);", rust)
        self.assertIn("py_register_type_info(1001, 10, 10, 10);", rust)

    def test_isinstance_lowering_for_object_type(self) -> None:
        src = """
from typing import Any

def from_static(x: int) -> bool:
    return isinstance(x, object)

def from_any(x: Any) -> bool:
    return isinstance(x, object)
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "isinstance_object.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            rust = transpile_to_rust(east)

        self.assertNotIn("return isinstance(", rust)
        self.assertIn("py_register_generated_type_info(); py_runtime_value_isinstance(&x, PYTRA_TID_OBJECT)", rust)

    def test_isinstance_tuple_lowering_for_any_uses_or_of_type_id_checks(self) -> None:
        src = """
from typing import Any

def f(x: Any) -> bool:
    return isinstance(x, (int, dict))
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "isinstance_tuple_any.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            rust = transpile_to_rust(east)

        self.assertNotIn("return isinstance(", rust)
        self.assertIn("py_runtime_value_isinstance(&x, PYTRA_TID_INT)", rust)
        self.assertIn("py_runtime_value_isinstance(&x, PYTRA_TID_DICT)", rust)
        self.assertIn("||", rust)

    def test_isinstance_set_lowering_for_any_uses_type_id_runtime_api(self) -> None:
        src = """
from typing import Any

def f(x: Any) -> bool:
    return isinstance(x, set)
"""
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "isinstance_set_any.py"
            case.write_text(src, encoding="utf-8")
            east = load_east(case, parser_backend="self_hosted")
            rust = transpile_to_rust(east)

        self.assertNotIn("return isinstance(", rust)
        self.assertIn("py_runtime_value_isinstance(&x, PYTRA_TID_SET)", rust)

    def test_transpile_rejects_general_union_type_expr_in_annassign(self) -> None:
        east = {
            "kind": "Module",
            "body": [
                {
                    "kind": "AnnAssign",
                    "target": {"kind": "Name", "id": "value", "resolved_type": "list[int64|bool]"},
                    "annotation": "list[int64|bool]",
                    "annotation_type_expr": parse_type_expr_text("list[int | bool]"),
                    "decl_type": "list[int64|bool]",
                    "decl_type_expr": parse_type_expr_text("list[int | bool]"),
                    "value": {"kind": "List", "elements": [], "resolved_type": "list[int64|bool]"},
                }
            ],
        }
        with self.assertRaisesRegex(
            RuntimeError,
            "unsupported_syntax\\|Rust backend does not support general union TypeExpr yet",
        ):
            transpile_to_rust(east)

    def test_transpile_rejects_general_union_type_expr_in_signature(self) -> None:
        east = {
            "kind": "Module",
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "pick",
                    "args": [{"arg": "x"}],
                    "arg_order": ["x"],
                    "arg_types": {"x": "int64|bool"},
                    "arg_type_exprs": {"x": parse_type_expr_text("int | bool")},
                    "arg_usage": {"x": "readonly"},
                    "return_type": "int64|bool",
                    "return_type_expr": parse_type_expr_text("int | bool"),
                    "body": [{"kind": "Return", "value": {"kind": "Name", "id": "x", "resolved_type": "int64|bool"}}],
                }
            ],
        }
        with self.assertRaisesRegex(
            RuntimeError,
            "unsupported_syntax\\|Rust backend does not support general union TypeExpr yet",
        ):
            transpile_to_rust(east)

    def test_transpile_rejects_nominal_adt_class_lane(self) -> None:
        east = {
            "kind": "Module",
            "body": [
                {
                    "kind": "ClassDef",
                    "name": "Maybe",
                    "meta": {
                        "nominal_adt_v1": {
                            "schema_version": 1,
                            "role": "family",
                            "family_name": "Maybe",
                        }
                    },
                    "body": [],
                }
            ],
        }
        with self.assertRaisesRegex(
            RuntimeError,
            "unsupported_syntax\\|Rust backend does not support nominal ADT v1 lanes yet",
        ):
            transpile_to_rust(east)

    def test_transpile_rejects_nominal_adt_match_lane(self) -> None:
        east = {
            "kind": "Module",
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "f",
                    "args": [{"arg": "x"}],
                    "arg_order": ["x"],
                    "arg_types": {"x": "Maybe"},
                    "arg_usage": {"x": "readonly"},
                    "return_type": "int64",
                    "body": [{"kind": "Match", "subject": {"kind": "Name", "id": "x", "resolved_type": "Maybe"}}],
                }
            ],
        }
        with self.assertRaisesRegex(
            RuntimeError,
            "unsupported_syntax\\|Rust backend does not support nominal ADT v1 lanes yet",
        ):
            transpile_to_rust(east)

    def test_transpile_rejects_nominal_adt_projection_lane(self) -> None:
        east = {
            "kind": "Module",
            "body": [
                {
                    "kind": "FunctionDef",
                    "name": "f",
                    "args": [{"arg": "x"}],
                    "arg_order": ["x"],
                    "arg_types": {"x": "Just"},
                    "arg_usage": {"x": "readonly"},
                    "return_type": "int64",
                    "body": [
                        {
                            "kind": "Return",
                            "value": {
                                "kind": "Attribute",
                                "value": {"kind": "Name", "id": "x", "resolved_type": "Just"},
                                "attr": "value",
                                "resolved_type": "int64",
                                "lowered_kind": "NominalAdtProjection",
                            },
                        }
                    ],
                }
            ],
        }
        with self.assertRaisesRegex(
            RuntimeError,
            "unsupported_syntax\\|Rust backend does not support nominal ADT v1 lanes yet",
        ):
            transpile_to_rust(east)


if __name__ == "__main__":
    unittest.main()
