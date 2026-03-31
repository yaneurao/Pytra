from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
TOOLCHAIN2_ROOT = ROOT / "src" / "toolchain2"


def _missing_return_annotations(root: Path) -> list[str]:
    missing: list[str] = []
    for path in sorted(root.rglob("*.py")):
        try:
            module = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            raise AssertionError(f"failed to parse {path}: {exc}") from exc
        rel = path.relative_to(ROOT)
        for node in ast.walk(module):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.returns is None:
                missing.append(f"{rel}:{node.lineno}:{node.name}")
    return missing


class SelfhostReturnAnnotationsTest(unittest.TestCase):
    def test_toolchain2_functions_have_explicit_return_annotations(self) -> None:
        missing = _missing_return_annotations(TOOLCHAIN2_ROOT)
        self.assertEqual(missing, [])
