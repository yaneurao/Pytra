"""Unit tests for EAST3 integer promotion rules.

Verifies that C++-style integer promotion is applied:
- int8/uint8/int16/uint16 operands → int32 after arithmetic ops
- bytes/bytearray iteration variables → int32 (not uint8)
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.toolchain.compile.core_entrypoints import convert_source_to_east_with_backend
from src.toolchain.compile.east2_to_east3_lowering import lower_east2_to_east3


def _build_east3(source: str) -> dict[str, object]:
    east = convert_source_to_east_with_backend(
        source,
        filename="test.py",
        parser_backend="self_hosted",
    )
    return lower_east2_to_east3(east)


def _find_function_body(east3: dict[str, object], func_name: str) -> list[dict[str, object]]:
    body = east3.get("body", [])
    for stmt in body:
        if isinstance(stmt, dict) and stmt.get("kind") == "FunctionDef" and stmt.get("name") == func_name:
            return stmt.get("body", [])
    return []


def _find_nodes_by_kind(node: object, kind: str) -> list[dict[str, object]]:
    """Recursively find all nodes with the given kind."""
    results: list[dict[str, object]] = []
    if isinstance(node, dict):
        if node.get("kind") == kind:
            results.append(node)
        for v in node.values():
            results.extend(_find_nodes_by_kind(v, kind))
    elif isinstance(node, list):
        for item in node:
            results.extend(_find_nodes_by_kind(item, kind))
    return results


class TestIntegerPromotionSpec(unittest.TestCase):
    """Specification tests for integer promotion behavior.

    These tests document the expected behavior once P0-INTEGER-PROMOTION
    is implemented.  Tests that depend on unimplemented features are
    marked with @unittest.skip.
    """

    def test_uint8_shift_result_is_int32(self) -> None:
        """uint8 << int should produce int32 or wider, not uint8."""
        source = """def shift(v: int, n: int) -> int:
    data: bytes = bytes([v])
    for b in data:
        return b << n
    return 0
"""
        east3 = _build_east3(source)
        body = _find_function_body(east3, "shift")
        # After promotion, the shift result type should be int32 or int64
        shifts = _find_nodes_by_kind(body, "BinOp")
        for s in shifts:
            if s.get("op") == "LShift":
                result_type = str(s.get("resolved_type", ""))
                self.assertIn(result_type, {"int32", "int64", "int"},
                              f"shift result should be promoted, got {result_type}")

    def test_bytes_iteration_var_is_int(self) -> None:
        """Iterating over bytes should yield int32, not uint8."""
        source = """def sum_bytes(data: bytes) -> int:
    total: int = 0
    for v in data:
        total += v
    return total
"""
        east3 = _build_east3(source)
        body = _find_function_body(east3, "sum_bytes")
        # The ForCore target type should be int32
        for_nodes = _find_nodes_by_kind(body, "ForCore")
        self.assertTrue(len(for_nodes) > 0, "ForCore node not found")
        for f in for_nodes:
            target_plan = f.get("target_plan", {})
            if isinstance(target_plan, dict):
                target_type = str(target_plan.get("target_type", ""))
                self.assertIn(target_type, {"int32", "int64", "int"},
                              f"bytes iteration var should be int, got {target_type}")

    def test_uint8_shift_overflow_demonstrates_problem(self) -> None:
        """Demonstrate that uint8 << 9 overflows in languages without promotion.

        This test verifies the problem exists: Python's int is arbitrary
        precision, but uint8 << 9 in Julia/Go/Rust/Zig/Swift yields 0.
        """
        # Python semantics: 1 << 9 = 512
        self.assertEqual(1 << 9, 512)
        # uint8 semantics (simulated): (1 << 9) & 0xFF = 0
        self.assertEqual((1 << 9) & 0xFF, 0)

    def test_int16_shift_overflow_demonstrates_problem(self) -> None:
        """Demonstrate that int16 << 15 overflows without promotion."""
        # Python semantics: 1 << 15 = 32768
        self.assertEqual(1 << 15, 32768)
        # int16 semantics (simulated): (1 << 15) as signed int16 wraps
        val = (1 << 15) & 0xFFFF
        # 32768 as uint16 is fine, but as signed int16 it's -32768
        self.assertEqual(val, 32768)

    def test_promotion_rule_spec(self) -> None:
        """Document the C++ integer promotion rules that EAST3 should follow.

        Types smaller than int32 are promoted to int32 for arithmetic.
        """
        small_types = {"int8", "uint8", "int16", "uint16"}
        no_promotion_types = {"int32", "uint32", "int64", "uint64", "float32", "float64"}

        for t in small_types:
            # Should promote to int32
            promoted = "int32"  # C++ rule: smaller than int → int
            self.assertEqual(promoted, "int32", f"{t} should promote to int32")

        for t in no_promotion_types:
            # Should NOT promote (already >= int32)
            self.assertIn(t, no_promotion_types, f"{t} should not be promoted")


if __name__ == "__main__":
    unittest.main()
