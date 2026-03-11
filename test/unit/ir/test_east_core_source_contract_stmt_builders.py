"""Source-contract regressions for EAST core statement builder clusters."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import CORE_BUILDER_BASE_SOURCE_PATH
from _east_core_test_support import CORE_SOURCE_PATH
from _east_core_test_support import CORE_STMT_BUILDERS_SOURCE_PATH


class EastCoreSourceContractStmtBuildersTest(unittest.TestCase):
    def test_stmt_builder_defs_live_in_split_module(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        stmt_text = CORE_STMT_BUILDERS_SOURCE_PATH.read_text(encoding="utf-8")

        for marker in (
            "def _sh_make_assign_stmt(",
            "def _sh_make_tuple_destructure_assign_stmt(",
            "def _sh_make_ann_assign_stmt(",
            "def _sh_make_raise_stmt(",
            "def _sh_make_pass_stmt(",
            "def _sh_make_return_stmt(",
            "def _sh_make_yield_stmt(",
            "def _sh_make_augassign_stmt(",
            "def _sh_make_swap_stmt(",
            "def _sh_make_if_stmt(",
            "def _sh_make_while_stmt(",
            "def _sh_make_except_handler(",
            "def _sh_make_try_stmt(",
            "def _sh_make_for_stmt(",
            "def _sh_make_for_range_stmt(",
            "def _sh_make_function_def_stmt(",
            "def _sh_make_class_def_stmt(",
        ):
            self.assertIn(marker, stmt_text)
            self.assertNotIn(marker, core_text)

    def test_core_source_uses_stmt_builder_helpers_for_statement_clusters(self) -> None:
        text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("assign_stmt = _sh_make_assign_stmt(", text)
        self.assertIn("try_stmt = _sh_make_try_stmt(", text)
        self.assertIn(
            "pending_blank_count = _sh_push_stmt_with_trivia(\n"
            "                stmts,\n"
            "                pending_leading_trivia,\n"
            "                pending_blank_count,\n"
            "                _sh_make_while_stmt(",
            text,
        )
        self.assertIn("_sh_make_except_handler(", text)
        self.assertIn(
            "pending_blank_count = _sh_push_stmt_with_trivia(\n"
            "                stmts,\n"
            "                pending_leading_trivia,\n"
            "                pending_blank_count,\n"
            "                _sh_make_try_stmt(",
            text,
        )
        self.assertIn("_sh_make_raise_stmt(", text)
        self.assertIn("pass_stmt = _sh_make_pass_stmt(", text)
        self.assertIn("_sh_make_return_stmt(", text)
        self.assertIn("_sh_make_augassign_stmt(", text)
        self.assertIn("_sh_make_swap_stmt(", text)
        self.assertNotIn('assign_stmt = {"kind": "Assign"', text)
        self.assertNotIn('try_stmt = {"kind": "Try"', text)
        self.assertNotIn(
            'pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, {"kind": "While"',
            text,
        )
        self.assertNotIn('handlers.append({"kind": "ExceptHandler"', text)
        self.assertNotIn(
            'pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, {"kind": "Try"',
            text,
        )
        self.assertNotIn(
            'pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, {"kind": "Raise"',
            text,
        )
        self.assertNotIn('pass_stmt = {"kind": "Pass"', text)
        self.assertNotIn(
            'pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, {"kind": "Return"',
            text,
        )
        self.assertNotIn(
            'pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, {"kind": "AugAssign"',
            text,
        )
        self.assertNotIn(
            'pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, {"kind": "Swap"',
            text,
        )

    def test_stmt_builder_module_routes_statement_envelopes_through_shared_helper(self) -> None:
        builder_text = CORE_BUILDER_BASE_SOURCE_PATH.read_text(encoding="utf-8")
        stmt_text = CORE_STMT_BUILDERS_SOURCE_PATH.read_text(encoding="utf-8")
        node_helper_text = builder_text.split("def _sh_make_node", 1)[1].split("def _sh_make_stmt_node", 1)[0]
        helper_text = builder_text.split("def _sh_make_stmt_node", 1)[1].split("def _sh_make_trivia_blank", 1)[0]
        assign_text = stmt_text.split("def _sh_make_assign_stmt", 1)[1].split("def _sh_make_tuple_destructure_assign_stmt", 1)[0]
        except_text = stmt_text.split("def _sh_make_except_handler", 1)[1].split("def _sh_make_try_stmt", 1)[0]
        try_text = stmt_text.split("def _sh_make_try_stmt", 1)[1].split("def _sh_make_for_stmt", 1)[0]
        fn_text = stmt_text.split("def _sh_make_function_def_stmt", 1)[1].split("def _sh_make_class_def_stmt", 1)[0]

        self.assertIn('node = _sh_make_kind_carrier(kind)', node_helper_text)
        self.assertIn("node.update(fields)", node_helper_text)
        self.assertIn("return _sh_make_node(kind, source_span=source_span)", helper_text)
        self.assertIn('node = _sh_make_stmt_node("Assign", source_span)', assign_text)
        self.assertIn('return _sh_make_node("ExceptHandler", type=type_expr, name=name, body=body)', except_text)
        self.assertIn('node = _sh_make_stmt_node("Try", source_span)', try_text)
        self.assertIn('node = _sh_make_stmt_node("FunctionDef", source_span)', fn_text)
        self.assertNotIn('{"kind": "Assign"', assign_text)
        self.assertNotIn('"kind": "ExceptHandler"', except_text)
        self.assertNotIn('{"kind": "Try"', try_text)
        self.assertNotIn('{"kind": "FunctionDef"', fn_text)

    def test_core_source_uses_stmt_builder_helpers_for_tuple_destructuring_clusters(self) -> None:
        core_text = CORE_SOURCE_PATH.read_text(encoding="utf-8")
        stmt_text = CORE_STMT_BUILDERS_SOURCE_PATH.read_text(encoding="utf-8")
        stmt_block_text = core_text.split("def _sh_parse_stmt_block_mutable", 1)[1].split(
            "def _sh_build_module_root",
            1,
        )[0]

        self.assertIn("def _sh_make_tuple_destructure_assign_stmt(", stmt_text)
        self.assertIn("_sh_make_tuple_destructure_assign_stmt(", stmt_block_text)
        self.assertIn('resolved_type=name_types.get(n1, "unknown")', stmt_block_text)
        self.assertIn('resolved_type=name_types.get(n2, "unknown")', stmt_block_text)
        self.assertNotIn("target_expr = _sh_make_tuple_expr(", stmt_block_text)
        self.assertNotIn('target_expr = {"kind": "Tuple"', stmt_block_text)
        self.assertNotIn(
            'pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, dict<str, object>{{"kind", make_object("Assign")}',
            stmt_block_text,
        )
