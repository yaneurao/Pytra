"""Tests for EAST3 human renderer and compatibility wrapper."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.pytra.compiler.east_parts.render_human_east2_cpp import render_east_human_cpp
from src.pytra.compiler.east_parts.render_human_east3_cpp import render_east3_human_cpp


class RenderHumanEast3CppTest(unittest.TestCase):
    def _sample_east3_doc(self) -> dict[str, object]:
        return {
            "ok": True,
            "east": {
                "kind": "Module",
                "east_stage": 3,
                "source_path": "sample.py",
                "body": [
                    {
                        "kind": "ForCore",
                        "iter_mode": "runtime_protocol",
                        "iter_plan": {
                            "kind": "RuntimeIterForPlan",
                            "iter_expr": {"kind": "Name", "id": "xs", "resolved_type": "object"},
                            "dispatch_mode": "type_id",
                            "init_op": "ObjIterInit",
                            "next_op": "ObjIterNext",
                        },
                        "target_plan": {"kind": "NameTarget", "id": "x", "target_type": "object"},
                        "body": [
                            {
                                "kind": "Expr",
                                "value": {
                                    "kind": "ObjBool",
                                    "value": {"kind": "Name", "id": "x", "resolved_type": "object"},
                                },
                            },
                            {
                                "kind": "Expr",
                                "value": {
                                    "kind": "Box",
                                    "value": {"kind": "Name", "id": "x", "resolved_type": "int64"},
                                },
                            },
                            {
                                "kind": "Expr",
                                "value": {
                                    "kind": "IsInstance",
                                    "value": {"kind": "Name", "id": "x", "resolved_type": "object"},
                                    "expected_type_id": {"kind": "Name", "id": "PY_TYPE_NUMBER"},
                                },
                            },
                        ],
                        "orelse": [],
                    }
                ],
                "main_guard_body": [],
            },
        }

    def test_render_east3_human_cpp_renders_core_nodes(self) -> None:
        rendered = render_east3_human_cpp(self._sample_east3_doc())
        self.assertIn("EAST3 Human View", rendered)
        self.assertIn("ForCore mode=runtime_protocol", rendered)
        self.assertIn("obj_bool(", rendered)
        self.assertIn("box(", rendered)
        self.assertIn("is_instance(", rendered)

    def test_compat_wrapper_dispatches_stage3_doc(self) -> None:
        rendered = render_east_human_cpp(self._sample_east3_doc())
        self.assertIn("EAST3 Human View", rendered)
        self.assertIn("py_iter_runtime(", rendered)

    def test_compat_wrapper_keeps_stage2_renderer(self) -> None:
        out_doc = {
            "ok": True,
            "east": {
                "kind": "Module",
                "east_stage": 2,
                "source_path": "sample.py",
                "body": [],
                "main_guard_body": [],
            },
        }
        rendered = render_east_human_cpp(out_doc)
        self.assertIn("EAST Human View", rendered)


if __name__ == "__main__":
    unittest.main()
