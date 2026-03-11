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
}
REPRESENTATIVE_TEST_IMPORTERS = {
    ROOT / "test" / "unit" / "common" / "test_self_hosted_signature.py",
    ROOT / "test" / "unit" / "backends" / "cpp" / "test_east3_cpp_bridge.py",
    ROOT / "test" / "unit" / "backends" / "cs" / "test_py2cs_smoke.py",
    ROOT / "test" / "unit" / "backends" / "go" / "test_py2go_smoke.py",
    ROOT / "test" / "unit" / "backends" / "java" / "test_py2java_smoke.py",
    ROOT / "test" / "unit" / "backends" / "js" / "test_py2js_smoke.py",
    ROOT / "test" / "unit" / "backends" / "kotlin" / "test_py2kotlin_smoke.py",
    ROOT / "test" / "unit" / "backends" / "lua" / "test_py2lua_smoke.py",
    ROOT / "test" / "unit" / "backends" / "rb" / "test_py2rb_smoke.py",
    ROOT / "test" / "unit" / "backends" / "rs" / "test_py2rs_smoke.py",
    ROOT / "test" / "unit" / "backends" / "scala" / "test_py2scala_smoke.py",
    ROOT / "test" / "unit" / "backends" / "swift" / "test_py2swift_smoke.py",
    ROOT / "test" / "unit" / "backends" / "ts" / "test_py2ts_smoke.py",
    ROOT / "test" / "unit" / "ir" / "test_east2_to_east3_lowering.py",
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

    def test_representative_tests_and_backend_smokes_do_not_import_core_facade(self) -> None:
        actual = {
            str(path.relative_to(ROOT)): _core_import_names(path)
            for path in sorted(REPRESENTATIVE_TEST_IMPORTERS)
            if _core_import_names(path)
        }
        self.assertEqual(actual, {})


if __name__ == "__main__":
    unittest.main()
