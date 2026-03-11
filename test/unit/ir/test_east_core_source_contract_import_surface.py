"""Import-surface guard for the thin EAST core facade."""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from _east_core_test_support import ROOT


IR_SOURCE_DIR = ROOT / "src" / "toolchain" / "ir"
APPROVED_SOURCE_IMPORTERS = {
    ROOT / "src" / "toolchain" / "frontends" / "transpile_cli.py": {
        "convert_path",
        "convert_source_to_east_with_backend",
    },
}


def _core_import_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.module not in {"toolchain.ir.core", "src.toolchain.ir.core"}:
            continue
        for alias in node.names:
            imported.add(alias.name)
    return imported


class EastCoreSourceContractImportSurfaceTest(unittest.TestCase):
    def test_internal_ir_modules_do_not_import_core_hub(self) -> None:
        offenders: list[str] = []
        for path in sorted(IR_SOURCE_DIR.glob("*.py")):
            if path.name == "core.py":
                continue
            if _core_import_names(path):
                offenders.append(path.name)
        self.assertEqual(offenders, [])

    def test_non_ir_source_importers_stay_within_public_surface(self) -> None:
        actual: dict[str, set[str]] = {}
        for path in sorted((ROOT / "src").rglob("*.py")):
            if path.is_relative_to(IR_SOURCE_DIR):
                continue
            names = _core_import_names(path)
            if names:
                actual[str(path.relative_to(ROOT))] = names
        expected = {str(path.relative_to(ROOT)): names for path, names in APPROVED_SOURCE_IMPORTERS.items()}
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
