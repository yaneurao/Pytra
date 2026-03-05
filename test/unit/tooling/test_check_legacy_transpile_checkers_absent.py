from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
SCRIPT = ROOT / "tools" / "check_legacy_transpile_checkers_absent.py"

SPEC = importlib.util.spec_from_file_location("check_legacy_transpile_checkers_absent", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("failed to load check_legacy_transpile_checkers_absent.py")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class LegacyCheckerGuardTest(unittest.TestCase):
    def test_no_legacy_scripts_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            tools = root / "tools"
            tools.mkdir(parents=True, exist_ok=True)
            (tools / "check_py2x_transpile.py").write_text("# ok", encoding="utf-8")
            found = MOD._find_legacy_checker_scripts(root)
            self.assertEqual(found, [])

    def test_legacy_scripts_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            tools = root / "tools"
            tools.mkdir(parents=True, exist_ok=True)
            (tools / "check_py2x_transpile.py").write_text("# ok", encoding="utf-8")
            (tools / "check_py2cpp_transpile.py").write_text("# legacy", encoding="utf-8")
            (tools / "check_py2java_transpile.py").write_text("# legacy", encoding="utf-8")
            found = MOD._find_legacy_checker_scripts(root)
            self.assertEqual(
                found,
                [
                    "tools/check_py2cpp_transpile.py",
                    "tools/check_py2java_transpile.py",
                ],
            )


if __name__ == "__main__":
    unittest.main()
